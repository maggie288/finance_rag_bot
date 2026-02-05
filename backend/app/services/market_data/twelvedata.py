from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional, List
import httpx
import yfinance as yf
from functools import partial
from yahooquery import Ticker
from app.config import settings
from app.schemas.market import StockQuote, KlinePoint, FundamentalData
from app.services.market_data.base import MarketDataProvider

logger = logging.getLogger(__name__)
BASE_URL = "https://api.twelvedata.com"


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class TwelveDataProvider(MarketDataProvider):
    def __init__(self):
        self.api_key = settings.twelvedata_api_key

    def _params(self, **kwargs) -> dict:
        return {"apikey": self.api_key, **kwargs}

    async def get_quote(self, symbol: str) -> StockQuote:
        logger.info(f"[TwelveData] get_quote: symbol={symbol}")
        
        if "/" in symbol:
            return await self._get_crypto_quote(symbol)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/quote",
                params=self._params(symbol=symbol),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info(f"[TwelveData] get_quote response: {data}")

        if data.get("status") == "error":
            error_msg = data.get("message", "Unknown error")
            raise ValueError(f"TwelveData API error for {symbol}: {error_msg}")

        market = "us"
        if ".HK" in symbol.upper():
            market = "hk"
        elif "/" in symbol:
            market = "commodity"

        return StockQuote(
            symbol=data.get("symbol", symbol),
            name=data.get("name"),
            market=market,
            price=float(data.get("close", 0)),
            change=float(data.get("change", 0)) if data.get("change") else None,
            change_percent=float(data.get("percent_change", 0)) if data.get("percent_change") else None,
            volume=int(data.get("volume", 0)) if data.get("volume") else None,
            high=float(data.get("high", 0)) if data.get("high") else None,
            low=float(data.get("low", 0)) if data.get("low") else None,
            open=float(data.get("open", 0)) if data.get("open") else None,
            prev_close=float(data.get("previous_close", 0)) if data.get("previous_close") else None,
        )

    async def _get_crypto_quote(self, symbol: str) -> StockQuote:
        logger.info(f"[TwelveData] _get_crypto_quote: symbol={symbol}")
        
        parts = symbol.split("/")
        base = parts[0].upper()
        quote = parts[1].upper() if len(parts) > 1 else "USD"
        
        if quote == "USD":
            quote = "USDT"
        
        trading_pair = f"{base}{quote}"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.binance.com/api/v3/ticker/24hr",
                    params={"symbol": trading_pair},
                    timeout=10,
                )
                
            if resp.status_code == 429:
                logger.warning(f"[TwelveData] Binance rate limited")
                return StockQuote(symbol=symbol, name=base, market="commodity", price=0)
            
            if resp.status_code != 200:
                logger.warning(f"[TwelveData] Binance returned {resp.status_code} for {trading_pair}")
                return StockQuote(symbol=symbol, name=symbol, market="commodity", price=0)
            
            data = resp.json()
            
            if "lastPrice" in data:
                return StockQuote(
                    symbol=symbol,
                    name=base,
                    market="commodity",
                    price=float(data.get("lastPrice", 0)),
                    change_percent=float(data.get("priceChangePercent", 0)) if data.get("priceChangePercent") else None,
                )
        except Exception as e:
            logger.error(f"[TwelveData] Failed to get crypto quote: {e}")
        
        return StockQuote(
            symbol=symbol,
            name=symbol,
            market="commodity",
            price=0,
        )

    async def get_kline(
        self, symbol: str, interval: str = "1day", outputsize: int = 100
    ) -> List[KlinePoint]:
        if "/" in symbol:
            return await self._get_crypto_kline(symbol, interval, outputsize)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/time_series",
                params=self._params(
                    symbol=symbol,
                    interval=interval,
                    outputsize=outputsize,
                    order="ASC",
                ),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") == "error":
            error_msg = data.get("message", "Unknown error")
            raise ValueError(f"TwelveData API error for {symbol}: {error_msg}")

        values = data.get("values", [])
        return [
            KlinePoint(
                datetime=v["datetime"],
                open=float(v["open"]),
                high=float(v["high"]),
                low=float(v["low"]),
                close=float(v["close"]),
                volume=int(v.get("volume", 0)) if v.get("volume") else None,
            )
            for v in values
        ]

    async def _get_crypto_kline(
        self, symbol: str, interval: str = "1day", outputsize: int = 100
    ) -> List[KlinePoint]:
        logger.info(f"[TwelveData] _get_crypto_kline: symbol={symbol}, interval={interval}")
        
        parts = symbol.split("/")
        base = parts[0].upper()
        quote = parts[1].upper() if len(parts) > 1 else "USD"
        
        if quote == "USD":
            quote = "USDT"
        
        trading_pair = f"{base}{quote}"
        
        interval_map = {
            "1min": "1m",
            "5min": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1day": "1d",
            "1week": "1w",
        }
        binance_interval = interval_map.get(interval, "1d")
        
        limit_map = {
            "1m": 1500,
            "5min": 1200,
            "15m": 1000,
            "30m": 1000,
            "1h": 1000,
            "4h": 1000,
            "1day": 1000,
            "1week": 1000,
        }
        limit = min(limit_map.get(interval, 1000), outputsize)
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.binance.com/api/v3/klines",
                    params={"symbol": trading_pair, "interval": binance_interval, "limit": limit},
                    timeout=15,
                )
            
            if resp.status_code != 200:
                logger.warning(f"[TwelveData] Binance klines returned {resp.status_code}")
                return []
            
            data = resp.json()
            
            if data:
                return [
                    KlinePoint(
                        datetime=datetime.fromtimestamp(v[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                        open=float(v[1]),
                        high=float(v[2]),
                        low=float(v[3]),
                        close=float(v[4]),
                        volume=int(float(v[5])),
                    )
                    for v in data[-outputsize:]
                ]
        except Exception as e:
            logger.error(f"[TwelveData] Failed to get crypto kline: {e}")
        
        return []

    async def search(self, query: str) -> List[dict]:
        logger.info(f"[TwelveData] search: query={query}")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/symbol_search",
                params=self._params(symbol=query, outputsize=10),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info(f"[TwelveData] search response: {data}")

        if data.get("status") == "error":
            logger.warning(f"[TwelveData] Search error: {data.get('message')}")
            return []

        return [
            {
                "symbol": item.get("symbol"),
                "name": item.get("instrument_name"),
                "type": item.get("instrument_type"),
                "exchange": item.get("exchange"),
                "country": item.get("country"),
            }
            for item in data.get("data", [])
        ]

    async def get_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        import asyncio
        
        market = "hk" if ".HK" in symbol.upper() else "us"
        
        if market == "us":
            try:
                ticker = Ticker(symbol)
                loop = asyncio.get_event_loop()
                
                stats = await loop.run_in_executor(None, lambda: ticker.key_stats)
                summary = await loop.run_in_executor(None, lambda: ticker.summary_detail)
                
                s = stats.get(symbol, {})
                sm = summary.get(symbol, {})
                
                if not s or len(s) < 3:
                    logger.warning(f"[TwelveData] yahooquery returned empty data for {symbol}")
                    return None
                
                return FundamentalData(
                    symbol=symbol,
                    market=market,
                    pe_ratio=_safe_float(s.get("trailingPE")) or _safe_float(sm.get("trailingPE")),
                    pb_ratio=_safe_float(s.get("priceToBook")),
                    market_cap=_safe_float(s.get("enterpriseValue")),
                    eps=_safe_float(s.get("trailingEps")),
                    dividend_yield=_safe_float(s.get("dividendYield")),
                    revenue=None,
                    net_income=_safe_float(s.get("netIncomeToCommon")),
                    roe=_safe_float(s.get("returnOnEquity")),
                    debt_ratio=_safe_float(s.get("debtToEquity")) if s.get("debtToEquity") else None,
                    revenue_growth=_safe_float(s.get("revenueGrowth")) if s.get("revenueGrowth") else None,
                    net_profit_margin=_safe_float(s.get("profitMargins")),
                    total_debt=_safe_float(s.get("totalDebt")) if s.get("totalDebt") else None,
                    total_cash=None,
                    operating_cash_flow=None,
                    free_cash_flow=None,
                )
            except Exception as e:
                logger.error(f"[TwelveData] yahooquery failed for {symbol}: {e}")
                return None
        else:
            logger.warning(f"[TwelveData] Fundamentals only supported for US stocks currently, symbol: {symbol}")
            return None
