#!/bin/bash

echo "🛑 停止蛋白质设计工作流服务"
echo "============================"

# 读取并停止后端服务
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ 后端服务已停止 (PID: $BACKEND_PID)"
    else
        echo "⚠️  后端服务已停止"
    fi
    rm -f logs/backend.pid
fi

# 读取并停止前端服务
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止 (PID: $FRONTEND_PID)"
    else
        echo "⚠️  前端服务已停止"
    fi
    rm -f logs/frontend.pid
fi

# 清理可能的僵尸进程
pkill -f "python.*main.py" 2>/dev/null
pkill -f "npm.*run.*dev" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "🎉 所有服务已停止"
