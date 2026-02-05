from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Finance RAG Bot"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://finance_bot:finance_bot_dev@localhost:5432/finance_rag_bot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    # 手机测试时，修改 .env 文件添加你的局域网IP，例如：
    # CORS_ORIGINS=http://localhost:3000,http://192.168.1.14:3000
    cors_origins: str = "http://localhost:3000"

    # TwelveData
    twelvedata_api_key: str = ""

    # TuShare (A股数据)
    tushare_token: str = ""

    # NewsAPI (新闻数据)
    newsapi_key: str = ""

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "finance-rag-bot"

    # LLM Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    minimax_api_key: str = ""

    # Embedding
    embedding_model: str = "text-embedding-3-small"

    # Credits
    default_credits: float = 100.0

    # Scheduler
    scheduler_enabled: bool = False
    scheduler_refresh_interval: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
