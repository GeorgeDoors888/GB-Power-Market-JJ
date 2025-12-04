# 📦 Installation Guide

Complete setup instructions for the GB-Power-Market-JJ - BESS Dashboard & Energy Analysis System.

---

## 📋 Prerequisites

### System Requirements
- **Operating System:** macOS, Linux, or Windows with WSL2
- **Python:** 3.9 or higher
- **Node.js:** 16+ (for clasp CLI)
- **Memory:** 4GB RAM minimum
- **Storage:** 500MB free space

### Account Requirements
- **Google Cloud Platform**
  - Active GCP project
  - BigQuery API enabled
  - Service account with credentials
  
- **Google Workspace**
  - Access to Google Sheets
  - Apps Script deployment permissions
  - Google Drive storage

- **Network Access**
  - Outbound HTTPS to googleapis.com
  - Outbound HTTPS to script.google.com
  - Outbound HTTPS to vercel.app (for proxy)

---

## 🚀 Step-by-Step Installation

### Step 1: Verify Python Installation

```bash
# Check Python version
python3 --version
# Should show: Python 3.9.x or higher

# Check pip
pip3 --version

# Upgrade pip if needed
python3 -m pip install --upgrade pip
```

### Step 2: Clone/Navigate to Repository

```bash
cd "/Users/georgemajor/GB-Power-Market-JJ"
# Repository should already exist

# Verify files present
ls -la
# Should see: requirements.txt, apps-script/, *.py files
```

### Step 3: Install Python Dependencies

```bash
# Install all required packages
pip3 install -r requirements.txt

# Expected output:
# Successfully installed gspread-6.2.1 google-cloud-bigquery-3.25.0 
# pandas-2.2.3 numpy-2.1.3 matplotlib-3.9.2 seaborn-0.13.2 ...
```

**Verify Installation:**
```bash
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")

try:
    import gspread
    print(f"✅ gspread {gspread.__version__}")
except ImportError as e:
    print(f"❌ gspread: {e}")

try:
    from google.cloud import bigquery
    print(f"✅ google-cloud-bigquery {bigquery.__version__}")
except ImportError as e:
    print(f"❌ google-cloud-bigquery: {e}")

try:
    import pandas as pd
    print(f"✅ pandas {pd.__version__}")
except ImportError as e:
    print(f"❌ pandas: {e}")

try:
    import numpy as np
    print(f"✅ numpy {np.__version__}")
except ImportError as e:
    print(f"❌ numpy: {e}")

try:
    import matplotlib
    print(f"✅ matplotlib {matplotlib.__version__}")
except ImportError as e:
    print(f"❌ matplotlib: {e}")

try:
    import seaborn as sns
    print(f"✅ seaborn {sns.__version__}")
except ImportError as e:
    print(f"❌ seaborn: {e}")

print("\n✅ All core packages verified!")
EOF
```

### Step 4: Configure Google Cloud Credentials

#### Option A: Service Account (Recommended)

1. **Locate Credentials File**
   ```bash
   # File should be named: inner-cinema-credentials.json
   # Location: workspace root
   ls -la inner-cinema-credentials.json
   ```

2. **If Missing, Download from GCP**
   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Project: `inner-cinema-476211-u9`
   - Find service account
   - Click "Keys" tab
   - "Add Key" → "Create new key" → JSON
   - Download and rename to `inner-cinema-credentials.json`
   - Move to workspace root

3. **Verify Permissions**
   ```bash
   python3 << 'EOF'
   from google.cloud import bigquery
   from google.oauth2 import service_account
   
   credentials = service_account.Credentials.from_service_account_file(
       'inner-cinema-credentials.json',
       scopes=['https://www.googleapis.com/auth/bigquery']
   )
   
   client = bigquery.Client(
       credentials=credentials,
       project='inner-cinema-476211-u9'
   )
   
   # Test query
   query = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_prices` LIMIT 1"
   try:
       result = list(client.query(query).result())
       print(f"✅ BigQuery access verified: {result[0].count:,} records")
   except Exception as e:
       print(f"❌ BigQuery access failed: {e}")
   EOF
   ```

4. **Add to .gitignore**
   ```bash
   # Ensure credentials are NOT committed to git
   echo "inner-cinema-credentials.json" >> .gitignore
   git check-ignore inner-cinema-credentials.json
   # Should output: inner-cinema-credentials.json
   ```

#### Option B: User Credentials (Alternative)

```bash
gcloud auth application-default login
# Follow browser prompts to authenticate
```

### Step 5: Install Node.js and Clasp (for Apps Script)

#### Install Node.js

**macOS (Homebrew):**
```bash
brew install node
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Verify:**
```bash
node --version  # Should show v16.x or higher
npm --version   # Should show 8.x or higher
```

#### Install Clasp

```bash
npm install -g @google/clasp

# Verify installation
clasp --version
# Should show: 2.4.x or higher
```

#### Login to Clasp

```bash
clasp login
# Opens browser for Google authentication
# Grant permissions to clasp
# Should see: "Authorization successful"
```

### Step 6: Configure Apps Script Deployment

#### Verify .clasp.json

```bash
cat .clasp.json
# Should show:
# {
#   "scriptId": "1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz",
#   "rootDir": "./apps-script"
# }
```

#### Verify apps-script Directory

```bash
ls -la apps-script/
# Should show:
# Code.gs (383 lines)
# appsscript.json
```

#### Test Clasp Connection

```bash
clasp list
# Should show your Apps Script projects including:
# 1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz - BESS Tools
```

### Step 7: Deploy Apps Script

#### Option A: Clasp Push (Automated)

```bash
cd "/Users/georgemajor/GB-Power-Market-JJ"
clasp push

# Expected output:
# └─ apps-script/Code.gs
# └─ apps-script/appsscript.json
# Pushed 2 files.
```

**Verify Deployment:**
```bash
clasp open
# Opens Apps Script editor in browser
# Verify Code.gs contains 383 lines with all functions
```

#### Option B: Manual Copy-Paste (If Clasp Fails)

1. **Open Apps Script Editor**
   ```
   https://script.google.com/d/1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz/edit
   ```

2. **Delete Existing Code**
   - Click in editor
   - Cmd+A (Select All)
   - Delete

3. **Copy Local Code**
   ```bash
   # macOS
   cat apps-script/Code.gs | pbcopy
   
   # Linux
   cat apps-script/Code.gs | xclip -selection clipboard
   ```

4. **Paste in Editor**
   - Cmd+V in Apps Script editor
   - Click 💾 Save
   - Wait for "Saved" confirmation

5. **Refresh Dashboard**
   - Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
   - Cmd+R (Refresh page)
   - Look for "🔋 BESS Tools" menu in menu bar

### Step 8: Verify Installation

#### Test Python Scripts

```bash
# Test PPA Arbitrage (quick test with sample data)
python3 << 'EOF'
from calculate_ppa_arbitrage import get_system_prices
import datetime

# Test with 7 days
start = datetime.datetime.now() - datetime.timedelta(days=7)
end = datetime.datetime.now()
prices = get_system_prices(start, end)

if prices and len(prices) > 0:
    print(f"✅ PPA Arbitrage: {len(prices)} prices fetched")
else:
    print("⚠️  Using sample data (BigQuery may not be accessible)")
    print("   Script will still work with fallback data")
EOF

# Test Google Sheets connection
python3 << 'EOF'
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    credentials = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
    print(f"✅ Google Sheets: Connected to '{sheet.title}'")
except Exception as e:
    print(f"❌ Google Sheets: {e}")
EOF
```

#### Test Apps Script Menu

1. Open Dashboard V2
2. Look for "🔋 BESS Tools" menu
3. Click menu → Should show 8 items:
   - 🔄 Refresh DNO Data
   - ✅ Validate MPAN
   - 📍 Validate Postcode
   - 📊 Generate HH Profile
   - 💰 Calculate PPA Arbitrage
   - 📈 Show Status
   - ℹ️ Help & Instructions

4. Test a function:
   - Click "📈 Show Status"
   - Should show popup with current settings

### Step 9: Initial Configuration

#### Set Up BESS Sheet

1. **Open Dashboard V2**
   ```
   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
   ```

2. **Configure Basic Settings**
   - Cell A6: Enter postcode (e.g., "SW2 5UP")
   - Cell B6: Enter MPAN ID (10-23)
   - Cell A10: Select voltage level (LV/HV/EHV)
   - Cell B21: Enter PPA price (e.g., "150")

3. **Refresh DNO Data**
   - Menu: 🔋 BESS Tools → 🔄 Refresh DNO Data
   - Wait for status update in A4
   - Verify B6:H6 populated with DNO details
   - Verify B10:D10 populated with DUoS rates

4. **Generate HH Profile**
   - Set Min kW (B17): e.g., "500"
   - Set Avg kW (B18): e.g., "1500"
   - Set Max kW (B19): e.g., "2500"
   - Menu: 🔋 BESS Tools → 📊 Generate HH Profile
   - Verify rows 22-69 populated

### Step 10: Run First Analysis

```bash
cd "/Users/georgemajor/GB-Power-Market-JJ"

# Run PPA Arbitrage Analysis
echo "Running PPA Arbitrage Analysis..."
python3 calculate_ppa_arbitrage.py
# Expected: ~60 seconds
# Output: Rows 90-162 in BESS sheet

# Run Revenue Calculator
echo "Running Revenue Calculator..."
python3 calculate_bess_revenue.py
# Expected: ~45 seconds
# Output: Rows 170-205 in BESS sheet

# Generate Visualizations
echo "Generating Charts..."
python3 visualize_ppa_costs.py
# Expected: ~30 seconds
# Output: ppa_cost_analysis.png, ppa_cost_summary.png, Rows 210-245

# Update Dashboard Controls
echo "Updating Dashboard..."
python3 update_bess_dashboard.py
# Expected: ~20 seconds
# Output: Time period dropdown (L6), Cost table (A250:F285)
```

---

## ✅ Installation Checklist

### Python Environment
- [ ] Python 3.9+ installed
- [ ] pip upgraded to latest
- [ ] All packages from requirements.txt installed
- [ ] Import test passes for all packages

### Google Cloud
- [ ] Service account credentials downloaded
- [ ] File named `inner-cinema-credentials.json`
- [ ] File in workspace root directory
- [ ] File added to .gitignore
- [ ] BigQuery access verified
- [ ] Google Sheets access verified

### Apps Script
- [ ] Node.js 16+ installed
- [ ] Clasp installed globally
- [ ] Clasp login successful
- [ ] .clasp.json configured
- [ ] apps-script/ directory present
- [ ] Apps Script deployed (clasp push OR manual)
- [ ] Menu appears in Dashboard V2
- [ ] Test function works (Show Status)

### Dashboard Configuration
- [ ] Dashboard V2 accessible
- [ ] BESS sheet present
- [ ] Basic settings configured (MPAN, voltage, PPA)
- [ ] DNO data refreshed successfully
- [ ] HH profile generated
- [ ] Time period dropdown visible (L6)
- [ ] Cost breakdown table visible (A250:F285)

### Analysis Scripts
- [ ] PPA Arbitrage runs successfully
- [ ] Revenue Calculator runs successfully
- [ ] Visualization generates PNG files
- [ ] Dashboard Update completes
- [ ] All output rows populated correctly

---

## 🚨 Troubleshooting Installation Issues

### Python Package Installation Fails

**Issue:** `pip install -r requirements.txt` fails with errors

**Solutions:**

1. **Upgrade pip:**
   ```bash
   python3 -m pip install --upgrade pip setuptools wheel
   ```

2. **Install packages individually:**
   ```bash
   pip3 install gspread==6.2.1
   pip3 install google-cloud-bigquery==3.25.0
   pip3 install pandas==2.2.3
   # ... etc
   ```

3. **Use virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

### Clasp Login Fails

**Issue:** `clasp login` opens browser but authentication fails

**Solutions:**

1. **Clear clasp credentials:**
   ```bash
   rm ~/.clasprc.json
   clasp login
   ```

2. **Use different browser:**
   ```bash
   clasp login --no-localhost
   # Follow manual authentication flow
   ```

3. **Check Google account permissions:**
   - Ensure account has Apps Script access
   - Check organization policies don't block clasp

### Apps Script Not Deploying

**Issue:** `clasp push` fails with authentication error

**Solutions:**

1. **Re-authenticate:**
   ```bash
   clasp logout
   clasp login
   clasp push
   ```

2. **Use manual deployment:**
   - See "Option B: Manual Copy-Paste" above
   - This always works when clasp fails

### BigQuery Access Denied

**Issue:** Python scripts fail with BigQuery 403 errors

**Solutions:**

1. **Verify service account permissions:**
   - Go to GCP Console → IAM
   - Find service account
   - Ensure roles: BigQuery Data Viewer, BigQuery Job User

2. **Regenerate service account key:**
   - GCP Console → Service Accounts
   - Create new key
   - Download as `inner-cinema-credentials.json`

3. **Use sample data fallback:**
   - Scripts automatically use sample data if BigQuery unavailable
   - No action needed - analysis will still work

### Google Sheets Access Denied

**Issue:** gspread fails with 403 errors

**Solutions:**

1. **Share spreadsheet with service account:**
   - Open Dashboard V2
   - Share → Add service account email
   - Grant "Editor" permission

2. **Verify scopes in credentials:**
   ```python
   scopes = [
       'https://www.googleapis.com/auth/spreadsheets',
       'https://www.googleapis.com/auth/drive'
   ]
   ```

---

## 📚 Next Steps

After successful installation:

1. **Read [ARCHITECTURE.md](ARCHITECTURE.md)** - Understand system design
2. **Read [APPS_SCRIPT_GUIDE.md](APPS_SCRIPT_GUIDE.md)** - Learn Apps Script features
3. **Read [API_REFERENCE.md](API_REFERENCE.md)** - Explore function APIs
4. **Read [CONFIGURATION.md](CONFIGURATION.md)** - Advanced settings

---

**Installation Complete! 🎉**

You're now ready to analyze BESS revenue and optimize battery operations.
