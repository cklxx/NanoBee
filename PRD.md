# PPT 生成工作流工具 PRD

## 背景与目标
- 面向需要快速准备演示文稿的业务/产品/市场人员，提供“一站式从主题到可导出 PPT/PDF”的自动化工作流。
- 默认对接火山文本模型（`doubao-seed-1-6-251015`）和 SeaDream 图片模型（`doubao-seedream-4-5-251128`），可通过界面配置模型名称、API Base URL 与 API Key。
- 输出内容遵循“左侧参考检索—中间大纲/文案—右侧图片/PDF”的三列布局体验；图片遵循首图风格，不添加 AI 水印（可通过后端开关配置）。

## 用户故事
1. **快速准备**：用户输入主题，即可获得若干参考文章，便于确认素材来源。
2. **自动结构化**：基于参考生成 PPT 大纲与每页要点，并支持自定义文案风格提示。
3. **风格一致的图片**：使用 SeaDream 4.5 输出各页插图，首图确定风格，后续沿用；可切换图片模型和 Base URL。
4. **可导出与复核**：支持预览、状态日志与 PDF 下载，便于复核与分享。

## 功能范围
- **模型配置**：文本/图片模型名称、Base URL、API Key，可存本地不回传；文本默认 `doubao-seed-1-6-251015`，图片默认 `doubao-seedream-4-5-251128`。
- **参考检索**：按主题生成 5 条以上可点击的参考文章，按权威度排序并编号以便 PPT 索引。
- **大纲生成**：汇总参考得到 5 个章节标题及要点，最多 14 页内容 + 1 页参考索引（总页数 ≤ 15）。
- **内容展开**：每个章节生成关键词、要点、配色基调，并标注使用的参考索引；输入给大模型的 prompt 以 Markdown 存储，支持迭代覆盖。
- **Prompt Notebook**：所有阶段的 prompt 都以 Markdown Notebook 迭代存读，支持通过 API 拉取指定主题/阶段的历史记录。
- **图片生成**：SeaDream 4.5（或可配模型）生成 16:9 图片，除首图外沿用首图调色；水印开关可选。
- **导出**：将文字与图片组合导出 PDF；流程状态日志可查看。
- **后端裁剪**：后端仅保留 PPT Workflow 所需接口与配置，移除旧有的任务/数据库样板代码，降低依赖。

## 业务流程（与前端三列布局对应）
1. **参考检索**（左列）：输入主题 → 调用 `/api/ppt/search` → 展示文章列表。
2. **大纲与文案**（中列）：点击生成大纲 `/api/ppt/outline` → 展示章节 → 点击生成文案 `/api/ppt/slides`。
3. **配图与导出**（右列）：调用 `/api/ppt/images` → 展示首图+沿用风格的图片 → 导出 PDF。

## 接口设计
- `POST /api/ppt/search`：入参 `{ topic, limit? }`；出参 `{ topic, references[] }`（含权威排序的 `rank` 字段）。
- `POST /api/ppt/outline`：入参 `{ topic, references[] }`；出参 `{ topic, outline[] }`。
- `POST /api/ppt/slides`：入参 `{ topic, outline[], references[], style_prompt?, model? }`；出参 `{ slides[] }`，包含配色、关键词与引用的参考索引。
- `POST /api/ppt/images`：入参 `{ topic?, slides[], image_model?, base_url?, watermark? }`；出参 `{ images[] }`，每条含 `title`、`style_seed`、`data_url`。
- `GET /api/ppt/prompts?topic=...&stage?=...`：返回指定主题的 Markdown Notebook 列表或单个阶段内容，便于复盘/迭代。

## 数据结构
- `ReferenceArticle`：`title`、`url`、`summary`、`source`。
- `OutlineSection`：`title`、`bullets[]`。
- `SlideContent`：`title`、`bullets[]`、`palette{primary,secondary,accent}`、`keywords`、`style_prompt`。
- `SlideImage`：`title`、`style_seed`、`data_url`（Base64 PNG）。

## 非功能需求
- **可靠性**：后端以纯函数生成可预测内容，便于离线演示；未来可替换为真实 LLM/图片 API。
- **可配置性**：文本/图片模型、Base URL、API Key 与水印开关均在后端配置并暴露给前端。
- **可观测性**：流程事件日志（前端 UI 已提供）；后端可扩展 tracing/存储。
- **国际化**：默认中文输出，文本与模型配置保留英文命名。

## 验收标准
- 提供可运行的 `/api/ppt/*` 接口，返回结构与前端使用的字段一致。
- 前端可通过接口完成“检索→大纲→内容→配图→PDF”链路，图片风格保持一致且无 AI 水印。
- PRD 与代码落库，包含默认配置说明、数据结构、流程描述。

## 任务拆解与进度
- [x] 后端裁剪为单一 PPT Workflow，移除遗留任务/数据库代码，保留 `/api/ppt/*` 接口。
- [x] 默认文本/图片模型设置为 `doubao-seed-1-6-251015` / `doubao-seedream-4-5-251128`，支持 Base URL 与水印开关。
- [x] Prompt Notebook 以 Markdown 迭代存读，`/api/ppt/prompts` 可按主题+阶段回溯。
- [x] 参考检索按权威度排序并在 PPT 末尾生成参考索引页，整体页数不超过 15。
- [x] 图片生成沿用首图调色并在保存 prompt 时按主题归档（Images 请求增加 `topic` 以保持 Notebook 完整）。
- [x] 接入真实火山文本/图片 API（当前为可预测占位逻辑，后续可替换为正式服务）。
