import uuid
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class AnalysisReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_reports"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # fundamental | sentiment | prediction | custom | macro
    title: Mapped[Optional[str]] = mapped_column(String(500))
    symbol: Mapped[Optional[str]] = mapped_column(String(20))
    market: Mapped[Optional[str]] = mapped_column(String(10))
    content: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    llm_model: Mapped[Optional[str]] = mapped_column(String(50))
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    credits_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="generating")


class PredictionResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "prediction_results"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    prediction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 3day | 1week | 1month
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    states: Mapped[dict] = mapped_column(JSONB, nullable=False)
    transition_matrix: Mapped[dict] = mapped_column(JSONB, nullable=False)
    predicted_states: Mapped[dict] = mapped_column(JSONB, nullable=False)
    predicted_range: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    computation_log: Mapped[Optional[dict]] = mapped_column(JSONB)
