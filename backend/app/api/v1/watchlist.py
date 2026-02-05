from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.market_data.aggregator import market_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistAddRequest(BaseModel):
    symbol: str
    market: str
    name: Optional[str] = None


@router.get("/")
async def get_watchlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == user.id)
        .order_by(Watchlist.sort_order)
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": str(item.id),
                "symbol": item.symbol,
                "market": item.market,
                "name": item.name,
                "sort_order": item.sort_order,
            }
            for item in items
        ]
    }


@router.post("/")
async def add_to_watchlist(
    req: WatchlistAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user.id,
            Watchlist.symbol == req.symbol,
            Watchlist.market == req.market,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in watchlist")

    item = Watchlist(
        user_id=user.id,
        symbol=req.symbol,
        market=req.market,
        name=req.name,
    )
    db.add(item)
    await db.flush()
    logger.info(f"[Watchlist] 添加股票: {item.symbol}, 请求名称: {req.name}")

    try:
        quote = await market_data.get_quote(req.symbol, req.market, db, force_refresh=True)
        logger.info(f"[Watchlist] 行情API返回: {quote.name}")
        if quote and quote.name:
            item.name = quote.name
            logger.info(f"[Watchlist] 更新数据库名称: {quote.name}")
            await db.commit()
            await db.refresh(item)
            logger.info(f"[Watchlist] 已保存股票名称: {item.name}")
    except Exception as e:
        logger.warning(f"[Watchlist] 获取行情失败: {e}")

    return {"id": str(item.id), "symbol": item.symbol, "market": item.market, "name": item.name}


@router.delete("/{item_id}")
async def remove_from_watchlist(
    item_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(Watchlist).where(
            Watchlist.id == item_id,
            Watchlist.user_id == user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Removed from watchlist"}


@router.post("/refresh-names")
async def refresh_watchlist_names(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"[Watchlist] 开始刷新用户 {user.id} 的股票名称")
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id)
    )
    items = result.scalars().all()
    logger.info(f"[Watchlist] 用户共有 {len(items)} 个自选股")
    refreshed = []
    for item in items:
        logger.info(f"[Watchlist] 处理股票: {item.symbol}, 当前市场: {item.market}, 当前名称: {item.name}")
        try:
            quote = await market_data.get_quote(item.symbol, item.market, db, force_refresh=False)
            logger.info(f"[Watchlist] API返回结果: symbol={quote.symbol}, name={quote.name}, market={quote.market}")
            if quote and quote.name and quote.name != item.name:
                logger.info(f"[Watchlist] 更新 {item.symbol} 名称: '{item.name}' -> '{quote.name}'")
                item.name = quote.name
                await db.commit()
                await db.refresh(item)
                refreshed.append({"symbol": item.symbol, "name": quote.name})
                logger.info(f"[Watchlist] 已刷新 {item.symbol}: {item.name}")
            else:
                if not quote:
                    logger.warning(f"[Watchlist] 无法获取 {item.symbol} 的行情数据")
                elif not quote.name:
                    logger.warning(f"[Watchlist] API返回的名称为空 (quote.name=None)")
                elif quote.name == item.name:
                    logger.info(f"[Watchlist] 名称相同，跳过")
        except Exception as e:
            logger.error(f"[Watchlist] 刷新 {item.symbol} 失败: {e}")
    logger.info(f"[Watchlist] 完成刷新，共更新 {len(refreshed)} 个股票")
    return {"message": f"Refreshed {len(refreshed)} stock names", "refreshed": refreshed}
