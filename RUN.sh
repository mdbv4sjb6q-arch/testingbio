#!/bin/bash

# ============================================================
# 🚀 XBIT AI 系统启动脚本
# ============================================================

echo "🚀 启动 XBIT AI 投资系统..."
echo ""

# 进入项目目录
cd /Users/tonychan/Documents/trae_projects/AI

# 激活虚拟环境
echo "📦 激活Python虚拟环境..."
source .venv/bin/activate

# 验证依赖
echo "✅ 验证依赖..."
python -c "import flask, pandas, openpyxl, requests; print('✅ 所有依赖已就绪')" 2>/dev/null || {
    echo "⚠️  缺少依赖，正在安装..."
    pip install -q Flask Flask-CORS Flask-Session pandas numpy requests openpyxl ccxt yfinance python-dotenv pyyaml
    echo "✅ 依赖安装完成"
}

echo ""
echo "=================================================="
echo "🌐 启动Web服务器..."
echo "=================================================="
echo ""
echo "📍 访问地址:"
echo "   🏠 首页: http://localhost:9000/"
echo "   ✨ PRO会员: http://localhost:9000/pro"
echo "   🌟 SVIP会员: http://localhost:9000/svip"
echo ""
echo "📝 按 Ctrl+C 停止服务"
echo "=================================================="
echo ""

# 启动Flask应用
python app.py
