#!/bin/bash
# Finance RAG Bot - 定时任务管理脚本
# 用法: ./scheduler.sh [命令]
#   ./scheduler.sh start     - 启动所有定时任务
#   ./scheduler.sh stop      - 停止所有定时任务
#   ./scheduler.sh status    - 查看任务状态
#   ./scheduler.sh worker    - 仅启动 Celery Worker
#   ./scheduler.sh beat      - 仅启动 Celery Beat
#   ./scheduler.sh scheduler - 仅启动 APScheduler

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# ============================================
# 启动所有定时任务
# ============================================
start_all() {
    echo ""
    echo "======================================"
    echo "    Finance RAG Bot 定时任务启动中..."
    echo "======================================"
    echo ""

    start_worker
    start_beat
    start_apscheduler

    echo ""
    echo "======================================"
    echo "    所有定时任务已启动!"
    echo "======================================"
    echo ""
    echo "任务说明:"
    echo "  Celery Worker:  处理异步任务 (新闻采集、数据抓取)"
    echo "  Celery Beat:   定时调度器 (定时触发新闻采集)"
    echo "  APScheduler:   市场数据调度器 (行情刷新、自选股更新)"
    echo ""
    echo "日志:"
    echo "  Celery Worker: tail -f $PROJECT_DIR/.celery.log"
    echo "  Celery Beat:   tail -f $PROJECT_DIR/.celery-beat.log"
    echo "  APScheduler:  查看后端日志 $PROJECT_DIR/.backend.log"
    echo ""
}

# ============================================
# Celery Worker
# ============================================
start_worker() {
    echo "--- [Worker] 启动 Celery Worker ---"

    cd "$BACKEND_DIR"
    nohup celery -A app.workers.celery_app worker --loglevel=info > "$PROJECT_DIR/.celery.log" 2>&1 &
    echo $! > "$PROJECT_DIR/.celery.pid"

    sleep 2
    if kill -0 "$(cat "$PROJECT_DIR/.celery.pid")" 2>/dev/null; then
        log "Celery Worker 已启动 (PID: $(cat "$PROJECT_DIR/.celery.pid"))"
        log "  功能: 新闻采集、数据抓取、异步任务处理"
    else
        error "Celery Worker 启动失败"
    fi
}

stop_worker() {
    if [ -f "$PROJECT_DIR/.celery.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.celery.pid")" 2>/dev/null && log "Celery Worker 已停止" || warn "Celery Worker 进程未运行"
        rm -f "$PROJECT_DIR/.celery.pid"
    else
        warn "Celery Worker 未运行"
    fi
}

# ============================================
# Celery Beat
# ============================================
start_beat() {
    echo "--- [Beat] 启动 Celery Beat ---"

    cd "$BACKEND_DIR"
    nohup celery -A app.workers.celery_app beat --loglevel=info > "$PROJECT_DIR/.celery-beat.log" 2>&1 &
    echo $! > "$PROJECT_DIR/.celery-beat.pid"

    sleep 2
    if kill -0 "$(cat "$PROJECT_DIR/.celery-beat.pid")" 2>/dev/null; then
        log "Celery Beat 已启动 (PID: $(cat "$PROJECT_DIR/.celery-beat.pid"))"
        log "  功能: 定时触发新闻采集任务"
    else
        error "Celery Beat 启动失败"
    fi
}

stop_beat() {
    if [ -f "$PROJECT_DIR/.celery-beat.pid" ]; then
        kill "$(cat "$PROJECT_DIR/.celery-beat.pid")" 2>/dev/null && log "Celery Beat 已停止" || warn "Celery Beat 进程未运行"
        rm -f "$PROJECT_DIR/.celery-beat.pid"
    else
        warn "Celery Beat 未运行"
    fi
}

# ============================================
# APScheduler (市场数据调度器)
# ============================================
start_apscheduler() {
    echo "--- [Scheduler] APScheduler 随后端自动启动 ---"
    log "APScheduler 已集成在后端服务中"
    log "  功能: 每5分钟刷新行情、每小时更新自选股"
    log "  说明: 启动后端服务时自动运行，无需单独启动"
}

stop_apscheduler() {
    log "APScheduler 随后端停止而停止"
    log "  使用 ./start.sh stop 停止后端"
}

# ============================================
# 查看任务状态
# ============================================
check_status() {
    echo ""
    echo "=== Finance RAG Bot 定时任务状态 ==="
    echo ""

    # Celery Worker
    if [ -f "$PROJECT_DIR/.celery.pid" ] && kill -0 "$(cat "$PROJECT_DIR/.celery.pid")" 2>/dev/null; then
        log "Celery Worker:   运行中 (PID: $(cat "$PROJECT_DIR/.celery.pid"))"
        log "  功能: 新闻采集、数据抓取"
        log "  日志: $PROJECT_DIR/.celery.log"
    else
        error "Celery Worker:   未运行"
        echo "  启动: ./scheduler.sh worker"
    fi
    echo ""

    # Celery Beat
    if [ -f "$PROJECT_DIR/.celery-beat.pid" ] && kill -0 "$(cat "$PROJECT_DIR/.celery-beat.pid")" 2>/dev/null; then
        log "Celery Beat:      运行中 (PID: $(cat "$PROJECT_DIR/.celery-beat.pid"))"
        log "  功能: 定时触发任务"
        log "  日志: $PROJECT_DIR/.celery-beat.log"
    else
        error "Celery Beat:      未运行"
        echo "  启动: ./scheduler.sh beat"
    fi
    echo ""

    # APScheduler
    if curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
        log "APScheduler:     运行中 (集成在后端)"
        log "  功能: 行情刷新、自选股更新"
        log "  说明: 后端启动时自动运行"
    else
        warn "APScheduler:     后端未运行"
        echo "  启动: ./start.sh 启动后端"
    fi
    echo ""
}

# ============================================
# 停止所有定时任务
# ============================================
stop_all() {
    echo ""
    echo "正在停止定时任务..."

    stop_worker
    stop_beat
    stop_apscheduler

    log "所有定时任务已停止"
}

# ============================================
# 主入口
# ============================================
case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    status)
        check_status
        ;;
    worker)
        start_worker
        ;;
    beat)
        start_beat
        ;;
    scheduler)
        start_apscheduler
        ;;
    *)
        echo "用法: ./scheduler.sh [start|stop|status|worker|beat|scheduler]"
        echo ""
        echo "命令:"
        echo "  start     - 启动所有定时任务"
        echo "  stop     - 停止所有定时任务"
        echo "  status   - 查看任务状态"
        echo "  worker   - 仅启动 Celery Worker"
        echo "  beat     - 仅启动 Celery Beat"
        echo "  scheduler - APScheduler 说明"
        exit 1
        ;;
esac
