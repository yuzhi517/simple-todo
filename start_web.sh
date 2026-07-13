#!/bin/bash
# ==========================================
# Simple Todo — Web 前端一键启动脚本
# 启动后端 API 服务 (端口 8000) + 静态文件服务 (端口 3000)
# ==========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

cleanup() {
    echo ""
    echo "正在关闭服务..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null
    echo "服务已关闭。"
}

trap cleanup EXIT INT TERM

echo "======================================"
echo "  Simple Todo — 待办事项"
echo "======================================"
echo ""

# 启动后端 API 服务
echo "[1/2] 启动后端 API 服务..."
python3 -m uvicorn server.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
sleep 1

# 启动静态文件服务
echo "[2/2] 启动 Web 前端..."
python3 -m http.server 3000 -d web &
WEB_PID=$!

echo ""
echo "  后端 API : http://127.0.0.1:8000"
echo "  Web 前端 : http://127.0.0.1:3000"
echo ""
echo "按 Ctrl+C 关闭所有服务"
echo ""

wait
