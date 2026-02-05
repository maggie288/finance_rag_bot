#!/usr/bin/env python3
"""验证所有市场的K线API获取逻辑"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.market_data.twelvedata import TwelveDataProvider
from app.services.market_data.tushare_provider import TuShareProvider


async def test_all_providers():
    print("=" * 60)
    print("验证所有市场的K线获取")
    print("=" * 60)
    
    twelvedata = TwelveDataProvider()
    tushare = TuShareProvider()
    
    test_cases = [
        # 美股 (TwelveData)
        {"symbol": "AAPL", "provider": "twelvedata", "name": "Apple"},
        {"symbol": "TSLA", "provider": "twelvedata", "name": "Tesla"},
        {"symbol": "NVDA", "provider": "twelvedata", "name": "Nvidia"},
        
        # 加密货币 (TwelveData - Binance)
        {"symbol": "BTC/USD", "provider": "twelvedata", "name": "Bitcoin"},
        {"symbol": "ETH/USD", "provider": "twelvedata", "name": "Ethereum"},
        
        # A股 (TuShare)
        {"symbol": "600556.SH", "provider": "tushare", "name": "天下秀"},
        
        # 港股 (TuShare)
        {"symbol": "0700.HK", "provider": "tushare", "name": "腾讯"},
    ]
    
    for tc in test_cases:
        symbol = tc["symbol"]
        provider_name = tc["provider"]
        provider = twelvedata if provider_name == "twelvedata" else tushare
        
        print(f"\n【{tc['name']} ({symbol}) - {provider_name}】")
        
        try:
            # 获取K线
            klines = await provider.get_kline(symbol, "1day", 5)
            
            if klines and len(klines) > 0:
                print(f"  ✓ 获取成功: {len(klines)} 条")
                latest = klines[0]
                print(f"    最新: {latest.datetime} open={latest.open:.2f} high={latest.high:.2f} low={latest.low:.2f} close={latest.close:.2f}")
            else:
                print(f"  ✗ 无数据")
                
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("验证完成 - 所有K线数据应存入数据库")
    print("=" * 60)
    print("\n存储逻辑说明:")
    print("- 通过 aggregator.get_kline() 调用时会自动存入数据库")
    print("- 前端请求 market/kline 接口时会调用 aggregator")
    print("- 需要传入 db 参数才能存储")
    print("- 数据库存储由 repository.save_klines() 完成")


if __name__ == "__main__":
    asyncio.run(test_all_providers())
