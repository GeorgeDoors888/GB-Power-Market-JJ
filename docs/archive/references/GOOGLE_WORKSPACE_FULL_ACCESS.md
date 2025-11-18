# Google Workspace Full Access API - Complete Reference

**Date**: November 11, 2025  
**Status**: 🟢 Production Ready  
**Base URL**: https://jibber-jabber-production.up.railway.app

---

## 🎯 Overview

Complete API for accessing Google Workspace (Sheets, Docs, Drive) with full read/write capabilities. Your ChatGPT can now:

- ✅ **List all accessible spreadsheets** (not just GB Energy Dashboard)
- ✅ **Read/Write Google Sheets** (any spreadsheet by ID or name)
- ✅ **Read/Write Google Docs** (full document access)
- ✅ **Browse Google Drive** (list, search, filter files)
- ✅ **Dynamic discovery** (no hardcoded file IDs)

---

## 🔐 Authentication

All endpoints require Bearer token authentication:

```bash
Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

---

## 📊 Endpoint Summary

| Endpoint | Method | Purpose | Read/Write |
|----------|--------|---------|------------|
| `/workspace/health` | GET | Health check + list spreadsheets | Read |
| `/workspace/list_spreadsheets` | GET | List ALL accessible spreadsheets | Read |
| `/workspace/get_spreadsheet` | POST | Get spreadsheet info by ID/name | Read |
| `/workspace/read_sheet` | POST | Read data from any worksheet | Read |
| `/workspace/write_sheet` | POST | Write data to worksheet | **Write** |
| `/workspace/list_drive_files` | GET | Browse Google Drive files | Read |
| `/workspace/search_drive` | POST | Search Drive with filters | Read |
| `/workspace/read_doc` | POST | Read Google Doc content | Read |
| `/workspace/write_doc` | POST | Write/update Google Doc | **Write** |

---

## 📖 API Reference

### 1. Health Check

**Endpoint**: `GET /workspace/health`

**Purpose**: Verify workspace access and list accessible spreadsheets

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
      "id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
      "url": "https://docs.google.com/spreadsheets/d/..."
    }
  ]
}
```

---

### 2. List All Spreadsheets

**Endpoint**: `GET /workspace/list_spreadsheets`

**Purpose**: Get complete inventory of all accessible Google Sheets

**Example**:
```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
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
      "id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
      "url": "https://docs.google.com/spreadsheets/d/...",
      "worksheets": 29
    },
    {
      "title": "Project Budget 2025",
      "id": "1AbC...XyZ",
      "url": "https://docs.google.com/spreadsheets/d/...",
      "worksheets": 5
    }
  ]
}
```

---

### 3. Get Spreadsheet Info

**Endpoint**: `POST /workspace/get_spreadsheet`

**Purpose**: Get detailed information about a specific spreadsheet

**Parameters**:
- `spreadsheet_id` (string, optional): Spreadsheet ID
- `spreadsheet_title` (string, optional): Spreadsheet title

**Example by ID**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"}' \
  https://jibber-jabber-production.up.railway.app/workspace/get_spreadsheet
```

**Example by Title**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_title": "GB Energy Dashboard"}' \
  https://jibber-jabber-production.up.railway.app/workspace/get_spreadsheet
```

**Response**:
```json
{
  "success": true,
  "title": "GB Energy Dashboard",
  "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
  "url": "https://docs.google.com/spreadsheets/d/...",
  "worksheets": [
    {
      "id": 0,
      "title": "Dashboard",
      "rows": 838,
      "cols": 27
    },
    {
      "id": 1275276105,
      "title": "HH Profile",
      "rows": 17321,
      "cols": 26
    }
  ],
  "total_worksheets": 29
}
```

---

### 4. Read Worksheet Data

**Endpoint**: `POST /workspace/read_sheet`

**Purpose**: Read data from any worksheet in any accessible spreadsheet

**Parameters**:
- `spreadsheet_id` (string, optional): Spreadsheet ID (default: GB Energy Dashboard)
- `spreadsheet_title` (string, optional): Spreadsheet title
- `worksheet_name` (string, required): Worksheet name
- `cell_range` (string, optional): A1 notation range (e.g., "A1:E10")

**Example - Specific Range**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
    "worksheet_name": "Dashboard",
    "cell_range": "A1:E10"
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet
```

**Example - Full Worksheet**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_title": "Project Budget 2025",
    "worksheet_name": "Q4 Summary"
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet
```

**Response**:
```json
{
  "success": true,
  "spreadsheet_title": "GB Energy Dashboard",
  "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
  "worksheet_name": "Dashboard",
  "rows": 44,
  "cols": 8,
  "data": [
    ["File: Dashboard", "", "", ""],
    ["Total Records: 18", "", "", ""],
    ["GSPs Analyzed: 18", "", "", ""]
  ]
}
```

---

### 5. Write Worksheet Data ✍️

**Endpoint**: `POST /workspace/write_sheet`

**Purpose**: Write data to any worksheet (creates worksheet if doesn't exist)

**Parameters**:
- `spreadsheet_id` (string, optional): Spreadsheet ID (default: GB Energy Dashboard)
- `spreadsheet_title` (string, optional): Spreadsheet title
- `worksheet_name` (string, required): Worksheet name
- `cell_range` (string, required): A1 notation range (e.g., "A1:C3")
- `values` (array, required): 2D array of values to write

**Example - Write to Existing Sheet**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
    "worksheet_name": "Test Data",
    "cell_range": "A1:C3",
    "values": [
      ["Name", "Value", "Date"],
      ["Price", 100.5, "2025-11-11"],
      ["Volume", 250, "2025-11-11"]
    ]
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/write_sheet
```

**Response**:
```json
{
  "success": true,
  "spreadsheet_title": "GB Energy Dashboard",
  "spreadsheet_id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
  "worksheet_name": "Test Data",
  "cell_range": "A1:C3",
  "cells_updated": 9
}
```

---

### 6. List Drive Files

**Endpoint**: `GET /workspace/list_drive_files`

**Purpose**: Browse Google Drive files with filtering

**Query Parameters**:
- `file_type` (string, optional): Filter by MIME type (e.g., "spreadsheet", "document", "folder")
- `max_results` (int, optional): Max files to return (default: 100)

**Example - All Files**:
```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  "https://jibber-jabber-production.up.railway.app/workspace/list_drive_files"
```

**Example - Only Spreadsheets**:
```bash
curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  "https://jibber-jabber-production.up.railway.app/workspace/list_drive_files?file_type=spreadsheet"
```

**Response**:
```json
{
  "success": true,
  "total_files": 47,
  "files": [
    {
      "id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
      "name": "GB Energy Dashboard",
      "mimeType": "application/vnd.google-apps.spreadsheet",
      "url": "https://docs.google.com/spreadsheets/d/...",
      "modifiedTime": "2025-11-10T15:30:00Z",
      "size": "2.5 MB"
    },
    {
      "id": "1AbC...XyZ",
      "name": "Project Notes.docx",
      "mimeType": "application/vnd.google-apps.document",
      "url": "https://docs.google.com/document/d/...",
      "modifiedTime": "2025-11-09T10:20:00Z",
      "size": "45 KB"
    }
  ]
}
```

---

### 7. Search Drive

**Endpoint**: `POST /workspace/search_drive`

**Purpose**: Search Google Drive files by query

**Parameters**:
- `query` (string, required): Search query (searches file names and content)
- `file_type` (string, optional): Filter by type
- `max_results` (int, optional): Max results (default: 50)

**Example - Search for "energy"**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "energy",
    "file_type": "spreadsheet",
    "max_results": 10
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/search_drive
```

**Response**:
```json
{
  "success": true,
  "query": "energy",
  "total_results": 3,
  "files": [
    {
      "id": "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8",
      "name": "GB Energy Dashboard",
      "mimeType": "application/vnd.google-apps.spreadsheet",
      "url": "https://docs.google.com/spreadsheets/d/..."
    }
  ]
}
```

---

### 8. Read Google Doc

**Endpoint**: `POST /workspace/read_doc`

**Purpose**: Read full content from a Google Doc

**Parameters**:
- `document_id` (string, optional): Document ID
- `document_title` (string, optional): Document title

**Example by ID**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "1AbC...XyZ"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_doc
```

**Example by Title**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"document_title": "Project Notes"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_doc
```

**Response**:
```json
{
  "success": true,
  "document_title": "Project Notes",
  "document_id": "1AbC...XyZ",
  "url": "https://docs.google.com/document/d/...",
  "content": "Full text content of the document...",
  "word_count": 1247,
  "last_modified": "2025-11-10T15:30:00Z"
}
```

---

### 9. Write Google Doc ✍️

**Endpoint**: `POST /workspace/write_doc`

**Purpose**: Write/update content in a Google Doc

**Parameters**:
- `document_id` (string, optional): Document ID
- `document_title` (string, optional): Document title
- `content` (string, required): Text content to write
- `mode` (string, optional): "append" or "replace" (default: "replace")

**Example - Replace Content**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "1AbC...XyZ",
    "content": "# New Content\n\nThis replaces the entire document.",
    "mode": "replace"
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/write_doc
```

**Example - Append Content**:
```bash
curl -X POST \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{
    "document_title": "Project Notes",
    "content": "\n\n## New Section\nThis is appended to the end.",
    "mode": "append"
  }' \
  https://jibber-jabber-production.up.railway.app/workspace/write_doc
```

**Response**:
```json
{
  "success": true,
  "document_title": "Project Notes",
  "document_id": "1AbC...XyZ",
  "url": "https://docs.google.com/document/d/...",
  "operation": "replace",
  "characters_written": 156
}
```

---

## 🔒 Permissions & Scopes

The service account has these Google Workspace scopes:

```python
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',  # Read/write Sheets
    'https://www.googleapis.com/auth/drive',          # Full Drive access
    'https://www.googleapis.com/auth/documents'       # Read/write Docs
]
```

**Delegation**: Service account impersonates `george@upowerenergy.uk`

---

## 🎯 Use Cases

### 1. Dynamic Spreadsheet Access
```python
# ChatGPT can discover and read ANY spreadsheet
"List all my spreadsheets"
"Read the Budget 2025 spreadsheet, Q4 worksheet"
```

### 2. Automated Data Entry
```python
# Write data to sheets programmatically
"Write these values to cell A1:C3 in Test Data worksheet:
Name, Value, Date
Price, 100, Today
Volume, 250, Today"
```

### 3. Document Management
```python
# Read and write Google Docs
"Read the Project Notes document"
"Append this summary to the Meeting Notes document"
```

### 4. Drive Search & Discovery
```python
# Find files across Drive
"Search my Drive for files containing 'energy data'"
"List all spreadsheets modified this week"
```

---

## 📊 Comparison: Old vs New

### Before (Hardcoded)
```python
# Only worked with GB Energy Dashboard
sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
# Read only
# Limited to 3 endpoints
```

### After (Dynamic)
```python
# Works with ANY accessible spreadsheet/doc
spreadsheets = gc.openall()  # Discover all
sheet = gc.open(title)  # Open by name
# Full read/write
# 9 comprehensive endpoints
```

---

## 🧪 Testing All Endpoints

```bash
# 1. Health check
curl -H "Authorization: Bearer TOKEN" \
  https://jibber-jabber-production.up.railway.app/workspace/health

# 2. List spreadsheets
curl -H "Authorization: Bearer TOKEN" \
  https://jibber-jabber-production.up.railway.app/workspace/list_spreadsheets

# 3. Get spreadsheet info
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"spreadsheet_title": "GB Energy Dashboard"}' \
  https://jibber-jabber-production.up.railway.app/workspace/get_spreadsheet

# 4. Read sheet
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"worksheet_name": "Dashboard", "cell_range": "A1:E5"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_sheet

# 5. Write sheet
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"worksheet_name": "Test", "cell_range": "A1", "values": [["Hello"]]}' \
  https://jibber-jabber-production.up.railway.app/workspace/write_sheet

# 6. List Drive files
curl -H "Authorization: Bearer TOKEN" \
  "https://jibber-jabber-production.up.railway.app/workspace/list_drive_files?file_type=spreadsheet"

# 7. Search Drive
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"query": "energy"}' \
  https://jibber-jabber-production.up.railway.app/workspace/search_drive

# 8. Read doc
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"document_title": "Project Notes"}' \
  https://jibber-jabber-production.up.railway.app/workspace/read_doc

# 9. Write doc
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"document_title": "Test Doc", "content": "Hello World", "mode": "append"}' \
  https://jibber-jabber-production.up.railway.app/workspace/write_doc
```

---

## 🚨 Error Handling

### Common Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| 401 | Missing/invalid token | Check Authorization header |
| 403 | Permission denied | Verify service account has access |
| 404 | File not found | Check spreadsheet ID/title |
| 500 | Server error | Check Railway logs |
| 503 | Credentials missing | Verify GOOGLE_WORKSPACE_CREDENTIALS env var |

---

## 📚 Related Documentation

- `WORKSPACE_RAILWAY_SUCCESS.md` - Initial 3-endpoint setup
- `CHATGPT_WORKSPACE_ACTIONS.md` - ChatGPT integration guide
- `PROJECT_CONFIGURATION.md` - All configuration settings
- `codex-server/codex_server_secure.py` - Full API implementation

---

## 🎉 Summary

You now have **complete Google Workspace access** via API:

✅ **9 endpoints** (6 new + 3 original)  
✅ **Read + Write** capabilities  
✅ **Dynamic discovery** (no hardcoding)  
✅ **Sheets + Docs + Drive** fully accessible  
✅ **Production ready** on Railway  

**Your ChatGPT is now a full Workspace automation assistant!** 🚀

---

**Last Updated**: November 11, 2025  
**Status**: 🟢 Production  
**Railway URL**: https://jibber-jabber-production.up.railway.app  
**Maintainer**: George Major (george@upowerenergy.uk)
