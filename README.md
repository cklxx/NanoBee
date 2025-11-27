# NanoBee Harness

该仓库实现了长时运行 Agent 的工程化 harness（受《Effective harnesses for long-running agents》启发），包含 initializer + coding agent、workspace/git 管理与演示后端。

## 快速了解
- 后端：FastAPI + 自定义 harness 组件（workspace、initializer、coding agent、LLM 抽象等）。
- 当前 Demo：可通过 `python -m backend.app.harness.runner` 运行模拟任务。
- 详情请查看项目说明与任务清单：[`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md)。

## 配置

- 复制 `.env.example` 到 `.env` 并按需修改：数据库位置、工作区目录、可选的 OpenAI Key、前端 API 基址。
- 如果需要对接兼容的 OpenAI 接口或切换模型，可设置 `NANOBEE_OPENAI_BASE_URL` 与 `NANOBEE_OPENAI_MODEL`。
- 如果前端与后端运行在不同端口，请设置 `NANOBEE_CORS_ORIGINS`（逗号分隔）允许前端来源访问。

## API 快速上手

本地运行 FastAPI：

```bash
uvicorn backend.app.main:app --reload
```

主要接口：
- `POST /api/tasks`：创建任务与 workspace 记录。
- `POST /api/tasks/{task_id}/run/init`：触发 initializer agent。
- `POST /api/tasks/{task_id}/run/coding`：运行一次 coding session。
- `POST /api/tasks/{task_id}/run/coding/all`：连续运行多次 coding session，直到所有 feature 通过或达到上限。
- `POST /api/tasks/{task_id}/evaluate`：运行 Eval Agent，生成评测结果。
- `GET /api/tasks`、`GET /api/tasks/{task_id}`：查询任务。
- `GET /api/workspaces/{workspace_id}/files`：列出 workspace 文件。
- `GET /api/tasks/{task_id}/events`：查看任务事件（占位，后续丰富 payload）。
- `GET /api/tasks/{task_id}/features`：返回 feature_list.json 的解析内容。
- `GET /api/tasks/{task_id}/progress`：返回 progress.log 内容。
- `GET /api/tasks/{task_id}/evals`：返回历史评测。

### 端到端 Demo（本地 SQLite + Dummy LLM）

1) 安装后端依赖：

```bash
pip install -e ./backend
```

2) 启动 API：

```bash
uvicorn backend.app.main:app --reload
```

3) 在另一个终端调用接口跑通完整链路（初始化 + 连续 Coding）：

```bash
# 创建任务（会同时创建 workspace 目录）
curl -X POST http://localhost:8000/api/tasks -H 'Content-Type: application/json' \
  -d '{"goal":"build a tiny todo app"}'

# 假设返回 id 为 task-...，触发 initializer
curl -X POST http://localhost:8000/api/tasks/task-<id>/run/init

# 触发一次 coding session（Dummy LLM 会跑本地 tests）
curl -X POST http://localhost:8000/api/tasks/task-<id>/run/coding/all

# 查看事件时间线
curl http://localhost:8000/api/tasks/task-<id>/events

# 触发评测
curl -X POST http://localhost:8000/api/tasks/task-<id>/evaluate
```

### 前端控制台（Next.js）

前端使用 Next.js 14 + Tailwind，默认从 `NEXT_PUBLIC_API_BASE` 读取后端地址（见 `.env.example`）。

```bash
cd frontend
npm install
npm run dev
```

页面：

- `/`：任务列表。
- `/tasks/[id]`：任务详情，包括 Timeline、Features、Files、Progress、Evaluation，并提供按钮触发 initializer / coding(all) / evaluation API。

### 全链路本地运行（后端 + 前端）

1) 准备环境：复制 `.env.example` 到 `.env`，必要时调整数据库路径、工作区目录、CORS 来源与 API Base。
2) 启动后端：

```bash
uvicorn backend.app.main:app --reload --port 8000
```

3) 启动前端（新终端）：

```bash
cd frontend
npm install
npm run dev -- --hostname 0.0.0.0 --port 3000
```

4) 打开浏览器访问 `http://localhost:3000`，通过 UI 创建任务、运行 initializer / coding-all / evaluation，并在时间线、Feature 表、文件树与 Progress/Evaluation 面板查看实时结果。

### 一键本地开发脚本

脚本会自动复制缺失的 `.env`（根目录与 `frontend`）并安装后端依赖；你可以直接运行命令一次性启动后端与前端（默认端口 8000/3000）：

```bash
./scripts/run_fullstack.sh
```

脚本会自动：

- 检查 `.env` / `frontend/.env` 是否存在，如果缺失则从对应的 `.env.example` 复制；
- 安装 Python 后端依赖（`pip install -e backend`，仅首次运行需要安装）；
- 读取根目录 `.env` 以获得数据库、工作区根目录、CORS 以及 `NEXT_PUBLIC_API_BASE` 配置；
- 在后台启动 `uvicorn backend.app.main:app`；
- 如果还没有 `frontend/node_modules`，会先执行 `npm install`；
- 在前台启动 Next.js dev server，并把 `NEXT_PUBLIC_API_BASE` 默认指向后端端口。

当你停止脚本（`Ctrl+C`）时，后台的后端进程也会自动退出。
