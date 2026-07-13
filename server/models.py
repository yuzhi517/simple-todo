"""Simple Todo 数据模型定义。"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Task(BaseModel):
    """一条待办任务。"""
    id: int
    title: str
    priority: int = Field(default=1, ge=1, le=5, description="优先级 1-5（CLI 使用）")
    deadline: Optional[float] = Field(default=None, description="截止日期 Unix 时间戳，None 表示长期")
    focus: bool = Field(default=False, description="是否聚焦（重要任务置顶）")
    notes: Optional[str] = Field(default=None, description="详细备注内容")
    done: bool = False
    created_at: float
    done_at: Optional[float] = None


class TaskCreate(BaseModel):
    """创建任务时的请求体。"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="任务标题，不能为空，最长 500 字符",
    )
    priority: int = Field(default=1, ge=1, le=5, description="优先级 1-5（CLI 使用）")
    deadline: Optional[float] = Field(default=None, description="截止日期 Unix 时间戳，None 表示长期")
    focus: bool = Field(default=False, description="是否聚焦")
    notes: Optional[str] = Field(default=None, description="详细备注")

    @field_validator('title', mode='before')
    @classmethod
    def strip_title(cls, v: str) -> str:
        """自动去除首尾空白。"""
        if isinstance(v, str):
            return v.strip()
        return v


class TaskUpdate(BaseModel):
    """更新任务优先级时的请求体。"""
    priority: int = Field(..., ge=1, le=5, description="优先级 1-5，数字越小越重要")


class FocusUpdate(BaseModel):
    """切换聚焦状态的请求体。"""
    focus: bool = Field(..., description="是否聚焦")


class DeadlineUpdate(BaseModel):
    """更新截止日期的请求体。"""
    deadline: Optional[float] = Field(default=None, description="截止日期时间戳，None 表示长期")


class NotesUpdate(BaseModel):
    """更新备注的请求体。"""
    notes: Optional[str] = Field(default=None, description="备注内容，None 表示清空")
