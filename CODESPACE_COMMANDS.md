# Quick Commands for Codespace

## You are here:
```
/workspaces/overarch-jibber-jabber
```

## Files are in:
```
/workspaces/overarch-jibber-jabber/codex-server/
```

## Run these commands:

```bash
# 1. Go to codex-server directory
cd codex-server

# 2. Make sure you're in the right place
pwd
# Should show: /workspaces/overarch-jibber-jabber/codex-server

# 3. List files to confirm secure server is there
ls -lh *.py

# 4. Start the secure server
python codex_server_secure.py
```

## Expected Output:

You'll see:
```
============================================================
🚀 Codex Server Starting...
============================================================

🔑 Your API Token (SAVE THIS!):
   codex_abc123xyz789...

📋 How to use:
   Include this header in all requests:
   Authorization: Bearer codex_abc123xyz789...

🧪 Test with curl:
   curl -X POST http://localhost:8000/execute \
     -H "Authorization: Bearer codex_abc123xyz789..." \
     -H "Content-Type: application/json" \
     -d '{"code": "print(\"Hello!\")", "language": "python"}'

📖 API Documentation: http://localhost:8000/docs
============================================================

INFO:     Started server process [1234]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## ⚠️ IMPORTANT:
**COPY AND SAVE THE TOKEN** that appears after "🔑 Your API Token"!
You'll need it to authenticate with ChatGPT!
