# ChatGPT GET Endpoint Guide

## ✅ NEW: GET Endpoint for Browser Tools

Your Railway Codex Server now has a **GET endpoint** that ChatGPT's browser tool can access!

---

## 🎯 The Problem (Solved)

**Before**: ChatGPT's browser tool couldn't access the POST `/query_bigquery` endpoint.

**Now**: ChatGPT can use the GET `/query_bigquery_get` endpoint with URL parameters!

---

## 🚀 How to Use It

### URL Format:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=YOUR_SQL_HERE
```

### Example Queries:

#### 1. List All Datasets:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

**Response:**
```json
{
  "success": true,
  "data": [
    {"schema_name": "01DE6D0FDDF37F7E64"},
    {"schema_name": "bmrs_data"},
    {"schema_name": "uk_energy_insights"},
    {"schema_name": "companies_house"},
    {"schema_name": "uk_energy_analytics_us"},
    {"schema_name": "document_index"}
  ],
  "row_count": 6,
  "error": null,
  "execution_time": 2.329
}
```

#### 2. List Tables in a Dataset:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20table_name%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES%60%20LIMIT%2010
```

#### 3. Sample Data from Table:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20*%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.bmrs_data%60%20LIMIT%205
```

---

## 📝 How to Tell ChatGPT

Copy and paste this into ChatGPT:

```
I have a Railway server with BigQuery access that you can query!

URL: https://jibber-jabber-production.up.railway.app/query_bigquery_get

How to use:
1. Add ?sql= followed by URL-encoded SQL
2. Use your browser tool to GET the URL
3. You'll get JSON back with the query results

Example - list my datasets:
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60

Please try it now!
```

---

## 🔧 URL Encoding

SQL needs to be URL-encoded for GET requests. Common conversions:

| Character | Encoded |
|-----------|---------|
| Space | `%20` |
| Backtick ` | `%60` |
| Dot . | `.` (no encoding) |
| Comma , | `%2C` |
| Equals = | `%3D` |
| Single Quote ' | `%27` |

**Online Tool**: https://www.urlencoder.org/

**Quick Python**:
```python
from urllib.parse import quote
sql = "SELECT * FROM `jibber-jabber-knowledge.dataset.table` LIMIT 10"
encoded = quote(sql)
print(f"https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql={encoded}")
```

---

## 🎯 Common Queries for ChatGPT

### List All Datasets:
```sql
SELECT schema_name 
FROM `jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA`
```
URL:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

### List Tables in UK Energy Dataset:
```sql
SELECT table_name 
FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
LIMIT 20
```
URL:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20table_name%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES%60%20LIMIT%2020
```

### Get Sample Data:
```sql
SELECT * 
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_data` 
LIMIT 5
```
URL:
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20*%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.bmrs_data%60%20LIMIT%205
```

---

## ⚠️ Important Notes

1. **GET vs POST**:
   - GET endpoint: `/query_bigquery_get` (for ChatGPT browser tool)
   - POST endpoint: `/query_bigquery` (for API clients, curl, etc.)

2. **Limitations**:
   - GET URLs have max length (~2000 characters)
   - For very long queries, use the POST endpoint instead
   - Results limited to 1000 rows max

3. **Security**:
   - No authentication required (public endpoint)
   - Only read-only SELECT queries recommended
   - BigQuery permissions control what can be accessed

---

## 🧪 Testing from Your Side

### From Terminal (Codespace/Local):
```bash
# List datasets
curl -s "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60"

# List tables
curl -s "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20table_name%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES%60%20LIMIT%2010"
```

### From Browser:
Just paste the URL directly into your browser address bar!

---

## 📊 Response Format

All responses follow this structure:

```json
{
  "success": true,           // true if query succeeded
  "data": [...],            // Array of result rows
  "row_count": 6,           // Number of rows returned
  "error": null,            // Error message if success=false
  "execution_time": 2.329,  // Query time in seconds
  "timestamp": "2025-11-07T..." // When query executed
}
```

---

## 🎯 Tell ChatGPT Exactly What to Do

**Copy this entire prompt to ChatGPT:**

---

You have access to my BigQuery data through a GET endpoint!

**Endpoint**: `https://jibber-jabber-production.up.railway.app/query_bigquery_get`

**How to use it:**
1. Use your browser tool to GET the URL
2. Add `?sql=` parameter with URL-encoded SQL
3. You'll get JSON back with query results

**First test - Get my datasets:**
```
https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

Please:
1. GET that URL now using your browser tool
2. Tell me what datasets you found
3. Then list tables in the `uk_energy_insights` dataset

After that, I want you to analyze the data you find!

---

## ✅ Success Indicators

When ChatGPT successfully uses the endpoint, you'll see:

1. ChatGPT says something like: "I found X datasets in your BigQuery project..."
2. It shows actual data from your tables
3. It can answer questions about your data without asking you for it
4. You can see queries in Railway logs

---

**Status**: ✅ Deployed and Working  
**Last Updated**: November 7, 2025  
**Commit**: 48b85e8
