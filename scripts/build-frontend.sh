#!/bin/bash

# 前端构建脚本 (Linux/Mac)
# 用法: ./scripts/build-frontend.sh

set -e  # 遇到错误立即退出

echo "🔨 开始构建前端..."
echo ""

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo "💡 请先安装 Node.js: https://nodejs.org/"
    exit 1
fi

# 检查 npm 是否安装
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 进入前端目录
cd "$(dirname "$0")/../frontend" || exit 1

echo "📦 安装前端依赖..."
npm install
echo ""

echo "🏗️  构建前端..."
npm run build
echo ""

# 检查构建产物
if [ -d "../frontend-dist" ]; then
    echo "✅ 前端构建成功!"
    echo "📁 构建产物: ../frontend-dist/"
    echo ""
    
    # 显示构建产物大小
    SIZE=$(du -sh ../frontend-dist | cut -f1)
    echo "📊 构建产物大小: $SIZE"
    echo ""
    echo "🎉 完成! 现在可以提交 frontend-dist/ 到 Git"
else
    echo "❌ 构建失败: frontend-dist/ 目录不存在"
    exit 1
fi
