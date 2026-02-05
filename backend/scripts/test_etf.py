#!/usr/bin/env python3
"""测试A股ETF支持的脚本"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.market_data.tushare_provider import TuShareProvider


async def main():
    print("=" * 50)
    print("测试 A股 ETF 支持")
    print("=" * 50)
    
    provider = TuShareProvider()
    
    # 测试 ETF (50xxx, 51xxx, 15xxx, 16xxx)
    etf_stocks = [
        "510300.SH",  # 沪深300ETF
        "159920.SZ",  # 恒生ETF
        "513100.SH",  # 纳指ETF
    ]
    
    print("\n【A股ETF测试】")
    for symbol in etf_stocks:
        try:
            is_etf = provider._is_etf(symbol)
            print(f"{symbol}: is_etf={is_etf}", end=" ")
            if is_etf:
                quote = await provider.get_quote(symbol)
                print(f"name='{quote.name}', price={quote.price}")
            else:
                print("❌ 未识别为ETF")
        except Exception as e:
            print(f"❌ 失败 - {e}")
    
    # 测试普通股票
    stocks = [
        "600556.SH",  # 天下秀
        "000998.SZ",  # 隆平高科
    ]
    
    print("\n【普通A股测试】")
    for symbol in stocks:
        try:
            is_etf = provider._is_etf(symbol)
            print(f"{symbol}: is_etf={is_etf}", end=" ")
            quote = await provider.get_quote(symbol)
            print(f"name='{quote.name}', price={quote.price}")
        except Exception as e:
            print(f"❌ 失败 - {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
