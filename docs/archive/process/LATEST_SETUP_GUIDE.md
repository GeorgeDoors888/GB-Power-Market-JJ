# 🎯 COMPLETE GUIDE - Custom GPT + Railway Setup

**Last Updated**: 2025-11-09  
**Status**: Most current instructions

---

## 📋 Quick Summary

You have:
- ✅ Railway server running: https://jibber-jabber-production.up.railway.app
- ✅ Bearer token: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- ✅ BigQuery data: 155,405 rows in `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
- ⚠️ Custom GPT needs Actions configured

**Your Custom GPT**: https://chatgpt.com/g/g-690fd99ad3dc8191b47126eb06e2c593-gb-power-market-code-execution-true

---

## 🚀 Step-by-Step Setup (DO THIS NOW)

### Step 1: Open GPT Editor
Click: **https://chatgpt.com/gpts/editor/g-690fd99ad3dc8191b47126eb06e2c593**

### Step 2: Go to Configure Tab
- You'll see: Configure | Create | [Preview]
- Click **"Configure"**

### Step 3: Scroll to Actions Section
Look for **"Actions"** (usually near bottom of page)

**What do you see?**
- If you see "GB Power Market API" → Actions exist (go to Step 6)
- If you see "[Add action]" or empty → Actions need to be added (continue to Step 4)

### Step 4: Add New Action
1. Click **"Create new action"** or **"Add action"**
2. A schema editor will appear

### Step 5: Paste Complete Schema

**Copy this ENTIRE schema** and paste it into the schema editor:

```json
{
    "openapi": "3.1.0",
    "info": {
        "title": "GB Power Market API",
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
                        "description": "Server is running",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "version": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/execute": {
            "post": {
                "summary": "Execute Code",
                "description": "Execute Python or JavaScript code",
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
                                        "description": "The code to execute"
                                    },
                                    "language": {
                                        "type": "string",
                                        "enum": ["python", "javascript"],
                                        "description": "Programming language"
                                    },
                                    "timeout": {
                                        "type": "integer",
                                        "description": "Timeout in seconds",
                                        "default": 30
                                    }
                                },
                                "required": ["code", "language"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Code executed successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "output": {"type": "string"},
                                        "error": {"type": "string"},
                                        "exit_code": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/query_bigquery": {
            "post": {
                "summary": "Query BigQuery",
                "description": "Execute SQL query on BigQuery",
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
                                        "description": "SQL query to execute"
                                    }
                                },
                                "required": ["sql"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Query executed successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {"type": "array"},
                                        "row_count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        },
        "schemas": {}
    },
    "security": [
        {
            "BearerAuth": []
        }
    ]
}
```

### Step 6: Configure Authentication

After pasting schema, look for **"Authentication"** section below the schema editor:

1. **Authentication Type**: Select **"Bearer"**
2. **Token Field**: Paste this exact token:
   ```
   codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   ```

### Step 7: Test the Connection

Click the **"Test"** button next to the action

**Expected results:**
- ✅ Green checkmark = Working!
- ❌ Red X = Check token/URL

### Step 8: Update Instructions

Scroll to the top of the Configure page, find the **"Instructions"** text box, and add this:

```
You are a UK electricity market data analyst with direct access to a Railway server.

CRITICAL RULES:
1. When user asks to execute Python code, ALWAYS use the execute_code action
2. When user asks to query data, ALWAYS use the query_bigquery action  
3. DO NOT use your built-in Python interpreter
4. After executing code, mention the execution time to confirm it ran on Railway

Available Data:
- BigQuery Project: inner-cinema-476211-u9
- Dataset: uk_energy_prod
- Main Table: bmrs_mid (155,405 rows of UK electricity prices)
- Column Names: settlementDate, settlementPeriod, price, volume (camelCase!)

When executing code on Railway:
- Show the output clearly
- Mention execution time
- Confirm it ran on the Railway server

Example query:
SELECT price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` ORDER BY settlementDate DESC LIMIT 10
```

### Step 9: Save Everything

Click **"Update"** or **"Save"** button (top right)

### Step 10: Test in Chat

Go to your Custom GPT: https://chatgpt.com/g/g-690fd99ad3dc8191b47126eb06e2c593-gb-power-market-code-execution-true

Send this EXACT test message:

```
Use the execute_code action to run this Python code:
print("✅ Railway connection successful!")
print("🚀 System operational")
```

**If working correctly, you'll see:**
```
✅ Railway connection successful!
🚀 System operational

Execution time: 0.03s
```

**If NOT working, you'll see:**
- "I can execute that code right here..." → Using local Python (wrong!)
- "I don't have the ability..." → Actions not configured
- Error message → Check authentication/token

---

## ✅ Verification Checklist

After completing all steps, verify:

- [ ] Actions section shows "GB Power Market API"
- [ ] Schema is pasted (no red errors)
- [ ] Authentication shows "Bearer" 
- [ ] Token is: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- [ ] Test button shows green checkmark
- [ ] Instructions mention "execute_code action"
- [ ] Test in chat shows execution time

---

## 🧪 Full Test Suite

Once configured, try these tests in your Custom GPT:

### Test 1: Simple Execution
```
Use the execute_code action:
print("Hello from Railway!")
```
**Expected**: Shows "Hello from Railway!" with execution time

### Test 2: Math Calculation
```
Use the execute_code action:
import statistics
prices = [45.0, 52.3, 48.7, 55.1, 49.8]
print(f"Mean: £{statistics.mean(prices):.2f}")
```
**Expected**: Shows "Mean: £50.18" with execution time

### Test 3: BigQuery Query
```
Use the query_bigquery action to run:
SELECT price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 5
```
**Expected**: Returns 5 prices from BigQuery

### Test 4: Combined Workflow
```
First, use query_bigquery to get 10 recent prices from bmrs_mid table.
Then use execute_code to calculate the average price.
```
**Expected**: ChatGPT calls both actions and shows results

---

## ❌ Troubleshooting

### Problem: "I don't have the ability to send HTTP POST"
**Cause**: Actions not configured  
**Fix**: Complete Steps 4-9 above

### Problem: "I can execute that code right here"
**Cause**: ChatGPT using local Python instead of Railway  
**Fix**: Update Instructions (Step 8) and be explicit: "Use the execute_code action"

### Problem: Authentication Error
**Cause**: Wrong or missing bearer token  
**Fix**: Check Step 6, token should be `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

### Problem: 404 or Connection Error
**Cause**: Railway server down or wrong URL  
**Fix**: Test Railway manually:
```bash
curl https://jibber-jabber-production.up.railway.app/
```
Should return: `{"status":"running","version":"1.0.0"}`

### Problem: Test Button Shows Red X
**Cause**: Schema error or auth issue  
**Fix**: 
1. Check for red error messages in schema editor
2. Verify bearer token is set correctly
3. Make sure URL is: `https://jibber-jabber-production.up.railway.app`

---

## 📊 What You Can Do After Setup

Once working, you can ask your Custom GPT:

**Data Analysis:**
```
Get the last 100 prices from bmrs_mid and calculate:
- Mean
- Median
- Standard deviation
- Volatility
```

**Time Patterns:**
```
Query BigQuery to show average price by settlement period.
Which hours have the highest prices?
```

**Forecasting:**
```
Get 500 recent prices and run an ARIMA forecast for the next 10 periods
```

**Peak vs Off-Peak:**
```
Compare average prices during peak hours (16-40) vs off-peak.
Calculate the spread.
```

---

## 🔗 Quick Reference

**Railway Server**: https://jibber-jabber-production.up.railway.app  
**Bearer Token**: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`  
**Custom GPT (Edit)**: https://chatgpt.com/gpts/editor/g-690fd99ad3dc8191b47126eb06e2c593  
**Custom GPT (Use)**: https://chatgpt.com/g/g-690fd99ad3dc8191b47126eb06e2c593-gb-power-market-code-execution-true

**BigQuery Details:**
- Project: `inner-cinema-476211-u9`
- Dataset: `uk_energy_prod`
- Main Table: `bmrs_mid` (155,405 rows)
- Columns: `settlementDate`, `settlementPeriod`, `price`, `volume`

---

## 📞 Need Help?

**If you get stuck:**
1. Note which step you're on (1-10)
2. Copy any error messages you see
3. Describe what happens when you test
4. Share a screenshot of the Actions section

**Common questions:**
- "Where is the Actions section?" → Configure tab, scroll to bottom
- "Where do I paste the schema?" → In the schema editor box after clicking "Add action"
- "Where does the token go?" → In Authentication section below the schema
- "Why isn't it working?" → Check if you're using the Custom GPT link, not regular ChatGPT

---

**🎊 Once this is working, you'll have a fully functional AI data analyst for UK electricity markets!**

**Last verified**: 2025-11-09  
**All systems operational**: Railway ✅ | BigQuery ✅ | Schema ✅
