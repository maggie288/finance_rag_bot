# 新闻资讯功能使用指南

## 功能概述

单个股票的新闻资讯模块可以自动采集和分析与该股票相关的财经新闻，并提供AI情感分析。

## 主要特性

### 1. 多数据源新闻采集
- **美国财经媒体**: CNBC, Bloomberg, WSJ, Financial Times
- **免费数据源**: 使用RSS feeds，无需API密钥
- **自动去重**: 基于URL自动去重，避免重复新闻

### 2. AI情感分析
- 使用 DeepSeek AI 对每条新闻进行情感分析
- **情感标签**: 看涨(positive) / 看跌(negative) / 中性(neutral)
- **情感评分**: -1.0 到 1.0 的数值评分

### 3. 定时自动更新
- **全市场新闻**: 每小时自动采集一次
- **热门股票**: 每30分钟更新一次
  - 美股: AAPL, TSLA, NVDA, MSFT, GOOGL
  - 港股: 0700.HK (腾讯), 9988.HK (阿里)
  - A股: 600519.SH (茅台), 000858.SZ (五粮液)

## 使用方法

### 1. 访问股票新闻页面

在单个股票详情页，点击 **"新闻资讯"** 按钮进入新闻页面。

路径: `/market/{symbol}/news?market={market}`

例如:
- AAPL (美股): `/market/AAPL/news?market=us`
- 0700.HK (腾讯): `/market/0700.HK/news?market=hk`
- 600519.SH (茅台): `/market/600519.SH/news?market=cn`

### 2. 手动获取新闻

点击页面右上角的 **"获取新闻"** 按钮，可以立即触发新闻采集任务。

**注意**:
- 新闻采集需要约1-5分钟完成
- 任务提交后会自动在后台执行
- 10秒后页面会自动刷新显示新数据

### 3. 查看新闻详情

每条新闻卡片显示:
- **标题**: 新闻标题
- **摘要**: 新闻内容简介（前200字）
- **情感标签**: 看涨/看跌/中性标签及评分
- **来源信息**: 数据源、作者、发布时间
- **原文链接**: 点击"阅读"按钮跳转到原文

### 4. 情感标签说明

| 标签 | 颜色 | 说明 | 评分范围 |
|------|------|------|----------|
| 看涨 (positive) | 绿色 ↗ | 利好消息，可能推动股价上涨 | 0.2 ~ 1.0 |
| 看跌 (negative) | 红色 ↘ | 利空消息，可能导致股价下跌 | -1.0 ~ -0.2 |
| 中性 (neutral) | 灰色 − | 对股价影响不明显 | -0.2 ~ 0.2 |

## 后台服务

### Celery Worker
负责执行新闻采集任务，包括:
- 从多个数据源获取新闻
- 使用AI进行情感分析
- 保存到数据库

### Celery Beat
定时任务调度器，负责:
- 每小时自动采集全市场新闻
- 每30分钟更新热门股票新闻

## 服务状态检查

使用启动脚本检查所有服务状态:

```bash
./start.sh status
```

应该看到:
```
=== 服务状态 ===
✓ PostgreSQL: 运行中 (localhost:5432)
✓ Redis:      运行中 (localhost:6379)
✓ 后端 API:   运行中 (http://localhost:8000)
✓ API 文档:   http://localhost:8000/docs
✓ Celery Worker: 运行中 (新闻采集功能)
✓ Celery Beat:   运行中 (定时任务调度)
✓ 前端应用:   运行中 (http://localhost:3000)
```

## 查看日志

### 后端日志
```bash
tail -f .backend.log
```

### Celery Worker 日志
```bash
tail -f .celery.log
```

### Celery Beat 日志
```bash
tail -f .celery-beat.log
```

## API 接口

### 1. 获取新闻列表
```http
GET /api/v1/news/feed?symbol={symbol}&page_size=30
```

参数:
- `symbol` (可选): 股票代码
- `source` (可选): 数据源过滤
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20, 最大 50)

### 2. 手动触发新闻采集
```http
POST /api/v1/news/fetch?symbol={symbol}&max_articles=20
```

参数:
- `symbol` (可选): 股票代码，不指定则获取所有财经新闻
- `max_articles`: 每个数据源最多获取的文章数 (默认 20, 最大 50)

返回:
```json
{
  "message": "新闻采集任务已启动",
  "task_id": "df00fd8f-d3d3-428a-962a-f722abc303dc",
  "symbol": "AAPL",
  "max_articles": 20
}
```

## 数据统计

查看数据库中的新闻统计:

```bash
docker exec finance_rag_bot-postgres-1 psql -U finance_bot -d finance_rag_bot -c \
"SELECT
    COUNT(*) as total_news,
    COUNT(DISTINCT source) as sources,
    COUNT(CASE WHEN sentiment_label IS NOT NULL THEN 1 END) as with_sentiment,
    MIN(published_at) as oldest,
    MAX(published_at) as newest
FROM news_articles;"
```

按来源统计:
```bash
docker exec finance_rag_bot-postgres-1 psql -U finance_bot -d finance_rag_bot -c \
"SELECT
    source,
    COUNT(*) as count,
    AVG(sentiment_score) as avg_sentiment
FROM news_articles
GROUP BY source
ORDER BY count DESC;"
```

## 故障排除

### 1. 新闻采集任务不执行

检查 Celery 服务是否运行:
```bash
ps aux | grep celery
```

重启 Celery 服务:
```bash
kill $(cat .celery.pid)
kill $(cat .celery-beat.pid)
./start.sh  # 重新启动所有服务
```

### 2. 新闻数据为空

手动触发采集:
```bash
# 方法1: 通过前端页面点击"获取新闻"按钮
# 方法2: 直接调用 Celery 任务
cd backend
python << 'EOF'
from app.workers.news_tasks import fetch_all_market_news
result = fetch_all_market_news.delay()
print(f"任务ID: {result.id}")
EOF
```

### 3. 情感分析失败

检查 DeepSeek API 配置:
```bash
# 确保 .env 文件中配置了 DEEPSEEK_API_KEY
cat backend/.env | grep DEEPSEEK_API_KEY
```

### 4. Redis 连接失败

检查 Redis 服务:
```bash
docker exec finance_rag_bot-redis-1 redis-cli ping
# 应该返回: PONG
```

## 成本估算

- **RSS Feeds**: 完全免费
- **DeepSeek API**: 约 $0.0001/次分析
- **每天采集量**:
  - 全市场新闻: 24次 × 68篇 ≈ 1632篇/天
  - 热门股票: 48次 × 10篇 ≈ 480篇/天
- **每日成本**: 约 $0.21/天 (仅AI分析费用)

## 扩展功能 (未来)

- [ ] 支持 Twitter 新闻源
- [ ] 支持 YouTube 视频新闻
- [ ] 新闻翻译功能
- [ ] 新闻摘要生成
- [ ] 自定义关键词订阅
- [ ] 新闻推送通知

---

## 问题修复记录 (2026-02-05)

### 问题描述
查询特定股票代码（如TSLA）的新闻时，数据库返回空结果。

### 根本原因
原始的股票代码提取逻辑过于简单，只能识别文章中直接出现的股票代码（如"TSLA"），无法识别公司名称（如"Tesla"、"Elon Musk"、"SpaceX"）。

### 解决方案

#### 1. 改进股票代码提取逻辑
在 [backend/app/services/news/fetchers.py](backend/app/services/news/fetchers.py:138) 中：
- **添加公司名称映射表**：将常见公司名称映射到股票代码
- **改进 `_extract_symbols` 方法**：支持公司名称匹配

支持的公司名称映射：
- Tesla, Elon Musk, SpaceX → TSLA
- Apple → AAPL
- NVIDIA → NVDA
- 等等...

#### 2. 创建手动采集脚本
[backend/scripts/fetch_news_manual.py](backend/scripts/fetch_news_manual.py) - 用于手动触发新闻采集。

使用方法：
```bash
cd backend

# 获取TSLA相关新闻
python scripts/fetch_news_manual.py --symbol TSLA --max 20

# 获取所有财经新闻
python scripts/fetch_news_manual.py --max 30
```

#### 3. 创建API测试脚本
[backend/scripts/test_news_api.py](backend/scripts/test_news_api.py) - 用于测试新闻API端点。

使用方法：
```bash
cd backend
python scripts/test_news_api.py
```

### 验证结果
执行修复后：
- ✅ 从RSS源获取了90+篇新闻
- ✅ 识别出SpaceX相关新闻并关联到TSLA
- ✅ 保存了103篇新闻到数据库
- ✅ 支持通过API查询TSLA相关新闻

---

**文档版本**: v1.1
**最后更新**: 2026-02-05
**维护**: Finance RAG Bot Team
