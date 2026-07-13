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
    document.getElementById('create-deadline').value = '';
    document.getElementById('create-deadline').disabled = false;
    document.getElementById('create-longterm').checked = false;
    document.getElementById('create-focus').checked = false;
    document.getElementById('create-notes').value = '';
    document.getElementById('create-modal').classList.remove('st-modal--hidden');
    _lockScroll(true);
    setTimeout(() => document.getElementById('create-title').focus(), 100);
}

function _closeCreateModal() {
    document.getElementById('create-modal').classList.add('st-modal--hidden');
    _lockScroll(false);
}

function _wireCreateModal() {
    const longtermCheck = document.getElementById('create-longterm');
    const deadlineInput = document.getElementById('create-deadline');

    longtermCheck.addEventListener('change', () => {
        deadlineInput.disabled = longtermCheck.checked;
        if (longtermCheck.checked) deadlineInput.value = '';
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
    if (!document.getElementById('create-longterm').checked && document.getElementById('create-deadline').value) {
        const d = new Date(document.getElementById('create-deadline').value + 'T23:59:59');
        deadline = d.getTime() / 1000;
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
        if (result.ok) { state.updateTask(result.data); state.clearError(); }
        else { state.setError(result.error); }
        state.setLoading(false);
    });

    app.addEventListener('task-undone', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const result = await api.markUndone(id);
        if (result.ok) { state.updateTask(result.data); state.clearError(); }
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
        if (result.ok) { state.updateTask(result.data); state.clearError(); }
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
