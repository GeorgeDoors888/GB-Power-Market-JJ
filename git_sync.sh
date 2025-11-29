#!/bin/bash
# git_sync.sh
# Automatic git sync for dashboard changes

set -e

cd ~/GB-Power-Market-JJ

echo "═══════════════════════════════════════════════════════════════════"
echo "📦 GIT SYNC - Dashboard V2"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Check if there are changes
if [[ -z $(git status -s) ]]; then
    echo "✅ No changes to commit"
    exit 0
fi

# Show changes
echo "📝 Changes detected:"
git status -s
echo ""

# Add all changes
echo "➕ Staging changes..."
git add -A

# Generate commit message
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CHANGED_FILES=$(git diff --cached --name-only | wc -l | tr -d ' ')

COMMIT_MSG="Dashboard V2 sync: $CHANGED_FILES file(s) updated - $TIMESTAMP

Auto-synced changes:
$(git diff --cached --name-only | head -10)"

# Commit
echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG"

# Push
echo "📤 Pushing to remote..."
if git push origin main 2>&1; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "✅ GIT SYNC COMPLETE"
    echo "═══════════════════════════════════════════════════════════════════"
else
    echo ""
    echo "⚠️ Push failed - check connection and try manually:"
    echo "   git push origin main"
fi
