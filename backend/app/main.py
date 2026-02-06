import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.services.market_data.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)

STARTUP_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.scheduler_enabled:
        logger.info("[Startup] Starting market data scheduler...")
        start_scheduler()
        logger.info("[Startup] Market data scheduler started")
    else:
        logger.info("[Startup] Scheduler disabled (SCHEDULER_ENABLED=false)")
    yield
    if settings.scheduler_enabled:
        logger.info("[Shutdown] Stopping market data scheduler...")
        stop_scheduler()
        logger.info("[Shutdown] Market data scheduler stopped")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)


@app.get("/health")
async def health(request: Request = None):
    elapsed = time.time() - STARTUP_TIME
    client_ip = request.client.host if request else "unknown"
    
    logger.info(f"[HealthCheck] Request from {client_ip}, elapsed={elapsed:.1f}s")

    if elapsed < 5:
        logger.warning(f"[HealthCheck] Rejecting - still starting up ({elapsed:.1f}s)")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Starting up ({elapsed:.1f}s)")

    logger.info(f"[HealthCheck] Passed - service ready")
    return {
        "status": "ok", 
        "service": settings.app_name,
        "uptime": f"{elapsed:.1f}s"
    }
