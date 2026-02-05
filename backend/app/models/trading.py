from __future__ import annotations

import uuid
from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Numeric, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class TradingSimulation(Base, UUIDMixin, TimestampMixin):
    """AI Agent trading simulation record"""
    __tablename__ = "trading_simulations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(10), nullable=False)

    # Agent configuration
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)  # deepseek, minimax, etc
    llm_model: Mapped[str] = mapped_column(String(50), nullable=False)

    # Financial configuration
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # USD, CNY

    # Simulation period
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # pending, running, completed, stopped, failed

    # Holdings
    current_shares: Mapped[Decimal] = mapped_column(Numeric(15, 6), default=Decimal("0"), nullable=False)
    average_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))

    # Performance metrics
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_profit_loss: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    max_drawdown: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # Configuration and metadata
    config: Mapped[Optional[dict]] = mapped_column(JSONB)
    # {
    #   "decision_frequency": "daily",
    #   "max_position_size": 0.5,
    #   "stop_loss_pct": 0.1,
    #   "take_profit_pct": 0.2,
    #   "risk_tolerance": "medium"
    # }

    # LLM usage tracking
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_llm_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"), nullable=False)

    # Result summary
    summary: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Execution logs
    execution_logs: Mapped[Optional[dict]] = mapped_column(JSONB)
    # {
    #   "logs": [
    #     {"timestamp": "2026-02-05 10:00:00", "level": "info", "message": "Starting simulation..."},
    #     {"timestamp": "2026-02-05 10:01:00", "level": "info", "message": "Day 1: Price = $150.00"}
    #   ]
    # }


class Trade(Base, UUIDMixin, TimestampMixin):
    """Individual trade executed by AI agent"""
    __tablename__ = "trades"

    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trading_simulations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Trade details
    trade_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # buy, sell
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)

    # Execution details
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)

    # Position tracking
    shares_before: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)
    shares_after: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False)
    cash_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cash_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Profit/Loss for this trade
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))

    # AI decision reasoning
    llm_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Market context at trade time
    market_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    # {
    #   "price": 100.50,
    #   "volume": 1000000,
    #   "change_percent": 2.5,
    #   "high": 101.0,
    #   "low": 99.0
    # }

    # LLM usage for this decision
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"), nullable=False)
