# GitHub Codespaces + Tailscale Integration

## Overview
This setup enables GitHub Codespaces to automatically connect to your Tailscale network, allowing access to the Dell server at `100.119.237.107` for BigQuery development.

## Architecture
```
GitHub Codespace → Tailscale VPN → Dell Server (100.119.237.107)
                                    ├─ code-server (port 8080)
                                    ├─ BigQuery credentials
                                    └─ 227 tables in uk_energy_prod
```

## Prerequisites
- Tailscale auth key stored in `.env` (already configured ✅)
- Dell server running Tailscale at 100.119.237.107
- GitHub repository with Codespaces enabled

## Setup Instructions

### 1. Add Tailscale Auth Key to Codespaces Secrets

**Option A: Via GitHub Web UI (Recommended)**
1. Go to https://github.com/GeorgeDoors888/GB-Power-Market-JJ/settings/secrets/codespaces
2. Click **New repository secret**
3. Name: `TAILSCALE_AUTHKEY`
4. Value: `tskey-auth-kuaPiqWm1211CNTRL-WgmJW25VQVCjeRMcdPgvUCQv6WLrYSJ8D`
5. Click **Add secret**

**Option B: Via GitHub CLI**
```bash
gh secret set TAILSCALE_AUTHKEY --repos GeorgeDoors888/GB-Power-Market-JJ \
  --body "tskey-auth-kuaPiqWm1211CNTRL-WgmJW25VQVCjeRMcdPgvUCQv6WLrYSJ8D"
```

### 2. Create Devcontainer Configuration

Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "GB Power Market Development",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  
  "features": {
    "ghcr.io/tailscale/codespace:latest": {}
  },
  
  "postCreateCommand": "pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "GitHub.copilot",
        "GitHub.copilot-chat"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python"
      }
    }
  },
  
  "remoteEnv": {
    "GOOGLE_APPLICATION_CREDENTIALS": "/workspaces/GB-Power-Market-JJ/inner-cinema-credentials.json"
  }
}
```

### 3. Test Codespace Connection

**Launch Codespace:**
```bash
# From local machine
gh codespace create --repo GeorgeDoors888/GB-Power-Market-JJ
```

**Verify Tailscale Connection:**
```bash
# Inside Codespace terminal
tailscale status
# Should show: dell (100.119.237.107)

ping 100.119.237.107
# Should get responses

ssh george@100.119.237.107
# Should connect to Dell server
```

**Test BigQuery Access via Dell:**
```bash
# SSH tunnel from Codespace → Dell → BigQuery
ssh -L 8080:localhost:8080 george@100.119.237.107

# Or access code-server directly
curl http://100.119.237.107:8080
```

## Usage Patterns

### Pattern 1: Direct BigQuery from Codespace
```python
# Codespace has BigQuery credentials in repo
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
df = client.query("SELECT * FROM uk_energy_prod.bmrs_mid LIMIT 10").to_dataframe()
```

### Pattern 2: SSH to Dell for Heavy Queries
```bash
# Codespace → SSH → Dell
ssh george@100.119.237.107
python3 advanced_statistical_analysis_enhanced.py
```

### Pattern 3: Access Dell's code-server from Codespace
```bash
# Forward port 8080 from Dell to Codespace
ssh -L 8080:localhost:8080 george@100.119.237.107

# Then in Codespace's Simple Browser:
# http://localhost:8080
```

## Tailscale Features Available

### MagicDNS (After Enabling)
```bash
# Instead of: ssh george@100.119.237.107
ssh george@dell

# Instead of: http://100.119.237.107:8080
http://dell:8080
```

Enable at: https://login.tailscale.com/admin/dns

### Funnel (Expose Codespace to Internet)
```bash
# Make Codespace port accessible to public
tailscale funnel 8080
# Generates: https://your-codespace.tailXXXX.ts.net
```

### SSH via Tailscale
```bash
# No SSH keys needed, uses Tailscale identity
tailscale ssh george@dell
```

## Troubleshooting

### Auth Key Expired
```bash
# Generate new key at: https://login.tailscale.com/admin/settings/keys
# Update in:
# 1. .env file (local)
# 2. GitHub Codespaces secrets
```

### Tailscale Not Connecting in Codespace
```bash
# Check logs
sudo journalctl -u tailscaled

# Restart service
sudo systemctl restart tailscaled
tailscale up --authkey=$TAILSCALE_AUTHKEY
```

### Can't Reach Dell Server
```bash
# Check Tailscale status
tailscale status
# Dell should show as "active; direct"

# Check Dell IP
tailscale ip -4
# Should show 100.119.237.107

# Ping test
ping 100.119.237.107

# Port test
nc -zv 100.119.237.107 8080
```

### BigQuery Credentials Not Found
```bash
# Verify file exists in Codespace
ls -la /workspaces/GB-Power-Market-JJ/inner-cinema-credentials.json

# Check environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Manual set if needed
export GOOGLE_APPLICATION_CREDENTIALS="/workspaces/GB-Power-Market-JJ/inner-cinema-credentials.json"
```

## Security Notes

### Auth Key Rotation
- Current key: Created 2025-12-16
- Purpose: "GitHub Codespaces Auto-Connect"
- Expiry: Check at https://login.tailscale.com/admin/settings/keys
- Rotation: Generate new key → Update .env + GitHub secret

### Network Isolation
```bash
# Codespace can ONLY access:
# - Dell server (100.119.237.107)
# - Other devices you authorize in Tailscale ACLs

# Codespace CANNOT access:
# - Other Tailscale users' devices
# - Your home network (unless explicitly shared)
```

### Credentials Protection
- ✅ `.env` in `.gitignore` (not committed to Git)
- ✅ `TAILSCALE_AUTHKEY` in GitHub Codespaces secrets (encrypted)
- ✅ `inner-cinema-credentials.json` in `.gitignore`
- ⚠️ Ensure credentials file NOT committed to public repo

## Advanced: Multi-Repository Setup

### Share Tailscale Across Multiple Repos
```bash
# Add secret to organization level:
gh secret set TAILSCALE_AUTHKEY --org YourOrg \
  --repos "repo1,repo2,repo3" \
  --body "tskey-auth-..."
```

### Different Tailscale Networks per Repo
```bash
# Production repo: prod-authkey
# Development repo: dev-authkey
# Personal repo: personal-authkey
```

## Resources

- **Tailscale Codespaces Feature**: https://tailscale.com/kb/1160/github-codespaces
- **Devcontainer Reference**: https://containers.dev/implementors/json_reference/
- **GitHub Secrets**: https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/managing-encrypted-secrets-for-your-repository-and-organization-for-github-codespaces

## Quick Reference

```bash
# Codespace → Dell connection test
tailscale status && ping -c 3 100.119.237.107

# SSH to Dell
ssh george@100.119.237.107

# Access code-server (after MagicDNS)
http://dell:8080

# Run BigQuery script on Dell
ssh george@100.119.237.107 'cd GB-Power-Market-JJ && python3 advanced_statistical_analysis_enhanced.py'
```

---

**Status**: ✅ Auth key stored in `.env` (2025-12-16)  
**Next Steps**: 
1. Add `TAILSCALE_AUTHKEY` to GitHub Codespaces secrets
2. Create `.devcontainer/devcontainer.json`
3. Test Codespace → Dell connection
4. Enable MagicDNS for `dell` hostname
