#!/bin/bash

# 快速启动脚本 - 一键启动系统

cd /Users/tonychan/Documents/trae_projects/AI

echo "🚀 启动 XBIT AI 系统..."
echo ""

# 激活虚拟环境
source .venv/bin/activate

echo "✅ 虚拟环境已激活"
echo ""
echo "🌐 服务器启动于: http://localhost:9000"
echo "📍 首页: http://localhost:9000/"
echo "✨ PRO会员: http://localhost:9000/pro"  
echo "🌟 SVIP会员: http://localhost:9000/svip"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动Flask
python app.py
