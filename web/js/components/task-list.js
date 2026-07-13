// ==========================================
// task-list.js — 任务列表组件
// 导入 task-item.js（纯渲染子组件，合理）
// 订阅 state，使用事件委托处理用户操作
// 派发事件: task-done, task-undone, task-delete,
//           task-priority-change, view-toggle, search-clear
// ==========================================

import * as state from '../state.js';
import { renderTaskItem } from './task-item.js';

let _listContainer = null;

/**
 * 渲染任务列表
 * @param {HTMLElement} container
 */
export function renderTaskList(container) {
    if (!container) return;

    _listContainer = container;

    // 初始渲染
    _render(container, state.getState());

    // 订阅状态变化
    state.on('change', (newState) => _render(container, newState));

    // 事件委托：在容器上统一监听所有交互
    container.addEventListener('click', _handleClick);
    container.addEventListener('change', _handleChange);
}

/**
 * 事件委托 — 统一处理所有点击
 */
function _handleClick(e) {
    const action = e.target.dataset.action;
    if (!action) return;

    // === 视图级操作（不需要 task 上下文） ===
    if (action === 'show-all') {
        _listContainer.dispatchEvent(new CustomEvent('view-toggle', {
            detail: { showAll: true },
            bubbles: true,
        }));
        return;
    }
    if (action === 'show-undone') {
        _listContainer.dispatchEvent(new CustomEvent('view-toggle', {
            detail: { showAll: false },
            bubbles: true,
        }));
        return;
    }
    if (action === 'clear-search') {
        _listContainer.dispatchEvent(new CustomEvent('search-clear', {
            bubbles: true,
        }));
        return;
    }

    // === 任务级操作 ===
    const taskEl = e.target.closest('.st-task');
    if (!taskEl) return;

    const taskId = parseInt(taskEl.dataset.taskId, 10);
    const eventMap = {
        'done': 'task-done',
        'undone': 'task-undone',
        'delete': 'task-delete',
    };

    const eventName = eventMap[action];
    if (eventName) {
        _listContainer.dispatchEvent(new CustomEvent(eventName, {
            detail: { id: taskId },
            bubbles: true,
        }));
    }
}

/**
 * 事件委托 — 优先级下拉框变更
 */
function _handleChange(e) {
    if (e.target.dataset.action !== 'priority-change') return;

    const taskEl = e.target.closest('.st-task');
    if (!taskEl) return;

    const taskId = parseInt(taskEl.dataset.taskId, 10);
    const newPriority = parseInt(e.target.value, 10);

    _listContainer.dispatchEvent(new CustomEvent('task-priority-change', {
        detail: { id: taskId, priority: newPriority },
        bubbles: true,
    }));
}

/**
 * 渲染函数
 */
function _render(container, s) {
    const { tasks, showAll, searchActive, searchQuery, allTasks } = s;

    let html = '<div class="st-list">';

    // 视图切换
    if (searchActive) {
        html += `
            <div class="st-list__toggle">
                <button class="st-list__toggle-btn st-list__toggle-btn--active"
                        data-action="clear-search">← 返回列表</button>
            </div>`;
    } else {
        html += `
            <div class="st-list__toggle">
                <button class="st-list__toggle-btn${!showAll ? ' st-list__toggle-btn--active' : ''}"
                        data-action="show-undone">未完成</button>
                <button class="st-list__toggle-btn${showAll ? ' st-list__toggle-btn--active' : ''}"
                        data-action="show-all">全部</button>
            </div>`;
    }

    // 空状态
    if (tasks.length === 0) {
        html += '<div class="st-list__empty">';
        if (searchActive) {
            html += '<span class="st-list__empty-icon">🔍</span>';
            html += `<p>没有找到包含 "${escapeHtml(searchQuery)}" 的任务</p>`;
        } else if (!showAll && allTasks.length > 0) {
            html += '<span class="st-list__empty-icon">🎉</span>';
            html += '<p>全部任务都完成了！</p>';
        } else {
            html += '<span class="st-list__empty-icon">📝</span>';
            html += '<p>还没有任何任务，在上面添加一个吧</p>';
        }
        html += '</div>';
    } else if (showAll && !searchActive) {
        // 分组：未完成 + 已完成
        const undone = tasks.filter(t => !t.done);
        const done = tasks.filter(t => t.done);

        if (undone.length > 0) {
            html += '<div class="st-list__group">';
            html += '<div class="st-list__group-header">未完成</div>';
            html += undone.map(renderTaskItem).join('');
            html += '</div>';
        }
        if (done.length > 0) {
            html += '<div class="st-list__group">';
            html += '<div class="st-list__group-header">已完成</div>';
            html += done.map(renderTaskItem).join('');
            html += '</div>';
        }
    } else {
        // 平铺列表
        html += tasks.map(renderTaskItem).join('');
    }

    html += '</div>';
    container.innerHTML = html;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
