#!/usr/bin/env python3
"""
Simple Todo — 统一启动入口
双击此文件或运行 `python3 run.py` 即可启动后端 + Web 前端
Windows / macOS / Linux 通用
"""

import argparse
import functools
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

HOST = "127.0.0.1"
STARTUP_TIMEOUT = 15
LOG_PATH = os.path.expanduser("~/.simple_todo/logs/launcher.log")


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def configure_logging():
    logger = logging.getLogger("simple_todo.launcher")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(threadName)s] %(message)s"
    )
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        handler = RotatingFileHandler(
            LOG_PATH, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except OSError:
        pass

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    return logger


def reserve_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, 0))
        sock.listen(2048)
        return sock
    except Exception:
        sock.close()
        raise


def wait_for_health(api_url, web_url, failed, timeout=STARTUP_TIMEOUT):
    deadline = time.monotonic() + timeout
    last_error = "服务尚未响应"

    while time.monotonic() < deadline:
        if failed.is_set():
            raise RuntimeError(failed.message)
        try:
            with urlopen(f"{api_url}/health", timeout=1) as response:
                payload = json.loads(response.read().decode("utf-8"))
                api_ready = response.status == 200 and payload.get("status") == "ok"
            with urlopen(web_url, timeout=1) as response:
                web_ready = response.status == 200
            if api_ready and web_ready:
                return
            last_error = "健康检查返回了非预期响应"
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.1)

    raise TimeoutError(f"服务启动超时：{last_error}")


class FailureState:
    def __init__(self):
        self._event = threading.Event()
        self.message = "服务线程意外退出"

    def set(self, service, exc):
        self.message = f"{service} 启动失败：{exc}"
        self._event.set()

    def is_set(self):
        return self._event.is_set()


def start_service_thread(service, target, failed, logger):
    def run():
        try:
            target()
        except Exception as exc:
            logger.exception("%s 服务线程异常", service)
            failed.set(service, exc)

    thread = threading.Thread(target=run, name=service, daemon=True)
    thread.start()
    return thread


class InProcessServices:
    def __init__(self, root, logger):
        import uvicorn
        from server.main import app

        self.logger = logger
        self.failed = FailureState()
        self.api_socket = reserve_socket()
        self.api_port = self.api_socket.getsockname()[1]
        self.uvicorn_server = uvicorn.Server(
            uvicorn.Config(app, log_level="warning", lifespan="on")
        )

        web_dir = os.path.join(root, "web")
        handler = functools.partial(QuietHTTPRequestHandler, directory=web_dir)
        self.httpd = HTTPServer((HOST, 0), handler)
        self.web_port = self.httpd.server_address[1]
        self.threads = []
        self._cleaned = False

    @property
    def api_url(self):
        return f"http://{HOST}:{self.api_port}"

    @property
    def web_url(self):
        return f"http://{HOST}:{self.web_port}"

    @property
    def browser_url(self):
        return f"{self.web_url}/?apiPort={self.api_port}"

    def start(self):
        self.threads.append(start_service_thread(
            "backend",
            lambda: self.uvicorn_server.run(sockets=[self.api_socket]),
            self.failed,
            self.logger,
        ))
        self.threads.append(start_service_thread(
            "web", self.httpd.serve_forever, self.failed, self.logger
        ))

    def wait_until_ready(self, timeout=STARTUP_TIMEOUT):
        wait_for_health(
            self.api_url, self.web_url, self.failed, timeout=timeout
        )

    def start_notifier(self):
        import server.notifier as notifier

        notifier.WEB_URL = self.browser_url
        self.threads.append(start_service_thread(
            "notifier", notifier.main, FailureState(), self.logger
        ))

    def cleanup(self):
        if self._cleaned:
            return
        self._cleaned = True
        self.uvicorn_server.should_exit = True
        try:
            self.httpd.shutdown()
        except Exception:
            self.logger.exception("关闭 Web 服务失败")
        for thread in self.threads:
            if thread is not threading.current_thread():
                thread.join(timeout=3)
        self.httpd.server_close()
        try:
            self.api_socket.close()
        except OSError:
            pass


def show_startup_error(message):
    text = f"Simple Todo 启动失败\n\n{message}\n\n诊断日志：{LOG_PATH}"
    print(text, file=sys.stderr)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, text, "Simple Todo", 0x10)
        except Exception:
            pass


def run_in_process(root, smoke_test, logger):
    services = None
    try:
        services = InProcessServices(root, logger)
        logger.info(
            "启动核心服务 frozen=%s api=%s web=%s",
            getattr(sys, "frozen", False), services.api_url, services.web_url,
        )
        services.start()
        services.wait_until_ready()
        print(f"  后端 API : {services.api_url}")
        print(f"  Web 前端 : {services.browser_url}")

        if smoke_test:
            print("  Smoke test passed")
            return 0

        services.start_notifier()
        print("\n  正在打开浏览器...")
        print("  按 Ctrl+C 关闭所有服务\n")
        try:
            webbrowser.open(services.browser_url)
        except Exception:
            logger.exception("打开浏览器失败")

        def handle_signal(sig, frame):
            services.cleanup()
            raise SystemExit(0)

        signal.signal(signal.SIGINT, handle_signal)
        try:
            signal.signal(signal.SIGTERM, handle_signal)
        except AttributeError:
            pass

        while True:
            if services.failed.is_set():
                raise RuntimeError(services.failed.message)
            time.sleep(1)
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logger.exception("应用启动或运行失败")
        if not smoke_test:
            show_startup_error(str(exc))
        return 1
    finally:
        if services is not None:
            services.cleanup()


def run_development(root, logger):
    processes = []
    try:
        processes.append(subprocess.Popen([
            sys.executable, "-m", "uvicorn", "server.main:app",
            "--host", HOST, "--port", "8000",
        ]))
        processes.append(subprocess.Popen([
            sys.executable, "-m", "http.server", "3000", "-d", "web",
        ]))
        processes.append(subprocess.Popen([
            sys.executable, "-m", "server.notifier",
        ]))

        failed = FailureState()
        wait_for_health(
            "http://127.0.0.1:8000", "http://127.0.0.1:3000", failed
        )
        print("  后端 API : http://127.0.0.1:8000")
        print("  Web 前端 : http://127.0.0.1:3000")
        print("\n  正在打开浏览器...")
        print("  按 Ctrl+C 关闭所有服务\n")
        webbrowser.open("http://127.0.0.1:3000")
        return processes[0].wait()
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logger.exception("开发服务启动失败")
        show_startup_error(str(exc))
        return 1
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simple Todo 启动器")
    parser.add_argument(
        "--smoke-test", action="store_true", help="验证打包服务后立即退出"
    )
    args = parser.parse_args(argv)

    frozen = getattr(sys, "frozen", False)
    root = sys._MEIPASS if frozen else os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    logger = configure_logging()

    print("=" * 42)
    print("  Simple Todo — 待办事项")
    print("=" * 42)

    if frozen or args.smoke_test:
        return run_in_process(root, args.smoke_test, logger)
    return run_development(root, logger)


if __name__ == "__main__":
    sys.exit(main())
