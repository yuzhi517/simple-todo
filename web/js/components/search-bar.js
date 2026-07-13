// ==========================================
// search-bar.js — 搜索栏组件
// 不订阅 state，不调 api
// 派发事件: search-submit (detail: { query }), search-clear
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
                    title="清除搜索"
                >×</button>
            </div>
        </div>
    `;

    const input = container.querySelector('#search-input');
    const clearBtn = container.querySelector('#search-clear-btn');

    // 输入防抖 → 派发搜索事件
    input.addEventListener('input', () => {
        const query = input.value;

        // 显示/隐藏清除按钮
        if (query.length > 0) {
            clearBtn.classList.add('st-search__clear--visible');
        } else {
            clearBtn.classList.remove('st-search__clear--visible');
        }

        // 防抖
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

    // 清除按钮
    clearBtn.addEventListener('click', () => {
        input.value = '';
        clearBtn.classList.remove('st-search__clear--visible');
        clearTimeout(_debounceTimer);
        container.dispatchEvent(new CustomEvent('search-clear', {
            bubbles: true,
        }));
        input.focus();
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
