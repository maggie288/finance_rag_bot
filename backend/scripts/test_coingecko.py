#!/usr/bin/env python3
"""测试 CoinGecko API"""

import asyncio
import httpx


async def test_coingecko():
    print("=" * 50)
    print("测试 CoinGecko API")
    print("=" * 50)
    
    # 测试 simple price API
    print("\n【BTC/USD 价格】")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10,
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    
    # 测试 market chart API
    print("\n【BTC/USD 历史数据】")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": 7},
            timeout=15,
        )
        data = resp.json()
        print(f"Status: {resp.status_code}")
        print(f"Keys: {list(data.keys())}")
        if "prices" in data:
            print(f"Prices: {len(data['prices'])} points")
            print(f"First price: {data['prices'][0]}")
            print(f"Last price: {data['prices'][-1]}")


if __name__ == "__main__":
    asyncio.run(test_coingecko())
