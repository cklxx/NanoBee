# NanoBee PPT

AI 驱动的 PPT 生成工具，通过智能搜索、大纲生成、内容创作和图像生成，快速创建专业的演示文稿。

## ✨ 功能特点

- 🔍 **智能搜索** - DuckDuckGo真实Web搜索 + LLM知识生成
- 📋 **大纲生成** - 自动规划PPT结构和章节
- ✍️ **内容创作** - AI生成每页标题、要点和配色方案
- 🎨 **图像生成** - SeaDream 4.5生成整页PPT视觉效果
- 💾 **项目管理** - 浏览器本地保存，支持多项目管理
- 📄 **PDF导出** - 一键导出为PDF文件

## 🚀 快速开始

### 1. 配置环境

复制 `.env.example` 到 `.env` 并配置必需的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 必需配置
NANOBEE_TEXT_API_KEY=你的文本生成API密钥
NANOBEE_IMAGE_API_KEY=你的图像生成API密钥

# 可选配置（使用默认值即可）
NANOBEE_DEFAULT_TEXT_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
NANOBEE_DEFAULT_IMAGE_BASE_URL=你的SeaDream API地址
```

### 2. 启动服务

使用一键启动脚本：

```bash
./scripts/run_fullstack.sh
```

该脚本会自动：
- 安装后端依赖
- 启动后端API（端口8000）
- 安装前端依赖
- 启动前端开发服务器（端口3000）

### 3. 使用

打开浏览器访问 `http://localhost:3000`，按照界面提示：

1. **输入主题** - 设置PPT主题和风格
2. **搜索参考资料** - 自动搜索权威参考来源
3. **生成大纲** - AI规划PPT结构（可预览）
4. **生成内容** - 为每页生成详细内容（可预览）
5. **生成页面** - 使用SeaDream生成视觉效果
6. **导出PDF** - 下载最终的PPT文档

## 📁 项目结构

```
NanoBee/
├── backend/           # FastAPI后端
│   ├── app/
│   │   ├── api/      # API路由
│   │   ├── ppt/      # PPT生成核心
│   │   └── config.py # 配置管理
│   └── tests/        # 后端测试
├── frontend/         # Next.js前端
│   ├── app/          # 页面和组件
│   └── public/       # 静态资源
├── scripts/          # 辅助脚本
└── .env.example      # 环境变量示例
```

## 🔧 API接口

主要端点：

- `POST /api/ppt/search` - 搜索参考资料
- `POST /api/ppt/outline` - 生成PPT大纲
- `POST /api/ppt/slides` - 生成每页内容
- `POST /api/ppt/images` - 生成PPT页面图像
- `GET /api/ppt/prompts` - 查看Prompt记录

## 🛠️ 开发

### 仅启动后端

```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 仅启动前端

```bash
cd frontend
npm install
npm run dev -- --port 3000
```

### 运行测试

```bash
# 后端测试
pip install -e ./backend
pytest backend/tests

# 前端测试
cd frontend
npm install
npm run test:e2e
```

## 📋 环境变量说明

详细配置请查看 [`ENV_VARIABLES.md`](./ENV_VARIABLES.md)

### 必需配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `NANOBEE_TEXT_API_KEY` | 文本生成API密钥 | `sk-xxx` |
| `NANOBEE_IMAGE_API_KEY` | 图像生成API密钥 | `sk-xxx` |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NANOBEE_WORKSPACES_ROOT` | Prompt笔记保存目录 | `./workspaces` |
| `NANOBEE_DEFAULT_TEXT_MODEL` | 文本模型名称 | `doubao-seed-1-6-251015` |
| `NANOBEE_DEFAULT_IMAGE_MODEL` | 图像模型名称 | `doubao-seedream-4-5-251128` |
| `NANOBEE_CORS_ORIGINS` | CORS允许的源 | `["http://localhost:3000"]` |

## 🎯 技术栈

- **后端**: FastAPI, Python 3.12+
- **前端**: Next.js 14, React, TypeScript, Tailwind CSS
- **AI**: 火山引擎豆包（文本）, SeaDream 4.5（图像）
- **搜索**: DuckDuckGo API

## 📝 许可证

MIT License
