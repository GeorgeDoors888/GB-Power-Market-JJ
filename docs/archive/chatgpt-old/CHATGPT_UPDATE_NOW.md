# 🚀 Update ChatGPT NOW - Quick Guide

**Status:** ✅ Railway is WORKING! Schema is READY!  
**Date:** November 11, 2025  
**ChatGPT Link:** https://chatgpt.com/g/g-690f95eceb788191a021dc00389f41ee-gb-power-market-code-execution

---

## ⚡ Quick 5-Minute Update

### Step 1: Open ChatGPT Editor
1. Go to: https://chatgpt.com/g/g-690f95eceb788191a021dc00389f41ee-gb-power-market-code-execution
2. Click **"Edit GPT"** (top right)

### Step 2: Update Actions
1. Click **"Actions"** in the left sidebar
2. Find the action named **"GB Power Market API"**
3. Click **"Edit"** next to it
4. **Delete the entire existing schema**

### Step 3: Paste New Schema
1. Open: `CHATGPT_COMPLETE_SCHEMA.json` (in this folder)
2. **Copy the entire contents** (all 593 lines)
3. **Paste into ChatGPT** (replacing the old schema)

### Step 4: Verify Settings
Make sure these are set:
- **Authentication:** Bearer token
- **Bearer Token:** `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- **Privacy Policy:** (optional, can leave blank)

### Step 5: Save
1. Click **"Update"** or **"Save"**
2. Click **"Update"** again on the main GPT page
3. Done! ✅

---

## 🧪 Test Immediately

Once updated, test with these queries in ChatGPT:

### Test 1: Health Check
```
Can you check if the API is working?
```
**Expected:** Should return server status

### Test 2: Get Spreadsheet Info
```
Show me the structure of the GB Energy Dashboard spreadsheet
```
**Expected:** Should list all 29 worksheets

### Test 3: Read Data
```
Read cells A1 to C5 from the Dashboard worksheet
```
**Expected:** Should return data from those cells

### Test 4: BigQuery
```
Query BigQuery for the latest 5 records from bmrs_freq table
```
**Expected:** Should return frequency data

### Test 5: Drive Files
```
List the first 10 files in my Google Drive
```
**Expected:** Should return Drive files

---

## ✅ What Changed

### Removed (Too Slow ⚠️)
- ❌ `list_spreadsheets` operation - was timing out after 5+ minutes

### Working Endpoints (11 total)
1. ✅ `health_check` - Server health
2. ✅ `execute_code` - Run Python code
3. ✅ `query_bigquery` - Query BigQuery database
4. ✅ `workspace_health` - Workspace auth check
5. ✅ `get_spreadsheet` - Get spreadsheet info by ID/title
6. ✅ `read_sheet` - Read worksheet data
7. ✅ `write_sheet` - Write worksheet data
8. ✅ `list_drive_files` - Browse Drive files
9. ✅ `search_drive` - Search Drive
10. ✅ `read_doc` - Read Google Docs
11. ✅ `write_doc` - Write Google Docs

---

## 🎯 Key Differences from Before

### OLD Behavior (Hardcoded)
```json
{
  "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
}
```
- ❌ Could only access GB Energy Dashboard
- ❌ Had to change code to access different spreadsheets
- ❌ No Drive or Docs access

### NEW Behavior (Dynamic)
```json
{
  "spreadsheet_id": "ANY_SPREADSHEET_ID",
  "spreadsheet_title": "Or use the title"
}
```
- ✅ Access ANY spreadsheet by ID or title
- ✅ Full Drive access (list, search)
- ✅ Full Docs access (read, write)
- ✅ GB Energy Dashboard is still the default if no ID provided

---

## 💡 Pro Tips

### For Spreadsheets
- **Default access:** Just ask "read Dashboard worksheet" - uses GB Energy Dashboard
- **Custom spreadsheet:** Say "read worksheet X from spreadsheet Y" - ChatGPT will search by title
- **Use IDs for speed:** If you know the ID, include it: "spreadsheet ID 12jY0..."

### For Drive
- **Browse:** "List my Google Drive files"
- **Filter:** "Show me all spreadsheets in Drive"
- **Search:** "Find files containing 'energy' in my Drive"

### For Docs
- **Read:** "Read the Google Doc titled X"
- **Write:** "Append 'new text' to the Doc titled Y"

---

## 🔧 Troubleshooting

### If Endpoints Don't Work
1. Check DNS: `ping jibber-jabber-production.up.railway.app`
2. If fails, add to `/etc/hosts`:
   ```
   66.33.22.174 jibber-jabber-production.up.railway.app
   ```
3. Flush DNS: `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`

### If ChatGPT Says "Action Failed"
- Check bearer token is correct
- Verify Railway is running: `cd codex-server && railway status`
- Check logs: `railway logs --tail 50`

### If Slow Responses
- Normal: First request wakes Railway container (~2-5 seconds)
- Spreadsheet reads: 2-4 seconds typical
- BigQuery queries: 1-3 seconds typical
- If >30 seconds: Check Railway logs for errors

---

## 📊 Validation Checklist

After updating, verify:

- [ ] ChatGPT shows 11 operations (not 12)
- [ ] `list_spreadsheets` is NOT in the list
- [ ] Bearer token is set correctly
- [ ] Test query returns data successfully
- [ ] No authentication errors
- [ ] Response time <10 seconds

---

## 📁 Reference Files

- **This Guide:** `CHATGPT_UPDATE_NOW.md`
- **Schema File:** `CHATGPT_COMPLETE_SCHEMA.json` (593 lines)
- **Success Summary:** `WORKSPACE_SUCCESS_SUMMARY.md`
- **Full Details:** `WORKSPACE_INTEGRATION_COMPLETE.md`
- **API Docs:** `GOOGLE_WORKSPACE_FULL_ACCESS.md`
- **DNS Fix:** `DNS_ISSUE_RESOLUTION.md`

---

## 🎉 You're Ready!

Everything is working:
- ✅ Railway deployed and responding
- ✅ Credentials configured
- ✅ Domain-wide delegation verified
- ✅ Endpoints tested and working
- ✅ Schema optimized (slow endpoint removed)
- ✅ Documentation complete

**Just update the schema in ChatGPT and you're done!** 🚀

---

**Last Updated:** November 11, 2025  
**Latest Commit:** 41d2eac5  
**Status:** Production Ready ✅
