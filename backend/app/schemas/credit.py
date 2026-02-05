from __future__ import annotations

from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class CreditBalanceResponse(BaseModel):
    balance: Decimal
    currency: str = "credits"


class CreditTransactionResponse(BaseModel):
    id: UUID
    type: str
    amount: Decimal
    balance_after: Decimal
    description: Optional[str]
    reference_type: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditHistoryResponse(BaseModel):
    transactions: List[CreditTransactionResponse]
    total: int
    page: int
    page_size: int


class MockRechargeRequest(BaseModel):
    amount: Decimal
