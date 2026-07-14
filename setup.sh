#!/bin/bash
# Simple Todo — 一键安装脚本
set -e

echo "========================================"
echo "  Simple Todo 安装向导"
echo "========================================"
echo ""

# 检查 Python
if command -v python3 &>/dev/null; then
    echo "✅ Python $(python3 --version 2>&1)"
else
    echo "❌ 未找到 Python3，请先安装: https://www.python.org/downloads/"
    exit 1
fi

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip3 install -r server/requirements.txt -q
echo "✅ 依赖安装完成"

echo ""
echo "========================================"
echo "  安装完成！"
echo ""
echo "  启动方式："
echo "    python3 run.py"
echo ""
echo "  或直接双击 run.py 文件"
echo "========================================"
