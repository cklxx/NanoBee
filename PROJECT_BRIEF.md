# 长时运行 Agent Harness 项目说明与任务清单

本文档可直接交给编程代理执行，说明项目目标、技术选型、目录结构与分阶段任务。内容基于《Effective harnesses for long-running agents》的核心思路，包含 initializer + coding agent 的工程化落地，并预留 memory、子 Agent、评测与前端控制台。

## 1. 项目总目标
- 实现一个长时运行的 Agent Harness：每个任务对应独立 workspace + git 仓库。
- 提供 **Initializer Agent**：生成初始结构、`init.sh`、`feature_list.json`、`progress.log`。
- 提供 **Coding Agent**：每个 session 针对单一 feature 做增量开发，运行 `./init.sh`，更新 feature 状态与 `progress.log`。
- 扩展方向：memory 自动压缩检索、子 Agent（QA/Eval）、文件系统统一操作、任务日志/回放、Web UI 控制台。

## 2. 技术栈
### 后端
- Python 3.11+、FastAPI、SQLAlchemy + Postgres（+ pgvector 预留）。
- 自定义 `LLMClient` 抽象，首版可用 OpenAI；文件存储本地，可扩展 S3/MinIO。
- 标准 logging + `TaskEvent` 表；后续可接队列（Celery/RQ）。

### 前端
- Next.js 14 (App Router) + TypeScript，Tailwind CSS + shadcn/ui。
- 目标：任务列表、任务详情、时间线、文件树、feature 状态视图。

## 3. 目录结构（目标状态）
```
long-run-agent-harness/
├── backend/
│   ├── pyproject.toml / requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── deps.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   └── openai_client.py
│   │   ├── harness/
│   │   │   ├── models.py
│   │   │   ├── prompts.py
│   │   │   ├── workspace.py
│   │   │   ├── initializer.py
│   │   │   ├── coder.py
│   │   │   ├── feature_list.py
│   │   │   ├── progress_log.py
│   │   │   ├── git_tools.py
│   │   │   ├── shell_tools.py
│   │   │   ├── memory.py
│   │   │   ├── evaluation.py
│   │   │   └── runner.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── models.py
│   │   │   └── session.py
│   │   ├── api/
│   │   │   ├── tasks.py
│   │   │   ├── workspaces.py
│   │   │   └── logs.py
│   │   └── utils/
│   │       └── logging.py
│   └── tests/
└── frontend/
    ├── package.json
    ├── next.config.mjs
    └── app/
        ├── layout.tsx
        ├── page.tsx
        ├── tasks/[id]/page.tsx
        └── components/
            ├── TaskList.tsx
            ├── TaskTimeline.tsx
            ├── LogViewer.tsx
            ├── FeatureTable.tsx
            ├── WorkspaceFileTree.tsx
            └── TaskHeader.tsx
```

## 4. 分阶段任务
### Phase 1：后端基础骨架 + DB + 简单 API
1. ✅ 初始化 FastAPI 项目与配置（`config.py`、`db/base.py`、`db/session.py`）。
2. ✅ 设计 ORM：`Workspace`、`Task`、`TaskEvent`，预留 `MemoryChunk`、`EvalResult`。
3. ✅ 定义 `LLMClient` 抽象与 OpenAI 实现。
4. ✅ API：创建任务、查询任务列表/详情。

### Phase 2：Workspace + Harness 核心（Initializer & Coding）
5. ✅ Workspace 管理：创建目录、文件读写、文件树。
6. ✅ 引入 `prompts.py`（Initializer/Coding 的 system & user 模板）。
7. ✅ 工具：`feature_list.py`、`progress_log.py`、`git_tools.py`、`shell_tools.py`。
8. ✅ Initializer Agent：生成 scaffold、`init.sh`、`feature_list.json`、`progress.log`，首 commit。
9. ✅ Coding Agent：单 feature 增量开发、运行 `./init.sh`、更新状态与 `progress.log`、git commit。

### Phase 3：日志/回放 API & 基础前端
10. ✅ TaskEvent 记录关键步骤（LLM 调用、工具操作、测试结果）。
11. ✅ API：`/api/tasks/{id}/events` 时间线；可按 `session_type`/`event_type` 过滤。
12. ✅ 前端初始化与页面：任务列表、任务详情（Timeline/Features/Files/Progress/Evaluation）。

### Phase 4：增强（Memory / Subagent / Eval）
13. ✅ `memory.py`：事件写入、阈值压缩为 summary、向量检索召回（基础版）。
14. ✅ 在 Coding prompt 中注入 Memory 摘要；可调用 Summarizer 子 Agent（预留）。
15. ✅ Eval/QA 子 Agent：LLM 评测整体结果，写入 `EvalResult`，API `POST /api/tasks/{id}/evaluate`。
16. ✅ 前端增加 Evaluation 视图。

## 5. 提示与使用建议
- 初始阶段可以先用 Dummy/OpenAI LLM 跑通链路；demo 任务可用“极简 todo webapp”。
- `init.sh` 应成为唯一入口：安装依赖 + 运行 dev/test。
- `feature_list.json` 初始全为 `"failing"`，后续只能改 status/notes，不改描述或删除条目。
- `progress.log` 只追加；每个 session 记录目标、修改、测试结果与 TODO。
- 每个 session 结束保持 git 干净；Coding 成功时 `git commit`。
- 预留 memory/子 Agent/评测模块接口，方便后续接入。
