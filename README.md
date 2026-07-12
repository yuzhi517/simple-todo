# Simple Todo

> 命令行待办事项管理工具 | 完整支持中文 | 前后端分离 | 双击就能用

## 版本说明

| 版本 | 目录 | 简介 |
|------|------|------|
| **v2**（当前） | `server/` + `client/` | 前后端分离架构，FastAPI REST API + SQLite 存储 + 零依赖 CLI |
| **v1**（保留） | `simple-todo/todo.py` | 单文件实现，纯标准库 + JSON 存储，首次启动可自动迁移到 v2 |

## 架构概览

```
simple-todo/
├── server/                    # 后端 API 服务 (FastAPI)
│   ├── main.py               # API 入口，定义所有端点
│   ├── models.py             # 数据模型 (Pydantic)
│   ├── storage.py            # 持久化层 (SQLite + WAL 模式)
│   └── requirements.txt      # 后端依赖
├── client/                    # CLI 客户端 (纯标准库，零依赖)
│   ├── cli.py                # 命令行入口
│   ├── api.py                # API 调用封装 (urllib)
│   ├── display.py            # 终端渲染 (中文对齐)
│   └── menu.py               # 交互式菜单
├── simple-todo/               # v1 单体版 (保留)
│   └── todo.py               # 单文件实现
├── todo.command               # macOS 双击启动
├── todo.bat                   # Windows 双击启动
├── LICENSE
└── README.md
```

## 功能概览

- ✅ **增删改查** — 添加 / 删除 / 完成 / 恢复任务
- ✅ **中文支持** — 标题支持中文，终端对齐不偏移
- ✅ **优先级管理** — 1-5 级，数字越小越重要
- ✅ **搜索功能** — 大小写不敏感的关键词搜索
- ✅ **REST API** — 后端提供标准 HTTP 接口，可用 curl/Postman 调用
- ✅ **前后端分离** — CLI 和 API 服务可独立运行、独立部署
- ✅ **零依赖客户端** — 只靠 Python 标准库，复制就能用
- ✅ **SQLite 存储** — 数据库文件存储，WAL 模式支持并发，首次启动自动从 v1 JSON 迁移

## 快速开始

### 环境要求

- Python 3.8+
- macOS、Linux 或 Windows

### 安装后端依赖

```bash
cd server
pip install -r requirements.txt
```

### 使用方法一：双击运行（推荐）

直接双击启动脚本：
- **macOS** → 双击 [todo.command](todo.command)
- **Windows** → 双击 [todo.bat](todo.bat)

### 使用方法二：手动启动

```bash
# 终端 1：启动后端服务
cd server
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 终端 2：使用 CLI
python -m client.cli add "完成中期报告" -p 1
python -m client.cli
python -m client.cli done 1
python -m client.cli search 报告
python -m client.cli menu
```

### 使用方法三：直接调用 API

```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 添加任务
curl -X POST -H 'Content-Type: application/json' \
  -d '{"title":"买菜","priority":1}' \
  http://127.0.0.1:8000/tasks

# 查看全部
curl http://127.0.0.1:8000/tasks?all=true

# 搜索
curl http://127.0.0.1:8000/tasks/search?q=报告
```

## API 参考

| Method | Path | 说明 |
|--------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/tasks` | 任务列表 `?all=true` 含已完成 |
| POST | `/tasks` | 添加任务 |
| GET | `/tasks/{id}` | 获取单个任务 |
| PUT | `/tasks/{id}/done` | 标记完成 |
| PUT | `/tasks/{id}/undone` | 恢复未完成 |
| DELETE | `/tasks/{id}` | 删除任务 |
| PUT | `/tasks/{id}/priority` | 修改优先级 |
| GET | `/tasks/search?q=关键词` | 搜索任务 |

## CLI 命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `add <标题>` | 添加任务 | `python -m client.cli add "买菜" -p 1` |
| `list` | 列出未完成任务 | `python -m client.cli` |
| `all` | 列出所有任务 | `python -m client.cli all` |
| `done <ID>` | 标记完成 | `python -m client.cli done 1` |
| `undone <ID>` | 恢复未完成 | `python -m client.cli undone 1` |
| `rm <ID>` | 删除 | `python -m client.cli rm 1` |
| `search <关键词>` | 搜索 | `python -m client.cli search 报告` |
| `priority <ID> <数字>` | 修改优先级 | `python -m client.cli priority 1 3` |
| `menu` | 交互菜单 | `python -m client.cli menu` |
| `help` | 帮助信息 | `python -m client.cli help` |

## 数据存储

所有数据存放于 `~/.simple_todo/tasks.db`（SQLite 数据库）。

首次启动时，如果检测到旧版 `~/.simple_todo/tasks.json`，会自动迁移数据到 SQLite 并将 JSON 文件备份为 `.migrated`。

### 查看数据

```bash
# 用 sqlite3 命令行查看
sqlite3 ~/.simple_todo/tasks.db "SELECT * FROM tasks"

# 或用任意 SQLite 客户端打开
open ~/.simple_todo/tasks.db
```

### 数据表结构

```sql
CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    priority    INTEGER NOT NULL DEFAULT 1 CHECK(priority >= 1 AND priority <= 5),
    done        INTEGER NOT NULL DEFAULT 0,
    created_at  REAL NOT NULL,
    done_at     REAL
);
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TODO_API_URL` | 后端 API 地址 | `http://127.0.0.1:8000` |

## 设计原则

1. **前后端分离** — 后端专注数据管理，前端专注交互体验
2. **双击就能用** — 启动脚本自动管理后端生命周期
3. **中文优先** — 原生中文支持和终端对齐
4. **数据透明** — SQLite 单文件存储，可用任意 SQLite 客户端查看修改
5. **API 优先** — 所有功能通过 REST API 暴露
6. **客户端零依赖** — 只靠 Python 标准库

## 许可证

MIT License
