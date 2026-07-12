"""API 客户端 — 封装对后端服务的 HTTP 请求。"""

from __future__ import annotations

import os
import urllib.request
import urllib.error
import json

# 后端地址，可通过环境变量覆盖
BASE_URL = os.environ.get('TODO_API_URL', 'http://127.0.0.1:8000')


def _request(method: str, path: str, body: dict | None = None) -> dict | list | None:
    """发送 HTTP 请求的底层封装。

    Args:
        method: HTTP 方法 (GET, POST, PUT, DELETE)
        path: API 路径 (如 '/tasks', '/tasks/1/done')
        body: 请求体 (JSON 序列化)

    Returns:
        解析后的 JSON 响应，请求失败返回 None
    """
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode('utf-8')
            if raw:
                return json.loads(raw)
            return raw
    except urllib.error.HTTPError as e:
        body_text = e.read().decode('utf-8')
        try:
            detail = json.loads(body_text).get('detail', e.reason)
        except Exception:
            detail = e.reason
        print(f'出错了 ({e.code}): {detail}')
        return None
    except urllib.error.URLError as e:
        print(f'无法连接到后端服务 ({BASE_URL}): {e.reason}')
        print('请确认后端服务已启动，例如: cd server && uvicorn main:app')
        return None


class TodoAPI:
    """Todo 后端 API 的 Python 封装。"""

    @staticmethod
    def health_check() -> bool:
        """检查后端是否存活。"""
        return _request('GET', '/health') is not None

    @staticmethod
    def add_task(title: str, priority: int = 1) -> dict | None:
        """添加任务，返回创建的任务 dict。"""
        return _request('POST', '/tasks', {'title': title, 'priority': priority})

    @staticmethod
    def list_tasks(show_all: bool = False) -> list[dict]:
        """获取任务列表，默认只返回未完成的任务。"""
        suffix = '?all=true' if show_all else ''
        result = _request('GET', f'/tasks{suffix}')
        return result if isinstance(result, list) else []

    @staticmethod
    def get_task(task_id: int) -> dict | None:
        """获取单个任务。"""
        return _request('GET', f'/tasks/{task_id}')

    @staticmethod
    def done_task(task_id: int) -> dict | None:
        """将任务标记为已完成。"""
        return _request('PUT', f'/tasks/{task_id}/done')

    @staticmethod
    def undone_task(task_id: int) -> dict | None:
        """将任务恢复为未完成。"""
        return _request('PUT', f'/tasks/{task_id}/undone')

    @staticmethod
    def delete_task(task_id: int) -> dict | None:
        """删除任务。"""
        return _request('DELETE', f'/tasks/{task_id}')

    @staticmethod
    def search_tasks(keyword: str) -> list[dict]:
        """搜索任务。"""
        result = _request('GET', f'/tasks/search?q={urllib.request.quote(keyword)}')
        return result if isinstance(result, list) else []

    @staticmethod
    def set_priority(task_id: int, priority: int) -> dict | None:
        """修改任务优先级。"""
        return _request('PUT', f'/tasks/{task_id}/priority', {'priority': priority})
