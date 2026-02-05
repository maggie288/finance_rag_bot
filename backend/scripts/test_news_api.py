"""测试新闻API端点"""
import requests
import json
from datetime import datetime

# API配置
BASE_URL = "http://localhost:8000/api/v1"

# 测试用户凭据（需要先登录）
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"


def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        return None


def get_news_feed(token, symbol=None, page=1, page_size=10):
    """获取新闻列表"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": page, "page_size": page_size}
    if symbol:
        params["symbol"] = symbol

    response = requests.get(
        f"{BASE_URL}/news/feed",
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 获取新闻失败: {response.status_code}")
        print(response.text)
        return None


def fetch_news(token, symbol=None, max_articles=20):
    """手动触发新闻采集"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"max_articles": max_articles}
    if symbol:
        params["symbol"] = symbol

    response = requests.post(
        f"{BASE_URL}/news/fetch",
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ 触发采集失败: {response.status_code}")
        print(response.text)
        return None


def main():
    print("🔑 正在登录...")
    token = login()

    if not token:
        print("\n⚠️  登录失败，请确保:")
        print("   1. 后端服务正在运行")
        print("   2. 测试用户已创建（或修改脚本中的TEST_EMAIL和TEST_PASSWORD）")
        return

    print("✅ 登录成功\n")

    # 测试1: 获取TSLA新闻
    print("=" * 80)
    print("📊 测试1: 查询TSLA相关新闻")
    print("=" * 80)
    result = get_news_feed(token, symbol="TSLA", page_size=10)
    if result:
        articles = result.get("articles", [])
        print(f"找到 {len(articles)} 篇TSLA相关新闻:\n")
        for i, article in enumerate(articles, 1):
            print(f"{i}. 标题: {article['title']}")
            print(f"   来源: {article['source']}")
            print(f"   股票代码: {article['symbols']}")
            print(f"   发布时间: {article['published_at']}")
            print(f"   情感: {article['sentiment_label']} (分数: {article['sentiment_score']})")
            print()

    # 测试2: 获取所有最新新闻
    print("=" * 80)
    print("📰 测试2: 查询最新新闻（所有股票）")
    print("=" * 80)
    result = get_news_feed(token, page_size=10)
    if result:
        articles = result.get("articles", [])
        print(f"找到 {len(articles)} 篇最新新闻:\n")
        for i, article in enumerate(articles, 1):
            symbols_str = ', '.join(article['symbols']) if article['symbols'] else '无'
            print(f"{i}. {article['title'][:80]}")
            print(f"   股票: {symbols_str} | 来源: {article['source']} | 发布: {article['published_at']}")

    # 测试3: 手动触发新闻采集
    print("\n" + "=" * 80)
    print("🔄 测试3: 手动触发TSLA新闻采集")
    print("=" * 80)
    print("正在触发采集任务...")
    result = fetch_news(token, symbol="TSLA", max_articles=20)
    if result:
        print(f"✅ 任务已启动:")
        print(f"   任务ID: {result['task_id']}")
        print(f"   股票代码: {result['symbol']}")
        print(f"   最大文章数: {result['max_articles']}")
        print("\n⏳ 请等待几秒后再次查询新闻列表")


if __name__ == "__main__":
    main()
