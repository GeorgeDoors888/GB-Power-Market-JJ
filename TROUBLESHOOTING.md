# 🔧 Troubleshooting Guide

Comprehensive issue resolution for the BESS Dashboard system.

---

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Python Environment](#python-environment)
- [Google Cloud Access](#google-cloud-access)
- [Apps Script](#apps-script)
- [BigQuery](#bigquery)
- [Google Sheets API](#google-sheets-api)
- [Clasp Deployment](#clasp-deployment)
- [Data Issues](#data-issues)
- [Performance](#performance)
- [Network & Connectivity](#network--connectivity)

---

## 🚀 Quick Diagnostics

### System Health Check

Run this diagnostic script to check all components:

```bash
#!/bin/bash
# diagnose_bess.sh

echo "🔍 BESS System Diagnostics"
echo "=========================="

# 1. Python version
echo -e "\n📦 Python:"
python3 --version || echo "❌ Python not found"

# 2. Required packages
echo -e "\n📚 Python Packages:"
python3 -c "import gspread; print('✅ gspread', gspread.__version__)" 2>/dev/null || echo "❌ gspread"
python3 -c "import google.cloud.bigquery; print('✅ bigquery')" 2>/dev/null || echo "❌ bigquery"
python3 -c "import pandas; print('✅ pandas', pandas.__version__)" 2>/dev/null || echo "❌ pandas"
python3 -c "import matplotlib; print('✅ matplotlib', matplotlib.__version__)" 2>/dev/null || echo "❌ matplotlib"

# 3. Credentials
echo -e "\n🔑 Credentials:"
if [ -f "credentials.json" ]; then
  echo "✅ credentials.json found"
  ls -lh credentials.json | awk '{print "   Size:", $5}'
else
  echo "❌ credentials.json missing"
fi

# 4. BigQuery access
echo -e "\n💾 BigQuery:"
python3 << EOF 2>/dev/null
try:
    from google.cloud import bigquery
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'
    client = bigquery.Client(project='inner-cinema-476211-u9')
    query = "SELECT COUNT(*) as count FROM \`inner-cinema-476211-u9.uk_energy_prod.balancing_prices\` LIMIT 1"
    result = list(client.query(query).result())
    print(f"✅ BigQuery accessible ({result[0].count:,} rows)")
except Exception as e:
    print(f"❌ BigQuery error: {e}")
EOF

# 5. Sheets access
echo -e "\n📊 Google Sheets:"
python3 << EOF 2>/dev/null
try:
    import gspread
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials.json'
    gc = gspread.service_account(filename='credentials.json')
    sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
    print(f"✅ Sheets accessible: {sheet.title}")
except Exception as e:
    print(f"❌ Sheets error: {e}")
EOF

# 6. Node & Clasp
echo -e "\n🔧 Node.js & Clasp:"
node --version 2>/dev/null && echo "✅ Node.js" || echo "❌ Node.js not found"
clasp --version 2>/dev/null && echo "✅ Clasp" || echo "❌ Clasp not found"

# 7. Apps Script config
echo -e "\n📝 Apps Script:"
if [ -f ".clasp.json" ]; then
  echo "✅ .clasp.json found"
  cat .clasp.json
else
  echo "❌ .clasp.json missing"
fi

# 8. Dashboard URL
echo -e "\n🔗 Dashboard:"
echo "   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"

echo -e "\n✅ Diagnostics Complete"
```

**Usage:**
```bash
chmod +x diagnose_bess.sh
./diagnose_bess.sh
```

---

## 🐍 Python Environment

### Issue: Module Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'gspread'
```

**Solution 1: Install Missing Package**
```bash
# Install specific package
pip3 install gspread

# Or reinstall all requirements
pip3 install -r requirements.txt
```

**Solution 2: Virtual Environment**
```bash
# Create venv
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Run scripts
python calculate_ppa_arbitrage.py
```

**Solution 3: Check Python Version**
```bash
# Must be 3.9+
python3 --version

# If using multiple versions
python3.9 -m pip install -r requirements.txt
python3.9 calculate_ppa_arbitrage.py
```

### Issue: ImportError with BigQuery

**Symptom:**
```
ImportError: cannot import name 'bigquery' from 'google.cloud'
```

**Cause:** Conflicting `google` packages

**Solution:**
```bash
# Uninstall all google packages
pip3 uninstall google google-cloud google-api-core google-cloud-bigquery

# Reinstall cleanly
pip3 install google-cloud-bigquery==3.25.0
```

### Issue: SSL Certificate Error

**Symptom:**
```
ssl.SSLCertVerificationError: certificate verify failed
```

**Solution (macOS):**
```bash
# Install certificates
/Applications/Python\ 3.9/Install\ Certificates.command

# Or use conda
conda install certifi
```

**Solution (Linux):**
```bash
# Update CA certificates
sudo apt-get update
sudo apt-get install ca-certificates
```

### Issue: Pandas FutureWarning

**Symptom:**
```
FutureWarning: The default value of numeric_only in DataFrameGroupBy.sum is deprecated
```

**Solution:**
```python
# Update pandas
pip3 install --upgrade pandas==2.2.3

# Or suppress warnings in script
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
```

---

## ☁️ Google Cloud Access

### Issue: Credentials Not Found

**Symptom:**
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution 1: Check File Location**
```bash
# Verify file exists
ls -l credentials.json

# Should be in project root
pwd
# Output: /Users/georgemajor/GB-Power-Market-JJ

# If elsewhere, move it
mv ~/Downloads/credentials.json .
```

**Solution 2: Set Environment Variable**
```bash
# Temporary (current session)
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/credentials.json"

# Permanent (add to ~/.zshrc)
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/GB-Power-Market-JJ/credentials.json"' >> ~/.zshrc
source ~/.zshrc
```

**Solution 3: Verify JSON Format**
```bash
# Check file is valid JSON
python3 -c "import json; json.load(open('credentials.json'))"

# Should have these keys
python3 << EOF
import json
creds = json.load(open('credentials.json'))
required = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
for key in required:
    if key in creds:
        print(f"✅ {key}")
    else:
        print(f"❌ {key} missing")
EOF
```

### Issue: Permission Denied (403)

**Symptom:**
```
google.api_core.exceptions.Forbidden: 403 Permission denied on resource project inner-cinema-476211-u9
```

**Cause:** Service account lacks IAM roles

**Solution:**
1. **Open GCP Console:**
   ```
   https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9
   ```

2. **Find Service Account:**
   - Email format: `bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com`
   - Look in IAM permissions list

3. **Add Required Roles:**
   - Click ✏️ Edit
   - Add Role: `BigQuery Data Viewer`
   - Add Role: `BigQuery Job User`
   - Click Save

4. **For Sheets Access:**
   - Open Dashboard: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
   - Click Share
   - Add service account email
   - Give Editor access

5. **Test Access:**
   ```python
   from google.cloud import bigquery
   client = bigquery.Client(project='inner-cinema-476211-u9')
   query = "SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_prices`"
   result = list(client.query(query).result())
   print(f"✅ Access granted: {result[0][0]:,} rows")
   ```

### Issue: Project Not Found

**Symptom:**
```
google.api_core.exceptions.NotFound: 404 Project 'inner-cinema-476211-u9' not found
```

**Solution:**
1. Verify project ID:
   ```bash
   # Check credentials.json
   python3 -c "import json; print(json.load(open('credentials.json'))['project_id'])"
   ```

2. List your projects:
   ```bash
   gcloud projects list
   ```

3. Update project ID in scripts if different

### Issue: Quota Exceeded

**Symptom:**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Solution:**
1. **Check Current Usage:**
   - Go to: https://console.cloud.google.com/apis/api/bigquery.googleapis.com/quotas?project=inner-cinema-476211-u9

2. **BigQuery Free Tier:**
   - 1 TB query data processed/month
   - 10 GB storage
   - 2,000 free streaming inserts/day

3. **Sheets API Limits:**
   - 100 requests per 100 seconds per user
   - 500 requests per 100 seconds per project

4. **Add Delays:**
   ```python
   import time
   
   # Between BigQuery queries
   time.sleep(2)  # 2 seconds
   
   # Between Sheets updates
   time.sleep(1)
   ```

---

## 📜 Apps Script

### Issue: Menu Not Appearing

**Symptom:** "🔋 BESS Tools" menu doesn't show after opening spreadsheet

**Solution 1: Refresh Page**
```
1. Press Cmd+R (Mac) or Ctrl+R (Windows)
2. Wait for page to fully reload
3. Check menu bar
```

**Solution 2: Re-deploy Apps Script**
```bash
# Via clasp
clasp push
clasp open

# Or manual:
# 1. Copy apps-script/Code.gs
# 2. Paste into Apps Script editor
# 3. Save
# 4. Refresh spreadsheet
```

**Solution 3: Check onOpen() Function**
```javascript
// In Apps Script editor, click Run → onOpen
// Should see "Execution log" with no errors

function testMenu() {
  onOpen();  // Manually trigger
}
```

**Solution 4: Check Permissions**
```
1. Open Apps Script: script.google.com
2. Click project name
3. Check "This app has access to:"
   - Google Sheets
   - External requests (UrlFetchApp)
4. If missing, re-authorize:
   - Run → Run function → onOpen
   - Click "Review Permissions"
   - Allow access
```

### Issue: Function Not Found

**Symptom:**
```
Script function refreshDnoLookup could not be found
```

**Cause:** Function name mismatch between menu and code

**Solution:**
```javascript
// Menu calls this name:
.addItem('🔄 Refresh DNO Data', 'refreshDnoLookup')

// Function must match exactly:
function refreshDnoLookup() {  // ← Exact match
  refreshDnoData();
}

// Common mistakes:
function refresh_dno_lookup() {  // ❌ Underscore
function RefreshDnoLookup() {    // ❌ Capitalization
function refreshDNOLookup() {     // ❌ Different capitalization
```

**Fix:**
1. Check function name in menu:
   ```javascript
   function onOpen() {
     ui.createMenu('🔋 BESS Tools')
       .addItem('Menu Text', 'functionName')  // ← This must match function
   ```

2. Ensure function exists:
   ```javascript
   function functionName() {
     // Implementation
   }
   ```

3. Re-deploy and refresh spreadsheet

### Issue: Auto-Trigger Not Working

**Symptom:** Editing cell B6 doesn't trigger DNO lookup

**Debug Steps:**

1. **Check onEdit() Exists:**
   ```javascript
   // Search for this function in Code.gs
   function onEdit(e) {
     // Should exist
   }
   ```

2. **Test Manually:**
   ```javascript
   // Add test function
   function testOnEdit() {
     const e = {
       source: SpreadsheetApp.getActive(),
       range: SpreadsheetApp.getActive().getRange('B6'),
       value: '14'
     };
     onEdit(e);
   }
   
   // Run this function
   // Check if it triggers refreshDnoData()
   ```

3. **Check Sheet Name:**
   ```javascript
   function onEdit(e) {
     const sheet = e.source.getActiveSheet();
     Logger.log('Sheet name: ' + sheet.getName());  // Add this
     
     if (sheet.getName() !== 'BESS') {
       Logger.log('Wrong sheet, exiting');
       return;
     }
     // ...
   }
   ```

4. **View Execution Log:**
   - Apps Script editor
   - View → Executions
   - Look for `onEdit` entries
   - Check for errors

5. **Common Issues:**
   ```javascript
   // ❌ BAD: Triggers on any edit
   function onEdit(e) {
     refreshDnoData();  // Too broad
   }
   
   // ✅ GOOD: Specific cell check
   function onEdit(e) {
     const range = e.range;
     if (range.getRow() === 6 && range.getColumn() === 2) {  // B6
       refreshDnoData();
     }
   }
   ```

### Issue: BigQuery Request Failed

**Symptom:**
```
Exception: Request failed for https://gb-power-market-jj.vercel.app/api/proxy-v2 returned code 500
```

**Solution 1: Check Vercel Proxy**
```bash
# Test proxy directly
curl -X POST https://gb-power-market-jj.vercel.app/api/proxy-v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT 1 as test"}'

# Should return JSON
# If 500, proxy has issue
```

**Solution 2: Check Query Syntax**
```javascript
// In Apps Script, log the query
function refreshDnoData() {
  const query = `SELECT * FROM neso_dno_reference WHERE mpan_id = '${mpanId}'`;
  Logger.log('Query: ' + query);  // Add this
  
  // Send query...
}

// Check log for SQL errors
```

**Solution 3: Add Error Handling**
```javascript
function queryBigQuery(sqlQuery) {
  const url = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
  
  try {
    const response = UrlFetchApp.fetch(url, {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({ query: sqlQuery }),
      'muteHttpExceptions': true  // ← Important!
    });
    
    const code = response.getResponseCode();
    const text = response.getContentText();
    
    Logger.log('Status: ' + code);
    Logger.log('Response: ' + text);
    
    if (code !== 200) {
      throw new Error('HTTP ' + code + ': ' + text);
    }
    
    return JSON.parse(text);
    
  } catch (error) {
    Logger.log('Error: ' + error);
    Browser.msgBox('BigQuery Error', error.toString(), Browser.Buttons.OK);
    throw error;
  }
}
```

### Issue: Script Timeout (30 seconds)

**Symptom:**
```
Exceeded maximum execution time
```

**Cause:** Apps Script has 30-second limit per execution

**Solution:**
```javascript
// ❌ BAD: Loop 1000 times
for (let i = 0; i < 1000; i++) {
  sheet.getRange(i, 1).setValue(i);  // Each call is slow
}

// ✅ GOOD: Batch update
const data = [];
for (let i = 0; i < 1000; i++) {
  data.push([i]);
}
sheet.getRange(1, 1, data.length, 1).setValues(data);  // Single call

// ✅ GOOD: Use SpreadsheetApp.flush()
for (let i = 0; i < 10; i++) {
  sheet.getRange('A4').setValue('Processing ' + i);
  SpreadsheetApp.flush();  // Update display
  // ... long operation ...
}
```

---

## 💾 BigQuery

### Issue: Table Not Found

**Symptom:**
```
google.api_core.exceptions.NotFound: 404 Not found: Table inner-cinema-476211-u9:uk_energy_prod.balancing_prices
```

**Solution 1: Verify Table Name**
```python
from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')

# List all tables
dataset = client.get_dataset('uk_energy_prod')
tables = list(client.list_tables(dataset))

print("Available tables:")
for table in tables:
    print(f"  - {table.table_id}")

# Expected output:
#   - balancing_prices
#   - duos_tariff_rates
#   - dno_duos_rates
#   - neso_dno_reference
```

**Solution 2: Check Dataset**
```python
# List all datasets
datasets = list(client.list_datasets())
print("Available datasets:")
for dataset in datasets:
    print(f"  - {dataset.dataset_id}")
```

**Solution 3: Use Full Table ID**
```python
# Always use fully-qualified name
query = """
SELECT * 
FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_prices`
WHERE date >= '2024-01-01'
LIMIT 10
"""
```

### Issue: Query Timeout

**Symptom:**
```
google.api_core.exceptions.DeadlineExceeded: 408 Deadline exceeded
```

**Solution 1: Add LIMIT**
```python
# ❌ BAD: Scans entire table
query = "SELECT * FROM `...balancing_prices`"

# ✅ GOOD: Limit rows
query = "SELECT * FROM `...balancing_prices` LIMIT 1000"
```

**Solution 2: Use Partition Pruning**
```python
# ❌ BAD: Full table scan
query = """
SELECT * FROM `...balancing_prices`
WHERE EXTRACT(YEAR FROM date) = 2024
"""

# ✅ GOOD: Partition pruning
query = """
SELECT * FROM `...balancing_prices`
WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
"""
```

**Solution 3: Increase Timeout**
```python
from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')

# Set job config with timeout
job_config = bigquery.QueryJobConfig()
job_config.use_query_cache = True
job_config.timeout_ms = 60000  # 60 seconds

query_job = client.query(query, job_config=job_config)
results = query_job.result(timeout=120)  # Wait up to 2 minutes
```

### Issue: Slow Query Performance

**Symptom:** Query takes > 30 seconds

**Optimization 1: Check Query Plan**
```python
# Get execution statistics
job = client.query(query)
result = job.result()

print(f"Total bytes processed: {job.total_bytes_processed:,}")
print(f"Total bytes billed: {job.total_bytes_billed:,}")
print(f"Slot milliseconds: {job.slot_millis:,}")
print(f"Cache hit: {job.cache_hit}")
```

**Optimization 2: Use SELECT Columns**
```python
# ❌ BAD: Returns all columns
query = "SELECT * FROM `...balancing_prices`"

# ✅ GOOD: Only needed columns
query = """
SELECT 
  settlement_date,
  settlement_period,
  ssp
FROM `...balancing_prices`
"""
```

**Optimization 3: Enable Caching**
```python
job_config = bigquery.QueryJobConfig()
job_config.use_query_cache = True  # Use cached results
```

### Issue: Data Not Up-to-Date

**Symptom:** Missing recent balancing prices

**Check Last Update:**
```python
query = """
SELECT 
  MAX(settlement_date) as latest_date,
  COUNT(*) as total_rows
FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_prices`
"""

result = list(client.query(query).result())
print(f"Latest data: {result[0].latest_date}")
print(f"Total rows: {result[0].total_rows:,}")
```

**Expected:**
- Latest date: Within 1-2 days of today
- Total rows: ~35,000+ (growing daily)

**If Outdated:**
1. Check data pipeline (separate system)
2. Use sample data fallback in scripts
3. Contact data provider

---

## 📊 Google Sheets API

### Issue: Worksheet Not Found

**Symptom:**
```
gspread.exceptions.WorksheetNotFound: BESS
```

**Solution:**
```python
import gspread

gc = gspread.service_account(filename='credentials.json')
sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')

# List all worksheets
print("Available worksheets:")
for worksheet in sheet.worksheets():
    print(f"  - {worksheet.title}")

# Access specific worksheet
try:
    worksheet = sheet.worksheet('BESS')
except gspread.WorksheetNotFound:
    # Create if missing
    worksheet = sheet.add_worksheet(title='BESS', rows=300, cols=15)
```

### Issue: Rate Limit Exceeded

**Symptom:**
```
gspread.exceptions.APIError: 429 RESOURCE_EXHAUSTED
```

**Cause:** Google Sheets API limits:
- 100 requests per 100 seconds per user
- 500 requests per 100 seconds per project

**Solution 1: Batch Updates**
```python
# ❌ BAD: 48 separate requests
for i, value in enumerate(values):
    worksheet.update_cell(i+1, 1, value)

# ✅ GOOD: 1 request
worksheet.update('A1:A48', [[v] for v in values])
```

**Solution 2: Add Delays**
```python
import time

for batch in batches:
    worksheet.update('A1:Z10', batch)
    time.sleep(2)  # 2-second delay between batches
```

**Solution 3: Use Exponential Backoff**
```python
import time
from gspread.exceptions import APIError

def update_with_retry(worksheet, range, values, max_retries=5):
    for attempt in range(max_retries):
        try:
            worksheet.update(range, values)
            return
        except APIError as e:
            if '429' in str(e):
                wait = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
                print(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} retries")
```

### Issue: Permission Denied

**Symptom:**
```
gspread.exceptions.APIError: 403 Insufficient Permission
```

**Solution:**
1. **Share Spreadsheet:**
   ```
   1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
   2. Click "Share" button
   3. Add service account email (from credentials.json)
   4. Give "Editor" access
   5. Click "Send"
   ```

2. **Verify Email:**
   ```python
   import json
   
   creds = json.load(open('credentials.json'))
   print(f"Service account: {creds['client_email']}")
   # Copy this email
   ```

3. **Check Scopes:**
   ```python
   # Verify scopes in credentials
   import google.auth
   from google.oauth2 import service_account
   
   SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
   creds = service_account.Credentials.from_service_account_file(
       'credentials.json',
       scopes=SCOPES
   )
   ```

---

## 🔧 Clasp Deployment

### Issue: Clasp Not Found

**Symptom:**
```bash
zsh: command not found: clasp
```

**Solution:**
```bash
# Install Node.js (if needed)
# macOS
brew install node

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node
node --version  # Should be 16+
npm --version

# Install clasp globally
npm install -g @google/clasp

# Verify clasp
clasp --version

# If permission error
sudo npm install -g @google/clasp
```

### Issue: Not Logged In

**Symptom:**
```
Error: You need to login first.
```

**Solution:**
```bash
# Login to clasp
clasp login

# This will:
# 1. Open browser
# 2. Ask for Google account
# 3. Request permissions
# 4. Show "Authorization successful"

# If browser doesn't open
clasp login --no-localhost

# Then paste URL manually
```

### Issue: Invalid Grant

**Symptom:**
```
Error: invalid_grant
invalid_rapt
```

**Cause:** Clasp authentication expired (happens after ~1 week)

**Solution:**
```bash
# Clear credentials
rm ~/.clasprc.json

# Or logout via clasp
clasp logout

# Re-authenticate
clasp login

# Try push again
clasp push
```

### Issue: Script Not Found

**Symptom:**
```
Error: Could not find script.
```

**Solution 1: Check .clasp.json**
```bash
# Verify file exists
cat .clasp.json

# Should contain:
{
  "scriptId": "1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz",
  "rootDir": "./apps-script"
}

# If missing, create it
cat > .clasp.json << 'EOF'
{
  "scriptId": "1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz",
  "rootDir": "./apps-script"
}
EOF
```

**Solution 2: List Projects**
```bash
# See all your Apps Script projects
clasp list

# Should show project with ID
```

**Solution 3: Clone Project**
```bash
# If .clasp.json wrong, re-clone
rm .clasp.json

clasp clone 1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz
```

### Issue: Push Conflicts

**Symptom:**
```
Manifest file has been updated. Do you want to push and overwrite?
```

**Solution:**
```bash
# Option 1: Overwrite remote (use local version)
# Type 'yes' at prompt

# Option 2: Pull remote first
clasp pull

# Then resolve conflicts manually
# Then push
clasp push
```

---

## 📈 Data Issues

### Issue: Missing DNO Data

**Symptom:** B6:H6 empty after refresh

**Debug:**
```python
from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')

# Check table contents
query = """
SELECT 
  mpan_id,
  dno_name,
  dno_short_code
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
ORDER BY CAST(mpan_id AS INT64)
"""

result = list(client.query(query).result())

print("Available MPAN IDs:")
for row in result:
    print(f"  {row.mpan_id}: {row.dno_name} ({row.dno_short_code})")
```

**Expected:** 14 rows (MPAN 10-23)

**If Missing:**
1. Re-import reference data
2. Check BigQuery table exists
3. Use sample data fallback

### Issue: Incorrect DUoS Rates

**Symptom:** B10:D10 showing wrong rates

**Verify:**
```python
query = """
SELECT 
  dno_code,
  voltage_level,
  time_band,
  rate_p_per_kwh
FROM `inner-cinema-476211-u9.uk_energy_prod.duos_tariff_rates`
WHERE dno_code = 'NGED'
  AND voltage_level = 'LV'
ORDER BY 
  CASE time_band
    WHEN 'RED' THEN 1
    WHEN 'AMBER' THEN 2
    WHEN 'GREEN' THEN 3
  END
"""

result = list(client.query(query).result())

for row in result:
    print(f"{row.time_band}: {row.rate_p_per_kwh} p/kWh")
```

**Check:**
- RED should be highest (e.g., 8.00-12.00 p/kWh)
- GREEN should be lowest (e.g., 0.30-0.60 p/kWh)
- Values realistic for 2024/25 rates

### Issue: PPA Results Not Appearing

**Symptom:** Rows 90-162 empty after running script

**Solution 1: Check Script Output**
```bash
# Run with verbose logging
python3 calculate_ppa_arbitrage.py 2>&1 | tee ppa_output.log

# Look for errors
grep -i error ppa_output.log
grep -i exception ppa_output.log
```

**Solution 2: Verify Sheet Access**
```python
# Test Sheets write access
import gspread

gc = gspread.service_account(filename='credentials.json')
sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
worksheet = sheet.worksheet('BESS')

# Try writing test data
worksheet.update('A90', [['TEST']])
print("✅ Write successful")

# Clean up
worksheet.update('A90', [['']])
```

**Solution 3: Check Row Range**
```python
# Verify script writes to correct rows
# In calculate_ppa_arbitrage.py, look for:
start_row = 90
end_row = start_row + len(data)
print(f"Writing to rows {start_row}-{end_row}")

# Should be 90-162 (73 rows for 24 months × 3 bands)
```

---

## ⚡ Performance

### Issue: Scripts Taking Too Long

**Current Timing:**
- `calculate_ppa_arbitrage.py`: ~60s
- `calculate_bess_revenue.py`: ~45s
- `visualize_ppa_costs.py`: ~30s
- `update_bess_dashboard.py`: ~20s
- **Total:** ~155s (2.5 minutes)

**Target:**
- PPA: 45s (-25%)
- Revenue: 30s (-33%)
- Visualize: 20s (-33%)
- Update: 15s (-25%)
- **Total:** ~110s (1.8 minutes)

**Optimization 1: Use Query Cache**
```python
from google.cloud import bigquery

job_config = bigquery.QueryJobConfig()
job_config.use_query_cache = True  # Enable caching

query_job = client.query(query, job_config=job_config)
```

**Optimization 2: Vectorize Pandas**
```python
import pandas as pd

# ❌ BAD: Row-by-row iteration (slow)
for idx, row in df.iterrows():
    df.loc[idx, 'total'] = row['price'] * row['volume']

# ✅ GOOD: Vectorized operation (fast)
df['total'] = df['price'] * df['volume']
```

**Optimization 3: Batch Sheets Updates**
```python
# ❌ BAD: Multiple updates
for row_data in data:
    worksheet.append_row(row_data)

# ✅ GOOD: Single batch update
worksheet.update(f'A{start_row}:Z{end_row}', data)
```

**Optimization 4: Use Local Cache**
```python
import pickle
import os
from datetime import datetime, timedelta

CACHE_FILE = 'bigquery_cache.pkl'
CACHE_HOURS = 24

def fetch_with_cache(query):
    # Check cache
    if os.path.exists(CACHE_FILE):
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if cache_age < timedelta(hours=CACHE_HOURS):
            print("Using cached data")
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
    
    # Fetch from BigQuery
    print("Fetching from BigQuery")
    result = list(client.query(query).result())
    
    # Save to cache
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(result, f)
    
    return result
```

### Issue: High Memory Usage

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solution 1: Process in Chunks**
```python
# Instead of loading all data
df = pd.read_gbq(query)  # May be huge

# Process in date chunks
dates = pd.date_range('2024-01-01', '2025-12-31', freq='M')

results = []
for start, end in zip(dates[:-1], dates[1:]):
    query = f"""
    SELECT * FROM `...balancing_prices`
    WHERE date BETWEEN '{start.date()}' AND '{end.date()}'
    """
    chunk = pd.read_gbq(query, project_id='inner-cinema-476211-u9')
    results.append(process_chunk(chunk))

final_df = pd.concat(results)
```

**Solution 2: Use dtypes**
```python
# Reduce memory by specifying dtypes
df = pd.read_csv('data.csv', dtype={
    'settlement_period': 'int8',  # 1-48
    'ssp': 'float32',  # Don't need float64
    'volume': 'float32'
})
```

---

## 🌐 Network & Connectivity

### Issue: Cannot Reach Vercel Proxy

**Symptom:**
```
URLError: <urlopen error [Errno 60] Operation timed out>
```

**Solution 1: Test Connectivity**
```bash
# Test Vercel URL
curl -X POST https://gb-power-market-jj.vercel.app/api/proxy-v2 \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT 1"}'

# Should return JSON
# If timeout, network issue
```

**Solution 2: Check Firewall**
```bash
# Check if port 443 (HTTPS) is open
nc -zv gb-power-market-jj.vercel.app 443

# Should show "succeeded"
```

**Solution 3: Use Different Network**
- Try cellular hotspot
- Check corporate firewall settings
- VPN may block requests

### Issue: SSL Verification Failed

**Symptom:**
```
ssl.SSLCertVerificationError: certificate verify failed
```

**Solution (Temporary - Not Recommended):**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with retries
session = requests.Session()
retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)

# Make request
response = session.post(url, json=payload, timeout=30)
```

**Solution (Permanent):**
```bash
# macOS: Install certificates
/Applications/Python\ 3.9/Install\ Certificates.command

# Linux: Update CA bundle
sudo apt-get update
sudo apt-get install --reinstall ca-certificates

# Python: Update certifi
pip3 install --upgrade certifi
```

---

## 📞 Getting Help

### Log Files

**Location:** `logs/` directory

**Files:**
- `ppa_arbitrage_YYYYMMDD.log`
- `bess_revenue_YYYYMMDD.log`
- `visualization_YYYYMMDD.log`
- `dashboard_update_YYYYMMDD.log`

**Retention:** 7 days

**Check Recent Logs:**
```bash
# View latest PPA log
ls -t logs/ppa_arbitrage_*.log | head -1 | xargs cat

# Search for errors
grep -i error logs/*.log
grep -i exception logs/*.log
```

### System Information

```bash
# Python
python3 --version
pip3 list | grep -E 'gspread|bigquery|pandas'

# Node
node --version
npm list -g @google/clasp

# OS
sw_vers  # macOS
lsb_release -a  # Linux

# Credentials
ls -lh credentials.json
```

### Contact Support

**GitHub Issues:**
```
Repository: GeorgeDoors888/GB-Power-Market-JJ
URL: https://github.com/GeorgeDoors888/GB-Power-Market-JJ/issues
```

**Include:**
1. Error message (full text)
2. Command that failed
3. System info (Python version, OS)
4. Log files (if applicable)
5. Steps to reproduce

---

**Next Steps:**
- [Apps Script Guide](APPS_SCRIPT_GUIDE.md) - Function reference
- [API Reference](API_REFERENCE.md) - Python documentation
- [Installation](INSTALLATION.md) - Setup guide
