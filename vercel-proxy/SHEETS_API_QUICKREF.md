# ChatGPT Google Sheets Access - Quick Reference

## ✅ NOW AVAILABLE: ChatGPT Can Access Your Google Sheets!

Your dashboard at `https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc` is now accessible to ChatGPT via the new Sheets API proxy.

---

## Quick Examples

### 1. View FR Revenue Results
```
User: "Show me the FR Revenue data from the dashboard"

ChatGPT uses:
GET https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=FR%20Revenue&range=A1:H50
```

### 2. Check Current Dashboard Status
```
User: "What's on the Dashboard right now?"

ChatGPT uses:
GET https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=Dashboard&range=A1:Z50
```

### 3. List All Available Sheets
```
User: "What sheets are in my spreadsheet?"

ChatGPT uses:
GET https://gb-power-market-jj.vercel.app/api/sheets?action=get_sheets
```

### 4. Update FR Revenue Summary
```
User: "Add today's FR results: £8,773 net margin"

ChatGPT uses:
POST https://gb-power-market-jj.vercel.app/api/sheets?action=write&sheet=FR%20Revenue&range=A20:B20
Body: {"values": [["2025-12-01", "£8,773"]]}
```

---

## API Endpoints Summary

| Action | Method | URL | Purpose |
|--------|--------|-----|---------|
| Health Check | GET | `/api/sheets?action=health` | Verify API is working |
| List Sheets | GET | `/api/sheets?action=get_sheets` | Get all sheet names |
| Read Data | GET | `/api/sheets?action=read&sheet=NAME&range=RANGE` | Read cells |
| Write Data | POST | `/api/sheets?action=write&sheet=NAME&range=RANGE` | Write cells |

---

## Common Use Cases

### Monitor FR Optimizer
```
"What's the latest monthly net margin from the FR optimizer?"
→ Reads FR Revenue sheet, shows summary
```

### Dashboard Health Check
```
"Check if my dashboard is updating correctly"
→ Reads Dashboard sheet, verifies timestamps
```

### Analysis Results
```
"Show me the service selection breakdown (DC/DM/DR)"
→ Reads FR Revenue sheet, shows percentages
```

### Update Notes
```
"Add a note that today had unusually high DR prices"
→ Writes to notes section in FR Revenue sheet
```

---

## Deployment Status

✅ **API Endpoint**: `https://gb-power-market-jj.vercel.app/api/sheets`  
✅ **Spreadsheet**: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`  
✅ **Credentials**: Service account configured in Vercel environment  
✅ **Permissions**: Service account has Editor access to spreadsheet  

---

## Test It Now

```bash
# Health check
curl "https://gb-power-market-jj.vercel.app/api/sheets?action=health"

# List sheets
curl "https://gb-power-market-jj.vercel.app/api/sheets?action=get_sheets"

# Read Dashboard
curl "https://gb-power-market-jj.vercel.app/api/sheets?action=read&sheet=Dashboard&range=A1:C10"
```

---

## For ChatGPT Custom Instructions

Add this to your ChatGPT custom GPT:

```markdown
## Google Sheets Access (NEW)

You can now access George's Google Sheets dashboard directly via:
https://gb-power-market-jj.vercel.app/api/sheets

Available actions:
- Read data: ?action=read&sheet=SHEET_NAME&range=A1:Z100
- Write data: ?action=write&sheet=SHEET_NAME&range=A1:B10 (POST with {"values": [[...]]})
- List sheets: ?action=get_sheets
- Health check: ?action=health

Dashboard spreadsheet ID: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

Example queries:
- "Show me the FR Revenue data"
- "What's on the Dashboard?"
- "Update the FR Revenue sheet with today's results"
- "List all available sheets"
```

---

## Limitations

1. **Rate Limits**: 100 requests per 100 seconds per user (Google Sheets API quota)
2. **Data Size**: Best for <10,000 cells per request
3. **Real-time**: Not instant - allow 1-2 seconds for API calls
4. **Permissions**: Service account must have Editor access to spreadsheet

---

## Troubleshooting

### "Failed to get access token"
- Check Vercel environment variables are set
- Verify service account credentials are correct
- Run: `cd vercel-proxy && ./deploy-sheets-api.sh`

### "Failed to read sheet: 403"
- Spreadsheet not shared with service account
- Share with email from: `cat inner-cinema-credentials.json | jq -r '.client_email'`

### "Invalid sheet name"
- Sheet names are case-sensitive
- Use: `?action=get_sheets` to see available names
- URL encode sheet names with spaces: "FR%20Revenue"

---

## Files Created

1. **`/vercel-proxy/api/sheets.ts`** - Main API endpoint
2. **`/vercel-proxy/SHEETS_API_SETUP.md`** - Full setup guide
3. **`/vercel-proxy/deploy-sheets-api.sh`** - Automated deployment script
4. **`/vercel-proxy/SHEETS_API_QUICKREF.md`** - This file

---

**Ready to Use**: ✅ Yes  
**Deployment**: `cd vercel-proxy && ./deploy-sheets-api.sh`  
**Status**: Production Ready  
**Date**: 1 December 2025
