from __future__ import annotations

from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: Optional[str]
    credits_balance: Decimal
    preferred_llm: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    display_name: Optional[str] = None
    preferred_llm: Optional[str] = None
    language: Optional[str] = None
