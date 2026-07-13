"""持久化层 — SQLite 存储，WAL 模式，自动从 JSON 迁移。"""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime

DB_PATH = os.path.expanduser('~/.simple_todo/tasks.db')
_init_lock = threading.Lock()
_init_done = False


# ═══════════════════════════════════════════════════════════════════════════════
# 自定义异常
# ═══════════════════════════════════════════════════════════════════════════════

class NotFoundError(Exception):
    """资源不存在。"""
    pass


class ConflictError(Exception):
    """状态冲突（如重复标记完成）。"""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# 内部辅助
# ═══════════════════════════════════════════════════════════════════════════════

def _get_conn() -> sqlite3.Connection:
    """获取数据库连接（已设置 row_factory）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _escape_like(keyword: str) -> str:
    """转义 LIKE 通配符 % 和 _ 防止意外匹配。"""
    return keyword.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _ensure_column(conn: sqlite3.Connection, table: str, col: str, col_def: str):
    """如果表中缺少指定列，自动 ALTER TABLE 添加（兼容旧数据库）。"""
    cols = [row['name'] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if col not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
        conn.commit()


def _ensure_init():
    """线程安全的延迟初始化：首次调用时创建表 + 执行 JSON 迁移。"""
    global _init_done
    if _init_done:
        return

    with _init_lock:
        if _init_done:           # 双重检查：锁内再确认一次
            return

        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = _get_conn()
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            priority    INTEGER NOT NULL DEFAULT 1 CHECK(priority >= 1 AND priority <= 5),
            deadline    REAL,
            focus       INTEGER NOT NULL DEFAULT 0,
            notes       TEXT,
            done        INTEGER NOT NULL DEFAULT 0,
            created_at  REAL NOT NULL,
            done_at     REAL
        )""")
        # 兼容旧表：如果缺少新列则自动添加
        _ensure_column(conn, 'tasks', 'deadline', 'REAL')
        _ensure_column(conn, 'tasks', 'focus', 'INTEGER NOT NULL DEFAULT 0')
        _ensure_column(conn, 'tasks', 'notes', 'TEXT')
        conn.commit()
        _migrate_if_needed(conn)
        conn.close()
        _init_done = True


def _migrate_if_needed(conn: sqlite3.Connection):
    """如果旧 JSON 文件存在且数据库为空，自动迁移数据。"""
    import json

    json_file = os.path.expanduser('~/.simple_todo/tasks.json')
    if not os.path.exists(json_file):
        return

    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count > 0:
        return

    try:
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
    except (json.JSONDecodeError, OSError, KeyError) as e:
        # 迁移失败不影响正常使用，数据库为空就从头开始
        print(f'警告: 旧数据迁移失败 ({e})，将从空白数据库开始。', flush=True)

    # 无论迁移成功与否，都备份旧文件
    try:
        os.replace(json_file, json_file + '.migrated')
    except OSError:
        pass


def _row_to_dict(row: sqlite3.Row) -> dict:
    """sqlite3.Row → dict，done/focus 从 INTEGER 转回 bool。"""
    return {
        'id': row['id'],
        'title': row['title'],
        'priority': row['priority'],
        'deadline': row['deadline'],
        'focus': bool(row['focus']),
        'notes': row['notes'],
        'done': bool(row['done']),
        'created_at': row['created_at'],
        'done_at': row['done_at'],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 对外 API
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks(*, all: bool = True) -> list[dict]:
    """获取任务列表。
    排序：聚焦优先 → 有截止日期的按时间排 → 长期的排最后 → 同组按创建时间
    - all=True：所有任务
    - all=False：只返回未完成的
    """
    _ensure_init()
    sql = "SELECT * FROM tasks"
    params = ()
    if not all:
        sql += " WHERE done = 0"
    sql += " ORDER BY focus DESC, deadline IS NULL, deadline ASC, created_at ASC"

    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_task(task_id: int) -> dict | None:
    """获取单个任务。"""
    _ensure_init()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row) if row else None


def add_task(title: str, priority: int = 1, deadline: float | None = None,
             focus: bool = False, notes: str | None = None) -> dict:
    """创建任务，返回完整字典。"""
    _ensure_init()
    now = datetime.now().timestamp()
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, priority, deadline, focus, notes, done, created_at) "
            "VALUES (?, ?, ?, ?, ?, 0, ?)",
            (title, priority, deadline, int(focus), notes, now)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return _row_to_dict(row)


def mark_done(task_id: int) -> dict:
    """原子标记完成 — 在事务内完成校验+更新。

    Raises:
        NotFoundError: 任务不存在
        ConflictError: 任务已完成
    """
    _ensure_init()
    now = datetime.now().timestamp()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")
        if row['done']:
            conn.rollback()
            raise ConflictError(f"任务 [{task_id}] 已经是已完成状态")

        conn.execute(
            "UPDATE tasks SET done = 1, done_at = ? WHERE id = ?",
            (now, task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row)


def mark_undone(task_id: int) -> dict:
    """原子恢复未完成 — 在事务内完成校验+更新。

    Raises:
        NotFoundError: 任务不存在
        ConflictError: 任务当前就是未完成状态
    """
    _ensure_init()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")
        if not row['done']:
            conn.rollback()
            raise ConflictError(f"任务 [{task_id}] 当前就是未完成状态")

        conn.execute(
            "UPDATE tasks SET done = 0, done_at = NULL WHERE id = ?",
            (task_id,)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row)


def delete_task(task_id: int) -> dict:
    """原子删除 — 返回被删除的数据。

    Raises:
        NotFoundError: 任务不存在
    """
    _ensure_init()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return _row_to_dict(row)


def update_priority(task_id: int, priority: int) -> dict:
    """原子修改优先级 — 在事务内完成校验+更新。

    Raises:
        NotFoundError: 任务不存在
    """
    _ensure_init()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")

        conn.execute(
            "UPDATE tasks SET priority = ? WHERE id = ?",
            (priority, task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row)


def update_notes(task_id: int, notes: str | None) -> dict:
    """更新任务备注。

    Raises:
        NotFoundError: 任务不存在
    """
    _ensure_init()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")
        conn.execute(
            "UPDATE tasks SET notes = ? WHERE id = ?",
            (notes, task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row)


def search_tasks(keyword: str) -> list[dict]:
    """按标题搜索（大小写不敏感），已转义 LIKE 通配符。"""
    _ensure_init()
    escaped = _escape_like(keyword)
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE title LIKE ? ESCAPE '\\' "
            "ORDER BY focus DESC, deadline IS NULL, deadline ASC, created_at ASC",
            (f'%{escaped}%',)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_focus(task_id: int, focus: bool) -> dict:
    """切换聚焦状态。

    Raises:
        NotFoundError: 任务不存在
    """
    _ensure_init()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")
        conn.execute(
            "UPDATE tasks SET focus = ? WHERE id = ?",
            (int(focus), task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row)


def update_deadline(task_id: int, deadline: float | None) -> dict:
    """更新截止日期（None 表示长期）。

    Raises:
        NotFoundError: 任务不存在
    """
    _ensure_init()
    with _get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            conn.rollback()
            raise NotFoundError(f"任务 [{task_id}] 未找到")
        conn.execute(
            "UPDATE tasks SET deadline = ? WHERE id = ?",
            (deadline, task_id)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return _row_to_dict(row)
