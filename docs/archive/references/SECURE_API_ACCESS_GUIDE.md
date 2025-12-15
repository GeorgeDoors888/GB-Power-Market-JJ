# 🔐 Secure API Access Guide

**Date:** 2025-11-08  
**Status:** ✅ Token storage configured and tested

---

## 🎯 Overview

This guide shows how to securely use your Railway API bearer token without exposing it in code or commits.

---

## ✅ Step 1: Token Storage (DONE)

Your bearer token is now securely stored in `.env`:

```bash
BEARER_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
RAILWAY_API_URL=https://jibber-jabber-production.up.railway.app
```

**Security features:**
- ✅ `.env` file is in `.gitignore` (never committed to GitHub)
- ✅ Token is loaded from environment at runtime
- ✅ No hardcoded secrets in code

---

## 🧪 Step 2: Verification (DONE)

Tested with `test_railway_secure.py`:

```bash
python3 test_railway_secure.py
```

**Results:**
- ✅ Health check: Working
- ✅ Debug endpoint: inner-cinema-476211-u9 configured correctly
- ✅ BigQuery query: 155,405 rows accessible
- ✅ Execution time: ~1.7 seconds

---

## 💻 Step 3: Usage in Your Code

### Python Example

```python
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get configuration
url = os.getenv('RAILWAY_API_URL')
token = os.getenv('BEARER_TOKEN')

# Make secure API call
response = requests.get(
    f"{url}/query_bigquery_get",
    params={
        "sql": "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 5"
    },
    headers={
        "Authorization": f"Bearer {token}"
    }
)

data = response.json()
print(data)
```

### JavaScript/Node.js Example

```javascript
// Install: npm install dotenv
import 'dotenv/config';

const url = process.env.RAILWAY_API_URL;
const token = process.env.BEARER_TOKEN;

const response = await fetch(`${url}/query_bigquery_get?sql=SELECT * FROM ...`, {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});

const data = await response.json();
console.log(data);
```

---

## 🔗 Available Endpoints

### 1. Health Check
```python
GET /health
Headers: Authorization: Bearer {token}

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "languages": ["python", "javascript"]
}
```

### 2. Debug Environment
```python
GET /debug/env
Headers: Authorization: Bearer {token}

Response:
{
  "BQ_PROJECT_ID": "inner-cinema-476211-u9",
  "project_in_credentials": "inner-cinema-476211-u9"
}
```

### 3. BigQuery Query (GET)
```python
GET /query_bigquery_get?sql={SQL_QUERY}
Headers: Authorization: Bearer {token}

Example:
GET /query_bigquery_get?sql=SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`

Response:
{
  "success": true,
  "data": [{"cnt": 155405}],
  "row_count": 1,
  "execution_time": 1.7,
  "timestamp": "2025-11-08T17:43:55.655346"
}
```

### 4. BigQuery Query (POST)
```python
POST /query_bigquery
Headers: Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "sql": "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 5"
}

Response: Same as GET version
```

---

## 🌐 Cloud Deployment

### Railway (Already Configured)
The token is already set in Railway environment variables:
- Variable: `CODEX_API_TOKEN`
- Used by: codex_server.py for authentication

### Vercel / Other Platforms
If deploying to other platforms:

1. **Go to** platform dashboard → Settings → Environment Variables
2. **Add:**
   - `BEARER_TOKEN`: `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
   - `RAILWAY_API_URL`: `https://jibber-jabber-production.up.railway.app`

---

## 🛡️ Security Best Practices

### ✅ DO:
- Store tokens in `.env` file (local)
- Use environment variables in cloud
- Load with `python-dotenv` or similar
- Add `.env` to `.gitignore`
- Use HTTPS for all API calls

### ❌ DON'T:
- Hardcode tokens in source code
- Commit `.env` to Git
- Share tokens in public channels
- Log tokens in console/logs
- Use HTTP (non-encrypted) for token transmission

---

## 📝 Environment Variables Reference

### Required Variables
```bash
# Railway API
BEARER_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
RAILWAY_API_URL=https://jibber-jabber-production.up.railway.app

# BigQuery
BQ_PROJECT_ID=inner-cinema-476211-u9
BQ_DATASET=uk_energy_prod

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/inner-cinema-credentials.json
```

### Optional Variables
```bash
# Google Sheet
SHEET_ID=1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

# OpenAI (if using Assistant)
OPENAI_API_KEY=sk-your-key-here
OPENAI_ASSISTANT_ID=asst_...

# Features
OCR_ENABLED=false
```

---

## 🧪 Testing Scripts

### Test Railway Connection
```bash
python3 test_railway_secure.py
```

Tests:
1. Health check
2. Debug environment
3. BigQuery query (count)

### Test OpenAI Assistant
```bash
python3 setup_openai_assistant.py
```

Creates:
1. OpenAI Assistant
2. Vector store with documentation
3. File search capability

---

## 🔄 Token Rotation

If you need to change the bearer token:

### 1. Update Local Environment
Edit `.env` file:
```bash
BEARER_TOKEN=new_token_here
```

### 2. Update Railway
1. Go to Railway dashboard
2. Service Settings → Variables
3. Update `CODEX_API_TOKEN`
4. Redeploy service

### 3. Test Connection
```bash
python3 test_railway_secure.py
```

---

## 📊 Example Use Cases

### 1. Get Latest System Prices
```python
from dotenv import load_dotenv
import os, requests

load_dotenv()

sql = """
SELECT settlement_date, settlement_period, ssp, sbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
ORDER BY settlement_date DESC, settlement_period DESC
LIMIT 10
"""

response = requests.get(
    f"{os.getenv('RAILWAY_API_URL')}/query_bigquery_get",
    params={"sql": sql},
    headers={"Authorization": f"Bearer {os.getenv('BEARER_TOKEN')}"}
)

data = response.json()
if data['success']:
    for row in data['data']:
        print(f"{row['settlement_date']} SP{row['settlement_period']}: £{row['ssp']:.2f}")
```

### 2. Get Fuel Mix
```python
sql = """
SELECT fuelType, SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE DATE(startTime) = CURRENT_DATE()
GROUP BY fuelType
ORDER BY total_mw DESC
"""

response = requests.get(
    f"{os.getenv('RAILWAY_API_URL')}/query_bigquery_get",
    params={"sql": sql},
    headers={"Authorization": f"Bearer {os.getenv('BEARER_TOKEN')}"}
)

data = response.json()
if data['success']:
    print("Today's Generation by Fuel Type:")
    for row in data['data']:
        print(f"  {row['fuelType']}: {row['total_mw']:.0f} MW")
```

### 3. Check Interconnector Flows
```python
sql = """
SELECT startTime, fuelType, generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE fuelType LIKE '%INTFR%'  -- France interconnector
  OR fuelType LIKE '%INTIRL%'  -- Ireland interconnector
  OR fuelType LIKE '%INTNED%'  -- Netherlands interconnector
ORDER BY startTime DESC
LIMIT 20
"""

response = requests.get(
    f"{os.getenv('RAILWAY_API_URL')}/query_bigquery_get",
    params={"sql": sql},
    headers={"Authorization": f"Bearer {os.getenv('BEARER_TOKEN')}"}
)

data = response.json()
if data['success']:
    print("Recent Interconnector Flows:")
    for row in data['data']:
        flow = "Import" if row['generation'] > 0 else "Export"
        print(f"{row['startTime']}: {row['fuelType']} - {abs(row['generation']):.0f} MW {flow}")
```

---

## 🆘 Troubleshooting

### Token Not Found
**Error:** `❌ BEARER_TOKEN not set!`

**Solution:**
1. Check `.env` file exists in project root
2. Verify token is on line: `BEARER_TOKEN=codex_...`
3. Make sure you're running from correct directory
4. Try: `python3 -m dotenv run python3 your_script.py`

### Unauthorized Error
**Error:** `401 Unauthorized`

**Solution:**
1. Verify token is correct in `.env`
2. Check Railway environment variable matches
3. Ensure token hasn't expired
4. Test with `test_railway_secure.py`

### Module Not Found
**Error:** `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
python3 -m pip install --break-system-packages python-dotenv
```

---

## 📚 Related Documentation

- **RAILWAY_BIGQUERY_FIX_STATUS.md** - Railway backend status
- **PROJECT_IDENTITY_MASTER.md** - Project identity guide
- **DASHBOARD_V2_GUIDE.md** - Dashboard setup
- **test_railway_secure.py** - Security testing script
- **setup_openai_assistant.py** - OpenAI Assistant setup

---

## ✅ Status Summary

**Security:** ✅ Configured  
**Token Storage:** ✅ In .env (gitignored)  
**Railway API:** ✅ Tested and working  
**BigQuery Access:** ✅ Verified (155,405 rows)  
**Documentation:** ✅ Complete

---

**Last Tested:** 2025-11-08 17:43 UTC  
**All Systems:** 🟢 Operational
