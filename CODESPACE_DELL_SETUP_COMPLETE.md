# GitHub Codespace → Tailscale → Dell Server Setup

**Status**: ✅ **COMPLETE AND TESTED** (December 17, 2025)

## Overview

This setup enables you to access your Dell server (100.119.237.107) from GitHub Codespaces using Tailscale VPN, giving you full access to BigQuery credentials, code-server, and all 227 tables from anywhere.

## Architecture

```
GitHub Codespace → Tailscale VPN → Dell Server (100.119.237.107)
                                    ├─ SSH access (port 22)
                                    ├─ code-server (port 8080)
                                    ├─ BigQuery credentials
                                    └─ 227 tables in uk_energy_prod
```

## What's Configured

### ✅ Tailscale Network
- **Network**: tailec2e5a.ts.net
- **MagicDNS**: Enabled (100.100.100.100)
- **Dell server**: 100.119.237.107 (hostname: `dell`)
- **Auth key**: Stored in GitHub Codespaces secrets

### ✅ Dell Server
- **IP**: 100.119.237.107
- **Hostname**: dell.tailec2e5a.ts.net
- **User**: george
- **code-server**: Running on port 8080
- **Password**: GB-Power-2025

### ✅ Codespace Configuration
- **Devcontainer**: `.devcontainer/devcontainer.json` with Tailscale feature
- **Auth key**: `TAILSCALE_AUTHKEY` in GitHub secrets
- **Python packages**: google-cloud-bigquery, db-dtypes, pyarrow, pandas, gspread

### ✅ Connected Devices
```
100.119.237.107  dell                        (Dell R630 server)
100.79.212.74    almalinux-1cpu-2gb-uk-lon1  (AlmaLinux VPS)
100.98.82.52     imac-1                      (iMac #1)
100.90.89.16     imac                        (iMac #2)
100.123.1.37     ipad-pro-12-9-gen-4         (iPad Pro)
100.81.252.110   iphone-14                   (iPhone 14)
```

## Usage Instructions

### From GitHub Codespace

#### 1. Launch Codespace
```bash
# Via GitHub web UI:
# https://github.com/GeorgeDoors888/GB-Power-Market-JJ
# Click: Code → Codespaces → Create codespace

# Via CLI:
gh codespace create --repo GeorgeDoors888/GB-Power-Market-JJ
```

#### 2. Start Tailscale (if not auto-started)
```bash
sudo systemctl start tailscaled
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY --reset
```

#### 3. Verify Connection
```bash
# Check Tailscale status
tailscale status

# Test DNS resolution (MagicDNS)
nslookup dell
# Should show: 100.119.237.107

# Test connectivity
curl -I http://100.119.237.107:8080
# Should return: HTTP/1.1 302 Found
```

#### 4. SSH to Dell
```bash
# Using hostname (MagicDNS enabled)
ssh george@dell

# Or using IP address
ssh george@100.119.237.107

# Note: You'll need george's password for the Dell server
```

#### 5. Run BigQuery Scripts
```bash
# SSH into Dell first
ssh george@dell

# Navigate to project
cd ~/GB-Power-Market-JJ

# Run analysis scripts
python3 advanced_statistical_analysis_enhanced.py
python3 update_analysis_bi_enhanced.py

# Or run BigQuery queries directly
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
df = client.query('SELECT * FROM uk_energy_prod.bmrs_mid LIMIT 10').to_dataframe()
print(df)
"
```

### From iPad

#### 1. Install Tailscale App
- Download from App Store: https://apps.apple.com/app/tailscale/id1470499037
- Sign in with your Tailscale account (GeorgeDoors888@)
- Should auto-connect to network

#### 2. Access code-server
```
URL: http://dell:8080
OR:  http://100.119.237.107:8080
Password: GB-Power-2025
```

#### 3. Install GitHub Copilot (Manual)
1. In code-server, click **Extensions** icon (left sidebar)
2. Search: "GitHub Copilot"
3. Click **Install** on both:
   - GitHub Copilot
   - GitHub Copilot Chat
4. Click **Accounts** icon (bottom left)
5. Select "Sign in to use GitHub Copilot"
6. Follow GitHub authentication flow

#### 4. Start Coding
- Open folder: `/home/george/GB-Power-Market-JJ`
- Edit Python files with Copilot suggestions
- Run scripts in integrated terminal
- Access all 227 BigQuery tables

### From iMac

#### Using SSH
```bash
# With MagicDNS
ssh george@dell

# Or with IP
ssh george@100.119.237.107
```

#### Using code-server
```bash
# In Safari or any browser
open http://dell:8080
# Password: GB-Power-2025
```

#### File Transfer
```bash
# Copy files to Dell
scp myfile.py george@dell:~/GB-Power-Market-JJ/

# Copy files from Dell
scp george@dell:~/GB-Power-Market-JJ/results.csv ~/Downloads/
```

## Configuration Files

### .env (Local - Protected by .gitignore)
```bash
# Tailscale authentication key for GitHub Codespaces auto-connect
TAILSCALE_AUTHKEY=tskey-auth-kuaPiqWm1211CNTRL-WgmJW25VQVCjeRMcdPgvUCQv6WLrYSJ8D

# Dell server details
# IP: 100.119.237.107
# Hostname: dell (via MagicDNS)
```

### .devcontainer/devcontainer.json
```json
{
  "name": "GB Power Market Development",
  "image": "mcr.microsoft.com/devcontainers/python:3.14",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "lts"
    },
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/tailscale/codespace:latest": {}
  },
  "forwardPorts": [8000, 8080],
  "portsAttributes": {
    "8000": {
      "label": "Codex Server API",
      "onAutoForward": "notify",
      "protocol": "http"
    },
    "8080": {
      "label": "Dell code-server (via Tailscale)",
      "onAutoForward": "notify",
      "protocol": "http"
    }
  },
  "postCreateCommand": "bash .devcontainer/setup.sh"
}
```

### GitHub Codespaces Secrets
```
Repository: GeorgeDoors888/GB-Power-Market-JJ
Secret name: TAILSCALE_AUTHKEY
Secret value: tskey-auth-kuaPiqWm1211CNTRL-WgmJW25VQVCjeRMcdPgvUCQv6WLrYSJ8D

Location: https://github.com/GeorgeDoors888/GB-Power-Market-JJ/settings/secrets/codespaces
```

## Troubleshooting

### Tailscale Not Starting in Codespace

**Problem**: `tailscale status` shows "failed to connect to local tailscaled"

**Solution**:
```bash
# Start Tailscale daemon
sudo systemctl start tailscaled

# Connect with auth key
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY --reset

# Verify
tailscale status
```

### Can't Reach Dell Server

**Problem**: SSH/HTTP connection times out

**Check 1 - Verify Tailscale connection**:
```bash
tailscale status
# Dell should show as: 100.119.237.107  dell  GeorgeDoors888@  linux  -
```

**Check 2 - Test DNS resolution**:
```bash
nslookup dell
# Should resolve to 100.119.237.107
```

**Check 3 - Test network connectivity**:
```bash
# Install iputils if ping not available
sudo apt-get update && sudo apt-get install -y iputils-ping

# Ping test
ping -c 3 100.119.237.107
```

**Check 4 - Verify Dell services running**:
```bash
# SSH into Dell
ssh george@dell

# Check code-server
sudo systemctl status code-server@george

# Check if port 8080 listening
netstat -tlnp | grep 8080

# Restart if needed
sudo systemctl restart code-server@george
```

### Code-Server Not Responding

**Problem**: `curl http://100.119.237.107:8080` returns connection error

**Solution** (run on Dell server):
```bash
# Check service status
sudo systemctl status code-server@george

# Restart service
sudo systemctl restart code-server@george

# Wait a moment
sleep 3

# Verify it's listening
netstat -tlnp | grep 8080
# Should show: 0.0.0.0:8080

# Test locally
curl -I http://localhost:8080
# Should return: HTTP/1.1 302 Found

# Check logs if still failing
sudo journalctl -u code-server@george -n 50 --no-pager
```

### GitHub Copilot Not Installing via CLI

**Problem**: `code-server --install-extension GitHub.copilot` fails

**Why**: code-server marketplace API differs from VS Code, extensions must be installed via UI

**Solution**:
1. Access code-server web UI: http://dell:8080
2. Click Extensions icon (left sidebar)
3. Search "GitHub Copilot"
4. Click Install button
5. Sign in with GitHub account when prompted

### Auth Key Expired

**Problem**: `tailscale up` fails with "key expired" error

**Solution**:
1. Generate new key: https://login.tailscale.com/admin/settings/keys
2. Update `.env` file locally
3. Update GitHub Codespaces secret:
   - Go to: https://github.com/GeorgeDoors888/GB-Power-Market-JJ/settings/secrets/codespaces
   - Edit `TAILSCALE_AUTHKEY`
   - Paste new key value
   - Save

### MagicDNS Not Resolving

**Problem**: `nslookup dell` returns "No answer"

**Check 1 - Verify MagicDNS enabled**:
- Go to: https://login.tailscale.com/admin/dns
- Ensure MagicDNS toggle is ON
- Nameserver should show: 100.100.100.100

**Check 2 - Wait for DNS propagation**:
```bash
# Can take 30-60 seconds after enabling
sleep 60
nslookup dell
```

**Check 3 - Use full domain name**:
```bash
nslookup dell.tailec2e5a.ts.net
```

**Workaround**: Use IP address directly
```bash
ssh george@100.119.237.107
curl http://100.119.237.107:8080
```

## Advanced Usage

### Port Forwarding from Codespace

Forward Dell's code-server port to Codespace's localhost:
```bash
# In Codespace terminal
ssh -L 8080:localhost:8080 george@dell -N

# Then access in Codespace's browser (port forwarding)
# VS Code will auto-detect and offer to open
```

### Running Long Scripts on Dell

Use `screen` or `tmux` to keep scripts running after disconnect:
```bash
# SSH to Dell
ssh george@dell

# Start screen session
screen -S bigquery_analysis

# Run long-running script
python3 advanced_statistical_analysis_enhanced.py

# Detach: Press Ctrl+A then D

# Exit SSH (script keeps running)
exit

# Later, reconnect and reattach:
ssh george@dell
screen -r bigquery_analysis
```

### Automated Codespace Setup

Add to `.devcontainer/setup.sh` for automatic Tailscale connection:
```bash
#!/bin/bash
set -e

echo "🚀 Setting up Codespace environment..."

# Start Tailscale
echo "Starting Tailscale..."
sudo systemctl start tailscaled
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY --reset --accept-routes

# Verify connection
echo "Verifying Tailscale connection..."
tailscale status | grep dell && echo "✅ Connected to Dell server"

# Install Python packages
echo "Installing Python packages..."
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread

echo "✅ Codespace setup complete!"
```

### Access from Multiple Codespaces

The same auth key works for all Codespaces in the repository. Each Codespace gets its own Tailscale node name:
```bash
# First Codespace: codespaces-abc123
# Second Codespace: codespaces-def456
# All can access: dell (100.119.237.107)
```

## Security Notes

### Auth Key Protection
- ✅ `.env` file in `.gitignore` (not committed to Git)
- ✅ `TAILSCALE_AUTHKEY` in GitHub Codespaces secrets (encrypted)
- ✅ Auth key scoped to "GitHub Codespaces Auto-Connect"
- ⚠️ Rotate key every 90 days: https://login.tailscale.com/admin/settings/keys

### Network Isolation
- Codespaces can ONLY access devices on your Tailscale network
- Dell server is NOT exposed to public internet
- All traffic encrypted via WireGuard protocol
- No inbound firewall rules needed on Dell

### Credentials Protection
- ✅ `inner-cinema-credentials.json` in `.gitignore`
- ✅ BigQuery service account has minimal permissions
- ✅ code-server password protected
- ⚠️ Ensure credentials file NOT in public repository

### Access Control
Manage device authorization at:
- https://login.tailscale.com/admin/machines
- Can disable/remove Codespace nodes individually
- Can set key expiry for auto-removal

## Performance Tips

### Reduce Latency
```bash
# Check Tailscale connection type
tailscale status
# Look for "direct" vs "relay"
# Direct = peer-to-peer (faster)
# Relay = via Tailscale DERP servers (slower)
```

### Use SSH Multiplexing
Add to `~/.ssh/config` in Codespace:
```
Host dell
    HostName 100.119.237.107
    User george
    ControlMaster auto
    ControlPath ~/.ssh/control-%r@%h:%p
    ControlPersist 10m
```

Then SSH connections reuse same TCP connection (faster).

### Monitor Bandwidth
```bash
# On Dell server
tailscale status
# Shows: tx (transmitted) rx (received) bytes
```

## Quick Reference

### Common Commands

```bash
# === In Codespace ===
# Start Tailscale
sudo tailscale up --authkey=$TAILSCALE_AUTHKEY --reset

# Check status
tailscale status

# SSH to Dell
ssh george@dell

# Test code-server
curl http://dell:8080

# === On Dell Server ===
# Restart code-server
sudo systemctl restart code-server@george

# Check code-server status
systemctl status code-server@george

# View code-server logs
journalctl -u code-server@george -f

# Check Tailscale
tailscale status

# === URLs ===
# Code-server: http://dell:8080 or http://100.119.237.107:8080
# Tailscale admin: https://login.tailscale.com/admin
# DNS settings: https://login.tailscale.com/admin/dns
# Codespaces secrets: https://github.com/GeorgeDoors888/GB-Power-Market-JJ/settings/secrets/codespaces
```

### Connection Matrix

| From Device | To Dell SSH | To code-server | Method |
|-------------|-------------|----------------|--------|
| Codespace | `ssh george@dell` | `http://dell:8080` | Tailscale VPN |
| iPad | N/A (no SSH app) | Safari: `http://dell:8080` | Tailscale app + VPN |
| iMac | `ssh george@dell` | Browser: `http://dell:8080` | Tailscale app + VPN |
| iPhone | N/A | Safari: `http://dell:8080` | Tailscale app + VPN |

### Passwords

| Service | Username | Password | Location |
|---------|----------|----------|----------|
| code-server | N/A | `GB-Power-2025` | Dell: `~/.config/code-server/config.yaml` |
| Dell SSH | `george` | (your Dell user password) | System user password |
| Tailscale | N/A | SSO via GitHub | https://login.tailscale.com |

## Resources

- **Tailscale Documentation**: https://tailscale.com/kb/1160/github-codespaces
- **code-server GitHub**: https://github.com/coder/code-server
- **VS Code Remote**: https://code.visualstudio.com/docs/remote/remote-overview
- **GitHub Codespaces**: https://docs.github.com/en/codespaces
- **BigQuery Python Client**: https://cloud.google.com/python/docs/reference/bigquery/latest

## Related Documentation

- `TAILSCALE_SETUP_COMPLETE.md` - Comprehensive Tailscale guide (591 lines)
- `CODESPACES_TAILSCALE_SETUP.md` - Original setup instructions
- `TAILSCALE_AUTHKEY_SETUP.md` - Quick reference for auth key
- `DELL_IPAD_SETUP_GUIDE.md` - iPad-specific instructions
- `DELL_REMOTE_ACCESS_SOLUTIONS.md` - Comparison of remote access methods

---

**Setup Date**: December 17, 2025  
**Status**: ✅ Production Ready  
**Tested**: Codespace → Dell SSH ✅, code-server ✅, MagicDNS ✅  
**Maintainer**: George Major (george@upowerenergy.uk)
