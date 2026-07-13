// ==========================================
// status-bar.js — 状态栏组件
// 订阅 state，显示：连接状态、任务计数、加载指示器、错误横幅
// 不派发事件，纯展示
// ==========================================

import * as state from '../state.js';

/**
 * 渲染状态栏
 * @param {HTMLElement} container
 */
export function renderStatusBar(container) {
    if (!container) return;

    // 初始渲染
    _render(container, state.getState());

    // 订阅状态变化
    state.on('change', (newState) => _render(container, newState));
}

function _render(container, s) {
    const doneCount = s.allTasks.filter(t => t.done).length;
    const totalCount = s.allTasks.length;

    let html = '<div class="st-status">';

    // 左侧：连接状态 + 任务计数
    html += '<div class="st-status__left">';
    if (s.loading) {
        html += '<span class="st-status__loading">⏳ 同步中...</span>';
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
                <span>⚠ ${escapeHtml(s.error.message)}</span>
                <button class="st-error__dismiss" data-action="dismiss-error" title="关闭">×</button>
            </div>`;
    }

    container.innerHTML = html;

    // 绑定错误关闭按钮（通过事件冒泡，由 app.js 处理）
    const dismissBtn = container.querySelector('[data-action="dismiss-error"]');
    if (dismissBtn) {
        dismissBtn.addEventListener('click', () => {
            container.dispatchEvent(new CustomEvent('dismiss-error', {
                bubbles: true,
            }));
        });
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
