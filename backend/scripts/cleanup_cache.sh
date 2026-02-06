#!/bin/bash
# 清理HuggingFace缓存脚本
# 运行此脚本可释放本地磁盘空间（不会影响Docker镜像）

echo "🧹 清理 HuggingFace 模型缓存..."
echo ""

# 显示当前缓存大小
echo "📊 当前缓存大小:"
du -sh ~/.cache/huggingface/ 2>/dev/null || echo "缓存不存在"

echo ""
echo "🗑️  删除 sentence-transformers 模型 (all-MiniLM-L6-v2)..."
rm -rf ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2

echo "🗑️  删除 BAAI 模型 (bge-small-zh)..."
rm -rf ~/.cache/huggingface/hub/models--BAAI--bge-small-zh

echo ""
echo "✅ 清理完成!"
echo ""
echo "📊 清理后缓存大小:"
du -sh ~/.cache/huggingface/ 2>/dev/null || echo "缓存已清空"
