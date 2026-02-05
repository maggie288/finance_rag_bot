#!/bin/bash
# Finance RAG Bot - Railway 部署启动脚本
# 用法: railway deploy 或直接运行此脚本

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "======================================"
echo "    Finance RAG Bot - Railway 部署"
echo "======================================"
echo ""

# 检测是否在 Railway 环境
if [ -n "$RAILWAY" ] || [ -n "$PORT" ]; then
    echo "检测到 Railway 环境"
    IS_RAILWAY=true
else
    echo "检测到本地开发环境"
    IS_RAILWAY=false
fi

# ============================================
# Railway 环境: 等待数据库就绪
# ============================================
if [ "$IS_RAILWAY" = true ]; then
    echo ""
    echo "--- [1/4] 等待数据库服务 ---"

    # 等待 PostgreSQL
    if [ -n "$DATABASE_URL" ]; then
        echo -n "    等待 PostgreSQL..."
        for i in $(seq 1 30); do
            if python3 -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; asyncio.run(create_async_engine('$DATABASE_URL').connect())" 2>/dev/null; then
                echo ""
                log "PostgreSQL 已就绪"
                break
            fi
            echo -n "."
            sleep 2
        done
    else
        warn "DATABASE_URL 未设置"
    fi

    # 等待 Redis
    if [ -n "$REDIS_URL" ]; then
        echo -n "    等待 Redis..."
        if python3 -c "import redis; r=redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null; then
            echo ""
            log "Redis 已就绪"
        else
            warn "Redis 连接失败，但继续启动"
        fi
    fi
fi

# ============================================
# 数据库迁移
# ============================================
echo ""
echo "--- [2/4] 数据库迁移 ---"

cd "$BACKEND_DIR"

# 检查是否有 alembic 迁移
if [ -d "alembic/versions" ]; then
    # 设置环境变量以确保使用正确的 DATABASE_URL
    export DATABASE_URL="${DATABASE_URL:-postgresql://finance_bot:finance_bot_dev@localhost:5432/finance_rag_bot}"
    
    python3 -m alembic upgrade head 2>&1 | tail -5
    if [ $? -eq 0 ]; then
        log "数据库迁移完成"
    else
        warn "数据库迁移可能已是最新的或出错"
    fi
else
    log "无迁移文件，跳过"
fi

# ============================================
# 启动后端
# ============================================
echo ""
echo "--- [3/4] 启动后端 API ---"

# Railway 使用 $PORT 环境变量
if [ -n "$PORT" ]; then
    BIND_PORT=$PORT
else
    BIND_PORT=8000
fi

echo "    绑定端口: $BIND_PORT"

# 使用 gunicorn + uvicorn workers 以获得更好的性能
if command -v gunicorn &> /dev/null; then
    exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind "0.0.0.0:$BIND_PORT" --workers 2 --timeout 120 --access-logfile - --error-logfile -
else
    # 降级到纯 uvicorn
    exec python3 -m uvicorn app.main:app --host "0.0.0.0" --port "$BIND_PORT" --workers 2
fi
