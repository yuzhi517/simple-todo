"""
Simple Todo — 截止日期通知服务
跨平台：macOS (osascript) / Windows (PowerShell Toast)
每 5 分钟检查一次即将到期的任务，弹系统原生通知
"""
import sqlite3
import time
import subprocess
import platform
import os
import sys
import signal
import argparse
import json
from datetime import datetime

DB_PATH = os.path.expanduser("~/.simple_todo/tasks.db")
CHECK_INTERVAL = 60  # 1 分钟
MINUTE = 60
HOUR = 3600
DAY = 86400

# 提醒节点：到期、5分钟、1小时、12小时、1天、3天、7天
CHECKPOINTS = [
    0,              # 已到期
    5 * MINUTE,
    1 * HOUR,
    12 * HOUR,
    1 * DAY,
    3 * DAY,
    7 * DAY,
]

PID_FILE = os.path.expanduser("~/.simple_todo/notifier.pid")
NOTIFIED_FILE = os.path.expanduser("~/.simple_todo/notified.json")

_notified = set()  # 防重复通知 (task_id, checkpoint_seconds)


def _load_notified():
    """从文件加载已通知记录"""
    global _notified
    try:
        with open(NOTIFIED_FILE) as f:
            _notified = set(tuple(x) for x in json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        _notified = set()


def _save_notified():
    """将已通知记录持久化到文件"""
    os.makedirs(os.path.dirname(NOTIFIED_FILE), exist_ok=True)
    with open(NOTIFIED_FILE, "w") as f:
        json.dump([list(x) for x in _notified], f)


def write_pid():
    """写入 PID 文件"""
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def read_pid():
    """读取 PID 文件，返回进程 ID 或 None"""
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def remove_pid():
    """删除 PID 文件"""
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def is_running(pid):
    """检查指定 PID 的进程是否存活"""
    if platform.system() == "Windows":
        import ctypes
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


WEB_URL = "http://127.0.0.1:3000"


def notify(title: str, body: str):
    system = platform.system()
    try:
        if system == "Darwin":
            # macOS: 点击通知打开 Web 界面
            script = (
                f'display notification "{body}" with title "{title}"'
                f' sound name "Glass"'
            )
            subprocess.run(["osascript", "-e", script])
            # 额外尝试：把 URL 附加到剪贴板通知（macOS 原生 osascript 不支持点击回调）
        elif system == "Windows":
            # PowerShell Toast 通知 — 点击通知本体打开 Web 界面
            esc_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            esc_body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            ps = (
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,'
                f'ContentType = WindowsRuntime] > $null;'
                f'$template = [Windows.UI.Notifications.ToastNotificationManager]::'
                f'GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
                f'$template.SelectSingleNode("//text[@id=1]").InnerText = "{esc_title}";'
                f'$template.SelectSingleNode("//text[@id=2]").InnerText = "{esc_body}";'
                f'$template.DocumentElement.SetAttribute("launch", "{WEB_URL}");'
                f'$template.DocumentElement.SetAttribute("activationType", "protocol");'
                f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
                f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier'
                f'("Simple Todo").Show($toast);'
            )
            result = subprocess.run(
                ["powershell", "-Command", ps],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"[notifier] Toast 失败: {result.stderr.strip()}")
        else:
            print(f"[notifier] {title}: {body}")
    except Exception as e:
        print(f"[notifier] 通知失败: {e}")


def check_deadlines():
    conn = get_db()
    now = time.time()

    tasks = conn.execute(
        "SELECT id, title, deadline FROM tasks WHERE deadline IS NOT NULL AND done = 0"
    ).fetchall()

    for task in tasks:
        remaining = task["deadline"] - now
        if remaining > 7 * DAY:
            continue

        for seconds in CHECKPOINTS:
            if remaining <= seconds:
                key = f"{task['id']}-{seconds}"
                if key in _notified:
                    break
                _notified.add(key)
                _save_notified()

                if remaining <= 0:
                    title = f"⏰ 已到期 — Simple Todo"
                    body = f"「{task['title']}」已经截止"
                elif remaining < HOUR:
                    mins = max(1, int(remaining // MINUTE))
                    title = f"🚨 {mins} 分钟后截止 — Simple Todo"
                    body = f"「{task['title']}」将在 {mins} 分钟后截止"
                elif remaining < DAY:
                    hrs = int(remaining // HOUR) + 1
                    title = f"⏰ {hrs} 小时后截止 — Simple Todo"
                    body = f"「{task['title']}」将在约 {hrs} 小时后截止"
                else:
                    days = int(remaining // DAY) + 1
                    title = f"📅 {days} 天后截止 — Simple Todo"
                    body = f"「{task['title']}」将在 {days} 天后截止"

                try:
                    print(f"[{datetime.now():%H:%M:%S}] {title}: {body}")
                except UnicodeEncodeError:
                    print(f"[{datetime.now():%H:%M:%S}] 通知: {task['title']}")
                notify(title, body)
                break

    conn.close()


_running = True

def stop():
    global _running
    _running = False


def _handle_signal(sig, frame):
    """信号处理：优雅退出并清理 PID 文件"""
    stop()
    remove_pid()
    sys.exit(0)


def stop_daemon():
    """停止正在运行的通知服务"""
    pid = read_pid()
    if pid is None or not is_running(pid):
        print("通知服务未在运行")
        remove_pid()
        sys.exit(0)
    os.kill(pid, signal.SIGTERM)
    time.sleep(0.5)
    if is_running(pid):
        print(f"警告: 进程 {pid} 未能终止，请手动处理")
    else:
        print(f"通知服务已停止 (PID: {pid})")
    remove_pid()


def main():
    # 加载已通知记录（防重复）
    _load_notified()

    # 防止重复启动
    pid = read_pid()
    if pid is not None and is_running(pid):
        print(f"通知服务已在运行中 (PID: {pid})")
        sys.exit(1)

    write_pid()

    # 注册信号处理
    signal.signal(signal.SIGINT, _handle_signal)
    try:
        signal.signal(signal.SIGTERM, _handle_signal)
    except AttributeError:
        pass  # Windows 不支持 SIGTERM handler

    try:
        print(f"  [通知服务] 已启动 (平台: {platform.system()})")
        print(f"  [通知服务] 每 {CHECK_INTERVAL} 秒检查一次截止日期")
        while _running:
            try:
                check_deadlines()
            except Exception as e:
                print(f"  [通知服务] 检查出错: {e}")
            # 用短睡眠分段，以便快速响应退出信号
            for _ in range(CHECK_INTERVAL):
                if not _running:
                    break
                time.sleep(1)
    finally:
        remove_pid()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Todo 通知服务")
    parser.add_argument(
        "--stop", action="store_true", help="停止正在运行的通知服务"
    )
    args = parser.parse_args()

    if args.stop:
        stop_daemon()
    else:
        main()
