#!/bin/bash

# NanoBee PPT Docker 停止脚本

set -e

echo "=========================================="
echo "  停止 NanoBee PPT 服务"
echo "=========================================="
echo ""

# 停止服务
if docker compose version &> /dev/null; then
    docker compose down
else
    docker-compose down
fi

echo ""
echo "✅ 所有服务已停止"
echo ""

# 询问是否清理镜像
read -p "是否删除 Docker 镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "清理 Docker 镜像..."
    docker rmi nanobee-backend nanobee-frontend 2>/dev/null || true
    echo "✅ 镜像已清理"
fi

echo ""
echo "如需重新启动，运行: ./docker-start.sh"
echo ""
