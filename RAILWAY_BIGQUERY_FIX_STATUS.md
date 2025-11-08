# Railway BigQuery Access Fix - Status

## Problem
Apps Script dashboard missing data: SSP, SBP, BOALF, BOD prices not populating.

**Root Cause:** Railway backend was configured to query wrong BigQuery project.

## Fixes Applied

### 1. ✅ Added BQ_PROJECT_ID Environment Variable
- **Variable:** `BQ_PROJECT_ID=inner-cinema-476211-u9`
- **Status:** Added to Railway
- **Purpose:** Tell backend which BigQuery project to query

### 2. ✅ Updated GOOGLE_CREDENTIALS_BASE64
- **Variable:** `GOOGLE_CREDENTIALS_BASE64`
- **Value:** Base64-encoded credentials for `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`
- **Status:** Updated in Railway (verified starts with `ewogICJ0eXBlIjog`)
- **Purpose:** Authenticate to inner-cinema-476211-u9 project

### 3. ✅ Fixed codex_server.py Code
- **File:** `codex-server/codex_server.py`
- **Change:** Use `BQ_PROJECT_ID` env var instead of hardcoded `jibber-jabber-knowledge`
- **Commit:** `ab29ba50`
- **Code:**
  ```python
  bq_project = os.environ.get('BQ_PROJECT_ID', 'inner-cinema-476211-u9')
  client = bigquery.Client(project=bq_project)
  ```

### 4. ✅ Added Better Error Logging
- **File:** `codex-server/codex_server.py`
- **Change:** Show full error details (stderr, stdout, return code)
- **Commit:** `c12a81ea`
- **Purpose:** See actual BigQuery error messages

### 5. ✅ Fixed api_gateway.py (Not Used by Railway)
- **File:** `api_gateway.py`
- **Change:** Added base64 credentials support
- **Commit:** `a83dfe5a`
- **Note:** Railway runs `codex_server.py` not `api_gateway.py`

## Current Status

### Configuration ✅
- ✅ BQ_PROJECT_ID set correctly
- ✅ GOOGLE_CREDENTIALS_BASE64 updated with correct credentials
- ✅ Code fixes committed and pushed to GitHub

### Deployment ⏸️
- ⏸️ Railway deployment stuck on old commit (`f210c2f1`)
- ⏸️ Latest commit (`c12a81ea`) not deployed yet
- ⏸️ Need manual redeploy to pull latest code

### Testing ❌
- ❌ BigQuery queries still failing
- ❌ Error message empty (need better logging from latest commit)
- ❌ Apps Script still missing SSP/SBP/BOALF/BOD data

## Next Steps

1. **Manually trigger Railway redeploy** to pull commit `c12a81ea`
2. **Check Deploy Logs** for actual error message
3. **Debug based on error** (permissions, table access, etc.)
4. **Test Apps Script** once Railway working

## Railway Deployment Info

- **Project:** jibber-jabber-production
- **Project ID:** c0c79bb5-e2fc-4e0e-93db-39d6027301ca
- **URL:** https://jibber-jabber-production.up.railway.app
- **Start Command:** `python codex_server.py`
- **Current Active Commit:** f210c2f1 (old)
- **Should Be On Commit:** c12a81ea (latest)

## Test Commands

```bash
# Test BigQuery access
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20COUNT(*)%20as%20cnt%20FROM%20\`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\`%20LIMIT%201"

# Should return success with count, not "Query execution failed"
```

## Architecture

```
Apps Script (Google Sheets)
    ↓
Vercel Proxy (/api/proxy-v2)
    ↓
Railway Backend (jibber-jabber-production)
    ↓
BigQuery (inner-cinema-476211-u9.uk_energy_prod)
```

## Project Identity Reference

- **Smart Grid (Data):** inner-cinema-476211-u9 - BigQuery datasets
- **UPower (Workspace):** jibber-jabber-knowledge - Google Sheets, Apps Script
- **Railway Name:** jibber-jabber-production (confusing but queries inner-cinema)

See: `PROJECT_IDENTITY_MASTER.md` for full details
