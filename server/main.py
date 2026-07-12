"""Simple Todo REST API 服务。"""

from datetime import datetime
from typing import Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from server.models import Task, TaskCreate, TaskUpdate
from server.storage import load_tasks, save_tasks, locked_write

app = FastAPI(title="Simple Todo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 辅助函数 ────────────────────────────────────────────────────────────────

def _get_next_id(tasks: list[dict]) -> int:
    """生成下一个任务 ID。"""
    if not tasks:
        return 1
    return max(t['id'] for t in tasks) + 1


def _find_task(tasks: list[dict], task_id: int) -> Tuple[Optional[dict], int]:
    """按 ID 查找任务，返回 (task_dict, index) 或 (None, -1)。"""
    for i, t in enumerate(tasks):
        if t['id'] == task_id:
            return t, i
    return None, -1


# ── API 端点 ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """健康检查端点。"""
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task])
def list_tasks(all: bool = Query(False, alias="all")):
    """获取任务列表。
    - `all=false`（默认）：只返回未完成的任务
    - `all=true`：返回所有任务（含已完成）
    """
    tasks = load_tasks()

    if not all:
        tasks = [t for t in tasks if not t['done']]

    # 排序：优先级 ASC → 创建时间 ASC
    tasks.sort(key=lambda t: (t['priority'], t['created_at']))

    return tasks


@app.get("/tasks/search", response_model=list[Task])
def search_tasks(q: str = Query(..., description="搜索关键词")):
    """按标题搜索任务（大小写不敏感）。"""
    tasks = load_tasks()
    keyword = q.lower()
    results = [t for t in tasks if keyword in t['title'].lower()]
    # 搜索结果也按优先级排列
    results.sort(key=lambda t: (t['priority'], t['created_at']))
    return results


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    """获取单个任务详情。"""
    tasks = load_tasks()
    task, _ = _find_task(tasks, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务 [{task_id}] 未找到")
    return task


@app.post("/tasks", response_model=Task, status_code=201)
def add_task(body: TaskCreate):
    """添加一条新任务。"""
    with locked_write():
        tasks = load_tasks()

        task = {
            'id': _get_next_id(tasks),
            'title': body.title,
            'priority': body.priority,
            'done': False,
            'created_at': datetime.now().timestamp(),
            'done_at': None,
        }
        tasks.append(task)
        save_tasks(tasks)
    return task


@app.put("/tasks/{task_id}/done", response_model=Task)
def done_task(task_id: int):
    """将任务标记为已完成。"""
    with locked_write():
        tasks = load_tasks()
        task, idx = _find_task(tasks, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"任务 [{task_id}] 未找到")
        if task['done']:
            raise HTTPException(status_code=400, detail=f"任务 [{task_id}] 已经是已完成状态")

        tasks[idx]['done'] = True
        tasks[idx]['done_at'] = datetime.now().timestamp()
        save_tasks(tasks)
    return tasks[idx]


@app.put("/tasks/{task_id}/undone", response_model=Task)
def undone_task(task_id: int):
    """将任务恢复为未完成。"""
    with locked_write():
        tasks = load_tasks()
        task, idx = _find_task(tasks, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"任务 [{task_id}] 未找到")
        if not task['done']:
            raise HTTPException(status_code=400, detail=f"任务 [{task_id}] 当前就是未完成状态")

        tasks[idx]['done'] = False
        tasks[idx]['done_at'] = None
        save_tasks(tasks)
    return tasks[idx]


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """删除一条任务。"""
    with locked_write():
        tasks = load_tasks()
        task, idx = _find_task(tasks, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"任务 [{task_id}] 未找到")

        deleted = tasks.pop(idx)
        save_tasks(tasks)
    return {"message": f"任务 [{task_id}] 已删除: {deleted['title']}", "task": deleted}


@app.put("/tasks/{task_id}/priority", response_model=Task)
def set_priority(task_id: int, body: TaskUpdate):
    """修改任务优先级。"""
    with locked_write():
        tasks = load_tasks()
        task, idx = _find_task(tasks, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"任务 [{task_id}] 未找到")

        tasks[idx]['priority'] = body.priority
        save_tasks(tasks)
    return tasks[idx]
