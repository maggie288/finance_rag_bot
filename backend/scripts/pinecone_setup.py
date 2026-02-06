#!/usr/bin/env python3
"""
Pinecone索引管理脚本
用于检查和创建finance-rag-bot索引
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

from pinecone import Pinecone, ServerlessSpec


def check_and_create_index():
    """检查并创建Pinecone索引"""
    pinecone_api_key = os.environ.get('PINECONE_API_KEY', '')
    pinecone_index_name = os.environ.get('PINECONE_INDEX_NAME', 'finance-rag-bot')
    
    if not pinecone_api_key:
        print("✗ 错误: 未找到PINECONE_API_KEY环境变量")
        return False
    
    print(f"正在检查Pinecone索引: {pinecone_index_name}")
    print(f"Pinecone API Key: {pinecone_api_key[:10]}...")
    
    try:
        # 初始化Pinecone客户端
        pc = Pinecone(api_key=pinecone_api_key)
        print("✓ 成功连接Pinecone")
        
        # 获取所有索引列表
        indexes = pc.list_indexes()
        index_names = [idx['name'] for idx in indexes]
        print(f"当前已有索引: {index_names}")
        
        # 检查目标索引是否存在
        if pinecone_index_name in index_names:
            print(f"✓ 索引 '{pinecone_index_name}' 已存在")
            index = pc.Index(pinecone_index_name)
            stats = index.describe_index_stats()
            print(f"  - 维度: {stats.dimension}")
            print(f"  - 向量数量: {stats.total_vector_count}")
            return True
        else:
            print(f"✗ 索引 '{pinecone_index_name}' 不存在，正在创建...")
            
            # 创建索引
            pc.create_index(
                name=pinecone_index_name,
                dimension=384,  # all-MiniLM-L6-v2的维度
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print(f"✓ 索引 '{pinecone_index_name}' 创建成功")
            
            # 等待索引初始化完成
            import time
            time.sleep(5)
            
            # 验证索引
            index = pc.Index(pinecone_index_name)
            stats = index.describe_index_stats()
            print(f"  - 维度: {stats.dimension}")
            print(f"  - 向量数量: {stats.total_vector_count}")
            return True
            
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_and_create_index()
    sys.exit(0 if success else 1)
