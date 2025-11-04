#!/bin/bash
# Quick Git Push Script for ChatGPT Collaboration

echo "🚀 Push to GitHub"
echo "================"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not a git repository!"
    echo ""
    echo "Run: git init"
    exit 1
fi

# Check GitHub CLI authentication
if ! gh auth status > /dev/null 2>&1; then
    echo "❌ GitHub CLI not authenticated!"
    echo ""
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub authenticated as: $(gh api user --jq .login)"
echo ""

# Show current status
echo "📊 Current changes:"
git status --short
echo ""

# Ask for commit message if not provided
if [ -z "$1" ]; then
    read -p "💬 Commit message: " MESSAGE
else
    MESSAGE="$1"
fi

# Confirm
read -p "Push these changes? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🔄 Processing..."

# Add all changes
git add .
echo "  ✅ Files staged"

# Commit
git commit -m "$MESSAGE"
if [ $? -eq 0 ]; then
    echo "  ✅ Changes committed"
else
    echo "  ℹ️  No new changes to commit"
fi

# Push
git push
if [ $? -eq 0 ]; then
    echo "  ✅ Pushed to GitHub"
    echo ""
    echo "🎉 Done! View at:"
    gh repo view --web
else
    echo "  ❌ Push failed"
    echo ""
    echo "Try:"
    echo "  git push -u origin main"
fi
