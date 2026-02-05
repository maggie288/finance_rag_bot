"""
测试基本面估算功能的集成测试
"""

import asyncio
import sys
sys.path.insert(0, '/Users/lydiadu/finance_rag_bot/backend')

from app.services.market_data.aggregator import market_data
from app.schemas.market import FundamentalData


async def test_fundamental_estimation():
    """测试基本面估算功能"""

    print("=" * 60)
    print("基本面数据估算功能测试")
    print("=" * 60)

    # 测试港股（通常没有基本面数据）
    test_symbols = [
        ("0700.HK", "hk", "腾讯控股"),
        ("AAPL", "us", "苹果"),
    ]

    for symbol, market, name in test_symbols:
        print(f"\n测试 {name} ({symbol}, {market})")
        print("-" * 60)

        try:
            # 不使用数据库，强制从 API 获取
            fundamentals = await market_data.get_fundamentals(
                symbol=symbol,
                market=market,
                db=None,
                force_refresh=True
            )

            if fundamentals:
                print(f"✓ 成功获取基本面数据")
                print(f"  - 是否为估算数据: {fundamentals.is_estimated}")
                if fundamentals.is_estimated:
                    print(f"  - 估算说明: {fundamentals.estimation_note}")
                    print(f"  - PE比率: {fundamentals.pe_ratio}")
                    print(f"  - PB比率: {fundamentals.pb_ratio}")
                    print(f"  - ROE: {fundamentals.roe}")
                    print(f"  - 市值: {fundamentals.market_cap}")
                    print(f"  - 20日均线: {fundamentals.price_ma20}")
                    print(f"  - 60日均线: {fundamentals.price_ma60}")
                    print(f"  - 波动率: {fundamentals.volatility}")
                    print(f"  - 60日涨跌幅: {fundamentals.return_60d}")
                else:
                    print(f"  - PE比率: {fundamentals.pe_ratio}")
                    print(f"  - PB比率: {fundamentals.pb_ratio}")
                    print(f"  - ROE: {fundamentals.roe}")
                    print(f"  - 市值: {fundamentals.market_cap}")
            else:
                print(f"✗ 未能获取基本面数据")

        except Exception as e:
            print(f"✗ 错误: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fundamental_estimation())
