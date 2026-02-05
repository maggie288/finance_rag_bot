import uuid
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    credits_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("100.00"))
    preferred_llm: Mapped[str] = mapped_column(String(50), default="deepseek")
    language: Mapped[str] = mapped_column(String(10), default="zh-CN")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PasswordResetToken(Base, UUIDMixin):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
