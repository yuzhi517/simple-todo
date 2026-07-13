// ==========================================
// search-bar.js — 搜索栏组件
// 不订阅 state，不调 api
// 派发事件: search-submit, search-clear, search-close
// ==========================================

let _debounceTimer = null;
const DEBOUNCE_MS = 300;

/**
 * 渲染搜索栏
 * @param {HTMLElement} container
 */
export function renderSearchBar(container) {
    if (!container) return;

    container.innerHTML = `
        <div class="st-search">
            <div class="st-search__wrap">
                <input
                    type="text"
                    class="st-search__input"
                    id="search-input"
                    placeholder="搜索任务..."
                    autocomplete="off"
                >
                <button
                    class="st-search__clear"
                    id="search-clear-btn"
                    title="清除搜索内容"
                >×</button>
            </div>
            <button
                class="st-search__close"
                id="search-close-btn"
                title="关闭搜索"
            >关闭</button>
        </div>
    `;

    const input = container.querySelector('#search-input');
    const clearBtn = container.querySelector('#search-clear-btn');
    const closeBtn = container.querySelector('#search-close-btn');

    // 输入防抖 → 派发搜索事件
    input.addEventListener('input', () => {
        const query = input.value;

        if (query.length > 0) {
            clearBtn.classList.add('st-search__clear--visible');
        } else {
            clearBtn.classList.remove('st-search__clear--visible');
        }

        clearTimeout(_debounceTimer);
        _debounceTimer = setTimeout(() => {
            if (query.trim()) {
                container.dispatchEvent(new CustomEvent('search-submit', {
                    detail: { query: query.trim() },
                    bubbles: true,
                }));
            } else {
                container.dispatchEvent(new CustomEvent('search-clear', {
                    bubbles: true,
                }));
            }
        }, DEBOUNCE_MS);
    });

    // 清除按钮 → 清空输入 + 恢复列表
    clearBtn.addEventListener('click', () => {
        input.value = '';
        clearBtn.classList.remove('st-search__clear--visible');
        clearTimeout(_debounceTimer);
        container.dispatchEvent(new CustomEvent('search-clear', {
            bubbles: true,
        }));
        input.focus();
    });

    // 关闭按钮 → 关闭搜索面板
    closeBtn.addEventListener('click', () => {
        container.dispatchEvent(new CustomEvent('search-close', {
            bubbles: true,
        }));
    });

    // Enter 键立即提交
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            clearTimeout(_debounceTimer);
            const query = input.value.trim();
            if (query) {
                container.dispatchEvent(new CustomEvent('search-submit', {
                    detail: { query },
                    bubbles: true,
                }));
            }
        }
    });
}

/**
 * 聚焦搜索框（面板展开时由 app.js 调用）
 * @param {HTMLElement} container
 */
export function focusSearchInput(container) {
    if (!container) return;
    const input = container.querySelector('#search-input');
    if (input) {
        setTimeout(() => input.focus(), 100);
    }
}
