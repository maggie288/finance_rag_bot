from __future__ import annotations

import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.market import StockQuote, KlineResponse, FundamentalData
from app.services.market_data.aggregator import market_data
from app.services.market_data.repository import StockDataRepository
from app.services.market_data.scheduler import trigger_manual_refresh

router = APIRouter(prefix="/market", tags=["market"])


class BatchQuoteItem(BaseModel):
    symbol: str
    market: Optional[str] = None


class BatchQuoteRequest(BaseModel):
    items: List[BatchQuoteItem]


class ForceRefreshRequest(BaseModel):
    symbols: List[BatchQuoteItem]
    refresh_klines: bool = False


@router.get("/quote", response_model=StockQuote)
async def get_quote(
    symbol: str = Query(..., description="Stock symbol, e.g., TSLA, 0700.HK, 600519.SH"),
    market: Optional[str] = Query(None, description="Market: us, hk, cn, commodity"),
    use_db: bool = Query(True, description="Use database cache if available"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if use_db:
            return await market_data.get_quote(symbol, market, db)
        return await market_data.get_quote(symbol, market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get quote: {str(e)}")


@router.get("/kline", response_model=KlineResponse)
async def get_kline(
    symbol: str = Query(...),
    market: Optional[str] = Query(None),
    interval: str = Query("1day", description="1min, 5min, 15min, 30min, 1h, 1day, 1week, 1month"),
    outputsize: int = Query(100, ge=1, le=5000),
    use_db: bool = Query(True, description="Use database cache if available"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if not market:
            market = market_data._detect_market(symbol)
        data = await market_data.get_kline(symbol, market, interval, outputsize, db if use_db else None)
        return KlineResponse(symbol=symbol, market=market, interval=interval, data=data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get kline: {str(e)}")


@router.get("/search")
async def search_symbols(
    query: str = Query(..., min_length=1),
    market: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
):
    try:
        return await market_data.search(query, market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")


@router.post("/batch-quote")
async def batch_quote(
    req: BatchQuoteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(req.items) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 symbols per batch")

    async def _fetch(item: BatchQuoteItem) -> Optional[dict]:
        try:
            quote = await market_data.get_quote(item.symbol, item.market, db)
            return quote.model_dump()
        except Exception:
            return None

    results = await asyncio.gather(*[_fetch(item) for item in req.items])
    return {"quotes": [r for r in results if r is not None]}


@router.get("/fundamentals", response_model=FundamentalData)
async def get_fundamentals(
    symbol: str = Query(...),
    market: Optional[str] = Query(None),
    use_db: bool = Query(True, description="Use database cache if available"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await market_data.get_fundamentals(symbol, market, db if use_db else None)
        if not data:
            raise HTTPException(status_code=404, detail="Fundamental data not available")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get fundamentals: {str(e)}")


@router.post("/refresh")
async def refresh_market_data(
    background_tasks: BackgroundTasks,
    market: Optional[str] = Query(None, description="Specific market to refresh, or all"),
    user: User = Depends(get_current_user),
):
    background_tasks.add_task(trigger_manual_refresh, market)
    return {"message": f"Market data refresh triggered for {market or 'all markets'}"}


@router.post("/force-refresh")
async def force_refresh_quotes(
    req: ForceRefreshRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = []
    for item in req.symbols:
        try:
            quote = await market_data.get_quote(item.symbol, item.market, db, force_refresh=True)
            results.append({"symbol": item.symbol, "success": True, "quote": quote.model_dump()})
        except Exception as e:
            results.append({"symbol": item.symbol, "success": False, "error": str(e)})

    return {"results": results}


@router.get("/cache/status")
async def get_cache_status(
    market: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = StockDataRepository(db)
    all_quotes = await repo.get_all_quotes(market=market)

    return {
        "total_symbols": len(all_quotes),
        "market": market or "all",
        "symbols": [
            {
                "symbol": q.symbol,
                "market": q.market,
                "price": q.price,
                "updated_at": q.updated_at.isoformat() if q.updated_at else None,
            }
            for q in all_quotes
        ],
    }
