// ==========================================
// task-form.js — 添加任务表单组件
// 不订阅 state，不调 api
// 派发事件: task-create (detail: { title, priority })
// ==========================================

/**
 * 渲染添加任务表单
 * @param {HTMLElement} container
 */
export function renderTaskForm(container) {
    if (!container) return;

    container.innerHTML = `
        <form class="st-form" id="task-form-el">
            <input
                type="text"
                class="st-form__input"
                id="task-title-input"
                placeholder="输入新任务标题..."
                maxlength="500"
                autocomplete="off"
            >
            <select class="st-form__priority" id="task-priority-select">
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3" selected>3</option>
                <option value="4">4</option>
                <option value="5">5</option>
            </select>
            <button type="submit" class="st-form__submit">添加</button>
        </form>
    `;

    const form = container.querySelector('#task-form-el');
    const titleInput = container.querySelector('#task-title-input');

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const title = titleInput.value.trim();
        if (!title) {
            titleInput.classList.add('st-form__input--error');
            titleInput.focus();
            return;
        }

        const priority = parseInt(container.querySelector('#task-priority-select').value, 10);

        // 派发事件到 DOM 树，由 app.js 在 #app 上捕获
        container.dispatchEvent(new CustomEvent('task-create', {
            detail: { title, priority },
            bubbles: true,
        }));

        // 清空表单
        titleInput.value = '';
        titleInput.classList.remove('st-form__input--error');
        titleInput.focus();
    });

    // 输入时清除错误状态
    titleInput.addEventListener('input', () => {
        titleInput.classList.remove('st-form__input--error');
    });
}
