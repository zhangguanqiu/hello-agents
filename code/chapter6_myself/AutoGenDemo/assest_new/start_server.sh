#!/bin/bash

# AutoGen 动态智能体团队 API 启动脚本

echo "=========================================="
echo "🚀 AutoGen 动态智能体团队 API"
echo "=========================================="
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

echo "✓ Python 版本: $(python3 --version)"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  警告: 未找到 .env 文件"
    echo "请创建 .env 文件并配置以下环境变量："
    echo "  - LLM_MODEL_ID"
    echo "  - LLM_API_KEY"
    echo "  - LLM_BASE_URL"
    echo "  - LLM_TIMEOUT"
    exit 1
fi

echo "✓ 找到 .env 配置文件"

# 检查依赖是否安装
echo ""
echo "📦 检查依赖..."

MISSING_DEPS=0

for package in fastapi uvicorn pydantic python-dotenv autogen-agentchat autogen-ext; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo "❌ 缺少依赖: $package"
        MISSING_DEPS=1
    fi
done

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo "⚠️  检测到缺少依赖，是否自动安装？(y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "📥 安装依赖..."
        pip install -r requirements_assest_new.txt
        if [ $? -ne 0 ]; then
            echo "❌ 依赖安装失败"
            exit 1
        fi
        echo "✓ 依赖安装完成"
    else
        echo "❌ 请手动安装依赖: pip install -r requirements_assest_new.txt"
        exit 1
    fi
else
    echo "✓ 所有依赖已安装"
fi

# 启动服务
echo ""
echo "=========================================="
echo "🎬 启动服务..."
echo "=========================================="
echo ""
echo "📍 服务地址: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo "🏥 健康检查: http://localhost:8000/api/v1/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""
echo "=========================================="
echo ""

# 启动 FastAPI 服务
python3 assest_new.py
