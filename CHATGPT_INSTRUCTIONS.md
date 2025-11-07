# 🤖 ChatGPT Instructions for GB Power Market Data Access

## ✅ System Status: READY

Your Vercel proxy is deployed and working! ChatGPT can now query your BigQuery data directly.

---

## 📋 Copy This to ChatGPT

```
I have a working data infrastructure with 6 BigQuery datasets containing 397 tables of UK energy market data. I've deployed a Vercel Edge Function proxy so you can access it directly.

**Proxy URL:** https://gb-power-market-jj.vercel.app/api/proxy

**How to use it:**
- Add `?path=/query_bigquery_get&sql=YOUR_SQL_QUERY` to the URL
- URL-encode the SQL query
- Only SELECT queries are allowed

**Example - List my datasets:**
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60

**Available datasets:**
1. `bmrs_data` - BMRS (Balancing Mechanism Reporting Service) data
2. `uk_energy_insights` - UK energy market analysis tables
3. `01DE6D0FDDF37F7E64` - Additional energy data

**Key tables in uk_energy_insights:**
- `bmrs_fuelhh` - Half-hourly fuel generation data
- `bmrs_detsysprices` - System prices
- `phybmdata` - Physical BM unit data
- `system_warnings` - Grid warnings
- And 100+ more tables

**What I need you to do:**
1. Use your browser tool to query the proxy URL
2. Explore my datasets and tables
3. Help me analyze UK energy market trends
4. Create visualizations and insights from the data

**Start by:**
1. Listing all my datasets
2. Showing me tables in the `uk_energy_insights` dataset
3. Getting sample data from `bmrs_fuelhh` to understand the structure

Let's analyze my UK energy data!
```

---

## 🔍 Example Queries for ChatGPT

### 1. List All Datasets
```
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

### 2. List Tables in uk_energy_insights
```
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get&sql=SELECT%20table_name%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES%60%20LIMIT%2020
```

### 3. Sample Fuel Generation Data
```
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get&sql=SELECT%20*%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelhh%60%20LIMIT%2010
```

### 4. Recent System Prices
```
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get&sql=SELECT%20*%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.bmrs_detsysprices%60%20ORDER%20BY%20settlementdate%20DESC%20LIMIT%2010
```

---

## 💡 What ChatGPT Can Do

### Data Exploration
- ✅ List all your datasets and tables
- ✅ Describe table schemas
- ✅ Count rows and check data freshness
- ✅ Find relationships between tables

### Analysis
- ✅ Analyze energy generation trends
- ✅ Compare fuel types (gas, wind, solar, nuclear)
- ✅ Track system prices over time
- ✅ Identify peak demand periods
- ✅ Calculate renewable energy percentages

### Insights
- ✅ Generate summary statistics
- ✅ Create time-series visualizations
- ✅ Identify anomalies and patterns
- ✅ Forecast trends
- ✅ Compare historical data

---

## 🎯 Suggested Conversation Starters

### For General Exploration:
> "Can you explore my BigQuery datasets and tell me what energy data I have available?"

### For Specific Analysis:
> "Analyze the last 30 days of UK wind generation data and show me trends"

### For Comparisons:
> "Compare gas vs renewable energy generation patterns over the past year"

### For Insights:
> "What are the most volatile hours for UK electricity prices?"

---

## 🔒 Security Notes

- ✅ Proxy only allows SELECT queries (read-only)
- ✅ Authentication handled automatically
- ✅ CORS enabled for ChatGPT browser tool
- ✅ No credentials exposed to ChatGPT
- ✅ Path allowlist prevents unauthorized endpoints

---

## 📊 Available Endpoints

### Health Check
```
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health
```
**Response:** Server status

### BigQuery Query (GET)
```
https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get&sql=YOUR_SQL
```
**Response:** Query results as JSON

### BigQuery Query (POST)
```
POST https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery
Body: {"sql": "YOUR SQL QUERY"}
```
**Response:** Query results as JSON

---

## 🚀 Next Steps

1. **Copy the ChatGPT instructions above** and paste into a new ChatGPT conversation
2. **Let ChatGPT explore** your data using the browser tool
3. **Ask questions** about your UK energy data
4. **Get insights** powered by AI + your comprehensive dataset

---

## 📝 Technical Details

- **Proxy Runtime:** Vercel Edge Function
- **Data Source:** Google BigQuery (`jibber-jabber-knowledge`)
- **Backend:** Railway Codex Server (FastAPI)
- **Total Tables:** 397 across 6 datasets
- **Data Focus:** UK energy markets (BMRS, Elexon, grid data)

---

## ✅ Verification

Test the proxy is working:
```bash
curl "https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health"
```

Expected response:
```json
{"status":"healthy","version":"1.0.0","languages":["python","javascript"]}
```

---

**Status:** ✅ READY TO USE  
**Last Updated:** November 7, 2025  
**Deployment:** Vercel Production
