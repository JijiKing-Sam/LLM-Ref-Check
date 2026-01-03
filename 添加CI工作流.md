# 添加 CI/CD 工作流（可选）

## 当前状态

✅ 代码已成功推送到 GitHub  
⚠️  GitHub Actions 工作流文件被暂时移除了（因为需要 `workflow` scope）

## 如果需要 CI/CD 功能

### 方法 1：添加 workflow scope 的 Token（推荐）

1. 访问：https://github.com/settings/tokens
2. 编辑现有的 token 或创建新 token
3. 在 Scopes 中勾选：
   - ✅ `repo`（完整仓库权限）
   - ✅ `workflow`（GitHub Actions 权限）
4. 更新 token

然后推送工作流文件：

```bash
cd /jet/home/xma8/LLM-Ref-Check

# 恢复工作流文件
git checkout HEAD~1 -- .github/workflows/python-package.yml
git add .github/workflows/python-package.yml
git commit -m "Add CI/CD workflow"
git push origin main
```

### 方法 2：直接在 GitHub 上添加

1. 访问：https://github.com/JijiKing-Sam/LLM-Ref-Check
2. 点击 "Add file" -> "Create new file"
3. 路径输入：`.github/workflows/python-package.yml`
4. 复制以下内容：

```yaml
name: Python Package

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
    - name: Test imports
      run: |
        python -c "import bibtexparser; import arxiv; print('✅ All imports successful')"
    - name: Test basic functionality
      run: |
        python test_example.py
```

5. 点击 "Commit new file"

## 当前工作流文件位置

工作流文件仍然在本地，位于：
- `.github/workflows/python-package.yml`

只是没有推送到 GitHub。如果需要，可以按照上面的方法添加。

