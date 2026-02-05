# 新闻数据采集模块

## 功能概述

新闻采集模块自动从多个数据源获取财经新闻，进行情感分析，并存储到数据库中。支持按股票代码定时更新，使用免费数据源。

## 数据源

### 1. RSS Feeds (免费)
- **美国财经媒体**: Reuters, CNBC, Bloomberg, WSJ, FT, Investing
- **中国财经媒体**: 新浪财经, 东方财富, 财新网
- **央行新闻**: Federal Reserve, 中国人民银行

### 2. NewsAPI (免费版)
- 每天100次请求
- 覆盖全球主流媒体
- 需要配置 `NEWSAPI_KEY` 环境变量

### 3. AKShare (免费)
- 中国市场专用
- 东方财富网新闻
- 无需API密钥

## 配置

### 环境变量

在 `.env` 文件中添加:

```bash
# 可选：NewsAPI密钥 (免费版每天100次)
NEWSAPI_KEY=your_newsapi_key_here
```

获取 NewsAPI 密钥: https://newsapi.org/register

## 使用方式

### 1. 自动定时任务

系统会自动运行定时任务:

- **全市场新闻**: 每小时获取一次
- **热门股票**: 每30分钟更新一次
  - 美股: AAPL, TSLA, NVDA, MSFT, GOOGL
  - 港股: 0700.HK (腾讯), 9988.HK (阿里)
  - A股: 600519.SH (茅台), 000858.SZ (五粮液)

### 2. 手动触发 API

```bash
# 获取所有财经新闻
POST /api/v1/news/fetch

# 获取特定股票的新闻
POST /api/v1/news/fetch?symbol=AAPL&max_articles=20
```

### 3. 查询新闻

```bash
# 获取新闻列表
GET /api/v1/news/feed?symbol=AAPL&page=1&page_size=20

# 按来源过滤
GET /api/v1/news/feed?source=reuters_finance
```

## 代码示例

### Python - 直接使用服务

```python
from app.services.news import NewsAggregator, SentimentAnalyzer, NewsStorageService
from app.db.session import async_session_maker

# 初始化服务
aggregator = NewsAggregator(newsapi_key="your_key")
sentiment_analyzer = SentimentAnalyzer(model_name="deepseek")

# 获取新闻
articles = await aggregator.fetch_all_news(symbol="AAPL", max_per_source=10)

# 情感分析
article_dicts = [{"title": a.title, "content": a.content} for a in articles]
sentiment_results = await sentiment_analyzer.batch_analyze(article_dicts)

# 保存到数据库
async with async_session_maker() as db:
    saved = await NewsStorageService.save_articles(db, articles, sentiment_results)
    print(f"Saved {len(saved)} articles")
```

### Celery Task

```python
from app.workers.news_tasks import fetch_news_for_symbol

# 异步执行
task = fetch_news_for_symbol.apply_async(
    args=["AAPL", 20],
    countdown=1  # 1秒后执行
)

print(f"Task ID: {task.id}")
```

## 启动 Celery Worker

```bash
# 进入backend目录
cd backend

# 启动 Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# 启动 Celery beat (定时任务调度器)
celery -A app.workers.celery_app beat --loglevel=info
```

## 数据库模型

### NewsArticle

```python
{
    "id": "uuid",
    "source": "reuters_finance",  # 数据源
    "title": "Apple announces new...",
    "content": "Full article content...",
    "url": "https://...",
    "author": "John Doe",
    "symbols": ["AAPL", "MSFT"],  # 相关股票
    "sentiment_score": 0.75,  # -1.0 到 1.0
    "sentiment_label": "positive",  # positive/negative/neutral
    "published_at": "2026-02-04T10:00:00Z",
    "created_at": "2026-02-04T10:05:00Z"
}
```

## 情感分析

使用 LLM (DeepSeek) 分析新闻情感:

- **score**: -1.0 (极度看跌) 到 1.0 (极度看涨)
- **label**: positive (看涨) / negative (看跌) / neutral (中性)
- **confidence**: 分析置信度 (0.0 - 1.0)
- **reasoning**: AI 分析理由

## 故障排除

### 1. Celery 任务不执行

```bash
# 检查 Redis 是否运行
redis-cli ping

# 检查 Celery worker 是否启动
celery -A app.workers.celery_app inspect active
```

### 2. 新闻数据为空

- 检查 RSS 源是否可访问
- 验证 NewsAPI 密钥是否有效
- 查看日志: `tail -f logs/celery.log`

### 3. 情感分析失败

- 检查 LLM API 密钥配置
- 验证 DeepSeek API 额度
- 查看 `sentiment_score` 是否为 null

## 扩展方案

### 添加新的 RSS 源

编辑 `fetchers.py`:

```python
RSS_FEEDS = {
    # ... 现有源
    "my_source": "https://example.com/rss",
}
```

### 自定义情感分析模型

编辑 `sentiment.py`:

```python
analyzer = SentimentAnalyzer(model_name="claude")  # 使用 Claude
```

### 调整定时任务频率

编辑 `news_tasks.py`:

```python
sender.add_periodic_task(
    1800.0,  # 改为 1800 秒 (30分钟)
    fetch_all_market_news.s(),
    name="fetch_market_news"
)
```

## 成本估算

- **RSS Feeds**: 完全免费
- **AKShare**: 完全免费
- **NewsAPI**: 免费版每天100次请求
- **LLM 情感分析**:
  - DeepSeek: ~$0.0001/次 (每篇新闻)
  - 每天200篇新闻 ≈ $0.02/天

## 未来优化

1. 支持更多数据源 (Twitter, YouTube)
2. 增加新闻去重算法
3. 实现增量更新
4. 添加新闻质量评分
5. 支持多语言新闻翻译
