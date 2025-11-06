# ChatGPT Integration Troubleshooting Guide

## ❌ Common Error: "Project not found or insufficient permissions"

### What This Means
ChatGPT is trying to access BigQuery **directly** instead of using your API endpoint.

### Why This Happens
ChatGPT has built-in BigQuery integration, so when you mention "BigQuery" it tries to:
1. Connect directly to Google BigQuery
2. Use its own authentication
3. Access your project (which fails - it doesn't have permission)

---

## ✅ The Correct Approach

### What ChatGPT Should Do
**Use your API as an HTTP endpoint** - treat it like any web API, not as BigQuery.

### Don't Say This ❌
> "Query BigQuery for me using project jibber-jabber-knowledge"
> 
> "Access my BigQuery table in inner-cinema-476211-u9"
> 
> "Run this SQL in BigQuery: SELECT * FROM table"

**Why**: These phrases trigger ChatGPT's direct BigQuery integration.

### Say This Instead ✅
> "Make an HTTP POST request to this API endpoint:
> https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery
> 
> Send this JSON body:
> {
>   \"sql\": \"SELECT CURRENT_TIMESTAMP() as now\"
> }"

**Why**: This tells ChatGPT to use HTTP, not direct BigQuery access.

---

## 📝 Exact Prompts That Work

### ✅ Correct Prompt #1: Simple Query
```
Please make an HTTP POST request to:
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery

Headers:
Content-Type: application/json

Body:
{
  "sql": "SELECT 1 as test_number, CURRENT_TIMESTAMP() as current_time"
}

Show me the response.
```

### ✅ Correct Prompt #2: Data Query
```
Call my API endpoint with a POST request:

Endpoint: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery

JSON payload:
{
  "sql": "SELECT COUNT(*) as total_records FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`",
  "timeout": 60
}

This is a REST API that executes SQL queries server-side. Do not access BigQuery directly.
```

### ✅ Correct Prompt #3: Complex Analysis
```
I have a REST API that can execute SQL queries. Please use it:

1. Send POST to: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery

2. Request body:
{
  "sql": "SELECT fuel_type, COUNT(*) as records FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) = CURRENT_DATE() GROUP BY fuel_type ORDER BY records DESC",
  "timeout": 90,
  "max_results": 100
}

3. Parse the JSON response and analyze the data.

Note: This is an HTTP API wrapper around BigQuery. Do not use direct BigQuery access.
```

---

## 🔍 How to Verify ChatGPT is Using Your API

### Signs ChatGPT is Doing It Correctly ✅
- It mentions "making an HTTP request"
- It shows curl commands or similar
- It displays JSON request/response
- No mention of "connecting to BigQuery"
- No authentication errors

### Signs ChatGPT is Doing It Wrong ❌
- Error: "Project not found or insufficient permissions"
- Error: "Access Denied: User does not have permission"
- It asks for Google Cloud credentials
- It mentions "authenticating with BigQuery"
- It tries to access the project directly

---

## 🛠️ Debugging Steps

### Step 1: Test Your API Manually
```bash
curl -X POST "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 as test"}'
```

**Expected Response**:
```json
{
  "success": true,
  "data": [{"test": 1}],
  "row_count": 1,
  "error": null,
  "execution_time": 1.5,
  "timestamp": "2025-11-06T20:48:00.000000"
}
```

### Step 2: Verify Endpoint is Accessible
```bash
curl "https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/health"
```

**Expected Response**:
```json
{
  "status": "running",
  "version": "1.0.0",
  "languages": ["python", "javascript"],
  "timestamp": "2025-11-06T20:48:00.000000"
}
```

### Step 3: Check API Documentation
Visit: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/docs

This should show the interactive API documentation (Swagger UI).

---

## 💡 Key Points to Remember

### Your Server Architecture
```
ChatGPT → HTTP Request → Your API → BigQuery
                ↓
         (Authentication happens here)
```

**NOT**:
```
ChatGPT → Direct BigQuery Access ❌ (This causes the error)
```

### What Your API Does
1. Receives HTTP POST request with SQL
2. Authenticates using service account (server-side)
3. Executes query in BigQuery
4. Returns JSON results

### What ChatGPT Should Do
1. Make HTTP POST request to your endpoint
2. Send SQL in JSON body
3. Parse JSON response
4. Never mention "BigQuery authentication"

---

## 📋 Quick Reference Card for ChatGPT

Copy and paste this into your ChatGPT conversation:

```
IMPORTANT: How to use my BigQuery API

Endpoint: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery
Method: POST
Content-Type: application/json

Request Format:
{
  "sql": "YOUR SQL QUERY HERE",
  "timeout": 60,
  "max_results": 1000
}

Response Format:
{
  "success": true/false,
  "data": [...],
  "row_count": number,
  "error": null or error message,
  "execution_time": seconds,
  "timestamp": ISO timestamp
}

Rules:
1. Always use HTTP POST requests
2. Never access BigQuery directly
3. All authentication is handled server-side
4. Treat this as a REST API, not BigQuery

Example:
POST to above endpoint with body:
{"sql": "SELECT CURRENT_TIMESTAMP() as now"}
```

---

## 🚨 If You Still Get Errors

### Error: Connection Refused
**Cause**: Server might be down  
**Solution**: Check server status at `/health` endpoint

### Error: 404 Not Found
**Cause**: Wrong endpoint URL  
**Solution**: Verify the URL includes `/query_bigquery`

### Error: 422 Validation Error
**Cause**: Missing required fields in request  
**Solution**: Ensure JSON includes `"sql"` field

### Error: Timeout
**Cause**: Query takes too long  
**Solution**: Increase `"timeout"` value or optimize query

### Server Error: "Service account not found"
**Cause**: Server configuration issue  
**Solution**: Check `/workspace/gridsmart_service_account.json` exists

---

## ✅ Success Checklist

Before asking ChatGPT to use your API:

- [ ] Server is running (check `/health`)
- [ ] Public URL is accessible
- [ ] Manual curl test works
- [ ] You're using HTTP request language (not BigQuery language)
- [ ] You're NOT asking ChatGPT to "connect to BigQuery"
- [ ] You ARE asking ChatGPT to "make POST request to endpoint"

---

**Remember**: Your API is a **wrapper** around BigQuery. ChatGPT should treat it like any HTTP API, not as direct BigQuery access.
