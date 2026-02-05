from __future__ import annotations

import uuid
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin
from datetime import datetime


class PolymarketMarket(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "polymarket_markets"

    market_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    creator_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    yes_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    no_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    liquidity: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    
    outcome: Mapped[str] = mapped_column(String(20), nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    closed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=True)


class ClawdBotOpportunity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clawdbot_opportunities"

    market_id: Mapped[str] = mapped_column(String(100), nullable=False)
    market_slug: Mapped[str] = mapped_column(String(200), nullable=True)
    market_question: Mapped[str] = mapped_column(Text, nullable=True)
    
    opportunity_type: Mapped[str] = mapped_column(String(50), nullable=True)
    signal_strength: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=True)
    
    entry_price_yes: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    entry_price_no: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    target_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    
    expected_return: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=True)
    
    analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="active")
    
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    executed_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    profit_loss: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)


class ClawdBotWallet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clawdbot_wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    wallet_type: Mapped[str] = mapped_column(String(50), nullable=True)
    wallet_name: Mapped[str] = mapped_column(String(100), nullable=True)
    
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    public_key: Mapped[str] = mapped_column(String(500), nullable=True)
    
    balance_btc: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=True)
    balance_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    config: Mapped[dict] = mapped_column(JSONB, default=dict)


class ClawdBotTrade(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clawdbot_trades"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clawdbot_wallets.id"), nullable=False
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clawdbot_opportunities.id"), nullable=True
    )
    
    market_id: Mapped[str] = mapped_column(String(100), nullable=False)
    market_slug: Mapped[str] = mapped_column(String(200), nullable=True)
    
    side: Mapped[str] = mapped_column(String(10), nullable=True)
    amount_btc: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=True)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    
    entry_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    pnl: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    pnl_percent: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="open")
    
    transaction_hash: Mapped[str] = mapped_column(String(500), nullable=True)
    polymarket_order_id: Mapped[str] = mapped_column(String(200), nullable=True)
    
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow())
    closed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    settled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class ClawdBotConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clawdbot_configs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_trade: Mapped[bool] = mapped_column(Boolean, default=False)
    
    min_opportunity_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.7"))
    max_position_size_btc: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=Decimal("0.01"))
    max_daily_loss_btc: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=Decimal("0.05"))
    
    selected_markets: Mapped[list] = mapped_column(JSONB, default=list)
    excluded_categories: Mapped[list] = mapped_column(JSONB, default=list)
    
    telegram_notify: Mapped[bool] = mapped_column(Boolean, default=False)
    telegram_token: Mapped[str] = mapped_column(String(200), nullable=True)
    telegram_chat_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    performance_stats: Mapped[dict] = mapped_column(JSONB, default=dict)
