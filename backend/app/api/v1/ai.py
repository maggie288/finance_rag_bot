from decimal import Decimal
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.core.credits import deduct_credits, get_credit_cost
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import AIQueryRequest, AIQueryResponse
from app.services.llm.provider import llm_provider
from app.services.rag.pipeline import rag_pipeline

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/models")
async def list_models(user: User = Depends(get_current_user)):
    return llm_provider.get_available_models()


@router.post("/chat", response_model=AIQueryResponse)
async def ai_chat(
    req: AIQueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"[AI Chat] 用户={user.id}, 模型={req.model}, use_rag={req.use_rag}, symbol={req.symbol}")
    logger.debug(f"[AI Chat] 查询内容: {req.query}")

    # Check credits
    try:
        cost = await get_credit_cost("ai_chat", req.model)
        logger.debug(f"[AI Chat] 积分消耗: {cost}")
    except Exception as e:
        logger.error(f"[AI Chat] 获取积分成本失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取积分成本失败: {str(e)}")

    try:
        transaction = await deduct_credits(
            db, user.id, cost,
            description=f"AI chat ({req.model}): {req.query[:50]}...",
            reference_type="llm_query",
        )
        if not transaction:
            logger.warning(f"[AI Chat] 用户={user.id} 积分不足")
            raise HTTPException(status_code=402, detail="Insufficient credits")
        logger.debug(f"[AI Chat] 积分扣除成功, 交易ID={transaction.id if hasattr(transaction, 'id') else 'N/A'}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI Chat] 积分扣除失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"积分扣除失败: {str(e)}")

    try:
        if req.use_rag:
            logger.info(f"[AI Chat] 使用RAG模式查询")
            result = await rag_pipeline.rag_query(
                query=req.query,
                model_key=req.model,
                symbol=req.symbol,
            )
            logger.info(f"[AI Chat] RAG查询成功, 来源数={len(result.get('sources', []))}, tokens={result.get('tokens_used')}")
            return AIQueryResponse(
                answer=result["answer"],
                sources=result["sources"],
                model_used=result["model_used"],
                tokens_used=result["tokens_used"],
                credits_cost=cost,
            )
        else:
            logger.info(f"[AI Chat] 使用直接LLM模式查询")
            messages = [{"role": "user", "content": req.query}]
            result = await llm_provider.chat(req.model, messages)
            logger.info(f"[AI Chat] LLM查询成功, tokens={result.get('total_tokens')}")
            return AIQueryResponse(
                answer=result["content"],
                sources=None,
                model_used=req.model,
                tokens_used=result["total_tokens"],
                credits_cost=cost,
            )
    except Exception as e:
        logger.error(f"[AI Chat] AI查询失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI query failed: {str(e)}")


@router.post("/chat/stream")
async def ai_chat_stream(
    req: AIQueryRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"[AI Stream] 用户={user.id}, 模型={req.model}")
    logger.debug(f"[AI Stream] 查询内容: {req.query}")

    # Check credits
    try:
        cost = await get_credit_cost("ai_chat", req.model)
    except Exception as e:
        logger.error(f"[AI Stream] 获取积分成本失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取积分成本失败: {str(e)}")

    try:
        transaction = await deduct_credits(
            db, user.id, cost,
            description=f"AI chat stream ({req.model}): {req.query[:50]}...",
            reference_type="llm_query",
        )
        if not transaction:
            logger.warning(f"[AI Stream] 用户={user.id} 积分不足")
            raise HTTPException(status_code=402, detail="Insufficient credits")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI Stream] 积分扣除失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"积分扣除失败: {str(e)}")

    messages = [{"role": "user", "content": req.query}]

    async def generate():
        chunk_count = 0
        try:
            logger.info(f"[AI Stream] 开始流式生成")
            async for chunk in llm_provider.chat_stream(req.model, messages):
                chunk_count += 1
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            logger.info(f"[AI Stream] 流式生成完成, 共 {chunk_count} 个chunk")
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"[AI Stream] 流式生成失败 (已发送 {chunk_count} chunks): {str(e)}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
