"""新闻数据采集模块 - 使用免费数据源"""
from __future__ import annotations

import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from abc import ABC, abstractmethod
import feedparser
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class NewsArticleData:
    """新闻文章数据结构"""
    def __init__(
        self,
        source: str,
        title: str,
        content: Optional[str],
        url: str,
        author: Optional[str],
        published_at: Optional[datetime],
        symbols: List[str] = None,
        source_id: Optional[str] = None,
        metadata: Dict = None,
    ):
        self.source = source
        self.title = title
        self.content = content
        self.url = url
        self.author = author
        self.published_at = published_at
        self.symbols = symbols or []
        self.source_id = source_id
        self.metadata = metadata or {}


class NewsFetcher(ABC):
    """新闻采集器基类"""

    @abstractmethod
    async def fetch_news(
        self, symbol: Optional[str] = None, max_articles: int = 10
    ) -> List[NewsArticleData]:
        """获取新闻"""
        pass


class RSSFeedFetcher(NewsFetcher):
    """RSS Feed 采集器（免费）"""

    # 主流财经媒体RSS源
    RSS_FEEDS = {
        "reuters_finance": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "cnbc": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "wsj": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "ft": "https://www.ft.com/?format=rss",
        "investing": "https://www.investing.com/rss/news.rss",

        # 中国财经媒体
        "sina_finance": "https://finance.sina.com.cn/roll/index.d.html",
        "eastmoney": "http://feed.eastmoney.com/",
        "caixin": "http://www.caixin.com/rss/rss_index.html",

        # 央行新闻
        "federal_reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
        "pboc": "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.rss",
    }

    async def fetch_news(
        self, symbol: Optional[str] = None, max_articles: int = 10
    ) -> List[NewsArticleData]:
        """从RSS源获取新闻"""
        articles = []

        # 选择相关的RSS源
        feeds_to_fetch = list(self.RSS_FEEDS.items())[:5]  # 限制数量避免超时

        for source_name, feed_url in feeds_to_fetch:
            try:
                # 使用feedparser解析RSS
                feed = await asyncio.to_thread(feedparser.parse, feed_url)

                for entry in feed.entries[:max_articles]:
                    try:
                        # 解析发布时间
                        published_at = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                            published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                        # 提取内容
                        content = None
                        if hasattr(entry, 'summary'):
                            content = entry.summary
                        elif hasattr(entry, 'description'):
                            content = entry.description

                        # 清理HTML标签
                        if content:
                            soup = BeautifulSoup(content, 'html.parser')
                            content = soup.get_text()[:1000]

                        # 提取相关股票代码（简单关键词匹配）
                        symbols = self._extract_symbols(entry.title, content, symbol)

                        # 如果指定了symbol，只保留相关的
                        if symbol and symbol not in symbols:
                            continue

                        article = NewsArticleData(
                            source=source_name,
                            title=entry.title if hasattr(entry, 'title') else "No title",
                            content=content,
                            url=entry.link if hasattr(entry, 'link') else "",
                            author=entry.author if hasattr(entry, 'author') else None,
                            published_at=published_at,
                            symbols=symbols,
                            source_id=entry.id if hasattr(entry, 'id') else entry.link,
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.warning(f"Failed to parse RSS entry: {e}")
                        continue

                logger.info(f"Fetched {len(feed.entries)} articles from {source_name}")
            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {source_name}: {e}")
                continue

        return articles

    # 公司名称到股票代码的映射
    COMPANY_TO_SYMBOL = {
        "apple": "AAPL",
        "tesla": "TSLA",
        "elon musk": "TSLA",
        "spacex": "TSLA",
        "nvidia": "NVDA",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "amd": "AMD",
        "intel": "INTC",
        "netflix": "NFLX",
        "tencent": "0700.HK",
        "alibaba": "9988.HK",
        "moutai": "600519.SH",
        "kweichow moutai": "600519.SH",
        "wuliangye": "000858.SZ",
    }

    def _extract_symbols(self, title: str, content: Optional[str], target_symbol: Optional[str] = None) -> List[str]:
        """从标题和内容中提取股票代码（改进版）"""
        symbols = set()
        text = f"{title} {content or ''}".upper()
        text_lower = f"{title} {content or ''}".lower()

        # 常见股票代码模式
        common_symbols = [
            "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "INTC", "NFLX",
            "0700.HK", "9988.HK", "1810.HK",  # 腾讯、阿里、小米
            "600519.SH", "000858.SZ",  # 茅台、五粮液
        ]

        # 1. 直接匹配股票代码
        for sym in common_symbols:
            if sym in text or sym.replace(".HK", "").replace(".SH", "").replace(".SZ", "") in text:
                symbols.add(sym)

        # 2. 通过公司名称匹配
        for company_name, symbol in self.COMPANY_TO_SYMBOL.items():
            if company_name.lower() in text_lower:
                symbols.add(symbol)

        # 3. 如果指定了目标symbol，检查是否相关
        if target_symbol:
            target_upper = target_symbol.upper()
            # 检查是否在symbols中
            if target_upper in symbols:
                return [target_upper]

            # 检查目标symbol对应的公司名称
            for company_name, symbol in self.COMPANY_TO_SYMBOL.items():
                if symbol.upper() == target_upper and company_name.lower() in text_lower:
                    return [target_upper]

            # 如果没有找到匹配，返回空（不包含目标symbol）
            return []

        return list(symbols)


class NewsAPIFetcher(NewsFetcher):
    """NewsAPI采集器（免费版每天100次请求）"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"

    async def fetch_news(
        self, symbol: Optional[str] = None, max_articles: int = 10
    ) -> List[NewsArticleData]:
        """从NewsAPI获取新闻"""
        if not self.api_key:
            logger.warning("NewsAPI key not configured, skipping")
            return []

        articles = []

        # 构建查询关键词
        query = self._build_query(symbol)

        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "apiKey": self.api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        for item in data.get("articles", []):
                            published_at = None
                            if item.get("publishedAt"):
                                try:
                                    published_at = datetime.fromisoformat(
                                        item["publishedAt"].replace("Z", "+00:00")
                                    )
                                except:
                                    pass

                            article = NewsArticleData(
                                source="newsapi",
                                title=item.get("title", ""),
                                content=item.get("description", ""),
                                url=item.get("url", ""),
                                author=item.get("author"),
                                published_at=published_at,
                                symbols=[symbol] if symbol else [],
                                source_id=item.get("url"),
                            )
                            articles.append(article)

                        logger.info(f"Fetched {len(articles)} articles from NewsAPI")
                    else:
                        logger.error(f"NewsAPI returned status {response.status}")

        except Exception as e:
            logger.error(f"Failed to fetch from NewsAPI: {e}")

        return articles

    def _build_query(self, symbol: Optional[str]) -> str:
        """构建搜索查询"""
        if symbol:
            # 移除后缀，获取公司名称
            base_symbol = symbol.replace(".HK", "").replace(".SH", "").replace(".SZ", "")

            # 常见公司名称映射
            company_names = {
                "AAPL": "Apple",
                "TSLA": "Tesla",
                "NVDA": "NVIDIA",
                "MSFT": "Microsoft",
                "GOOGL": "Google",
                "AMZN": "Amazon",
                "META": "Meta",
                "0700": "Tencent",
                "9988": "Alibaba",
                "600519": "Moutai",
            }

            company = company_names.get(base_symbol, base_symbol)
            return f"{company} stock market finance"
        else:
            return "stock market finance news"


class AKShareNewsFetcher(NewsFetcher):
    """AKShare新闻采集器（免费，中国市场）"""

    async def fetch_news(
        self, symbol: Optional[str] = None, max_articles: int = 10
    ) -> List[NewsArticleData]:
        """从AKShare获取新闻"""
        articles = []

        try:
            import akshare as ak

            # 获取财经新闻
            news_df = await asyncio.to_thread(
                ak.stock_news_em,
                symbol="全部"
            )

            if news_df is not None and not news_df.empty:
                for _, row in news_df.head(max_articles).iterrows():
                    try:
                        published_at = None
                        if '发布时间' in row and row['发布时间']:
                            try:
                                published_at = datetime.strptime(
                                    str(row['发布时间']), "%Y-%m-%d %H:%M:%S"
                                ).replace(tzinfo=timezone.utc)
                            except:
                                pass

                        # 提取股票代码
                        symbols = []
                        if symbol:
                            symbols = [symbol]

                        article = NewsArticleData(
                            source="akshare",
                            title=row.get('标题', ''),
                            content=row.get('内容', ''),
                            url=row.get('链接', ''),
                            author=row.get('来源', '东方财富'),
                            published_at=published_at,
                            symbols=symbols,
                            source_id=row.get('链接', ''),
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.warning(f"Failed to parse AKShare news item: {e}")
                        continue

                logger.info(f"Fetched {len(articles)} articles from AKShare")
        except Exception as e:
            logger.error(f"Failed to fetch from AKShare: {e}")

        return articles


class NewsAggregator:
    """新闻聚合器 - 整合多个数据源（优化版）"""

    def __init__(self, newsapi_key: Optional[str] = None, enable_advanced: bool = True):
        self.fetchers = [
            RSSFeedFetcher(),
            AKShareNewsFetcher(),
        ]

        if newsapi_key:
            self.fetchers.append(NewsAPIFetcher(newsapi_key))

        # 集成高级爬虫
        if enable_advanced:
            try:
                from app.services.news.advanced_fetchers import (
                    YahooFinanceFetcher, EastMoneyFetcher, SinaFinanceFetcher
                )
                self.fetchers.extend([YahooFinanceFetcher(), EastMoneyFetcher(), SinaFinanceFetcher()])
                logger.info(f"NewsAggregator initialized with {len(self.fetchers)} fetchers (advanced enabled)")
            except ImportError as e:
                logger.warning(f"Advanced fetchers not available: {e}")

        self._seen_urls = set()  # 增量去重缓存

    async def fetch_all_news(
        self, symbol: Optional[str] = None, max_per_source: int = 10, incremental: bool = True
    ) -> List[NewsArticleData]:
        """
        从所有数据源获取新闻（优化版）

        Args:
            symbol: 股票代码
            max_per_source: 每个数据源最多获取的文章数
            incremental: 是否启用增量爬取

        Returns:
            新闻文章列表
        """
        all_articles = []
        success_count = 0

        # 并发获取（带超时）
        async def fetch_with_timeout(fetcher, timeout=30.0):
            try:
                return await asyncio.wait_for(
                    fetcher.fetch_news(symbol, max_per_source), timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"{fetcher.__class__.__name__} timed out")
                return []
            except Exception as e:
                logger.error(f"{fetcher.__class__.__name__} error: {e}")
                return []

        tasks = [fetch_with_timeout(f) for f in self.fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Fetcher {self.fetchers[idx].__class__.__name__} failed: {result}")
            elif isinstance(result, list):
                success_count += 1
                all_articles.extend(result)

        logger.info(f"Fetched from {success_count}/{len(self.fetchers)} sources, total {len(all_articles)} articles")

        # 去重（基于URL和标题）
        seen_urls = set()
        seen_titles = set()
        unique_articles = []

        for article in all_articles:
            # 增量去重
            if incremental and article.url and article.url in self._seen_urls:
                continue

            if article.url and article.url in seen_urls:
                continue

            # 标题去重
            norm_title = " ".join(article.title.lower().split()) if article.title else ""
            if norm_title and norm_title in seen_titles:
                continue

            if article.url:
                seen_urls.add(article.url)
                if incremental:
                    self._seen_urls.add(article.url)
            if norm_title:
                seen_titles.add(norm_title)
            unique_articles.append(article)

        # 按发布时间排序
        unique_articles.sort(
            key=lambda x: x.published_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )

        # 限制缓存大小
        if len(self._seen_urls) > 10000:
            self._seen_urls = set(list(self._seen_urls)[-5000:])

        logger.info(f"Final: {len(unique_articles)} unique articles")
        return unique_articles
