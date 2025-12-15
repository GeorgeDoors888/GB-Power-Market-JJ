# 🚀 Comprehensive Google Workspace API - Complete Access

**Status**: ✅ **DEPLOYED**  
**Date**: November 11, 2025  
**Base URL**: https://jibber-jabber-production.up.railway.app

---

## 🎯 Overview

Your ChatGPT now has **FULL READ/WRITE ACCESS** to:
- ✅ **All Google Sheets** (read, write, update)
- ✅ **All Google Docs** (read, write, update)  
- ✅ **All Google Drive files** (list, search)
- ✅ **Dynamic access** - No hardcoded IDs, works with any file

---

## 📊 New Endpoints Summary

### 🔍 Discovery & Search
1. `/workspace/health` - Test access + list accessible spreadsheets
2. `/workspace/list_drive_files` - List ALL Drive files (Docs, Sheets, PDFs, folders)
3. `/workspace/search_drive` - Search Drive by filename or content

### 📄 Google Sheets
4. `/workspace/list_spreadsheets` - List all accessible spreadsheets
5. `/workspace/get_spreadsheet` - Get info about specific spreadsheet (by ID or title)
6. `/workspace/read_sheet` - Read data from any sheet in any spreadsheet
7. `/workspace/write_sheet` - **NEW!** Write/update data in sheets

### 📝 Google Docs
8. `/workspace/read_doc` - **NEW!** Read content from Google Docs
9. `/workspace/write_doc` - **NEW!** Write/update Google Docs

---

## 🔌 API Endpoints Detail

### 1. Health Check (Enhanced)

**Endpoint**: `GET /workspace/health`

**Purpose**: Verify access and list available spreadsheets

**Example**:
```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  https://jibber-jabber-production.up.railway.app/workspace/health
```

**Response**:
```json
{
  "status": "healthy",
  "message": "Workspace access working!",
  "services": {
    "sheets": "ok",
    "drive": "ok"
  },
  "accessible_spreadsheets": 15,
  "sample_spreadsheets": [
    {
      "title": "GB Energy Dashboard",
      "id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
      "url": "https://docs.google.com/spreadsheets/d/..."
    }
  ]
}
```

---

### 2. List All Drive Files

**Endpoint**: `GET /workspace/list_drive_files?file_type=<type>`

**Purpose**: List all files in Google Drive

**Parameters**:
- `file_type` (optional): Filter by type: `doc`, `sheet`, `slide`, `pdf`, `folder`

**Examples**:
```bash
# List all files
curl -H "Authorization: Bearer codex_..." \
  https://jibber-jabber-production.up.railway.app/workspace/list_drive_files

# List only Google Docs
curl -H "Authorization: Bearer codex_..." \
  "https://jibber-jabber-production.up.railway.app/workspace/list_drive_files?file_type=doc"

# List only PDFs
curl -H "Authorization: Bearer codex_..." \
  "https://jibber-jabber-production.up.railway.app/workspace/list_drive_files?file_type=pdf"
```

**Response**:
```json
{
  "success": true,
  "total_files": 127,
  "files": [
    {
      "id": "1abc...",
      "name": "Project Plan.docx",
      "mimeType": "application/vnd.google-apps.document",
      "modifiedTime": "2025-11-10T14:32:00.000Z",
      "webViewLink": "https://docs.google.com/..."
    }
  ]
}
```

---

### 3. Search Drive

**Endpoint**: `POST /workspace/search_drive`

**Purpose**: Search Google Drive by filename or content

**Request Body**:
```json
{
  "query": "energy analysis",
  "file_type": "doc"  // optional: doc, sheet, slide, pdf, folder
}
```

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{"query": "battery", "file_type": "sheet"}' \
  https://jibber-jabber-production.up.railway.app/workspace/search_drive
```

**Response**:
```json
{
  "success": true,
  "query": "battery",
  "results_count": 5,
  "files": [
    {
      "id": "1xyz...",
      "name": "Battery Analysis 2025",
      "mimeType": "application/vnd.google-apps.spreadsheet",
      "webViewLink": "https://docs.google.com/..."
    }
  ]
}
```

---

### 4. List All Spreadsheets

**Endpoint**: `GET /workspace/list_spreadsheets`

**Purpose**: List all accessible Google Sheets spreadsheets

**Example**:
```bash
curl -H "Authorization: Bearer codex_..." \
  https://jibber-jabber-production.up.railway.app/workspace/list_spreadsheets
```

**Response**:
```json
{
  "success": true,
  "total_spreadsheets": 15,
  "spreadsheets": [
    {
      "title": "GB Energy Dashboard",
      "id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
      "url": "https://docs.google.com/spreadsheets/d/...",
      "worksheets": 29
    }
  ]
}
```

---

### 5. Get Spreadsheet Info

**Endpoint**: `POST /workspace/get_spreadsheet`

**Purpose**: Get detailed info about a specific spreadsheet

**Request Body**:
```json
{
  "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
  // OR
  "spreadsheet_title": "GB Energy Dashboard"
}
```

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_title": "GB Energy Dashboard"}' \
  https://jibber-jabber-production.up.railway.app/workspace/get_spreadsheet
```

**Response**:
```json
{
  "success": true,
  "title": "GB Energy Dashboard",
  "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
  "url": "https://docs.google.com/spreadsheets/d/...",
  "worksheets": [
    {
      "id": 0,
      "title": "Dashboard",
      "rows": 838,
      "cols": 27
    }
  ],
  "total_worksheets": 29
}
```

---

### 6. Read Sheet Data

**Endpoint**: `POST /workspace/read_sheet`

**Purpose**: Read data from any worksheet in any spreadsheet

**Request Body**:
```json
{
  "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
  // OR
  "spreadsheet_title": "GB Energy Dashboard",
  "worksheet_name": "Dashboard",
  "cell_range": "A1:E10"  // optional
}
```

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_title": "GB Energy Dashboard", "worksheet_name": "HH Profile", "cell_range": "A1:Z50"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet
```

**Response**:
```json
{
  "success": true,
  "spreadsheet_title": "GB Energy Dashboard",
  "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
  "worksheet_name": "HH Profile",
  "rows": 50,
  "cols": 26,
  "data": [
    ["Date", "Time", "Price", "Volume", ...],
    ["2025-11-01", "00:00", "45.23", "1234", ...],
    ...
  ]
}
```

---

### 7. Write/Update Sheet Data ✨ NEW!

**Endpoint**: `POST /workspace/write_sheet`

**Purpose**: Write or update data in Google Sheets

**Request Body**:
```json
{
  "spreadsheet_id": "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA",
  // OR
  "spreadsheet_title": "GB Energy Dashboard",
  "worksheet_name": "Dashboard",
  "cell_range": "A1:C3",
  "values": [
    ["Header1", "Header2", "Header3"],
    ["Value1", "Value2", "Value3"],
    ["Value4", "Value5", "Value6"]
  ]
}
```

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_title": "Test Sheet",
    "worksheet_name": "Sheet1",
    "cell_range": "A1:B2",
    "values": [["Name", "Value"], ["Test", "123"]]
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/write_sheet
```

**Response**:
```json
{
  "success": true,
  "spreadsheet_title": "Test Sheet",
  "worksheet_name": "Sheet1",
  "cell_range": "A1:B2",
  "rows_written": 2
}
```

---

### 8. Read Google Doc ✨ NEW!

**Endpoint**: `POST /workspace/read_doc`

**Purpose**: Read content from Google Docs

**Request Body**:
```json
{
  "document_id": "1abc123...",
  // OR
  "document_title": "Project Plan"
}
```

**Example**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{"document_title": "Project Plan"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_doc
```

**Response**:
```json
{
  "success": true,
  "document_id": "1abc123...",
  "title": "Project Plan",
  "content": "Full text content of the document...",
  "character_count": 5432
}
```

---

### 9. Write/Update Google Doc ✨ NEW!

**Endpoint**: `POST /workspace/write_doc`

**Purpose**: Write or update content in Google Docs

**Request Body**:
```json
{
  "document_id": "1abc123...",
  "content": "New content to write...",
  "append": false  // true = append, false = replace all
}
```

**Example - Replace Content**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "1abc123...",
    "content": "This is the new content for the document.",
    "append": false
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/write_doc
```

**Example - Append Content**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_..." \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "1abc123...",
    "content": "\n\nThis text will be appended to the end.",
    "append": true
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/write_doc
```

**Response**:
```json
{
  "success": true,
  "document_id": "1abc123...",
  "title": "Project Plan",
  "action": "replaced",  // or "appended"
  "characters_written": 156
}
```

---

## 🤖 ChatGPT Integration

### What ChatGPT Can Now Do

**Discovery**:
- "List all my Google Docs"
- "Search Drive for files about 'energy'"
- "Show me all PDFs in my Drive"
- "List all spreadsheets I have access to"

**Read**:
- "Read the Project Plan document"
- "Show me data from the HH Profile worksheet"
- "What's in the Battery Analysis spreadsheet?"
- "Read cells A1:E10 from Dashboard sheet"

**Write**:
- "Update cell A1 in Dashboard to 'Updated Value'"
- "Write these values to the Test Sheet"
- "Append this text to my Project Plan document"
- "Replace all content in Meeting Notes with this summary"

**Complex Operations**:
- "Find all sheets with 'battery' in the name, read the Dashboard worksheet from each"
- "Search for documents about 'VLP analysis', read the first one"
- "List all sheets, then read the HH Profile from the GB Energy Dashboard"

---

## 🔐 Security & Permissions

### Current Scopes
```python
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',      # Read/write Sheets
    'https://www.googleapis.com/auth/drive',            # Full Drive access
    'https://www.googleapis.com/auth/documents',        # Read/write Docs (write)
    'https://www.googleapis.com/auth/documents.readonly' # Read-only Docs (read)
]
```

### Service Account
- **Account**: jibber-jabber-knowledge@appspot.gserviceaccount.com
- **Impersonates**: george@upowerenergy.uk
- **Access**: All files accessible to george@upowerenergy.uk

### Railway Environment
- **Variable**: `GOOGLE_WORKSPACE_CREDENTIALS` (base64 encoded)
- **File**: workspace-credentials.json (local, not in repo)
- **Security**: Bearer token authentication required for all endpoints

---

## 📊 Use Cases

### 1. Dynamic Dashboard Updates
```python
# ChatGPT query: "Update the Dashboard with today's metrics"
# Reads from BigQuery → Writes to Sheets
```

### 2. Document Analysis
```python
# ChatGPT query: "Read all docs about 'battery revenue', summarize findings"
# Searches Drive → Reads Docs → Provides summary
```

### 3. Data Synchronization
```python
# ChatGPT query: "Copy HH Profile data from GB Energy to Analysis Sheet"
# Reads from one sheet → Writes to another
```

### 4. Automated Reporting
```python
# ChatGPT query: "Create a new doc with this week's VLP analysis"
# Queries BigQuery → Writes to new Doc
```

---

## 🐛 Troubleshooting

### "Document not found"
**Cause**: Service account doesn't have access to the file  
**Fix**: Share the file with `jibber-jabber-knowledge@appspot.gserviceaccount.com`

### "Permission denied"
**Cause**: Missing scopes or credentials  
**Fix**: Verify `GOOGLE_WORKSPACE_CREDENTIALS` environment variable in Railway

### "Spreadsheet title ambiguous"
**Cause**: Multiple files with same name  
**Fix**: Use `spreadsheet_id` instead of `spreadsheet_title`

---

## 🚀 Deployment Status

**Commit**: e0429dc4  
**Deployed**: November 11, 2025  
**Railway URL**: https://jibber-jabber-production.up.railway.app  
**Status**: ✅ All endpoints operational

---

## 📚 Related Documentation

- `WORKSPACE_RAILWAY_SUCCESS.md` - Initial workspace setup
- `CHATGPT_WORKSPACE_ACTIONS.md` - ChatGPT action schemas  
- `PROJECT_CONFIGURATION.md` - Project configuration
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data architecture

---

**Last Updated**: November 11, 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
