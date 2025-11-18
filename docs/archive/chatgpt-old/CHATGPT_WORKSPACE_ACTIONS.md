# ChatGPT Workspace Actions - Quick Setup Guide

## 🎯 Purpose
Add Google Workspace access to your ChatGPT Custom GPT to read GB Energy Dashboard data.

---

## 📋 Quick Setup Steps

### 1. Open ChatGPT Custom GPT Editor
- Go to: https://chat.openai.com/gpts/mine
- Find: "Jibber Jabber Knowledge" GPT
- Click: **Edit**

### 2. Add Actions (Create 3 New Actions)

Click **"+ Add Action"** for each endpoint below:

---

## 🔌 Action 1: Check Workspace Health

**Purpose**: Verify workspace access and dashboard connection

**Configuration**:
```yaml
Action Name: workspace_health
Method: GET
URL: https://jibber-jabber-production.up.railway.app/workspace/health
Authentication: API Key
Auth Type: Bearer Token
API Key: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**OpenAPI Schema**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Workspace Health Check",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://jibber-jabber-production.up.railway.app"
    }
  ],
  "paths": {
    "/workspace/health": {
      "get": {
        "operationId": "checkWorkspaceHealth",
        "summary": "Check if Google Workspace access is working",
        "responses": {
          "200": {
            "description": "Workspace health status",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": { "type": "string" },
                    "message": { "type": "string" },
                    "services": {
                      "type": "object",
                      "properties": {
                        "sheets": { "type": "string" },
                        "drive": { "type": "string" }
                      }
                    },
                    "dashboard": {
                      "type": "object",
                      "properties": {
                        "title": { "type": "string" },
                        "worksheets": { "type": "integer" }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 🔌 Action 2: Get Dashboard Info

**Purpose**: List all worksheets in the GB Energy Dashboard

**Configuration**:
```yaml
Action Name: workspace_dashboard
Method: GET
URL: https://jibber-jabber-production.up.railway.app/workspace/dashboard
Authentication: API Key
Auth Type: Bearer Token
API Key: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**OpenAPI Schema**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Workspace Dashboard Info",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://jibber-jabber-production.up.railway.app"
    }
  ],
  "paths": {
    "/workspace/dashboard": {
      "get": {
        "operationId": "getDashboardInfo",
        "summary": "Get list of all worksheets in the GB Energy Dashboard",
        "responses": {
          "200": {
            "description": "Dashboard structure and worksheet list",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "success": { "type": "boolean" },
                    "dashboard_id": { "type": "string" },
                    "title": { "type": "string" },
                    "worksheets": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "id": { "type": "integer" },
                          "title": { "type": "string" },
                          "rows": { "type": "integer" },
                          "cols": { "type": "integer" }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 🔌 Action 3: Read Worksheet Data

**Purpose**: Read data from any worksheet in the dashboard

**Configuration**:
```yaml
Action Name: workspace_read_sheet
Method: POST
URL: https://jibber-jabber-production.up.railway.app/workspace/read_sheet
Authentication: API Key
Auth Type: Bearer Token
API Key: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
Content-Type: application/json
```

**OpenAPI Schema**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Workspace Read Sheet",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://jibber-jabber-production.up.railway.app"
    }
  ],
  "paths": {
    "/workspace/read_sheet": {
      "post": {
        "operationId": "readWorksheetData",
        "summary": "Read data from a specific worksheet in the GB Energy Dashboard",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["worksheet_name"],
                "properties": {
                  "worksheet_name": {
                    "type": "string",
                    "description": "Name of the worksheet to read (e.g., 'Dashboard', 'HH Profile')"
                  },
                  "cell_range": {
                    "type": "string",
                    "description": "Optional A1 notation range (e.g., 'A1:E10'). If not specified, returns up to 100 rows."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Worksheet data",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "success": { "type": "boolean" },
                    "worksheet_name": { "type": "string" },
                    "rows": { "type": "integer" },
                    "data": {
                      "type": "array",
                      "items": {
                        "type": "array",
                        "items": { "type": "string" }
                      }
                    },
                    "headers": {
                      "type": "array",
                      "items": { "type": "string" }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 3. Update Instructions

Add this to your ChatGPT instructions:

```
## Google Workspace Access

You can access the GB Energy Dashboard via these actions:

1. **workspace_health** - Check if workspace access is working
2. **workspace_dashboard** - Get list of all 29 worksheets
3. **workspace_read_sheet** - Read data from any worksheet

### Available Worksheets:
- Dashboard (main overview)
- HH Profile (half-hourly data)
- Live_Raw_IC (real-time interconnector data)
- Calculations BHM (battery hour-by-hour metrics)
- Plus 25 more worksheets

### Example Queries You Can Answer:
- "Show me the dashboard structure"
- "Read the Dashboard worksheet"
- "Get data from HH Profile for the last week"
- "What worksheets are available?"
```

---

## 4. Test Your Setup

After adding actions, test with these queries:

### Test 1: Health Check
**Query**: "Check if workspace access is working"

**Expected**: ChatGPT calls `workspace_health` and reports:
- ✅ Sheets API working
- ✅ Drive API working
- ✅ Dashboard accessible with 29 worksheets

### Test 2: List Worksheets
**Query**: "List all worksheets in my energy dashboard"

**Expected**: ChatGPT calls `workspace_dashboard` and shows:
- Dashboard (838 rows)
- HH Profile (17,321 rows)
- Live_Raw_IC (1,000 rows)
- ... all 29 worksheets

### Test 3: Read Data
**Query**: "Read the first 10 rows of the Dashboard worksheet"

**Expected**: ChatGPT calls `workspace_read_sheet` with:
```json
{
  "worksheet_name": "Dashboard",
  "cell_range": "A1:Z10"
}
```
And displays the data in a formatted table.

---

## 🐛 Troubleshooting

### Error: "Authentication failed"
**Fix**: Verify Bearer token in Action settings matches:
```
codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

### Error: "Action not available"
**Fix**: Save the GPT after adding actions, then refresh ChatGPT

### Error: "Worksheet not found"
**Fix**: Get exact worksheet names first:
1. Ask: "List all worksheets"
2. Use exact name (case-sensitive)

---

## 📊 Example Queries

Once setup is complete, try these:

```
1. "Check workspace health"
   → Verifies connection

2. "Show me all worksheets in the GB Energy Dashboard"
   → Lists 29 worksheets with sizes

3. "Read the Dashboard worksheet, first 20 rows"
   → Returns actual data

4. "Get data from HH Profile worksheet for cells A1:E100"
   → Returns specific range

5. "What's in the Live_Raw_IC worksheet?"
   → Reads real-time interconnector data
```

---

## 🎯 Benefits

With these actions, ChatGPT can now:

✅ **Read Dashboard Data** - Access live energy metrics  
✅ **Query Historical Data** - Browse HH Profile, CVA tracking  
✅ **Check Real-Time Data** - View Live_Raw_IC updates  
✅ **Navigate Worksheets** - Explore all 29 worksheets  
✅ **Analyze Trends** - Combine with BigQuery data  

---

## 🔐 Security

- ✅ Bearer token authentication required
- ✅ Read-only access (no write operations)
- ✅ Service account with limited scopes
- ✅ HTTPS encryption enforced
- ✅ Railway environment variable protection

---

## 📚 Related Docs

- `WORKSPACE_RAILWAY_SUCCESS.md` - Full technical details
- `CHATGPT_INSTRUCTIONS.md` - Complete GPT instructions
- `PROJECT_CONFIGURATION.md` - Project settings

---

**Status**: ✅ Ready for Production  
**Last Updated**: November 11, 2025  
**Railway URL**: https://jibber-jabber-production.up.railway.app  
**Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
