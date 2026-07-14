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
MINUTE = 60
HOUR = 3600
DAY = 86400

# 提醒节点：5分钟、1小时、12小时、1天、3天、7天
CHECKPOINTS = [
    (5 * MINUTE,  '5 分钟后截止', '🚨'),
    (1 * HOUR,    '1 小时后截止', '⚠️'),
    (12 * HOUR,   '12 小时后截止', '⏰'),
    (1 * DAY,     '1 天后截止',   '📅'),
    (3 * DAY,     '3 天后截止',   '📅'),
    (7 * DAY,     '7 天后截止',   '📅'),
]

_notified = set()  # 防重复通知 (task_id, checkpoint_seconds)


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
        if remaining < 0 or remaining > 7 * DAY:
            continue

        for seconds, label, emoji in CHECKPOINTS:
            if remaining <= seconds:
                key = f"{task['id']}-{seconds}"
                if key in _notified:
                    break
                _notified.add(key)

                if remaining < HOUR:
                    mins = max(1, int(remaining // MINUTE))
                    title = f"{emoji} {label} — Simple Todo"
                    body = f"「{task['title']}」将在 {mins} 分钟后截止"
                elif remaining < DAY:
                    hrs = int(remaining // HOUR) + 1
                    title = f"{emoji} {label} — Simple Todo"
                    body = f"「{task['title']}」将在约 {hrs} 小时后截止"
                else:
                    days = int(remaining // DAY) + 1
                    title = f"{emoji} {label} — Simple Todo"
                    body = f"「{task['title']}」将在 {days} 天后截止"

                print(f"[{datetime.now():%H:%M:%S}] {title}: {body}")
                notify(title, body)
                break

    conn.close()


_running = True

def stop():
    global _running
    _running = False


def main():
    print(f"  [通知服务] 已启动 (平台: {platform.system()})")
    print(f"  [通知服务] 每 {CHECK_INTERVAL // 60} 分钟检查一次截止日期")
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


if __name__ == "__main__":
    main()
