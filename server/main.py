"""Simple Todo REST API 服务。"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from server.models import Task, TaskCreate, TaskUpdate
from server.storage import (
    load_tasks, get_task, add_task,
    mark_done, mark_undone, delete_task,
    update_priority, search_tasks,
    NotFoundError, ConflictError,
)

app = FastAPI(title="Simple Todo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return load_tasks(all=all)


@app.get("/tasks/search", response_model=list[Task])
def search_tasks_endpoint(q: str = Query(..., description="搜索关键词")):
    """按标题搜索任务（大小写不敏感）。"""
    return search_tasks(q)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task_endpoint(task_id: int):
    """获取单个任务详情。"""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务 [{task_id}] 未找到")
    return task


@app.post("/tasks", response_model=Task, status_code=201)
def add_task_endpoint(body: TaskCreate):
    """添加一条新任务。"""
    return add_task(body.title, body.priority)


@app.put("/tasks/{task_id}/done", response_model=Task)
def done_task(task_id: int):
    """将任务标记为已完成。"""
    try:
        return mark_done(task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/tasks/{task_id}/undone", response_model=Task)
def undone_task(task_id: int):
    """将任务恢复为未完成。"""
    try:
        return mark_undone(task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/tasks/{task_id}", response_model=Task)
def delete_task_endpoint(task_id: int):
    """删除一条任务。"""
    try:
        return delete_task(task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/tasks/{task_id}/priority", response_model=Task)
def set_priority(task_id: int, body: TaskUpdate):
    """修改任务优先级。"""
    try:
        return update_priority(task_id, body.priority)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
