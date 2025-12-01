# Google Sheets API - Railway Deployment

## ✅ What Was Added

Added Google Sheets API endpoints to existing Railway server at:
`https://jibber-jabber-production.up.railway.app`

### New Endpoints

1. **Health Check** (Public)
   ```bash
   GET /sheets_health
   ```
   Response:
   ```json
   {
     "ok": true,
     "message": "Google Sheets API is healthy",
     "spreadsheet_id": "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc",
     "sheets_api_available": true
   }
   ```

2. **List All Sheets**
   ```bash
   GET /sheets_list
   Headers: Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   ```
   Response:
   ```json
   {
     "ok": true,
     "sheets": ["Dashboard", "FR Revenue", "BESS", "Stats", "..."],
     "count": 15
   }
   ```

3. **Read Sheet Data**
   ```bash
   POST /sheets_read
   Headers: Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   Body: {
     "sheet": "Dashboard",
     "range": "A1:Z50"
   }
   ```

4. **Write Sheet Data**
   ```bash
   POST /sheets_write
   Headers: Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   Body: {
     "sheet": "FR Revenue",
     "range": "A20:B20",
     "values": [["2025-12-01", "£8,773"]]
   }
   ```

## Access via Vercel Proxy (ChatGPT)

ChatGPT can access these endpoints through the existing Vercel proxy:

### 1. Health Check
```
GET https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_health
```

### 2. List Sheets
```
GET https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_list
```

### 3. Read Data
```
POST https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_read
Body: {"sheet": "Dashboard", "range": "A1:Z50"}
```

### 4. Write Data
```
POST https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_write
Body: {"sheet": "FR Revenue", "range": "A20:B20", "values": [["Test", "Data"]]}
```

## Deployment Steps

### 1. Commit Changes
```bash
cd /Users/georgemajor/GB-Power-Market-JJ
git add codex-server/codex_server_secure.py
git add vercel-proxy/api/proxy-v2.ts
git commit -m "Add Google Sheets API endpoints to Railway server"
git push
```

### 2. Railway Auto-Deploy
Railway will automatically deploy the changes when you push to GitHub.

### 3. Deploy Vercel Proxy Update
```bash
cd /Users/georgemajor/GB-Power-Market-JJ/vercel-proxy
vercel --prod
```

## Testing

### Test Railway Direct (with auth token)
```bash
# Health check
curl "https://jibber-jabber-production.up.railway.app/sheets_health"

# List sheets
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  "https://jibber-jabber-production.up.railway.app/sheets_list"

# Read data
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"sheet": "Dashboard", "range": "A1:C10"}' \
  "https://jibber-jabber-production.up.railway.app/sheets_read"
```

### Test via Vercel Proxy (no auth needed - for ChatGPT)
```bash
# Health check
curl "https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_health"

# List sheets
curl "https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_list"

# Read data
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"sheet": "Dashboard", "range": "A1:C10"}' \
  "https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/sheets_read"
```

## For ChatGPT

Add to ChatGPT custom instructions:

```markdown
## Google Sheets Access (NEW)

You can now access George's Google Sheets dashboard via the existing proxy:

Base URL: https://gb-power-market-jj.vercel.app/api/proxy-v2

Sheets endpoints:
- Health: ?path=/sheets_health
- List sheets: ?path=/sheets_list
- Read: ?path=/sheets_read (POST with {"sheet": "NAME", "range": "A1:Z100"})
- Write: ?path=/sheets_write (POST with {"sheet": "NAME", "range": "A1:B10", "values": [[...]]})

Spreadsheet ID: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

Examples:
- "Show me FR Revenue data" → POST to /sheets_read with sheet="FR Revenue"
- "List all sheets" → GET /sheets_list
- "Update dashboard note" → POST to /sheets_write
```

## Code Changes Made

### 1. codex_server_secure.py
- Added Google Sheets API client initialization
- Added 4 new endpoints: sheets_health, sheets_list, sheets_read, sheets_write
- Uses existing Google credentials (GOOGLE_CREDENTIALS_BASE64 env var)
- All endpoints require Authorization header (except health)

### 2. proxy-v2.ts
- Added Sheets endpoints to ALLOW list
- Enables ChatGPT access without authentication

### 3. Dependencies
- Already included: google-api-python-client>=2.100.0 ✅
- Already included: google-auth>=2.23.0 ✅

## Benefits

✅ **No Vercel authentication issues** - uses Railway  
✅ **Uses existing infrastructure** - same server as BigQuery  
✅ **ChatGPT already has access** - via proxy-v2  
✅ **Zero additional cost** - Railway free tier  
✅ **Automatic auth** - proxy handles bearer token  

## Next Steps

1. Push code to GitHub → Railway auto-deploys
2. Deploy Vercel proxy update → `vercel --prod`
3. Test endpoints → Use curl commands above
4. Update ChatGPT → Add Sheets API examples to custom instructions

---

**Status**: ✅ Code Ready - Awaiting Deployment  
**Date**: 1 December 2025  
**Maintainer**: George Major
