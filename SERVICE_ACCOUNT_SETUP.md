# Adding More Service Accounts for 5x Google Sheets API Quota

## Current Status
- **1 service account**: 60 requests/minute
- **Target**: 5 accounts = 300 requests/minute

## Quick Setup Guide

### Option 1: Via gcloud CLI (Automated - Recommended)

**On your local machine** (not the server):

```bash
# 1. Download the script
scp root@94.237.55.234:/home/george/GB-Power-Market-JJ/create_additional_service_accounts.sh .

# 2. Run it (creates 4 new service accounts)
bash create_additional_service_accounts.sh
```

This creates:
- `inner-cinema-credentials-2.json`
- `inner-cinema-credentials-3.json`
- `inner-cinema-credentials-4.json`
- `inner-cinema-credentials-5.json`

**Then upload to server:**
```bash
scp inner-cinema-credentials-*.json root@94.237.55.234:/home/george/GB-Power-Market-JJ/
```

### Option 2: Via Google Cloud Console (Manual)

1. **Go to GCP Console** → https://console.cloud.google.com
2. **Select Project**: `inner-cinema-476211-u9`
3. **Navigate**: IAM & Admin → Service Accounts
4. **Create Service Account** (repeat 4 times):
   - Name: `sheets-api-account-2` (then 3, 4, 5)
   - Description: "Google Sheets API Account 2"
   - Click "Create and Continue"

5. **Grant Roles** (for each account):
   - `BigQuery User`
   - `BigQuery Data Viewer`
   - Click "Continue" → "Done"

6. **Create Keys** (for each account):
   - Click on the service account
   - Keys tab → Add Key → Create New Key
   - JSON format → Create
   - Save as `inner-cinema-credentials-2.json` (etc.)

7. **Download & Upload to Server**:
   ```bash
   scp ~/Downloads/inner-cinema-credentials-*.json root@94.237.55.234:/home/george/GB-Power-Market-JJ/
   ```

## Enable Google Sheets API Access

**For each new service account email** (e.g., `sheets-api-account-2@inner-cinema-476211-u9.iam.gserviceaccount.com`):

1. **Open Google Sheets** → https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. **Click Share** button (top right)
3. **Add each service account email** with **Editor** access:
   ```
   sheets-api-account-2@inner-cinema-476211-u9.iam.gserviceaccount.com
   sheets-api-account-3@inner-cinema-476211-u9.iam.gserviceaccount.com
   sheets-api-account-4@inner-cinema-476211-u9.iam.gserviceaccount.com
   sheets-api-account-5@inner-cinema-476211-u9.iam.gserviceaccount.com
   ```
4. **Uncheck "Notify people"** (they're bots, not humans)
5. **Click Share**

## Verify Setup on Server

```bash
# Check all credential files exist
ls -la /home/george/GB-Power-Market-JJ/inner-cinema-credentials-*.json

# Should show:
# inner-cinema-credentials.json (original)
# inner-cinema-credentials-2.json
# inner-cinema-credentials-3.json
# inner-cinema-credentials-4.json
# inner-cinema-credentials-5.json
```

## Test Service Account Rotation

```bash
cd /home/george/GB-Power-Market-JJ

# Run quick test
python3 -c "
from cache_manager import get_cache_manager

# Will auto-detect all credential files
cache = get_cache_manager()

# Check how many accounts loaded
stats = cache.get_stats()
print(f'Service accounts loaded: {stats[\"service_accounts\"]}')
print(f'Total quota: {stats[\"service_accounts\"] * 60} requests/minute')
print(f'Account rotation: {cache.credentials_files}')
"
```

**Expected output:**
```
✅ CacheManager initialized: 5 accounts, Redis=disabled
Service accounts loaded: 5
Total quota: 300 requests/minute
Account rotation: ['inner-cinema-credentials.json', 'inner-cinema-credentials-2.json', ...]
```

## How Rotation Works

The cache manager **automatically**:
1. Finds all `inner-cinema-credentials*.json` files
2. Tracks requests per account (max 55/minute to be safe)
3. Rotates to next account when approaching limit
4. Waits only if ALL accounts exhausted (rare with 5 accounts)

**No code changes needed!** Just add the files.

## Troubleshooting

### "Permission denied" errors
→ Service account not shared with the spreadsheet. Repeat "Enable Google Sheets API Access" steps.

### "File not found: inner-cinema-credentials-2.json"
→ Upload the files to the correct directory: `/home/george/GB-Power-Market-JJ/`

### Cache manager still shows "1 accounts"
→ Files might have wrong names. Must match pattern: `inner-cinema-credentials*.json`

### Want to verify individual account works?
```bash
python3 -c "
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials-2.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
print(f'✅ Account 2 can access: {sheet.title}')
"
```

## Benefits

| Accounts | Quota | Rate Limit Risk | Cost |
|----------|-------|-----------------|------|
| 1 | 60 req/min | High (current) | Free |
| 2 | 120 req/min | Medium | Free |
| 3 | 180 req/min | Low | Free |
| 5 | 300 req/min | None | Free |

**Recommendation**: Add at least 2 more accounts (total 3) for safety. Full 5 accounts only needed under very heavy load.

## Quick Start (Copy-Paste)

```bash
# On your LOCAL machine with gcloud:
cd ~/Downloads
bash create_additional_service_accounts.sh

# Upload to server:
scp inner-cinema-credentials-*.json root@94.237.55.234:/home/george/GB-Power-Market-JJ/

# Share spreadsheet with new emails (via browser)
# Then test:
ssh root@94.237.55.234 "cd /home/george/GB-Power-Market-JJ && python3 -c 'from cache_manager import get_cache_manager; cache = get_cache_manager(); print(cache.get_stats())'"
```

Done! 🚀
