from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class StockQuote(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: str
    price: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    prev_close: Optional[float] = None
    timestamp: Optional[datetime] = None


class KlinePoint(BaseModel):
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class KlineResponse(BaseModel):
    symbol: str
    market: str
    interval: str
    data: List[KlinePoint]


class MarketSearchResult(BaseModel):
    symbol: str
    name: str
    market: str
    type: str  # stock | etf | commodity


class FundamentalData(BaseModel):
    symbol: str
    market: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    net_profit_margin: Optional[float] = None
    market_cap: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    # 估算标记和技术指标（基于行情数据）
    is_estimated: Optional[bool] = False
    estimation_note: Optional[str] = None
    price_ma20: Optional[float] = None
    price_ma60: Optional[float] = None
    volatility: Optional[float] = None
    return_60d: Optional[float] = None
