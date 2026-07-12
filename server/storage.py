"""持久化层 — JSON 文件读写，带文件锁、写序列化和原子写入保护。"""

import json
import os
import tempfile
import fcntl
import sys
import threading
from contextlib import contextmanager

DATA_DIR = os.path.expanduser('~/.simple_todo')
DATA_FILE = os.path.join(DATA_DIR, 'tasks.json')

# 写操作互斥锁：防止多个请求同时 load→modify→save 导致丢失更新
_write_lock = threading.Lock()


def _ensure_data_dir():
    """确保数据目录存在。"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_tasks() -> list[dict]:
    """从 JSON 文件加载任务列表（带文件锁）。

    返回 dict 列表；若文件不存在或损坏则返回空列表。
    数据格式与旧版完全兼容。
    """
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # 获取共享锁，允许并发读
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f'警告: 数据文件 {DATA_FILE} 已损坏，将使用空列表并备份损坏文件。',
                      file=sys.stderr)
                # 备份损坏文件
                backup_path = DATA_FILE + '.corrupted'
                try:
                    os.replace(DATA_FILE, backup_path)
                except OSError:
                    pass
                return []
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except OSError as e:
        print(f'警告: 无法读取数据文件: {e}', file=sys.stderr)
        return []


def save_tasks(tasks: list[dict]):
    """将任务列表原子写入 JSON 文件（先写临时文件，再 rename）。

    使用排他锁防止并发写入导致的数据丢失。
    """
    _ensure_data_dir()

    # 先写入临时文件，确保写入完整后再原子替换
    tmp_fd = None
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix='.json',
            prefix='.tasks_tmp_',
            dir=DATA_DIR,
        )
        with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # 原子替换目标文件
        os.replace(tmp_path, DATA_FILE)

    except Exception:
        # 写入失败时清理临时文件
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


@contextmanager
def locked_write():
    """写操作上下文管理器：持有排他锁完成 load→modify→save 流程。

    用法:
        with locked_write():
            tasks = load_tasks()
            tasks.append(...)
            save_tasks(tasks)
    """
    _write_lock.acquire()
    try:
        yield
    finally:
        _write_lock.release()
