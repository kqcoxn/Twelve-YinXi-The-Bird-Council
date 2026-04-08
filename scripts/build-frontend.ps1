# 前端构建脚本 (Windows PowerShell)
# 用法: .\scripts\build-frontend.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "🔨 开始构建前端..." -ForegroundColor Cyan
Write-Host ""

# 检查 Node.js 是否安装
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js 版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 未找到 Node.js" -ForegroundColor Red
    Write-Host "💡 请先安装 Node.js: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# 检查 npm 是否安装
try {
    $npmVersion = npm --version
    Write-Host "✅ npm 版本: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 未找到 npm" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 进入前端目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $scriptDir "../frontend"
Set-Location $frontendDir

Write-Host "📦 安装前端依赖..." -ForegroundColor Cyan
npm install
Write-Host ""

Write-Host "🏗️  构建前端..." -ForegroundColor Cyan
npm run build
Write-Host ""

# 检查构建产物
$frontendDist = Join-Path $scriptDir "../frontend-dist"
if (Test-Path $frontendDist) {
    Write-Host "✅ 前端构建成功!" -ForegroundColor Green
    Write-Host "📁 构建产物: $frontendDist" -ForegroundColor Green
    Write-Host ""
    
    # 显示构建产物大小
    $size = (Get-ChildItem $frontendDist -Recurse | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "📊 构建产物大小: ${sizeMB} MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🎉 完成! 现在可以提交 frontend-dist/ 到 Git" -ForegroundColor Green
} else {
    Write-Host "❌ 构建失败: frontend-dist/ 目录不存在" -ForegroundColor Red
    exit 1
}
