# 🔐 Google Workspace & BigQuery Access - Universal Setup Guide

**For**: GB Power Market JJ Project  
**Purpose**: Enable all GitHub repos to access BigQuery Smart Grid account and Google Drive (george@upowerenergy.uk)  
**Audience**: Novice-friendly with detailed steps

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [One-Time Setup (Do This Once)](#one-time-setup)
4. [Automatic Propagation to All Repos](#automatic-propagation)
5. [ChatGPT Integration](#chatgpt-integration)
6. [Testing & Verification](#testing--verification)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This guide sets up automatic access to:
- **BigQuery**: `inner-cinema-476211-u9` project (UK energy data)
- **Google Drive**: `george@upowerenergy.uk` workspace
- **Google Sheets**: Dashboard access
- **ChatGPT**: Natural language queries to your data

### What You'll Achieve

✅ **All repos** automatically have credentials  
✅ **New clones** work immediately  
✅ **ChatGPT** can query your BigQuery data  
✅ **No manual credential copying** needed

---

## Prerequisites

### What You Need

1. ✅ **Google Cloud Service Account** (you already have this)
   - File: `inner-cinema-credentials.json`
   - Project: `inner-cinema-476211-u9`

2. ✅ **Google Workspace Credentials** (you already have this)
   - File: `workspace-credentials.json`
   - Domain: `upowerenergy.uk`
   - User: `george@upowerenergy.uk`

3. ✅ **Mac with Git** (you have this)

4. ✅ **GitHub account** (GeorgeDoors888)

---

## One-Time Setup (Do This Once)

### Step 1: Create Credentials Directory

```bash
# Create a central location for credentials
mkdir -p ~/.google-credentials
chmod 700 ~/.google-credentials  # Only you can access
```

**What this does**: Creates a hidden folder in your home directory that all projects will reference.

### Step 2: Copy Credentials Files

```bash
# Copy BigQuery credentials
cp inner-cinema-credentials.json ~/.google-credentials/

# Copy Workspace credentials (if you have it)
cp workspace-credentials.json ~/.google-credentials/

# Secure them
chmod 600 ~/.google-credentials/*.json
```

**What this does**: 
- Stores credentials centrally (not in each repo)
- Sets permissions so only you can read them
- Prevents accidental commits to GitHub

### Step 3: Set Environment Variables Globally

Add these lines to your `~/.zshrc` (Mac default shell):

```bash
# Open your shell config
nano ~/.zshrc

# Add these lines at the end:
# ===================================
# Google Credentials (GB Power Market)
# ===================================
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.google-credentials/inner-cinema-credentials.json"
export GOOGLE_WORKSPACE_CREDENTIALS="$HOME/.google-credentials/workspace-credentials.json"
export GCP_PROJECT="inner-cinema-476211-u9"
export BQ_DATASET="uk_energy_prod"
export BQ_LOCATION="US"
export SHEETS_ID="1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Save: Ctrl+O, Enter, Ctrl+X

# Apply changes
source ~/.zshrc
```

**What this does**:
- Sets environment variables that Python scripts will read
- Loads automatically every time you open a terminal
- Works for all repos and scripts

### Step 4: Verify Setup

```bash
# Check environment variables
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should show: /Users/georgemajor/.google-credentials/inner-cinema-credentials.json

echo $GCP_PROJECT
# Should show: inner-cinema-476211-u9

# Check file exists and is readable
ls -la ~/.google-credentials/
# Should show both .json files with -rw------- permissions

# Test BigQuery access
python3 -c "
from google.cloud import bigquery
import os
client = bigquery.Client(
    project=os.getenv('GCP_PROJECT'),
    location=os.getenv('BQ_LOCATION')
)
print('✅ BigQuery connected!')
print(f'Project: {client.project}')
"
```

**Expected output:**
```
✅ BigQuery connected!
Project: inner-cinema-476211-u9
```

---

## Automatic Propagation to All Repos

### How It Works

With environment variables set in `~/.zshrc`, **all Python scripts automatically use them**:

```python
import os
from google.cloud import bigquery

# This automatically uses GOOGLE_APPLICATION_CREDENTIALS
client = bigquery.Client(project=os.getenv('GCP_PROJECT'))
```

### For Existing Repos

**No changes needed!** Scripts that use these environment variables will work immediately.

If a script has hardcoded paths, update them:

```python
# ❌ OLD (hardcoded):
credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)

# ✅ NEW (uses environment):
import os
credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)
```

### For New Repos

When you clone or create a new repo:

```bash
# Clone repo
git clone https://github.com/GeorgeDoors888/new-energy-project.git
cd new-energy-project

# Credentials already work! Just verify:
python3 -c "import os; print(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))"
```

### Template for New Python Scripts

Save this as a template for any new script:

```python
#!/usr/bin/env python3
"""
Template: BigQuery & Google Sheets Access
Uses credentials from environment variables
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT", "inner-cinema-476211-u9")
DATASET = os.getenv("BQ_DATASET", "uk_energy_prod")
LOCATION = os.getenv("BQ_LOCATION", "US")
SHEETS_ID = os.getenv("SHEETS_ID")

# BigQuery client (uses GOOGLE_APPLICATION_CREDENTIALS automatically)
bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

# Google Sheets client (needs explicit workspace credentials)
workspace_creds = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_WORKSPACE_CREDENTIALS'),
    scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
).with_subject('george@upowerenergy.uk')

sheets_client = gspread.authorize(workspace_creds)

# Example: Query BigQuery
def query_bigquery():
    query = f"""
    SELECT DATE(settlementDate) as date, AVG(price) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
    WHERE settlementDate >= '2025-11-01'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 7
    """
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} rows from BigQuery")
    return df

# Example: Update Google Sheet
def update_sheet():
    sheet = sheets_client.open_by_key(SHEETS_ID)
    worksheet = sheet.worksheet('Dashboard')
    worksheet.update('A1', [['Last Updated', 'Now']])
    print("✅ Updated Google Sheet")

if __name__ == "__main__":
    query_bigquery()
    update_sheet()
```

---

## ChatGPT Integration

### Architecture Overview

```
ChatGPT (you ask questions)
    ↓
Vercel Proxy (vercel-proxy/api/proxy-v2)
    ↓
BigQuery (inner-cinema-476211-u9)
    ↓
Returns data to ChatGPT
    ↓
ChatGPT formats answer for you
```

### Current Setup (Already Working)

Your ChatGPT custom GPT is configured with:

1. **Vercel Endpoint**: `https://gb-power-market-jj.vercel.app/api/proxy-v2`
2. **Actions**: Query BigQuery, read Sheets, check system status
3. **Security**: API key validation, SQL injection prevention

### How to Use ChatGPT (Novice Guide)

#### 1. Access Your Custom GPT

```
Open ChatGPT → Your GPTs → "GB Power Market Assistant"
```

#### 2. Ask Natural Language Questions

**Example Queries:**

```
"What was the average electricity price last week?"

"Show me the top 5 generating units yesterday"

"What's the current system frequency?"

"When did we last have negative prices?"

"Show me battery storage VLP activity today"

"What's the generation mix right now?"

"Compare wind vs gas generation this month"
```

#### 3. ChatGPT Translates to SQL

Behind the scenes, ChatGPT:
1. Converts your question to SQL
2. Sends it to Vercel proxy
3. Vercel queries BigQuery
4. Returns data
5. ChatGPT formats the answer

**You see:**
```
The average price last week was £45.23/MWh. Here's the breakdown by day:
- Monday: £42.50
- Tuesday: £48.10
...
```

#### 4. Advanced: Ask for Raw Data

```
"Give me the SQL query for last week's prices"

"Export the last 100 rows of frequency data as CSV"
```

### Vercel Deployment (Already Done)

Your Vercel proxy is deployed at:
- **URL**: https://gb-power-market-jj.vercel.app
- **Repo**: `vercel-proxy/` folder
- **Status**: ✅ Production

To update:
```bash
cd vercel-proxy
# Make changes to api/proxy-v2.js
vercel --prod
```

### Railway Deployment (Alternative - Optional)

You also have a Railway deployment for workspace access:
- **Script**: `railway_google_workspace_endpoints.py`
- **Purpose**: Read/write Google Sheets from ChatGPT
- **Status**: Available if needed

---

## Testing & Verification

### Quick Test Suite

Run this to verify everything works:

```bash
cd ~/GB\ Power\ Market\ JJ

# Test 1: Environment variables
echo "Testing environment variables..."
printenv | grep -E "GOOGLE|GCP|BQ_|SHEETS" && echo "✅ Variables set" || echo "❌ Variables missing"

# Test 2: Credentials files exist
echo -e "\nTesting credential files..."
[ -f ~/.google-credentials/inner-cinema-credentials.json ] && echo "✅ BigQuery creds found" || echo "❌ BigQuery creds missing"
[ -f ~/.google-credentials/workspace-credentials.json ] && echo "✅ Workspace creds found" || echo "❌ Workspace creds missing"

# Test 3: BigQuery access
echo -e "\nTesting BigQuery access..."
python3 -c "
from google.cloud import bigquery
import os
client = bigquery.Client(project=os.getenv('GCP_PROJECT'))
query = 'SELECT COUNT(*) as count FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\` LIMIT 1'
result = client.query(query).result()
print('✅ BigQuery access working!')
"

# Test 4: Google Sheets access
echo -e "\nTesting Google Sheets access..."
python3 -c "
import gspread
from google.oauth2 import service_account
import os

creds = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_WORKSPACE_CREDENTIALS'),
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv('SHEETS_ID'))
print(f'✅ Sheets access working! Dashboard: {sheet.title}')
"

# Test 5: ChatGPT proxy
echo -e "\nTesting ChatGPT proxy..."
curl -s "https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health" && echo -e "\n✅ Vercel proxy responding" || echo "❌ Proxy not responding"
```

### Expected Output

```
Testing environment variables...
GOOGLE_APPLICATION_CREDENTIALS=/Users/georgemajor/.google-credentials/inner-cinema-credentials.json
GCP_PROJECT=inner-cinema-476211-u9
...
✅ Variables set

Testing credential files...
✅ BigQuery creds found
✅ Workspace creds found

Testing BigQuery access...
✅ BigQuery access working!

Testing Google Sheets access...
✅ Sheets access working! Dashboard: GB Energy Dashboard

Testing ChatGPT proxy...
{"status":"healthy","service":"GB Power Market Proxy"...}
✅ Vercel proxy responding
```

---

## Troubleshooting

### Problem: "Could not automatically determine credentials"

**Cause**: Environment variable not set or pointing to wrong file.

**Fix**:
```bash
# Check what it's set to
echo $GOOGLE_APPLICATION_CREDENTIALS

# If empty or wrong, set it:
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.google-credentials/inner-cinema-credentials.json"

# Make permanent:
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.google-credentials/inner-cinema-credentials.json"' >> ~/.zshrc
source ~/.zshrc
```

### Problem: "Access Denied: jibber-jabber-knowledge"

**Cause**: Using wrong GCP project (you have two).

**Fix**:
```python
# Always use inner-cinema-476211-u9 (NOT jibber-jabber-knowledge)
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
```

### Problem: "Table not found in europe-west2"

**Cause**: Using wrong location (tables are in `US`, not `europe-west2`).

**Fix**:
```python
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
```

### Problem: ChatGPT says "API error"

**Causes & Fixes**:

1. **Vercel proxy down**:
```bash
# Check status
curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health

# Redeploy if needed
cd vercel-proxy && vercel --prod
```

2. **SQL error**: Check ChatGPT used correct table names
   - Use: `bmrs_mid`, `bmrs_fuelinst`, `bmrs_freq`
   - NOT: `prices`, `generation` (these don't exist)

3. **Rate limit**: Wait 1 minute, try again

### Problem: New repo doesn't have access

**Fix**:
```bash
# In the new repo directory
cd ~/new-energy-project

# Check environment
printenv | grep GOOGLE_APPLICATION_CREDENTIALS

# If empty, you need to source your shell config
source ~/.zshrc

# Or restart terminal
```

---

## Summary: What You've Set Up

### ✅ Central Credentials
- Location: `~/.google-credentials/`
- Files: `inner-cinema-credentials.json`, `workspace-credentials.json`
- Permissions: Secure (600)

### ✅ Environment Variables
- Loaded automatically in every terminal
- Used by all Python scripts
- No hardcoded paths needed

### ✅ Automatic Propagation
- All existing repos work immediately
- New clones work without setup
- Template available for new scripts

### ✅ ChatGPT Integration
- Custom GPT connected to your data
- Natural language queries
- Real-time BigQuery access

### ✅ Zero Maintenance
- Credentials in one place
- Update once, works everywhere
- No per-repo configuration

---

## Quick Reference Card

### File Locations
```
~/.google-credentials/inner-cinema-credentials.json  # BigQuery
~/.google-credentials/workspace-credentials.json     # Sheets/Drive
~/.zshrc                                             # Environment config
```

### Environment Variables
```bash
$GOOGLE_APPLICATION_CREDENTIALS  # BigQuery credentials
$GOOGLE_WORKSPACE_CREDENTIALS    # Sheets/Drive credentials
$GCP_PROJECT                      # inner-cinema-476211-u9
$BQ_DATASET                       # uk_energy_prod
$BQ_LOCATION                      # US
$SHEETS_ID                        # Dashboard ID
```

### Key Commands
```bash
# Reload environment
source ~/.zshrc

# Test BigQuery
python3 check_bigquery_access.py

# Test ChatGPT proxy
curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health

# Deploy Vercel changes
cd vercel-proxy && vercel --prod
```

### Support Documentation
- Main guide: `GOOGLE_WORKSPACE_UNIVERSAL_SETUP.md` (this file)
- ChatGPT specifics: `CHATGPT_ACTUAL_ACCESS.md`
- Project config: `PROJECT_CONFIGURATION.md`
- Architecture: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`

---

**Created**: November 19, 2025  
**For**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production Ready  
**Next Review**: When adding new repos or credentials
