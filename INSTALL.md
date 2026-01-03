# 安装指南

## 快速安装

### 方法 1: 使用 python -m pip（推荐）

```bash
# 激活你的 conda 环境（如果有）
conda activate your_env

# 进入项目目录
cd /jet/home/xma8/LLM-Ref-Check

# 安装依赖
python -m pip install -r requirements.txt
```

### 方法 2: 使用 pip（如果确定环境正确）

```bash
pip install -r requirements.txt
```

## 为什么使用 python -m pip？

当使用 conda 环境时，直接使用 `pip` 可能会指向系统的 pip（例如 Python 3.12），而不是 conda 环境中的 pip（例如 Python 3.10）。使用 `python -m pip` 可以确保使用当前 Python 解释器对应的 pip。

## 验证安装

安装完成后，运行以下命令验证：

```bash
python -c "import bibtexparser; import arxiv; print('✅ 安装成功！')"
```

## 常见问题

### Q: ModuleNotFoundError: No module named 'bibtexparser'

**原因**: 包安装到了错误的 Python 环境。

**解决方法**:
1. 确认已激活正确的 conda 环境
2. 使用 `python -m pip install -r requirements.txt` 而不是 `pip install`
3. 检查 Python 路径: `which python` 应该指向 conda 环境的 Python

### Q: 如何确认包安装位置？

```bash
# 检查 Python 路径
which python

# 检查包安装位置
python -m pip show bibtexparser
```

## 依赖列表

- `bibtexparser>=1.4.0` - BibTeX 文件解析
- `requests>=2.31.0` - HTTP 请求
- `arxiv>=2.1.0` - ArXiv API 客户端
- `python-dateutil>=2.8.2` - 日期处理
- `tqdm>=4.66.0` - 进度条显示
