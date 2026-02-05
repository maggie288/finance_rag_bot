from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from functools import partial
from typing import Optional, List
from app.config import settings
from app.schemas.market import StockQuote, KlinePoint, FundamentalData
from app.services.market_data.base import MarketDataProvider

logger = logging.getLogger(__name__)


class TuShareProvider(MarketDataProvider):
    def __init__(self):
        self.token = settings.tushare_token
        self._api = None
        self._hk_name_cache: dict = {}
        self._cn_name_cache: dict = {}
        self._etf_name_cache: dict = {}

    def _get_api(self):
        if self._api is None:
            import tushare as ts
            self._api = ts.pro_api(self.token)
        return self._api

    def _code_to_ts(self, symbol: str) -> str:
        if symbol.endswith(".HK"):
            return symbol
        return symbol

    def _is_etf(self, symbol: str) -> bool:
        code = symbol.split(".")[0]
        if len(code) != 6:
            return False
        prefix = code[:2]
        try:
            num = int(prefix)
            return (50 <= num <= 51 or 15 <= num <= 16)
        except ValueError:
            return False

    async def _get_hk_name(self, symbol: str) -> Optional[str]:
        if symbol in self._hk_name_cache:
            return self._hk_name_cache[symbol]
        
        api = self._get_api()
        loop = asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(
                None,
                lambda: api.hk_basic(ts_code=symbol)
            )
            if data is not None and len(data) > 0:
                name = data.iloc[0].get("name", "")
                self._hk_name_cache[symbol] = name
                logger.info(f"[TuShare] 获取港股名称: {symbol} -> {name}")
                return name
        except Exception as e:
            logger.warning(f"[TuShare] 获取港股名称失败 {symbol}: {e}")
        return None

    async def _get_cn_name(self, symbol: str) -> Optional[str]:
        if symbol in self._cn_name_cache:
            return self._cn_name_cache[symbol]
        
        api = self._get_api()
        loop = asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(
                None,
                lambda: api.stock_basic(ts_code=symbol, fields="ts_code,name")
            )
            if data is not None and len(data) > 0:
                name = data.iloc[0].get("name", "")
                self._cn_name_cache[symbol] = name
                logger.info(f"[TuShare] 获取A股名称: {symbol} -> {name}")
                return name
        except Exception as e:
            logger.warning(f"[TuShare] 获取A股名称失败 {symbol}: {e}")
        return None

    async def _get_etf_name(self, symbol: str) -> Optional[str]:
        if symbol in self._etf_name_cache:
            return self._etf_name_cache[symbol]
        
        api = self._get_api()
        loop = asyncio.get_event_loop()
        
        try:
            data = await loop.run_in_executor(
                None,
                lambda: api.fund_basic(ts_code=symbol)
            )
            if data is not None and len(data) > 0:
                name = data.iloc[0].get("name", "")
                self._etf_name_cache[symbol] = name
                logger.info(f"[TuShare] 获取ETF名称: {symbol} -> {name}")
                return name
        except Exception as e:
            logger.warning(f"[TuShare] 获取ETF名称失败 {symbol}: {e}")
        return None

    async def get_quote(self, symbol: str) -> StockQuote:
        logger.info(f"[TuShare] get_quote: symbol={symbol}")

        api = self._get_api()
        ts_code = self._code_to_ts(symbol)

        loop = asyncio.get_event_loop()
        is_hk = symbol.endswith(".HK")
        is_etf = self._is_etf(symbol)

        name = None
        try:
            if is_hk:
                data = await loop.run_in_executor(
                    None,
                    lambda: api.hk_daily(ts_code=ts_code)
                )
                if data is not None and len(data) > 0:
                    name = await self._get_hk_name(ts_code)
            elif is_etf:
                data = await loop.run_in_executor(
                    None,
                    lambda: api.fund_daily(ts_code=ts_code)
                )
                if data is not None and len(data) > 0:
                    name = await self._get_etf_name(ts_code)
            else:
                data = await loop.run_in_executor(
                    None,
                    lambda: api.daily(ts_code=ts_code)
                )
                if data is not None and len(data) > 0:
                    name = await self._get_cn_name(ts_code)
        except Exception as e:
            logger.error(f"[TuShare] Failed to get quote: {e}")
            raise ValueError(f"TuShare API error for {symbol}: {str(e)}")

        if data is None or len(data) == 0:
            raise ValueError(f"No data for {symbol}")

        row = data.iloc[0]
        market = "hk" if is_hk else "cn"

        return StockQuote(
            symbol=symbol,
            name=name,
            market=market,
            price=float(row.get("close", 0)),
            change=float(row.get("change", 0)) if row.get("change") else None,
            change_percent=float(row.get("pct_chg", 0)) if row.get("pct_chg") else None,
            volume=int(row.get("vol", 0)) if row.get("vol") else None,
            high=float(row.get("high", 0)) if row.get("high") else None,
            low=float(row.get("low", 0)) if row.get("low") else None,
            open=float(row.get("open", 0)) if row.get("open") else None,
            prev_close=float(row.get("pre_close", 0)) if row.get("pre_close") else None,
            timestamp=datetime.strptime(row.get("trade_date"), "%Y%m%d") if row.get("trade_date") else None,
        )

    async def get_kline(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 100,
    ) -> List[KlinePoint]:
        logger.info(f"[TuShare] get_kline: symbol={symbol}, interval={interval}")

        api = self._get_api()
        ts_code = self._code_to_ts(symbol)

        is_hk = symbol.endswith(".HK")

        interval_map = {
            "1day": "daily",
            "1week": "weekly",
            "1month": "monthly",
        }
        freq = interval_map.get(interval, "daily")

        loop = asyncio.get_event_loop()

        try:
            if is_hk:
                if freq == "daily":
                    data = await loop.run_in_executor(
                        None,
                        lambda: api.hk_daily(ts_code=ts_code, limit=outputsize)
                    )
                else:
                    logger.warning(f"[TuShare] HK stock only supports daily interval currently")
                    data = await loop.run_in_executor(
                        None,
                        lambda: api.hk_daily(ts_code=ts_code, limit=outputsize)
                    )
            else:
                if freq == "daily":
                    data = await loop.run_in_executor(
                        None,
                        lambda: api.daily(ts_code=ts_code, limit=outputsize)
                    )
                elif freq == "weekly":
                    data = await loop.run_in_executor(
                        None,
                        lambda: api.weekly(ts_code=ts_code, limit=outputsize)
                    )
                elif freq == "monthly":
                    data = await loop.run_in_executor(
                        None,
                        lambda: api.monthly(ts_code=ts_code, limit=outputsize)
                    )
                else:
                    data = await loop.run_in_executor(
                        None,
                        lambda: api.daily(ts_code=ts_code, limit=outputsize)
                    )
        except Exception as e:
            logger.error(f"[TuShare] Failed to get kline: {e}")
            raise ValueError(f"TuShare API error for {symbol}: {str(e)}")

        if data is None or len(data) == 0:
            raise ValueError(f"No kline data for {symbol}")

        result = []
        for _, row in data.iterrows():
            dt = datetime.strptime(row.get("trade_date"), "%Y%m%d")
            result.append(
                KlinePoint(
                    datetime=dt.isoformat(),
                    open=float(row.get("open", 0)),
                    high=float(row.get("high", 0)),
                    low=float(row.get("low", 0)),
                    close=float(row.get("close", 0)),
                    volume=int(row.get("vol", 0)) if row.get("vol") else None,
                )
            )

        return result

    async def search(self, query: str) -> List[dict]:
        logger.info(f"[TuShare] search: query={query}")

        api = self._get_api()
        loop = asyncio.get_event_loop()

        try:
            data = await loop.run_in_executor(
                None,
                lambda: api.stock_basic(ts_code=query, exchange="", fields="ts_code,symbol,name,exchange,list_status")
            )
            if data is None or len(data) == 0:
                data = await loop.run_in_executor(
                    None,
                    lambda: api.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,exchange,list_status")
                )
                data = data[data["name"].str.contains(query, na=False) | data["symbol"].str.contains(query, na=False)]
        except Exception as e:
            logger.warning(f"[TuShare] Search failed: {e}")
            return []

        return [
            {
                "symbol": f"{row['ts_code'].replace('-', '.')}",
                "name": row["name"],
                "type": "stock",
                "exchange": row["exchange"],
                "country": "China",
            }
            for _, row in data.head(10).iterrows()
        ]

    async def get_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        logger.info(f"[TuShare] get_fundamentals: symbol={symbol}")

        api = self._get_api()
        ts_code = self._code_to_ts(symbol)
        loop = asyncio.get_event_loop()

        try:
            info = await loop.run_in_executor(
                None,
                lambda: api.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,market,exchange,list_status")
            )

            daily = await loop.run_in_executor(
                None,
                lambda: api.daily(ts_code=ts_code, limit=1)
            )

            if info is None or len(info) == 0:
                return None

            info_row = info.iloc[0]

            return FundamentalData(
                symbol=symbol,
                market="cn",
                market_cap=daily.iloc[0].get("total_share") * daily.iloc[0].get("close") if len(daily) > 0 else None,
                eps=daily.iloc[0].get("close") / info_row.get("pe") if len(daily) > 0 and info_row.get("pe") else None,
            )
        except Exception as e:
            logger.warning(f"[TuShare] Failed to get fundamentals: {e}")
            return None
