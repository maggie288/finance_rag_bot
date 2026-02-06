from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.news import NewsArticle
from app.workers.news_tasks import fetch_news_for_symbol
from app.services.rag.pipeline_mvp import rag_pipeline

router = APIRouter(prefix="/news", tags=["news"])

# 新闻分类定义
NEWS_CATEGORIES = {
    "a_stock": {
        "name": "A股",
        "symbol_patterns": [".SH", ".SZ"],  # 上海/深圳交易所
        "keywords": ["A股", "沪指", "深成指", "创业板", "科创板", "上证", "深证"],
    },
    "hk_stock": {
        "name": "港股",
        "symbol_patterns": [".HK"],
        "keywords": ["港股", "恒生指数", "港交所", "恒指"],
    },
    "us_stock": {
        "name": "美股",
        "symbol_patterns": [],  # 美股通常没有后缀
        "keywords": ["美股", "纳斯达克", "道琼斯", "标普500", "NYSE", "NASDAQ"],
        "exclude_patterns": [".SH", ".SZ", ".HK", "BTC", "ETH", "USDT"],
    },
    "commodity": {
        "name": "大宗商品",
        "symbol_patterns": [],
        "keywords": ["原油", "黄金", "白银", "铜", "铁矿石", "大宗商品", "期货", "油价", "金价"],
    },
    "crypto": {
        "name": "加密货币",
        "symbol_patterns": ["BTC", "ETH", "USDT", "BNB", "XRP", "SOL", "DOGE"],
        "keywords": ["比特币", "以太坊", "加密货币", "区块链", "币圈", "虚拟货币", "数字货币"],
    },
    "policy": {
        "name": "国家政策",
        "sources": ["fed", "pboc", "policy"],
        "keywords": ["央行", "美联储", "货币政策", "利率", "降息", "加息", "政策", "监管", "国务院"],
    },
}


@router.get("/categories")
async def get_news_categories(
    user: User = Depends(get_current_user),
):
    """获取所有新闻分类"""
    return {
        "categories": [
            {"key": key, "name": cat["name"]}
            for key, cat in NEWS_CATEGORIES.items()
        ]
    }


def _build_category_filter(category: str):
    """根据分类构建SQLAlchemy过滤条件"""
    cat_config = NEWS_CATEGORIES.get(category)
    if not cat_config:
        return None

    conditions = []

    # 按来源过滤
    if "sources" in cat_config:
        conditions.append(NewsArticle.source.in_(cat_config["sources"]))

    # 按symbol模式过滤
    if cat_config.get("symbol_patterns"):
        symbol_conditions = []
        for pattern in cat_config["symbol_patterns"]:
            # 使用 ANY 来检查 symbols 数组中是否有匹配的元素
            symbol_conditions.append(
                func.array_to_string(NewsArticle.symbols, ',').ilike(f"%{pattern}%")
            )
        if symbol_conditions:
            conditions.append(or_(*symbol_conditions))

    # 按关键词过滤（标题或内容）
    if cat_config.get("keywords"):
        keyword_conditions = []
        for keyword in cat_config["keywords"]:
            keyword_conditions.append(
                or_(
                    NewsArticle.title.ilike(f"%{keyword}%"),
                    NewsArticle.content.ilike(f"%{keyword}%")
                )
            )
        if keyword_conditions:
            conditions.append(or_(*keyword_conditions))

    if not conditions:
        return None

    return or_(*conditions)


@router.get("/feed")
async def get_news_feed(
    symbol: Optional[str] = Query(None, description="股票代码"),
    source: Optional[str] = Query(None, description="来源"),
    category: Optional[str] = Query(None, description="分类: a_stock, hk_stock, us_stock, commodity, crypto, policy"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取新闻列表

    - symbol: 股票代码（可选）
    - source: 来源（可选）
    - category: 分类（可选）: a_stock(A股), hk_stock(港股), us_stock(美股), commodity(大宗商品), crypto(加密货币), policy(国家政策)
    """
    query = select(NewsArticle).order_by(NewsArticle.published_at.desc())

    if symbol:
        query = query.where(NewsArticle.symbols.any(symbol))
    if source:
        query = query.where(NewsArticle.source == source)
    if category:
        cat_filter = _build_category_filter(category)
        if cat_filter is not None:
            query = query.where(cat_filter)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()

    return {
        "articles": [
            {
                "id": str(a.id),
                "source": a.source,
                "title": a.title,
                "content": a.content[:200] if a.content else None,
                "url": a.url,
                "author": a.author,
                "symbols": a.symbols,
                "sentiment_score": float(a.sentiment_score) if a.sentiment_score else None,
                "sentiment_label": a.sentiment_label,
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ],
        "page": page,
        "page_size": page_size,
        "category": category,
    }


@router.post("/fetch")
async def fetch_news(
    symbol: Optional[str] = Query(None, description="股票代码，不指定则获取所有财经新闻"),
    max_articles: int = Query(20, ge=1, le=50, description="每个数据源最多获取的文章数"),
    background_tasks: BackgroundTasks = None,
    user: User = Depends(get_current_user),
):
    """
    手动触发新闻采集

    - symbol: 股票代码（可选）
    - max_articles: 每个数据源最多获取的文章数
    """
    # Trigger the Celery task
    task = fetch_news_for_symbol.apply_async(
        args=[symbol, max_articles],
        countdown=1  # 1秒后执行
    )

    return {
        "message": "新闻采集任务已启动",
        "task_id": task.id,
        "symbol": symbol,
        "max_articles": max_articles,
    }


@router.post("/index-to-rag")
async def index_news_to_rag(
    symbol: Optional[str] = Query(None, description="股票代码，不指定则索引所有新闻"),
    limit: int = Query(100, ge=1, le=1000, description="最多索引的文章数"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发将数据库中的新闻索引到向量数据库（RAG）

    - symbol: 股票代码（可选）
    - limit: 最多索引的文章数
    """
    try:
        # 查询数据库中的新闻
        query = select(NewsArticle).order_by(NewsArticle.published_at.desc())

        if symbol:
            query = query.where(NewsArticle.symbols.any(symbol))

        query = query.limit(limit)
        result = await db.execute(query)
        articles = result.scalars().all()

        if not articles:
            return {
                "message": "没有找到新闻数据",
                "indexed": 0,
            }

        # 构建文档列表
        documents = []
        for article in articles:
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
                    "symbol": symbol or (article.symbols[0] if article.symbols else "general"),
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

        return {
            "message": f"成功索引 {len(documents)} 篇新闻到向量数据库",
            "indexed": len(documents),
            "symbol": symbol,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")
