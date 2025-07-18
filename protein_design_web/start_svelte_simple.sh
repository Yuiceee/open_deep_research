#!/bin/bash

echo "🧬 启动蛋白质设计工作流 Web 应用 "
echo "=========================================="

# 检查是否在正确的目录
if [ ! -f "backend/main.py" ]; then
    echo "❌ 错误: 请在 protein_design_web 目录下运行此脚本"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动后端服务
echo "🚀 启动后端服务..."
cd backend
python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 3

# 检查后端是否成功启动
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ 后端服务启动失败，请检查 logs/backend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 启动新的 Svelte 前端
echo "🎨 启动 Svelte 前端..."
cd frontend_svelte

# 只在必要时重新安装依赖
if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
    echo "📦 安装前端依赖..."
    npm install --legacy-peer-deps --silent
fi

# 启动开发服务器
echo "🚀 启动 Vite 开发服务器..."
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ Svelte 前端已启动 (PID: $FRONTEND_PID)"

# 保存 PID 用于停止
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 服务已启动完成!"
echo "📊 后端 API: http://localhost:8000"
echo "🖥️  前端界面: http://localhost:5173"
echo ""
echo "💡 使用 './stop.sh' 停止所有服务"
echo "📝 日志文件: logs/backend.log, logs/frontend.log"

# 等待用户按 Ctrl+C
trap 'echo ""; echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f logs/*.pid; echo "✅ 服务已停止"; exit 0' INT

echo "按 Ctrl+C 停止服务..."
wait
