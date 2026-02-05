import uuid
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class CreditTransaction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "credit_transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # recharge | consumption | refund
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))  # llm_query | report_gen | prediction
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
