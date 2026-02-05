from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.credits import router as credits_router
from app.api.v1.market import router as market_router
from app.api.v1.prediction import router as prediction_router
from app.api.v1.ai import router as ai_router
from app.api.v1.news import router as news_router
from app.api.v1.reports import router as reports_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.trading import router as trading_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(credits_router)
api_router.include_router(market_router)
api_router.include_router(prediction_router)
api_router.include_router(ai_router)
api_router.include_router(news_router)
api_router.include_router(reports_router)
api_router.include_router(watchlist_router)
api_router.include_router(trading_router)
