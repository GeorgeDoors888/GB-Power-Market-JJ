# 🚀 Deployment Guide

Production deployment procedures for the BESS Dashboard system.

---

## 📋 Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Initial Deployment](#initial-deployment)
- [Apps Script Deployment](#apps-script-deployment)
- [Python Environment](#python-environment)
- [Credentials Management](#credentials-management)
- [Monitoring Setup](#monitoring-setup)
- [Backup Procedures](#backup-procedures)
- [Update Procedures](#update-procedures)
- [Rollback Process](#rollback-process)

---

## ✅ Pre-Deployment Checklist

### Infrastructure

- [ ] Google Cloud Project created: `inner-cinema-476211-u9`
- [ ] BigQuery dataset exists: `uk_energy_prod`
- [ ] BigQuery tables populated:
  - [ ] `balancing_prices` (~35k rows)
  - [ ] `duos_tariff_rates` (207 rows)
  - [ ] `dno_duos_rates` (time bands)
  - [ ] `neso_dno_reference` (14 DNOs)
- [ ] Google Sheets Dashboard created: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
- [ ] Apps Script project created: `1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz`

### Credentials

- [ ] Service account created: `bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com`
- [ ] IAM roles assigned:
  - [ ] `BigQuery Data Viewer`
  - [ ] `BigQuery Job User`
- [ ] Service account key downloaded: `credentials.json`
- [ ] Key file permissions set: `chmod 600 credentials.json`
- [ ] Key added to `.gitignore`
- [ ] Dashboard shared with service account (Editor access)

### Local Environment

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] Clasp CLI installed globally
- [ ] Repository cloned
- [ ] `requirements.txt` dependencies installed
- [ ] Environment variables configured

### Configuration Files

- [ ] `.clasp.json` configured with scriptId
- [ ] `apps-script/Code.gs` ready (383 lines)
- [ ] `apps-script/appsscript.json` configured
- [ ] `config/battery_params.json` (if using)
- [ ] `config/fixed_levies.json` (if using)

---

## 🏁 Initial Deployment

### Step 1: Clone Repository

```bash
cd ~/
git clone https://github.com/GeorgeDoors888/GB-Power-Market-JJ.git
cd GB-Power-Market-JJ
```

**Verification:**
```bash
ls -la
# Should see:
# - requirements.txt
# - .clasp.json
# - apps-script/
# - *.py files
```

---

### Step 2: Setup Python Environment

**Option A: System Python**
```bash
# Verify Python version
python3 --version  # Must be 3.9+

# Upgrade pip
python3 -m pip install --upgrade pip

# Install dependencies
pip3 install -r requirements.txt

# Verify installations
python3 << 'EOF'
import gspread
import google.cloud.bigquery
import pandas
import matplotlib
print("✅ All packages installed successfully")
EOF
```

**Option B: Virtual Environment (Recommended)**
```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify
python --version
pip list | grep gspread
```

**Environment Variable:**
```bash
# Add to ~/.zshrc or ~/.bashrc
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$PWD/credentials.json"' >> ~/.zshrc
source ~/.zshrc

# Verify
echo $GOOGLE_APPLICATION_CREDENTIALS
```

---

### Step 3: Deploy Credentials

**Download Service Account Key:**
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=inner-cinema-476211-u9
2. Click service account: `bess-dashboard@...`
3. Click Keys → Add Key → Create New Key → JSON
4. Download file

**Deploy to Project:**
```bash
# Copy to project root
cp ~/Downloads/inner-cinema-*.json credentials.json

# Set permissions
chmod 600 credentials.json

# Verify format
python3 << 'EOF'
import json
with open('credentials.json') as f:
    creds = json.load(f)
    print(f"✅ Project: {creds['project_id']}")
    print(f"✅ Email: {creds['client_email']}")
EOF
```

**Security Check:**
```bash
# Ensure not tracked by git
git check-ignore credentials.json
# Should output: credentials.json

# If not ignored:
echo "credentials.json" >> .gitignore
git add .gitignore
git commit -m "Add credentials to gitignore"
```

---

### Step 4: Deploy Apps Script

**Method A: Clasp (Automated)**
```bash
# Install clasp
npm install -g @google/clasp

# Login
clasp login
# Opens browser → Authorize

# Verify configuration
cat .clasp.json
# Should show scriptId: 1svUewU3Q0n77...

# Push to Apps Script
clasp push

# Expected output:
# └─ apps-script/Code.gs
# └─ apps-script/appsscript.json
# Pushed 2 files.

# Open in browser to verify
clasp open
# Check:
# - 383 lines of code
# - onOpen() function exists
# - All functions present
```

**Method B: Manual (If clasp fails)**
```bash
# Open Apps Script editor
open "https://script.google.com/d/1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz/edit"

# Copy local code
cat apps-script/Code.gs | pbcopy  # macOS
# OR
cat apps-script/Code.gs | xclip -selection clipboard  # Linux

# In Apps Script editor:
# 1. Select all (Cmd+A)
# 2. Delete
# 3. Paste (Cmd+V)
# 4. Save (Cmd+S)
# 5. Wait for "Saved" message

# Verify line count
wc -l apps-script/Code.gs
# Should show: 383
```

---

### Step 5: Configure Dashboard

**Share with Service Account:**
1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
2. Click Share button
3. Add: `bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com`
4. Permission: Editor
5. Uncheck "Notify people"
6. Click Share

**Initial Configuration:**
```bash
# Open dashboard in browser
open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"

# Configure cells:
# A6: Postcode (e.g., "B33 8TH")
# B6: MPAN ID (e.g., 14)
# A10: Voltage ("LV")
# B17: Min kW (500)
# B18: Avg kW (1500)
# B19: Max kW (2500)
# B21: PPA Price (150.00)
# L6: Period ("90 Days")

# Refresh page (Cmd+R)
# Look for menu: "🔋 BESS Tools"
```

**Test Menu:**
```
1. Click: 🔋 BESS Tools → 🔄 Refresh DNO Data
2. Wait 3-5 seconds
3. Verify B6:H6 populated with DNO details
4. Verify B10:D10 shows DUoS rates
```

---

### Step 6: Run Initial Analysis

**Test Python Scripts:**
```bash
# Test 1: PPA Arbitrage (60s)
echo "Running PPA Arbitrage analysis..."
python3 calculate_ppa_arbitrage.py

# Check output:
# - Rows 90-162 should be populated
# - 73 rows (24 months × 3 bands + header)

# Test 2: Revenue Calculator (45s)
echo "Running Revenue calculation..."
python3 calculate_bess_revenue.py

# Check output:
# - Rows 170-205 populated
# - Revenue breakdown visible

# Test 3: Visualization (30s)
echo "Generating charts..."
python3 visualize_ppa_costs.py

# Check output:
# - ppa_cost_analysis.png created (664 KB)
# - ppa_cost_summary.png created (477 KB)
# - Rows 210-245 populated

# Test 4: Dashboard Update (20s)
echo "Updating dashboard..."
python3 update_bess_dashboard.py

# Check output:
# - L6 dropdown created
# - Rows 250-285 table created

# Total runtime: ~155 seconds (2.5 minutes)
```

**Verify Results:**
```bash
# Check log files
ls -lh logs/
# Should see:
# - ppa_arbitrage_YYYYMMDD.log
# - bess_revenue_YYYYMMDD.log
# - visualization_YYYYMMDD.log
# - dashboard_update_YYYYMMDD.log

# Check charts
ls -lh *.png
# ppa_cost_analysis.png (~664 KB)
# ppa_cost_summary.png (~477 KB)

# View dashboard
open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"
# Verify all output ranges populated
```

---

## 🔐 Credentials Management

### Service Account Key Rotation

**Schedule:** Every 90 days

**Process:**
```bash
# 1. Create new key
# Go to: GCP Console → IAM → Service Accounts
# Click account → Keys → Add Key → Create new key → JSON
# Download new key

# 2. Test new key
mv credentials.json credentials.json.old
cp ~/Downloads/inner-cinema-*.json credentials.json

# 3. Verify access
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = "SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_prices`"
result = list(client.query(query).result())
print(f"✅ BigQuery access verified: {result[0][0]:,} rows")
EOF

# 4. Run test scripts
python3 calculate_ppa_arbitrage.py
# If successful:

# 5. Delete old key
rm credentials.json.old

# 6. Delete old key from GCP Console
# IAM → Service Accounts → Keys → Delete old key
```

---

## 📊 Monitoring Setup

### Script Execution Monitoring

```bash
cat > monitor_bess.sh << 'EOF'
#!/bin/bash

LOG_DIR="logs"

check_log() {
    local script=$1
    local log_file="${LOG_DIR}/${script}_$(date +%Y%m%d).log"
    
    if [ ! -f "$log_file" ]; then
        echo "❌ $script: No log file today"
        return 1
    fi
    
    if grep -q "ERROR" "$log_file"; then
        echo "❌ $script: Errors found"
        return 1
    fi
    
    echo "✅ $script: OK"
    return 0
}

echo "🔍 Monitoring BESS Scripts"
check_log "ppa_arbitrage"
check_log "bess_revenue"
check_log "visualization"
check_log "dashboard_update"

echo "✅ Monitoring complete"
EOF

chmod +x monitor_bess.sh

# Schedule monitoring (every 6 hours)
crontab -e
# Add: 0 */6 * * * /path/to/monitor_bess.sh
```

---

## 💾 Backup Procedures

### Automated Dashboard Backup

```bash
cat > backup_dashboard.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/bess_${TIMESTAMP}.csv"

python3 << PYTHON
import gspread
import pandas as pd

gc = gspread.service_account(filename='credentials.json')
sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
worksheet = sheet.worksheet('BESS')
data = worksheet.get_all_values()
df = pd.DataFrame(data)
df.to_csv('${BACKUP_FILE}', index=False)
PYTHON

echo "✅ Backup saved: ${BACKUP_FILE}"

# Keep only last 30 days
find "$BACKUP_DIR" -name "bess_*.csv" -mtime +30 -delete
EOF

chmod +x backup_dashboard.sh

# Schedule daily backups (2 AM)
crontab -e
# Add: 0 2 * * * /path/to/backup_dashboard.sh
```

---

## 🔄 Update Procedures

### Python Scripts Update

```bash
# 1. Pull latest changes
git pull origin main

# 2. Check for dependency changes
diff requirements.txt <(git show HEAD~1:requirements.txt)

# 3. Update dependencies if changed
pip3 install --upgrade -r requirements.txt

# 4. Run tests
python3 calculate_ppa_arbitrage.py
python3 calculate_bess_revenue.py

# 5. Verify output
open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"
```

### Apps Script Update

```bash
# 1. Backup current version
clasp pull
cp apps-script/Code.gs "backups/Code_$(date +%Y%m%d)_pre_update.gs"

# 2. Update local code
# Edit apps-script/Code.gs

# 3. Deploy to production
clasp push

# 4. Verify in dashboard
open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"

# 5. Commit to git
git add apps-script/Code.gs
git commit -m "Update Apps Script: [description]"
git push
```

---

## ⏪ Rollback Process

### Apps Script Rollback

```bash
# 1. Find previous version
ls -lt backups/Code_*.gs | head -5

# 2. Copy to apps-script/
cp backups/Code_20241115.gs apps-script/Code.gs

# 3. Deploy
clasp push

# 4. Verify
open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"
```

---

## 📞 Support

**Documentation:**
- [Installation Guide](INSTALLATION.md)
- [Architecture](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [API Reference](API_REFERENCE.md)

**GitHub Issues:**
https://github.com/GeorgeDoors888/GB-Power-Market-JJ/issues

---

✅ **Deployment Complete**

Your BESS Dashboard system is now fully deployed and operational.
