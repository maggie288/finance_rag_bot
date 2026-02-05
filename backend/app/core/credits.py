from __future__ import annotations

from typing import Optional
from decimal import Decimal
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.credit import CreditTransaction


CREDIT_COSTS = {
    "stock_quote": Decimal("0"),
    "kline_data": Decimal("0"),
    "fundamental_analysis": Decimal("1.0"),
    "ai_chat_deepseek": Decimal("0.5"),
    "ai_chat_minimax": Decimal("0.5"),
    "ai_chat_claude": Decimal("2.0"),
    "ai_chat_openai": Decimal("2.0"),
    "report_generation": Decimal("5.0"),
    "markov_prediction": Decimal("1.0"),
    "sentiment_analysis": Decimal("2.0"),
    "trading_simulation": Decimal("10.0"),  # AI trading simulation
}


async def get_credit_cost(action: str, model: Optional[str] = None) -> Decimal:
    if action == "ai_chat" and model:
        return CREDIT_COSTS.get(f"ai_chat_{model}", Decimal("1.0"))
    return CREDIT_COSTS.get(action, Decimal("1.0"))


async def deduct_credits(
    db: AsyncSession,
    user_id: UUID,
    amount: Decimal,
    description: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[UUID] = None,
) -> Optional[CreditTransaction]:
    """Atomically deduct credits from user. Returns transaction or None if insufficient."""
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one_or_none()
    if not user or user.credits_balance < amount:
        return None

    new_balance = user.credits_balance - amount
    await db.execute(
        update(User).where(User.id == user_id).values(credits_balance=new_balance)
    )

    transaction = CreditTransaction(
        user_id=user_id,
        type="consumption",
        amount=-amount,
        balance_after=new_balance,
        description=description,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(transaction)
    await db.flush()
    return transaction


async def add_credits(
    db: AsyncSession,
    user_id: UUID,
    amount: Decimal,
    description: str = "Recharge",
) -> CreditTransaction:
    """Add credits to user account."""
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one()

    new_balance = user.credits_balance + amount
    await db.execute(
        update(User).where(User.id == user_id).values(credits_balance=new_balance)
    )

    transaction = CreditTransaction(
        user_id=user_id,
        type="recharge",
        amount=amount,
        balance_after=new_balance,
        description=description,
    )
    db.add(transaction)
    await db.flush()
    return transaction
