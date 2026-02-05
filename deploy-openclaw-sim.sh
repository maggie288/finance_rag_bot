#!/bin/bash

set -e

echo "🐾 OpenClaw 模拟模式部署脚本"
echo "============================"
echo "模式: 纯模拟交易 (无需 API Key)"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 已安装${NC}"

# 创建目录
mkdir -p openclaw/data openclaw/config openclaw/openclaw_home
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 确认配置文件存在
if [ ! -f "openclaw/config/openclaw.json" ]; then
    echo -e "${RED}❌ 配置文件不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 配置文件已就绪${NC}"

echo ""
echo "🚀 启动 OpenClaw 模拟环境..."
echo ""

# 启动容器
docker-compose -f docker-compose.openclaw.yml up -d

echo ""
echo "⏳ 等待服务启动 (10秒)..."
sleep 10

echo ""
echo "📊 容器状态:"
docker-compose -f docker-compose.openclaw.yml ps

echo ""
echo "================================================"
echo "🎉 OpenClaw 模拟环境已启动!"
echo "================================================"
echo ""
echo "📝 访问地址:"
echo "   Web UI: http://localhost:3000"
echo ""
echo "🔧 管理命令:"
echo "   查看日志: docker-compose -f docker-compose.openclaw.yml logs -f"
echo "   停止服务: docker-compose -f docker-compose.openclaw.yml down"
echo ""
echo "💡 提示:"
echo "   - 无需配置 API Key"
echo "   - 所有交易均为模拟"
echo "   - 可查看 Polymarket 市场数据"
echo "================================================"
