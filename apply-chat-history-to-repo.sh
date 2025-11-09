#!/bin/bash
# Apply Chat History System to All Repositories
# Run this in any repository to enable chat history logging

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_REPO="${1:-.}"

echo "🔧 Applying Chat History System to: $TARGET_REPO"
echo ""

# Create chat-history directory
mkdir -p "$TARGET_REPO/chat-history"
echo "✅ Created chat-history/ directory"

# Copy README
cp "$SCRIPT_DIR/chat-history/README.md" "$TARGET_REPO/chat-history/README.md" 2>/dev/null || echo "ℹ️  README template not copied"

# Create .vscode directory if needed
mkdir -p "$TARGET_REPO/.vscode"

# Add or update VS Code settings
SETTINGS_FILE="$TARGET_REPO/.vscode/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    echo "⚠️  VS Code settings.json already exists"
    echo "   Please manually add these settings:"
    echo ""
    cat << 'EOF'
{
  "github.copilot.chat.exportHistory": true,
  "github.copilot.chat.historyLocation": "${workspaceFolder}/chat-history",
  "workbench.localHistory.enabled": true
}
EOF
else
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "github.copilot.chat.exportHistory": true,
  "github.copilot.chat.historyLocation": "${workspaceFolder}/chat-history",
  "files.autoSave": "afterDelay",
  "workbench.localHistory.enabled": true
}
EOF
    echo "✅ Created .vscode/settings.json"
fi

# Copy save script
cp "$SCRIPT_DIR/save-chat-session.sh" "$TARGET_REPO/save-chat-session.sh" 2>/dev/null && chmod +x "$TARGET_REPO/save-chat-session.sh"
echo "✅ Copied save-chat-session.sh script"

# Copy guide
cp "$SCRIPT_DIR/CHAT_HISTORY_GUIDE.md" "$TARGET_REPO/CHAT_HISTORY_GUIDE.md" 2>/dev/null
echo "✅ Copied CHAT_HISTORY_GUIDE.md"

# Update .gitignore if it exists
if [ -f "$TARGET_REPO/.gitignore" ]; then
    if ! grep -q "chat-history" "$TARGET_REPO/.gitignore"; then
        cat >> "$TARGET_REPO/.gitignore" << 'EOF'

# Chat history - Keep in git for knowledge preservation
# Uncomment below to make chat history local-only
# chat-history/*.md
EOF
        echo "✅ Updated .gitignore"
    else
        echo "ℹ️  .gitignore already has chat-history entry"
    fi
fi

echo ""
echo "🎉 Chat History System Applied!"
echo ""
echo "📝 Next steps:"
echo "   1. Review: $TARGET_REPO/CHAT_HISTORY_GUIDE.md"
echo "   2. Save chats with: ./save-chat-session.sh"
echo "   3. Commit: git add . && git commit -m 'Add chat history system'"
echo ""
