# 环境变量配置说明

本文档说明 NanoBee 项目中所有使用的环境变量。

## 📋 概述

NanoBee 使用环境变量来配置后端和前端服务。所有后端环境变量都使用 `NANOBEE_` 前缀。

## 🔧 配置方法

1. 复制 `.env.example` 文件为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填写必需的 API 密钥和其他配置

3. **重要**: `.env` 文件已被添加到 `.gitignore`，不会被提交到 Git 仓库

## 📝 环境变量详解

### 后端配置

#### 基础配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NANOBEE_WORKSPACES_ROOT` | 否 | `./workspaces` | 工作空间根目录，存储提示词笔记和生成的文件 |
| `NANOBEE_CORS_ORIGINS` | 否 | `["http://localhost:3000",...]` | CORS 允许的源，支持逗号分隔或 JSON 数组格式 |

#### 文本生成模型配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NANOBEE_DEFAULT_TEXT_MODEL` | 否 | `doubao-seed-1-6-251015` | 默认文本模型名称，用于 PPT 内容生成 |
| `NANOBEE_DEFAULT_TEXT_BASE_URL` | 否 | `https://ark.cn-beijing.volces.com/api/v3` | 文本模型 API 基础 URL（自动添加 /chat/completions 端点） |
| `NANOBEE_TEXT_API_KEY` | ⚠️ **是** | - | 文本模型 API 密钥，用于调用文本生成服务 |

#### 图像生成模型配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NANOBEE_DEFAULT_IMAGE_MODEL` | 否 | `doubao-seedream-4-5-251128` | 默认图像模型名称，用于 PPT 图片生成 |
| `NANOBEE_DEFAULT_IMAGE_BASE_URL` | 否 | `https://ark.cn-beijing.volces.com/api/v3` | 图像模型 API 基础 URL（自动追加 images/generations 端点） |
| `NANOBEE_IMAGE_API_KEY` | ⚠️ **是** | - | 图像模型 API 密钥，用于调用图像生成服务 |
| `NANOBEE_ALLOW_IMAGE_WATERMARK` | 否 | `false` | 是否允许 AI 生成图像添加水印 (true/false 或 1/0) |

> **注意**: 搜索功能使用豆包文本模型自动生成权威参考资料建议，无需额外配置。

### 前端配置

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NEXT_PUBLIC_API_BASE` | 否 | `http://localhost:8000` | 后端 API 地址，前端用于调用后端服务 |

## 🚀 使用示例

### 开发环境配置示例

```bash
# 后端配置
NANOBEE_WORKSPACES_ROOT=./workspaces
NANOBEE_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# 文本生成配置
NANOBEE_DEFAULT_TEXT_MODEL=doubao-seed-1-6-251015
NANOBEE_DEFAULT_TEXT_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
NANOBEE_TEXT_API_KEY=your_text_api_key_here

# 图像生成配置
NANOBEE_DEFAULT_IMAGE_MODEL=doubao-seedream-4-5-251128
NANOBEE_DEFAULT_IMAGE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
NANOBEE_IMAGE_API_KEY=your_image_api_key_here
NANOBEE_ALLOW_IMAGE_WATERMARK=false

# 前端配置
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### 生产环境配置示例

```bash
# 后端配置
NANOBEE_WORKSPACES_ROOT=/var/nanobee/workspaces
NANOBEE_CORS_ORIGINS=["https://yourdomain.com"]

# 文本生成配置
NANOBEE_TEXT_API_KEY=prod_text_api_key

# 图像生成配置
NANOBEE_IMAGE_API_KEY=prod_image_api_key
NANOBEE_ALLOW_IMAGE_WATERMARK=false

# 前端配置
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com
```

## 📚 相关文件

- [/.env.example](file:///Users/bytedance/code/personal/NanoBee/.env.example) - 根目录环境变量模板
- [/frontend/.env.example](file:///Users/bytedance/code/personal/NanoBee/frontend/.env.example) - 前端环境变量模板
- [/backend/app/config.py](file:///Users/bytedance/code/personal/NanoBee/backend/app/config.py) - 后端配置定义文件

## ⚠️ 注意事项

1. **API 密钥安全**: 
   - 永远不要将 `.env` 文件提交到 Git 仓库
   - 不要在代码中硬编码 API 密钥
   - 在生产环境中使用环境变量或密钥管理服务

2. **必填变量**:
   - `NANOBEE_TEXT_API_KEY` - 没有此密钥将无法调用文本生成服务
   - `NANOBEE_IMAGE_API_KEY` - 没有此密钥将无法调用图像生成服务

3. **CORS 配置**:
   - 开发环境: 包含所有本地地址
   - 生产环境: 仅包含实际的前端域名

4. **前端环境变量**:
   - 所有前端环境变量必须以 `NEXT_PUBLIC_` 开头才能在浏览器中访问
   - 修改前端环境变量后需要重新构建应用

## 🔄 更新日志

### 2025-12-05
- ✅ 移除了不再使用的 `NANOBEE_DATABASE_URL`
- ✅ 移除了不再使用的 OpenAI 相关配置（`NANOBEE_OPENAI_API_KEY`, `NANOBEE_OPENAI_BASE_URL`, `NANOBEE_OPENAI_MODEL`）
- ✅ 移除了不再使用的 `NANOBEE_ALLOW_DUMMY_LLM`
- ✅ 添加了火山引擎豆包模型相关配置
- ✅ 为所有环境变量添加了中英文说明
- ✅ 更新了 `.env.example` 文件以匹配实际代码使用的变量
