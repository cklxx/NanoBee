#!/bin/bash

# NanoBee PPT Docker 一键启动脚本
# 适用于腾讯云轻量服务器

set -e

echo "=========================================="
echo "  NanoBee PPT Docker 一键部署"
echo "=========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未找到 Docker，请先安装 Docker"
    echo ""
    echo "腾讯云服务器安装 Docker 命令："
    echo "  curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun"
    echo "  systemctl start docker"
    echo "  systemctl enable docker"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ 错误: 未找到 docker-compose，请先安装"
    echo ""
    echo "安装 docker-compose 命令："
    echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "  sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo ""
    echo "🔧 请编辑 .env 文件，配置以下必需的 API 密钥："
    echo "   - NANOBEE_TEXT_API_KEY"
    echo "   - NANOBEE_IMAGE_API_KEY"
    echo ""
    read -p "按 Enter 继续，或按 Ctrl+C 退出去配置 .env 文件..."
fi

# 创建工作空间目录
if [ ! -d workspaces ]; then
    mkdir -p workspaces
    echo "✅ 已创建 workspaces 目录"
fi

echo ""
echo "🚀 开始构建和启动 Docker 容器..."
echo ""

# 构建并启动服务
if docker compose version &> /dev/null; then
    docker compose up --build -d
else
    docker-compose up --build -d
fi

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "服务访问地址："
echo "  🌐 前端界面: http://localhost"
echo "  📡 后端 API: http://localhost/api"
echo "  💚 健康检查: http://localhost/health"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  查看状态: docker-compose ps"
echo "  停止服务: ./docker-stop.sh"
echo ""
echo "🎉 访问 http://localhost 开始使用 NanoBee PPT！"
echo ""
