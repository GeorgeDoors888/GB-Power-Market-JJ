# 🚀 ChatGPT Actions Setup - Complete Guide
**Server Status**: ✅ LIVE (Verified 2025-11-08)  
**Capabilities**: Code Execution + BigQuery Access

---

## What You're Setting Up

ChatGPT will be able to:
- ✅ Execute Python/JavaScript code on your Railway server
- ✅ Query BigQuery with SQL
- ✅ Run complex data analysis
- ✅ Access 155,405+ rows of UK electricity data

---

## Step 1: Open ChatGPT Settings

1. Go to: **https://chat.openai.com**
2. Click your **profile icon** (bottom left)
3. Select **"Settings"**
4. Click **"Personalization"** (left menu)
5. Scroll to **"Actions"** section
6. Click **"+ Create new action"**

---

## Step 2: Basic Information

**Name:**
```
GB Power Market - Code Execution
```

**Description:**
```
Execute Python code and query BigQuery for UK electricity market data. Access system prices, generation data, fuel types, and run custom analysis scripts.
```

---

## Step 3: Copy This Complete Schema

**Paste this ENTIRE JSON in the "Schema" field:**

```json
{
    "openapi": "3.1.0",
    "info": {
        "title": "GB Power Market Code Execution API",
        "description": "Execute Python/JavaScript code and query BigQuery",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "https://jibber-jabber-production.up.railway.app"
        }
    ],
    "paths": {
        "/": {
            "get": {
                "summary": "Health Check",
                "operationId": "health_check",
                "responses": {
                    "200": {
                        "description": "Server is running"
                    }
                }
            }
        },
        "/execute": {
            "post": {
                "summary": "Execute Code",
                "description": "Execute Python or JavaScript code in sandboxed environment",
                "operationId": "execute_code",
                "requestBody": {
                    "required": true,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "code": {
                                        "type": "string",
                                        "description": "Code to execute"
                                    },
                                    "language": {
                                        "type": "string",
                                        "enum": ["python", "javascript"],
                                        "default": "python"
                                    },
                                    "timeout": {
                                        "type": "integer",
                                        "default": 30
                                    }
                                },
                                "required": ["code"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Execution results"
                    }
                },
                "security": [
                    {
                        "BearerAuth": []
                    }
                ]
            }
        },
        "/query_bigquery": {
            "post": {
                "summary": "Query BigQuery",
                "description": "Execute SQL query on BigQuery via Python",
                "operationId": "query_bigquery",
                "requestBody": {
                    "required": true,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "sql": {
                                        "type": "string",
                                        "description": "SQL query to execute on BigQuery"
                                    },
                                    "timeout": {
                                        "type": "integer",
                                        "default": 60
                                    },
                                    "max_results": {
                                        "type": "integer",
                                        "default": 1000
                                    }
                                },
                                "required": ["sql"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Query results"
                    }
                },
                "security": [
                    {
                        "BearerAuth": []
                    }
                ]
            }
        }
    },
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        }
    }
}
```

---

## Step 4: Configure Authentication

In the **"Authentication"** section:

**Authentication Type:** Select **"Bearer"**

**Token:** Paste this exact token:
```
codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

⚠️ **Important**: Copy the token exactly - no spaces before or after!

---

## Step 5: Test the Connection

1. Click **"Test"** button (bottom of the page)
2. You should see:
   ```json
   {
       "status": "running",
       "version": "1.0.0",
       "languages": ["python", "javascript"],
       "timestamp": "..."
   }
   ```
3. If you see this → **SUCCESS!** ✅

---

## Step 6: Save & Enable

1. Click **"Save"** or **"Update"** (top right corner)
2. Make sure the toggle switch is **ON** (enabled)
3. Close the settings panel

---

## Step 7: Test It Out!

Go to ChatGPT and try these commands:

### Test 1: Health Check
```
Check if my Railway server is running
```
**Expected**: ChatGPT confirms server is healthy

### Test 2: Execute Python Code
```
Can you execute this Python code on my server:
print([x**2 for x in range(10)])
```
**Expected**: `[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]`

### Test 3: Query BigQuery
```
Query my BigQuery database and count how many rows are in the bmrs_mid table
```
**Expected**: "There are 155,405 rows in the bmrs_mid table"

### Test 4: Complex Query
```
What were the electricity prices for the last 5 settlement periods? Query from BigQuery.
```
**Expected**: ChatGPT shows actual price data with dates

### Test 5: List Tables
```
List all tables in my uk_energy_prod dataset in BigQuery
```
**Expected**: List of tables like bmrs_mid, bmrs_bod, bmrs_indgen_iris, etc.

---

## What You Can Now Ask ChatGPT

### Data Queries:
- "How many generators are in the database?"
- "What was the average price yesterday?"
- "Show me wind generation for the past week"
- "Count all rows in each table"

### Code Execution:
- "Run this Python code: [your code]"
- "Calculate the average of these numbers using Python"
- "Execute this data transformation script"

### Analysis:
- "Analyze price trends for the last month"
- "Compare wind vs solar generation"
- "Find peak demand periods"
- "Calculate price volatility"

---

## Architecture - How It Works

```
You → ChatGPT → Railway Server → Python Execution → BigQuery → Results → ChatGPT → You
```

**Behind the scenes:**
1. You ask ChatGPT a question
2. ChatGPT decides to call `/query_bigquery` or `/execute`
3. Railway server creates a Python script
4. Python script queries BigQuery or processes data
5. Results return to ChatGPT
6. ChatGPT analyzes and presents insights

---

## Troubleshooting

### "Action failed to execute"

**Check server is running:**
```bash
curl https://jibber-jabber-production.up.railway.app/
```
Should return JSON with `"status": "running"`

### "Unauthorized" Error

- Verify bearer token is exactly: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- No extra spaces before/after token
- Authentication type must be "Bearer"

### "ChatGPT doesn't use the action"

- Go to Settings → Personalization → Actions
- Confirm toggle is **ON** (enabled)
- Try saying "Use my GB Power Market action to..."

### Query Returns Error

- BigQuery project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`
- Full table names: `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`

---

## Quick Reference Card

**Railway URL:**
```
https://jibber-jabber-production.up.railway.app
```

**Bearer Token:**
```
codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**BigQuery Project:**
```
inner-cinema-476211-u9
```

**Dataset:**
```
uk_energy_prod
```

**Main Tables:**
- `bmrs_mid` - System prices (155,405 rows)
- `bmrs_bod` - Bid-Offer Data
- `bmrs_indgen_iris` - Generator data
- `bmrs_fuelinst_iris` - Fuel mix data

**Endpoints:**
- `GET /` - Health check
- `POST /execute` - Run Python/JavaScript code
- `POST /query_bigquery` - SQL queries on BigQuery

---

## Security Notes

✅ **Protected:**
- Bearer token authentication required
- Code runs in sandboxed subprocess
- 30-60 second execution timeout
- Forbidden patterns blocked (os, sys, subprocess imports)

✅ **Safe to use:**
- Read-only BigQuery access
- Temporary file execution only
- No persistent state between executions

---

## Success Checklist

- [ ] Created ChatGPT Action
- [ ] Pasted complete JSON schema
- [ ] Added bearer token authentication
- [ ] Tested connection (saw "running" status)
- [ ] Saved and enabled action
- [ ] Tested Python code execution
- [ ] Tested BigQuery query
- [ ] Asked complex analysis question

---

## You're All Set! 🎉

ChatGPT can now:
- ✅ Execute Python code on your Railway server
- ✅ Query BigQuery for UK electricity data
- ✅ Run complex data analysis
- ✅ Process and transform data
- ✅ Generate insights automatically

**Start asking questions and watch ChatGPT query your database!**

---

**Last Verified**: 2025-11-08 18:42:10  
**Server Status**: ✅ Running  
**Version**: 1.0.0  
**Languages**: Python, JavaScript
