from __future__ import annotations

from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class ReportRequest(BaseModel):
    report_type: str  # fundamental | sentiment | prediction | macro
    symbol: Optional[str] = None
    market: Optional[str] = None
    query: Optional[str] = None
    llm_model: Optional[str] = None


class ReportResponse(BaseModel):
    id: UUID
    report_type: str
    title: Optional[str]
    symbol: Optional[str]
    market: Optional[str]
    content: Optional[str]
    summary: Optional[str]
    llm_model: Optional[str]
    credits_cost: Optional[Decimal]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AIQueryRequest(BaseModel):
    query: str
    symbol: Optional[str] = None
    market: Optional[str] = None
    model: str = "deepseek"
    use_rag: bool = True


class AIQueryResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict]] = None
    model_used: str
    tokens_used: Optional[int] = None
    credits_cost: Optional[Decimal] = None
