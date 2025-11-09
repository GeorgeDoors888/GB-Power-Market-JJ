# 🤖 ChatGPT Actions Setup for Railway Backend

**Time Required**: 5-10 minutes  
**Status**: Railway backend verified working ✅

---

## What This Does

Connects ChatGPT to your **Railway backend** so you can ask natural language questions and ChatGPT will query BigQuery directly.

### Example Questions You Can Ask:

- "What tables are in my uk_energy_prod dataset?"
- "Show me the last 10 system prices from bmrs_mid"
- "How many generators are in the database?"
- "What was the average electricity price yesterday?"
- "Show me wind generation data for the past week"

---

## Setup Steps

### 1. Go to ChatGPT

1. Visit: https://chatgpt.com/
2. Click your **profile** (bottom left)
3. Click **"Settings"** → **"Personalization"**
4. Scroll to **"Actions"** section
5. Click **"Create new action"**

### 2. Configure the Action

**Name**: 
```
GB Power Market Railway API
```

**Description**:
```
Query UK electricity market data from BigQuery via Railway backend. Access system prices, generation mix, fuel types, interconnectors, and generator data.
```

**Schema**: 
Copy and paste the **entire contents** of `chatgpt-action-schema-railway.json`

### 3. Set Up Authentication

**Auth Type**: `API Key`

**Authentication Method**: `Bearer`

**API Key**: 
```
codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

**Header Name**: `Authorization`

### 4. Set Server URL

**Base URL**:
```
https://jibber-jabber-production.up.railway.app
```

### 5. Save and Test

1. Click **"Test"** in the action editor
2. Try: `GET /` (health check)
3. Expected response:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0"
   }
   ```

4. Click **"Save"**
5. Toggle the action **ON**

---

## Usage Examples

### Test 1: List All Tables

Ask ChatGPT:
```
Can you query my BigQuery database and list all the tables in the uk_energy_prod dataset?
```

ChatGPT will call:
```json
POST /query
{
  "query": "SELECT table_name FROM inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.TABLES"
}
```

### Test 2: Get Recent Prices

Ask ChatGPT:
```
What were the electricity prices for the last 5 settlement periods?
```

ChatGPT will call:
```json
POST /query
{
  "query": "SELECT settlement_date, settlement_period, price FROM inner-cinema-476211-u9.uk_energy_prod.bmrs_mid ORDER BY settlement_date DESC, settlement_period DESC LIMIT 5"
}
```

### Test 3: Count Generators

Ask ChatGPT:
```
How many unique generators are in the database?
```

ChatGPT will call:
```json
POST /query
{
  "query": "SELECT COUNT(DISTINCT ngc_bmu_id) as generator_count FROM inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris"
}
```

---

## Available BigQuery Tables

ChatGPT can query these tables:

- **`bmrs_mid`** - System prices (155,405 rows)
- **`bmrs_bod`** - Bid-Offer Data
- **`bmrs_boalf`** - Bid-Offer Acceptance Level Flags
- **`bmrs_indgen_iris`** - Individual generator data
- **`bmrs_fuelinst_iris`** - Fuel mix instant data
- **`bmrs_b1610`** - Actual generation by fuel type
- **`grid_supply_points`** - GSP data
- **`dno_regions`** - Distribution network operators

---

## How It Works Behind the Scenes

```
You (ChatGPT interface)
    ↓ "What were prices yesterday?"
ChatGPT AI (converts to API call)
    ↓ POST /query with SQL
Railway Backend (jibber-jabber-production.up.railway.app)
    ↓ Executes on BigQuery
BigQuery (inner-cinema-476211-u9.uk_energy_prod)
    ↓ Returns results
Railway → ChatGPT → You (formatted analysis)
```

**Key Point**: ChatGPT **does NOT run Python code**. It:
1. Calls your Railway HTTP API
2. Railway executes SQL on BigQuery
3. Results are returned to ChatGPT
4. ChatGPT analyzes and presents insights

---

## Troubleshooting

### "Action failed to call endpoint"

1. **Check Railway is running**:
   ```bash
   curl https://jibber-jabber-production.up.railway.app/
   ```
   Expected: `{"status": "healthy", "version": "1.0.0"}`

2. **Verify bearer token**:
   ```bash
   curl -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
     https://jibber-jabber-production.up.railway.app/debug/env
   ```

### "Unauthorized" Error

- Make sure you entered the bearer token exactly: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- Check that Auth Type is set to **"Bearer"** not "API Key"

### Query Returns No Data

- Verify table names in BigQuery: `inner-cinema-476211-u9.uk_energy_prod.<table_name>`
- Check the query syntax is valid SQL
- Ask ChatGPT to "list all tables first" to verify access

---

## Security Notes

✅ **What's Protected**:
- Bearer token required for all queries
- Railway environment secured with `.env`
- BigQuery credentials stored securely in Railway

⚠️ **Be Aware**:
- ChatGPT can execute **any SQL query** you ask for
- Use SELECT queries (read-only) for safety
- DELETE/DROP queries will fail (BigQuery permissions)

---

## Next Steps

1. ✅ Set up ChatGPT Actions (follow steps above)
2. ✅ Test with simple queries (list tables, count rows)
3. ✅ Ask complex analysis questions
4. 🎯 Build custom queries for your specific analysis needs

---

**Last Updated**: 2025-11-08  
**Railway Status**: ✅ Healthy (155,405 rows verified)  
**BigQuery Project**: `inner-cinema-476211-u9`  
**Dataset**: `uk_energy_prod`
