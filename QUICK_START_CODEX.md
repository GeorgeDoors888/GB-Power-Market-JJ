# ⚡ Quick Start - Codex Server with BigQuery

## 🎯 5-Minute Quick Start

### 1️⃣ Open Codespace
```
https://github.com/GeorgeDoors888/overarch-jibber-jabber
→ Code button → Codespaces → Create/Open
```

### 2️⃣ Upload Service Account
```bash
# Drag gridsmart_service_account.json to /workspace/ in Codespace
```

### 3️⃣ Install & Start
```bash
cd /workspace/codex-server
pip install -r requirements.txt
python codex_server.py
```

### 4️⃣ Make Port Public
```
PORTS tab → Right-click 8000 → "Port Visibility: Public"
Copy URL (e.g., https://xxx-8000.app.github.dev)
```

### 5️⃣ Tell ChatGPT
```
ChatGPT, my BigQuery API is at:
https://xxx-8000.app.github.dev/query_bigquery

You can POST SQL queries to get UK energy data from:
- Project: inner-cinema-476211-u9
- Dataset: uk_energy_prod
- Tables: bmrs_fuelinst_iris, bmrs_imbalprices_iris, etc.
```

---

## 🧪 Test It

### Health Check:
```bash
curl http://localhost:8000/health
```

### BigQuery Test:
```bash
curl -X POST http://localhost:8000/query_bigquery \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT fuelType, SUM(generation) as total FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris` WHERE DATE(settlementDate) = CURRENT_DATE() GROUP BY fuelType LIMIT 5"
  }'
```

---

## 📋 What ChatGPT Can Do

**Before:** 
- You: "What's renewable %?"
- ChatGPT: "Can you run a query and paste results?"

**After:**
- You: "What's renewable %?"
- ChatGPT: *[Makes POST to your server with SQL query]*
- ChatGPT: "Renewable is 68.4%"

---

## 🔧 Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8000 not showing | Wait 10 sec after starting server |
| Service account not found | Upload to `/workspace/` folder |
| Module not found | Run `pip install -r requirements.txt` |
| Codespace stopped | Restart and re-run step 3 |

---

## 💰 Cost: $0
- Codespaces: 60 hrs/month free
- BigQuery: First 1 TB/month free
- Your usage: Well within limits

---

## 📚 Full Guide
See: `START_CODEX_WITH_BIGQUERY.md` for detailed instructions

---

**Ready? Go to step 1! 🚀**
