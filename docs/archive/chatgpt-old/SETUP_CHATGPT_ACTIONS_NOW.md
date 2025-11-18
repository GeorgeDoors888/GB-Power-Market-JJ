# 🚀 Setup ChatGPT Actions - Step by Step

**Time**: 10 minutes  
**What You'll Get**: Ask ChatGPT questions and it will query your BigQuery database automatically!

---

## Step 1: Go to ChatGPT Settings

1. Open your browser and go to: **https://chat.openai.com**
2. Click your **profile picture** (bottom left corner)
3. Click **"Settings"**
4. Click **"Personalization"** (left sidebar)
5. Scroll down to the **"Actions"** section
6. Click **"Create new action"**

---

## Step 2: Fill in Basic Info

### Action Name:
```
GB Power Market
```

### Description:
```
Query UK electricity market data from BigQuery. Access system prices, generation data, fuel types, and generator information.
```

---

## Step 3: Copy the Schema

**In the "Schema" box, paste this ENTIRE JSON:**

```json
{
    "openapi": "3.1.0",
    "info": {
        "title": "GB Power Market API",
        "description": "Query BigQuery for UK electricity market data",
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
                        "description": "API is healthy"
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

## Step 4: Set Up Authentication

Scroll down to the **"Authentication"** section:

1. **Authentication Type**: Select **"Bearer"**
2. **Token**: Paste this token:
   ```
   codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   ```

---

## Step 5: Test the Connection

1. Click the **"Test"** button at the bottom
2. You should see: `{"status": "healthy", "version": "1.0.0"}`
3. If you see this, it's working! ✅

---

## Step 6: Save and Enable

1. Click **"Update"** or **"Save"** (top right)
2. Make sure the toggle is **ON** (enabled)
3. Close the settings

---

## Step 7: Try It Out!

Go back to ChatGPT and start a new conversation. Try these questions:

### Test 1: List Tables
```
Can you query my BigQuery database and list all the tables in the uk_energy_prod dataset?
```

**Expected**: ChatGPT will call your API and show you table names like:
- bmrs_mid
- bmrs_bod
- bmrs_indgen_iris
- etc.

### Test 2: Count Rows
```
How many rows are in the bmrs_mid table?
```

**Expected**: ChatGPT will respond: "155,405 rows"

### Test 3: Get Recent Prices
```
What were the electricity prices for the last 5 settlement periods?
```

**Expected**: ChatGPT will show you actual price data with dates and values

---

## Troubleshooting

### "Action failed to execute"

**Check Railway is running:**
```bash
curl https://jibber-jabber-production.up.railway.app/
```

Should return: `{"status":"healthy","version":"1.0.0"}`

### "Unauthorized" error

- Make sure you copied the **entire token** correctly
- Check there are no extra spaces before or after the token
- Token should be: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`

### ChatGPT says "I don't have access to that action"

- Go back to Settings → Personalization → Actions
- Make sure the toggle is **ON** (green/enabled)
- Try refreshing the page

---

## What You Can Ask ChatGPT

Once set up, you can ask questions like:

- **"What tables are in my BigQuery database?"**
- **"Show me the average electricity price for the last 7 days"**
- **"How many generators are in the database?"**
- **"What was the peak price yesterday?"**
- **"Show me wind generation data for the past week"**
- **"Count all rows in bmrs_mid table"**
- **"What's the structure of the bmrs_indgen_iris table?"**

ChatGPT will automatically:
1. Understand your question
2. Convert it to SQL
3. Call your Railway API
4. Get results from BigQuery
5. Analyze and present the data

---

## Quick Reference

**Your Railway URL:**
```
https://jibber-jabber-production.up.railway.app
```

**Your Bearer Token:**
```
codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**BigQuery Project:**
```
inner-cinema-476211-u9
```

**BigQuery Dataset:**
```
uk_energy_prod
```

**Available Tables:**
- `bmrs_mid` - System prices (155,405 rows)
- `bmrs_bod` - Bid-Offer Data
- `bmrs_boalf` - Bid-Offer Acceptance Level Flags
- `bmrs_indgen_iris` - Individual generator data
- `bmrs_fuelinst_iris` - Fuel mix instant data
- `bmrs_b1610` - Actual generation by fuel type

---

## Need Help?

If something isn't working:

1. Check Railway is running: https://jibber-jabber-production.up.railway.app/
2. Verify the bearer token is correct (no spaces)
3. Make sure the action is enabled (toggle ON)
4. Try refreshing ChatGPT

---

**You're all set!** 🎉

Once configured, ChatGPT becomes your natural language interface to BigQuery!
