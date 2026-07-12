# Simple Todo

> 前后端分离的命令行待办事项管理工具 | 完整支持中文 | 双击就能用

这个工具是一个 CLI 任务管理器，采用**前后端分离架构**：后端提供 REST API 服务，CLI 作为 API 客户端运行。两者可独立部署，也可以通过双击启动脚本一键启动。

## 架构概览

```
simple-todo/
├── server/                    # 后端 API 服务（FastAPI）
│   ├── main.py               # API 入口，定义所有端点
│   ├── models.py             # 数据模型（Pydantic）
│   ├── storage.py            # 持久化层（JSON 读写）
│   └── requirements.txt      # 后端依赖
├── client/                    # CLI 客户端（纯标准库）
│   ├── cli.py                # 命令行入口
│   ├── api.py                # API 调用封装
│   ├── display.py            # 终端渲染（中文对齐）
│   └── menu.py               # 交互式菜单
├── todo.command               # macOS 双击启动
├── todo.bat                   # Windows 双击启动
└── README.md
```

## 功能概览

- ✅ **添加 / 删除 / 完成任务** — 基本的增删改操作
- ✅ **中文的显示处理** — 标题支持中文，终端对齐不偏移
- ✅ **优先级管理** — 数字越小越重要，排得越靠前
- ✅ **搜索功能** — 通过关键词快速查找任务
- ✅ **REST API** — 后端提供标准 HTTP 接口，可用 curl/Postman 直接调用
- ✅ **前后端分离** — CLI 和 API 服务可独立运行、独立部署
- ✅ **JSON 存储** — 数据格式与旧版完全兼容

## 快速开始

### 环境要求

- Python 3.8+
- macOS、Linux 或 Windows

### 安装依赖

```bash
# 安装后端依赖
cd server
pip install -r requirements.txt
```

### 使用方法一：双击运行（推荐）

直接双击启动脚本，会自动启动后端服务并打开交互菜单：
- **macOS** → 双击 `todo.command`
- **Windows** → 双击 `todo.bat`

启动后会自动弹出菜单界面：

```
========================================
         Simple Todo — 待办事项
========================================

  （当前的任务列表会显示在这里）

----------------------------------------
  1. 添加任务
  2. 完成任务
  3. 恢复任务（取消完成）
  4. 删除任务
  5. 搜索任务
  6. 修改优先级
  7. 查看全部（含已完成）
  8. 刷新列表
  0. 退出
----------------------------------------

请选择操作 [0-8]:
```

### 使用方法二：手动启动

```bash
# 终端 1：启动后端服务
cd server
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 终端 2：使用 CLI
cd simple-todo
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
  -d '{"title":"完成中期报告","priority":1}' \
  http://127.0.0.1:8000/tasks

# 查看任务列表
curl http://127.0.0.1:8000/tasks

# 查看全部（含已完成）
curl http://127.0.0.1:8000/tasks?all=true

# 标记完成
curl -X PUT http://127.0.0.1:8000/tasks/1/done

# 搜索
curl http://127.0.0.1:8000/tasks/search?q=报告

# 修改优先级
curl -X PUT -H 'Content-Type: application/json' \
  -d '{"priority":2}' \
  http://127.0.0.1:8000/tasks/1/priority

# 删除
curl -X DELETE http://127.0.0.1:8000/tasks/1
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
| `list` | 列出未完成任务（默认） | `python -m client.cli` 或 `python -m client.cli list` |
| `all` | 列出所有任务 | `python -m client.cli all` |
| `done <ID>` | 标记完成 | `python -m client.cli done 1` |
| `undone <ID>` | 恢复未完成 | `python -m client.cli undone 1` |
| `rm <ID>` | 删除任务 | `python -m client.cli rm 1` |
| `search <关键词>` | 搜索 | `python -m client.cli search 报告` |
| `priority <ID> <数字>` | 修改优先级 | `python -m client.cli priority 1 1` |
| `menu` | 交互菜单 | `python -m client.cli menu` |
| `help` | 帮助信息 | `python -m client.cli help` |

## 排序规则

任务列表按以下顺序排列：

1. **完成状态** — 未完成的任务排在前面
2. **任务优先级** — 数字越小越靠前（1 最重要）
3. **创建时间** — 优先级相同时，创建更早的排在前面

## 数据存储

所有数据存放于 `~/.simple_todo/tasks.json`，格式与旧版完全兼容：

```json
[
  {
    "id": 1,
    "title": "完成中期报告",
    "priority": 1,
    "done": true,
    "created_at": 1752053425.123,
    "done_at": 1752053520.456
  }
]
```

## 中文支持

| 方面 | 方法 |
|------|------|
| 内容存储 | JSON 编码 UTF-8，`ensure_ascii=False` |
| 终端显示 | `unicodedata.east_asian_width()` 检测字符宽度 |
| 表格对齐 | 中文字符按两列宽度计算，英文按一列 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TODO_API_URL` | 后端 API 地址 | `http://127.0.0.1:8000` |

## 设计原则

1. **前后端分离** — 后端专注数据管理，前端专注交互体验
2. **双击就能用** — 启动脚本自动管理后端生命周期
3. **优先考虑中文** — 原生的中文支持和终端对齐
4. **数据透明** — JSON 格式存储，可随时查看修改
5. **API 优先** — 所有功能通过 REST API 暴露，可被任意客户端调用

## 后续规划

- [ ] 任务分类功能（标签/项目分组）
- [ ] 截止日期提醒
- [ ] 周期性重复任务
- [ ] 数据导出（CSV / Markdown）
- [ ] Web 可视化面板
- [ ] Docker 部署支持

## 许可证

MIT License

---

**提交日期**：2026 年 7 月
