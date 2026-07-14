# Simple Todo

> 优雅的待办事项管理工具 · 全平台通用 · 双击即用

**Simple Todo** 是一个轻量、美观、功能完备的待办事项管理器。它拥有 macOS / iOS 风格的液体玻璃界面、精确到分钟的截止日期提醒、跨平台系统原生通知，以及一键启动的零配置体验。

---

## 亮点

### 🫧 液体玻璃 UI
macOS / iOS 风格的 Liquid Glass 主题——毛玻璃卡片、天空渐变背景、柔和光斑，每个任务卡片都有通透的层次感。

### ⏰ 多级截止日期提醒
支持精确到分钟的截止日期。在 **7天 / 3天 / 1天 / 12小时 / 1小时 / 5分钟** 六个时间节点自动提醒，浏览器开着弹 Web 通知，关着也能收到系统原生通知（macOS 横幅 / Windows Toast）。

### 🔍 聚焦自动置顶
点击卡片上的 `◆` 即可标记聚焦。聚焦任务自动排到列表最上面，截止日期越近越靠前，重要事项一目了然。

### 💻 双前端 + API
一套后端同时驱动 **Web 前端**（液体玻璃 UI）和 **CLI 命令行**（纯标准库），REST API 可直接用 curl 调用。适合任何工作流。

### 🪶 零依赖 · 零配置
前端纯原生 JS/CSS，CLI 只用 Python 标准库。`python3 run.py` 一行命令启动全部服务，Windows / macOS / Linux 通用。

---

## 快速开始

```bash
pip install -r server/requirements.txt   # 仅需一次
python3 run.py                           # 一键启动
```

浏览器自动打开 `http://127.0.0.1:3000`，开始使用。`Ctrl+C` 关闭所有服务。

---

## 功能

### Web 界面
| 操作 | 方式 |
|---|---|
| **添加任务** | 点击「添加」→ 填写标题，日期时间自动默认（可修改） |
| **完成 / 恢复** | 卡片上的 ✓ 完成 / ↩ 恢复 按钮 |
| **聚焦置顶** | 点击卡片左侧 `◇` → `◆`，任务瞬间排到最顶 |
| **编辑备注** | 管理模式下的「编辑」按钮 |
| **搜索** | 工具栏「搜索」→ 实时防抖搜索 |
| **视图切换** | 未完成 / 全部 胶囊切换 |
| **删除** | 管理模式下的「删除」按钮，有确认弹窗 |

### 截止日期与通知
- 日期和时间采用**分段数字输入框**，点击即清空直接输入
- 默认截止日期为 **今天 + 1 分钟**，永远有效
- 勾选「长期」则不限期
- 后台通知服务每 5 分钟检查一次，到期前自动推送系统通知

### CLI 命令行

```bash
python3 -m client.cli add "完成报告"           # 添加
python3 -m client.cli                           # 查看未完成
python3 -m client.cli all                       # 查看全部
python3 -m client.cli done 1                    # 标记完成
python3 -m client.cli search 报告               # 搜索
python3 -m client.cli menu                      # 交互菜单
```

### REST API

```bash
curl http://127.0.0.1:8000/tasks
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"买菜","deadline":1710000000,"focus":true,"notes":"青菜、豆腐"}'
```

| Method | Path | 说明 |
|--------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/tasks` | 任务列表 `?all=true` 含已完成 |
| `POST` | `/tasks` | 创建任务 |
| `GET` | `/tasks/search?q=` | 搜索任务 |
| `GET` | `/tasks/{id}` | 获取任务详情 |
| `PUT` | `/tasks/{id}/done` | 标记完成 |
| `PUT` | `/tasks/{id}/undone` | 恢复未完成 |
| `DELETE` | `/tasks/{id}` | 删除任务 |
| `PUT` | `/tasks/{id}/priority` | 修改优先级 |
| `PUT` | `/tasks/{id}/focus` | 切换聚焦 |
| `PUT` | `/tasks/{id}/deadline` | 更新截止日期 |
| `PUT` | `/tasks/{id}/notes` | 更新备注 |

---

## 架构

```
simple-todo/
├── run.py                         # 统一启动入口（推荐双击运行）
├── server/
│   ├── main.py                    # FastAPI 后端（13 个端点）
│   ├── models.py                  # Pydantic 数据模型
│   ├── storage.py                 # SQLite + WAL 持久化
│   └── notifier.py                # 跨平台系统通知服务
├── client/
│   ├── cli.py                     # CLI 命令分发
│   ├── api.py                     # urllib API 封装（纯标准库）
│   ├── display.py                 # 终端渲染（CJK 对齐）
│   └── menu.py                    # 交互式菜单
├── web/
│   ├── index.html                 # 入口页面
│   ├── css/style.css              # Liquid Glass 主题
│   └── js/
│       ├── app.js                 # 应用控制器 + 通知逻辑
│       ├── api.js                 # fetch API 封装
│       ├── state.js               # 集中状态管理（发布/订阅）
│       └── components/
│           ├── task-item.js       # 任务卡片渲染
│           ├── task-list.js       # 任务列表 + 视图切换
│           ├── search-bar.js      # 搜索栏
│           └── status-bar.js      # 状态栏
├── simple-todo/todo.py            # v1 单文件版（保留）
└── server/requirements.txt
```

### 启动后的进程

```
run.py
├── uvicorn (API)         :8000
├── http.server (Web)     :3000
└── notifier.py (通知)     后台静默
```

---

## 数据存储

SQLite 数据库位于 `~/.simple_todo/tasks.db`，WAL 模式，v1 JSON 自动迁移。

排序规则：**聚焦优先 → 截止日期近的优先 → 创建时间早的优先**。

---

## 设计原则

1. **零依赖** — CLI 纯标准库，Web 原生 JS/CSS，不引入任何框架
2. **一键启动** — `run.py` 双击即用，无需配置
3. **跨平台** — Windows / macOS / Linux 均可用，系统通知各自原生
4. **API 优先** — 所有功能通过 REST API 暴露，便于扩展
5. **中文优先** — 全中文界面，终端宽度自适应中文对齐

---

## 许可证

MIT License
