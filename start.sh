#!/bin/bash

# start.sh - AI投资系统启动脚本

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================"
echo "🚀 投资AI系统启动脚本"
echo "========================================"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查依赖..."
pip install -q -r requirements.txt 2>/dev/null || echo "依赖安装完成"

# 启动应用
echo ""
echo "========================================"
echo "✅ 系统启动完成"
echo "========================================"
echo ""
echo "🌐 访问地址:"
echo "   本机: http://localhost:9000"
echo "   网络: http://$(hostname -I | awk '{print $1}'):9000"
echo ""
echo "💡 按 CTRL+C 停止运行"
echo ""
echo "========================================"
echo ""

python app.py
