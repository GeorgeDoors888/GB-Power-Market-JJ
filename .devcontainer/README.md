# 🚀 Running Your Codex Server in GitHub Codespaces

## 💰 **Cost: FREE for 60 hours/month** (2-core machine)

Your Codex Server is now configured to run in GitHub Codespaces!

---

## 🎯 **Quick Start**

### 1️⃣ Launch Codespace

**From GitHub Website:**
1. Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber
2. Click **"Code"** button (green)
3. Click **"Codespaces"** tab
4. Click **"Create codespace on main"**
5. Wait 1-2 minutes for setup

**From GitHub CLI:**
```bash
gh codespace create --repo GeorgeDoors888/overarch-jibber-jabber
```

**From VS Code Desktop:**
1. Install "GitHub Codespaces" extension
2. Press `Cmd+Shift+P`
3. Type "Codespaces: Create New Codespace"
4. Select your repo

---

### 2️⃣ Start Server

Once in Codespace, run:

```bash
cd codex-server
source .venv/bin/activate
python codex_server.py
```

Or use the convenience script:
```bash
cd codex-server
./server-start.sh
```

---

### 3️⃣ Access Server

**In Codespace:**
- Click "PORTS" tab (bottom panel)
- Find port 8000
- Click globe icon 🌐 to open in browser
- Your URL: `https://[codespace-name]-8000.app.github.dev`

**Test it:**
```bash
curl https://[your-codespace-url]/health
```

---

## 💰 **Cost Control**

### Free Tier
- **120 core-hours/month FREE**
- **2-core machine = 60 hours/month FREE**
- **4-core machine = 30 hours/month FREE**

### Auto-Stop Configuration ✅
- Automatically stops after **30 minutes of inactivity**
- Saves money when you're not actively coding
- Starts instantly when you reconnect

### Manual Control
```bash
# Stop Codespace (via GitHub UI)
1. Go to https://github.com/codespaces
2. Click [...] next to your Codespace
3. Click "Stop codespace"

# Or use CLI
gh codespace stop --codespace [name]

# Delete when not needed for a while
gh codespace delete --codespace [name]
```

### View Usage & Costs
- Check: https://github.com/settings/billing
- Click "Codespaces"
- See current usage in core-hours

### Set Spending Limit
- Go to: https://github.com/settings/billing/spending_limit
- Set limit (e.g., $5/month)
- Codespaces stop when limit reached

---

## 📊 **Cost Examples**

### Scenario 1: Casual Development
```
Usage: 2 hours/day, weekdays only
Machine: 2-core
Core-hours: 2 × 10 days = 20 core-hours/month
Cost: $0 (within free 120 core-hours)
```

### Scenario 2: Active Development
```
Usage: 3 hours/day, 5 days/week
Machine: 2-core
Core-hours: 2 × 60 hours = 120 core-hours/month
Cost: $0 (exactly at free limit)
```

### Scenario 3: Heavy Use
```
Usage: 5 hours/day, 7 days/week
Machine: 2-core
Core-hours: 2 × 150 hours = 300 core-hours/month
Billable: 300 - 120 = 180 core-hours
Cost: 180 × $0.09 = $16.20/month
```

### Scenario 4: Always-On (Not Recommended)
```
Usage: 24/7
Machine: 2-core
Core-hours: 2 × 720 hours = 1,440 core-hours/month
Billable: 1,440 - 120 = 1,320 core-hours
Cost: 1,320 × $0.09 = $118.80/month
❌ Use Railway/Render instead for always-on ($5-7/month)
```

---

## 🔧 **What's Configured**

### Auto-Installed
- ✅ Python 3.14
- ✅ Node.js (latest LTS)
- ✅ Git
- ✅ VS Code extensions (Python, Pylance, Black formatter)
- ✅ All Codex Server dependencies

### Auto-Configured
- ✅ Port 8000 forwarded automatically
- ✅ Virtual environment created
- ✅ Dependencies installed
- ✅ 30-minute idle timeout

### What You Get
- ✅ Full VS Code in browser
- ✅ Access from any device (Mac, iPad, phone)
- ✅ Consistent environment every time
- ✅ GitHub integration (push/pull seamlessly)
- ✅ Terminal access
- ✅ File explorer
- ✅ Extensions

---

## 🌐 **Access from Different Devices**

### From Web Browser (Any Device)
```
1. Go to: https://github.com/codespaces
2. Click on your Codespace
3. Full VS Code in browser!
```

### From iPad/Tablet
```
1. Install "GitHub" app
2. Navigate to your repo
3. Tap "Code" → "Codespaces"
4. Open in browser
```

### From VS Code Desktop
```
1. Install "GitHub Codespaces" extension
2. Cmd+Shift+P → "Codespaces: Connect to Codespace"
3. Select your Codespace
```

### From Mobile (View Only)
```
1. Go to: https://github.com/codespaces
2. View/edit files in browser
3. Limited terminal access
```

---

## 🎯 **Best Practices**

### Save Money
1. ✅ **Stop Codespace** when done for the day
2. ✅ **Delete Codespace** if not using for > 1 week
3. ✅ **Use 2-core** machine (60 free hours vs 30 for 4-core)
4. ✅ **Let auto-stop work** (30min idle)
5. ❌ **Don't leave running 24/7**

### Workflow
```bash
# Morning: Start Codespace
gh codespace create

# Work for 2-3 hours
cd codex-server && ./server-start.sh

# Test your changes
curl https://[url]/health

# Commit & push
git add .
git commit -m "Feature update"
git push

# Stop when done
# (or let it auto-stop after 30min idle)
gh codespace stop
```

---

## 📱 **Mobile Access**

### From Phone/Tablet Browser:
1. Open: https://github.com/codespaces
2. Tap your Codespace
3. Gets VS Code web interface
4. Can edit code, run terminal commands
5. Port 8000 auto-forwarded

### Test Server from Phone:
```bash
# In Codespace terminal
cd codex-server
./server-start.sh

# Click "PORTS" tab
# Click globe icon on port 8000
# Opens in new tab
# Visit: /docs for API documentation
```

---

## 🆚 **Codespaces vs Other Options**

| Feature | Codespaces | Local Mac | Railway | Render |
|---------|-----------|-----------|---------|--------|
| **Free Tier** | 60 hrs/mo | Unlimited | 500 hrs/mo | Unlimited |
| **Cost (Paid)** | $0.18/hr | $0 | $5/mo | $7/mo |
| **Access Anywhere** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Auto-Stop** | ✅ 30min | Manual | ✅ 15min | ✅ 15min |
| **Setup Time** | 2 minutes | 0 (already done) | 5 minutes | 5 minutes |
| **Always On** | ❌ Expensive | ✅ Free (when Mac on) | ✅ $5/mo | ✅ $7/mo |
| **Best For** | Dev on-the-go | Local dev | Production | Production |

---

## 🚨 **Troubleshooting**

### Port Not Forwarding?
```bash
# Check if server is running
ps aux | grep codex_server

# Check port
lsof -i :8000

# Restart server
cd codex-server && ./server-stop.sh && ./server-start.sh
```

### Dependencies Not Installed?
```bash
# Re-run setup
bash .devcontainer/setup.sh

# Or manually
cd codex-server
source .venv/bin/activate
pip install -r requirements.txt
```

### Codespace Won't Start?
```bash
# Delete and recreate
gh codespace delete --codespace [name]
gh codespace create --repo GeorgeDoors888/overarch-jibber-jabber
```

---

## 📚 **Next Steps**

### Deploy to Production
Once you've tested in Codespaces, deploy to Railway for 24/7 availability:

```bash
# In Codespace terminal
npm install -g @railway/cli
railway login
cd codex-server
railway init
railway up

# Now have both:
# - Codespaces for development ($0-18/mo)
# - Railway for production ($5/mo)
```

---

## 📞 **Support**

- **GitHub Codespaces Docs:** https://docs.github.com/codespaces
- **Check Usage:** https://github.com/settings/billing
- **Pricing Calculator:** https://github.com/pricing/calculator

---

**🎉 You're all set! Your Codex Server can now run anywhere, anytime, from any device!**

**💰 Remember: FREE for first 60 hours/month on 2-core machine**
