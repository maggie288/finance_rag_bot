from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Integer, BigInteger, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class StockQuote(Base, TimestampMixin):
    __tablename__ = "stock_quotes"
    __table_args__ = (
        Index("ix_stock_quotes_symbol_market", "symbol", "market"),
    )

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    market: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    price: Mapped[float] = mapped_column(Float, default=0)
    change: Mapped[Optional[float]] = mapped_column(Float)
    change_percent: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    high: Mapped[Optional[float]] = mapped_column(Float)
    low: Mapped[Optional[float]] = mapped_column(Float)
    open: Mapped[Optional[float]] = mapped_column(Float)
    prev_close: Mapped[Optional[float]] = mapped_column(Float)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class StockKline(Base, TimestampMixin):
    __tablename__ = "stock_klines"
    __table_args__ = (
        UniqueConstraint("symbol", "market", "interval", "datetime", name="uq_stock_kline_symbol_market_interval_datetime"),
        Index("ix_stock_klines_symbol_interval", "symbol", "interval"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    interval: Mapped[str] = mapped_column(String(10), nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Float, default=0)
    high: Mapped[float] = mapped_column(Float, default=0)
    low: Mapped[float] = mapped_column(Float, default=0)
    close: Mapped[float] = mapped_column(Float, default=0)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)


class StockFundamental(Base, TimestampMixin):
    __tablename__ = "stock_fundamentals"
    __table_args__ = (
        Index("ix_stock_fundamentals_symbol_market", "symbol", "market"),
    )

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    market: Mapped[str] = mapped_column(String(10), primary_key=True)
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float)
    roe: Mapped[Optional[float]] = mapped_column(Float)
    debt_ratio: Mapped[Optional[float]] = mapped_column(Float)
    revenue_growth: Mapped[Optional[float]] = mapped_column(Float)
    net_profit_margin: Mapped[Optional[float]] = mapped_column(Float)
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    dividend_yield: Mapped[Optional[float]] = mapped_column(Float)
    eps: Mapped[Optional[float]] = mapped_column(Float)
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    net_income: Mapped[Optional[float]] = mapped_column(Float)
    total_debt: Mapped[Optional[float]] = mapped_column(Float)
    total_cash: Mapped[Optional[float]] = mapped_column(Float)
    operating_cash_flow: Mapped[Optional[float]] = mapped_column(Float)
    free_cash_flow: Mapped[Optional[float]] = mapped_column(Float)
