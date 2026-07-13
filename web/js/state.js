// ==========================================
// state.js — 集中状态管理 + 发布订阅
// 唯一的数据源，只有 app.js 可以调用 mutation 方法
// 组件通过 on('change', fn) 订阅状态变化
// ==========================================

const _listeners = new Set();

const _state = {
    tasks: [],           // 当前可见任务列表
    allTasks: [],        // 全量缓存（用于 showAll 视图切换）
    showAll: false,      // 是否显示全部（含已完成）
    loading: false,      // 是否有请求进行中
    error: null,         // { message: string } | null
    searchActive: false, // 是否处于搜索模式
    searchQuery: '',     // 当前搜索关键词
    connectionOk: true,  // 后端是否可达
};

/**
 * 获取当前状态的只读快照
 * @returns {Readonly<typeof _state>}
 */
export function getState() {
    return _state;
}

/**
 * 订阅状态变化
 * @param {'change'} event
 * @param {(state: Readonly<typeof _state>) => void} callback
 */
export function on(event, callback) {
    if (event === 'change') {
        _listeners.add(callback);
    }
}

/**
 * 取消订阅
 * @param {'change'} event
 * @param {(state: Readonly<typeof _state>) => void} callback
 */
export function off(event, callback) {
    if (event === 'change') {
        _listeners.delete(callback);
    }
}

/**
 * 通知所有订阅者（内部使用，仅 app.js 调用链触发）
 */
function _emit() {
    const snapshot = { ..._state };
    for (const fn of _listeners) {
        try {
            fn(snapshot);
        } catch (err) {
            console.error('[state] 订阅回调出错:', err);
        }
    }
}

// ==========================================
// Mutation 方法（仅 app.js 调用）
// ==========================================

/** 设置任务列表 */
export function setTasks(tasks) {
    _state.tasks = tasks;
    _emit();
}

/** 设置全量缓存（用于视图切换和变更后同步） */
export function setAllTasks(allTasks) {
    _state.allTasks = allTasks;
    _emit();
}

/** 更新单条任务（同步更新 tasks 和 allTasks） */
export function updateTask(task) {
    const replace = (list) => {
        const idx = list.findIndex(t => t.id === task.id);
        if (idx !== -1) list[idx] = task;
        else list.push(task);
    };
    replace(_state.tasks);
    replace(_state.allTasks);
    _emit();
}

/** 从列表中移除任务 */
export function removeTask(id) {
    const filterFn = (t) => t.id !== id;
    _state.tasks = _state.tasks.filter(filterFn);
    _state.allTasks = _state.allTasks.filter(filterFn);
    _emit();
}

/** 切换显示模式 */
export function setShowAll(showAll) {
    _state.showAll = showAll;
    // 不触发额外 HTTP 请求：app.js 监听此变化后从 allTasks 过滤
    _emit();
}

/** 设置加载状态 */
export function setLoading(loading) {
    _state.loading = loading;
    _emit();
}

/** 设置错误消息 */
export function setError(message) {
    _state.error = { message };
    _emit();
}

/** 清除错误 */
export function clearError() {
    _state.error = null;
    _emit();
}

/** 设置连接状态 */
export function setConnectionOk(ok) {
    _state.connectionOk = ok;
    _emit();
}

/** 设置搜索状态 */
export function setSearch(query, results) {
    _state.searchActive = true;
    _state.searchQuery = query;
    _state.tasks = results;
    _emit();
}

/** 清除搜索状态 */
export function clearSearch() {
    _state.searchActive = false;
    _state.searchQuery = '';
    _emit();
}
