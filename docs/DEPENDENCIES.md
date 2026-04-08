# 依赖说明

## 📦 依赖分层

本项目采用分层依赖策略,用户可根据需求选择安装:

### 1. 核心依赖 (必需)

**文件**: `requirements.txt`  
**大小**: ~50MB  
**安装**: `pip install -r requirements.txt`

包含:

- FastAPI - Web 框架
- SQLite - 数据库 (Python 内置,无需额外安装)
- 基础缓存 - 内存缓存
- LLM 调用 - OpenAI/LiteLLM

**功能**:
✅ 完整的议会功能  
✅ 基础文本检索  
✅ 用户数据持久化  
✅ 风铃系统  
✅ 票型统计

---

### 2. 向量检索增强 (可选,推荐)

**文件**: `requirements-vector.txt`  
**大小**: ~300MB (含 torch)  
**安装**: `pip install -r requirements-vector.txt`

包含:

- sentence-transformers - 向量模型
- torch - 深度学习框架
- numpy, scipy - 数值计算

**功能增强**:
✨ 高精度相似案例检索  
✨ 语义搜索 (而非关键词匹配)  
✨ 更好的用户体验

**不安装的影响**:
⚠️ 自动降级为文本匹配  
⚠️ 检索精度略低  
✅ 基础功能完全正常

---

### 3. 开发工具 (可选)

**文件**: `requirements-dev.txt`  
**大小**: ~20MB  
**安装**: `pip install -r requirements-dev.txt`

包含:

- pytest - 测试框架
- black, ruff - 代码格式化
- alembic - 数据库迁移
- mypy - 类型检查

**用途**: 仅开发者需要,用户无需安装

---

## 🚀 安装建议

### 普通用户

```bash
# 最小安装 (推荐开始)
pip install -r requirements.txt

# 如果想要更好的检索体验
pip install -r requirements-vector.txt
```

### 开发者

```bash
# 完整安装
pip install -r requirements.txt
pip install -r requirements-vector.txt
pip install -r requirements-dev.txt
```

---

## 📊 依赖对比

| 依赖包                  | 大小   | 安装时间 | 必需 | 功能影响 |
| ----------------------- | ------ | -------- | ---- | -------- |
| requirements.txt        | ~50MB  | 30-60秒  | ✅   | 核心功能 |
| requirements-vector.txt | ~300MB | 3-5分钟  | ❌   | 检索精度 |
| requirements-dev.txt    | ~20MB  | 15-30秒  | ❌   | 开发工具 |

---

## 🔄 降级策略

### 向量检索降级

```python
# 自动检测
try:
    from sentence_transformers import SentenceTransformer
    HAS_VECTOR = True
except ImportError:
    HAS_VECTOR = False

# 使用
if HAS_VECTOR:
    # 高精度向量检索
    results = vector_search(query)
else:
    # 降级为文本匹配
    results = text_search(query)
```

### 用户体验

**无向量检索时**:

```
启动提示:
⚠️  向量检索未安装,使用文本匹配模式
💡 安装增强包: pip install -r requirements-vector.txt

功能:
✅ 议会辩论 - 正常
✅ 风铃系统 - 正常
✅ 数据存储 - 正常
⚠️ 相似案例检索 - 精度略低 (关键词匹配)
```

**有向量检索时**:

```
启动提示:
✅ 向量检索已启用

功能:
✅ 所有功能正常
✨ 相似案例检索 - 高精度 (语义搜索)
```

---

## 🐛 常见问题

### Q: 不安装向量检索会影响使用吗?

A: **不会!** 系统会自动降级:

- 基础功能完全正常
- 只是相似案例检索使用关键词匹配而非语义搜索
- 随时可以安装: `pip install -r requirements-vector.txt`

### Q: 向量模型从哪里下载?

A: 首次使用时自动从 HuggingFace 下载:

- 模型: `all-MiniLM-L6-v2`
- 大小: ~80MB
- 来源: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

### Q: 安装 torch 失败怎么办?

A: 可以尝试:

```bash
# 使用 CPU 版本 (更小)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 或使用预编译版本
pip install torch torchvision torchaudio
```

### Q: 如何检查已安装的依赖?

A:

```bash
pip list

# 或检查特定包
pip show sentence-transformers
```

---

## 📝 依赖更新

### 开发者更新依赖后

1. 更新对应的 `requirements-*.txt` 文件
2. 测试降级逻辑是否正常
3. 更新本文档
4. 提交到 Git

### 用户更新依赖

```bash
# 更新核心依赖
pip install -r requirements.txt --upgrade

# 更新向量检索
pip install -r requirements-vector.txt --upgrade
```

---

**最后更新**: 2026-04-08  
**维护者**: 开发团队
