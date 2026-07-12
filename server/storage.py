"""持久化层 — SQLite 存储，WAL 模式，自动从 JSON 迁移。"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.expanduser('~/.simple_todo/tasks.db')
_init_done = False


def _ensure_init():
    """延迟初始化：首次调用时创建表 + 执行 JSON 迁移。"""
    global _init_done
    if _init_done:
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        priority    INTEGER NOT NULL DEFAULT 1 CHECK(priority >= 1 AND priority <= 5),
        done        INTEGER NOT NULL DEFAULT 0,
        created_at  REAL NOT NULL,
        done_at     REAL
    )""")
    conn.commit()
    _migrate_if_needed(conn)
    conn.close()
    _init_done = True


def _migrate_if_needed(conn):
    """如果旧 JSON 文件存在且数据库为空，自动迁移数据。"""
    import json

    json_file = os.path.expanduser('~/.simple_todo/tasks.json')
    if not os.path.exists(json_file):
        return

    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count > 0:
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    for t in tasks:
        conn.execute(
            "INSERT INTO tasks (id, title, priority, done, created_at, done_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (t['id'], t['title'], t['priority'], int(t['done']),
             t['created_at'], t['done_at'])
        )
    conn.commit()
    os.replace(json_file, json_file + '.migrated')


def _row_to_dict(row) -> dict:
    """sqlite3.Row → dict，done 从 INTEGER 转回 bool。"""
    return {
        'id': row['id'],
        'title': row['title'],
        'priority': row['priority'],
        'done': bool(row['done']),
        'created_at': row['created_at'],
        'done_at': row['done_at'],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 对外 API
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> list[dict]:
    """获取所有任务，按优先级 → 创建时间排序。"""
    _ensure_init()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY priority ASC, created_at ASC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_task(task_id: int) -> dict | None:
    """获取单个任务。"""
    _ensure_init()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def add_task(title: str, priority: int) -> dict:
    """创建任务，返回完整字典。"""
    _ensure_init()
    now = datetime.now().timestamp()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "INSERT INTO tasks (title, priority, done, created_at) VALUES (?, ?, 0, ?)",
            (title, priority, now)
        )
        conn.commit()
        task_id = cur.lastrowid
    return {
        'id': task_id, 'title': title, 'priority': priority,
        'done': False, 'created_at': now, 'done_at': None,
    }


def mark_done(task_id: int) -> dict | None:
    """标记完成。调用方应已校验任务存在且未完成。"""
    _ensure_init()
    now = datetime.now().timestamp()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            "UPDATE tasks SET done = 1, done_at = ? WHERE id = ? AND done = 0",
            (now, task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def mark_undone(task_id: int) -> dict | None:
    """恢复未完成。调用方应已校验任务存在且已完成。"""
    _ensure_init()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            "UPDATE tasks SET done = 0, done_at = NULL WHERE id = ? AND done = 1",
            (task_id,)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def delete_task(task_id: int) -> dict | None:
    """删除任务（原子操作），返回删除前的数据。"""
    _ensure_init()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            return None
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return _row_to_dict(row)


def update_priority(task_id: int, priority: int) -> dict | None:
    """修改优先级。调用方应已校验任务存在。"""
    _ensure_init()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute(
            "UPDATE tasks SET priority = ? WHERE id = ?",
            (priority, task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def search_tasks(keyword: str) -> list[dict]:
    """按标题搜索（大小写不敏感），按优先级 → 创建时间排序。"""
    _ensure_init()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM tasks WHERE title LIKE ? ORDER BY priority ASC, created_at ASC",
            (f'%{keyword}%',)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]
