# Google Workspace Service Account Setup

## Your Current Architecture (CORRECT ✅)

You have **TWO separate systems**:

### 1. BigQuery (Company 1) - inner-cinema-476211-u9
- **Credentials**: `inner-cinema-credentials.json`
- **Authentication**: Service Account (standard)
- **Purpose**: Query BigQuery data
- **Status**: ✅ Working perfectly - **NO CHANGES NEEDED**

### 2. Google Sheets/Docs (Company 2) - upowerenergy.uk Workspace
- **Current Auth**: `token.pickle` (OAuth user token)
- **Organization**: Your Google Workspace
- **Purpose**: Update Google Sheets dashboards
- **Status**: ⚠️ Needs domain-wide delegation for automation

## Why You Need a NEW Service Account

You CANNOT use `inner-cinema-credentials.json` for Google Workspace delegation because:
- It belongs to Company 1's GCP project
- You don't have admin rights on that project
- Domain-wide delegation must be set up in YOUR Workspace organization

## Solution: Create Workspace Service Account

### Step 1: Create NEW GCP Project (Your Own)

1. Go to: https://console.cloud.google.com/
2. Click project dropdown → **"New Project"**
3. Name: `gb-power-workspace` (or similar)
4. Organization: **Your upowerenergy.uk organization** (not inner-cinema)
5. Click **Create**

### Step 2: Enable Required APIs

```bash
# In your new project:
# 1. Go to: https://console.cloud.google.com/apis/library
# 2. Search and enable:
   - Google Sheets API
   - Google Docs API
   - Google Drive API
   - Google Apps Script API (if needed)
```

### Step 3: Create Service Account

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Select YOUR new project (`gb-power-workspace`)
3. Click **"+ CREATE SERVICE ACCOUNT"**
4. Fill in:
   - Name: `gb-power-sheets-automation`
   - ID: Will auto-fill (e.g., `gb-power-sheets-automation@gb-power-workspace.iam.gserviceaccount.com`)
   - Description: "Domain-wide delegation for Google Sheets/Docs automation"
5. Click **CREATE AND CONTINUE**
6. Skip role assignment → Click **CONTINUE**
7. Click **DONE**

### Step 4: Enable Domain-Wide Delegation

1. Click on your new service account name
2. Go to **"ADVANCED SETTINGS"** section
3. Click **"Enable Google Workspace Domain-wide Delegation"**
4. Click **SAVE**
5. Copy the **Client ID** (numeric, like `123456789012345678901`)

### Step 5: Create Key File

1. Still on service account details page
2. Go to **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Choose **JSON**
5. Click **CREATE**
6. Save the downloaded file as: `workspace-credentials.json`
7. Move it to your project directory:
   ```bash
   mv ~/Downloads/gb-power-workspace-*.json ~/GB\ Power\ Market\ JJ/workspace-credentials.json
   chmod 600 workspace-credentials.json
   ```

### Step 6: Authorize in Google Workspace Admin

1. Go to: https://admin.google.com/ac/owl/domainwidedelegation
2. Click **"Add new"**
3. Fill in:
   - **Client ID**: Paste the numeric ID from Step 4
   - **OAuth Scopes**: Paste this (one per line or comma-separated):
     ```
     https://www.googleapis.com/auth/spreadsheets
     https://www.googleapis.com/auth/documents
     https://www.googleapis.com/auth/drive.readonly
     https://www.googleapis.com/auth/script.projects
     ```
4. Click **Authorize**
5. Done! ✅

## Using the NEW Credentials

### Update Your Scripts

**Option 1: Minimal Change (Keep BigQuery Separate)**

```python
from google.oauth2 import service_account
from google.cloud import bigquery
import gspread

# BigQuery - Company 1 (NO CHANGE)
bq_creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=bq_creds)

# Google Sheets - Company 2 (NEW with delegation)
WORKSPACE_ADMIN = 'george@upowerenergy.uk'
sheets_creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject(WORKSPACE_ADMIN)  # <-- This is delegation!

gc = gspread.authorize(sheets_creds)
```

**Option 2: Use google_auth_utils.py (Cleaner)**

Create a new utility module:

```python
# workspace_auth.py
from google.oauth2 import service_account
import os

WORKSPACE_CREDS = 'workspace-credentials.json'
WORKSPACE_ADMIN = os.environ.get('WORKSPACE_ADMIN_EMAIL', 'george@upowerenergy.uk')

def get_workspace_credentials(scopes=None):
    """Get delegated credentials for Google Workspace"""
    if scopes is None:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
    
    creds = service_account.Credentials.from_service_account_file(
        WORKSPACE_CREDS,
        scopes=scopes
    )
    return creds.with_subject(WORKSPACE_ADMIN)

def get_sheets_client():
    """Get authenticated gspread client"""
    import gspread
    creds = get_workspace_credentials()
    return gspread.authorize(creds)
```

Then in your scripts:

```python
# realtime_dashboard_updater.py
from google.oauth2 import service_account
from google.cloud import bigquery
import workspace_auth

# BigQuery - Keep exactly as is
bq_creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
bq_client = bigquery.Client(project='inner-cinema-476211-u9', credentials=bq_creds)

# Google Sheets - NEW (replaces token.pickle)
gc = workspace_auth.get_sheets_client()
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
```

## Benefits of This Approach

### ✅ Advantages
1. **Separation of Concerns**: BigQuery (Company 1) and Workspace (Company 2) completely separate
2. **No GCP Console Access Needed**: You own the new project
3. **Automatic Access**: All Sheets/Docs accessible without sharing
4. **No More token.pickle**: No OAuth flow, no token expiry
5. **Secure**: Credentials file stays on your server, never shared

### 🎯 What Changes
- **Scripts**: Replace `token.pickle` OAuth with delegation
- **ChatGPT Integration**: Use `workspace-credentials.json` for Vercel proxy
- **Automation**: No more "token expired" errors

### ❌ What Stays THE SAME
- **BigQuery queries**: Still use `inner-cinema-credentials.json`
- **BigQuery project**: Still `inner-cinema-476211-u9`
- **Data architecture**: Zero changes
- **IRIS pipeline**: No changes
- **All analysis scripts**: Just different auth method

## Migration Plan

### Phase 1: Test (1 script)
```bash
# 1. Create workspace_auth.py
# 2. Update realtime_dashboard_updater.py
# 3. Test:
python3 realtime_dashboard_updater.py
```

### Phase 2: Rollout (All scripts)
```bash
# Find all scripts using token.pickle
grep -r "token.pickle" *.py

# Update each to use workspace_auth
# Remove OAuth flow code
```

### Phase 3: ChatGPT Integration
```bash
cd vercel-proxy
echo 'WORKSPACE_CREDENTIALS=<base64_encoded_json>' >> .env
echo 'WORKSPACE_ADMIN_EMAIL=george@upowerenergy.uk' >> .env
vercel --prod
```

## Comparison: Old vs New

### OLD (Current)
```python
# OAuth flow - requires browser, expires
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

gc = gspread.authorize(creds)
```

### NEW (With Delegation)
```python
# Service account - no browser, never expires
import workspace_auth
gc = workspace_auth.get_sheets_client()
```

**3 lines instead of 15!** 🎉

## Security Considerations

### ✅ Safe
- `workspace-credentials.json` has limited scopes
- Only accesses files admin can access
- Audit log in Google Workspace Admin
- Can revoke anytime in Admin Console

### ⚠️ Keep Secure
```bash
# Add to .gitignore
echo "workspace-credentials.json" >> .gitignore

# Set permissions
chmod 600 workspace-credentials.json

# Backup securely
cp workspace-credentials.json ~/secure-backup/
```

## Troubleshooting

### "Access Denied" Error
```
google.auth.exceptions.RefreshError: unauthorized_client: Client is unauthorized to retrieve access tokens using this method
```

**Solution**: Check Step 6 - Domain-wide delegation not authorized in Admin Console

### "Invalid Grant" Error
```
google.auth.exceptions.RefreshError: invalid_grant: Invalid email
```

**Solution**: Check `with_subject()` email is valid user in your Workspace

### "API Not Enabled" Error
```
User does not have permission to access this API
```

**Solution**: Enable API in Step 2 of your GCP project

## Quick Command Reference

```bash
# Check if service account has delegation enabled
gcloud iam service-accounts describe SERVICE_ACCOUNT_EMAIL \
  --project=gb-power-workspace

# List delegated scopes in Workspace (manual check)
# Go to: https://admin.google.com/ac/owl/domainwidedelegation

# Test workspace credentials
python3 -c "
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json'
).with_subject('george@upowerenergy.uk')
print('✅ Workspace delegation working!')
"
```

## Summary

### What You're Doing
Creating a **NEW service account in YOUR Google Workspace organization** for Sheets/Docs automation with domain-wide delegation.

### What You're NOT Doing
- ❌ Not changing BigQuery authentication
- ❌ Not modifying `inner-cinema-credentials.json`
- ❌ Not touching Company 1's GCP project
- ❌ Not changing data architecture

### Result
- **BigQuery**: Still uses `inner-cinema-credentials.json` (Company 1)
- **Sheets/Docs**: Uses `workspace-credentials.json` (Company 2)
- **Separation**: Clean boundary between data storage and presentation
- **Automation**: No more OAuth flows, no token expiry

---

**Next Step**: Create your new GCP project and service account following Step 1-6 above.

**Questions?** Check existing documentation:
- `PROJECT_CONFIGURATION.md` - Current project settings
- `GOOGLE_AUTH_FILES_REFERENCE.md` - All auth files
- `DOMAIN_DELEGATION_IMPLEMENTATION.md` - Previous delegation attempt (ignore - was for wrong project)
