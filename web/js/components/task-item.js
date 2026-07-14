// ==========================================
// task-item.js — 单条任务行（纯渲染函数）
// 所有操作按钮始终可见
// ==========================================

function formatDate(ts) {
    if (!ts) return '';
    const d = new Date(ts * 1000);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatDeadline(ts) {
    if (!ts) return '长期';
    const d = new Date(ts * 1000);
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} 截止`;
}

function isExpired(ts, done) {
    if (!ts || done) return false;
    return ts < Date.now() / 1000;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

export function renderTaskItem(task, { showManage = false } = {}) {
    const doneClass = task.done ? ' st-task--done' : '';
    const focusClass = task.focus ? ' st-task--focus' : '';
    const expiredClass = isExpired(task.deadline, task.done) ? ' st-task--expired' : '';

    const dateLabel = task.done
        ? `完成于 ${formatDate(task.done_at)}`
        : `创建于 ${formatDate(task.created_at)}`;

    const deadlineLabel = formatDeadline(task.deadline);
    const deadlineClass = isExpired(task.deadline, task.done) ? ' st-task__deadline--expired' : '';

    const focusStar = task.focus
        ? '<span class="st-task__focus-star" data-action="focus-toggle" title="取消聚焦">◆</span>'
        : '<span class="st-task__focus-star st-task__focus-star--off" data-action="focus-toggle" title="设为聚焦">◇</span>';

    const mainAction = task.done
        ? '<button class="st-task__btn st-task__btn--undone" data-action="undone">恢复</button>'
        : '<button class="st-task__btn st-task__btn--done" data-action="done">完成</button>';

    const manageActions = showManage ? `
        <button class="st-task__btn st-task__btn--focus"
                data-action="focus-toggle"
                title="${task.focus ? '取消聚焦' : '设为聚焦'}">
            ${task.focus ? '取消聚焦' : '聚焦'}
        </button>
        <button class="st-task__btn st-task__btn--edit" data-action="edit">编辑</button>
        <button class="st-task__btn st-task__btn--delete" data-action="delete">删除</button>
    ` : '';

    const notesIndicator = task.notes
        ? ' <span class="st-task__notes-badge" title="有备注"></span>'
        : '';

    return `
        <div class="st-task${doneClass}${focusClass}${expiredClass}" data-task-id="${task.id}">
            ${focusStar}
            <span class="st-task__title" data-action="view-task">${escapeHtml(task.title)}${notesIndicator}</span>
            <span class="st-task__deadline${deadlineClass}">${deadlineLabel}</span>
            <span class="st-task__date">${dateLabel}</span>
            <div class="st-task__actions">
                ${manageActions}
                ${mainAction}
            </div>
        </div>`;
}
