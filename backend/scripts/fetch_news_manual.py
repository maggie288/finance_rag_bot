"""手动新闻采集脚本 - 改进的股票代码关联逻辑"""
import asyncio
import sys
import logging
from datetime import datetime, timezone
from typing import List, Optional

# 添加项目路径
sys.path.insert(0, '/Users/lydiadu/finance_rag_bot/backend')

from app.services.news.fetchers import RSSFeedFetcher, NewsArticleData
from app.services.news.storage import NewsStorageService
from app.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 改进的公司名称到股票代码映射
COMPANY_TO_SYMBOL = {
    # 美股科技公司
    "apple": "AAPL",
    "tesla": "TSLA",
    "elon musk": "TSLA",  # 马斯克通常关联Tesla
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
    "spacex": "TSLA",  # SpaceX和Tesla都是马斯克的公司

    # 中国公司
    "tencent": "0700.HK",
    "alibaba": "9988.HK",
    "moutai": "600519.SH",
    "kweichow moutai": "600519.SH",
    "wuliangye": "000858.SZ",
}

# 常见股票代码列表（用于直接匹配）
COMMON_SYMBOLS = [
    "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "INTC", "NFLX",
    "0700.HK", "9988.HK", "1810.HK",
    "600519.SH", "000858.SZ",
]


def extract_symbols_improved(title: str, content: Optional[str], target_symbol: Optional[str] = None) -> List[str]:
    """改进的股票代码提取逻辑"""
    symbols = set()
    text = f"{title} {content or ''}".upper()

    # 1. 直接匹配股票代码
    for symbol in COMMON_SYMBOLS:
        if symbol in text:
            symbols.add(symbol)

    # 2. 通过公司名称匹配
    text_lower = text.lower()
    for company_name, symbol in COMPANY_TO_SYMBOL.items():
        if company_name.lower() in text_lower:
            symbols.add(symbol)
            logger.debug(f"Found company name '{company_name}' -> {symbol}")

    # 3. 如果指定了目标symbol，检查是否相关
    if target_symbol:
        target_upper = target_symbol.upper()
        # 检查是否在symbols中
        if target_upper in symbols:
            return [target_upper]

        # 检查目标symbol对应的公司名称
        for company_name, symbol in COMPANY_TO_SYMBOL.items():
            if symbol.upper() == target_upper and company_name.lower() in text_lower:
                return [target_upper]

        # 如果没有找到匹配，返回空（不包含目标symbol）
        return []

    return list(symbols)


async def fetch_and_save_news(symbol: Optional[str] = None, max_articles: int = 20):
    """获取并保存新闻"""
    logger.info(f"Starting news fetch for symbol: {symbol}")

    # 获取RSS新闻
    fetcher = RSSFeedFetcher()
    articles = await fetcher.fetch_news(symbol=None, max_articles=max_articles)

    logger.info(f"Fetched {len(articles)} articles from RSS")

    # 重新提取股票代码（使用改进的逻辑）
    processed_articles = []
    for article in articles:
        # 使用改进的提取逻辑
        symbols = extract_symbols_improved(article.title, article.content, target_symbol=symbol)

        # 如果指定了symbol但没有匹配，跳过
        if symbol and not symbols:
            continue

        # 更新文章的symbols
        article.symbols = symbols
        processed_articles.append(article)

        logger.info(f"Article: {article.title[:80]}... -> Symbols: {symbols}")

    logger.info(f"Processed {len(processed_articles)} articles (matched symbol filter)")

    # 保存到数据库
    if processed_articles:
        async with AsyncSessionLocal() as db:
            saved = await NewsStorageService.save_articles(db, processed_articles, sentiment_results=None)
            logger.info(f"Saved {len(saved)} articles to database")
            return len(saved)

    return 0


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="手动获取新闻")
    parser.add_argument("--symbol", type=str, help="股票代码（可选）")
    parser.add_argument("--max", type=int, default=20, help="每个数据源最多获取的文章数")

    args = parser.parse_args()

    try:
        saved_count = await fetch_and_save_news(symbol=args.symbol, max_articles=args.max)
        print(f"\n✅ 成功保存 {saved_count} 篇新闻")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
