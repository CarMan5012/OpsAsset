#!/bin/sh
set -e

echo "=== 正在启动 OpsAsset 系统架构 ==="

# 1. 启动后端 FastAPI 业务服务 (监听本地 127.0.0.1:8001)
echo "[1/2] 启动 FastAPI 后端服务 (127.0.0.1:8001)..."
uvicorn app.main:app --host 127.0.0.1 --port 8001 &

# 等待后端端口就绪
sleep 2

# 建立标准输出软链接，确保 docker logs 无遗漏捕获所有 Nginx 访问与错误日志
mkdir -p /var/log/nginx
ln -sf /dev/stdout /var/log/nginx/access.log
ln -sf /dev/stderr /var/log/nginx/error.log

# 2. 启动前端 Nginx 极速网关 (监听对外 0.0.0.0:8000)
echo "[2/2] 启动 Nginx 动静分离网关 (0.0.0.0:8000)..."
exec nginx -g "daemon off;"
