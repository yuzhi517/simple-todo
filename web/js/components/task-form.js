// ==========================================
// task-form.js — 添加任务表单组件
// 不订阅 state，不调 api
// 派发事件: task-create (detail: { title, deadline, focus, notes })
// ==========================================

/**
 * 渲染添加任务表单
 * @param {HTMLElement} container
 */
export function renderTaskForm(container) {
    if (!container) return;

    container.innerHTML = `
        <form class="st-form" id="task-form-el">
            <div class="st-form__row">
                <input
                    type="text"
                    class="st-form__input"
                    id="task-title-input"
                    placeholder="输入新任务标题..."
                    maxlength="500"
                    autocomplete="off"
                >
                <input
                    type="date"
                    class="st-form__input"
                    id="task-deadline-input"
                    style="max-width: 150px;"
                >
                <label class="st-form__check">
                    <input type="checkbox" id="task-longterm-check">
                    长期
                </label>
                <label class="st-form__check" style="position: relative;">
                    <input type="checkbox" id="task-focus-check">
                    聚焦
                    <span class="st-form__hint" title="重要及需要优先完成的任务勾选">?</span>
                </label>
                <button type="submit" class="st-form__submit">添加</button>
            </div>
            <textarea
                class="st-form__textarea"
                id="task-notes-input"
                placeholder="详细备注（可选）..."
                rows="2"
                maxlength="2000"
            ></textarea>
        </form>
    `;

    const form = container.querySelector('#task-form-el');
    const titleInput = container.querySelector('#task-title-input');
    const deadlineInput = container.querySelector('#task-deadline-input');
    const longtermCheck = container.querySelector('#task-longterm-check');
    const focusCheck = container.querySelector('#task-focus-check');
    const notesInput = container.querySelector('#task-notes-input');

    // "长期"勾选时禁用日期选择器
    longtermCheck.addEventListener('change', () => {
        deadlineInput.disabled = longtermCheck.checked;
        if (longtermCheck.checked) {
            deadlineInput.value = '';
        }
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const title = titleInput.value.trim();
        if (!title) {
            titleInput.classList.add('st-form__input--error');
            titleInput.focus();
            return;
        }

        // 解析截止日期：长期 → null，否则取日期 23:59:59 的时间戳
        let deadline = null;
        if (!longtermCheck.checked && deadlineInput.value) {
            const d = new Date(deadlineInput.value + 'T23:59:59');
            deadline = d.getTime() / 1000;
        }

        const focus = focusCheck.checked;
        const notes = notesInput.value.trim() || null;

        container.dispatchEvent(new CustomEvent('task-create', {
            detail: { title, deadline, focus, notes },
            bubbles: true,
        }));

        // 清空表单
        titleInput.value = '';
        titleInput.classList.remove('st-form__input--error');
        deadlineInput.value = '';
        deadlineInput.disabled = false;
        longtermCheck.checked = false;
        focusCheck.checked = false;
        notesInput.value = '';
        titleInput.focus();
    });

    titleInput.addEventListener('input', () => {
        titleInput.classList.remove('st-form__input--error');
    });
}
