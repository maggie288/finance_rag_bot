"""新闻存储服务"""
from __future__ import annotations

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.services.news.fetchers import NewsArticleData

logger = logging.getLogger(__name__)


class NewsStorageService:
    """新闻存储服务"""

    @staticmethod
    async def save_articles(
        db: AsyncSession,
        articles: List[NewsArticleData],
        sentiment_results: Optional[List[dict]] = None
    ) -> List[NewsArticle]:
        """
        保存新闻文章到数据库

        Args:
            db: 数据库会话
            articles: 新闻文章数据列表
            sentiment_results: 情感分析结果列表（可选）

        Returns:
            保存的NewsArticle对象列表
        """
        saved_articles = []

        for idx, article_data in enumerate(articles):
            try:
                # 检查是否已存在（通过URL或source_id）
                existing = None
                if article_data.url:
                    stmt = select(NewsArticle).where(NewsArticle.url == article_data.url)
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                if existing:
                    logger.debug(f"Article already exists: {article_data.url}")
                    continue

                # 获取情感分析结果
                sentiment_score = None
                sentiment_label = None
                if sentiment_results and idx < len(sentiment_results):
                    sentiment_result = sentiment_results[idx]
                    sentiment_score = sentiment_result.get("score")
                    sentiment_label = sentiment_result.get("label")

                # 创建新文章
                news_article = NewsArticle(
                    source=article_data.source,
                    title=article_data.title,
                    content=article_data.content,
                    url=article_data.url,
                    author=article_data.author,
                    symbols=article_data.symbols,
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label,
                    published_at=article_data.published_at,
                    metadata_=article_data.metadata,
                )

                db.add(news_article)
                saved_articles.append(news_article)

            except Exception as e:
                logger.error(f"Failed to save article: {e}")
                continue

        # 提交所有更改
        try:
            await db.commit()
            logger.info(f"Saved {len(saved_articles)} new articles to database")
        except Exception as e:
            logger.error(f"Failed to commit articles: {e}")
            await db.rollback()
            return []

        return saved_articles

    @staticmethod
    async def get_latest_articles(
        db: AsyncSession,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        获取最新的新闻文章

        Args:
            db: 数据库会话
            symbol: 股票代码（可选）
            limit: 返回数量限制

        Returns:
            新闻文章列表
        """
        stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc())

        if symbol:
            stmt = stmt.where(NewsArticle.symbols.contains([symbol]))

        stmt = stmt.limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())
