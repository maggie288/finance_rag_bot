from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Text, Numeric, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, UUIDMixin, TimestampMixin


class NewsArticle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "news_articles"

    source: Mapped[str] = mapped_column(String(50), nullable=False)  # twitter | youtube | report | fed | pboc
    source_id: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(Text)
    author: Mapped[Optional[str]] = mapped_column(String(200))
    symbols: Mapped[Optional[list]] = mapped_column(ARRAY(String(20)), default=list)
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20))  # bullish | bearish | neutral
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pinecone_id: Mapped[Optional[str]] = mapped_column(String(255))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
