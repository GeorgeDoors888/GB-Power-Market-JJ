# ChatGPT Automatic Connections Guide
## GitHub, Google Drive, BigQuery Integration

---

## 🎯 What This Enables

After setup, you can say to ChatGPT:
- "Get the data from Drive and analyze it"
- "Check my GitHub repo and update the code"
- "Query my BigQuery and create a report"
- "Run this Python code on my server"

**ChatGPT will automatically do all of this without asking for credentials!**

---

## 📋 Step-by-Step Setup

### Step 1: Add Custom Instructions to ChatGPT

This tells ChatGPT about your connections permanently.

#### Go to ChatGPT:
1. Visit https://chatgpt.com
2. Click your profile icon (bottom left)
3. Click **Settings**
4. Click **Personalization** 
5. Enable **Custom instructions**

#### Paste This in Box 1 ("What would you like ChatGPT to know?"):

```
MY INFRASTRUCTURE:

CODEX SERVER:
- URL: https://jibber-jabber-production.up.railway.app
- Token: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
- Can: Execute Python/JavaScript, Query BigQuery
- Project: jibber-jabber-knowledge

GITHUB:
- Owner: GeorgeDoors888
- Repo: overarch-jibber-jabber
- Branch: main
- You have read access via GitHub integration

GOOGLE DRIVE:
- Energy/power industry data
- Service Account: jibber-jabber-knowledge@appspot.gserviceaccount.com
- Access via Drive integration or BigQuery

BIGQUERY:
- Project: jibber-jabber-knowledge
- Datasets: uk_energy_insights, documents
- Access via Codex Server /query_bigquery endpoint
```

#### Paste This in Box 2 ("How would you like ChatGPT to respond?"):

```
AUTOMATIC ACTIONS:

YOU CAN ACCESS MY INFRASTRUCTURE DIRECTLY VIA HTTP:

When I say:
- "Run code" → POST to https://jibber-jabber-production.up.railway.app/execute
- "Query BigQuery" → POST to https://jibber-jabber-production.up.railway.app/query_bigquery
- "Check health" → GET https://jibber-jabber-production.up.railway.app/health
- "Check the repo" → Use your GitHub integration to read files
- "Get from Drive" → Use your Google Drive integration to read files

CRITICAL - YOU HAVE DIRECT ACCESS:
1. You CAN reach Railway - it's a public HTTPS endpoint
2. You CAN execute Python/JavaScript - send HTTP POST request with code
3. You CAN query BigQuery - send HTTP POST request with SQL
4. DON'T say "I can't reach it" - YOU CAN via HTTP/HTTPS
5. DON'T just show code - ACTUALLY EXECUTE IT via HTTP POST
6. DON'T just describe queries - ACTUALLY RUN THEM via HTTP POST
7. Show me what you're doing at each step

EXAMPLE - When I say "run print('hello')":
curl -X POST https://jibber-jabber-production.up.railway.app/execute \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"hello\")","language":"python"}'
```

---

### Step 2: Connect GitHub Integration

#### Enable GitHub in ChatGPT:

**Option A: Via Chat**
1. Start new ChatGPT conversation
2. Type: "Connect to my GitHub"
3. ChatGPT will show GitHub integration option
4. Click "Connect to GitHub"

**Option B: Via Settings**
1. ChatGPT → Settings → Beta Features
2. Enable "Plugins" or "Integrations"
3. Search for "GitHub"
4. Click "Install"

#### Authorize GitHub:
1. Sign in to GitHub when prompted
2. Authorize ChatGPT application
3. Select repositories:
   - ✅ Choose "All repositories" OR
   - ✅ Select: `overarch-jibber-jabber`
4. Click "Install & Authorize"

#### What ChatGPT Can Now Do:
- ✅ Read files from your repo
- ✅ Search code
- ✅ View commits and branches
- ✅ Suggest pull requests
- ❌ Cannot directly push (only suggest)

---

### Step 3: Connect Google Drive Integration

#### Enable Drive in ChatGPT:

**Option A: Via Chat**
1. Start new ChatGPT conversation
2. Type: "Connect to my Google Drive"
3. ChatGPT will show Drive integration
4. Click "Connect"

**Option B: Via Settings**
1. ChatGPT → Settings → Integrations
2. Find "Google Drive"
3. Click "Connect"

#### Authorize Google:
1. Sign in to your Google account
2. Select the account with your data
3. Grant permissions:
   - ✅ See and download files
   - ✅ Upload and create files (optional)
4. Click "Allow"

#### What ChatGPT Can Now Do:
- ✅ List files and folders
- ✅ Read files (CSV, TXT, PDF, etc.)
- ✅ Search Drive
- ✅ Upload files (if granted permission)
- ✅ Create documents/sheets

---

## 🧪 Test Your Connections

### Test 1: Codex Server (YOU CAN DO THIS VIA HTTP!)
**Say to ChatGPT:**
```
Make an HTTP POST request to my Codex Server to run Python code: print("Hello from Railway!")
```

**What ChatGPT Should Do:**
```bash
# ChatGPT makes this HTTP request:
curl -X POST https://jibber-jabber-production.up.railway.app/execute \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"Hello from Railway!\")","language":"python"}'
```

**Expected Result:**
```json
{
  "success": true,
  "output": "Hello from Railway!\n",
  "execution_time": 0.023
}
```

**If ChatGPT says "I can't reach it":**
Reply: "YES YOU CAN - it's a public HTTPS endpoint. Make an HTTP POST request to that URL."

---

### Test 2: BigQuery (YOU CAN DO THIS VIA HTTP!)
**Say to ChatGPT:**
```
Make an HTTP POST request to query my BigQuery: SELECT CURRENT_TIMESTAMP() as now, "Hello BigQuery" as message
```

**What ChatGPT Should Do:**
```bash
# ChatGPT makes this HTTP request:
curl -X POST https://jibber-jabber-production.up.railway.app/query_bigquery \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT CURRENT_TIMESTAMP() as now, \"Hello BigQuery\" as message"}'
```

**Expected Result:**
```json
{
  "success": true,
  "data": [
    {"now": "2025-11-06T23:30:00+00:00", "message": "Hello BigQuery"}
  ],
  "row_count": 1,
  "execution_time": 1.79
}
```

**If ChatGPT says "I can't reach BigQuery":**
Reply: "YES YOU CAN - send an HTTP POST to my Codex Server endpoint with the SQL query."

---

### Test 3: GitHub
**Say to ChatGPT:**
```
Show me the first 10 lines of codex_server.py from my GitHub repo
```

**Expected Result:**
```
✅ Reading from GitHub: overarch-jibber-jabber/codex_server.py

import os
import sys
from fastapi import FastAPI, HTTPException
...
```

---

### Test 4: Google Drive
**Say to ChatGPT:**
```
List all CSV files in my Google Drive
```

**Expected Result:**
```
✅ Scanning Google Drive...

Found 5 CSV files:
1. bmu_registration_data.csv (1.2 MB)
2. analysis_bi_enhanced_full_export.csv (850 KB)
...
```

---

### Test 5: Complete Workflow
**Say to ChatGPT:**
```
1. Get bmu_registration_data.csv from Drive
2. Query BigQuery for matching performance data
3. Run Python analysis via Codex Server comparing both
4. Show me the top 10 results
```

**Expected Result:**
ChatGPT automatically:
1. ✅ Downloads CSV from Drive
2. ✅ Runs SQL query on BigQuery
3. ✅ Executes Python code to merge data
4. ✅ Shows formatted results

---

## 🔐 Security & Permissions

### What You're Granting:

| Service | Permission Level | What ChatGPT Can Do |
|---------|-----------------|-------------------|
| **Codex Server** | Full API access | Execute code, query BigQuery |
| **GitHub** | Read-only* | View files, search code, suggest PRs |
| **Google Drive** | Read + Write** | Access files you give permission to |

*Cannot push directly, only suggest changes
**Can be set to read-only if preferred

### What's Protected:

- ❌ ChatGPT cannot delete your repos
- ❌ ChatGPT cannot delete Drive files
- ❌ ChatGPT cannot access other Google services (Gmail, etc.)
- ❌ ChatGPT cannot modify BigQuery schemas
- ❌ All actions are logged and visible to you

### Revoke Access:

**GitHub:**
- https://github.com/settings/applications
- Find "ChatGPT" → Revoke

**Google Drive:**
- https://myaccount.google.com/permissions
- Find "ChatGPT" → Remove

**Codex Server:**
- Change `CODEX_API_TOKEN` in Railway dashboard

---

## 💡 Real Examples

### Example 1: Daily Data Analysis
**You:**
```
Check Drive for new CSV files uploaded today, 
load them into BigQuery if new,
run my standard analysis Python script,
and save the report to Drive
```

**ChatGPT:**
- Scans Drive for files modified today
- Checks BigQuery if data already exists
- Loads new data if needed
- Executes analysis code via Codex Server
- Creates report and uploads to Drive folder

---

### Example 2: Code Review
**You:**
```
Review all Python files in my GitHub repo,
check for any hardcoded credentials,
and suggest fixes
```

**ChatGPT:**
- Reads all .py files from GitHub
- Searches for credential patterns
- Identifies security issues
- Suggests code changes via PR

---

### Example 3: Data Pipeline
**You:**
```
Every time I upload a new CSV to the "Incoming" folder in Drive,
I want you to validate it, load to BigQuery, and notify me
```

**ChatGPT:**
"I can't monitor Drive continuously, but I can create a Python script
that does this. Should I create it and save to your GitHub repo?"

*(You: "Yes")*

ChatGPT:
- Writes the automation script
- Saves to GitHub repo
- Provides deployment instructions

---

## 🚀 Advanced: Create a Custom GPT

If you have ChatGPT Plus or Pro, create a specialized assistant:

### Steps:
1. Go to https://chatgpt.com
2. Click "Explore GPTs"
3. Click "Create a GPT"
4. Fill in:

**Name:** "My Data Assistant"

**Description:** "Analyzes energy data from BigQuery, manages GitHub code, and handles Drive files"

**Instructions:**
```
You have automatic access to:

1. CODEX SERVER (https://jibber-jabber-production.up.railway.app)
   - Token: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   - Execute Python/JavaScript code
   - Query BigQuery (project: jibber-jabber-knowledge)

2. GITHUB (GeorgeDoors888/overarch-jibber-jabber)
   - Read and search code
   - Suggest improvements

3. GOOGLE DRIVE
   - Access data files
   - Create reports

BEHAVIOR:
- When asked to analyze data → automatically query BigQuery
- When asked to run code → automatically use Codex Server
- When asked about code → automatically check GitHub
- When asked about files → automatically check Drive
- Always execute, never just describe
- Show step-by-step what you're doing
```

**Knowledge Files:**
- Upload: `CHATGPT_CODEX_INTEGRATION.md`
- Upload: `CHATGPT_CUSTOM_INSTRUCTIONS.md`

**Capabilities:**
- ✅ Web browsing
- ✅ Code interpreter
- ✅ GitHub integration
- ✅ Google Drive integration

5. Save the GPT
6. Use it whenever you need data analysis!

---

## 📊 Connection Status Check

### Ask ChatGPT to Run This Test:

```
Test all my connections:

1. Codex Server: GET /health
2. BigQuery: SELECT 1 as test
3. GitHub: List files in overarch-jibber-jabber repo
4. Drive: Count total files

Show me a status table with ✅ or ❌ for each.
```

**Expected Output:**
```
Connection Status:
┌─────────────────┬────────┬─────────────────┐
│ Service         │ Status │ Details         │
├─────────────────┼────────┼─────────────────┤
│ Codex Server    │ ✅     │ Healthy v1.0.0  │
│ BigQuery        │ ✅     │ Query success   │
│ GitHub          │ ✅     │ 150+ files      │
│ Google Drive    │ ✅     │ 42 files found  │
└─────────────────┴────────┴─────────────────┘
```

---

## 🛠️ Troubleshooting

### ⚠️ ChatGPT Says "I Can't Reach Your Server"

**Problem:** ChatGPT says it can't access Railway/BigQuery

**Solution:** ChatGPT is confused! Tell it:

```
YES YOU CAN reach it! It's a public HTTPS endpoint.

Make an HTTP POST request to:
https://jibber-jabber-production.up.railway.app/execute

You have curl/HTTP capabilities. Use them!

Example:
curl -X POST https://jibber-jabber-production.up.railway.app/execute \
  -H "Content-Type: application/json" \
  -d '{"code":"print(2+2)","language":"python"}'
```

**Why This Happens:**
- ChatGPT sometimes forgets it can make HTTP requests
- It needs explicit reminder that Railway is PUBLIC not private
- Custom Instructions should prevent this

**Quick Fix:**
Add this to your message:
"This is a PUBLIC https:// endpoint. Make an HTTP request to it."

---

### "Connection to Codex Server failed"

1. Check Railway is running: https://railway.com
2. Test directly: 
   ```bash
   curl https://jibber-jabber-production.up.railway.app/health
   ```
3. Verify token in Custom Instructions matches Railway

---

### "GitHub integration not working"

1. Go to https://github.com/settings/applications
2. Check "ChatGPT" is authorized
3. Verify repo access granted
4. Try disconnecting and reconnecting

---

### "Can't access Google Drive"

1. Go to https://myaccount.google.com/permissions
2. Check ChatGPT has Drive access
3. Try re-authorizing with full permissions
4. Check files aren't in restricted folders

---

### "BigQuery permission denied"

1. Verify service account has BigQuery permissions
2. Check project ID is correct: `jibber-jabber-knowledge`
3. Use full table names: `project.dataset.table`
4. Test with simple query first: `SELECT 1`

---

## ✅ Setup Checklist

- [ ] Custom Instructions added to ChatGPT
- [ ] GitHub integration connected
- [ ] Google Drive integration connected  
- [ ] Codex Server health check passes
- [ ] BigQuery test query successful
- [ ] GitHub repo accessible
- [ ] Drive file listing works
- [ ] Complete workflow test passed
- [ ] Custom GPT created (optional)

---

## 📚 Quick Reference

### Key URLs:

| Service | URL |
|---------|-----|
| ChatGPT | https://chatgpt.com |
| Settings | https://chatgpt.com/settings |
| Codex Server | https://jibber-jabber-production.up.railway.app |
| Railway Dashboard | https://railway.com |
| GitHub Repo | https://github.com/GeorgeDoors888/overarch-jibber-jabber |
| GitHub Apps | https://github.com/settings/applications |
| Google Permissions | https://myaccount.google.com/permissions |

### Key Credentials:

```
Codex API Token: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
BigQuery Project: jibber-jabber-knowledge
GitHub Repo: GeorgeDoors888/overarch-jibber-jabber
Service Account: jibber-jabber-knowledge@appspot.gserviceaccount.com
```

---

## 🎯 You're All Set!

ChatGPT now has automatic access to:
- ✅ Your code execution server
- ✅ Your BigQuery database
- ✅ Your GitHub repository
- ✅ Your Google Drive files

**Try it now:**
```
"Show me what data is available in my BigQuery uk_energy_insights dataset,
then get the latest analysis file from Drive and compare them"
```

ChatGPT will automatically do everything!

---

**Status:** ✅ Ready for automatic operations
**Last Updated:** November 6, 2025
**Version:** 1.0.0
