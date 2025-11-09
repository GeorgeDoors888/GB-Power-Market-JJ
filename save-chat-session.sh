#!/bin/bash
# Save GitHub Copilot Chat Session
# Usage: ./save-chat-session.sh [optional-description]

CHAT_DIR="chat-history"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
DESCRIPTION="${1:-session}"
FILENAME="${CHAT_DIR}/chat_${TIMESTAMP}_${DESCRIPTION}.md"

mkdir -p "$CHAT_DIR"

echo "📝 Creating chat history log: $FILENAME"
echo ""
echo "To save your chat:"
echo "1. Copy the entire conversation from VS Code Copilot Chat"
echo "2. Paste it into the file that's about to open"
echo "3. Save and close the editor"
echo ""
echo "Press Enter to open editor..."
read

cat > "$FILENAME" << 'EOF'
# GitHub Copilot Chat History

**Date:** $(date +%Y-%m-%d)  
**Time:** $(date +%H:%M:%S)  
**Project:** GB Power Market JJ  
**Repository:** GeorgeDoors888/GB-Power-Market-JJ  

---

## Session Summary

### Topics Discussed
- [Add topics here]

### Key Actions
- [Add actions here]

### Files Modified
- [Add files here]

---

## Conversation Log

[Paste your chat conversation here]

---

## Follow-up Items

- [ ] [Add follow-up tasks here]

---

**Session End:** $(date +%Y-%m-%d %H:%M:%S)
EOF

# Open in default editor
if command -v code &> /dev/null; then
    code "$FILENAME"
elif command -v nano &> /dev/null; then
    nano "$FILENAME"
else
    vi "$FILENAME"
fi

echo "✅ Chat history saved to: $FILENAME"
echo ""
echo "💡 Tip: Add this to your workflow:"
echo "   git add chat-history/"
echo "   git commit -m 'Add chat session: $DESCRIPTION'"
