from __future__ import annotations

import logging
import traceback
from typing import Optional, List
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.services.llm.provider import llm_provider
from app.services.llm.prompts import RAG_QUERY_PROMPT

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self._pinecone: Optional[Pinecone] = None
        self._encoder: Optional[SentenceTransformer] = None

    def _get_pinecone(self) -> Pinecone:
        if self._pinecone is None:
            self._pinecone = Pinecone(api_key=settings.pinecone_api_key)
        return self._pinecone

    def _get_encoder(self) -> SentenceTransformer:
        if self._encoder is None:
            logger.info(f"[RAG] 加载本地Embedding模型: sentence-transformers/all-MiniLM-L6-v2")
            self._encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return self._encoder

    async def embed_text(self, text: str) -> List[float]:
        logger.debug(f"[RAG] 嵌入文本, 长度={len(text)}")
        try:
            encoder = self._get_encoder()
            embedding = encoder.encode(text).tolist()
            logger.debug(f"[RAG] 嵌入成功, 向量维度={len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"[RAG] 嵌入文本失败: {str(e)}\n{traceback.format_exc()}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        logger.debug(f"[RAG] 批量嵌入文本, 数量={len(texts)}")
        try:
            encoder = self._get_encoder()
            embeddings = encoder.encode(texts).tolist()
            logger.debug(f"[RAG] 批量嵌入成功, 向量维度={len(embeddings[0])}")
            return embeddings
        except Exception as e:
            logger.error(f"[RAG] 批量嵌入失败: {str(e)}\n{traceback.format_exc()}")
            raise

    async def upsert_documents(
        self,
        documents: List[dict],
        namespace: str = "default",
    ):
        """Upsert documents to Pinecone. Each doc: {id, text, metadata}"""
        logger.info(f"[RAG] 插入文档到Pinecone, 数量={len(documents)}, namespace={namespace}")
        pc = self._get_pinecone()
        index = pc.Index(settings.pinecone_index_name)

        texts = [doc["text"] for doc in documents]
        embeddings = await self.embed_texts(texts)

        vectors = [
            {
                "id": doc["id"],
                "values": embedding,
                "metadata": {**doc.get("metadata", {}), "text": doc["text"][:1000]},
            }
            for doc, embedding in zip(documents, embeddings)
        ]

        for i in range(0, len(vectors), 100):
            batch = vectors[i : i + 100]
            index.upsert(vectors=batch, namespace=namespace)
            logger.debug(f"[RAG] 已插入批次 {i//100 + 1}")

    async def query(
        self,
        query: str,
        top_k: int = 5,
        namespace: str = "default",
        filter_dict: Optional[dict] = None,
    ) -> List[dict]:
        """Query Pinecone for similar documents."""
        logger.debug(f"[RAG] Pinecone查询 namespace={namespace}, top_k={top_k}, filter={filter_dict}")

        try:
            query_embedding = await self.embed_text(query)
        except Exception as e:
            logger.error(f"[RAG] 查询嵌入失败: {str(e)}")
            raise

        try:
            pc = self._get_pinecone()
            index = pc.Index(settings.pinecone_index_name)

            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
                filter=filter_dict,
            )
            logger.debug(f"[RAG] Pinecone查询成功, 匹配数={len(results.get('matches', []))}")
        except Exception as e:
            logger.error(f"[RAG] Pinecone查询失败: {str(e)}\n{traceback.format_exc()}")
            raise

        return [
            {
                "id": match["id"],
                "score": match["score"],
                "text": match.get("metadata", {}).get("text", ""),
                "metadata": match.get("metadata", {}),
            }
            for match in results.get("matches", [])
        ]

    async def rag_query(
        self,
        query: str,
        model_key: str = "deepseek",
        symbol: Optional[str] = None,
        namespace: str = "news",
        top_k: int = 5,
    ) -> dict:
        """Full RAG pipeline: embed query -> retrieve -> generate."""
        logger.info(f"[RAG] 开始RAG查询 model={model_key}, symbol={symbol}, namespace={namespace}, top_k={top_k}")
        logger.debug(f"[RAG] 查询内容: {query[:200]}...")

        filter_dict = None
        if symbol:
            filter_dict = {"symbol": symbol}

        try:
            logger.debug(f"[RAG] 开始向量检索")
            results = await self.query(query, top_k=top_k, namespace=namespace, filter_dict=filter_dict)
            logger.info(f"[RAG] 向量检索完成, 找到 {len(results)} 个相关文档")
            for i, r in enumerate(results):
                logger.debug(f"[RAG] 文档{i+1}: score={r.get('score', 'N/A'):.4f}, source={r.get('metadata', {}).get('source', 'unknown')}")
        except Exception as e:
            logger.error(f"[RAG] 向量检索失败: {str(e)}\n{traceback.format_exc()}")
            raise

        context = "\n\n---\n\n".join(
            [f"[Source: {r['metadata'].get('source', 'unknown')}]\n{r['text']}" for r in results]
        )

        if not context.strip():
            context = "No relevant documents found in the knowledge base."
            logger.warning(f"[RAG] 未找到相关文档，使用默认上下文")

        try:
            logger.debug(f"[RAG] 开始生成回答, 上下文长度={len(context)}")
            prompt = RAG_QUERY_PROMPT.format(context=context, query=query)
            messages = [{"role": "user", "content": prompt}]

            response = await llm_provider.chat(model_key, messages)
            logger.info(f"[RAG] 生成回答成功, tokens={response.get('total_tokens')}")
        except Exception as e:
            logger.error(f"[RAG] 生成回答失败: {str(e)}\n{traceback.format_exc()}")
            raise

        return {
            "answer": response["content"],
            "sources": results,
            "model_used": model_key,
            "tokens_used": response["total_tokens"],
            "cost_usd": response.get("cost_usd", 0),
        }


rag_pipeline = RAGPipeline()
