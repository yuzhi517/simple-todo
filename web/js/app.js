// ==========================================
// app.js — 应用控制器
// 初始化组件，加载初始数据，连线所有事件
// ==========================================

import * as api from './api.js';
import * as state from './state.js';
import { renderStatusBar } from './components/status-bar.js';
import { renderTaskForm } from './components/task-form.js';
import { renderSearchBar } from './components/search-bar.js';
import { renderTaskList } from './components/task-list.js';

/**
 * 启动应用：健康检查 → 加载初始数据 → 渲染所有组件
 */
async function boot() {
    // 1. 健康检查
    const health = await api.healthCheck();
    state.setConnectionOk(health.ok);

    // 2. 加载初始任务列表
    await loadTasks();

    // 3. 渲染所有组件
    renderStatusBar(document.getElementById('status-bar'));
    renderSearchBar(document.getElementById('search-bar'));
    renderTaskForm(document.getElementById('task-form'));
    renderTaskList(document.getElementById('task-list'));

    // 4. 连线事件处理器
    wireEvents();
}

/**
 * 加载任务列表
 */
async function loadTasks() {
    state.setLoading(true);
    const result = await api.listTasks(true); // 始终拉全量以更新缓存
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

/**
 * 连线所有组件事件
 */
function wireEvents() {
    const app = document.getElementById('app');

    app.addEventListener('task-create', async (e) => {
        const { title, priority } = e.detail;
        state.setLoading(true);
        const result = await api.createTask(title, priority);
        if (result.ok) {
            state.updateTask(result.data);
            state.clearError();
        } else {
            state.setError(result.error);
        }
        state.setLoading(false);
    });

    app.addEventListener('task-done', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const result = await api.markDone(id);
        if (result.ok) {
            state.updateTask(result.data);
            state.clearError();
        } else {
            state.setError(result.error);
        }
        state.setLoading(false);
    });

    app.addEventListener('task-undone', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const result = await api.markUndone(id);
        if (result.ok) {
            state.updateTask(result.data);
            state.clearError();
        } else {
            state.setError(result.error);
        }
        state.setLoading(false);
    });

    app.addEventListener('task-delete', async (e) => {
        const { id } = e.detail;
        state.setLoading(true);
        const result = await api.deleteTask(id);
        if (result.ok) {
            state.removeTask(id);
            state.clearError();
        } else {
            state.setError(result.error);
        }
        state.setLoading(false);
    });

    app.addEventListener('task-priority-change', async (e) => {
        const { id, priority } = e.detail;
        state.setLoading(true);
        const result = await api.updatePriority(id, priority);
        if (result.ok) {
            state.updateTask(result.data);
            state.clearError();
        } else {
            state.setError(result.error);
        }
        state.setLoading(false);
    });

    app.addEventListener('search-submit', async (e) => {
        const { query } = e.detail;
        if (!query.trim()) return;
        state.setLoading(true);
        const result = await api.searchTasks(query.trim());
        if (result.ok) {
            state.setSearch(query.trim(), result.data);
            state.clearError();
        } else {
            state.setError(result.error);
        }
        state.setLoading(false);
    });

    app.addEventListener('search-clear', async () => {
        state.clearSearch();
        await loadTasks();
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
}

// 启动
boot();
