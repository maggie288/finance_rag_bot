from celery import Celery
from app.config import settings

celery_app = Celery(
    "finance_rag_bot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Import tasks to register them
# Manually import tasks instead of autodiscover
from app.workers import news_tasks  # noqa: F401
from app.workers import trading_tasks  # noqa: F401
