# Google Sheets API Proxy for ChatGPT - Setup Guide

## Overview

This adds Google Sheets read/write capability to your Vercel proxy, enabling ChatGPT to:
- ✅ Read data from your dashboard: `https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
- ✅ Write data to update cells
- ✅ List all sheets in the spreadsheet
- ✅ Monitor FR Revenue Optimizer results

---

## Prerequisites

1. ✅ Vercel account with CLI installed
2. ✅ Google service account credentials (`inner-cinema-credentials.json`)
3. ✅ Spreadsheet ID: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`

---

## Step 1: Extract Service Account Credentials

```bash
cd /Users/georgemajor/GB-Power-Market-JJ

# Extract credentials from JSON file
cat inner-cinema-credentials.json | jq -r '.private_key_id'
cat inner-cinema-credentials.json | jq -r '.private_key'
cat inner-cinema-credentials.json | jq -r '.client_email'
cat inner-cinema-credentials.json | jq -r '.client_id'
```

---

## Step 2: Set Vercel Environment Variables

```bash
cd vercel-proxy

# Set Google credentials as Vercel secrets
vercel env add GOOGLE_PRIVATE_KEY_ID
# Paste: <value from step 1>

vercel env add GOOGLE_PRIVATE_KEY
# Paste: <value from step 1 - include the entire key with \n characters>

vercel env add GOOGLE_CLIENT_EMAIL
# Paste: <value from step 1>

vercel env add GOOGLE_CLIENT_ID
# Paste: <value from step 1>
```

**Note**: When pasting the private key, keep it as a single line with `\n` characters preserved.

---

## Step 3: Deploy to Vercel

```bash
cd vercel-proxy

# Deploy (will use environment variables set above)
vercel --prod
```

Expected output:
```
✅ Production: https://gb-power-market-jj.vercel.app [copied to clipboard]
📝  Deployed to production. Run `vercel --prod` to overwrite later.
```

---

## Step 4: Test the New Endpoint

### Health Check
```bash
curl "https://gb-power-market-jj.vercel.app/api/sheets?action=health"
```

Expected response:
```json
{
  "status": "healthy",
  "spreadsheet_id": "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc",
  "actions": ["read", "write", "get_sheets", "health"],
  "timestamp": "2025-12-01T19:00:00.000Z"
}
```

### List All Sheets
```bash
curl "https://gb-power-market-jj.vercel.app/api/sheets?action=get_sheets"
```

Expected response:
```json
{
  "spreadsheet_id": "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc",
  "sheets": [
    "Dashboard",
    "FR Revenue",
    "Daily_Chart_Data",
    "BESS",
    ...
  ],
  "count": 15
}
```

### Read Dashboard Data
```bash
curl "https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=Dashboard&range=A1:Z20"
```

Expected response:
```json
{
  "spreadsheet_id": "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc",
  "sheet": "Dashboard",
  "range": "A1:Z20",
  "values": [
    ["Fuel Type", "Capacity (MW)", "Generation (MW)", ...],
    ["Wind", "28523", "12456", ...],
    ...
  ],
  "row_count": 20
}
```

### Write Test Data
```bash
curl -X POST "https://gb-power-market-jj.vercel.app/api/sheets?action=write&sheet=FR%20Revenue&range=A1:B2" \
  -H "Content-Type: application/json" \
  -d '{
    "values": [
      ["Test Header 1", "Test Header 2"],
      ["Test Value 1", "Test Value 2"]
    ]
  }'
```

Expected response:
```json
{
  "success": true,
  "spreadsheet_id": "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc",
  "sheet": "FR Revenue",
  "range": "A1:B2",
  "rows_written": 2
}
```

---

## Step 5: ChatGPT Integration

### Update ChatGPT Custom Instructions

Add these examples to your ChatGPT custom GPT instructions:

```markdown
## Google Sheets Access

You can now read and write to the Google Sheets dashboard via the Sheets API proxy.

### Available Actions

1. **Health Check**
   GET https://gb-power-market-jj.vercel.app/api/sheets?action=health

2. **List All Sheets**
   GET https://gb-power-market-jj.vercel.app/api/sheets?action=get_sheets

3. **Read Data**
   GET https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=Dashboard&range=A1:Z100

4. **Write Data**
   POST https://gb-power-market-jj.vercel.app/api/sheets?action=write&sheet=FR%20Revenue&range=A1:B10
   Body: {"values": [["Header 1", "Header 2"], ["Value 1", "Value 2"]]}

### Example Queries

**User**: "Show me the FR Revenue data from the dashboard"
**ChatGPT**: 
```javascript
fetch('https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=FR%20Revenue&range=A1:H50')
```

**User**: "Update cell A1 in the FR Revenue sheet with today's date"
**ChatGPT**:
```javascript
fetch('https://gb-power-market-jj.vercel.app/api/sheets?action=write&sheet=FR%20Revenue&range=A1', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({values: [[new Date().toLocaleDateString()]]})
})
```
```

---

## API Reference

### Endpoints

#### GET /api/sheets?action=health
Returns health status and available actions.

**Response**:
```json
{
  "status": "healthy",
  "spreadsheet_id": "...",
  "actions": ["read", "write", "get_sheets", "health"],
  "timestamp": "2025-12-01T19:00:00.000Z"
}
```

#### GET /api/sheets?action=get_sheets
Returns list of all sheets in the spreadsheet.

**Response**:
```json
{
  "spreadsheet_id": "...",
  "sheets": ["Dashboard", "FR Revenue", ...],
  "count": 15
}
```

#### GET /api/sheets?action=read&sheet=SHEET_NAME&range=RANGE
Reads data from specified sheet and range.

**Parameters**:
- `sheet`: Sheet name (e.g., "Dashboard", "FR Revenue")
- `range`: A1 notation (e.g., "A1:Z100")

**Response**:
```json
{
  "spreadsheet_id": "...",
  "sheet": "Dashboard",
  "range": "A1:Z20",
  "values": [["row1col1", "row1col2"], ["row2col1", "row2col2"]],
  "row_count": 2
}
```

#### POST /api/sheets?action=write&sheet=SHEET_NAME&range=RANGE
Writes data to specified sheet and range.

**Parameters**:
- `sheet`: Sheet name
- `range`: A1 notation

**Body**:
```json
{
  "values": [
    ["Header 1", "Header 2"],
    ["Value 1", "Value 2"]
  ]
}
```

**Response**:
```json
{
  "success": true,
  "spreadsheet_id": "...",
  "sheet": "FR Revenue",
  "range": "A1:B2",
  "rows_written": 2
}
```

---

## Use Cases

### 1. ChatGPT Monitors FR Optimizer Results

**Query**: "What's the latest FR revenue from the optimizer?"

**ChatGPT Action**:
```javascript
fetch('https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=FR%20Revenue&range=A1:H50')
// Parse response and show monthly summary
```

### 2. ChatGPT Updates Dashboard with Analysis

**Query**: "Add a note about today's arbitrage opportunity"

**ChatGPT Action**:
```javascript
fetch('https://gb-power-market-jj.vercel.app/api/sheets?action=write&sheet=Dashboard&range=A100', {
  method: 'POST',
  body: JSON.stringify({
    values: [[`Analysis: High arbitrage opportunity - £150/MWh spread at 17:00`]]
  })
})
```

### 3. ChatGPT Creates Summary Tables

**Query**: "Summarize this week's FR revenue and write it to the dashboard"

**ChatGPT Action**:
1. Query BigQuery for FR data
2. Calculate weekly summary
3. Write to "FR Revenue" sheet:
```javascript
fetch('https://gb-power-market-jj.vercel.app/api/sheets?action=write&sheet=FR%20Revenue&range=A20:G20', {
  method: 'POST',
  body: JSON.stringify({
    values: [[
      '2025-12-01',
      'Week 48',
      '£8,773',
      '£9,703',
      '£930',
      'DR: 65%',
      'Optimizer +113% vs DC'
    ]]
  })
})
```

---

## Troubleshooting

### Error: "Google service account credentials not configured"

**Cause**: Environment variables not set in Vercel

**Fix**:
```bash
# Re-add environment variables
cd vercel-proxy
vercel env add GOOGLE_PRIVATE_KEY_ID
vercel env add GOOGLE_PRIVATE_KEY
vercel env add GOOGLE_CLIENT_EMAIL
vercel env add GOOGLE_CLIENT_ID

# Redeploy
vercel --prod
```

### Error: "Failed to get access token"

**Cause**: Invalid private key format

**Fix**: Ensure private key is a single line with `\n` preserved:
```bash
# Extract and format correctly
cat inner-cinema-credentials.json | jq -r '.private_key' | sed 's/$/\\n/g' | tr -d '\n'
```

### Error: "Failed to read sheet: 403"

**Cause**: Service account doesn't have access to spreadsheet

**Fix**: Share spreadsheet with service account email:
```bash
# Get service account email
cat inner-cinema-credentials.json | jq -r '.client_email'

# Share spreadsheet with this email (Editor permissions)
```

### Error: "Cannot find name 'process'"

**Cause**: TypeScript compilation issue

**Fix**: Already handled with `declare const process` in code

---

## Security Notes

1. **Environment Variables**: Never commit credentials to git
2. **Access Control**: Spreadsheet must be shared with service account
3. **Rate Limiting**: Google Sheets API has quotas (100 requests/100 seconds/user)
4. **CORS**: All endpoints include `Access-Control-Allow-Origin: *` for ChatGPT access

---

## Next Steps

1. ✅ **Deploy**: `cd vercel-proxy && vercel --prod`
2. ✅ **Test**: Run health check and test read/write
3. ✅ **ChatGPT**: Update custom GPT instructions with new endpoints
4. ⏳ **Monitor**: Check Vercel logs for any errors
5. ⏳ **Optimize**: Add caching for frequently accessed data

---

## File Reference

- **API Endpoint**: `vercel-proxy/api/sheets.ts`
- **Setup Guide**: `vercel-proxy/SHEETS_API_SETUP.md` (this file)
- **Deployment**: `vercel-proxy/deploy.sh`
- **Credentials**: `inner-cinema-credentials.json` (NOT in git)

---

**Status**: ✅ Ready to Deploy  
**Date**: 1 December 2025  
**Author**: George Major
