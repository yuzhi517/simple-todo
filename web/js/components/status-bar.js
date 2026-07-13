// ==========================================
// status-bar.js — 状态栏组件（纯渲染函数）
// 不订阅 state，由 app.js 调用
// ==========================================

/**
 * 渲染状态栏
 * @param {HTMLElement} container
 * @param {object} s - 状态快照
 */
export function renderStatusBar(container, s) {
    if (!container) return;

    const doneCount = s.allTasks.filter(t => t.done).length;
    const totalCount = s.allTasks.length;
    const focusCount = s.allTasks.filter(t => t.focus && !t.done).length;

    let html = '<div class="st-status">';

    html += '<div class="st-status__left">';
    if (s.loading) {
        html += '<span class="st-status__loading">同步中...</span>';
    } else {
        const dotClass = s.connectionOk ? 'st-status__dot--ok' : 'st-status__dot--err';
        html += `<span class="st-status__dot ${dotClass}"></span>`;
        html += '<span>';
        if (s.searchActive) {
            html += `搜索 "${escapeHtml(s.searchQuery)}" 找到 ${s.tasks.length} 条结果`;
        } else if (totalCount === 0) {
            html += '还没有任务';
        } else {
            html += `共 ${totalCount} 条任务`;
            if (focusCount > 0) {
                html += `，◆ ${focusCount} 条聚焦`;
            }
            if (doneCount > 0) {
                html += `，${doneCount} 条已完成`;
            }
        }
        html += '</span>';
    }
    html += '</div>';

    html += '</div>'; // .st-status

    // 错误横幅
    if (s.error) {
        html += `
            <div class="st-error">
                <span>${escapeHtml(s.error.message)}</span>
                <button class="st-error__dismiss" data-action="dismiss-error" title="关闭">×</button>
            </div>`;
    }

    container.innerHTML = html;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
