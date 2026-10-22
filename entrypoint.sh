#!/bin/sh
set -e

echo "=== 正在启动 OpsAsset 系统架构 ==="

# 启动 FastAPI 后端服务
echo "[1/2] 启动 FastAPI 后端服务 (127.0.0.1:8001)..."
uvicorn app.main:app --host 127.0.0.1 --port 8001 &

sleep 2

# 初始化 Nginx 日志目录
mkdir -p /var/log/nginx

# 安全更新日志软链接，避免重复启动时错误跟随已有链接
ln -sfnT /dev/stdout /var/log/nginx/access.log
ln -sfnT /dev/stderr /var/log/nginx/error.log

# 启动 Nginx
echo "[2/2] 启动 Nginx 动静分离网关 (0.0.0.0:8000)..."
exec nginx -g "daemon off;"
