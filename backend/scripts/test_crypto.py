#!/usr/bin/env python3
"""测试加密货币获取功能 - Binance API"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_binance():
    import httpx
    
    print("=" * 50)
    print("直接测试 Binance API")
    print("=" * 50)
    
    # 测试24小时行情
    print("\n【BTCUSDT 24小时行情】")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": "BTCUSDT"},
            timeout=10,
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Symbol: {data.get('symbol')}")
        print(f"Price: {data.get('lastPrice')}")
        print(f"Change: {data.get('priceChangePercent')}%")
    
    # 测试K线
    print("\n【BTCUSDT K线】")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1d", "limit": 5},
            timeout=15,
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"获取 {len(data)} 条K线")
        for v in data:
            print(f"  Time: {datetime.fromtimestamp(v[0]/1000)} Close: {v[4]}")


async def test_crypto():
    print("\n" + "=" * 50)
    print("测试 TwelveDataProvider")
    print("=" * 50)
    
    from app.services.market_data.twelvedata import TwelveDataProvider
    
    provider = TwelveDataProvider()
    
    # 测试 BTC/USD
    print("\n【BTC/USD】")
    quote = await provider.get_quote("BTC/USD")
    print(f"名称: {quote.name}")
    print(f"价格: {quote.price}")
    print(f"涨跌幅: {quote.change_percent}%")
    
    # 测试 K线
    print("\n【BTC/USD K线】")
    klines = await provider.get_kline("BTC/USD", "1day", 5)
    print(f"获取 {len(klines)} 条K线")
    for k in klines:
        print(f"  {k.datetime}: close={k.close}")
    
    # 测试 ETH/USD
    print("\n【ETH/USD】")
    quote = await provider.get_quote("ETH/USD")
    print(f"名称: {quote.name}")
    print(f"价格: {quote.price}")
    print(f"涨跌幅: {quote.change_percent}%")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(test_binance())
    asyncio.run(test_crypto())
