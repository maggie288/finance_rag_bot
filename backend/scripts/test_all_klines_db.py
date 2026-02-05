#!/usr/bin/env python3
"""测试所有市场的K线数据存储到数据库"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.services.market_data.aggregator import market_data
from app.services.market_data.repository import StockDataRepository


async def test_all_markets_kline_db():
    print("=" * 60)
    print("测试所有市场 K线 数据存储")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        repo = StockDataRepository(db)
        
        test_cases = [
            # A股
            {"symbol": "600556.SH", "market": "cn", "name": "天下秀"},
            # 港股
            {"symbol": "0700.HK", "market": "hk", "name": "腾讯"},
            # 美股
            {"symbol": "AAPL", "market": "us", "name": "Apple"},
            # 加密货币
            {"symbol": "BTC/USD", "market": "commodity", "name": "Bitcoin"},
            {"symbol": "ETH/USD", "market": "commodity", "name": "Ethereum"},
        ]
        
        for tc in test_cases:
            symbol = tc["symbol"]
            market = tc["market"]
            
            print(f"\n【{tc['name']} ({symbol}) - {market}】")
            
            try:
                # 调用 get_kline（传入 db 参数以保存到数据库）
                klines = await market_data.get_kline(
                    symbol=symbol,
                    market=market,
                    interval="1day",
                    outputsize=5,
                    db=db,
                    force_refresh=True
                )
                
                print(f"  ✓ API获取: {len(klines)} 条K线")
                
                if klines:
                    latest = klines[0]
                    print(f"    最新: {latest.datetime} close={latest.close}")
                
                # 从数据库验证
                db_klines = await repo.get_klines(
                    symbol=symbol,
                    market=market,
                    interval="1day",
                    limit=10
                )
                
                print(f"  ✓ DB存储: {len(db_klines)} 条K线")
                
                if db_klines:
                    latest_db = db_klines[0]
                    print(f"    最新: {latest_db.datetime} close={latest_db.close}")
                
            except Exception as e:
                print(f"  ✗ 失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 检查数据库中的所有K线
        print("\n" + "=" * 60)
        print("数据库中的 K线 统计")
        print("=" * 60)
        
        markets = ["cn", "hk", "us", "commodity"]
        for market in markets:
            try:
                all_quotes = await repo.get_all_quotes(market=market)
                print(f"\n{market}: {len(all_quotes)} 条行情数据")
                for q in all_quotes[:3]:
                    print(f"  - {q.symbol}: {q.name} @ {q.price}")
            except Exception as e:
                print(f"  ✗ 查询失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_all_markets_kline_db())
