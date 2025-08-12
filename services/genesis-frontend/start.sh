#!/bin/bash

echo "🚀 启动思想星系 - Project Genesis Frontend"
echo "==========================================="

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 16+"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖包..."
    npm install
fi

# 检查后端API
echo "🔍 检查后端API连接..."
if curl -s http://localhost:8080/api/graph/daily > /dev/null; then
    echo "✅ 后端API连接正常"
else
    echo "⚠️  后端API (localhost:8080) 未启动"
    echo "请先启动后端服务器: cd ../agent-crawler && uvicorn server.main:app --port 8080"
fi

echo ""
echo "🎯 启动开发服务器..."
echo "访问地址: http://localhost:3000"
echo "按 Ctrl+C 停止服务器"
echo ""
echo "🎮 交互说明:"
echo "  🖱️  鼠标拖拽 - 平移画布"
echo "  🔍 滚轮缩放 - 放大缩小"
echo "  👆 Mac触摸板 - 双指缩放/单指拖拽"
echo "  📱 触摸屏幕 - 双指捏合缩放"
echo "  🖱️  悬停节点 - 查看论文信息"
echo "  🖱️  点击节点 - 展开关联论文"
echo ""

npm run dev
