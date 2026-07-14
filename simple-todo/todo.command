#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# 启动后端服务（后台运行）
echo "正在启动后端服务..."
python3 -m uvicorn server.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# 等待后端就绪
echo "等待后端服务就绪..."
for i in $(seq 1 30); do
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "后端服务已就绪"
        break
    fi
    sleep 0.5
done

# 启动 CLI 菜单
python3 -m client.cli menu

# 退出时关闭后端
echo "正在关闭后端服务..."
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
echo "再见！"
