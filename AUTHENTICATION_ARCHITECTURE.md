# 🔐 Authentication Architecture - GB Power Market JJ

**Date**: November 18, 2025  
**Status**: ✅ Fully Operational

---

## 📊 Authentication Overview

Your project uses **3 different authentication methods** across **2 Google Cloud projects**:

| Service | Authentication Method | Identity | Project |
|---------|----------------------|----------|---------|
| **BigQuery** | Service Account | `all-jibber@inner-cinema-476211-u9` | inner-cinema-476211-u9 |
| **Google Drive** | Domain-Wide Delegation | `jibber-jabber-knowledge@appspot` → `george@upowerenergy.uk` | jibber-jabber-knowledge |
| **Google Sheets** | Domain-Wide Delegation | `jibber-jabber-knowledge@appspot` → `george@upowerenergy.uk` | jibber-jabber-knowledge |
| **Railway/ChatGPT** | Service Account (both) | Both accounts | Both projects |

---

## 🔑 The Two Service Accounts

### 1. **BigQuery Service Account** (inner-cinema-credentials.json)
```json
{
  "project_id": "inner-cinema-476211-u9",
  "client_email": "all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com",
  "type": "service_account"
}
```

**Purpose**: Direct BigQuery access  
**Used By**:
- All Python scripts querying BigQuery
- Railway backend (`/query_bigquery` endpoint)
- ChatGPT queries via Railway proxy
- Dashboard updates (via `realtime_dashboard_updater.py`)

**Permissions**:
- ✅ BigQuery Data Editor
- ✅ BigQuery Job User
- ✅ Storage Object Viewer

**Authentication Pattern**:
```python
from google.cloud import bigquery
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project='inner-cinema-476211-u9', credentials=credentials)
```

---

### 2. **Workspace Service Account** (workspace-credentials.json)
```json
{
  "project_id": "jibber-jabber-knowledge",
  "client_email": "jibber-jabber-knowledge@appspot.gserviceaccount.com",
  "type": "service_account"
}
```

**Purpose**: Google Workspace access (Drive, Sheets, Docs) via **Domain-Wide Delegation**  
**Used By**:
- Google Drive file indexing (`index_drive_pdfs.py`)
- Google Sheets updates (planned migration)
- Railway backend Workspace endpoints
- ChatGPT document access

**Permissions** (via Domain-Wide Delegation):
- ✅ Google Drive (read-only)
- ✅ Google Sheets (read/write)
- ✅ Google Docs (read/write)
- ✅ Apps Script (planned)

**Key Feature**: **Impersonates** `george@upowerenergy.uk`  
This means all Drive/Sheets operations appear as if George is doing them directly.

**Authentication Pattern**:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

credentials = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')  # ← Domain-wide delegation

drive = build('drive', 'v3', credentials=credentials)
```

**Critical Detail**: The `.with_subject('george@upowerenergy.uk')` call is what enables domain-wide delegation. Without it, the service account has no permissions.

---

## 🌐 Domain-Wide Delegation Setup

**Configured in**: Google Workspace Admin Console  
**URL**: https://admin.google.com/ac/owl/domainwidedelegation

**Configuration**:
```
Client ID: 108583076839984080568
Email: jibber-jabber-knowledge@appspot.gserviceaccount.com

Authorized Scopes:
- https://www.googleapis.com/auth/spreadsheets
- https://www.googleapis.com/auth/drive.readonly
- https://www.googleapis.com/auth/drive
- https://www.googleapis.com/auth/documents
- https://www.googleapis.com/auth/script.projects
```

**How It Works**:
1. Service account (`jibber-jabber-knowledge@appspot`) is authorized by Workspace Admin
2. Code uses `.with_subject('george@upowerenergy.uk')` to impersonate George
3. All operations inherit George's Workspace permissions
4. Audit logs show actions as performed by George

**Benefits**:
- ✅ No OAuth token expiration (permanent auth)
- ✅ No user interaction required
- ✅ Works in automated scripts/cron jobs
- ✅ Centralized permission management

---

## 🚂 Railway Backend Authentication

**Service**: https://jibber-jabber-production.up.railway.app  
**Authentication**: Environment variables with base64-encoded credentials

### Environment Variables in Railway:

```bash
# BigQuery access
GOOGLE_APPLICATION_CREDENTIALS="<base64 encoded inner-cinema-credentials.json>"
BQ_PROJECT_ID="inner-cinema-476211-u9"

# Workspace access
GOOGLE_WORKSPACE_CREDENTIALS="<base64 encoded workspace-credentials.json>"

# API security
CODEX_API_TOKEN="codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
```

### Railway Endpoints Using Authentication:

**BigQuery Endpoints** (use inner-cinema credentials):
- `POST /query_bigquery` - Execute SQL queries
- `GET /query_bigquery_get` - Execute SQL via URL params
- `GET /debug/env` - Check credential configuration

**Workspace Endpoints** (use workspace credentials with delegation):
- `POST /workspace/list_files` - List Drive files
- `POST /workspace/search_files` - Search Drive
- `POST /workspace/read_sheet` - Read Google Sheets
- `POST /workspace/read_doc` - Read Google Docs
- `POST /workspace/write_doc` - Write to Google Docs

### Authentication Flow in Railway:

```python
# BigQuery endpoint
@app.post("/query_bigquery")
async def query_bigquery(request: Request):
    # Decode base64 credentials
    bq_creds_base64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    creds_json = base64.b64decode(bq_creds_base64).decode('utf-8')
    creds_dict = json.loads(creds_json)
    
    # Create BigQuery client
    client = bigquery.Client.from_service_account_info(creds_dict)
    
    # Execute query
    results = client.query(sql).result()
    return {"success": True, "rows": list(results)}

# Workspace endpoint
@app.post("/workspace/list_files")
async def list_drive_files(request: Request):
    # Decode base64 credentials
    workspace_creds_base64 = os.getenv("GOOGLE_WORKSPACE_CREDENTIALS")
    creds_json = base64.b64decode(workspace_creds_base64).decode('utf-8')
    creds_dict = json.loads(creds_json)
    
    # Create delegated credentials
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    ).with_subject('george@upowerenergy.uk')  # ← Impersonate George
    
    # Build Drive service
    drive = build('drive', 'v3', credentials=credentials)
    
    # List files as George
    results = drive.files().list(pageSize=100).execute()
    return {"success": True, "files": results['files']}
```

---

## 🤖 ChatGPT Access Flow

**How ChatGPT queries your data**:

```mermaid
ChatGPT → Railway Proxy → BigQuery/Drive → Results → ChatGPT
```

**Step by Step**:

1. **User asks ChatGPT**: "Show me VLP revenue for October"
2. **ChatGPT generates SQL**: `SELECT * FROM bmrs_mid WHERE settlementDate >= '2025-10-01'`
3. **ChatGPT calls Railway**: `POST https://jibber-jabber-production.up.railway.app/api/proxy-v2?path=/query_bigquery`
4. **Railway authenticates**: Uses `GOOGLE_APPLICATION_CREDENTIALS` (inner-cinema)
5. **Railway executes query**: BigQuery returns results
6. **Railway returns JSON**: ChatGPT receives data
7. **ChatGPT formats response**: "Here's your VLP revenue data..."

**Authentication Used**:
- Railway → BigQuery: `all-jibber@inner-cinema-476211-u9` service account
- Railway → Drive/Sheets: `jibber-jabber-knowledge@appspot` impersonating George

**Security**:
- ✅ Bearer token required (`CODEX_API_TOKEN`)
- ✅ SQL validation (prevent DROP/DELETE)
- ✅ Project whitelist (only inner-cinema allowed)
- ✅ Rate limiting on Vercel proxy

---

## 📁 Local Script Authentication

### Current Setup (Mixed)

**BigQuery Scripts** (98 scripts):
```python
# Use service account directly
from google.cloud import bigquery
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
client = bigquery.Client(project='inner-cinema-476211-u9', credentials=credentials)
```

**Google Sheets Scripts** (98 scripts - LEGACY):
```python
# ⚠️ LEGACY: Uses OAuth token (expires!)
import pickle
import gspread

with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)  # ← Expires every 7 days!

gc = gspread.authorize(creds)
```

**Google Drive Scripts** (1 script - MODERN):
```python
# ✅ MODERN: Uses domain-wide delegation
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')  # ← Permanent auth

drive = build('drive', 'v3', credentials=credentials)
```

### Migration Plan (from ACTION_PLAN.md)

**Goal**: Convert all 98 Sheets scripts from OAuth → Domain-Wide Delegation

**Before** (OAuth - expires):
```python
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
```

**After** (Delegation - permanent):
```python
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(creds)
```

**Status**: Delegation authorized in Workspace Admin, ready to migrate scripts

---

## 🔍 How to Verify Each Authentication

### Test BigQuery Access:
```bash
python3 -c "
from google.cloud import bigquery
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
client = bigquery.Client(project='inner-cinema-476211-u9', credentials=creds)

results = client.query('SELECT COUNT(*) as count FROM uk_energy_prod.bmrs_freq LIMIT 1').result()
print('✅ BigQuery connected:', list(results)[0]['count'])
"
```

### Test Drive Access (Domain-Wide Delegation):
```bash
python3 -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
).with_subject('george@upowerenergy.uk')

drive = build('drive', 'v3', credentials=creds)
results = drive.files().list(pageSize=5, fields='files(name)').execute()
print('✅ Drive connected. Files:', [f['name'] for f in results['files']])
"
```

### Test Sheets Access (Domain-Wide Delegation):
```bash
python3 -c "
from google.oauth2 import service_account
import gspread

creds = service_account.Credentials.from_service_account_file(
    'workspace-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
).with_subject('george@upowerenergy.uk')

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
print('✅ Sheets connected. Title:', spreadsheet.title)
"
```

### Test Railway Endpoints:
```bash
# Test BigQuery endpoint
curl -X POST "https://jibber-jabber-production.up.railway.app/query_bigquery" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq` LIMIT 1"}'

# Test Drive endpoint
curl -X POST "https://jibber-jabber-production.up.railway.app/workspace/list_files" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"query": "name contains '\''pdf'\''", "pageSize": 5}'
```

---

## 📊 Authentication Summary Table

| What | Where | How | Identity | Expires? |
|------|-------|-----|----------|----------|
| **Local BigQuery** | Python scripts | Service Account | all-jibber@inner-cinema | ❌ Never |
| **Local Drive** | `index_drive_pdfs.py` | Domain-Wide Delegation | george@upowerenergy.uk | ❌ Never |
| **Local Sheets** | 98 scripts (legacy) | OAuth Token (token.pickle) | george@upowerenergy.uk | ⚠️ Yes (7 days) |
| **Local Sheets** | Future scripts | Domain-Wide Delegation | george@upowerenergy.uk | ❌ Never |
| **Railway BigQuery** | `/query_bigquery` | Service Account (base64) | all-jibber@inner-cinema | ❌ Never |
| **Railway Drive** | `/workspace/list_files` | Domain-Wide Delegation (base64) | george@upowerenergy.uk | ❌ Never |
| **Railway Sheets** | `/workspace/read_sheet` | Domain-Wide Delegation (base64) | george@upowerenergy.uk | ❌ Never |
| **ChatGPT → BigQuery** | Via Railway proxy | Service Account | all-jibber@inner-cinema | ❌ Never |
| **ChatGPT → Drive** | Via Railway proxy | Domain-Wide Delegation | george@upowerenergy.uk | ❌ Never |

---

## 🎯 Key Takeaways

### ✅ What's Working Perfectly:
1. **BigQuery**: Direct service account auth, no expiration issues
2. **Railway Backend**: Both credentials encoded in environment variables
3. **ChatGPT Integration**: Full access to BigQuery and Drive via Railway
4. **Drive Indexing**: Domain-wide delegation working (18,000 PDFs indexed so far!)

### ⚠️ What Needs Migration:
1. **98 Google Sheets scripts**: Using OAuth token (expires every 7 days)
2. Need to migrate to domain-wide delegation (same as Drive indexer)

### 🔐 Security Best Practices:
- ✅ Credentials stored in `.gitignore` (not in repo)
- ✅ Railway uses base64-encoded credentials (not plain JSON)
- ✅ Bearer token authentication on all Railway endpoints
- ✅ Domain-wide delegation scoped to minimum needed permissions
- ✅ Audit logs track all service account activity

### 💡 Why This Architecture?
- **BigQuery**: Service account is simpler, no delegation needed
- **Drive/Sheets**: Delegation allows "act as George" for permission inheritance
- **Railway**: Both methods supported for different use cases
- **ChatGPT**: Seamless access to all data sources via unified proxy

---

---

## 📄 PDF Extraction & Chunking Pipeline

### Overview

The project uses a **continuous extraction pipeline** to process PDFs from Google Drive into searchable chunks in BigQuery. This enables full-text search across all documents via ChatGPT.

### Architecture

```
Google Drive PDFs → Download → Extract Text → Chunk → BigQuery (document_chunks table)
```

### Key Scripts

**1. Metadata Indexer** (`index_drive_pdfs.py`)
- Scans all Drive PDFs (96,087 total)
- Stores metadata in `pdf_metadata_index` table
- Tracks which PDFs are chunked (`is_chunked` flag)
- Uses domain-wide delegation

**2. PDF Extractor** (`continuous_extract_fixed.py`)
- Processes PDFs in batches with parallel workers
- Extracts text using PyPDF2/OCR fallback
- Chunks text with configurable size/overlap
- Saves to `document_chunks` table
- Handles DOCX and PPTX files too

**3. Immediate Extractor** (`immediate_extract.py`)
- Processes documents one-by-one with instant feedback
- Saves each document immediately after processing
- Good for testing/debugging individual files

### Chunking Strategy

**Configuration** (from `config.yml`):
```yaml
chunk:
  size: 1000        # ~1000 tokens per chunk
  overlap: 200      # 200 token overlap between chunks
```

**Chunking Process**:
1. Extract raw text from PDF
2. Split into overlapping chunks (~1000 tokens each)
3. Store each chunk with metadata:
   - `doc_id`: Google Drive file ID
   - `chunk_id`: Unique identifier (doc_id:chunk_index)
   - `content`: Text content of chunk
   - `metadata`: JSON with filename, mime_type, drive_url
   - `chunk_index`: Position in document

**BigQuery Schema** (`document_chunks`):
```sql
CREATE TABLE document_chunks (
  doc_id STRING,
  chunk_id STRING,
  chunk_index INT64,
  content STRING,
  n_chars INT64,
  n_tokens_est INT64,
  metadata JSON,
  indexed_at TIMESTAMP
)
```

### Current Status

- **Metadata**: 96,087 PDFs indexed
- **Full-text chunks**: 8 PDFs (3,880 chunks)
  - DCUSA v16.1 (578 chunks)
  - Complete CUSC (618 chunks)
  - Grid Code (692 chunks)
  - FSO Modification NETA (210 chunks)
  - Consumer Engagement Survey (1,096 chunks)
  - Coforge BP2 (218 chunks)
  - CU3E6E~1 (459 chunks)
  - Enforcement Guidelines (9 chunks)

### Running the Pipeline

**Environment Setup**:
```bash
export DRIVE_SERVICE_ACCOUNT="workspace-credentials.json"
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
```

**Run Extraction**:
```bash
# Continuous processing (production)
python3 continuous_extract_fixed.py

# Immediate feedback (testing)
python3 immediate_extract.py
```

**Monitor Progress**:
```bash
tail -f /tmp/extraction_success.log
tail -f /tmp/extraction_errors.log
tail -f /tmp/extraction_progress.log
```

### Authentication

**Uses both service accounts**:
1. **Drive access**: `workspace-credentials.json` (with domain-wide delegation)
2. **BigQuery writes**: `inner-cinema-credentials.json`

### Performance

- **Parallel workers**: 6 threads
- **Batch size**: 500 documents
- **Memory management**: Process restarts every 5,000 docs to prevent leaks
- **Error handling**: Skips corrupted files, logs all errors

### ChatGPT Integration

Once PDFs are chunked, ChatGPT can search them:

```sql
-- Find energy regulation mentions
SELECT doc_id, chunk_index, LEFT(content, 200) as preview
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE LOWER(content) LIKE '%balancing mechanism%'
LIMIT 10
```

**Available via Railway endpoint**: `/query_bigquery`

---

## 📚 Related Documentation

- Full setup guide: `ACTION_PLAN.md`
- Workspace delegation details: `WORKSPACE_DELEGATION_SUCCESS.md`
- ChatGPT instructions: `CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md`
- Project configuration: `PROJECT_CONFIGURATION.md`
- PDF extraction setup: See guide at project root

---

*Last Updated: November 18, 2025*  
*Status: Domain-wide delegation working, 96K PDFs indexed, 8 PDFs fully chunked*
