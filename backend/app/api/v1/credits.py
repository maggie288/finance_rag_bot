from __future__ import annotations

from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.credits import add_credits
from app.dependencies import get_current_user
from app.models.user import User
from app.models.credit import CreditTransaction
from app.schemas.credit import (
    CreditBalanceResponse,
    CreditTransactionResponse,
    CreditHistoryResponse,
    MockRechargeRequest,
)

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_balance(user: User = Depends(get_current_user)):
    return CreditBalanceResponse(balance=user.credits_balance)


@router.get("/history", response_model=CreditHistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(CreditTransaction).where(CreditTransaction.user_id == user.id)
    count_query = select(func.count()).select_from(CreditTransaction).where(
        CreditTransaction.user_id == user.id
    )

    if type:
        query = query.where(CreditTransaction.type == type)
        count_query = count_query.where(CreditTransaction.type == type)

    query = query.order_by(CreditTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    transactions = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return CreditHistoryResponse(
        transactions=[CreditTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/mock-recharge", response_model=CreditTransactionResponse)
async def mock_recharge(
    req: MockRechargeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mock recharge - adds credits without real payment."""
    if req.amount <= 0 or req.amount > Decimal("10000"):
        raise HTTPException(status_code=400, detail="Invalid amount (1-10000)")

    transaction = await add_credits(
        db, user.id, req.amount, description=f"Mock recharge: {req.amount} credits"
    )
    return CreditTransactionResponse.model_validate(transaction)
