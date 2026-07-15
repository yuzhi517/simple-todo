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
import threading
import webbrowser


def main():
    frozen = getattr(sys, 'frozen', False)

    if frozen:
        root = sys._MEIPASS
    else:
        root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    if frozen:
        # ── PyInstaller 打包模式 ──────────────────────────────────────────
        # sys.executable 是打包后的 exe 自身，不能用它 spawn 子进程，
        # 否则每个子进程都会启动一个新的应用实例 → 无限递归 (fork bomb)
        # 解决方案：在后台线程中启动各服务

        import uvicorn
        from server.main import app

        uvicorn_config = uvicorn.Config(
            app, host="127.0.0.1", port=8000, log_level="warning",
        )
        uvicorn_server = uvicorn.Server(uvicorn_config)
        t_backend = threading.Thread(target=uvicorn_server.run, daemon=True)
        t_backend.start()

        import functools
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        web_dir = os.path.join(root, "web")
        handler = functools.partial(SimpleHTTPRequestHandler, directory=web_dir)
        httpd = HTTPServer(("127.0.0.1", 3000), handler)
        t_web = threading.Thread(target=httpd.serve_forever, daemon=True)
        t_web.start()

        import server.notifier as notifier_mod
        t_notifier = threading.Thread(target=notifier_mod.main, daemon=True)
        t_notifier.start()

        # 清理回调（daemon 线程随主进程退出自动终止，这里做显式的资源释放）
        def cleanup():
            uvicorn_server.should_exit = True
            httpd.shutdown()

    else:
        # ── 开发模式 ──────────────────────────────────────────────────────
        # 用子进程运行各服务，进程隔离更干净，crash 互不影响

        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        web = subprocess.Popen(
            [sys.executable, "-m", "http.server", "3000", "-d", "web"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        notifier_proc = subprocess.Popen(
            [sys.executable, "-m", "server.notifier"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def cleanup():
            for p in [backend, web, notifier_proc]:
                try:
                    p.terminate()
                    p.wait(timeout=3)
                except Exception:
                    p.kill()

    # ── 信号处理（主线程） ──────────────────────────────────────────────
    def handle_signal(sig, frame):
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    try:
        signal.signal(signal.SIGTERM, handle_signal)
    except AttributeError:
        pass  # Windows 不支持 SIGTERM handler

    print("=" * 42)
    print("  Simple Todo — 待办事项")
    print("=" * 42)
    print(f"  后端 API : http://127.0.0.1:8000")
    print(f"  Web 前端 : http://127.0.0.1:3000")
    print()
    print("  正在打开浏览器...")
    print("  按 Ctrl+C 关闭所有服务")
    print()

    # 等待服务就绪
    time.sleep(2)

    # 自动打开浏览器（仅此一次）
    try:
        webbrowser.open("http://127.0.0.1:3000")
    except Exception:
        pass

    # 等待
    try:
        if frozen:
            while True:
                time.sleep(1)
        else:
            backend.wait()
            web.wait()
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
