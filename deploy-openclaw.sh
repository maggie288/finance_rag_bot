#!/bin/bash

set -e

# OpenClaw 部署脚本
# 用法: ./deploy-openclaw.sh

echo "🚀 开始部署 OpenClaw (原 Clawdbot/Moltbot)..."
echo "================================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Docker
check_docker() {
    echo ""
    echo "📋 检查 Docker 环境..."
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker Desktop${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker 已安装: $(docker --version)${NC}"

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose 已安装${NC}"
}

# 创建目录结构
create_directories() {
    echo ""
    echo "📁 创建目录结构..."
    mkdir -p openclaw/data
    mkdir -p openclaw/config
    mkdir -p openclaw/openclaw_home
    echo -e "${GREEN}✅ 目录创建完成${NC}"
}

# 复制配置文件
setup_config() {
    echo ""
    echo "⚙️  配置 OpenClaw..."

    if [ ! -f "openclaw/.env" ]; then
        if [ -f "openclaw/.env.example" ]; then
            cp openclaw/.env.example openclaw/.env
            echo -e "${YELLOW}⚠️  请编辑 openclaw/.env 文件填入你的 API Key${NC}"
            echo "================================================"
            echo "需要配置的内容:"
            echo "  1. OPENAI_API_KEY - OpenAI API Key"
            echo "  2. BTC_WALLET_ADDRESS - Bitcoin 钱包地址 (可选)"
            echo "  3. BTC_WALLET_PRIVATE_KEY - Bitcoin 私钥 (可选)"
            echo "================================================"
        else
            echo -e "${RED}❌ 配置文件模板不存在${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ 环境配置文件已存在${NC}"
    fi

    if [ ! -f "openclaw/config/openclaw.json" ]; then
        echo -e "${RED}❌ 配置文件 openclaw.json 不存在${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ OpenClaw 配置完成${NC}"
}

# 拉取并启动 Docker 镜像
start_docker() {
    echo ""
    echo "🐳 启动 Docker 容器..."
    
    if [ -f "docker-compose.openclaw.yml" ]; then
        echo "📦 拉取 OpenClaw 镜像..."
        docker-compose -f docker-compose.openclaw.yml pull || true
        
        echo ""
        echo "🚀 启动容器..."
        docker-compose -f docker-compose.openclaw.yml up -d
        
        echo ""
        echo "⏳ 等待服务启动..."
        sleep 10
        
        echo ""
        echo "📊 检查容器状态..."
        docker-compose -f docker-compose.openclaw.yml ps
    else
        echo -e "${RED}❌ docker-compose.openclaw.yml 不存在${NC}"
        exit 1
    fi
}

# 检查服务健康状态
check_health() {
    echo ""
    echo "🏥 检查服务健康状态..."
    
    # 检查容器是否运行
    if docker ps | grep -q "openclaw"; then
        echo -e "${GREEN}✅ OpenClaw 容器正在运行${NC}"
        
        # 检查端口
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ OpenClaw 服务可访问 (http://localhost:3000)${NC}"
        else
            echo -e "${YELLOW}⚠️  服务可能还在启动中，请稍后访问 http://localhost:3000${NC}"
        fi
    else
        echo -e "${RED}❌ OpenClaw 容器未运行${NC}"
        echo ""
        echo "查看日志排查问题:"
        docker-compose -f docker-compose.openclaw.yml logs
    fi
}

# 显示访问信息
show_info() {
    echo ""
    echo "================================================"
    echo "🎉 OpenClaw 部署完成!"
    echo "================================================"
    echo ""
    echo "📝 访问地址:"
    echo "   Web UI: http://localhost:3000"
    echo ""
    echo "📂 数据目录:"
    echo "   - ./openclaw/data/ (存储数据)"
    echo "   - ./openclaw/config/ (配置文件)"
    echo ""
    echo "🔧 管理命令:"
    echo "   查看日志: docker-compose -f docker-compose.openclaw.yml logs -f"
    echo "   停止服务: docker-compose -f docker-compose.openclaw.yml down"
    echo "   重启服务: docker-compose -f docker-compose.openclaw.yml restart"
    echo ""
    echo "⚠️  重要提示:"
    echo "   - 请编辑 openclaw/.env 文件配置你的 API Key"
    echo "   - 如需交易功能，请配置 Bitcoin 钱包信息"
    echo "================================================"
}

# 主函数
main() {
    echo "🐾 OpenClaw 部署脚本"
    echo "   (原 Clawdbot / Moltbot)"
    echo ""
    
    check_docker
    create_directories
    setup_config
    start_docker
    check_health
    show_info
}

main "$@"
