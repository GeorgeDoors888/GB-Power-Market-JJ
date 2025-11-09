# GitHub Copilot Chat History

This directory contains logs of all GitHub Copilot chat conversations.

## Structure

- Each chat session is saved with timestamp: `chat_YYYY-MM-DD_HHmmss.md`
- Sessions are automatically created when using the `/save-chat` command
- Manual exports can be added here as well

## Usage

### To Save Current Chat
1. In Copilot Chat, type: `/save-chat`
2. Or manually copy conversation and save here

### To Review Past Chats
```bash
# List all chat sessions
ls -lt chat-history/

# Search for specific topic
grep -r "topic name" chat-history/

# View most recent chat
cat chat-history/$(ls -t chat-history/*.md | head -1)
```

## Backup

Chat histories are:
- ✅ Stored locally in this folder
- ✅ Backed up to Git (if committed)
- ✅ Searchable via grep/search tools

## Privacy Note

Chat histories may contain:
- Code snippets
- API keys (be careful!)
- Project-specific information
- Personal notes

Review before committing to public repositories.
