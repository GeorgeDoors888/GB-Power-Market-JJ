# ChatGPT Data Access - Complete Guide

**Last Updated:** December 18, 2025
**Status:** ⚠️ ChatGPT cannot access data - Railway works, Vercel broken

---

## 🚨 Current Problem

ChatGPT **cannot find information or data** from your system.

### Root Cause

**Vercel Proxy is BROKEN** (404 NOT FOUND)
- URL: `https://gb-power-market-jj.vercel.app/api/proxy-v2`
- Status: **404 NOT FOUND** ❌
- ChatGPT is configured to use this broken URL

**Railway Backend is WORKING**
- URL: `https://jibber-jabber-production.up.railway.app`
- Status: **Healthy** ✅
- Has access to all data (1.13B rows, 35,168 PDF chunks)
- BigQuery queries working perfectly

---

## 📊 Data Inventory (Available & Accessible)

### BigQuery Database
- **Project:** `inner-cinema-476211-u9`
- **Location:** US
- **Datasets:** 10
- **Tables:** 296
- **Total Rows:** 1.13 billion
- **Storage:** 466.08 GB

#### Key Datasets:
1. **uk_energy_prod** (185 tables)
   - `bmrs_bod`: 391M rows (bid-offer data)
   - `bmrs_mid`: 159,990 rows (market index prices)
   - `bmrs_costs`: Settlement prices
   - `document_chunks`: 2.5M rows (PDF chunks)
   - `pdf_metadata_index`: 96,087 PDFs indexed

2. **uk_energy_insights** (analytics views)

3. **gb_power** (supplementary data)

### PDF Documents (Searchable)
- **Table:** `uk_energy_prod.document_chunks`
- **Total PDFs:** 1,117 regulatory documents
- **Total Chunks:** 35,168 searchable text chunks
- **Total Size:** 60.72 GB (in `pdf_metadata_index`)

#### Top Documents:
1. CUSC Exhibit EE v1.17 - 168 chunks
2. Grid Code Rev 63 - 161 chunks
3. CUSC Exhibit MM4 v2 - 158 chunks
4. DCUSA v16.1 - 127 chunks

### Google Sheets
- **GB Energy Dashboard:** 29 worksheets
- Live data updates every 5 minutes
- BM metrics, VLP analysis, market indices

---

## 🏗️ Current Architecture

### How It Should Work:

```
ChatGPT (User Query)
    ↓
Vercel Proxy (BROKEN ❌)
    ↓
Railway Backend (WORKING ✅)
    ↓
BigQuery / Google Sheets / PDFs
```

### What's Actually Happening:

```
ChatGPT → Vercel Proxy → 404 NOT FOUND ❌
           ↓
      Query fails
```

### Verification Tests:

```bash
# ❌ Vercel (BROKEN)
curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health
# Response: 404 NOT FOUND

# ✅ Railway (WORKING)
curl https://jibber-jabber-production.up.railway.app/health
# Response: {"status": "healthy"}

# ✅ BigQuery Access (WORKING)
curl -X POST "https://jibber-jabber-production.up.railway.app/query_bigquery" \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM document_chunks LIMIT 1"}'
# Response: {"success": true, "results": [{"count": 35168}]}
```

---

## 🔧 Solution Options

### Option 1: Use Railway Directly (RECOMMENDED - Simplest)

Update ChatGPT Custom GPT to bypass broken Vercel and use Railway directly.

**Steps:**
1. Go to ChatGPT → My GPTs → [Your GPT] → Edit
2. Configure → Actions → Edit Schema
3. Replace schema with: `/home/george/GB-Power-Market-JJ/CHATGPT_COMPLETE_SCHEMA.json`
4. Set Authentication:
   - Type: **Bearer**
   - Token: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
5. Test and Save

**Schema Server URL:**
```json
{
  "servers": [{
    "url": "https://jibber-jabber-production.up.railway.app"
  }]
}
```

**Pros:**
- ✅ Works immediately (Railway already healthy)
- ✅ No deployment needed
- ✅ One less component to maintain
- ✅ Direct access to all data

**Cons:**
- ⚠️ ChatGPT knows Railway auth token (security)
- ⚠️ No rate limiting via Vercel

---

### Option 2: Fix Vercel Proxy (More Secure)

Redeploy Vercel proxy to restore the security layer.

**Why Vercel was there:**
- Hide Railway token from ChatGPT
- Whitelist only safe endpoints
- Add rate limiting
- CORS handling

**Steps to fix:**
1. Install Vercel CLI: `npm install -g vercel`
2. Deploy: `cd vercel-proxy && vercel --prod`
3. Update ChatGPT schema to use new Vercel URL
4. Test connection

**Vercel Proxy Code Location:**
- `/home/george/GB-Power-Market-JJ/vercel-proxy/api/proxy-v2.ts`

**Pros:**
- ✅ More secure (token hidden from ChatGPT)
- ✅ Endpoint whitelisting
- ✅ Rate limiting possible

**Cons:**
- ⚠️ Requires Vercel deployment
- ⚠️ One more service to maintain
- ⚠️ Currently broken (404)

---

### Option 3: Use Dell Server Directly (BEST for Heavy Workloads)

Run FastAPI server on your Dell (125GB RAM, 32 cores) instead of Railway (1GB RAM).

**Dell Server Specs:**
- **RAM:** 125 GB (vs Railway's ~1 GB)
- **CPU:** 32 cores (vs Railway's 1-2 shared vCPUs)
- **Storage:** 913 GB available (vs Railway's ephemeral)
- **BigQuery Access:** ✅ Already configured
- **Cost:** $0 (already owned)

**Setup Steps:**
```bash
# 1. Navigate to codex server
cd /home/george/GB-Power-Market-JJ/codex-server

# 2. Install dependencies (if needed)
pip3 install --user fastapi uvicorn python-multipart

# 3. Run server
python3 codex_server.py

# 4. Open firewall
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# 5. Test
curl http://94.237.55.234:8000/health
```

**Update ChatGPT schema to:**
```json
{
  "servers": [{
    "url": "http://94.237.55.234:8000"
  }]
}
```

**Pros:**
- ✅ 125x more RAM than Railway
- ✅ 16-32x more CPU power
- ✅ No timeout limits on queries
- ✅ Process multi-GB datasets in memory
- ✅ Save $5-10/month (no Railway cost)
- ✅ Already has all credentials
- ✅ Already running 24/7

**Cons:**
- ⚠️ Need to expose port 8000 publicly
- ⚠️ Need to manage firewall rules
- ⚠️ HTTP (not HTTPS) unless you setup nginx

**Best for:**
- Analyzing 391M rows of `bmrs_bod`
- Multi-year VLP revenue calculations
- Statistical analysis across all 296 tables
- Machine learning model training
- Dashboard aggregations

---

## 🔍 How ChatGPT Accesses PDFs

### Current PDF Chunking System

**Pipeline:**
```
Google Drive → index_drive_pdfs.py → extract/OCR → chunk → BigQuery
```

**Storage:**
- **Chunks Table:** `uk_energy_prod.document_chunks`
- **Metadata Table:** `uk_energy_prod.pdf_metadata_index`

### ChatGPT Search Queries

**List all PDFs:**
```sql
SELECT
  JSON_VALUE(metadata, '$.filename') as filename,
  COUNT(*) as chunks
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.mime_type') = 'application/pdf'
GROUP BY filename
ORDER BY chunks DESC
```

**Search PDF content:**
```sql
SELECT
  JSON_VALUE(metadata, '$.filename') as filename,
  chunk_index,
  LEFT(content, 200) as preview
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.mime_type') = 'application/pdf'
  AND LOWER(content) LIKE '%grid code%'
LIMIT 10
```

**Get specific document chunks:**
```sql
SELECT
  chunk_index,
  content
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE JSON_VALUE(metadata, '$.filename') = 'Grid_Code_Rev_63.pdf'
ORDER BY chunk_index
```

### Test Script

Location: `/home/george/GB-Power-Market-JJ/test_chatgpt_pdf_search.sh`

```bash
#!/bin/bash
# Test ChatGPT can find PDFs via Railway endpoint

RAILWAY_URL="https://jibber-jabber-production.up.railway.app"
AUTH_TOKEN="Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Test 1: List PDFs
curl -X POST "$RAILWAY_URL/query_bigquery" \
  -H "Authorization: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT JSON_VALUE(metadata, '\''$.filename'\'') as filename, COUNT(*) as chunks FROM document_chunks WHERE mime_type='\''application/pdf'\'' GROUP BY filename LIMIT 5"}'

# Test 2: Search for 'grid code'
curl -X POST "$RAILWAY_URL/query_bigquery" \
  -H "Authorization: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT filename, chunk_index, LEFT(content, 150) as preview FROM document_chunks WHERE mime_type='\''application/pdf'\'' AND LOWER(content) LIKE '\''%grid code%'\'' LIMIT 3"}'
```

---

## 🖥️ Where Python Code Runs

### Railway Container (Current Setup)

```
Railway Cloud Server
    ↓
FastAPI (codex_server.py)
    ↓
Receives code from ChatGPT
    ↓
Writes to /tmp/xxxxx.py
    ↓
subprocess.run([python3, temp.py])
    ↓
Captures stdout/stderr
    ↓
Returns to ChatGPT
```

**Railway Specs:**
- Memory: ~512MB-2GB
- CPU: 1-2 shared vCPUs
- Storage: Ephemeral (temp only)
- Cost: $5-10/month after free tier

**Code Execution Flow:**
```python
# In codex_server.py on Railway

def execute_python(code: str, timeout: int = 30) -> dict:
    """Execute Python code in a temporary file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name

    result = subprocess.run(
        [sys.executable, temp_file],
        capture_output=True,
        text=True,
        timeout=timeout
    )

    return {
        'output': result.stdout,
        'error': result.stderr,
        'exit_code': result.returncode
    }
```

### Dell Server (Recommended for Heavy Processing)

**Your Dell Advantage:**
- 125 GB RAM vs Railway's ~1 GB (125x more!)
- 32 CPU cores vs Railway's 1-2 (16-32x more!)
- 913 GB storage vs Railway's ephemeral
- Already has BigQuery credentials
- Already running 24/7
- No cost (vs Railway's $5-10/month)

**Perfect for:**
- Processing 391M rows of bid-offer data
- Multi-table joins across millions of rows
- Statistical analysis requiring lots of memory
- Machine learning model training
- Real-time IRIS data pipeline (already running)

---

## 📋 Verification Checklist

### Before Fixing
- [ ] ❌ ChatGPT queries return "Cannot access" errors
- [ ] ❌ Vercel proxy returns 404 NOT FOUND
- [ ] ❌ ChatGPT action shows failed status
- [ ] ✅ Railway backend is healthy
- [ ] ✅ BigQuery accessible from Railway
- [ ] ✅ PDF chunks exist in database

### After Fixing (Option 1 - Railway Direct)
- [ ] ✅ ChatGPT schema updated to Railway URL
- [ ] ✅ Authentication set to Bearer token
- [ ] ✅ Test query returns data successfully
- [ ] ✅ ChatGPT can list PDFs
- [ ] ✅ ChatGPT can search PDF content
- [ ] ✅ ChatGPT can query BigQuery tables

### After Fixing (Option 3 - Dell Server)
- [ ] ✅ FastAPI running on Dell port 8000
- [ ] ✅ Firewall port 8000 opened
- [ ] ✅ Health check responds: `http://94.237.55.234:8000/health`
- [ ] ✅ BigQuery access working from Dell
- [ ] ✅ ChatGPT schema updated to Dell IP
- [ ] ✅ Heavy queries complete without timeout

---

## 🧪 Test Queries for ChatGPT

Once fixed, test with these questions:

### PDF Search Tests
1. **"How many PDF documents do we have indexed?"**
   - Expected: ~1,117 PDFs with 35,168 chunks

2. **"Search for 'grid code' in our PDFs"**
   - Expected: Matches in Grid Code PDF with chunk numbers

3. **"What does the CUSC say about balancing services?"**
   - Expected: Excerpts from CUSC document

### BigQuery Tests
4. **"What tables exist in uk_energy_prod dataset?"**
   - Expected: List of 185+ tables

5. **"What was the average energy price in bmrs_mid yesterday?"**
   - Expected: SQL query result with average price

6. **"How many VLP units are in our database?"**
   - Expected: Count of Virtual Lead Party units

### Heavy Processing Tests (Dell only)
7. **"Analyze all 391 million rows of bid-offer data for October 2025"**
   - Expected: Statistical summary (will timeout on Railway, work on Dell)

8. **"Calculate monthly revenue for all VLP units across 2 years"**
   - Expected: Multi-table join results (needs Dell's RAM)

---

## 📁 Related Files

### Schema Files
- `CHATGPT_COMPLETE_SCHEMA.json` - Full API schema for Railway
- `CHATGPT_FULL_WORKSPACE_SCHEMA.json` - Includes Google Workspace
- `chatgpt-schema-fixed.json` - Minimal version
- `chatgpt-action-schema-railway.json` - Railway-specific

### Documentation
- `docs/CHATGPT_PDF_ACCESS_GUIDE.md` - PDF search guide
- `docs/CHATGPT_ACTUAL_ACCESS.md` - Access verification
- `docs/CHATGPT_INSTRUCTIONS_WITH_WORKSPACE.md` - Full instructions
- `docs/CHATGPT_DASHBOARD_ACCESS_STATUS.md` - Dashboard access

### Server Code
- `codex-server/codex_server.py` - FastAPI backend
- `vercel-proxy/api/proxy-v2.ts` - Vercel proxy (broken)
- `test_chatgpt_pdf_search.sh` - Test script

### Scripts
- `index_drive_pdfs.py` - PDF chunking pipeline
- `bigquery_document_search.py` - Document search
- `drive-bq-indexer/src/chunking.py` - Chunking logic

---

## 🚀 Quick Fix (5 Minutes)

**Fastest solution to restore ChatGPT access:**

1. **Copy schema file:**
   ```bash
   cat /home/george/GB-Power-Market-JJ/CHATGPT_COMPLETE_SCHEMA.json
   ```

2. **Go to ChatGPT:**
   - https://chatgpt.com → My GPTs → [Your GPT] → Edit

3. **Update Actions:**
   - Configure → Actions → Edit Schema
   - Delete old schema
   - Paste contents of CHATGPT_COMPLETE_SCHEMA.json

4. **Set Authentication:**
   - Type: Bearer
   - Token: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

5. **Test:**
   - Click "Test" button
   - Should see: "Test successful"

6. **Save and verify:**
   - Update GPT
   - Ask: "How many PDFs do we have?"
   - Should return: 1,117 PDFs with 35,168 chunks

---

## 📞 Support

**Railway Backend:**
- URL: https://jibber-jabber-production.up.railway.app
- Status: https://jibber-jabber-production.up.railway.app/health
- Auth: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA

**Dell Server:**
- IP: 94.237.55.234
- Port: 8000 (when running codex_server.py)
- BigQuery: ✅ Configured with inner-cinema-credentials.json

**BigQuery:**
- Project: inner-cinema-476211-u9
- Location: US
- Credentials: /home/george/GB-Power-Market-JJ/inner-cinema-credentials.json

---

**Last Verified:** December 18, 2025
**Status:** Railway working ✅ | Vercel broken ❌ | Dell ready ✅
