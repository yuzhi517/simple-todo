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
from datetime import datetime

DB_PATH = os.path.expanduser("~/.simple_todo/tasks.db")
CHECK_INTERVAL = 5 * 60  # 5 分钟
ONE_HOUR = 3600
ONE_DAY = 86400

_notified = set()  # 防重复通知 (task_id, hour_bucket)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def notify(title: str, body: str):
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run([
                "osascript", "-e",
                f'display notification "{body}" with title "{title}" sound name "Glass"'
            ])
        elif system == "Windows":
            # PowerShell Toast 通知
            ps = (
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,'
                f'ContentType = WindowsRuntime] > $null;'
                f'$template = [Windows.UI.Notifications.ToastNotificationManager]::'
                f'GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
                f'$template.SelectSingleNode("//text[@id=1]").InnerText = "{title}";'
                f'$template.SelectSingleNode("//text[@id=2]").InnerText = "{body}";'
                f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
                f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier'
                f'("Simple Todo").Show($toast);'
            )
            subprocess.run(["powershell", "-Command", ps], capture_output=True)
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
        if remaining < 0 or remaining > ONE_DAY:
            continue

        hours_left = int(remaining // 3600)
        key = f"{task['id']}-{hours_left}h"

        if key in _notified:
            continue
        _notified.add(key)

        if remaining < ONE_HOUR:
            mins = max(1, int(remaining // 60))
            title = "⚠️ 即将到期 — Simple Todo"
            body = f"「{task['title']}」将在 {mins} 分钟后截止"
        else:
            title = "⏰ 临近截止 — Simple Todo"
            body = f"「{task['title']}」将在约 {hours_left} 小时后截止"

        print(f"[{datetime.now():%H:%M:%S}] {title}: {body}")
        notify(title, body)

    conn.close()


def main():
    print(f"Simple Todo 通知服务已启动 (平台: {platform.system()})")
    print(f"每 {CHECK_INTERVAL // 60} 分钟检查一次截止日期...")
    while True:
        try:
            check_deadlines()
        except Exception as e:
            print(f"[notifier] 检查出错: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
