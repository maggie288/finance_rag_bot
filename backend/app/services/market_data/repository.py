from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stock_data import StockQuote, StockKline, StockFundamental
from app.schemas.market import StockQuote as StockQuoteSchema, KlinePoint

logger = logging.getLogger(__name__)


class StockDataRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_quote(self, symbol: str, market: str) -> Optional[StockQuoteSchema]:
        stmt = select(StockQuote).where(
            StockQuote.symbol == symbol,
            StockQuote.market == market
        )
        result = await self.db.execute(stmt)
        db_quote = result.scalar_one_or_none()

        if db_quote:
            return StockQuoteSchema(
                symbol=db_quote.symbol,
                name=db_quote.name,
                market=db_quote.market,
                price=db_quote.price,
                change=db_quote.change,
                change_percent=db_quote.change_percent,
                volume=db_quote.volume,
                high=db_quote.high,
                low=db_quote.low,
                open=db_quote.open,
                prev_close=db_quote.prev_close,
                timestamp=db_quote.timestamp,
            )
        return None

    async def save_quote(self, quote: StockQuoteSchema) -> None:
        stmt = select(StockQuote).where(
            StockQuote.symbol == quote.symbol,
            StockQuote.market == quote.market
        )
        result = await self.db.execute(stmt)
        db_quote = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if db_quote:
            if quote.name:
                db_quote.name = quote.name
            db_quote.price = quote.price
            db_quote.change = quote.change
            db_quote.change_percent = quote.change_percent
            db_quote.volume = quote.volume
            db_quote.high = quote.high
            db_quote.low = quote.low
            db_quote.open = quote.open
            db_quote.prev_close = quote.prev_close
            db_quote.timestamp = quote.timestamp
            db_quote.updated_at = now
        else:
            db_quote = StockQuote(
                symbol=quote.symbol,
                market=quote.market,
                name=quote.name,
                price=quote.price,
                change=quote.change,
                change_percent=quote.change_percent,
                volume=quote.volume,
                high=quote.high,
                low=quote.low,
                open=quote.open,
                prev_close=quote.prev_close,
                timestamp=quote.timestamp,
            )
            self.db.add(db_quote)

        await self.db.commit()

    async def get_klines(
        self,
        symbol: str,
        market: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[KlinePoint]:
        query = select(StockKline).where(
            StockKline.symbol == symbol,
            StockKline.market == market,
            StockKline.interval == interval,
        )

        if start_time:
            query = query.where(StockKline.datetime >= start_time)
        if end_time:
            query = query.where(StockKline.datetime <= end_time)

        query = query.order_by(StockKline.datetime.desc()).limit(limit)

        result = await self.db.execute(query)
        db_klines = result.scalars().all()

        return [
            KlinePoint(
                datetime=k.datetime.isoformat(),
                open=k.open,
                high=k.high,
                low=k.low,
                close=k.close,
                volume=k.volume,
            )
            for k in db_klines
        ]

    async def save_klines(
        self,
        symbol: str,
        market: str,
        interval: str,
        klines: List[KlinePoint],
    ) -> None:
        now = datetime.now(timezone.utc)
        existing_keys = set()

        if klines:
            for kline in klines:
                kline_dt = datetime.fromisoformat(kline.datetime.replace("Z", "+00:00"))
                stmt = select(StockKline).where(
                    StockKline.symbol == symbol,
                    StockKline.market == market,
                    StockKline.interval == interval,
                    StockKline.datetime == kline_dt,
                )
                result = await self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                key = f"{symbol}:{market}:{interval}:{kline_dt.isoformat()}"
                existing_keys.add(key)

                if existing:
                    existing.open = kline.open
                    existing.high = kline.high
                    existing.low = kline.low
                    existing.close = kline.close
                    existing.volume = kline.volume
                    existing.updated_at = now
                else:
                    db_kline = StockKline(
                        symbol=symbol,
                        market=market,
                        interval=interval,
                        datetime=kline_dt,
                        open=kline.open,
                        high=kline.high,
                        low=kline.low,
                        close=kline.close,
                        volume=kline.volume,
                    )
                    self.db.add(db_kline)

        await self.db.commit()

    async def get_fundamentals(self, symbol: str, market: str) -> Optional[dict]:
        stmt = select(StockFundamental).where(
            StockFundamental.symbol == symbol,
            StockFundamental.market == market,
        )
        result = await self.db.execute(stmt)
        db_fund = result.scalar_one_or_none()

        if db_fund:
            return {
                "symbol": db_fund.symbol,
                "market": db_fund.market,
                "pe_ratio": db_fund.pe_ratio,
                "pb_ratio": db_fund.pb_ratio,
                "roe": db_fund.roe,
                "debt_ratio": db_fund.debt_ratio,
                "revenue_growth": db_fund.revenue_growth,
                "net_profit_margin": db_fund.net_profit_margin,
                "market_cap": db_fund.market_cap,
                "dividend_yield": db_fund.dividend_yield,
                "eps": db_fund.eps,
                "revenue": db_fund.revenue,
                "net_income": db_fund.net_income,
                "total_debt": db_fund.total_debt,
                "total_cash": db_fund.total_cash,
                "operating_cash_flow": db_fund.operating_cash_flow,
                "free_cash_flow": db_fund.free_cash_flow,
            }
        return None

    async def save_fundamentals(self, symbol: str, market: str, data: dict) -> None:
        stmt = select(StockFundamental).where(
            StockFundamental.symbol == symbol,
            StockFundamental.market == market,
        )
        result = await self.db.execute(stmt)
        db_fund = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        data_copy = data.copy()
        data_copy.pop('symbol', None)
        data_copy.pop('market', None)
        
        if db_fund:
            for key, value in data_copy.items():
                if hasattr(db_fund, key):
                    setattr(db_fund, key, value)
            db_fund.updated_at = now
        else:
            db_fund = StockFundamental(symbol=symbol, market=market, **data_copy)
            self.db.add(db_fund)

        await self.db.commit()

    async def get_quotes_updated_before(
        self, market: str, before_minutes: int = 5
    ) -> List[StockQuote]:
        threshold = datetime.now(timezone.utc) - timedelta(minutes=before_minutes)
        stmt = select(StockQuote).where(
            StockQuote.market == market,
            StockQuote.updated_at < threshold,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_quotes(self, market: Optional[str] = None) -> List[StockQuote]:
        stmt = select(StockQuote)
        if market:
            stmt = stmt.where(StockQuote.market == market)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_quote(self, symbol: str, market: str) -> bool:
        stmt = select(StockQuote).where(
            StockQuote.symbol == symbol,
            StockQuote.market == market,
        )
        result = await self.db.execute(stmt)
        db_quote = result.scalar_one_or_none()

        if db_quote:
            await self.db.delete(db_quote)
            await self.db.commit()
            return True
        return False

    async def delete_klines(
        self, symbol: str, market: str, interval: str, keep_latest: int = 500
    ) -> int:
        subq = (
            select(StockKline.id)
            .where(
                StockKline.symbol == symbol,
                StockKline.market == market,
                StockKline.interval == interval,
            )
            .order_by(StockKline.datetime.desc())
            .limit(keep_latest)
        )
        stmt = select(StockKline).where(
            StockKline.symbol == symbol,
            StockKline.market == market,
            StockKline.interval == interval,
            ~StockKline.id.in_(subq),
        )
        result = await self.db.execute(stmt)
        to_delete = result.scalars().all()

        count = len(to_delete)
        for kline in to_delete:
            await self.db.delete(kline)

        if count > 0:
            await self.db.commit()

        return count
