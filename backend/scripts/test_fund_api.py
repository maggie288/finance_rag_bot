#!/usr/bin/env python3
"""测试 TuShare 基金接口获取 ETF 数据"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
import tushare as ts


def test_fund_api():
    print("=" * 50)
    print("测试 TuShare 基金接口")
    print("=" * 50)
    
    api = ts.pro_api(settings.tushare_token)
    
    # 测试基金列表
    print("\n【获取ETF列表】")
    try:
        df = api.fund_basic(market="E")  # ETF
        print(f"ETF列表: {len(df)} 只")
        print(df.head(5).to_string())
    except Exception as e:
        print(f"❌ 获取ETF列表失败: {e}")
    
    # 测试基金每日行情
    print("\n【获取ETF行情】")
    try:
        df = api.fund_daily(ts_code="510300.SH")
        print(f"510300.SH daily: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")
    except Exception as e:
        print(f"❌ 获取ETF行情失败: {e}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    test_fund_api()
