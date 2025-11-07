# GB Power Market JJ - Complete System Documentation

## 🎯 Overview

**GB Power Market JJ** is a comprehensive UK energy market data platform providing real-time access to 397 BigQuery tables across 6 datasets, accessible via ChatGPT through a Vercel Edge Function proxy.

---

## 🏗️ Architecture

```
┌─────────────────┐
│    ChatGPT      │
│  Browser Tool   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────┐
│  Vercel Edge Function       │
│  gb-power-market-jj         │
│  - SQL validation           │
│  - Auth injection           │
│  - CORS handling            │
└────────┬────────────────────┘
         │ Authenticated
         ▼
┌─────────────────────────────┐
│  Railway Codex Server       │
│  jibber-jabber-production   │
│  - FastAPI backend          │
│  - Query execution          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Google BigQuery            │
│  jibber-jabber-knowledge    │
│  - 6 datasets               │
│  - 397 tables               │
│  - UK energy data           │
└─────────────────────────────┘
```

---

## 📊 Data Inventory

### Datasets

1. **bmrs_data** - Balancing Mechanism Reporting Service
   - System balancing data
   - Generation forecasts
   - Market prices

2. **uk_energy_insights** - Primary analysis dataset
   - 100+ tables
   - Half-hourly generation data
   - System prices and forecasts
   - Grid warnings and constraints

3. **01DE6D0FDDF37F7E64** - Additional energy data

4. **Additional datasets** - Historical and reference data

### Key Tables

| Table | Dataset | Description | Update Frequency |
|-------|---------|-------------|------------------|
| `bmrs_fuelhh` | uk_energy_insights | Half-hourly fuel generation | 30 min |
| `bmrs_detsysprices` | uk_energy_insights | System buy/sell prices | Daily |
| `phybmdata` | uk_energy_insights | Physical BM unit data | Real-time |
| `system_warnings` | uk_energy_insights | Grid stability warnings | As issued |
| `generation_forecast` | uk_energy_insights | Generation predictions | Hourly |

**Total:** 397 tables across all datasets

---

## 🌐 API Endpoints

### Base URL
```
https://gb-power-market-jj.vercel.app
```

### Endpoints

#### 1. Health Check
```
GET /api/proxy?path=/health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "languages": ["python", "javascript"]
}
```

#### 2. BigQuery Query (GET)
```
GET /api/proxy?path=/query_bigquery_get&sql=<URL_ENCODED_SQL>
```
**Example:**
```
/api/proxy?path=/query_bigquery_get&sql=SELECT%20*%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelhh%60%20LIMIT%205
```

**Response:**
```json
{
  "success": true,
  "data": [...],
  "row_count": 5,
  "error": null,
  "execution_time": 1.234,
  "timestamp": "2025-11-07T12:00:00.000Z"
}
```

#### 3. BigQuery Query (POST)
```
POST /api/proxy?path=/query_bigquery
Content-Type: application/json

{
  "sql": "SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelhh` LIMIT 5"
}
```

---

## 🔒 Security

### Authentication
- **Railway Token:** Hardcoded in Vercel Edge Function
- **Token:** `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- **Auto-injection:** Proxy adds `Authorization: Bearer <token>` header

### SQL Validation
- ✅ Only SELECT queries allowed
- ❌ INSERT, UPDATE, DELETE blocked
- ❌ Multiple statements (semicolons) blocked
- ❌ Queries over 5000 characters blocked

### Path Allowlist
Only these paths are allowed:
- `/health`
- `/query_bigquery_get`
- `/query_bigquery`
- `/run_stack_check`

### CORS
- **Enabled:** `Access-Control-Allow-Origin: *`
- **Purpose:** ChatGPT browser tool access

---

## 🚀 Deployment

### Vercel Configuration

**Project:** gb-power-market-jj  
**Team:** George Major's projects  
**Framework:** None (Serverless Functions)  
**Runtime:** Edge  
**Root Directory:** `vercel-proxy`  

**GitHub Integration:**
- **Repository:** `GeorgeDoors888/overarch-jibber-jabber`
- **Branch:** `main`
- **Auto-deploy:** Enabled

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| RAILWAY_BASE | (hardcoded in code) | Railway server URL |
| CODEX_TOKEN | (hardcoded in code) | Authentication token |

**Note:** Currently hardcoded in `/vercel-proxy/api/proxy.ts` due to Edge Runtime env var limitations.

### URLs

- **Production:** https://gb-power-market-jj.vercel.app
- **Preview:** Auto-generated per commit
- **Railway Backend:** https://jibber-jabber-production.up.railway.app

---

## 📁 Repository Structure

```
overarch-jibber-jabber/
├── vercel-proxy/              # Vercel Edge Function
│   ├── api/
│   │   ├── proxy.ts          # Main proxy (working)
│   │   ├── proxy-v2.ts       # Backup version
│   │   ├── test.ts           # Test endpoint
│   │   └── debug.ts          # Debug endpoint
│   ├── package.json
│   └── README.md
├── CHATGPT_INSTRUCTIONS.md   # Guide for ChatGPT
├── README.md                 # Project overview
└── ... (other project files)
```

---

## 🧪 Testing

### Manual Testing

**1. Health Check:**
```bash
curl "https://gb-power-market-jj.vercel.app/api/proxy?path=/health"
```

**2. List Datasets:**
```bash
curl "https://gb-power-market-jj.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60"
```

**3. Sample Data:**
```bash
curl "https://gb-power-market-jj.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20*%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelhh%60%20LIMIT%203"
```

### Expected Responses

All successful responses include:
```json
{
  "success": true,
  "data": [...],
  "row_count": N,
  "error": null,
  "execution_time": X.XXX,
  "timestamp": "ISO-8601"
}
```

Error responses:
```json
{
  "ok": false,
  "error": "error message"
}
```

---

## 🤖 ChatGPT Integration

### How ChatGPT Accesses Data

1. **User provides proxy URL** to ChatGPT
2. **ChatGPT uses browser tool** to make GET requests
3. **Proxy validates and forwards** to Railway
4. **Railway queries BigQuery** and returns results
5. **ChatGPT processes** JSON response
6. **User receives** insights and analysis

### What ChatGPT Can Do

- ✅ Explore dataset structure
- ✅ Query any table
- ✅ Analyze time-series data
- ✅ Generate visualizations
- ✅ Compare metrics
- ✅ Identify trends
- ✅ Forecast patterns
- ✅ Answer natural language questions about UK energy data

### Limitations

- ❌ No write access (read-only)
- ❌ Query timeout: ~30 seconds
- ❌ Result size: Limited by Vercel response size (~4.5MB)
- ❌ Rate limits: Vercel free tier limits

---

## 📈 Use Cases

### 1. Energy Market Analysis
- Track renewable energy adoption
- Monitor system prices
- Analyze generation patterns

### 2. Grid Stability
- Monitor system warnings
- Track frequency response
- Analyze constraint periods

### 3. Forecasting
- Generation predictions
- Demand forecasting
- Price predictions

### 4. Reporting
- Automated insights
- Trend reports
- Anomaly detection

---

## 🛠️ Maintenance

### Updating the Proxy

**File:** `/workspaces/overarch-jibber-jabber/vercel-proxy/api/proxy.ts`

1. Edit the file
2. Commit changes:
   ```bash
   git add vercel-proxy/api/proxy.ts
   git commit -m "Update proxy logic"
   git push
   ```
3. Vercel auto-deploys (30-60 seconds)
4. Test the update

### Monitoring

- **Vercel Dashboard:** https://vercel.com/george-majors-projects/gb-power-market-jj
- **Railway Dashboard:** https://railway.app (Railway server logs)
- **BigQuery Console:** https://console.cloud.google.com/bigquery

### Troubleshooting

**Issue:** FUNCTION_INVOCATION_FAILED
- **Cause:** Code error in Edge Function
- **Fix:** Check syntax, ensure proper Edge Runtime API usage

**Issue:** Path not allowed
- **Cause:** Requesting non-whitelisted endpoint
- **Fix:** Use only: `/health`, `/query_bigquery_get`, `/query_bigquery`, `/run_stack_check`

**Issue:** SQL error
- **Cause:** Invalid SQL syntax
- **Fix:** Test SQL in BigQuery console first

---

## 💰 Costs

### Vercel (Free Tier)
- ✅ 100GB bandwidth/month
- ✅ 100GB edge network requests
- ✅ Unlimited edge function executions
- **Current usage:** <1% of free tier
- **Cost:** $0

### Railway
- ✅ Server running 24/7
- **Cost:** Variable based on usage

### Google BigQuery
- **Storage:** ~$0.02/GB/month
- **Queries:** $5/TB processed
- **Estimated:** <$10/month
- **Note:** ChatGPT queries count toward quota

---

## 📚 Documentation Links

- **Vercel Edge Functions:** https://vercel.com/docs/functions/edge-functions
- **Railway Deployment:** https://docs.railway.app
- **BigQuery API:** https://cloud.google.com/bigquery/docs
- **BMRS Data Guide:** https://www.bmreports.com

---

## ✅ Status

| Component | Status | URL |
|-----------|--------|-----|
| Vercel Proxy | ✅ LIVE | https://gb-power-market-jj.vercel.app |
| Railway Backend | ✅ LIVE | https://jibber-jabber-production.up.railway.app |
| BigQuery | ✅ LIVE | Console access |
| ChatGPT Access | ✅ READY | Use instructions |

---

## 🎯 Quick Start

1. **Test the proxy:**
   ```bash
   curl "https://gb-power-market-jj.vercel.app/api/proxy?path=/health"
   ```

2. **Open ChatGPT** and paste from `CHATGPT_INSTRUCTIONS.md`

3. **Let ChatGPT explore** your data

4. **Ask questions** like:
   - "What energy data do I have?"
   - "Show me recent wind generation trends"
   - "Compare gas vs renewable energy this week"

---

**Last Updated:** November 7, 2025  
**Version:** 1.0  
**Maintainer:** George Major
