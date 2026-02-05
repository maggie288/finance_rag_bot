"""高级新闻爬虫 - 支持更多数据源"""
from __future__ import annotations

import logging
import asyncio
import re
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from app.services.news.fetchers import NewsArticleData, NewsFetcher
from app.services.news.crawler_base import BaseCrawler, CrawlerConfig

logger = logging.getLogger(__name__)


class YahooFinanceCrawler(BaseCrawler):
    """Yahoo Finance 新闻爬虫（免费）"""

    BASE_URL = "https://finance.yahoo.com"

    async def crawl(self, symbol: Optional[str] = None, max_articles: int = 10) -> List[NewsArticleData]:
        articles = []
        try:
            if symbol:
                clean_symbol = symbol.replace(".HK", "").replace(".SH", "").replace(".SZ", "")
                url = f"{self.BASE_URL}/quote/{clean_symbol}/news"
            else:
                url = f"{self.BASE_URL}/news"

            self.stats["total_requests"] += 1
            html = await self.session.fetch_text(url)
            soup = BeautifulSoup(html, 'html.parser')

            # 查找新闻列表
            news_items = soup.select('li[class*="stream-item"]')[:max_articles]

            for item in news_items:
                try:
                    link = item.find('a')
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    article_url = urljoin(self.BASE_URL, link.get('href', ''))

                    summary = item.find('p')
                    content = summary.get_text(strip=True) if summary else None

                    article = NewsArticleData(
                        source="yahoo_finance",
                        title=title,
                        content=content,
                        url=article_url,
                        author="Yahoo Finance",
                        published_at=datetime.now(timezone.utc),
                        symbols=[symbol] if symbol else [],
                    )
                    articles.append(article)
                except Exception as e:
                    logger.debug(f"Failed to parse Yahoo item: {e}")
                    continue

            self.stats["successful_requests"] += 1
            logger.info(f"Yahoo Finance: {len(articles)} articles")
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Yahoo Finance error: {e}")

        return articles


class EastMoneyCrawler(BaseCrawler):
    """东方财富网新闻爬虫（免费，中文）"""

    API_URL = "https://np-anotice-stock.eastmoney.com/api/content/ann"

    async def crawl(self, symbol: Optional[str] = None, max_articles: int = 10) -> List[NewsArticleData]:
        articles = []
        try:
            params = {
                "page_index": 1,
                "page_size": max_articles,
                "type": "0,1,2,3,4",
            }

            if symbol and symbol.endswith(('.SH', '.SZ')):
                params['stock_list'] = symbol.split('.')[0]

            self.stats["total_requests"] += 1
            data = await self.session.fetch_json(self.API_URL, params=params)

            if data and 'data' in data and 'list' in data['data']:
                for item in data['data']['list']:
                    try:
                        published_at = None
                        if 'notice_date' in item:
                            timestamp = int(item['notice_date']) / 1000
                            published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                        article = NewsArticleData(
                            source="eastmoney",
                            title=item.get('title', ''),
                            content=item.get('content', '')[:500],
                            url=item.get('url', ''),
                            author=item.get('org_name', '东方财富网'),
                            published_at=published_at,
                            symbols=[symbol] if symbol else [],
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.debug(f"Failed to parse EastMoney item: {e}")
                        continue

            self.stats["successful_requests"] += 1
            logger.info(f"EastMoney: {len(articles)} articles")
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"EastMoney error: {e}")

        return articles


class SinaFinanceCrawler(BaseCrawler):
    """新浪财经新闻爬虫（免费，中文）"""

    API_URL = "https://feed.sina.com.cn/api/roll/get"

    async def crawl(self, symbol: Optional[str] = None, max_articles: int = 10) -> List[NewsArticleData]:
        articles = []
        try:
            params = {
                "pageid": "153",
                "lid": "2509",
                "num": max_articles,
                "page": 1,
            }

            self.stats["total_requests"] += 1
            data = await self.session.fetch_json(self.API_URL, params=params)

            if data and 'result' in data and 'data' in data['result']:
                for item in data['result']['data']:
                    try:
                        published_at = None
                        if 'ctime' in item:
                            published_at = datetime.strptime(
                                item['ctime'], "%Y-%m-%d %H:%M:%S"
                            ).replace(tzinfo=timezone.utc)

                        article = NewsArticleData(
                            source="sina_finance",
                            title=item.get('title', ''),
                            content=item.get('intro', ''),
                            url=item.get('url', ''),
                            author=item.get('media_name', '新浪财经'),
                            published_at=published_at,
                            symbols=[symbol] if symbol else [],
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.debug(f"Failed to parse Sina item: {e}")
                        continue

            self.stats["successful_requests"] += 1
            logger.info(f"Sina Finance: {len(articles)} articles")
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Sina Finance error: {e}")

        return articles


# 包装类，实现NewsFetcher接口
class YahooFinanceFetcher(NewsFetcher):
    """Yahoo Finance爬虫封装"""
    async def fetch_news(self, symbol: Optional[str] = None, max_articles: int = 10) -> List[NewsArticleData]:
        config = CrawlerConfig(
            requests_per_second=2.0,
            max_retries=3,
            connect_timeout=10.0,
            read_timeout=30.0
        )
        crawler = YahooFinanceCrawler(config)
        return await crawler.run(symbol=symbol, max_articles=max_articles)


class EastMoneyFetcher(NewsFetcher):
    """东方财富网爬虫封装"""
    async def fetch_news(self, symbol: Optional[str] = None, max_articles: int = 10) -> List[NewsArticleData]:
        config = CrawlerConfig(
            requests_per_second=3.0,
            max_retries=3,
            connect_timeout=10.0,
            read_timeout=30.0
        )
        crawler = EastMoneyCrawler(config)
        return await crawler.run(symbol=symbol, max_articles=max_articles)


class SinaFinanceFetcher(NewsFetcher):
    """新浪财经爬虫封装"""
    async def fetch_news(self, symbol: Optional[str] = None, max_articles: int = 10) -> List[NewsArticleData]:
        config = CrawlerConfig(
            requests_per_second=3.0,
            max_retries=3,
            connect_timeout=10.0,
            read_timeout=30.0
        )
        crawler = SinaFinanceCrawler(config)
        return await crawler.run(symbol=symbol, max_articles=max_articles)
