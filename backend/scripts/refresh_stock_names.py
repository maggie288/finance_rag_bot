#!/usr/bin/env python3
"""刷新数据库中所有股票名称的脚本"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.market_data.tushare_provider import TuShareProvider


def update_names():
    engine = create_engine(settings.database_url.replace("+asyncpg", ""))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    provider = TuShareProvider()
    
    try:
        # 获取所有股票
        result = session.execute(text("SELECT symbol, market FROM stock_quotes"))
        stocks = result.fetchall()
        
        print(f"找到 {len(stocks)} 只股票需要更新名称")
        print("=" * 50)
        
        for symbol, market in stocks:
            print(f"处理 {symbol} ({market})...", end=" ")
            
            # 跳过美股和商品
            if market in ("us", "commodity"):
                print("跳过 (非A股/港股)")
                continue
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                quote = loop.run_until_complete(provider.get_quote(symbol))
                loop.close()
                
                if quote and quote.name:
                    # 更新 stock_quotes
                    session.execute(
                        text("UPDATE stock_quotes SET name = :name WHERE symbol = :symbol AND market = :market"),
                        {"name": quote.name, "symbol": symbol, "market": market}
                    )
                    # 更新 watchlists
                    session.execute(
                        text("UPDATE watchlists SET name = :name WHERE symbol = :symbol AND market = :market"),
                        {"name": quote.name, "symbol": symbol, "market": market}
                    )
                    print(f"✅ {quote.name}")
                else:
                    print("❌ API返回空名称")
            except Exception as e:
                print(f"❌ 失败: {e}")
        
        session.commit()
        print("\n" + "=" * 50)
        print("更新完成！")
        
    finally:
        session.close()


if __name__ == "__main__":
    update_names()
