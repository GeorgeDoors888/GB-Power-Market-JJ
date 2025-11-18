# 🧠 How ChatGPT Actions Work - Complete Explanation

**Last Updated**: 2025-11-09  
**Your System**: Custom GPT + Railway + BigQuery

---

## 🎯 System Architecture Overview

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   You Type  │────────▶│ Custom GPT  │────────▶│   Railway   │────────▶│  BigQuery   │
│  in ChatGPT │         │  (Actions)  │  HTTP   │   Server    │  Python │  Database   │
└─────────────┘         └─────────────┘         └─────────────┘         └─────────────┘
                              │                        │
                              │                        │
                              │  Returns JSON          │  Returns Data
                              │◀───────────────────────┘
                              │
                              ▼
                        Formats & Shows
                        Results to You
```

---

## 📖 How Your System Works (Step by Step)

### Example: "Calculate average of last 100 prices"

**Step 1: You send a message to ChatGPT**
```
Query my BigQuery database for the last 100 prices and calculate the average
```

**Step 2: ChatGPT's AI understands your intent**
- Identifies you need data from BigQuery
- Realizes it needs to call the `query_bigquery` action
- Constructs the SQL query

**Step 3: ChatGPT calls your Railway server (via Actions)**
```http
POST https://jibber-jabber-production.up.railway.app/query_bigquery
Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
Content-Type: application/json

{
  "sql": "SELECT price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` ORDER BY settlementDate DESC LIMIT 100"
}
```

**Step 4: Railway server receives the request**
- Validates the bearer token
- Creates a Python script with BigQuery client code
- Executes the query against your BigQuery database

**Step 5: BigQuery returns data**
```json
{
  "success": true,
  "data": [
    {"price": 103.3},
    {"price": 105.0},
    ...
  ],
  "row_count": 100
}
```

**Step 6: Railway sends response back to ChatGPT**

**Step 7: ChatGPT processes the data**
- If calculation needed, calls `execute_code` action:
```http
POST https://jibber-jabber-production.up.railway.app/execute
{
  "code": "import statistics\nprices = [103.3, 105.0, ...]\nprint(statistics.mean(prices))",
  "language": "python"
}
```

**Step 8: Railway executes Python code**
- Creates temporary `.py` file
- Runs it via subprocess
- Captures output

**Step 9: Railway returns result**
```json
{
  "output": "Mean: £50.18",
  "error": null,
  "exit_code": 0,
  "execution_time": 0.038
}
```

**Step 10: ChatGPT formats and shows you the answer**
```
The average price from the last 100 entries is £50.18/MWh

Execution time: 0.038s
```

---

## 🔑 Key Components Explained

### 1. **Custom GPT (Your ChatGPT Interface)**

**What it is:**
- A specialized version of ChatGPT configured for your use case
- Has your Railway server's API endpoints configured as "Actions"
- Knows how to call your server when needed

**What it does:**
- Interprets your natural language requests
- Decides which action to call (execute_code or query_bigquery)
- Constructs the API requests
- Formats the responses for you

**What it knows:**
- Your BigQuery project, dataset, table names
- Column names (settlementDate, settlementPeriod, price, volume)
- How to construct SQL queries
- When to use Railway vs built-in capabilities

**Configuration:**
- Location: https://chatgpt.com/gpts/editor/g-690f95eceb788191a021dc00389f41ee
- Has OpenAPI schema defining your Railway endpoints
- Has bearer token for authentication
- Has custom instructions for behavior

---

### 2. **ChatGPT Actions (The API Bridge)**

**What they are:**
- HTTP API calls that ChatGPT can make to external services
- Defined using OpenAPI 3.1.0 specification
- Secured with bearer token authentication

**Your Actions:**

#### Action 1: `execute_code`
```json
{
  "operationId": "execute_code",
  "endpoint": "POST /execute",
  "parameters": {
    "code": "Python or JavaScript code as string",
    "language": "python" or "javascript",
    "timeout": 30 (optional)
  }
}
```
**What it does:** Runs code on Railway server

#### Action 2: `query_bigquery`
```json
{
  "operationId": "query_bigquery",
  "endpoint": "POST /query_bigquery",
  "parameters": {
    "sql": "SQL query as string"
  }
}
```
**What it does:** Executes SQL on your BigQuery database

#### Action 3: `health_check`
```json
{
  "operationId": "health_check",
  "endpoint": "GET /",
  "parameters": {}
}
```
**What it does:** Checks if Railway server is running

**How ChatGPT decides which action to call:**
- Reads your message
- Analyzes intent
- Checks action descriptions
- Calls the most appropriate action
- Can call multiple actions in sequence

---

### 3. **Railway Server (Code Execution Engine)**

**What it is:**
- FastAPI web server running on Railway cloud platform
- Listens for HTTP requests from ChatGPT
- Executes Python/JavaScript code in isolated environment
- Queries BigQuery with Python client

**URL:** https://jibber-jabber-production.up.railway.app

**Technology Stack:**
- **Language:** Python 3.x
- **Framework:** FastAPI
- **BigQuery Client:** google-cloud-bigquery
- **Execution:** subprocess (isolated)
- **Authentication:** Bearer token

**Security Features:**
- Bearer token required (blocks unauthorized access)
- Forbidden patterns list (blocks dangerous imports)
- Subprocess isolation (code runs in separate process)
- Timeout limits (30-60 seconds max)
- Temporary files (cleaned up after execution)

**How it works:**

**For `/execute` endpoint:**
1. Receives code string from ChatGPT
2. Creates temporary `.py` or `.js` file
3. Executes via `subprocess.run()`
4. Captures stdout and stderr
5. Returns output as JSON
6. Deletes temporary file

**For `/query_bigquery` endpoint:**
1. Receives SQL query from ChatGPT
2. Creates Python script with BigQuery client code
3. Decodes BigQuery credentials from environment variable
4. Executes query
5. Converts results to JSON
6. Returns data to ChatGPT

**Environment Variables on Railway:**
- `GOOGLE_CREDENTIALS_BASE64` - BigQuery credentials (base64 encoded)
- `BQ_PROJECT_ID` - Your GCP project ID (`inner-cinema-476211-u9`)
- `BEARER_TOKEN` - Authentication token for API calls

---

### 4. **BigQuery (Data Warehouse)**

**What it is:**
- Google Cloud's serverless data warehouse
- Stores your UK electricity market data
- Processes SQL queries at scale

**Your Data:**
- **Project:** `inner-cinema-476211-u9`
- **Dataset:** `uk_energy_prod`
- **Main Table:** `bmrs_mid` (155,405 rows)
- **Other Tables:** bmrs_bod, bmrs_boalf, bmrs_indgen_iris, etc.

**Schema (bmrs_mid):**
```
settlementDate   (TIMESTAMP) - Date/time of settlement
settlementPeriod (INTEGER)   - Period number (1-48)
price            (FLOAT)     - Price in £/MWh
volume           (FLOAT)     - Volume in MWh
startTime        (TIMESTAMP) - Start time
dataProvider     (STRING)    - Data source
```

**Access:**
- Railway server has service account credentials
- Credentials stored as base64 in environment variable
- Server decodes and uses them to authenticate with BigQuery

---

## 🔄 Complete Data Flow Examples

### Example 1: Simple Code Execution

**Your Input:**
```
Execute this Python code on my server:
print("Hello!")
```

**What Happens:**
1. ChatGPT → Railway: `POST /execute` with code
2. Railway creates `/tmp/code_abc123.py` with `print("Hello!")`
3. Railway runs: `python /tmp/code_abc123.py`
4. Output captured: `"Hello!"`
5. Railway → ChatGPT: `{"output": "Hello!", "exit_code": 0}`
6. ChatGPT → You: "Hello!" (with execution time)

**Time:** ~0.02 seconds

---

### Example 2: BigQuery Query

**Your Input:**
```
Get the last 5 prices from bmrs_mid
```

**What Happens:**
1. ChatGPT constructs SQL: `SELECT price FROM ... LIMIT 5`
2. ChatGPT → Railway: `POST /query_bigquery` with SQL
3. Railway creates Python script:
   ```python
   from google.cloud import bigquery
   client = bigquery.Client()
   query = "SELECT price FROM ..."
   results = client.query(query)
   print([dict(row) for row in results])
   ```
4. Railway executes script
5. BigQuery returns: `[{"price": 103.3}, {"price": 105.0}, ...]`
6. Railway → ChatGPT: `{"success": true, "data": [...], "row_count": 5}`
7. ChatGPT formats and shows you the prices

**Time:** ~2-3 seconds

---

### Example 3: Complex Analysis (Query + Calculate)

**Your Input:**
```
Get last 100 prices and calculate mean, median, and volatility
```

**What Happens:**

**Phase 1: Get Data**
1. ChatGPT → Railway: `POST /query_bigquery`
2. SQL: `SELECT price FROM ... LIMIT 100`
3. BigQuery returns 100 prices
4. Railway → ChatGPT: JSON with price array

**Phase 2: Calculate Stats**
5. ChatGPT → Railway: `POST /execute`
6. Python code:
   ```python
   import statistics
   prices = [103.3, 105.0, ...]  # 100 prices
   mean = statistics.mean(prices)
   median = statistics.median(prices)
   stdev = statistics.stdev(prices)
   volatility = (stdev / mean) * 100
   print(f"Mean: £{mean:.2f}")
   print(f"Median: £{median:.2f}")
   print(f"Volatility: {volatility:.1f}%")
   ```
7. Railway executes Python
8. Railway → ChatGPT: Output with results

**Phase 3: Present Results**
9. ChatGPT formats nicely and shows you:
   ```
   Analysis of 100 recent prices:
   - Mean: £50.18/MWh
   - Median: £49.50/MWh
   - Volatility: 5.2%
   
   Execution time: 2.5s
   ```

**Time:** ~3-4 seconds total

---

## 🎓 Understanding ChatGPT's Behavior

### When ChatGPT Uses Railway Actions:

✅ **Uses Railway when:**
- You explicitly say "execute on my server" or "query my database"
- You mention BigQuery or Railway
- Instructions tell it to use actions
- Task requires BigQuery data access

❌ **Uses built-in Python when:**
- You don't mention server/database
- Simple calculation that doesn't need BigQuery
- Instructions don't specify action usage
- Unclear if external action is needed

### How to Force Railway Usage:

**Method 1: Explicit action name**
```
Use the execute_code action to run: print("Hello")
```

**Method 2: Mention server**
```
Execute this Python code on my server: print("Hello")
```

**Method 3: Mention Railway**
```
Run this on Railway: print("Hello")
```

**Method 4: Context from query**
```
Query my BigQuery database for prices, then calculate average on my server
```

---

## 🔧 Technical Details

### Authentication Flow:

```
1. ChatGPT makes request
   ↓
2. Includes header: Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
   ↓
3. Railway checks if token matches BEARER_TOKEN env var
   ↓
4. If match: Process request
   If no match: Return 401 Unauthorized
```

### Error Handling:

**If Railway is down:**
- ChatGPT gets connection error
- ChatGPT tells you: "I couldn't reach the Railway server"

**If SQL query is wrong:**
- BigQuery returns error
- Railway captures error message
- ChatGPT shows you the SQL error

**If Python code crashes:**
- Subprocess captures stderr
- Railway returns: `{"error": "...", "exit_code": 1}`
- ChatGPT shows you the Python error

**If timeout:**
- Railway kills process after 30-60s
- Returns timeout error
- ChatGPT suggests simplifying the query

---

## 📊 Performance Characteristics

**Code Execution (`/execute`):**
- Startup: ~0.01s (Python interpreter)
- Execution: Depends on code complexity
- Typical: 0.02 - 0.5s
- Max timeout: 30s

**BigQuery Query (`/query_bigquery`):**
- Startup: ~0.5s (BigQuery client initialization)
- Query execution: 0.5 - 5s (depends on data size)
- Data transfer: ~0.1s per 1000 rows
- Typical: 2-3s for simple queries
- Max timeout: 60s

**Combined workflow:**
- Query + Calculate: 3-5s total
- Multiple queries: 5-10s

---

## 🎯 Best Practices

### For You (User):

1. **Be explicit when you want Railway:**
   - Say "on my server" or "query my database"
   - Use action names: "use execute_code action"

2. **Start simple:**
   - Test with small data (LIMIT 10) first
   - Then scale to larger datasets

3. **Check column names:**
   - Use camelCase: `settlementDate` not `settlement_date`
   - Full table path: `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`

4. **Monitor execution time:**
   - If >5s, query might be too complex
   - Consider using aggregations in SQL instead of post-processing

### For ChatGPT (Instructions):

1. **Always prefer actions for data tasks:**
   - Use `query_bigquery` for any BigQuery data
   - Use `execute_code` for Python calculations on server

2. **Show execution metadata:**
   - Always mention execution time
   - Confirm it ran on Railway

3. **Handle errors gracefully:**
   - If action fails, explain what went wrong
   - Suggest fixes for common issues

---

## 🔍 Debugging Your System

### Check Railway Health:
```bash
curl https://jibber-jabber-production.up.railway.app/
```
Expected: `{"status": "running", "version": "1.0.0"}`

### Test Code Execution:
```bash
curl -X POST https://jibber-jabber-production.up.railway.app/execute \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Test\")", "language": "python"}'
```
Expected: `{"output": "Test\n", "exit_code": 0}`

### Test BigQuery Access:
```bash
curl -X POST https://jibber-jabber-production.up.railway.app/query_bigquery \
  -H "Authorization: Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`"}'
```
Expected: `{"success": true, "data": [{"count": 155405}]}`

---

## 📚 Summary

**Your System = Natural Language → Data Analysis**

```
You speak plain English
    ↓
ChatGPT understands and calls appropriate APIs
    ↓
Railway executes code or queries BigQuery
    ↓
Results return to ChatGPT
    ↓
ChatGPT presents results in natural language
```

**No coding required for you!** Just talk to ChatGPT like you're talking to a data analyst.

---

## 🔗 Quick Links

- **Use Your GPT:** https://chatgpt.com/g/g-690f95eceb788191a021dc00389f41ee-gb-power-market-code-execution
- **Edit Your GPT:** https://chatgpt.com/gpts/editor/g-690f95eceb788191a021dc00389f41ee
- **Railway Dashboard:** https://railway.app (login to see your server)
- **BigQuery Console:** https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9

---

**Last Updated:** 2025-11-09  
**System Status:** ✅ All components operational  
**Ready for:** Advanced data analysis and forecasting
