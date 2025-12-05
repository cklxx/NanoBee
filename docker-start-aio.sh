#!/bin/bash

# NanoBee PPT 单容器模式启动脚本

set -e

echo "=========================================="
echo "  NanoBee PPT 单容器模式 (All-in-One)"
echo "=========================================="
echo ""

# 检查 .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  已创建 .env 文件，请务必配置 API 密钥！"
fi

# 构建镜像
echo "🔨 正在构建 All-in-One 镜像 (可能需要几分钟)..."
docker build -t nanobee-aio -f Dockerfile.aio .

# 停止旧容器
docker rm -f nanobee-aio 2>/dev/null || true

# 启动容器
echo ""
echo "🚀 启动容器..."
docker run -d \
  --name nanobee-aio \
  -p 80:80 \
  -v $(pwd)/workspaces:/app/workspaces \
  -v $(pwd)/.env:/app/.env:ro \
  nanobee-aio

echo ""
echo "✅ 部署完成！"
echo "访问: http://localhost"
