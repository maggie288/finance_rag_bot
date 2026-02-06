"""
MVP版RAG Pipeline - 使用OpenAI Embedding API替代本地模型
大幅减少镜像大小 (移除 sentence-transformers, torch, scipy 等)
"""
from __future__ import annotations

import logging
import traceback
from typing import Optional, List
from pinecone import Pinecone
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self._pinecone: Optional[Pinecone] = None
        self._openai_client: Optional[OpenAI] = None

    def _get_pinecone(self) -> Pinecone:
        if self._pinecone is None:
            self._pinecone = Pinecone(api_key=settings.pinecone_api_key)
        return self._pinecone

    def _get_openai_client(self) -> OpenAI:
        if self._openai_client is None:
            logger.info("[RAG] 初始化OpenAI客户端 (用于Embedding)")
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    async def embed_text(self, text: str) -> List[float]:
        """使用OpenAI API生成文本嵌入"""
        logger.debug(f"[RAG] 嵌入文本, 长度={len(text)}")
        try:
            client = self._get_openai_client()
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]  # OpenAI限制8192 tokens
            )
            embedding = response.data[0].embedding
            logger.debug(f"[RAG] OpenAI嵌入成功, 向量维度={len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"[RAG] OpenAI嵌入失败: {str(e)}\n{traceback.format_exc()}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量使用OpenAI API生成文本嵌入"""
        logger.debug(f"[RAG] 批量嵌入文本, 数量={len(texts)}")
        try:
            client = self._get_openai_client()
            
            # 批量处理（OpenAI限制单次请求8192 tokens）
            all_embeddings = []
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch
                )
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)
                logger.debug(f"[RAG] 已处理批次 {i//batch_size + 1}")
            
            logger.debug(f"[RAG] 批量嵌入成功, 向量维度={len(all_embeddings[0])}")
            return all_embeddings
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


rag_pipeline = RAGPipeline()
