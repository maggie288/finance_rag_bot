#!/usr/bin/env python3
"""调试 ETH/USD 问题"""

import asyncio
import httpx


async def test_eth():
    print("=" * 50)
    print("调试 ETH/USD")
    print("=" * 50)
    
    # 测试不同的交易对格式
    pairs = ["ETHUSDT", "ETHUSD"]
    
    for pair in pairs:
        print(f"\n【{pair}】")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": pair},
                timeout=10,
            )
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Symbol: {data.get('symbol')}")
                print(f"Price: {data.get('lastPrice')}")
            else:
                print(f"Error: {resp.text}")


if __name__ == "__main__":
    asyncio.run(test_eth())
