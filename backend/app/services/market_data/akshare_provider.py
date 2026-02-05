from __future__ import annotations

from typing import Optional, List
import asyncio
from datetime import datetime
from functools import partial

from app.schemas.market import StockQuote, KlinePoint, FundamentalData
from app.services.market_data.base import MarketDataProvider


class AKShareProvider(MarketDataProvider):
    """A-share market data via AKShare (free, open-source)."""

    async def get_quote(self, symbol: str) -> StockQuote:
        import akshare as ak

        # Strip exchange suffix for AKShare (e.g., 600519.SH -> 600519)
        code = symbol.split(".")[0]

        data = await asyncio.get_event_loop().run_in_executor(
            None, partial(ak.stock_zh_a_spot_em)
        )

        row = data[data["代码"] == code]
        if row.empty:
            raise ValueError(f"A-share symbol not found: {symbol}")

        row = row.iloc[0]
        return StockQuote(
            symbol=symbol,
            name=str(row.get("名称", "")),
            market="cn",
            price=float(row.get("最新价", 0)),
            change=float(row.get("涨跌额", 0)) if row.get("涨跌额") is not None else None,
            change_percent=float(row.get("涨跌幅", 0)) if row.get("涨跌幅") is not None else None,
            volume=int(row.get("成交量", 0)) if row.get("成交量") is not None else None,
            high=float(row.get("最高", 0)) if row.get("最高") is not None else None,
            low=float(row.get("最低", 0)) if row.get("最低") is not None else None,
            open=float(row.get("今开", 0)) if row.get("今开") is not None else None,
            prev_close=float(row.get("昨收", 0)) if row.get("昨收") is not None else None,
        )

    async def get_kline(
        self, symbol: str, interval: str = "1day", outputsize: int = 100
    ) -> List[KlinePoint]:
        import akshare as ak

        code = symbol.split(".")[0]

        period_map = {
            "1min": "1",
            "5min": "5",
            "15min": "15",
            "30min": "30",
            "60min": "60",
            "1day": "daily",
            "1week": "weekly",
            "1month": "monthly",
        }
        ak_period = period_map.get(interval, "daily")

        if ak_period in ("daily", "weekly", "monthly"):
            data = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(ak.stock_zh_a_hist, symbol=code, period=ak_period, adjust="qfq"),
            )
        else:
            data = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(ak.stock_zh_a_hist_min_em, symbol=code, period=ak_period),
            )

        if data is None or data.empty:
            return []

        data = data.tail(outputsize)

        result = []
        for _, row in data.iterrows():
            dt = row.get("日期", row.get("时间", ""))
            result.append(
                KlinePoint(
                    datetime=str(dt),
                    open=float(row.get("开盘", 0)),
                    high=float(row.get("最高", 0)),
                    low=float(row.get("最低", 0)),
                    close=float(row.get("收盘", 0)),
                    volume=int(row.get("成交量", 0)) if row.get("成交量") is not None else None,
                )
            )
        return result

    async def search(self, query: str) -> List[dict]:
        import akshare as ak

        data = await asyncio.get_event_loop().run_in_executor(
            None, partial(ak.stock_zh_a_spot_em)
        )

        matches = data[
            data["代码"].str.contains(query, na=False)
            | data["名称"].str.contains(query, na=False)
        ].head(10)

        return [
            {
                "symbol": f"{row['代码']}.{'SH' if str(row['代码']).startswith('6') else 'SZ'}",
                "name": row["名称"],
                "type": "stock",
                "exchange": "SSE" if str(row["代码"]).startswith("6") else "SZSE",
                "country": "China",
            }
            for _, row in matches.iterrows()
        ]

    async def get_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        import akshare as ak

        code = symbol.split(".")[0]

        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, partial(ak.stock_individual_info_em, symbol=code)
            )
            if data is None or data.empty:
                return None

            info = {}
            for _, row in data.iterrows():
                info[row.iloc[0]] = row.iloc[1]

            return FundamentalData(
                symbol=symbol,
                market="cn",
                pe_ratio=_safe_float(info.get("市盈率-动态")),
                pb_ratio=_safe_float(info.get("市净率")),
                market_cap=_safe_float(info.get("总市值")),
                revenue=_safe_float(info.get("营业收入")),
                net_income=_safe_float(info.get("净利润")),
                roe=_safe_float(info.get("净资产收益率")),
            )
        except Exception:
            return None


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
