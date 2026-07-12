"""显示层 — 任务列表的终端渲染，支持中文对齐。"""

from __future__ import annotations

import unicodedata
from datetime import datetime


def display_width(s: str) -> int:
    """计算字符串在终端中实际占用的列宽。
    CJK 字符占两列，普通字符占一列。
    """
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w


def pad_to_width(s: str, target_width: int) -> str:
    """在字符串末尾补空格，使其显示宽度等于 target_width。"""
    current = display_width(s)
    if current >= target_width:
        return s
    return s + ' ' * (target_width - current)


def format_date(ts) -> str:
    """将时间戳转为可读日期字符串。"""
    if ts is None:
        return ''
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')


def print_task_list(tasks: list[dict], show_all: bool = False, total_count: int | None = None):
    """在终端渲染任务列表。

    Args:
        tasks: 从 API 获取的任务列表（已是排序后的结果）
        show_all: 是否展示"未完成/已完成"分组
        total_count: 任务总数（用于区分"无任务"和"全部完成"）
    """
    if not tasks:
        if show_all:
            print('现在还没有任何任务被添加进来。')
        elif total_count is not None and total_count > 0:
            print('列表里的任务全部都被做完了！🎉')
            print(f'  列表里总共有 {total_count} 条任务。')
        elif total_count is not None and total_count == 0:
            print('现在还没有任何任务被添加进来。')
        else:
            print('现在还没有任何任务被添加进来。')
        return

    sorted_tasks = tasks
    pri_width = max(max(display_width(f' ★{t["priority"]}') for t in sorted_tasks), 1)

    if show_all:
        undone = [t for t in sorted_tasks if not t['done']]
        done = [t for t in sorted_tasks if t['done']]
        groups = [('未完成', undone), ('已完成', done)]
    else:
        groups = [('', sorted_tasks)]

    first_group = True
    for label, group in groups:
        if not group:
            continue

        if label and not first_group:
            print()

        if label:
            header = f'── {label} ──'
            print(header)

        id_width = max(max(display_width(str(t['id'])) for t in group), 2)

        for t in group:
            tid_str = pad_to_width(str(t['id']), id_width)
            date_str = f'  [{format_date(t["created_at"])}]'
            pri_str = pad_to_width(f' ★{t["priority"]}', pri_width)
            print(f'  ▸ {tid_str} | {pri_str} | {t["title"]}{date_str}')

        first_group = False


def print_search_results(results: list[dict], keyword: str):
    """在终端渲染搜索结果。

    Args:
        results: 从 API 获取的搜索结果（已是排序后的）
        keyword: 搜索关键词（用于标题显示）
    """
    if not results:
        print(f'在标题里没有找到包含 "{keyword}" 的任务。')
        return

    print(f'搜索 "{keyword}" 找到了以下结果（一共 {len(results)} 条）:')
    id_width = max(max(display_width(str(t['id'])) for t in results), 2)
    pri_w = max(max(display_width(f' ★{t["priority"]}') for t in results), 1)
    for t in results:
        tid_str = pad_to_width(str(t['id']), id_width)
        pri_str = pad_to_width(f' ★{t["priority"]}', pri_w)
        print(f'  ▸ {tid_str} | {pri_str} | {t["title"]}')
