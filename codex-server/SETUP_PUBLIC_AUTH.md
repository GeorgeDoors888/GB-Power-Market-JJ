# 🔐 Setup Guide: Public Port + Authentication

Follow these steps **in your Codespace** to make your server publicly accessible with security.

---

## 📋 Step-by-Step Instructions

### Step 1: Stop Current Server

In your Codespace terminal where the server is running:
```bash
# Press Ctrl+C to stop the current server
```

---

### Step 2: Update to Secure Server

```bash
# Copy the secure version
cp codex_server_secure.py codex_server.py

# Restart server
python codex_server.py
```

**🔑 IMPORTANT:** When the server starts, it will print your API token. **COPY IT AND SAVE IT!**

It will look like:
```
🔑 Your API Token (SAVE THIS!):
   codex_abc123xyz789...
```

---

### Step 3: Make Port Public

1. Click **"PORTS"** tab (bottom panel in VS Code)
2. Find port **8000** in the list
3. **Right-click** on port 8000
4. Select **"Port Visibility: Public"**
5. **Copy the URL** (click the globe icon or right-click → "Copy Local Address")

Your URL will look like:
```
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev
```

---

### Step 4: Test Authentication

In a **new terminal** in your Codespace (or from your Mac):

```bash
# Save your token (replace with actual token from Step 2)
export TOKEN="codex_abc123xyz789..."

# Test health check (no auth required)
curl https://[your-url]/health

# Test authenticated request
curl -X POST https://[your-url]/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello Secure World!\")", "language": "python"}'
```

Expected response:
```json
{
  "output": "Hello Secure World!\n",
  "error": null,
  "exit_code": 0,
  "execution_time": 0.023456,
  "timestamp": "2025-11-02 18:30:00"
}
```

---

## 🤖 Step 5: Connect to ChatGPT

### Method A: Simple (Tell ChatGPT in Conversation)

In ChatGPT, say:
```
I have a code execution server at:
URL: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev
Token: Bearer codex_abc123xyz789...

Please execute this Python code: print("Hello from ChatGPT!")

Use this curl command format:
curl -X POST [URL]/execute \
  -H "Authorization: Bearer [TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_CODE", "language": "python"}'
```

### Method B: Custom GPT Action (Advanced)

1. Go to ChatGPT → Settings → "My GPTs"
2. Create new GPT
3. Add this OpenAPI schema:

```yaml
openapi: 3.0.0
info:
  title: Codex Server
  version: 1.0.0
servers:
  - url: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev
paths:
  /execute:
    post:
      summary: Execute code
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: string
                language:
                  type: string
                  enum: [python, javascript]
                timeout:
                  type: integer
      responses:
        '200':
          description: Success
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
```

4. In Authentication settings:
   - Type: "API Key"
   - Header name: "Authorization"
   - Value: "Bearer codex_abc123xyz789..." (your actual token)

---

## 🧪 Testing Checklist

- [ ] Server restarted with authentication
- [ ] API token copied and saved
- [ ] Port 8000 set to Public visibility
- [ ] Public URL copied
- [ ] Health check works: `curl https://[url]/health`
- [ ] Authenticated request works (with token)
- [ ] Unauthenticated request fails (without token)
- [ ] ChatGPT can execute code

---

## 🔒 Security Features Enabled

✅ **Bearer Token Authentication** - All /execute requests require valid token
✅ **Forbidden Patterns** - Blocks dangerous imports (os, sys, subprocess)
✅ **Timeout Enforcement** - Maximum 10 seconds per execution
✅ **Input Validation** - Code is validated before execution
✅ **Logging** - All requests are logged
✅ **Public Health Check** - /health endpoint doesn't require auth

---

## 💰 Cost Reminder

- **2-core Codespace:** $0.18/hour
- **Free tier:** 60 hours/month (120 core-hours)
- **Auto-stop:** 30 minutes of inactivity
- **Current usage:** Check at https://github.com/settings/billing

---

## 🚨 Important Notes

### Your Token Security:
- ✅ **DO:** Save your token securely
- ✅ **DO:** Share only with ChatGPT or trusted services
- ❌ **DON'T:** Commit token to git
- ❌ **DON'T:** Share publicly

### If Token Compromised:
```bash
# Stop server (Ctrl+C)
# Set new token
export CODEX_API_TOKEN="codex_new_token_here"
# Restart server
python codex_server.py
```

### Port Visibility:
- **Public:** Anyone can access (but needs token for /execute)
- **Private:** Only accessible within Codespace
- Recommendation: Keep public with token auth

---

## 📋 Quick Reference

### Your Setup:
```
Codespace: super-duper-engine-wr46657556g6f5jpq
Port: 8000
Visibility: Public (you'll set this)
Auth: Bearer token (generated on startup)
```

### Test Commands:
```bash
# Health (no auth)
curl https://[your-url]/health

# Execute Python (with auth)
curl -X POST https://[your-url]/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "print(2+2)", "language": "python"}'

# Execute JavaScript (with auth)
curl -X POST https://[your-url]/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "console.log(2+2)", "language": "javascript"}'
```

---

## ❓ Troubleshooting

### "401 Unauthorized"
→ Check your Authorization header format: `Authorization: Bearer YOUR_TOKEN`

### "Port not found"
→ Restart server, check PORTS tab

### "Connection refused"
→ Make sure port visibility is "Public"

### "Invalid token"
→ Copy the token exactly as printed on server startup

---

## ✅ Success Checklist

When everything is working:
- ✅ Server shows API token on startup
- ✅ Port 8000 is Public in PORTS tab
- ✅ Health check returns 200 OK
- ✅ Authenticated requests work
- ✅ Unauthenticated requests fail with 401
- ✅ ChatGPT can execute code via your server

---

**Ready to set this up? Follow the steps above in your Codespace!** 🚀
