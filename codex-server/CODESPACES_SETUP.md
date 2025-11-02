# GitHub Codespaces Setup for Codex Server

## 💰 **Pricing: GitHub Codespaces**

### Free Tier (Generous!)
- **120 core-hours/month FREE** for personal accounts
- **2-core machine:** 60 hours/month FREE
- **4-core machine:** 30 hours/month FREE

### Paid Tier (After Free Hours)
| Machine Type | vCPUs | RAM | Storage | Cost/Hour |
|--------------|-------|-----|---------|-----------|
| **2-core** | 2 | 8 GB | 32 GB | $0.18 |
| **4-core** | 4 | 16 GB | 32 GB | $0.36 |
| **8-core** | 8 | 32 GB | 64 GB | $0.72 |
| **16-core** | 16 | 64 GB | 128 GB | $1.44 |
| **32-core** | 32 | 128 GB | 256 GB | $2.88 |

### 💡 **Cost Control with Auto-Stop**
```
Run server for 1 hour/day with 2-core:
- Uses: 2 hours of core-hours per day
- Monthly: 60 core-hours
- Cost: FREE (within 120 core-hour limit!)

Run server 24/7 with 2-core:
- Uses: 1,440 core-hours/month
- Cost: (1,440 - 120) × $0.09 = $118.80/month
- With auto-stop: Dramatically reduces cost!
```

---

## 🚀 **Setup: Your Codex Server in Codespaces**

### Step 1: Create Codespaces Configuration

Your repo already has everything! Just add Codespaces config:

```bash
# Create .devcontainer directory
mkdir -p ~/Overarch\ Jibber\ Jabber/.devcontainer
cd ~/Overarch\ Jibber\ Jabber/.devcontainer
```

### Step 2: Create `devcontainer.json`

```json
{
  "name": "Codex Server",
  "image": "mcr.microsoft.com/devcontainers/python:3.14",
  
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "lts"
    }
  },
  
  "forwardPorts": [8000],
  "portsAttributes": {
    "8000": {
      "label": "Codex Server",
      "onAutoForward": "notify"
    }
  },
  
  "postCreateCommand": "cd codex-server && python -m venv .venv && .venv/bin/pip install -r requirements.txt",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ],
      "settings": {
        "python.defaultInterpreterPath": "${workspaceFolder}/codex-server/.venv/bin/python"
      }
    }
  },
  
  "remoteUser": "vscode"
}
```

### Step 3: Add Auto-Stop Configuration

```json
{
  "name": "Codex Server",
  "image": "mcr.microsoft.com/devcontainers/python:3.14",
  
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "lts"
    }
  },
  
  "forwardPorts": [8000],
  "portsAttributes": {
    "8000": {
      "label": "Codex Server",
      "onAutoForward": "notify"
    }
  },
  
  "postCreateCommand": "cd codex-server && python -m venv .venv && .venv/bin/pip install -r requirements.txt",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ],
      "settings": {
        "python.defaultInterpreterPath": "${workspaceFolder}/codex-server/.venv/bin/python"
      }
    },
    "codespaces": {
      "idleTimeout": "30m"
    }
  },
  
  "remoteUser": "vscode"
}
```

---

## 📋 **Usage: Running in Codespaces**

### Start Codespace

1. **Go to your GitHub repo:**
   ```
   https://github.com/GeorgeDoors888/overarch-jibber-jabber
   ```

2. **Click "Code" → "Codespaces" → "Create codespace on main"**

3. **Wait 1-2 minutes** for setup (runs postCreateCommand)

4. **Start your server:**
   ```bash
   cd codex-server
   source .venv/bin/activate
   python codex_server.py
   ```

5. **Access your server:**
   - Click "Ports" tab in VS Code
   - Port 8000 will be forwarded automatically
   - Click the globe icon to open in browser
   - URL format: `https://[codespace-name]-8000.app.github.dev`

---

## 💰 **Cost Control Strategies**

### Strategy 1: Manual Start/Stop (FREE for 60 hours/month)
```bash
# Start Codespace only when needed
# Work for 1-2 hours
# Stop Codespace when done

Monthly cost: $0 (within free tier)
```

### Strategy 2: Auto-Stop After Idle (Minimal Cost)
```json
// In .devcontainer/devcontainer.json
"customizations": {
  "codespaces": {
    "idleTimeout": "30m"  // Auto-stop after 30min idle
  }
}
```

**Cost Calculation:**
- Use 2 hours/day on weekdays (10 hours/week)
- Auto-stops when idle
- Monthly: ~40 core-hours
- **Cost: $0** (within free 120 core-hours)

### Strategy 3: Delete Codespace When Not in Use
```bash
# From GitHub UI:
# Code → Codespaces → [...] → Delete

# Or use gh CLI:
gh codespace delete --codespace [name]
```

**Cost: $0** - Only pay when Codespace exists and is running

---

## 🔧 **Advanced: Always-Available Setup**

### Option A: Keep Codespace Running ($$)
- 2-core machine 24/7: ~$130/month
- ❌ Not cost-effective for always-on

### Option B: Hybrid Approach (Recommended)
```
Development → Codespaces (Free tier: 60 hours/month)
Production  → Railway/Render ($5-7/month, always on)
```

### Option C: Serverless with GitHub Actions
```yaml
# .github/workflows/execute-code.yml
name: Execute Code
on:
  repository_dispatch:
    types: [execute-code]

jobs:
  execute:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Execute Code
        run: |
          cd codex-server
          pip install -r requirements.txt
          python -c "${{ github.event.client_payload.code }}"
```

**Cost: FREE** (2,000 minutes/month free)

---

## 📊 **Cost Comparison: All Options**

| Option | Availability | Cost/Month | Auto-Stop | Best For |
|--------|--------------|------------|-----------|----------|
| **Local Mac** | Mac must be on | $0 | Manual | Development |
| **Codespaces 2-core** | On-demand | $0-18 | ✅ 30min idle | Flexible dev |
| **Codespaces 24/7** | Always | ~$130 | ❌ | Not recommended |
| **Railway Free** | 500hrs/month | $0 | ✅ 15min idle | Testing |
| **Railway Paid** | Always | $5 | ❌ | Production |
| **Render Free** | On-demand | $0 | ✅ 15min idle | Side projects |
| **Render Paid** | Always | $7 | ❌ | Production |
| **GitHub Actions** | Per-request | $0 | ✅ Per-job | Serverless |

---

## 🎯 **Recommended Setup for You**

### Best Option: **Codespaces for Dev + Railway for Production**

**Development (Codespaces):**
```bash
# Use when actively coding
1. Create Codespace
2. Code for 1-2 hours
3. Let it auto-stop after 30min idle
4. Delete when not needed for a few days

Monthly cost: $0 (within 120 free core-hours)
```

**Production (Railway):**
```bash
# Deploy for 24/7 availability
railway init
railway up

# Auto-sleeps after 15min idle
# Wakes on first request

Monthly cost: $0-5 (depending on usage)
```

---

## 🚀 **Quick Start: Set Up Codespaces Now**

I can help you set this up! Here's what we'll do:

1. **Create `.devcontainer/devcontainer.json`** in your repo
2. **Push to GitHub**
3. **Create Codespace** from GitHub UI
4. **Server will auto-configure** on first launch
5. **Start coding** from anywhere (web, iPad, phone)

---

## 💡 **Codespaces Benefits**

### ✅ Advantages:
- **Access from anywhere** - Web browser, iPad, phone
- **Consistent environment** - Same setup every time
- **Free tier** - 120 core-hours/month
- **Auto-stop** - Saves money when idle
- **Pre-configured** - Dependencies auto-install
- **GitHub integration** - Push/pull seamlessly
- **VS Code in browser** - Full IDE experience

### ⚠️ Considerations:
- **Costs money** after free tier
- **Need internet** to access
- **Slower than local** (network latency)
- **Delete when unused** to avoid storage charges

---

## 📝 **Cost Tracking**

### View Your Usage:
1. Go to: https://github.com/settings/billing
2. Click "Codespaces"
3. See current usage and costs

### Set Spending Limit:
1. Go to: https://github.com/settings/billing/spending_limit
2. Set limit (e.g., $5/month)
3. Codespaces will stop when limit reached

---

## 🎬 **Next Steps**

Want me to:
1. ✅ Create the `.devcontainer/devcontainer.json` file
2. ✅ Add auto-stop configuration
3. ✅ Push to GitHub
4. ✅ Show you how to launch your first Codespace

This will let you run your Codex server from anywhere (phone, iPad, web browser) for **FREE** (within 60 hours/month on 2-core machine)!

Ready to set it up? 🚀
