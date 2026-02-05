from __future__ import annotations

import asyncio
import json
import logging
from functools import partial
from typing import Optional, List
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.schemas.market import StockQuote, KlinePoint, FundamentalData
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.twelvedata import TwelveDataProvider
from app.services.market_data.tushare_provider import TuShareProvider
from app.services.market_data.repository import StockDataRepository
from app.services.market_data.estimator import MarketDataEstimator

logger = logging.getLogger(__name__)

QUOTE_FRESHNESS_MINUTES = 5
KLINE_FRESHNESS_MINUTES = {
    "1min": 1,
    "5min": 5,
    "1day": 60,
    "1week": 60,
    "1month": 60,
}
FUNDAMENTAL_FRESHNESS_HOURS = 24


class MarketDataAggregator:
    def __init__(self):
        self.twelvedata = TwelveDataProvider()
        self.tushare = TuShareProvider()
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def _get_provider(self, market: str) -> MarketDataProvider:
        if market in ("cn", "hk"):
            return self.tushare
        return self.twelvedata

    def _detect_market(self, symbol: str) -> str:
        symbol_upper = symbol.upper()
        if symbol_upper.endswith(".SH") or symbol_upper.endswith(".SZ"):
            return "cn"
        if symbol_upper.endswith(".HK"):
            return "hk"
        if "/" in symbol:
            return "commodity"
        return "us"

    async def get_quote(
        self,
        symbol: str,
        market: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        force_refresh: bool = False,
    ) -> StockQuote:
        if not market:
            market = self._detect_market(symbol)

        if db:
            repo = StockDataRepository(db)
            if not force_refresh:
                cached_quote = await repo.get_quote(symbol, market)
                if cached_quote:
                    logger.info(f"[DB] Cache hit for quote: {symbol}")
                    redis = await self._get_redis()
                    cache_key = f"quote:{market}:{symbol}"
                    await redis.set(
                        cache_key,
                        cached_quote.model_dump_json(),
                        ex=QUOTE_FRESHNESS_MINUTES * 60,
                    )
                    return cached_quote

        provider = self._get_provider(market)
        try:
            quote = await provider.get_quote(symbol)
            logger.info(f"[API] Fetched quote from API: {symbol}")
        except Exception as e:
            if db:
                cached_quote = await repo.get_quote(symbol, market)
                if cached_quote:
                    logger.warning(f"[API] Failed, using stale DB data: {symbol}")
                    return cached_quote
            raise e

        if db:
            try:
                await repo.save_quote(quote)
                logger.info(f"[DB] Saved quote to DB: {symbol}")
            except Exception as e:
                logger.error(f"[DB] Failed to save quote: {e}")

        redis = await self._get_redis()
        cache_key = f"quote:{market}:{symbol}"
        await redis.set(cache_key, quote.model_dump_json(), ex=QUOTE_FRESHNESS_MINUTES * 60)

        return quote

    async def get_kline(
        self,
        symbol: str,
        market: Optional[str] = None,
        interval: str = "1day",
        outputsize: int = 100,
        db: Optional[AsyncSession] = None,
        force_refresh: bool = False,
    ) -> List[KlinePoint]:
        if not market:
            market = self._detect_market(symbol)

        if db and not force_refresh:
            repo = StockDataRepository(db)
            freshness = KLINE_FRESHNESS_MINUTES.get(interval, 60)
            from datetime import datetime, timezone, timedelta
            start_time = datetime.now(timezone.utc) - timedelta(minutes=freshness)

            cached_klines = await repo.get_klines(
                symbol, market, interval,
                start_time=start_time,
                limit=outputsize,
            )
            if cached_klines and len(cached_klines) >= outputsize:
                logger.info(f"[DB] Cache hit for kline: {symbol} {interval}")
                redis = await self._get_redis()
                cache_key = f"kline:{market}:{symbol}:{interval}:{outputsize}"
                await redis.set(
                    cache_key,
                    json.dumps([k.model_dump() for k in cached_klines]),
                    ex=freshness * 60,
                )
                return cached_klines

        provider = self._get_provider(market)
        try:
            kline = await provider.get_kline(symbol, interval, outputsize)
            logger.info(f"[API] Fetched kline from API: {symbol} {interval}")
        except Exception as e:
            if db:
                all_klines = await repo.get_klines(symbol, market, interval, limit=outputsize)
                if all_klines:
                    logger.warning(f"[API] Failed, using stale DB data: {symbol}")
                    return all_klines
            raise e

        if db:
            try:
                await repo.save_klines(symbol, market, interval, kline)
                logger.info(f"[DB] Saved klines to DB: {symbol} {interval}")

                if market == "cn" and kline:
                    from datetime import datetime
                    try:
                        code = symbol.split(".")[0]
                        import akshare as ak
                        info = await asyncio.get_event_loop().run_in_executor(
                            None, partial(ak.stock_individual_info_em, symbol=code)
                        )
                        if info is not None and not info.empty:
                            name = info.iloc[0].get("股票名称") or info.iloc[0].get("名称")
                            if name:
                                from app.schemas.market import StockQuote
                                quote = StockQuote(
                                    symbol=symbol,
                                    name=str(name),
                                    market=market,
                                    price=kline[-1].close if kline else 0,
                                )
                                await repo.save_quote(quote)
                                logger.info(f"[DB] Saved quote name for {symbol}: {name}")
                    except Exception as e:
                        logger.warning(f"[DB] Failed to save quote name for {symbol}: {e}")
            except Exception as e:
                logger.error(f"[DB] Failed to save klines: {e}")

        ttl_map = {"1min": 60, "5min": 60, "1day": 14400, "1week": 14400, "1month": 14400}
        ttl = ttl_map.get(interval, 3600)
        redis = await self._get_redis()
        cache_key = f"kline:{market}:{symbol}:{interval}:{outputsize}"
        await redis.set(cache_key, json.dumps([k.model_dump() for k in kline]), ex=ttl)

        return kline

    async def search(self, query: str, market: Optional[str] = None) -> List[dict]:
        results = []
        if not market or market == "cn":
            try:
                cn_results = await self.tushare.search(query)
                results.extend(cn_results)
            except Exception:
                pass

        if not market or market in ("us", "hk", "commodity"):
            try:
                td_results = await self.twelvedata.search(query)
                results.extend(td_results)
            except Exception:
                pass

        return results

    async def get_fundamentals(
        self,
        symbol: str,
        market: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        force_refresh: bool = False,
    ) -> Optional[FundamentalData]:
        if not market:
            market = self._detect_market(symbol)

        if db and not force_refresh:
            repo = StockDataRepository(db)
            cached_data = await repo.get_fundamentals(symbol, market)
            if cached_data:
                logger.info(f"[DB] Cache hit for fundamentals: {symbol}")
                return FundamentalData(**cached_data)

        provider = self._get_provider(market)
        try:
            data = await provider.get_fundamentals(symbol)
            logger.info(f"[API] Fetched fundamentals from API: {symbol}")
        except Exception as e:
            if db:
                cached_data = await repo.get_fundamentals(symbol, market)
                if cached_data:
                    logger.warning(f"[API] Failed, using stale DB data: {symbol}")
                    return FundamentalData(**cached_data)
            logger.warning(f"[API] Failed to get fundamentals: {e}")
            data = None

        # 如果提供商没有返回数据，尝试基于行情数据估算
        if not data:
            logger.info(f"[Estimator] Attempting to estimate fundamentals from market data: {symbol}")
            try:
                # 获取实时行情
                quote = None
                try:
                    quote = await self.get_quote(symbol, market, db)
                except Exception as qe:
                    logger.warning(f"[Estimator] Failed to get quote: {qe}")

                # 获取K线数据（至少60天用于估算）
                kline_data = None
                try:
                    kline_data = await self.get_kline(
                        symbol, market, interval="1day", outputsize=100, db=db
                    )
                except Exception as ke:
                    logger.warning(f"[Estimator] Failed to get kline: {ke}")

                # 使用估算器生成基本面估算
                if quote or kline_data:
                    data = MarketDataEstimator.estimate_from_market_data(
                        symbol, market, quote, kline_data
                    )
                    if data:
                        logger.info(f"[Estimator] Successfully estimated fundamentals for {symbol}")
                    else:
                        logger.warning(f"[Estimator] Failed to estimate fundamentals for {symbol}")
            except Exception as est_error:
                logger.error(f"[Estimator] Error during estimation: {est_error}")

        if db and data:
            try:
                await repo.save_fundamentals(symbol, market, data.model_dump())
                logger.info(f"[DB] Saved fundamentals to DB: {symbol}")
            except Exception as e:
                logger.error(f"[DB] Failed to save fundamentals: {e}")

        return data

    async def batch_refresh_quotes(
        self, symbols: List[dict], db: AsyncSession
    ) -> List[StockQuote]:
        results = []
        for item in symbols:
            symbol = item.get("symbol")
            market = item.get("market") or self._detect_market(symbol)
            try:
                quote = await self.get_quote(symbol, market, db, force_refresh=True)
                results.append(quote)
            except Exception as e:
                logger.error(f"[Batch] Failed to refresh {symbol}: {e}")
        return results

    async def refresh_user_watchlist(
        self, watchlist_items: List[dict], db: AsyncSession
    ) -> dict:
        success_count = 0
        fail_count = 0
        updated_symbols = []

        for item in watchlist_items:
            symbol = item.get("symbol")
            market = item.get("market") or self._detect_market(symbol)
            try:
                quote = await self.get_quote(symbol, market, db, force_refresh=True)
                success_count += 1
                updated_symbols.append(symbol)
            except Exception as e:
                fail_count += 1
                logger.error(f"[Watchlist] Failed to refresh {symbol}: {e}")

        return {
            "success": success_count,
            "failed": fail_count,
            "updated_symbols": updated_symbols,
        }


market_data = MarketDataAggregator()
