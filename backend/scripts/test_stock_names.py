#!/usr/bin/env python3
"""手动刷新股票名称的脚本"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.market_data.tushare_provider import TuShareProvider


async def main():
    print("=" * 50)
    print("测试 TuShare API 获取股票名称")
    print("=" * 50)
    
    provider = TuShareProvider()
    
    # 测试 A 股
    cn_stocks = ["600556.SH", "000998.SZ"]
    print("\n【A股测试】")
    for symbol in cn_stocks:
        try:
            quote = await provider.get_quote(symbol)
            print(f"{symbol}: name='{quote.name}'")
        except Exception as e:
            print(f"{symbol}: 失败 - {e}")
    
    # 测试港股
    hk_stocks = ["00100.HK", "01024.HK"]
    print("\n【港股测试】")
    for symbol in hk_stocks:
        try:
            quote = await provider.get_quote(symbol)
            print(f"{symbol}: name='{quote.name}'")
        except Exception as e:
            print(f"{symbol}: 失败 - {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
