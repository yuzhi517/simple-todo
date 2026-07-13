// ==========================================
// task-item.js — 单条任务行（纯渲染函数）
// 不订阅 state，不调 api，不操作 DOM
// 返回 HTML 字符串，通过 data-action 属性支持事件委托
// ==========================================

/**
 * 格式化时间戳为可读日期
 * @param {number|null} ts - Unix 时间戳
 * @returns {string}
 */
function formatDate(ts) {
    if (!ts) return '';
    const d = new Date(ts * 1000);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * 转义 HTML 特殊字符
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * 渲染单条任务行
 * @param {object} task - { id, title, priority, done, created_at, done_at }
 * @returns {string} HTML 字符串
 */
export function renderTaskItem(task) {
    const doneClass = task.done ? ' st-task--done' : '';
    const dateLabel = task.done ? `完成于 ${formatDate(task.done_at)}` : `创建于 ${formatDate(task.created_at)}`;

    return `
        <div class="st-task${doneClass}" data-task-id="${task.id}">
            <span class="st-task__priority" data-priority="${task.priority}">
                ★${task.priority}
            </span>
            <span class="st-task__title">${escapeHtml(task.title)}</span>
            <span class="st-task__date">${dateLabel}</span>
            <select class="st-task__priority-select" data-action="priority-change">
                ${[1, 2, 3, 4, 5].map(p =>
                    `<option value="${p}"${p === task.priority ? ' selected' : ''}>★${p}</option>`
                ).join('')}
            </select>
            <div class="st-task__actions">
                ${task.done ? `
                    <button class="st-task__btn st-task__btn--undone" data-action="undone">恢复</button>
                ` : `
                    <button class="st-task__btn st-task__btn--done" data-action="done">完成</button>
                `}
                <button class="st-task__btn st-task__btn--delete" data-action="delete">删除</button>
            </div>
        </div>`;
}
