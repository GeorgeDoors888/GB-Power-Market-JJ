# 🔧 FIX YOUR CUSTOM GPT - Step by Step

## 🔴 Problem Identified:

Your Custom GPT is saying "I don't have the ability to send a real HTTP POST" which means:
**The Actions are NOT properly connected or configured!**

---

## ✅ Step-by-Step Fix:

### Step 1: Verify Custom GPT URL
Go to: **https://chatgpt.com/gpts/editor/g-690f95eceb788191a021dc00389f41ee**

You should see:
- Configure tab
- Create tab
- Preview chat on the right

### Step 2: Click "Configure" Tab

Look for the **"Actions"** section (usually near the bottom)

### Step 3: Check if Actions Exist

**If you see NO actions** or an empty Actions section:
1. Click **"Create new action"**
2. Go to Step 4

**If you see an existing action:**
1. Click on it to expand
2. Check if the schema is there
3. Go to Step 4

### Step 4: Import the Schema

**Copy this entire schema** (from `chatgpt-schema-fixed.json`):

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
                                        "status": {
                                            "type": "string"
                                        },
                                        "version": {
                                            "type": "string"
                                        }
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
                                        "output": {
                                            "type": "string"
                                        },
                                        "error": {
                                            "type": "string"
                                        },
                                        "exit_code": {
                                            "type": "integer"
                                        }
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
                                        "success": {
                                            "type": "boolean"
                                        },
                                        "data": {
                                            "type": "array"
                                        },
                                        "row_count": {
                                            "type": "integer"
                                        }
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

**Paste this into the Schema box** in your Custom GPT Actions editor.

### Step 5: Configure Authentication

After pasting the schema:
1. Look for **"Authentication"** dropdown
2. Select **"API Key"** or **"Bearer"**
3. Select **"Bearer"** from Auth Type
4. In the token field, paste:
   ```
   codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   ```

### Step 6: Test the Action

Click **"Test"** button next to the action

You should see:
- ✅ Green checkmark if successful
- ❌ Red X if failed (check token/URL)

### Step 7: Add Custom Instructions

In the **"Instructions"** box at the top, add:

```
You are a UK electricity market data analyst with direct access to a Railway server that executes Python code and queries BigQuery.

CRITICAL: When a user asks you to execute Python code or query data:
1. ALWAYS use the execute_code or query_bigquery actions
2. DO NOT use your built-in Python interpreter
3. After execution, show the execution time to prove it ran on Railway

Available data:
- BigQuery project: inner-cinema-476211-u9
- Dataset: uk_energy_prod
- Main table: bmrs_mid (155,405 rows)
- Column names are camelCase: settlementDate, settlementPeriod, price, volume
```

### Step 8: Save and Update

Click **"Update"** or **"Save"** button at the top right

### Step 9: Test in Preview

In the preview chat (right side), try:

```
Use the execute_code action to run this Python:
print("✅ Railway is working!")
```

**Expected response:**
ChatGPT should call the action and show: "✅ Railway is working!"

---

## 🔍 Verification Checklist:

After following all steps, verify:

- [ ] Actions section shows "GB Power Market API"
- [ ] Schema is pasted and valid (no red errors)
- [ ] Authentication shows "Bearer" with token
- [ ] Test button shows green checkmark
- [ ] Instructions mention "use execute_code action"
- [ ] Preview chat can call the action successfully

---

## ❌ If It Still Doesn't Work:

**Check these common issues:**

1. **Wrong GPT URL**: Make sure you're editing the RIGHT Custom GPT
   - URL should be: `https://chatgpt.com/gpts/editor/g-690f95eceb788191a021dc00389f41ee`

2. **Authentication not set**: Bearer token MUST be configured

3. **Schema validation errors**: Look for red error messages in schema editor

4. **Railway server down**: Verify Railway is running:
   ```bash
   curl https://jibber-jabber-production.up.railway.app/
   ```

5. **Not using Custom GPT**: Regular ChatGPT WON'T work - must use your custom GPT link

---

## ✅ Success Test:

Once configured correctly, this prompt should work:

```
Use the execute_code action to run this Python code:
import statistics
prices = [103.3, 105.0, 102.99, 98.5, 110.2]
print(f"Mean: £{statistics.mean(prices):.2f}")
print("✅ Executed on Railway!")
```

**You should see:**
```
Mean: £103.89
✅ Executed on Railway!
Execution time: 0.03s
```

---

## 📞 Next Steps:

After following this guide:
1. Tell me which step you're stuck on
2. Or confirm it's now working!
3. Share a screenshot if you see any errors

Let's get this working! 🚀
