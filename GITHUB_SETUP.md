# GitHub 上线指南

## 准备工作

### 1. 创建 GitHub 仓库

1. 登录 GitHub
2. 点击右上角 "+" -> "New repository"
3. 填写仓库信息：
   - Repository name: `LLM-Ref-Check`
   - Description: `🔍 LLM参考文献幻觉检测工具 - 验证BibTeX参考文献的真实性`
   - 选择 Public（公开）或 Private（私有）
   - **不要**初始化 README、.gitignore 或 LICENSE（我们已经有了）
4. 点击 "Create repository"

### 2. 初始化本地 Git 仓库

```bash
cd /jet/home/xma8/LLM-Ref-Check

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: LLM参考文献幻觉检测工具

- 支持BibTeX文件解析和验证
- ArXiv API集成验证
- Streamlit Web界面
- Markdown报告生成
- 命令行工具支持"
```

### 3. 连接到 GitHub 仓库

```bash
# 添加远程仓库
git remote add origin https://github.com/JijiKing-Sam/LLM-Ref-Check.git

# 或者使用 SSH（如果配置了SSH密钥）
# git remote add origin git@github.com:JijiKing-Sam/LLM-Ref-Check.git

# 验证远程仓库
git remote -v
```

### 4. 推送代码到 GitHub

```bash
# 推送主分支
git branch -M main
git push -u origin main
```

## 更新 README 中的链接

推送前，记得更新 README.md 中的 GitHub 链接：

```bash
# 用户名已更新为 JijiKing-Sam
# 如果需要修改，运行：
# sed -i 's/JijiKing-Sam/YOUR_USERNAME/g' README.md app.py
```

或者手动编辑：
- `README.md`: 用户名已设置为 `JijiKing-Sam`
- `app.py`: 第 280 行左右的 GitHub 链接

## 添加仓库描述和标签

在 GitHub 仓库页面：

1. 点击 "Settings" -> "General"
2. 在 "Topics" 中添加标签：
   - `llm`
   - `reference-checker`
   - `bibtex`
   - `arxiv`
   - `streamlit`
   - `python`
   - `academic-writing`

## 创建 Release

1. 点击 "Releases" -> "Create a new release"
2. 填写版本信息：
   - Tag: `v0.1.0`
   - Title: `v0.1.0 - Initial Release`
   - Description:
     ```
     ## 主要功能
     - ✅ BibTeX文件解析和验证
     - 🔍 ArXiv API集成
     - 📊 Markdown报告生成
     - 🌐 Streamlit Web界面
     - 💻 命令行工具支持
     ```

## 后续更新

```bash
# 添加更改
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到GitHub
git push origin main
```

## 推荐的项目结构

确保你的项目包含以下文件：

```
LLM-Ref-Check/
├── .github/
│   └── workflows/
│       └── python-package.yml    # CI/CD配置
├── .streamlit/
│   └── config.toml               # Streamlit配置
├── ref_checker/                  # 核心模块
│   ├── __init__.py
│   ├── bibtex_parser.py
│   ├── arxiv_validator.py
│   ├── validator.py
│   ├── report_generator.py
│   └── batch_processor.py
├── app.py                        # Streamlit Web界面
├── main.py                       # 命令行入口
├── requirements.txt              # 依赖列表
├── README.md                     # 项目说明
├── LICENSE                       # 许可证
├── .gitignore                    # Git忽略文件
├── DEPLOY.md                     # 部署指南
├── INSTALL.md                    # 安装指南
├── QUICKSTART.md                 # 快速开始
├── GITHUB_SETUP.md              # 本文件
├── run_web.sh                    # Web启动脚本
├── test_example.py               # 测试脚本
├── example.bib                   # 示例文件
└── test_references.bib           # 测试文件
```

## 添加徽章（可选）

在 README.md 顶部添加徽章：

```markdown
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
```

## 启用 GitHub Pages（可选）

如果需要展示文档：

1. Settings -> Pages
2. Source: 选择 `main` 分支和 `/docs` 目录
3. 创建 `docs/` 目录并添加文档

## 问题反馈

鼓励用户通过 GitHub Issues 报告问题或提出建议。
