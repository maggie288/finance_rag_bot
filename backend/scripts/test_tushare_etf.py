#!/usr/bin/env python3
"""直接测试 TuShare API 获取 ETF 数据"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
import tushare as ts


def test_etf_api():
    print("=" * 50)
    print("直接测试 TuShare ETF API")
    print("=" * 50)
    
    api = ts.pro_api(settings.tushare_token)
    
    # 测试获取ETF名称
    print("\n【获取ETF名称】")
    try:
        df = api.etf_basic(ts_code="510300.SH", fields="ts_code,csname,cname")
        print(f"510300.SH: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"❌ 获取ETF名称失败: {e}")
    
    # 测试获取ETF行情
    print("\n【获取ETF行情】")
    try:
        df = api.daily(ts_code="510300.SH")
        print(f"510300.SH daily: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")
    except Exception as e:
        print(f"❌ 获取ETF行情失败: {e}")
    
    # 测试ETF基金持仓
    print("\n【获取ETF基金持仓】")
    try:
        df = api.fund_portfolio(ts_code="510300.SH")
        print(f"510300.SH 持仓: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")
    except Exception as e:
        print(f"❌ 获取ETF持仓失败: {e}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    test_etf_api()
