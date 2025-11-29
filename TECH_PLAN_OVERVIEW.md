# 技术方案总览与 Anthropic Harness 复现路线图

本文件归纳了项目的目标、架构和具体落地步骤，可直接作为设计说明/任务说明交给自动化编程代理使用，复现 Anthropic 文章《Effective harnesses for long-running agents》中描述的 Harness 流程。

## 1. 目标与核心理念
- **目标**：用通用的 Agent 后端 + 控制台，工程化实现「Initializer Agent + Coding Agent + 长程环境管理」，支持多 context window 连续 session 的长时运行。
- **理念与约束**：
  - 长时运行 = 多轮 session 持续迭代，同一 workspace 内保持上下文连贯。
  - 使用两种角色：
    - **Initializer Agent**：生成 `init.sh`、完整 `feature_list.json`（全部 passing=false）、`progress.log`，初始化 git 并完成首个 commit。
    - **Coding Agent**：每轮选择一个未完成 feature，增量修改代码，执行 `./init.sh` 自测，更新 feature 状态与 `progress.log`，并提交 git commit。
  - 每个新 session 先“get bearings”：查看 `pwd`、git log、`feature_list.json`、`progress.log` 后再行动。

## 2. 架构与技术栈
### 后端
- Python 3.11+、FastAPI、SQLAlchemy + Postgres（含 pgvector 以支持记忆）。
- 自定义 `LLMClient` 抽象，首版接入 OpenAI，后续可换 Claude/自研模型。
- 本地文件系统 `workspaces/<workspace_id>/`（可扩展 S3/MinIO）。
- Task / TaskEvent ORM 记录 session、工具调用、测试结果，可选接 Langfuse 深度追踪。

### 前端
- Next.js 14（App Router）+ TypeScript，Tailwind CSS + shadcn/ui。
- 控制台视图：任务列表、任务详情（时间线 + Feature 表 + progress.log + 文件树），后续可扩展 Eval 和 Memory 视图。

### 目录与模块（核心）
- `backend/app/harness/`：`prompts.py`、`initializer.py`、`coder.py`、`workspace.py`、`feature_list.py`、`progress_log.py`、`git_tools.py`、`shell_tools.py`、`memory.py`、`evaluation.py`、`runner.py`。
- `backend/app/db/`：`Task`、`TaskEvent`、`Workspace`、`MemoryChunk`、`EvalResult` 等模型。
- `backend/app/api/`：`/api/tasks`、`/api/tasks/{id}/run/init`、`/api/tasks/{id}/run/coding` 等接口。
- `frontend/app/`：`/` 任务列表、`/tasks/[id]` 详情页（Timeline + Features + Files + Progress + Evaluation）。

## 3. 环境布局（Workspace）
```
workspaces/<workspace_id>/
├── init.sh
├── feature_list.json
├── progress.log
├── .git/
├── src/...
└── README.md
```
- `feature_list.json`：端到端用户视角的 feature，初始全部 `passes=false`。
- `progress.log`：跨 session 的自然语言纪要，append-only。
- 统一入口 `init.sh` 运行依赖安装与测试；git 记录用于理解变更和回滚。

## 4. Initializer Agent 职责
- 扩展用户 spec → 生成完整 feature list（不拆成微任务）。
- 写入 `init.sh`、`feature_list.json`、`progress.log`，创建基础代码 scaffold。
- 初始化 git 并完成首个 commit；记录 `TaskEvent` 标识 initializer 完成。
- Prompt 采用专用的 INITIALIZER_SYSTEM_PROMPT，确保只在首个 session 使用。

## 5. Coding Agent 流程
1. 读取 `pwd`、`feature_list.json`、`progress.log`、git log 获取上下文。
2. 选择一个未完成的 feature（或外部指定）。
3. 围绕该 feature 做最小但完整的增量改动。
4. 运行 `./init.sh` 进行自测（可扩展浏览器 E2E）。
5. 测试通过后将该 feature 标记为 `passes=true`，在 `progress.log` 中记录细节。
6. 完成后 `git commit`，保持环境干净；失败时仅记录，不标记通过。
7. Prompt 限制：一次只处理一个 feature，不改写/删除 feature 描述，禁止过早宣布完成。

## 6. 运行步骤（实验复现）
1. **创建任务**：`POST /api/tasks`，获得 `task_id` 与 `workspace_id`。
2. **运行 Initializer**：`POST /api/tasks/{task_id}/run/init`，检查 workspace 是否包含 `init.sh`、`feature_list.json`、`progress.log` 且 git 有初始 commit。
3. **多轮 Coding Session**：重复 `POST /api/tasks/{task_id}/run/coding`，验证每轮只处理一个 feature，`feature_list.json` 状态逐条变为 passing，`progress.log` 和 git log 记录清晰。
4. **结果判定**：当 webapp 随 session 逐步完善、失败/成功可追溯，即等价复现 Anthropic Harness。

## 7. 增强方向
- **Memory**：`memory.py` 将 TaskEvent 写入并定期压缩为 summary，存储 `MemoryChunk` 并可被 Coding Agent prompt 调用。
- **子 Agent**：QA Agent 跑重型测试或浏览器自动化；Eval Agent 给出完成度评分写入 `EvalResult`。
- **前端**：增加 Memory/Eval 视图，展示长程记忆摘要与评测结果。

## 8. 一句话总结
- 技术方案：Python/FastAPI + Postgres + workspace FS +「Initializer + Coding Agent」Harness + Task/Event Log + Next.js 控制台。
- 复现方式：遵循 `init.sh + feature_list.json + progress.log + git + 一次一个 feature + 测试通过才 passing` 的流程，用不同 prompt 的两个 Agent 多轮迭代完成真实项目。
