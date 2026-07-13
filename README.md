# Simple Todo

> 待办事项管理工具 | 全平台通用 | CLI + Web 双前端 | 双击就能用

## 版本说明

| 版本 | 目录 | 简介 |
|------|------|------|
| **v2**（当前） | `server/` + `client/` + `web/` | 前后端分离，FastAPI + SQLite + CLI + Web |
| **v1**（保留） | `simple-todo/todo.py` | 单文件实现，首次启动自动迁移到 v2 |

## 架构概览

```
simple-todo/
├── server/                     # 后端 API (FastAPI)
│   ├── main.py                # API 入口，13 个端点
│   ├── models.py              # Pydantic 数据模型
│   ├── storage.py             # SQLite 持久化 (WAL 模式)
│   └── requirements.txt       # 后端依赖
├── client/                     # CLI 客户端 (纯标准库)
│   ├── cli.py                 # 命令分发
│   ├── api.py                 # urllib API 封装
│   ├── display.py             # 终端渲染 (中文对齐)
│   └── menu.py                # 交互式菜单
├── web/                        # Web 前端 (原生 JS，零依赖)
│   ├── index.html             # 入口页面
│   ├── css/style.css          # 样式系统
│   └── js/
│       ├── api.js             # fetch API 封装
│       ├── state.js           # 集中状态 + 发布订阅
│       ├── app.js             # 应用控制器
│       └── components/        # UI 组件
│           ├── task-list.js   # 任务列表 + 视图切换
│           ├── task-item.js   # 单条任务行
│           ├── search-bar.js  # 搜索栏
│           └── status-bar.js  # 状态栏
├── run.py                      # 统一启动入口 (推荐)
├── start_web.sh                # bash 启动脚本
├── simple-todo/                # v1 单体版 (保留)
├── LICENSE
└── README.md
```

## 功能概览

- **增删改查** — 添加 / 删除 / 完成 / 恢复任务
- **截止日期** — 设定截止日期，支持"长期"选项，过期任务红色提醒
- **聚焦标记** — 标记重要任务，聚焦任务自动置顶
- **任务备注** — 每条任务可添加详细备注内容
- **多级界面** — 默认简洁模式，按需展开搜索 / 管理模式
- **搜索功能** — 防抖实时搜索
- **中文优先** — 全中文界面
- **REST API** — 13 个端点，curl / Postman 直接调用
- **零依赖** — CLI 只靠 Python 标准库，Web 只用原生 JS / CSS
- **SQLite 存储** — WAL 模式，自动从 v1 JSON 迁移

## 快速开始

### 环境要求

- Python 3.8+
- macOS / Windows / Linux

### 安装

```bash
pip install -r server/requirements.txt
```

### 启动（推荐）

```bash
python3 run.py
```

双击 `run.py` 也行。自动启动后端 + Web 前端并打开浏览器。

### Web 前端

打开 `http://127.0.0.1:3000`

| 按钮 | 功能 |
|------|------|
| **搜索** | 展开搜索栏，输入关键词实时搜索 |
| **添加** | 弹出新建窗口，填写标题 / 日期 / 详细内容 |
| **管理** | 显示聚焦 / 编辑 / 删除按钮 |

点击任务标题可查看详情，删除未完成任务会弹出确认框。

### CLI 命令行

```bash
python3 -m client.cli add "完成中期报告" -p 1
python3 -m client.cli                    # 查看未完成
python3 -m client.cli all                # 查看全部
python3 -m client.cli done 1             # 标记完成
python3 -m client.cli search 报告        # 搜索
python3 -m client.cli menu               # 交互菜单
```

### 直接调用 API

```bash
curl http://127.0.0.1:8000/health
curl -X POST -H 'Content-Type: application/json' \
  -d '{"title":"买菜","focus":true,"notes":"需要买青菜、豆腐"}' \
  http://127.0.0.1:8000/tasks
curl http://127.0.0.1:8000/tasks
curl "http://127.0.0.1:8000/tasks/search?q=报告"
```

## API 参考

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/tasks` | 任务列表 `?all=true` 含已完成 |
| POST | `/tasks` | 添加任务 |
| GET | `/tasks/search?q=` | 搜索任务 |
| GET | `/tasks/{id}` | 获取单个任务 |
| PUT | `/tasks/{id}/done` | 标记完成 |
| PUT | `/tasks/{id}/undone` | 恢复未完成 |
| DELETE | `/tasks/{id}` | 删除任务 |
| PUT | `/tasks/{id}/priority` | 修改优先级 (CLI) |
| PUT | `/tasks/{id}/focus` | 切换聚焦 |
| PUT | `/tasks/{id}/deadline` | 更新截止日期 |
| PUT | `/tasks/{id}/notes` | 更新备注 |

## 数据存储

数据库文件：`~/.simple_todo/tasks.db`

```sql
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    priority    INTEGER NOT NULL DEFAULT 1,
    deadline    REAL,
    focus       INTEGER NOT NULL DEFAULT 0,
    notes       TEXT,
    done        INTEGER NOT NULL DEFAULT 0,
    created_at  REAL NOT NULL,
    done_at     REAL
);
```

数据按 **聚焦 → 截止日期 → 创建时间** 排序。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TODO_API_URL` | 后端 API 地址 | `http://127.0.0.1:8000` |

## 设计原则

1. **前后端分离** — 一个后端，CLI + Web 双前端
2. **零依赖客户端** — CLI 用 Python 标准库，Web 用原生 JS/CSS
3. **双击就能用** — `run.py` 一键启动，全平台通用
4. **中文优先** — 全中文 UI + 终端对齐
5. **API 优先** — 所有功能通过 REST API 暴露

## 许可证

MIT License
