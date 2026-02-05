#!/bin/bash
# Finance RAG Bot - 一键启动脚本
# 用法: ./start.sh [命令]
#   ./start.sh          - 启动所有服务
#   ./start.sh stop    - 停止所有服务
#   ./start.sh status  - 查看服务状态
#   ./start.sh openclaw [start|stop|status] - 管理 OpenClaw

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# ============================================
# OpenClaw 管理函数
# ============================================
openclaw_service() {
    local action="${1:-status}"
    local openclaw_port=18789

    case "$action" in
        start)
            # 检查 Node.js 版本
            if ! command -v node &> /dev/null; then
                error "Node.js 未安装"
                return 1
            fi

            local node_version=$(node -v 2>/dev/null | sed 's/v//' | cut -d. -f1)
            if [ -z "$node_version" ] || [ "$node_version" -lt 22 ]; then
                warn "OpenClaw 需要 Node.js 22+，当前版本: $(node -v)"
                warn "尝试使用 nvm 安装..."
                if [ -f "$HOME/.nvm/nvm.sh" ]; then
                    source "$HOME/.nvm/nvm.sh"
                    nvm install 22 2>/dev/null
                    nvm use 22 2>/dev/null
                fi
            fi

            # 检查 OpenClaw 是否已安装
            if ! command -v openclaw &> /dev/null; then
                warn "OpenClaw 未安装，正在安装..."
                source "$HOME/.nvm/nvm.sh" 2>/dev/null
                nvm use 22 2>/dev/null
                npm install -g openclaw@latest 2>/dev/null
                if ! command -v openclaw &> /dev/null; then
                    error "OpenClaw 安装失败"
                    return 1
                fi
            fi

            # 检查是否已运行 (WebSocket 网关)
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:$openclaw_port 2>/dev/null | grep -q "200"; then
                log "OpenClaw 已在运行 (端口 $openclaw_port)"
                return 0
            fi

            # 修复配置并设置网关模式
            source "$HOME/.nvm/nvm.sh" 2>/dev/null
            nvm use 22 2>/dev/null

            warn "正在修复 OpenClaw 配置..."
            openclaw doctor --fix 2>/dev/null

            # 设置网关模式
            openclaw config set gateway.mode local 2>/dev/null

            # 启动网关服务
            cd ~
            nohup openclaw gateway --port $openclaw_port > "$PROJECT_DIR/.openclaw.log" 2>&1 &
            echo $! > "$PROJECT_DIR/.openclaw.pid"

            # 等待启动
            echo -n "    等待 OpenClaw 启动"
            for i in $(seq 1 15); do
                if curl -s -o /dev/null -w "%{http_code}" http://localhost:$openclaw_port 2>/dev/null | grep -q "200"; then
                    echo ""
                    log "OpenClaw 已启动: http://localhost:$openclaw_port"
                    log "模式: 模拟交易网关"
                    log "WebSocket: ws://localhost:$openclaw_port"
                    return 0
                fi
                echo -n "."
                sleep 1
            done
            echo ""
            warn "OpenClaw 启动中，请稍后访问 http://localhost:$openclaw_port"
            ;;
        stop)
            if [ -f "$PROJECT_DIR/.openclaw.pid" ]; then
                kill "$(cat "$PROJECT_DIR/.openclaw.pid")" 2>/dev/null
                rm -f "$PROJECT_DIR/.openclaw.pid"
                log "OpenClaw 已停止"
            else
                # 尝试查找并停止
                local pid=$(lsof -t -i:3001 2>/dev/null)
                if [ -n "$pid" ]; then
                    kill "$pid" 2>/dev/null
                    log "OpenClaw 已停止"
                else
                    warn "OpenClaw 未运行"
                fi
            fi
            ;;
        status)
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null | grep -q "200"; then
                log "OpenClaw:     运行中 (http://localhost:3001) [模拟模式]"
            else
                error "OpenClaw:     未运行 (模拟模式)"
            fi
            ;;
    esac
}

# ============================================
# 停止所有服务
# ============================================
stop_services() {
    echo ""
    echo "正在停止服务..."

    # 停止 OpenClaw
    openclaw_service stop

    # 停止 Celery Beat
    if [ -f "$PROJECT_DIR/.celery-beat.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.celery-beat.pid")" 2>/dev/null && log "Celery Beat已停止" || warn "Celery Beat进程未运行"
        rm -f "$PROJECT_DIR/.celery-beat.pid"
    fi

    # 停止 Celery Worker
    if [ -f "$PROJECT_DIR/.celery.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.celery.pid")" 2>/dev/null && log "Celery Worker已停止" || warn "Celery Worker进程未运行"
        rm -f "$PROJECT_DIR/.celery.pid"
    fi

    # 停止后端
    if [ -f "$PROJECT_DIR/.backend.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.backend.pid")" 2>/dev/null && log "后端已停止" || warn "后端进程未运行"
        rm -f "$PROJECT_DIR/.backend.pid"
    fi

    # 停止前端
    if [ -f "$PROJECT_DIR/.frontend.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.frontend.pid")" 2>/dev/null && log "前端已停止" || warn "前端进程未运行"
        rm -f "$PROJECT_DIR/.frontend.pid"
    fi

    # 停止 Docker (可选)
    cd "$PROJECT_DIR" && docker-compose down 2>/dev/null
    log "Docker 容器已停止"
    echo ""
}

# ============================================
# 查看服务状态
# ============================================
check_status() {
    echo ""
    echo "=== Finance RAG Bot 服务状态 ==="

    # Docker
    if docker ps --filter "name=finance_rag_bot-postgres" --format "{{.Status}}" 2>/dev/null | grep -q "Up"; then
        log "PostgreSQL:  运行中 (localhost:5432)"
    else
        error "PostgreSQL:  未运行"
    fi

    # Redis
    if docker exec mkfinance_redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log "Redis:       运行中 (localhost:6379)"
    elif docker exec finance_rag_bot-redis-1 redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log "Redis:       运行中 (localhost:6379)"
    else
        error "Redis:       未运行"
    fi

    # 后端
    if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
        log "后端 API:    运行中 (http://localhost:8000)"
        log "  API文档:   http://localhost:8000/docs"
    else
        error "后端 API:    未运行"
    fi

    # Celery Worker
    if [ -f "$PROJECT_DIR/.celery.pid" ] && kill -0 "$(cat "$PROJECT_DIR/.celery.pid")" 2>/dev/null; then
        log "Celery Worker:   运行中 (新闻采集)"
    else
        error "Celery Worker:   未运行"
    fi

    # Celery Beat
    if [ -f "$PROJECT_DIR/.celery-beat.pid" ] && kill -0 "$(cat "$PROJECT_DIR/.celery-beat.pid")" 2>/dev/null; then
        log "Celery Beat:      运行中 (定时任务)"
    else
        error "Celery Beat:      未运行"
    fi

    # 前端
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200"; then
        log "前端应用:    运行中 (http://localhost:3000)"
    else
        error "前端应用:    未运行"
    fi

    # OpenClaw
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null | grep -q "200"; then
        log "OpenClaw:    运行中 (http://localhost:3001) [模拟模式]"
    else
        warn "OpenClaw:    未运行 (模拟模式)"
        echo "    启动: ./start.sh openclaw start"
    fi

    echo ""
}

# ============================================
# 启动所有服务
# ============================================
start_services() {
    echo ""
    echo "======================================"
    echo "    Finance RAG Bot 启动中..."
    echo "======================================"
    echo ""

    # --- 1. Docker ---
    echo "--- [1/7] 启动数据库 ---"
    cd "$PROJECT_DIR"
    docker-compose up -d postgres 2>/dev/null
    if [ $? -eq 0 ]; then
        log "PostgreSQL 已启动"
    else
        error "PostgreSQL 启动失败"
        exit 1
    fi

    # 检查 Redis
    if docker exec mkfinance_redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log "Redis 已运行 (复用现有)"
    else
        docker-compose up -d redis 2>/dev/null
        if [ $? -eq 0 ]; then
            log "Redis 已启动"
        else
            warn "Redis 启动失败，请检查"
        fi
    fi

    # 等待 PostgreSQL
    echo -n "    等待数据库就绪"
    for i in $(seq 1 15); do
        if docker exec finance_rag_bot-postgres-1 pg_isready -U finance_bot 2>/dev/null | grep -q "accepting"; then
            echo ""
            log "数据库已就绪"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # --- 2. 数据库迁移 ---
    echo "--- [2/7] 数据库迁移 ---"
    cd "$BACKEND_DIR"
    python3 -m alembic upgrade head 2>&1 | grep -E "Running|No new" || log "迁移已是最新"
    log "数据库迁移完成"

    # --- 3. 后端 ---
    echo "--- [3/5] 启动后端 (port 8000) ---"
    if [ -f "$PROJECT_DIR/.backend.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.backend.pid")" 2>/dev/null
        rm -f "$PROJECT_DIR/.backend.pid"
    fi

    cd "$BACKEND_DIR"
    nohup python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/.backend.log" 2>&1 &
    echo $! > "$PROJECT_DIR/.backend.pid"

    echo -n "    等待后端就绪"
    for i in $(seq 1 20); do
        if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
            echo ""
            log "后端已启动: http://localhost:8000"
            log "API文档:    http://localhost:8000/docs"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # --- 4. 前端 ---
    echo "--- [4/5] 启动前端 (port 3000) ---"
    if [ -f "$PROJECT_DIR/.frontend.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.frontend.pid")" 2>/dev/null
        rm -f "$PROJECT_DIR/.frontend.pid"
    fi

    cd "$FRONTEND_DIR"
    nohup npm run dev > "$PROJECT_DIR/.frontend.log" 2>&1 &
    echo $! > "$PROJECT_DIR/.frontend.pid"

    echo -n "    等待前端就绪"
    for i in $(seq 1 30); do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null | grep -q "200"; then
            echo ""
            log "前端已启动: http://localhost:3000"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # --- 5. OpenClaw (模拟模式) ---
    echo "--- [5/5] 启动 OpenClaw (模拟模式) ---"
    mkdir -p "$PROJECT_DIR/.openclaw"
    openclaw_service start

    # --- 定时任务提示 ---
    echo ""
    echo "======================================"
    echo "    核心服务已启动!"
    echo "======================================"
    echo ""
    echo "定时任务 (Celery Worker/Beat):"
    echo "  如需启用定时任务，请运行: ./scheduler.sh start"
    echo ""
    echo "访问地址:"
    echo "  前端应用:    http://localhost:3000"
    echo "  后端 API:    http://localhost:8000"
    echo "  API 文档:    http://localhost:8000/docs"
    echo "  OpenClaw:   http://localhost:3001 (模拟模式)"
    echo ""

    # 获取本机 IP
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')
    if [ -n "$LOCAL_IP" ]; then
        echo "手机访问: http://$LOCAL_IP:3000"
        echo ""
    fi

    echo "管理命令:"
    echo "  查看状态: ./start.sh status"
    echo "  停止服务: ./start.sh stop"
    echo "  定时任务: ./scheduler.sh start"
    echo "  OpenClaw: ./start.sh openclaw start|stop|status"
    echo ""
    echo "日志:"
    echo "  后端:   tail -f $PROJECT_DIR/.backend.log"
    echo "  前端:   tail -f $PROJECT_DIR/.frontend.log"
    echo "  OpenClaw: tail -f $PROJECT_DIR/.openclaw.log"
    echo ""
}

# ============================================
# 主入口
# ============================================
case "${1:-start}" in
    stop)        stop_services ;;
    status)      check_status ;;
    openclaw)    openclaw_service "${2:-status}" ;;
    start)       start_services ;;
    *)
        echo "用法: ./start.sh [start|stop|status|openclaw]"
        echo ""
        echo "命令:"
        echo "  start       - 启动所有服务"
        echo "  stop       - 停止所有服务"
        echo "  status     - 查看服务状态"
        echo "  openclaw   - OpenClaw 管理"
        echo "    start    - 启动 OpenClaw (模拟模式)"
        echo "    stop     - 停止 OpenClaw"
        echo "    status   - 查看 OpenClaw 状态"
        exit 1
        ;;
esac
