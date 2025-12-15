# 🎓 Beginner's Guide: Using Your ChatGPT + BigQuery Setup

**For**: George Major  
**Level**: Complete Novice  
**Time**: 10 minutes to understand

---

## What You Have (In Simple Terms)

Think of your setup like this:

```
┌─────────────────────────────────────────────────────────────┐
│  YOU (talking to ChatGPT)                                   │
│  ↓                                                           │
│  ChatGPT (understands English)                              │
│  ↓                                                           │
│  Vercel Proxy (translator: English → SQL)                   │
│  ↓                                                           │
│  BigQuery (massive database: 391M+ rows of energy data)     │
│  ↓                                                           │
│  Answer comes back to you in plain English                  │
└─────────────────────────────────────────────────────────────┘
```

**Without this setup**: You'd need to learn SQL, connect to databases, write code.  
**With this setup**: You just ask questions like "What was the price yesterday?"

---

## Part 1: Asking Questions to ChatGPT

### Where to Start

1. **Open ChatGPT** (chatgpt.com)
2. **Find your custom GPT**: "GB Power Market Assistant" (in your GPT list)
3. **Just ask!**

### What You Can Ask

#### 💷 Price Questions
```
"What was the average electricity price last week?"
"Show me the highest prices in October 2025"
"When did we have negative prices?"
"What's the price trend this month?"
```

#### ⚡ Generation Questions
```
"How much wind power is being generated?"
"What's the generation mix today?"
"Show me top 10 power stations"
"Compare coal vs gas generation"
```

#### 🔋 Battery Questions
```
"Show me battery activity today"
"Which VLP units are most active?"
"What's the arbitrage opportunity right now?"
```

#### 📊 Frequency Questions
```
"What's the grid frequency?"
"Show me frequency dips last week"
"When was frequency below 49.8Hz?"
```

### What ChatGPT Does

1. **Understands** your question (uses AI)
2. **Translates** to SQL query
3. **Sends** to your Vercel proxy
4. **Gets** data from BigQuery
5. **Formats** answer nicely for you

**You never see the SQL!** (Unless you ask for it)

---

## Part 2: What's Happening Behind the Scenes

### Your Data Pipeline

```
HISTORICAL DATA (2020-present)
↓
Elexon BMRS API → Python scripts → BigQuery tables
- bmrs_bod: Bid/offer data (391M+ rows)
- bmrs_mid: Market prices
- bmrs_fuelinst: Generation by fuel type
- bmrs_freq: Grid frequency
(+ 174 other tables)

REAL-TIME DATA (last 48 hours)
↓
IRIS → Azure Service Bus → AlmaLinux server → BigQuery *_iris tables
- bmrs_fuelinst_iris
- bmrs_indgen_iris
- etc.
```

### Important Files (What's Where)

```
Your Mac (Development):
~/GB Power Market JJ/
├── *.py scripts           ← You write/edit these
├── *.md documentation     ← Guides like this
└── vercel-proxy/          ← ChatGPT connection code

Your Server (AlmaLinux - 94.237.55.234):
/opt/iris-pipeline/
├── client.py              ← Downloads real-time data
└── iris_to_bigquery_unified.py  ← Uploads to BigQuery

Your Server (UpCloud - 94.237.55.15):
/opt/arbitrage/
├── battery_arbitrage.py   ← Main analysis script
└── logs/                  ← Output logs

Google Cloud:
Project: inner-cinema-476211-u9
Dataset: uk_energy_prod
Tables: 174+ tables (bmrs_*)

Google Sheets:
Dashboard: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

---

## Part 3: The Credentials System (Simplified)

### What Are Credentials?

Think of credentials like **keys to your house**:
- **BigQuery key**: Opens the database
- **Google Sheets key**: Opens your spreadsheet
- **API key**: Lets ChatGPT talk to your system

### Where They Live (Mac)

```bash
# Your credentials (hidden folder)
~/.google-credentials/
├── inner-cinema-credentials.json    ← BigQuery key
└── workspace-credentials.json       ← Google Sheets key

# Your environment variables (auto-loaded settings)
~/.zshrc
```

**Important**: These files are **secret**! Never share them or commit to GitHub.

### How They Work Automatically

When you open Terminal, `~/.zshrc` runs automatically and sets:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/Users/georgemajor/.google-credentials/inner-cinema-credentials.json
GCP_PROJECT=inner-cinema-476211-u9
```

Then **every Python script** automatically knows:
- Where the credentials are
- Which project to use
- Which dataset to query

**You don't need to do anything!** It just works.

---

## Part 4: Common Tasks (Step-by-Step)

### Task 1: Ask ChatGPT a Question

1. Open ChatGPT
2. Select "GB Power Market Assistant"
3. Type: `"What was the average price yesterday?"`
4. Wait 5-10 seconds
5. Read the answer!

**If it fails**: See [Troubleshooting](#troubleshooting-for-beginners) below.

### Task 2: Check Your Dashboard

1. Open browser
2. Go to: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
3. Look at "Dashboard" tab
4. Data updates every 5 minutes automatically

### Task 3: Run a Python Script (Mac)

```bash
# Open Terminal
# Go to your project folder
cd ~/GB\ Power\ Market\ JJ

# Run a script
python3 analyze_battery_vlp_final.py

# Wait for it to finish
# Check the output (usually a CSV file or report)
ls -lt *.csv | head -5
```

### Task 4: Check Real-Time Data is Flowing

```bash
# SSH to your AlmaLinux server
ssh root@94.237.55.234

# Check the uploader log (last 20 lines)
tail -20 /opt/iris-pipeline/logs/iris_uploader.log

# You should see recent timestamps
# Exit
exit
```

### Task 5: Update Google Sheets from Python

```python
# This is already in your scripts, but here's how it works:

import os
import gspread
from google.oauth2 import service_account

# Credentials are auto-loaded from environment
creds = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_WORKSPACE_CREDENTIALS'),
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

# Connect to your dashboard
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv('SHEETS_ID'))
worksheet = sheet.worksheet('Dashboard')

# Update a cell
worksheet.update('A1', [['Hello from Python!']])
print("✅ Updated!")
```

---

## Part 5: Understanding Your Architecture

### The Three Layers

#### 1. **Data Collection** (Automatic)
- **Historical**: Python scripts download from Elexon API
- **Real-time**: IRIS client streams from Azure Service Bus
- **Frequency**: Every 15 minutes (historical), every 2 seconds (real-time)
- **Storage**: BigQuery tables (cloud database)

#### 2. **Data Processing** (Automatic or Manual)
- **Automatic**: Scripts run via cron (scheduled tasks)
- **Manual**: You run Python scripts when needed
- **Output**: Updated Google Sheets, CSV reports, analysis files

#### 3. **Data Access** (You!)
- **ChatGPT**: Ask questions in English
- **Google Sheets**: Visual dashboard
- **Python scripts**: Run custom analysis
- **Direct BigQuery**: Advanced SQL queries (if you learn SQL later)

### The Security Layer

```
┌─────────────────────────────────────┐
│  PUBLIC INTERNET                    │
│  ↓                                  │
│  Vercel Proxy (API key required)    │  ← Checks you're authorized
│  ↓                                  │
│  BigQuery (service account)         │  ← Checks credentials
│  ↓                                  │
│  Your Data                          │  ← Protected!
└─────────────────────────────────────┘
```

Multiple security layers protect your data:
1. **API keys**: Only your ChatGPT can access
2. **Service accounts**: Google credentials
3. **Firewall rules**: Server access restricted
4. **Audit logs**: Every action logged

---

## Part 6: Maintenance (What You Should Do)

### Daily (Automated - Just Check)
- ✅ IRIS pipeline running (check logs if needed)
- ✅ Dashboard auto-updates every 5 minutes
- ✅ Data flowing to BigQuery

### Weekly (Manual - Do This)
```bash
# Check data freshness
python3 check_iris_data.py

# Review dashboard for anomalies
# Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

# Check server health
ssh root@94.237.55.234 'systemctl status iris-uploader'
```

### Monthly (Backup - Nice to Have)
```bash
# Export important tables from BigQuery to Cloud Storage
# (This is already set up, but you can trigger manually if needed)
```

### Never Do These (Dangerous!)
- ❌ Share credentials files
- ❌ Commit .json files to GitHub
- ❌ Delete tables in BigQuery without backup
- ❌ Stop IRIS uploader service on server
- ❌ Change credentials without updating all systems

---

## Troubleshooting for Beginners

### Problem: ChatGPT says "I can't access that right now"

**Possible causes**:
1. Vercel proxy is down
2. BigQuery credentials expired
3. Rate limit hit

**What to do**:
```bash
# Step 1: Check Vercel proxy
curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health

# If it returns JSON with "healthy", proxy is fine
# If it errors, the proxy is down (rare)

# Step 2: Wait 1 minute and try again (rate limit)

# Step 3: If still failing, check documentation or ask for help
```

### Problem: Python script says "ModuleNotFoundError"

**Cause**: Missing Python package.

**What to do**:
```bash
# Install the missing package
pip3 install package-name

# Example:
pip3 install google-cloud-bigquery
pip3 install gspread
pip3 install pandas
```

### Problem: "Access Denied" or "Credentials not found"

**Cause**: Environment variables not set.

**What to do**:
```bash
# Check if variables are set
echo $GOOGLE_APPLICATION_CREDENTIALS

# If empty, reload shell config
source ~/.zshrc

# Or restart Terminal and try again
```

### Problem: Data looks old in dashboard

**Cause**: IRIS uploader might be stuck.

**What to do**:
```bash
# SSH to server
ssh root@94.237.55.234

# Check uploader status
systemctl status iris-uploader

# If stopped, restart it
systemctl restart iris-uploader

# Check logs
tail -f /opt/iris-pipeline/logs/iris_uploader.log
# (Press Ctrl+C to stop watching)

# Exit
exit
```

### Problem: Can't connect to server

**Cause**: Tailscale not connected or server down.

**What to do**:
```bash
# Check Tailscale is running
tailscale status

# If not connected, start it
# (Usually auto-starts on Mac)

# Try pinging server
ping 94.237.55.234

# If no response, server might be down (rare)
# Check UpCloud web console
```

---

## Learning Path (What to Learn Next)

### Level 1: Current (You!)
- ✅ Ask ChatGPT questions
- ✅ View Google Sheets dashboard
- ✅ Run existing Python scripts
- ✅ Check logs for issues

### Level 2: Next Steps (1-2 months)
- 📚 Learn basic SQL (to understand ChatGPT queries)
- 📚 Understand Python basics (read existing scripts)
- 📚 Learn Git basics (commit changes properly)
- 📚 Understand cron jobs (scheduled tasks)

### Level 3: Advanced (3-6 months)
- 🚀 Write your own Python scripts
- 🚀 Create custom BigQuery queries
- 🚀 Modify ChatGPT prompts
- 🚀 Set up new data pipelines

### Resources

**SQL Learning**:
- BigQuery SQL tutorial: https://cloud.google.com/bigquery/docs/tutorials
- W3Schools SQL: https://www.w3schools.com/sql/

**Python Learning**:
- Official Python tutorial: https://docs.python.org/3/tutorial/
- Real Python (beginners): https://realpython.com/

**Your Documentation**:
- Start here: `README.md`
- Full index: `DOCUMENTATION_INDEX.md`
- Architecture: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`

---

## Quick Reference: Daily Commands

```bash
# Check ChatGPT proxy is working
curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health

# View dashboard
open "https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"

# Check IRIS pipeline (server)
ssh root@94.237.55.234 'tail -20 /opt/iris-pipeline/logs/iris_uploader.log'

# Run battery analysis
cd ~/GB\ Power\ Market\ JJ && python3 analyze_battery_vlp_final.py

# Check BigQuery connection (local)
python3 -c "from google.cloud import bigquery; import os; client = bigquery.Client(project=os.getenv('GCP_PROJECT')); print('✅ Connected!')"

# Reload environment variables
source ~/.zshrc
```

---

## Summary: You Now Understand

✅ **What you have**: ChatGPT → Vercel → BigQuery → Your data  
✅ **How to use it**: Ask ChatGPT questions in plain English  
✅ **Where things are**: Mac, servers, cloud  
✅ **How it works**: Automatic credentials from ~/.zshrc  
✅ **What to check**: Dashboard, logs, server status  
✅ **How to fix problems**: Basic troubleshooting commands  

**You're ready to use your system!** Start by asking ChatGPT some questions about your energy data. 🎉

---

**Created**: November 19, 2025  
**For**: George Major (complete novice)  
**Next steps**: Try asking ChatGPT 5 questions about your data!
