// ==========================================
// api.js — HTTP 客户端层
// 镜像 client/api.py，封装所有后端 API 通信
// 统一返回 { ok: true, data } 或 { ok: false, error }
// ==========================================

const BASE_URL = window.TODO_API_URL || 'http://127.0.0.1:8000';

/**
 * 内部请求函数
 * @param {string} method - HTTP 方法
 * @param {string} path - URL 路径 (如 '/tasks')
 * @param {object|null} body - 请求体 JSON
 * @returns {Promise<{ok: boolean, data?: any, error?: string}>}
 */
async function _request(method, path, body = null) {
    const url = `${BASE_URL}${path}`;
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                if (errData.detail) {
                    errorMsg = errData.detail;
                }
            } catch (_) {
                // 响应体不是 JSON，使用默认错误消息
            }
            return { ok: false, error: errorMsg };
        }

        // 204 No Content 或空响应体
        const text = await response.text();
        if (!text) {
            return { ok: true, data: null };
        }

        return { ok: true, data: JSON.parse(text) };
    } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            return { ok: false, error: '无法连接到后端服务，请确认服务已启动' };
        }
        return { ok: false, error: `网络错误: ${err.message}` };
    }
}

// ==========================================
// 公开 API
// ==========================================

/** GET /health — 健康检查 */
export async function healthCheck() {
    return _request('GET', '/health');
}

/** GET /tasks — 获取任务列表 */
export async function listTasks(showAll = false) {
    const path = showAll ? '/tasks?all=true' : '/tasks';
    return _request('GET', path);
}

/** GET /tasks/search?q=... — 搜索任务 */
export async function searchTasks(query) {
    const path = `/tasks/search?q=${encodeURIComponent(query)}`;
    return _request('GET', path);
}

/** GET /tasks/{id} — 获取单个任务 */
export async function getTask(id) {
    return _request('GET', `/tasks/${id}`);
}

/** POST /tasks — 创建任务 */
export async function createTask(title, priority = 1) {
    return _request('POST', '/tasks', { title, priority });
}

/** PUT /tasks/{id}/done — 标记完成 */
export async function markDone(id) {
    return _request('PUT', `/tasks/${id}/done`);
}

/** PUT /tasks/{id}/undone — 恢复未完成 */
export async function markUndone(id) {
    return _request('PUT', `/tasks/${id}/undone`);
}

/** DELETE /tasks/{id} — 删除任务 */
export async function deleteTask(id) {
    return _request('DELETE', `/tasks/${id}`);
}

/** PUT /tasks/{id}/priority — 更新优先级 */
export async function updatePriority(id, priority) {
    return _request('PUT', `/tasks/${id}/priority`, { priority });
}
