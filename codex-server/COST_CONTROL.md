# Codex Server Cost Control Guide

## 💰 Current Setup: **$0/month (FREE)**

Your Codex server runs **locally** on your Mac - no cloud costs!

---

## 🎛️ Cost Control Options

### Option 1: Start/Stop Manually (Current - FREE)
```bash
# START server (only when needed)
cd ~/Overarch\ Jibber\ Jabber/codex-server
source .venv/bin/activate
python codex_server.py &
echo $! > server.pid

# STOP server (when done)
kill $(cat server.pid)
rm server.pid
```

**Cost:** $0/month
**Control:** Full control - only runs when you start it

---

### Option 2: Auto-Start Scripts (Convenience)

#### Create start script
```bash
cat > ~/Overarch\ Jibber\ Jabber/codex-server/start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python codex_server.py &
echo $! > server.pid
echo "✅ Codex server started (PID: $(cat server.pid))"
EOF

chmod +x start.sh
```

#### Create stop script
```bash
cat > ~/Overarch\ Jibber\ Jabber/codex-server/stop.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
if [ -f server.pid ]; then
    kill $(cat server.pid) 2>/dev/null
    rm server.pid
    echo "✅ Codex server stopped"
else
    echo "❌ No server.pid found"
fi
EOF

chmod +x stop.sh
```

**Usage:**
```bash
./start.sh  # Start when needed
./stop.sh   # Stop when done
```

**Cost:** $0/month (still local)

---

### Option 3: Deploy to Cloud (Pay-per-use)

#### A. Railway.app (Recommended for hobby projects)
```bash
# Free tier: 500 hours/month, $5/month after
# Auto-sleeps after 15min inactivity

# Install Railway CLI
npm install -g @railway/cli

# Deploy
cd ~/Overarch\ Jibber\ Jabber/codex-server
railway login
railway init
railway up
```

**Cost:** 
- Free tier: 500 hours/month (~16 hours/day)
- Paid: $5/month for always-on
- **Auto-sleeps when idle = saves money**

#### B. Render.com
```bash
# Free tier with auto-sleep after 15min
# Wakes up on first request (cold start)

# 1. Push to GitHub (already done ✅)
# 2. Go to https://render.com
# 3. Connect GitHub repo
# 4. Deploy as "Web Service"
```

**Cost:**
- Free tier: Unlimited deploys
- Auto-sleeps after 15min = **$0/month**
- Paid: $7/month for always-on

#### C. Fly.io
```bash
# 3 free VMs, auto-stop when idle

# Install Fly CLI
brew install flyctl

# Deploy
cd ~/Overarch\ Jibber\ Jabber/codex-server
flyctl launch
flyctl deploy
```

**Cost:**
- Free: 3 shared VMs, 160GB bandwidth
- Auto-scales to zero = **$0/month when idle**
- Paid: ~$5/month for dedicated resources

---

## 📊 Cloud Cost Comparison

| Provider | Free Tier | Auto-Sleep | Always-On Cost | Best For |
|----------|-----------|------------|----------------|----------|
| **Local (Current)** | ✅ Unlimited | ⚠️ Manual | $0 | Development |
| **Railway** | 500 hrs/mo | ✅ Yes (15min) | $5/mo | Quick deploy |
| **Render** | ✅ Unlimited | ✅ Yes (15min) | $7/mo | No credit card |
| **Fly.io** | 3 VMs | ✅ Scale to zero | $5/mo | Global edge |
| **AWS Lambda** | 1M requests | ✅ Per-request | $0.20/1M | Serverless |

---

## 🎯 Recommended Strategy

### For Development (Current)
```bash
# Stay local - FREE
# Start server when coding
./start.sh

# Stop when done
./stop.sh
```

### For Production (Later)
```bash
# Use Railway or Render with auto-sleep
# Cost: $0 if usage < 500 hours/month
# Automatically handles:
# - Sleep after 15min idle
# - Wake on first request
# - HTTPS certificates
# - Domain names
```

---

## 🔍 Monitor Costs

### Track Local Server Uptime
```bash
# Check if server is running
ps aux | grep codex_server.py | grep -v grep

# Check how long it's been running
ps -p $(cat server.pid) -o etime= 2>/dev/null || echo "Not running"
```

### Track Cloud Costs (if deployed)
```bash
# Railway
railway status
railway logs

# Render
# Check dashboard at https://dashboard.render.com

# Fly.io
flyctl status
flyctl scale show
```

---

## 💡 Cost Optimization Tips

### 1. Use Auto-Sleep
- Server sleeps after 15min inactivity
- Wakes up on first request (2-3 sec delay)
- **Saves 95% of idle time costs**

### 2. Set Resource Limits
```python
# In codex_server.py
MAX_EXECUTION_TIME = 10  # seconds
MAX_MEMORY = 256  # MB
MAX_REQUESTS_PER_HOUR = 100
```

### 3. Monitor Usage
```bash
# Log all executions
@app.post("/execute")
async def execute_code(request: CodeRequest):
    logging.info(f"Execution: {request.language}, {len(request.code)} chars")
    # ... rest of code
```

### 4. Use Caching
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def execute_cached(code_hash: str):
    # Cache identical code executions
    pass
```

---

## 🚨 Prevent Unexpected Costs

### Set Up Alerts
```bash
# Railway: Set spending limit in dashboard
# → Settings → Usage → Set limit to $5

# AWS: Set billing alerts
# → CloudWatch → Billing → Create alarm

# Render: Monitor in dashboard
# → No auto-billing, upgrade manually
```

### Kill Switch
```bash
# Emergency stop script
cat > ~/kill_all_servers.sh << 'EOF'
#!/bin/bash
pkill -f codex_server.py
echo "✅ All Codex servers stopped"
EOF

chmod +x ~/kill_all_servers.sh
```

---

## 📈 Current Status

**Your Setup:**
- ✅ Running locally (FREE)
- ✅ Manual start/stop (full control)
- ✅ ~16MB memory (minimal impact)
- ✅ 0.0% CPU when idle
- ✅ No cloud costs

**Recommendation:** Stay local until you need:
- 24/7 availability
- Public internet access
- Multiple users
- Higher reliability

Then deploy to Railway/Render with auto-sleep for $0-5/month.

---

## 🎛️ Quick Commands

```bash
# Check if running
ps aux | grep codex_server.py | grep -v grep

# Check resource usage
ps aux | grep codex_server.py | awk '{print "CPU: "$3"% | Memory: "$4"% | "$11}'

# Stop immediately
pkill -f codex_server.py

# Check port
lsof -i :8000

# View logs (if using systemd)
sudo journalctl -u codex-server -f
```
