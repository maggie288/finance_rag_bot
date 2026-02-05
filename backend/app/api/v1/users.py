from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UpdateUserRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    req: UpdateUserRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.preferred_llm is not None:
        if req.preferred_llm not in ("deepseek", "minimax", "claude", "openai"):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid LLM model")
        user.preferred_llm = req.preferred_llm
    if req.language is not None:
        user.language = req.language

    db.add(user)
    await db.flush()
    return user
