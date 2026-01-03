#!/bin/bash
# GitHub 仓库初始化脚本

echo "🚀 开始初始化 GitHub 仓库..."

# 检查是否已初始化 Git
if [ -d .git ]; then
    echo "⚠️  Git 仓库已存在"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "📦 初始化 Git 仓库..."
    git init
fi

# 添加所有文件
echo "📝 添加文件到 Git..."
git add .

# 提交
echo "💾 提交更改..."
git commit -m "Initial commit: LLM参考文献幻觉检测工具

- 支持BibTeX文件解析和验证
- ArXiv API集成验证
- Streamlit Web界面
- Markdown报告生成
- 命令行工具支持"

# 检查远程仓库
if git remote | grep -q origin; then
    echo "⚠️  远程仓库已存在"
    git remote -v
    read -p "是否更新远程仓库URL？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote set-url origin https://github.com/JijiKing-Sam/LLM-Ref-Check.git
    fi
else
    echo "🔗 添加远程仓库..."
    git remote add origin https://github.com/JijiKing-Sam/LLM-Ref-Check.git
fi

# 设置主分支
git branch -M main

echo ""
echo "✅ Git 仓库初始化完成！"
echo ""
echo "📋 下一步操作："
echo "1. 在 GitHub 上创建仓库: https://github.com/new"
echo "   仓库名: LLM-Ref-Check"
echo "   不要初始化 README、.gitignore 或 LICENSE"
echo ""
echo "2. 推送代码到 GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. 或者运行完整推送（如果仓库已创建）:"
read -p "是否现在推送？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 推送到 GitHub..."
    git push -u origin main
    if [ $? -eq 0 ]; then
        echo "✅ 推送成功！"
        echo "🌐 访问: https://github.com/JijiKing-Sam/LLM-Ref-Check"
    else
        echo "❌ 推送失败，请确保："
        echo "   1. GitHub 仓库已创建"
        echo "   2. 已配置 GitHub 认证"
        echo "   3. 有推送权限"
    fi
fi
