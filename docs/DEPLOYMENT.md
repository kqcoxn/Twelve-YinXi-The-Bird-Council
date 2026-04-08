# 本地部署指南

## 🚀 一键启动

### 前置要求

- Python 3.10+
- **无需安装 Node.js** (前端已预构建)
- **无需安装数据库服务** (SQLite 零配置)
- **无需安装 Redis**
- **无需 Docker**

### 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd Twelve-YinXi-The-Bird-Council

# 2. 安装核心依赖
pip install -r requirements.txt

# 3. (可选) 安装向量检索增强
pip install -r requirements-vector.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,填入 LLM API Key

# 5. 启动服务
python main.py

# 6. 浏览器自动打开 http://localhost:8000
```

就这么简单! 🎉

### 依赖说明

| 依赖包                  | 必需 | 大小   | 说明                      |
| ----------------------- | ---- | ------ | ------------------------- |
| requirements.txt        | ✅   | ~50MB  | FastAPI, SQLite, 基础功能 |
| requirements-vector.txt | ❌   | ~300MB | 向量检索 (可选,推荐)      |
| requirements-dev.txt    | ❌   | ~20MB  | 开发工具 (测试,代码检查)  |

---

## 📁 项目结构

```
Twelve-YinXi-The-Bird-Council/
├── backend/
│   ├── app/
│   │   ├── core/           # 配置、依赖
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 核心服务
│   │   │   ├── vector_search.py  # 向量检索 (自动降级)
│   │   ├── agents/         # Agent 实现
│   │   └── api/            # 路由
│   ├── data/
│   │   ├── council.db      # SQLite 数据库 (自动创建)
│   │   └── backups/        # 自动备份
│   └── main.py             # 统一入口
├── frontend/               # Next.js 源代码 (开发用)
│   └── ...
├── frontend-dist/          # 预构建产物 (用户无需关心)
│   ├── index.html
│   └── _next/
├── scripts/
│   ├── build-frontend.sh   # 前端构建脚本 (Linux/Mac)
│   └── build-frontend.ps1  # 前端构建脚本 (Windows)
├── requirements.txt        # 核心依赖 (必需)
├── requirements-vector.txt # 向量检索 (可选)
└── requirements-dev.txt    # 开发工具 (可选)
```

````

---

## 🔧 技术栈说明

### 为什么选择轻量化方案?

| 组件       | 原方案    | 轻量化方案            | 理由                       |
| ---------- | --------- | --------------------- | -------------------------- |
| 数据库     | Postgres  | SQLite                | 零配置,单文件,易备份       |
| 缓存       | Redis     | 内存 dict + TTL       | 本地单用户无需独立缓存服务 |
| 向量检索   | pgvector  | sentence-transformers (可选) | 降级为文本匹配,降低门槛 |
| Agent 编排 | LangGraph | 自研状态机            | 减少依赖,更灵活            |
| 前端部署   | 独立服务  | 预构建 + StaticFiles   | 用户无需 Node.js       |

### 优势

✅ **零配置**: 无需安装数据库服务
✅ **单文件数据库**: 所有数据在 `council.db`,直接复制即可备份
✅ **跨平台**: Windows/Mac/Linux 完全兼容
✅ **易于分发**: 用户只需 `pip install` + 一行命令
✅ **可迁移**: 后续需要时可平滑迁移到 Postgres
✅ **优雅降级**: 无向量检索也能正常使用

### 局限性

⚠️ 不支持高并发 (但本地使用完全够用)
⚠️ 向量检索性能略低于专业 Vector DB (MVP 阶段可接受)

---

## 🗄️ 数据库说明

### SQLite 自动初始化

首次运行 `python main.py` 时,系统会自动:

1. 创建 `backend/data/` 目录
2. 初始化 `council.db` 数据库文件
3. 创建所有必需的表和索引
4. 无需任何手动操作

### 数据备份

```bash
# 备份数据库
cp backend/data/council.db council-backup-$(date +%Y%m%d).db

# 恢复数据库
cp council-backup-20260408.db backend/data/council.db
````

就这么简单!所有用户数据、议会记录、席位状态都在一个文件里。

---

## ⚙️ 配置说明

### 环境变量 (.env)

```bash
# LLM 配置 (必需)
FAST_MODEL_API_KEY=your-api-key
FAST_MODEL_ENDPOINT=https://api.example.com
STRONG_MODEL_API_KEY=your-api-key
STRONG_MODEL_ENDPOINT=https://api.example.com

# 服务配置 (可选,有默认值)
HOST=127.0.0.1
PORT=8000
AUTO_OPEN_BROWSER=true

# 数据库 (可选,SQLite 自动创建)
# DATABASE_URL=sqlite:///./backend/data/council.db
```

### 最小配置

你只需要配置 LLM API Key 就能运行:

```bash
FAST_MODEL_API_KEY=xxx
STRONG_MODEL_API_KEY=xxx
```

其他所有配置都有合理的默认值。

---

## 🔍 开发模式

### 后端开发

```bash
# 启动开发服务器 (热重载)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 访问 API 文档
open http://127.0.0.1:8000/docs
```

### 前端开发

```bash
# 启动 Next.js 开发服务器
cd frontend
npm install
npm run dev

# 访问前端
open http://localhost:3000
```

### 前后端联调

开发时前后端可以分开启动:

- 后端: `localhost:8000`
- 前端: `localhost:3000` (配置 API 代理到 8000)

生产构建时,前端会打包到 `frontend-dist/`,由 FastAPI 统一服务。

---

## 📦 生产构建

### 开发者发布流程

```bash
# 1. 构建前端
cd frontend
npm run build
# 构建产物输出到 ../frontend-dist/

# 2. 测试构建产物
cd ../backend
python main.py
# 访问 http://localhost:8000 验证

# 3. 提交
git add frontend-dist/
git commit -m "build: 更新前端"
git push
```

### 用户使用

用户**无需构建**,直接使用预构建产物:

```bash
pip install -r requirements.txt
python main.py
# 完成!
```

---

## 🐛 常见问题

### Q: 启动后浏览器没有自动打开?

A: 检查 `.env` 中的 `AUTO_OPEN_BROWSER=true`,或手动访问 `http://localhost:8000`

### Q: 数据库文件在哪?

A: `backend/data/council.db`,首次运行时自动创建

### Q: 如何查看数据库内容?

A: 使用任何 SQLite 客户端工具:

```bash
# 命令行
sqlite3 backend/data/council.db

# 或使用 GUI 工具如 DB Browser for SQLite
```

### Q: 可以在服务器上部署吗?

A: 可以,但需要注意:

- SQLite 适合小规模使用 (< 100 并发)
- 如果需要高并发,建议迁移到 Postgres
- 数据迁移工具后续会提供

### Q: 如何升级数据库结构?

A: 使用 Alembic 管理数据库迁移:

```bash
alembic upgrade head
```

---

## 🔄 从 Postgres 迁移 (未来)

如果需要迁移到 Postgres:

1. 导出 SQLite 数据
2. 运行迁移脚本
3. 更新 `.env` 中的 `DATABASE_URL`
4. 重启服务

迁移工具会在需要时开发。

---

## ⚡ 性能对比

### 安装时间

| 方案                    | 安装时间   | 说明             |
| ----------------------- | ---------- | ---------------- |
| 原方案 (Postgres+Redis) | 10-15 分钟 | 需安装数据库服务 |
| 轻量化方案 (基础)       | 30-60 秒   | 仅核心依赖       |
| 轻量化方案 (增强)       | 3-5 分钟   | 含向量检索       |

### 启动时间

| 方案       | 启动时间 | 说明         |
| ---------- | -------- | ------------ |
| 原方案     | 30-60 秒 | 等待多个服务 |
| 轻量化方案 | 5-10 秒  | 单进程启动   |

### 内存占用

| 方案              | 内存占用  | 说明       |
| ----------------- | --------- | ---------- |
| 原方案            | 500MB-1GB | 多个服务   |
| 轻量化方案 (基础) | 100-200MB | 仅 FastAPI |
| 轻量化方案 (增强) | 400-600MB | 含向量模型 |

---

## 📞 获取帮助

- 查看 API 文档: `http://localhost:8000/docs`
- 查看日志: 终端输出
- 提交 Issue: GitHub Issues

---

**最后更新**: 2026-04-08  
**维护者**: 开发团队
