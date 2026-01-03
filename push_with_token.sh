#!/bin/bash
# 使用 Personal Access Token 推送代码

echo "📤 准备推送到 GitHub..."
echo ""
echo "⚠️  需要 GitHub Personal Access Token"
echo ""
echo "如果你还没有 Token，请："
echo "1. 访问: https://github.com/settings/tokens"
echo "2. 点击 'Generate new token' -> 'Generate new token (classic)'"
echo "3. 填写:"
echo "   - Note: LLM-Ref-Check"
echo "   - Expiration: 90 days (或更长)"
echo "   - Scopes: 勾选 'repo'"
echo "4. 点击 'Generate token'"
echo "5. 复制生成的 token（只显示一次）"
echo ""
read -p "请输入你的 GitHub Personal Access Token: " token

if [ -z "$token" ]; then
    echo "❌ Token 不能为空"
    exit 1
fi

# 使用 token 配置远程仓库
git remote set-url origin https://${token}@github.com/JijiKing-Sam/LLM-Ref-Check.git

echo ""
echo "📤 正在推送..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功！"
    echo "🌐 访问: https://github.com/JijiKing-Sam/LLM-Ref-Check"
    # 移除token（安全考虑）
    git remote set-url origin https://github.com/JijiKing-Sam/LLM-Ref-Check.git
else
    echo ""
    echo "❌ 推送失败，请检查："
    echo "   1. Token 是否正确"
    echo "   2. Token 是否有 'repo' 权限"
    echo "   3. 仓库是否存在"
fi

