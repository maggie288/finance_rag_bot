"""新闻服务模块"""
from app.services.news.fetchers import (
    NewsArticleData,
    NewsFetcher,
    RSSFeedFetcher,
    NewsAPIFetcher,
    AKShareNewsFetcher,
    NewsAggregator,
)
from app.services.news.sentiment import SentimentAnalyzer
from app.services.news.storage import NewsStorageService

# 高级爬虫（可选导入）
try:
    from app.services.news.advanced_fetchers import (
        YahooFinanceFetcher,
        EastMoneyFetcher,
        SinaFinanceFetcher,
    )
    from app.services.news.crawler_base import CrawlerConfig, BaseCrawler
    from app.services.news.symbol_matcher import SmartSymbolMatcher, SymbolMatch

    __all__ = [
        "NewsArticleData",
        "NewsFetcher",
        "RSSFeedFetcher",
        "NewsAPIFetcher",
        "AKShareNewsFetcher",
        "NewsAggregator",
        "SentimentAnalyzer",
        "NewsStorageService",
        # 高级爬虫
        "YahooFinanceFetcher",
        "EastMoneyFetcher",
        "SinaFinanceFetcher",
        "CrawlerConfig",
        "BaseCrawler",
        "SmartSymbolMatcher",
        "SymbolMatch",
    ]
except ImportError:
    __all__ = [
        "NewsArticleData",
        "NewsFetcher",
        "RSSFeedFetcher",
        "NewsAPIFetcher",
        "AKShareNewsFetcher",
        "NewsAggregator",
        "SentimentAnalyzer",
        "NewsStorageService",
    ]
