#!/usr/bin/env python3
"""
Simple Todo — 统一启动入口
双击此文件或运行 `python3 run.py` 即可启动后端 + Web 前端
Windows / macOS / Linux 通用
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    # 启动后端
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 启动 Web 前端
    web = subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000", "-d", "web"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 启动通知服务（后台检查截止日期）
    notifier = subprocess.Popen(
        [sys.executable, "server/notifier.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    def cleanup():
        for p in [backend, web, notifier]:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()

    def handle_signal(sig, frame):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    print("=" * 42)
    print("  Simple Todo — 待办事项")
    print("=" * 42)
    print(f"  后端 API : http://127.0.0.1:8000")
    print(f"  Web 前端 : http://127.0.0.1:3000")
    print()
    print("  正在打开浏览器...")
    print("  按 Ctrl+C 关闭所有服务")
    print()

    time.sleep(2)

    # 自动打开浏览器
    try:
        webbrowser.open("http://127.0.0.1:3000")
    except Exception:
        pass

    # 等待子进程
    try:
        backend.wait()
        web.wait()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
