# Update ChatGPT with Full Workspace Access

## Overview
You now have **9 new Google Workspace endpoints** deployed to Railway. This guide will help you update your ChatGPT Custom GPT to use all 15 operations (6 original + 9 workspace).

## What's New?
- **Dynamic spreadsheet access** - No more hardcoded GB Energy Dashboard!
- **Full Drive browsing** - List and search ALL files in Google Drive
- **Google Docs support** - Read and write to any Google Doc
- **Write capabilities** - Update spreadsheets and documents from ChatGPT

## Step-by-Step Update Instructions

### 1. Open Your ChatGPT GPT Editor
1. Go to: https://chat.openai.com/gpts/mine
2. Find: **"Jibber Jabber Knowledge"** (or your GB Power Market GPT)
3. Click: **Edit** button

### 2. Navigate to Actions
1. Scroll down to the **Actions** section
2. You should see existing action: **"GB Power Market API"**
3. Click the **Edit** (pencil) icon next to it

### 3. Replace the Schema
1. You'll see a large JSON schema in the text editor
2. **Delete everything** in that editor
3. Open the file: `CHATGPT_COMPLETE_SCHEMA.json` (in this directory)
4. **Copy ALL contents** of that file
5. **Paste** into the ChatGPT action editor

### 4. Verify Authentication
1. Scroll down to **Authentication** section
2. Ensure it's set to: **Bearer**
3. Token should be: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
4. If missing, add it now

### 5. Save Changes
1. Click **Update** or **Save** button
2. ChatGPT will validate the schema (should show green checkmark)
3. Wait for "Actions updated successfully" message

### 6. Test the Update
Click **Preview** (top right) and try these queries:

**Test 1: List All Spreadsheets**
```
List all my Google Sheets spreadsheets
```
*Should use: `list_spreadsheets` operation*

**Test 2: Dynamic Spreadsheet Access**
```
Show me the worksheets in the GB Energy Dashboard
```
*Should use: `get_spreadsheet` operation with default ID*

**Test 3: Read from Any Sheet**
```
Read the Dashboard worksheet from GB Energy spreadsheet
```
*Should use: `read_sheet` operation*

**Test 4: Search Drive**
```
Search my Drive for files containing "energy"
```
*Should use: `search_drive` operation*

**Test 5: List Drive Files**
```
Show me all spreadsheets in my Drive
```
*Should use: `list_drive_files` with mime_type filter*

## What Changed from Before?

### Original 3 Endpoints (Enhanced):
1. `/workspace/health` - Now lists ALL spreadsheets (not just GB Energy)
2. `/workspace/dashboard` → `/workspace/get_spreadsheet` - Now accepts any spreadsheet ID/title
3. `/workspace/read_sheet` - Now accepts `spreadsheet_id` parameter

### New 6 Endpoints:
4. `/workspace/list_spreadsheets` - Full inventory of all spreadsheets
5. `/workspace/write_sheet` - Update cells in any spreadsheet
6. `/workspace/list_drive_files` - Browse Drive files with filters
7. `/workspace/search_drive` - Search Drive by query, type, date
8. `/workspace/read_doc` - Read Google Docs content
9. `/workspace/write_doc` - Write/update Google Docs

## Common ChatGPT Queries to Try

### Spreadsheets
```
"List all my spreadsheets"
"Show me the UK Energy Data spreadsheet"
"Read row 5 from the Dashboard sheet"
"Write 'Updated' to cell A1 in the Dashboard sheet"
```

### Google Drive
```
"List all PDF files in my Drive"
"Search for files containing 'battery arbitrage'"
"Show me spreadsheets modified this week"
"Find all documents created in November 2025"
```

### Google Docs
```
"Read the Project Notes document (ID: abc123...)"
"Append 'New update: ...' to the Meeting Notes doc"
```

### Combined Queries
```
"List all spreadsheets, then read the Dashboard sheet from GB Energy"
"Search for energy-related files, then read the first spreadsheet"
```

## Troubleshooting

### ❌ "Action validation failed"
- **Cause**: JSON syntax error in schema
- **Fix**: Re-copy `CHATGPT_COMPLETE_SCHEMA.json` carefully (no truncation)

### ❌ "Authentication failed"
- **Cause**: Bearer token missing or wrong
- **Fix**: Ensure token is `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

### ❌ "No operation found"
- **Cause**: ChatGPT didn't detect the new endpoints
- **Fix**: Re-save the action, or try more explicit queries like "use list_spreadsheets operation"

### ❌ "Connection timeout"
- **Cause**: Railway container was idle
- **Fix**: Normal! Railway wakes up on first request (takes 5-10 seconds)
- **Solution**: Try the query again immediately

### ❌ "Spreadsheet not found"
- **Cause**: Using old hardcoded ID instead of dynamic parameter
- **Fix**: Schema updated correctly! Old chats may have cached behavior. Start fresh chat.

## Verification Checklist

- [ ] Opened ChatGPT GPT editor
- [ ] Found "GB Power Market API" action
- [ ] Replaced entire schema with `CHATGPT_COMPLETE_SCHEMA.json`
- [ ] Verified Bearer token is present
- [ ] Clicked Save/Update
- [ ] Tested "List all my spreadsheets" query
- [ ] Confirmed ChatGPT sees 15 operations (not just 6)
- [ ] Tested dynamic spreadsheet access

## Files Reference

**Complete Schema**: `CHATGPT_COMPLETE_SCHEMA.json` (copy/paste this into ChatGPT)
**API Documentation**: `GOOGLE_WORKSPACE_FULL_ACCESS.md` (reference for all endpoints)
**Server Code**: `codex-server/codex_server_secure.py` (deployed to Railway)

## Next Steps After Update

1. **Test Write Operations**
   - Try: "Write 'Test' to cell A1 in Dashboard sheet"
   - Verify change appears in actual Google Sheet

2. **Test Drive Search**
   - Try: "Find all spreadsheets modified last month"
   - Verify results match your Drive contents

3. **Test Google Docs**
   - Try: "Read the [document name] document"
   - Try: "Append 'Update from ChatGPT' to [document name]"

4. **Create Automation Workflows**
   - Example: "Search for 'VLP analysis' spreadsheets, read the latest one, then query BigQuery for recent VLP data"
   - ChatGPT can now chain workspace + BigQuery operations!

## Support

If you encounter issues:
1. Check `GOOGLE_WORKSPACE_FULL_ACCESS.md` for endpoint details
2. Test endpoints directly via curl (examples in that doc)
3. Check Railway logs: https://railway.app/project/[your-project]/deployments

---

**Status**: ✅ Schema ready to paste
**File to use**: `CHATGPT_COMPLETE_SCHEMA.json`
**Last updated**: November 2025
