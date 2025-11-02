# 🔧 Fix Codespace 401 Error - Step by Step

## 🎯 Problem Identified
- Local server works ✅
- Public URL returns 401 with `WWW-Authenticate: tunnel` ❌
- This is a **Codespaces tunnel authentication issue**, not your app

---

## 🚀 Solution: Follow These Steps EXACTLY

### Terminal A: Restart Server with Fixed Token

**In your Codespace, stop the current server (Ctrl+C), then run:**

```bash
cd /workspaces/overarch-jibber-jabber/codex-server
source .venv/bin/activate

# Set the token as environment variable
export CODEX_API_TOKEN="codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Start server in background with logging
nohup python codex_server_secure.py > server.log 2>&1 &

# Verify it started
ps aux | grep -E 'codex_server|uvicorn' | grep -v grep

# Check the log
sleep 2
tail -n 40 server.log
```

**Expected output in log:**
```
🔑 Your API Token (SAVE THIS!):
   codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Terminal B: Test Local Access

**Open a NEW terminal in Codespace:**

```bash
cd /workspaces/overarch-jibber-jabber/codex-server
source .venv/bin/activate

# Set variables
export TOKEN="codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
export URL="http://127.0.0.1:8000"

# Test health (no auth)
echo "=== LOCAL HEALTH ==="
curl -i "$URL/health"

# Test execute (with auth)
echo -e "\n=== LOCAL EXECUTE ==="
curl -i -X POST "$URL/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"Hello local\")","language":"python"}'
```

**Expected:**
```
HTTP/1.1 200 OK
{"status":"healthy",...}

HTTP/1.1 200 OK
{"output":"Hello local\n","error":null,"exit_code":0,...}
```

✅ If local works, continue to next step.
❌ If local fails, paste the `tail -n 80 server.log` output.

---

### Step 3: Make Port Public (Critical!)

**In Codespace UI:**

1. Click **"PORTS"** tab (bottom panel)
2. Find **port 8000**
3. **Right-click** on port 8000
4. Select **"Port Visibility" → "Public"**
5. Click the **🌐 globe icon** to open in browser

**What should happen:**
- Browser opens to your server
- You see either:
  - ✅ API documentation page (`/docs`) - GOOD!
  - ❌ Login page or 401 - Codespaces policy blocking

---

### Step 4: Test Public URL

**In Terminal B:**

```bash
# Your public URL (copy from PORTS tab)
export PUBLIC_URL="https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev"

# Test public health
echo "=== PUBLIC HEALTH ==="
curl -i "$PUBLIC_URL/health"

# Test public execute
echo -e "\n=== PUBLIC EXECUTE ==="
curl -i -X POST "$PUBLIC_URL/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"Hello public\")","language":"python"}'
```

**Possible Outcomes:**

✅ **If you get 200 OK:** Everything works! You're done!

❌ **If you get 401 with `WWW-Authenticate: tunnel`:** Codespaces is blocking external access. Go to Step 5.

---

### Step 5: Fix Tunnel Block (If Needed)

If public access is blocked, use **Option A** or **Option B**:

#### **Option A: Use Browser-Based Access**

1. Open `/docs` in browser (globe icon from PORTS tab)
2. If it loads, click "Authorize" button in Swagger UI
3. Enter: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
4. Test execute endpoint directly in browser

**For ChatGPT:** Tell ChatGPT to use the browser-accessible URL.

#### **Option B: Use ngrok (Bypasses Codespaces Tunnel)**

**In a new terminal in Codespace:**

```bash
# Install ngrok (if not already installed)
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or use snap
snap install ngrok

# Start ngrok tunnel to port 8000
ngrok http 8000
```

**ngrok will show:**
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Copy that `https://abc123.ngrok.io` URL and use it instead:**

```bash
export PUBLIC_URL="https://abc123.ngrok.io"

# Test with ngrok URL
curl -i "$PUBLIC_URL/health"

curl -i -X POST "$PUBLIC_URL/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"Hello ngrok!\")","language":"python"}'
```

This should work! ✅

---

## 📋 Diagnostic Checklist

Run these if you hit issues:

```bash
# Check if server is running
ps aux | grep codex_server | grep -v grep

# Check server logs
tail -n 80 /workspaces/overarch-jibber-jabber/codex-server/server.log

# Check port listening
lsof -i :8000

# Check port visibility in gh cli
gh codespace ports visibility --codespace super-duper-engine-wr46657556g6f5jpq
```

---

## 🎯 Quick Summary

1. **Restart server with fixed token** (Terminal A)
2. **Test local access** (Terminal B) - Should work ✅
3. **Make port public** (PORTS tab)
4. **Test public URL** (Terminal B)
5. **If 401 tunnel error:** Use ngrok (Option B)

---

## 🤖 For ChatGPT Integration

Once you have a working public URL (either Codespaces public or ngrok):

```
My code execution server:
URL: https://[your-working-url]
Token: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA

Test it with:
curl -X POST [URL]/execute \
  -H "Authorization: Bearer [TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"test\")","language":"python"}'
```

---

## ❓ Still Having Issues?

Paste these outputs:

1. `tail -n 80 server.log`
2. The `curl -i` output from public execute test
3. Whether browser `/docs` page opens successfully

I'll diagnose the exact issue!

---

**Start with Terminal A (restart server) and work through the steps!** 🚀
