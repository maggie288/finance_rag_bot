"""新闻采集Celery任务"""
from __future__ import annotations

import logging
import asyncio
from typing import Optional

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.news import NewsAggregator, SentimentAnalyzer, NewsStorageService
from app.services.rag.pipeline import rag_pipeline
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="fetch_news_for_symbol")
def fetch_news_for_symbol(self, symbol: Optional[str] = None, max_articles: int = 20):
    """
    为指定股票代码获取新闻

    Args:
        symbol: 股票代码（可选，None表示获取所有财经新闻）
        max_articles: 每个数据源最多获取的文章数

    Returns:
        {"success": bool, "articles_saved": int, "error": str}
    """
    async def _async_fetch():
        logger.info(f"Starting news fetch task for symbol: {symbol}")

        try:
            # 初始化服务
            aggregator = NewsAggregator(newsapi_key=settings.newsapi_key)
            sentiment_analyzer = SentimentAnalyzer(model_name="deepseek")

            # 获取新闻
            articles = await aggregator.fetch_all_news(
                symbol=symbol,
                max_per_source=max_articles
            )

            if not articles:
                logger.warning(f"No articles fetched for symbol: {symbol}")
                return {"success": True, "articles_saved": 0, "error": None}

            logger.info(f"Fetched {len(articles)} articles for symbol: {symbol}")

            # 批量情感分析
            article_dicts = [
                {"title": a.title, "content": a.content}
                for a in articles
            ]
            sentiment_results = await sentiment_analyzer.batch_analyze(article_dicts)

            # 保存到数据库
            async with AsyncSessionLocal() as db:
                saved_articles = await NewsStorageService.save_articles(
                    db, articles, sentiment_results
                )

            logger.info(f"Saved {len(saved_articles)} articles for symbol: {symbol}")

            # 索引到向量数据库（RAG）
            if saved_articles:
                try:
                    documents = []
                    for article in saved_articles:
                        # 构建文档内容
                        text = f"Title: {article.title}\n\n"
                        if article.content:
                            text += f"Content: {article.content}\n\n"
                        if article.sentiment_label:
                            text += f"Sentiment: {article.sentiment_label}\n"

                        # 构建文档ID和元数据
                        doc = {
                            "id": f"news_{article.id}",
                            "text": text,
                            "metadata": {
                                "type": "news",
                                "source": article.source,
                                "symbol": symbol or "general",
                                "symbols": article.symbols,
                                "published_at": article.published_at.isoformat() if article.published_at else None,
                                "url": article.url,
                                "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
                                "sentiment_label": article.sentiment_label,
                            }
                        }
                        documents.append(doc)

                    # 索引到Pinecone
                    await rag_pipeline.upsert_documents(documents, namespace="news")
                    logger.info(f"Indexed {len(documents)} articles to vector database")
                except Exception as e:
                    logger.error(f"Failed to index articles to vector database: {e}", exc_info=True)

            return {
                "success": True,
                "articles_saved": len(saved_articles),
                "error": None
            }

        except Exception as e:
            logger.error(f"News fetch task failed for symbol {symbol}: {e}", exc_info=True)
            return {
                "success": False,
                "articles_saved": 0,
                "error": str(e)
            }

    return asyncio.run(_async_fetch())


@celery_app.task(bind=True, name="fetch_all_market_news")
def fetch_all_market_news(self, max_articles: int = 20):
    """
    获取所有市场的财经新闻（不限股票代码）

    Args:
        max_articles: 每个数据源最多获取的文章数

    Returns:
        {"success": bool, "articles_saved": int, "error": str}
    """
    async def _async_fetch():
        logger.info("Starting fetch_all_market_news task")

        try:
            # 初始化服务
            aggregator = NewsAggregator(newsapi_key=settings.newsapi_key)
            sentiment_analyzer = SentimentAnalyzer(model_name="deepseek")

            # 获取新闻（不指定symbol，获取所有财经新闻）
            articles = await aggregator.fetch_all_news(
                symbol=None,
                max_per_source=max_articles
            )

            if not articles:
                logger.warning("No articles fetched")
                return {"success": True, "articles_saved": 0, "error": None}

            logger.info(f"Fetched {len(articles)} articles")

            # 批量情感分析
            article_dicts = [
                {"title": a.title, "content": a.content}
                for a in articles
            ]
            sentiment_results = await sentiment_analyzer.batch_analyze(article_dicts)

            # 保存到数据库
            async with AsyncSessionLocal() as db:
                saved_articles = await NewsStorageService.save_articles(
                    db, articles, sentiment_results
                )

            logger.info(f"Saved {len(saved_articles)} articles")

            # 索引到向量数据库（RAG）
            if saved_articles:
                try:
                    documents = []
                    for article in saved_articles:
                        # 构建文档内容
                        text = f"Title: {article.title}\n\n"
                        if article.content:
                            text += f"Content: {article.content}\n\n"
                        if article.sentiment_label:
                            text += f"Sentiment: {article.sentiment_label}\n"

                        # 构建文档ID和元数据
                        doc = {
                            "id": f"news_{article.id}",
                            "text": text,
                            "metadata": {
                                "type": "news",
                                "source": article.source,
                                "symbol": article.symbols[0] if article.symbols else "general",
                                "symbols": article.symbols,
                                "published_at": article.published_at.isoformat() if article.published_at else None,
                                "url": article.url,
                                "sentiment_score": float(article.sentiment_score) if article.sentiment_score else None,
                                "sentiment_label": article.sentiment_label,
                            }
                        }
                        documents.append(doc)

                    # 索引到Pinecone
                    await rag_pipeline.upsert_documents(documents, namespace="news")
                    logger.info(f"Indexed {len(documents)} articles to vector database")
                except Exception as e:
                    logger.error(f"Failed to index articles to vector database: {e}", exc_info=True)

            return {
                "success": True,
                "articles_saved": len(saved_articles),
                "error": None
            }

        except Exception as e:
            logger.error(f"fetch_all_market_news task failed: {e}", exc_info=True)
            return {
                "success": False,
                "articles_saved": 0,
                "error": str(e)
            }

    return asyncio.run(_async_fetch())


# 定时任务配置
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """配置定时任务"""

    # 每小时获取一次市场新闻
    sender.add_periodic_task(
        3600.0,  # 每小时
        fetch_all_market_news.s(),
        name="fetch_market_news_hourly"
    )

    # 热门股票配置（扩展版）
    # 第一梯队：高频监控（每15分钟）- 最热门股票
    tier1_symbols = [
        "AAPL", "TSLA", "NVDA",  # 美股科技龙头
        "0700.HK",  # 腾讯
        "600519.SH",  # 茅台
    ]

    # 第二梯队：中频监控（每30分钟）
    tier2_symbols = [
        "MSFT", "GOOGL", "AMZN", "META", "AMD",  # 美股科技
        "9988.HK", "1810.HK",  # 港股：阿里、小米
        "000858.SZ", "002594.SZ", "300750.SZ",  # A股：五粮液、比亚迪、宁德时代
    ]

    # 第三梯队：低频监控（每小时）
    tier3_symbols = [
        "INTC", "NFLX", "CRM", "ORCL",  # 美股
        "0941.HK", "3690.HK",  # 港股：中国移动、美团
        "601318.SH", "601398.SH",  # A股：平安、工商银行
    ]

    # 配置第一梯队任务
    for symbol in tier1_symbols:
        sender.add_periodic_task(
            900.0,  # 每15分钟
            fetch_news_for_symbol.s(symbol=symbol, max_articles=15),
            name=f"fetch_news_t1_{symbol}"
        )

    # 配置第二梯队任务
    for symbol in tier2_symbols:
        sender.add_periodic_task(
            1800.0,  # 每30分钟
            fetch_news_for_symbol.s(symbol=symbol, max_articles=10),
            name=f"fetch_news_t2_{symbol}"
        )

    # 配置第三梯队任务
    for symbol in tier3_symbols:
        sender.add_periodic_task(
            3600.0,  # 每小时
            fetch_news_for_symbol.s(symbol=symbol, max_articles=8),
            name=f"fetch_news_t3_{symbol}"
        )

    logger.info(
        f"Periodic news tasks configured: "
        f"Tier1={len(tier1_symbols)}, Tier2={len(tier2_symbols)}, Tier3={len(tier3_symbols)}"
    )
