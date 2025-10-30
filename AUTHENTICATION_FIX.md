# 🔧 Authentication Fix Applied

## ✅ What Was Fixed

### Problem
The `bulk_downloader.py` script was hardcoded to require a service account JSON file at:
```
/Users/georgemajor/service-account-key.json
```

This caused the error:
```
FileNotFoundError: Service account key file not found at /Users/georgemajor/service-account-key.json
```

### Solution
Updated `bulk_downloader.py` to use **Application Default Credentials** instead.

#### Before (Lines 291-300):
```python
# Ensure GOOGLE_APPLICATION_CREDENTIALS is set to a valid path
service_account_path = "/Users/georgemajor/service-account-key.json"
if not os.path.exists(service_account_path):
    raise FileNotFoundError(f"Service account key file not found at {service_account_path}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file(service_account_path)
bq = bigquery.Client(credentials=credentials)
```

#### After:
```python
# Use Application Default Credentials (from gcloud auth login)
# No need for service account JSON file
print("🔐 Using Application Default Credentials...")

# Initialize BigQuery client with default credentials
bq = bigquery.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT", "jibber-jabber-knowledge"))
```

## 🔐 Authentication Setup

### Already Completed
✅ `gcloud auth login` - You're authenticated as `george.major@grid-smart.co.uk`

### Required (In Progress)
⏳ `gcloud auth application-default login` - Browser window opened for authorization

**Complete the authorization in your browser**, then you're ready to run!

## 🚀 How to Run

### Option 1: Quick Test (7 days of data)
```bash
cd ~/GB\ Power\ Market\ JJ/
source .venv/bin/activate

# Test connection first
python test_bigquery_connection.py

# Run ingestion for last 7 days
./run_ingestion.sh
```

### Option 2: Custom Date Range
```bash
# Specify dates
./run_ingestion.sh 2024-10-01 2024-10-25

# Specific datasets only
./run_ingestion.sh 2024-10-01 2024-10-25 "NDF DEMAND_OUTTURN FUELINST"
```

### Option 3: Full Control
```bash
# Set environment
export GOOGLE_CLOUD_PROJECT="jibber-jabber-knowledge"
export INSIGHTS_CONCURRENCY=15

# Run directly
python bulk_downloader.py \
    --start-date 2024-01-01 \
    --end-date 2025-10-25
```

### Option 4: Safe Execution (Prevents Terminal Crash)
```bash
# For heavy downloads
python ~/repo/safe_runner.py 'python bulk_downloader.py --start-date 2024-01-01 --end-date 2025-10-25'
```

## 📁 Files Created

1. **`bulk_downloader.py`** - ✅ Fixed (backup: `bulk_downloader.py.backup`)
2. **`run_ingestion.sh`** - ✅ New helper script
3. **`test_bigquery_connection.py`** - ✅ Connection test
4. **`fix_auth.py`** - ✅ Fix script (can be deleted)

## 🧪 Testing

### Step 1: Complete Browser Authentication
1. Look for the browser window that opened
2. Sign in with your Google account
3. Grant permissions

### Step 2: Test BigQuery Connection
```bash
cd ~/GB\ Power\ Market\ JJ/
source .venv/bin/activate
python test_bigquery_connection.py
```

Expected output:
```
🔐 Testing BigQuery Connection...
✅ Client initialized
   Project: jibber-jabber-knowledge
✅ Query successful!
Recent tables:
   - insights_demand_outturn (created: ...)
🎉 BigQuery connection working perfectly!
```

### Step 3: Run Small Test
```bash
# Just 1 day of data
./run_ingestion.sh 2025-10-25 2025-10-25
```

## 🐛 Troubleshooting

### If authentication fails:
```bash
# Complete application-default login
gcloud auth application-default login

# Set project
gcloud config set project jibber-jabber-knowledge

# Verify
gcloud auth list
```

### If BigQuery access denied:
```bash
# Check project permissions
gcloud projects get-iam-policy jibber-jabber-knowledge --flatten="bindings[].members" --filter="bindings.members:george.major@grid-smart.co.uk"
```

### If dependencies missing:
```bash
pip install --upgrade google-cloud-bigquery httpx pandas pyarrow python-dotenv tqdm
```

## 📝 Next Steps

1. **Complete authentication** in the browser
2. **Test connection**: `python test_bigquery_connection.py`
3. **Run small test**: `./run_ingestion.sh 2025-10-25 2025-10-25`
4. **Run full ingestion**: `./run_ingestion.sh 2024-01-01 2025-10-25`

---

**Fixed**: 26 October 2025  
**Authentication Method**: Application Default Credentials (no JSON file needed)
