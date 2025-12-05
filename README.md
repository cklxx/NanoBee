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

### 方式一：Docker Compose 部署（推荐）

适用于生产环境，服务解耦，易于维护。

#### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 配置 API 密钥
```

#### 2. 一键启动

```bash
./docker-start.sh
```

### 方式二：单容器部署 (All-in-One)

如果您希望仅运行一个 Docker 容器：

```bash
chmod +x docker-start-aio.sh
./docker-start-aio.sh
```

此脚本会构建一个包含 Nginx、前端和后端的单一镜像并运行。

---

### 方式三：开发环境本地运行

#### 3. 访问应用

打开浏览器访问：
- **前端界面**：`http://localhost`（或服务器 IP 地址）
- **API 接口**：`http://localhost/api`
- **健康检查**：`http://localhost/health`

#### 4. 停止服务

```bash
./docker-stop.sh
```

#### 腾讯云服务器部署注意事项

1. **安装 Docker**（如未安装）：
   ```bash
   curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
   systemctl start docker
   systemctl enable docker
   ```

2. **开放端口**：在腾讯云控制台的安全组中开放 80 端口

3. **首次构建**：可能需要 5-10 分钟，脚本已配置国内镜像源加速

---

### 方式二：开发环境本地运行

适用于开发调试。

#### 1. 配置环境

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
NANOBEE_DEFAULT_IMAGE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

#### 2. 启动服务

使用一键启动脚本：

```bash
./scripts/run_fullstack.sh
```

该脚本会自动：
- 安装后端依赖
- 启动后端API（端口8000）
- 安装前端依赖
- 启动前端开发服务器（端口3000）

#### 3. 使用

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
- **部署**: Docker, Nginx（反向代理）

## 🐳 Docker 部署架构

```
┌─────────────────────────────────────────┐
│           Nginx (端口 80)               │
│      ┌─────────────┬──────────────┐     │
│      │   /         │    /api/     │     │
│      └──────┬──────┴──────┬───────┘     │
└─────────────┼─────────────┼─────────────┘
              │             │
        ┌─────▼──────┐ ┌───▼────────┐
        │  Frontend  │ │  Backend   │
        │  (3000)    │ │  (8000)    │
        └────────────┘ └────────────┘
```

- **Nginx**：作为反向代理统一在 80 端口对外提供服务
- **Frontend**：Next.js 生产构建（standalone 模式）
- **Backend**：FastAPI + Uvicorn

## 🔧 常见问题

### Docker 相关

**Q: 构建镜像时速度慢怎么办？**
- A: 已配置国内镜像源（pip: 清华源, npm: 腾讯云源），首次构建约 5-10 分钟属于正常

**Q: 提示端口 80 被占用？**
- A: 检查是否有其他服务占用 80 端口，使用 `sudo lsof -i :80` 查看，或修改 `docker-compose.yml` 中的端口映射

**Q: 前端无法访问后端 API？**
- A: 检查 Nginx 配置是否正确，使用 `docker-compose logs nginx` 查看日志

**Q: 如何查看服务日志？**
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### 环境配置

**Q: API 密钥配置错误？**
- A: 检查 `.env` 文件中的 `NANOBEE_TEXT_API_KEY` 和 `NANOBEE_IMAGE_API_KEY` 是否正确配置

**Q: 图片生成失败？**
- A: 确认图像 API 地址和密钥配置正确，检查后端日志获取详细错误信息

## 📝 许可证

MIT License
