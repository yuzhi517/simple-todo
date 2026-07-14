// ==========================================
// app.js — 应用控制器
// 工具栏：搜索（面板展开）+ 添加（弹窗创建）
// ==========================================

import * as api from './api.js';
import * as state from './state.js';
import { renderStatusBar } from './components/status-bar.js';
import { renderSearchBar, focusSearchInput } from './components/search-bar.js';
import { renderTaskList } from './components/task-list.js';

async function boot() {
    const health = await api.healthCheck();
    state.setConnectionOk(health.ok);

    await loadTasks();

    renderToolbar();
    renderSearchBar(document.getElementById('search-bar'));
    renderTaskList(document.getElementById('task-list'));

    _refreshStatusBar(state.getState());

    state.on('change', (s) => {
        _syncPanels(s);
        _syncToolbar(s);
        _refreshStatusBar(s);
    });

    _syncPanels(state.getState());
    _syncToolbar(state.getState());

    wireEvents();
    _wireCreateModal();
    _initNotifications();
}

// ── 截止日期通知 ──────────────────────────────────────

let _notifiedTasks = new Set();

function _initNotifications() {
    if (!('Notification' in window)) return;

    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }

    // 首次检查
    _checkDeadlines(state.getState().allTasks);

    // 每 5 分钟检查一次
    setInterval(() => {
        _checkDeadlines(state.getState().allTasks);
    }, 5 * 60 * 1000);

    // 任务更新后也检查
    state.on('change', (s) => {
        if (s.allTasks.length > 0) _checkDeadlines(s.allTasks);
    });
}

function _checkDeadlines(tasks) {
    if (Notification.permission !== 'granted') return;

    const now = Math.floor(Date.now() / 1000);
    const ONE_HOUR = 3600;
    const ONE_DAY = 86400;

    for (const task of tasks) {
        if (!task.deadline || task.done) continue;

        const remaining = task.deadline - now;
        if (remaining < 0 || remaining > ONE_DAY) continue;

        // 同一任务一天内不重复通知
        const key = `${task.id}-${Math.floor(remaining / ONE_HOUR)}h`;
        if (_notifiedTasks.has(key)) continue;
        _notifiedTasks.add(key);

        let urgency, body;
        if (remaining < ONE_HOUR) {
            urgency = '⚠️ 即将到期';
            body = `"${task.title}" 将在 ${Math.ceil(remaining / 60)} 分钟后截止`;
        } else {
            const hours = Math.ceil(remaining / ONE_HOUR);
            urgency = '⏰ 临近截止';
            body = `"${task.title}" 将在约 ${hours} 小时后截止`;
        }

        new Notification(`${urgency} — Simple Todo`, {
            body,
            icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🔔</text></svg>',
            tag: `todo-${task.id}`,
            requireInteraction: remaining < ONE_HOUR,
        });
    }
}

async function loadTasks() {
    state.setLoading(true);
    const result = await api.listTasks(true);
    if (result.ok) {
        state.setAllTasks(result.data);
        const showAll = state.getState().showAll;
        state.setTasks(showAll ? result.data : result.data.filter(t => !t.done));
        state.setConnectionOk(true);
        state.clearError();
    } else {
        state.setError(result.error);
        state.setConnectionOk(false);
    }
    state.setLoading(false);
}

// ── 工具栏 ────────────────────────────────────────────────

function renderToolbar() {
    const toolbar = document.getElementById('toolbar');
    if (!toolbar) return;

    toolbar.innerHTML = `
        <button class="st-toolbar__btn" data-action="toolbar-search">搜索</button>
        <button class="st-toolbar__btn" data-action="toolbar-add">添加</button>
        <button class="st-toolbar__btn" data-action="toolbar-manage">管理</button>
    `;

    toolbar.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'toolbar-search') {
            const wasOpen = state.getState().searchMode;
            state.setManageMode(false);          // 互斥：关闭管理
            state.setSearchMode(!wasOpen);       // 切换搜索
            if (!wasOpen) {
                focusSearchInput(document.getElementById('search-bar'));
            }
        } else if (action === 'toolbar-add') {
            state.setSearchMode(false);          // 互斥：关闭搜索
            state.setManageMode(false);          // 互斥：关闭管理
            _openCreateModal();
        } else if (action === 'toolbar-manage') {
            state.setSearchMode(false);          // 互斥：关闭搜索
            state.setManageMode(!state.getState().manageMode);
        }
    });
}

function _syncToolbar(s) {
    const searchBtn = document.querySelector('[data-action="toolbar-search"]');
    const manageBtn = document.querySelector('[data-action="toolbar-manage"]');
    if (searchBtn) {
        searchBtn.classList.toggle('st-toolbar__btn--active', s.searchMode);
    }
    if (manageBtn) {
        manageBtn.classList.toggle('st-toolbar__btn--active', s.manageMode);
    }
}

function _syncPanels(s) {
    const searchPanel = document.getElementById('search-panel');
    if (searchPanel) {
        searchPanel.classList.toggle('st-panel--collapsed', !s.searchMode);
        searchPanel.classList.toggle('st-panel--expanded', s.searchMode);
    }
}

function _refreshStatusBar(s) {
    const el = document.getElementById('status-bar');
    if (el) renderStatusBar(el, s);
}

// ── 创建任务弹窗 ──────────────────────────────────────────

function _openCreateModal() {
    document.getElementById('create-title').value = '';
    document.getElementById('create-longterm').checked = false;
    document.getElementById('create-focus').checked = false;
    document.getElementById('create-notes').value = '';

    // 默认截止日期：今天，时间：当前时间 + 1 分钟
    const due = new Date(Date.now() + 60000);
    _setSegDate('dl-year', 'dl-month', 'dl-day', due);
    _setSegTime('dl-hour', 'dl-min', due);
    _setSegEnabled(true);
    _muteSegs(true);

    const errEl = document.getElementById('create-deadline-error');
    if (errEl) errEl.style.display = 'none';

    document.getElementById('create-modal').classList.remove('st-modal--hidden');
    _lockScroll(true);
    setTimeout(() => document.getElementById('create-title').focus(), 100);
}

// ── 分段输入框辅助 ──────────────────────────────

function _setSegDate(yId, mId, dId, date) {
    document.getElementById(yId).value = date.getFullYear();
    document.getElementById(mId).value = String(date.getMonth() + 1).padStart(2, '0');
    document.getElementById(dId).value = String(date.getDate()).padStart(2, '0');
}

function _setSegTime(hId, mId, date) {
    document.getElementById(hId).value = String(date.getHours()).padStart(2, '0');
    document.getElementById(mId).value = String(date.getMinutes()).padStart(2, '0');
}

function _getSegDeadline() {
    const y = document.getElementById('dl-year').value;
    const mo = document.getElementById('dl-month').value;
    const d = document.getElementById('dl-day').value;
    const h = document.getElementById('dl-hour').value;
    const mi = document.getElementById('dl-min').value;
    if (!y || !mo || !d || !h || !mi) return null;
    const date = new Date(`${y}-${mo.padStart(2,'0')}-${d.padStart(2,'0')}T${h.padStart(2,'0')}:${mi.padStart(2,'0')}:00`);
    return isNaN(date.getTime()) ? null : date.getTime() / 1000;
}

function _setSegEnabled(enabled) {
    ['dl-year','dl-month','dl-day','dl-hour','dl-min'].forEach(id => {
        document.getElementById(id).disabled = !enabled;
    });
}

function _clearSegs() {
    ['dl-year','dl-month','dl-day','dl-hour','dl-min'].forEach(id => {
        document.getElementById(id).value = '';
    });
}

function _muteSegs(muted) {
    ['dl-year','dl-month','dl-day','dl-hour','dl-min'].forEach(id => {
        const el = document.getElementById(id);
        if (muted) el.classList.add('st-input--muted');
        else el.classList.remove('st-input--muted');
    });
}

function _closeCreateModal() {
    document.getElementById('create-modal').classList.add('st-modal--hidden');
    _lockScroll(false);
}

function _wireCreateModal() {
    const longtermCheck = document.getElementById('create-longterm');

    longtermCheck.addEventListener('change', () => {
        if (longtermCheck.checked) {
            _setSegEnabled(false);
            _clearSegs();
        } else {
            _setSegEnabled(true);
            const due = new Date(Date.now() + 60000);
            _setSegDate('dl-year', 'dl-month', 'dl-day', due);
            _setSegTime('dl-hour', 'dl-min', due);
            _muteSegs(true);
        }
    });

    // 用户修改分段输入框时取消灰色；聚焦时全选内容方便直接覆盖
    ['dl-year','dl-month','dl-day','dl-hour','dl-min'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => _muteSegs(false));
            el.addEventListener('focus', () => { el.dataset.prev = el.value; el.value = ''; });
            el.addEventListener('blur', () => { if (!el.value) el.value = el.dataset.prev || ''; });
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target.dataset.action === 'create-close') _closeCreateModal();
        if (e.target.dataset.action === 'create-submit') _submitCreate();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!document.getElementById('create-modal').classList.contains('st-modal--hidden')) {
                _closeCreateModal();
            } else if (!document.getElementById('notes-modal').classList.contains('st-modal--hidden')) {
                _closeNotesModal();
            } else if (!document.getElementById('delete-modal').classList.contains('st-modal--hidden')) {
                _closeDeleteModal();
            } else if (!document.getElementById('detail-modal').classList.contains('st-modal--hidden')) {
                _closeDetailModal();
            }
        }
    });
}

async function _submitCreate() {
    const title = document.getElementById('create-title').value.trim();
    if (!title) {
        document.getElementById('create-title').classList.add('st-form__input--error');
        document.getElementById('create-title').focus();
        return;
    }

    let deadline = null;
    if (!document.getElementById('create-longterm').checked) {
        const dl = _getSegDeadline();
        if (dl === null) {
            document.getElementById('dl-year').focus();
            return;
        }
        // 截止时间必须比当前时间晚至少 1 分钟
        if (dl <= Date.now() / 1000 + 60) {
            document.getElementById('dl-hour').classList.add('st-form__input--error');
            document.getElementById('dl-min').classList.add('st-form__input--error');
            document.getElementById('dl-hour').focus();
            const errEl = document.getElementById('create-deadline-error');
            if (errEl) { errEl.textContent = '请选择当前时间之后的时间'; errEl.style.display = ''; }
            return;
        }
        deadline = dl;
    }

    const focus = document.getElementById('create-focus').checked;
    const notes = document.getElementById('create-notes').value.trim() || null;

    state.setLoading(true);
    const result = await api.createTask(title, 1, deadline, focus, notes);
    if (result.ok) {
        state.updateTask(result.data);
        state.clearError();
        _closeCreateModal();
    } else {
        state.setError(result.error);
    }
    state.setLoading(false);
}

// ── 事件连线 ──────────────────────────────────────────────

function wireEvents() {
    const app = document.getElementById('app');

    app.addEventListener('task-done', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const result = await api.markDone(id);
        if (result.ok) { await loadTasks(); state.clearError(); }
        else { state.setError(result.error); }
        state.setLoading(false);
    });

    app.addEventListener('task-undone', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const result = await api.markUndone(id);
        if (result.ok) { await loadTasks(); state.clearError(); }
        else { state.setError(result.error); }
        state.setLoading(false);
    });

    app.addEventListener('task-delete', (e) => {
        const { id } = e.detail;
        const task = state.getState().allTasks.find(t => t.id === id);
        if (task) _openDeleteModal(id, task.title);
    });

    app.addEventListener('focus-toggle', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const task = state.getState().allTasks.find(t => t.id === id);
        const newFocus = task ? !task.focus : true;
        const result = await api.updateFocus(id, newFocus);
        if (result.ok) {
            await loadTasks();  // 重新加载以应用排序
            state.clearError();
        }
        else { state.setError(result.error); }
        state.setLoading(false);
    });

    app.addEventListener('search-submit', async (e) => {
        const { query } = e.detail;
        if (!query.trim()) return;
        state.setLoading(true);
        const result = await api.searchTasks(query.trim());
        if (result.ok) { state.setSearch(query.trim(), result.data); state.clearError(); }
        else { state.setError(result.error); }
        state.setLoading(false);
    });

    app.addEventListener('search-clear', async () => {
        state.clearSearch();
        await loadTasks();
    });

    app.addEventListener('search-close', () => {
        state.setSearchMode(false);
    });

    app.addEventListener('view-toggle', (e) => {
        const { showAll } = e.detail;
        const all = state.getState().allTasks;
        state.setShowAll(showAll);
        state.setTasks(showAll ? all : all.filter(t => !t.done));
    });

    app.addEventListener('dismiss-error', () => {
        state.clearError();
    });

    // 编辑备注
    app.addEventListener('task-edit', (e) => {
        const { id } = e.detail;
        const task = state.getState().allTasks.find(t => t.id === id);
        if (task) _openNotesModal(id, task.title, task.notes || '');
    });

    app.addEventListener('task-view', (e) => {
        const { id } = e.detail;
        const task = state.getState().allTasks.find(t => t.id === id);
        if (task) _openDetailModal(task);
    });

    document.addEventListener('click', (e) => {
        if (e.target.dataset.action === 'notes-close') _closeNotesModal();
        if (e.target.dataset.action === 'notes-save') _saveNotes();
        if (e.target.dataset.action === 'delete-cancel') _closeDeleteModal();
        if (e.target.dataset.action === 'delete-confirm') _confirmDelete();
        if (e.target.dataset.action === 'detail-close') _closeDetailModal();
    });
}

// ── 备注弹窗 ──────────────────────────────────────────────

let _editingTaskId = null;

function _openNotesModal(id, title, notes) {
    _editingTaskId = id;
    document.getElementById('notes-modal-title').textContent = `编辑备注 — ${title}`;
    document.getElementById('notes-textarea').value = notes;
    document.getElementById('notes-modal').classList.remove('st-modal--hidden');
    _lockScroll(true);
    setTimeout(() => document.getElementById('notes-textarea').focus(), 100);
}

function _closeNotesModal() {
    _editingTaskId = null;
    document.getElementById('notes-modal').classList.add('st-modal--hidden');
    _lockScroll(false);
}

// ── 滚轮锁定 ──────────────────────────────────────────────

let _scrollLockCount = 0;

function _lockScroll(lock) {
    _scrollLockCount += lock ? 1 : -1;
    if (_scrollLockCount < 0) _scrollLockCount = 0;
    document.body.style.overflow = _scrollLockCount > 0 ? 'hidden' : '';
}

async function _saveNotes() {
    if (_editingTaskId === null) return;
    const notes = document.getElementById('notes-textarea').value.trim() || null;
    state.setLoading(true);
    const result = await api.updateNotes(_editingTaskId, notes === '' ? null : notes);
    if (result.ok) { state.updateTask(result.data); state.clearError(); }
    else { state.setError(result.error); }
    state.setLoading(false);
    _closeNotesModal();
}

// ── 任务详情弹窗 ──────────────────────────────────────────

function _openDetailModal(task) {
    document.getElementById('detail-title').textContent = task.title;

    let meta = '';
    if (task.deadline) {
        const d = new Date(task.deadline * 1000);
        const pad = (n) => String(n).padStart(2, '0');
        meta += `截止日期：${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
    } else {
        meta += '截止日期：长期';
    }
    if (task.focus) meta += ' · ◆ 聚焦';
    if (task.done) meta += ' · 已完成';
    document.getElementById('detail-meta').textContent = meta;

    document.getElementById('detail-notes').textContent = task.notes || '暂无详细内容';

    document.getElementById('detail-modal').classList.remove('st-modal--hidden');
    _lockScroll(true);
}

function _closeDetailModal() {
    document.getElementById('detail-modal').classList.add('st-modal--hidden');
    _lockScroll(false);
}

// ── 删除确认弹窗 ──────────────────────────────────────────

let _deleteTaskId = null;

function _openDeleteModal(id, title) {
    _deleteTaskId = id;
    document.getElementById('delete-task-title').textContent = ' ' + title;
    document.getElementById('delete-modal').classList.remove('st-modal--hidden');
    _lockScroll(true);
}

function _closeDeleteModal() {
    _deleteTaskId = null;
    document.getElementById('delete-modal').classList.add('st-modal--hidden');
    _lockScroll(false);
}

async function _confirmDelete() {
    if (_deleteTaskId === null) return;
    const id = _deleteTaskId;
    _closeDeleteModal();
    state.setLoading(true);
    const result = await api.deleteTask(id);
    if (result.ok) { state.removeTask(id); state.clearError(); }
    else { state.setError(result.error); }
    state.setLoading(false);
}

boot();
