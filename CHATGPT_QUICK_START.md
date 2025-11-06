# ChatGPT Quick Start Card

## 🔗 Your Server
```
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev
```

## 📚 Full Documentation
```
https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/docs
```

---

## ⚡ Quick Commands

### Health Check
```bash
GET /health
```

### Execute Python Code
```json
POST /execute
{
  "code": "print('Hello')",
  "language": "python"
}
```

### Query BigQuery
```json
POST /query_bigquery
{
  "sql": "SELECT 1 as test"
}
```

---

## 🎯 Example for ChatGPT

**IMPORTANT**: ChatGPT should NOT access BigQuery directly. Instead, use the API endpoint.

**Correct Way - Ask ChatGPT**:
> "Make a POST request to my API endpoint:
> 
> URL: https://super-duper-engine-wr46657556g6f5jpq-8000.app.github.dev/query_bigquery
> 
> Headers: Content-Type: application/json
> 
> Body:
> ```json
> {
>   "sql": "SELECT CURRENT_TIMESTAMP() as now, 'Success!' as message"
> }
> ```
> 
> Do NOT access BigQuery directly. Use this HTTP endpoint which handles authentication."

---

## ✅ Status
- Server: Running ✅
- BigQuery: Working ✅  
- Project: jibber-jabber-knowledge ✅
- Docs: CHATGPT_API_ACCESS_GUIDE.md ✅
