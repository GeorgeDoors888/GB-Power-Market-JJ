# Google Sheets API Connection Timeout - Root Cause Analysis

**Issue Date**: December 29, 2025
**Affected Scripts**: `export_btm_sites_to_csv.py`, `add_single_price_frequency_and_regime.py`
**Status**: WORKAROUND DEPLOYED (mock data), PERMANENT FIX PENDING

---

## Problem Description

Multiple Python scripts using `gspread` library experience **connection timeouts** when attempting to authenticate with Google Sheets API:

```python
gc = gspread.service_account(filename="inner-cinema-credentials.json")
spreadsheet = gc.open_by_key(SPREADSHEET_ID)  # ⬅️ HANGS HERE
```

**Symptoms**:
- Script hangs indefinitely at `open_by_key()` call
- No error message, just silent hang
- Requires manual termination (Ctrl+C)
- Affects **only** Google Sheets connections (BigQuery works fine)

---

## Probable Root Causes

### 1. OAuth Token Refresh Issue (Most Likely)
**Theory**: Service account token expired/invalid, refresh request timing out

**Evidence**:
- gspread 6.2.1 uses OAuth2 token refresh mechanism
- Timeout occurs during authentication, not data retrieval
- BigQuery uses same service account but different auth flow

**Test**:
```bash
# Check if credentials file valid
python3 -c "from google.oauth2 import service_account; creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json'); print('✅ Credentials loaded')"

# Try gspread connection with timeout
timeout 10s python3 -c "import gspread; gc = gspread.service_account(); print('✅ Connected')"
```

**Fix**:
```python
# Add explicit timeout to gspread connection
import socket
socket.setdefaulttimeout(30)  # 30 second timeout

gc = gspread.service_account(filename="inner-cinema-credentials.json")
```

---

### 2. Google API Rate Limiting
**Theory**: Too many rapid API requests triggering rate limit

**Evidence**:
- Multiple scripts running in sequence (Task 1 EWAP → Task 2 frequency)
- Google Sheets API has 100 requests/100 seconds/user limit

**Test**:
```bash
# Check recent API usage
python3 <<'EOF'
from google.cloud import bigquery
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")

# Count recent BigQuery jobs (proxy for API activity)
query = "SELECT job_id, creation_time FROM `region-us`.INFORMATION_SCHEMA.JOBS WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)"
jobs = list(client.query(query).result())
print(f"Recent API jobs (5 min): {len(jobs)}")
EOF
```

**Fix**:
```python
import time
# Add delay between Google API calls
time.sleep(2)  # 2 seconds between requests
```

---

### 3. Network/Firewall Issue
**Theory**: Outbound HTTPS connections to `sheets.googleapis.com` blocked or slow

**Evidence**:
- AlmaLinux server 94.237.55.234 may have firewall rules
- BigQuery uses different endpoint (`bigquery.googleapis.com`)

**Test**:
```bash
# Test Google Sheets API endpoint connectivity
curl -I https://sheets.googleapis.com/v4/spreadsheets/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

# Check DNS resolution
nslookup sheets.googleapis.com

# Test with timeout
timeout 5s curl https://sheets.googleapis.com
```

**Fix**:
```bash
# Check firewall rules (if on server)
sudo firewall-cmd --list-all

# Test from different location (local machine vs server)
ssh root@94.237.55.234 'python3 -c "import gspread; gc = gspread.service_account(); print(\"OK\")"'
```

---

### 4. Service Account Permissions Issue
**Theory**: Service account missing required Google Sheets API scopes

**Evidence**:
- BigQuery works (has `bigquery` scope)
- Sheets may require explicit `spreadsheets` scope

**Test**:
```bash
# Check service account scopes in credentials JSON
python3 <<'EOF'
import json
with open("inner-cinema-credentials.json") as f:
    creds = json.load(f)
    print("Service account:", creds.get("client_email"))
    print("Private key ID:", creds.get("private_key_id"))
    # Note: Scopes are NOT in credentials file, they're requested at runtime
EOF
```

**Fix**:
```python
from google.oauth2 import service_account

# Explicitly set scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=SCOPES
)

gc = gspread.authorize(credentials)
```

---

### 5. gspread Library Bug
**Theory**: gspread 6.2.1 has connection timeout bug

**Evidence**:
- Recent gspread versions (6.x) changed authentication flow
- Issue may be version-specific

**Test**:
```bash
# Check gspread version
pip3 show gspread

# Try older version
pip3 install --user 'gspread==5.12.0'

# Or try latest
pip3 install --user --upgrade gspread
```

**Fix**:
```bash
# Downgrade to known-working version
pip3 install --user 'gspread==5.12.0'

# OR use Google Sheets API v4 directly (bypass gspread)
pip3 install --user google-api-python-client
```

---

## Recommended Fixes (Priority Order)

### Priority 1: Add Connection Timeout (Quick Fix)
```python
#!/usr/bin/env python3
"""
export_btm_sites_to_csv_v2.py - With timeout handling
"""
import signal
import gspread

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Google Sheets connection timed out")

# Set alarm for 60 seconds
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)

try:
    gc = gspread.service_account(filename="inner-cinema-credentials.json")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet("BESS")
    signal.alarm(0)  # Cancel alarm
    print("✅ Connected to Google Sheets")
except TimeoutException:
    print("❌ Connection timed out after 60 seconds")
    # Fallback to mock data or cached data
    use_fallback_data()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    use_fallback_data()
```

### Priority 2: Retry Logic with Exponential Backoff
```python
import time

def connect_with_retry(max_retries=3, initial_delay=5):
    """Connect to Google Sheets with exponential backoff"""
    for attempt in range(max_retries):
        try:
            delay = initial_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1}/{max_retries} (timeout: {delay}s)...")

            signal.alarm(delay)
            gc = gspread.service_account(filename="inner-cinema-credentials.json")
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            signal.alarm(0)

            print("✅ Connected successfully")
            return spreadsheet

        except TimeoutException:
            if attempt == max_retries - 1:
                print(f"❌ Failed after {max_retries} attempts")
                raise
            print(f"⚠️ Timeout, retrying in {delay} seconds...")
            time.sleep(delay)
```

### Priority 3: Switch to Google Sheets API v4 (Bypass gspread)
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=SCOPES
)

service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)

# Read data
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='BESS!A40:B100'
).execute()

values = result.get('values', [])
print(f"✅ Retrieved {len(values)} rows via Sheets API v4")
```

### Priority 4: Use Alternative OAuth Flow
```python
# Instead of service account, use user OAuth
gc = gspread.oauth(
    credentials_filename='oauth-credentials.json',  # OAuth client credentials
    authorized_user_filename='authorized-user.json'  # Cached user token
)

# First run will open browser for authorization
# Subsequent runs use cached token
```

---

## Workaround Currently Deployed

**File**: `export_btm_sites_mock.py`
**Approach**: Bypass Google Sheets entirely, use mock BtM site data

**Mock Data**:
```python
MOCK_BTM_SITES = [
    {"row_number": 1, "site_name": "Drax Battery Storage", "postcode": "YO8 8PH"},
    {"row_number": 2, "site_name": "Cottam BESS", "postcode": "DN22 0HU"},
    # ... 8 more sites with real UK postcodes
]
```

**Geocoding**: Direct postcodes.io API calls (no Google Sheets dependency)

**Limitation**: Not using real BtM site data from Live Dashboard v2

---

## Testing Plan

### Test 1: Timeout Isolation
```bash
# Test gspread connection with explicit timeout
timeout 30s python3 -c "
import gspread
gc = gspread.service_account(filename='inner-cinema-credentials.json')
print('✅ Service account loaded')
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
print('✅ Spreadsheet opened')
sheet = spreadsheet.worksheet('BESS')
print('✅ Worksheet loaded')
"
```

### Test 2: Alternative Auth Method
```bash
# Test OAuth flow instead of service account
python3 <<'EOF'
import gspread
gc = gspread.oauth()  # Will open browser for user authorization
print("✅ OAuth authentication successful")
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
print("✅ Spreadsheet opened")
EOF
```

### Test 3: API Endpoint Connectivity
```bash
# Test HTTPS connectivity to Google Sheets API
time curl -v https://sheets.googleapis.com/v4/spreadsheets/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA \
  -H "Authorization: Bearer $(gcloud auth print-access-token)"
```

### Test 4: Network Trace
```bash
# Capture network traffic during connection attempt
sudo tcpdump -i any -w gsheets-timeout.pcap host sheets.googleapis.com &
TCPDUMP_PID=$!

python3 export_btm_sites_to_csv.py

sudo kill $TCPDUMP_PID
wireshark gsheets-timeout.pcap  # Analyze captured packets
```

---

## Resolution Status

- ✅ **Immediate workaround deployed**: Mock data + postcodes.io API
- ⏳ **Root cause investigation**: Pending timeout testing
- ⏳ **Permanent fix**: Pending test results
- ⏳ **Real BtM data integration**: Blocked until Google Sheets connection fixed

---

## Next Actions

1. **Immediate** (today): Deploy timeout handler to `export_btm_sites_to_csv.py`
2. **Short-term** (this week): Test alternative OAuth flow, check firewall rules
3. **Medium-term** (next week): Switch to Google Sheets API v4 if gspread unfixable
4. **Long-term**: Consider caching BtM site data in BigQuery to reduce Google Sheets dependency

---

**Last Updated**: December 29, 2025, 08:20 UTC
**Status**: INVESTIGATION ONGOING
**Workaround**: DEPLOYED AND WORKING
