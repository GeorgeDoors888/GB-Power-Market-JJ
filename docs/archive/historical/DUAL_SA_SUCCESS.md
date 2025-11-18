# 🎉 Dual Service Account Setup - COMPLETE!

**Date:** November 3, 2025  
**Status:** ✅ FULLY OPERATIONAL

---

## What Was Accomplished

### ✅ **Dual Service Account Architecture**

Successfully configured **two separate service accounts** working together:

1. **jibber-jabber-knowledge** → Google Drive/Sheets/Docs Access
   - Email: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
   - Purpose: Read files from Google Drive
   - Location: `/secrets/drive_sa.json`

2. **inner-cinema-476211-u9** (GB Power Market JJ) → BigQuery Storage
   - Email: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`  
   - Purpose: Store metadata in BigQuery
   - Location: `/secrets/sa.json`

### ✅ **Configuration Updated**

**Environment Variables (.env):**
```properties
GCP_PROJECT=inner-cinema-476211-u9
BQ_DATASET=uk_energy_insights
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json
DRIVE_SERVICE_ACCOUNT=/secrets/drive_sa.json
DRIVE_OWNER_EMAIL=george@upowerenergy.uk
```

**Drive Query Updated** - Now includes:
- PDFs (`application/pdf`)
- Word docs (`.docx`)
- PowerPoint (`.pptx`)
- Excel files (`.xlsx`)
- **Google Docs** (`application/vnd.google-apps.document`)
- **Google Sheets** (`application/vnd.google-apps.spreadsheet`)
- **Google Slides** (`application/vnd.google-apps.presentation`)

### ✅ **Code Updates**

1. **`src/auth/google_auth.py`** - Updated to use separate service accounts:
   - `drive_client()` uses Drive SA (jibber-jabber-knowledge)
   - `bq_client()` uses BigQuery SA (inner-cinema)

2. **`src/cli.py`** - Added Google native formats to SUPPORTED types:
   ```python
   "application/vnd.google-apps.document": "gdoc",
   "application/vnd.google-apps.spreadsheet": "gsheet",
   "application/vnd.google-apps.presentation": "gslides",
   ```

3. **`scripts/export_to_sheets.py`** - Enhanced with:
   - Dual service account support
   - Auto-sharing with owner email
   - Better error handling

### ✅ **BigQuery Dataset Created**

- **Project:** `inner-cinema-476211-u9`
- **Dataset:** `uk_energy_insights`
- **Region:** `europe-west2`
- **Tables:**
  - `documents` - Drive file metadata (11 files)
  - `chunks` - Text chunks (ready for content extraction)
  - `chunk_embeddings` - Vector embeddings (ready for search)

### ✅ **Data Indexed**

**11 Google Drive files** successfully indexed:
- 10 × Google Sheets
- 1 × Google Doc

All metadata stored in BigQuery and queryable!

---

## Current Status

### ✅ Working
- Drive file discovery (finds Google Docs/Sheets)
- BigQuery storage (11 files indexed)
- Dual service account authentication
- Metadata extraction and storage

### ⚠️ Known Limitation
- **Google Sheets Export Blocked** - Service accounts' Drive storage quota exceeded
- **Workaround:** Data is in BigQuery and can be:
  1. Queried directly in BigQuery Console
  2. Exported to CSV
  3. Viewed via custom dashboard
  4. Accessed via API

---

## How to Use

### Query the Data

**Option 1: BigQuery Console**
1. Go to: https://console.cloud.google.com/bigquery
2. Select project: `inner-cinema-476211-u9`
3. Navigate to: `uk_energy_insights.documents`
4. Run query:
```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
ORDER BY updated DESC
```

**Option 2: From UpCloud Server**
```bash
ssh root@94.237.55.15 'docker exec driveindexer python3 /tmp/check_bq.py'
```

### Re-Index Drive Files

To update the index with new/changed files:
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli index-drive'
```

### Check What's Indexed

```bash
ssh root@94.237.55.15 'docker exec driveindexer python3 << "EOF"
from google.cloud import bigquery
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file("/secrets/sa.json")
client = bigquery.Client(project="inner-cinema-476211-u9", credentials=creds)

query = "SELECT name, mime_type, web_view_link FROM inner-cinema-476211-u9.uk_energy_insights.documents"

for row in client.query(query).result():
    print(f"- {row.name} ({row.mime_type.split('.')[-1]})")
    print(f"  {row.web_view_link}")
EOF
'
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│        jibber-jabber-knowledge              │
│     (Drive/Sheets/Docs Access)              │
│                                             │
│  • Reads files from Google Drive            │
│  • Lists folders and documents              │
│  • Gets file metadata                       │
└─────────────────┬───────────────────────────┘
                  │
                  │ Metadata
                  ↓
┌─────────────────────────────────────────────┐
│         Drive→BigQuery Indexer              │
│           (UpCloud Server)                  │
│                                             │
│  • Runs on 94.237.55.15                     │
│  • Docker container: driveindexer           │
│  • Processes Drive files                    │
│  • Extracts metadata                        │
└─────────────────┬───────────────────────────┘
                  │
                  │ Store
                  ↓
┌─────────────────────────────────────────────┐
│       inner-cinema-476211-u9                │
│         (BigQuery Storage)                  │
│                                             │
│  Dataset: uk_energy_insights                │
│  Tables:                                    │
│    • documents (11 files)                   │
│    • chunks (ready)                         │
│    • chunk_embeddings (ready)               │
└─────────────────────────────────────────────┘
```

---

## Next Steps

### To Find More Files

The indexer only found 11 files because:
1. The service account can only see files **explicitly shared** with it
2. PDFs mentioned might be in folders not yet shared

**To index more files:**
1. Share additional Drive folders with: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
2. Ensure "Share with all items inside" is enabled
3. Re-run indexing: `docker exec driveindexer python -m src.cli index-drive`

### To Extract Content

Once you have files indexed, extract their content:
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli extract'
```

### To Build Search Embeddings

After extraction, build vector embeddings for semantic search:
```bash
ssh root@94.237.55.15 'docker exec driveindexer python -m src.cli build-embeddings'
```

### To Export Data (Alternative to Sheets)

Since service accounts are out of Drive storage, export to CSV instead:
```bash
# Create CSV export script (already created: export_to_csv.py)
ssh root@94.237.55.15 'docker exec driveindexer python scripts/export_to_csv.py'

# Download the CSV
scp root@94.237.55.15:/tmp/drive_metadata_*.csv ./drive_metadata.csv

# Upload to your personal Drive manually
```

---

## Monitoring

### Check System Status
```bash
ssh root@94.237.55.15 'docker ps | grep driveindexer'
```

### View Logs
```bash
ssh root@94.237.55.15 'docker logs driveindexer --tail 50'
```

### Check BigQuery
```bash
ssh root@94.237.55.15 'docker exec driveindexer python3 /tmp/check_bq.py'
```

---

## Summary

✅ **Dual service account setup:** COMPLETE  
✅ **BigQuery storage configured:** COMPLETE  
✅ **11 files indexed:** COMPLETE  
✅ **Metadata stored:** COMPLETE  
⚠️ **Sheets export:** Blocked by service account storage quota  
✅ **Alternative exports:** CSV available  

**The system is fully operational!** You can now:
- Query indexed files via BigQuery
- Add more files by sharing with the service account
- Extract content and build search indexes
- Export data to CSV for manual upload to Sheets

---

**System:** UpCloud Server (94.237.55.15)  
**Container:** driveindexer  
**BigQuery Project:** inner-cinema-476211-u9  
**Dataset:** uk_energy_insights  
**Files Indexed:** 11 (10 Sheets, 1 Doc)

🎉 **Setup Complete!**
