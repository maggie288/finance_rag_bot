#!/usr/bin/env python3
"""
系统健康检查脚本
验证数据库表和Pinecone索引是否正常
"""
import os
import sys

# 读取.env文件
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

import psycopg2
from pinecone import Pinecone


def test_database():
    """测试数据库连接和表"""
    print("=" * 60)
    print("数据库健康检查")
    print("=" * 60)
    
    try:
        # 解析数据库URL
        db_url = os.environ.get('DATABASE_URL', '')
        # postgresql+asyncpg://finance_bot:finance_bot_dev@localhost:5432/finance_rag_bot
        # 转换为普通psycopg2连接字符串
        if '+asyncpg' in db_url:
            db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # 检查stock_quotes表
        cursor.execute("SELECT COUNT(*) FROM stock_quotes")
        count = cursor.fetchone()[0]
        print(f"✓ stock_quotes表: 存在 ({count} 行)")
        
        # 检查stock_klines表
        cursor.execute("SELECT COUNT(*) FROM stock_klines")
        count = cursor.fetchone()[0]
        print(f"✓ stock_klines表: 存在 ({count} 行)")
        
        # 检查stock_fundamentals表
        cursor.execute("SELECT COUNT(*) FROM stock_fundamentals")
        count = cursor.fetchone()[0]
        print(f"✓ stock_fundamentals表: 存在 ({count} 行)")
        
        cursor.close()
        conn.close()
        
        print("\n✓ 数据库检查通过!")
        return True
        
    except Exception as e:
        print(f"✗ 数据库错误: {e}")
        return False


def test_pinecone():
    """测试Pinecone连接和索引"""
    print("\n" + "=" * 60)
    print("Pinecone健康检查")
    print("=" * 60)
    
    try:
        pinecone_api_key = os.environ.get('PINECONE_API_KEY', '')
        pinecone_index_name = os.environ.get('PINECONE_INDEX_NAME', 'finance-rag-bot')
        
        pc = Pinecone(api_key=pinecone_api_key)
        
        # 列出所有索引
        indexes = pc.list_indexes()
        index_names = [idx['name'] for idx in indexes]
        print(f"已有索引: {', '.join(index_names) if index_names else '无'}")
        
        if pinecone_index_name in index_names:
            index = pc.Index(pinecone_index_name)
            stats = index.describe_index_stats()
            print(f"✓ 索引 '{pinecone_index_name}' 存在")
            print(f"  - 维度: {stats.dimension}")
            print(f"  - 向量数量: {stats.total_vector_count}")
            print("\n✓ Pinecone检查通过!")
            return True
        else:
            print(f"✗ 索引 '{pinecone_index_name}' 不存在")
            return False
            
    except Exception as e:
        print(f"✗ Pinecone错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Finance RAG Bot 系统健康检查")
    print("=" * 60 + "\n")
    
    db_ok = test_database()
    pinecone_ok = test_pinecone()
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    print(f"数据库: {'✓ 通过' if db_ok else '✗ 失败'}")
    print(f"Pinecone: {'✓ 通过' if pinecone_ok else '✗ 失败'}")
    
    if db_ok and pinecone_ok:
        print("\n🎉 所有检查通过! 系统运行正常。")
        return 0
    else:
        print("\n⚠️ 部分检查失败，请查看上述日志。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
