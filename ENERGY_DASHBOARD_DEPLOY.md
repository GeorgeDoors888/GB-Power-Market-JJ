# 🚀 Deploy Your Energy Dashboard in 5 Minutes

## ✅ What You Got

A complete, production-ready energy dashboard that:
- ✅ Connects to your Codex Server on Railway
- ✅ Queries BigQuery data from `jibber-jabber-knowledge.uk_energy_insights`
- ✅ Shows live charts with auto-refresh
- ✅ Adapts to your table structure
- ✅ Ready to deploy with one command

## 📍 Files Created

```
energy-dashboard/
├── app.py              ← FastAPI application (270 lines)
├── requirements.txt    ← Python dependencies
├── Dockerfile          ← Container config
├── railway.json        ← Railway deployment config
└── README.md          ← Full documentation
```

## 🎯 Deploy Now (3 Steps)

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Deploy

```bash
cd /workspaces/overarch-jibber-jabber/energy-dashboard
railway init
railway up
```

### Step 3: Set Environment Variables

```bash
railway variables set CODEX_BASE=https://jibber-jabber-production.up.railway.app
railway variables set BQ_PROJECT=jibber-jabber-knowledge  
railway variables set BQ_DATASET=uk_energy_insights
railway variables set REFRESH_MIN=5
```

### Step 4: Get Your URL

```bash
railway status
```

Visit: `https://your-dashboard.up.railway.app` 🎉

---

## 🧪 Test Locally First (Optional)

```bash
cd energy-dashboard

# Install dependencies
pip install -r requirements.txt

# Set environment
export CODEX_BASE=https://jibber-jabber-production.up.railway.app
export BQ_PROJECT=jibber-jabber-knowledge
export BQ_DATASET=uk_energy_insights
export REFRESH_MIN=5

# Run
uvicorn app:app --reload --port 8001
```

Visit: http://localhost:8001

Test API:
```bash
curl http://localhost:8001/health
curl http://localhost:8001/api/summary
```

---

## 📊 What the Dashboard Shows

### Live Widgets:

1. **Current GB Demand** - Latest power demand in MW
2. **Generation Mix** - Pie chart of fuel types
3. **24h Demand Trend** - Line chart of last 24 hours
4. **Top 10 BMUs** - Balancing Mechanism Units by output
5. **Balancing Costs** - Last 30 days trend
6. **Tables Used** - Shows which BigQuery tables it found

### Auto-Detection:

The dashboard automatically finds the best tables in your dataset:
- Looks for demand data
- Finds BMU/balancing data
- Detects cost tables
- Adapts queries to column names

---

## 🤖 Tell ChatGPT About It

Once deployed, paste this to ChatGPT:

```
I just deployed an energy dashboard!

URL: https://[your-url].up.railway.app
Repo: https://github.com/GeorgeDoors888/overarch-jibber-jabber/tree/main/energy-dashboard

It connects to my Codex Server and shows UK energy data from BigQuery.

Can you:
1. Check if it's working by visiting /health and /api/summary
2. Analyze the data structure
3. Suggest 3 new features to add
4. Help me add a Google Sheets export
```

ChatGPT will:
- ✅ Visit your dashboard
- ✅ Check the API
- ✅ Read the data
- ✅ Suggest improvements
- ✅ Write code for new features

---

## 🎨 Extend It

### Ask ChatGPT to add:

**More Charts:**
```
Add a renewable percentage chart showing:
- Wind
- Solar  
- Hydro
As % of total generation
```

**Google Sheets Export:**
```
Export the current data to Google Sheet:
Sheet ID: [your-sheet-id]
Update every 5 minutes
```

**Alerts:**
```
Send me an email when:
- Demand > 40,000 MW
- Balancing costs > £2M/day
- Wind generation drops below 10%
```

**Regional View:**
```
Add a map showing demand by DNO region
Use the DNO data from uk_energy_insights
```

---

## 💰 Cost Estimate

**Railway Free Tier:**
- 500 hours/month FREE
- Dashboard sleeps after 15 min idle
- Wakes in ~5 seconds

**Typical Usage:**
- Light: 2-3 hours/month ($0)
- Medium: 20-30 hours/month ($0)
- Heavy: 100+ hours/month ($0)

All within free tier! ✅

---

## 🆘 Troubleshooting

### Dashboard shows "—" for all data

**Check:**
```bash
# 1. Codex Server is running
curl https://jibber-jabber-production.up.railway.app/health

# 2. Environment variables are set
railway variables

# 3. View logs
railway logs
```

### "Codex error 502"

**Fix:**
```bash
# Verify CODEX_BASE
railway variables | grep CODEX_BASE

# Test Codex directly
curl -X POST https://jibber-jabber-production.up.railway.app/query_bigquery \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT 1 as test"}'
```

### Charts not rendering

**Check browser console (F12):**
- Look for JavaScript errors
- Verify `/api/summary` returns valid JSON
- Check if Chart.js CDN is loading

---

## 📚 Next Steps

1. ✅ Deploy to Railway (follow steps above)
2. ✅ Verify health: `https://your-url.up.railway.app/health`
3. ✅ Check API: `https://your-url.up.railway.app/api/summary`
4. ✅ View dashboard in browser
5. ✅ Tell ChatGPT to add features!

---

## 🎯 Key URLs

- **Dashboard Code**: https://github.com/GeorgeDoors888/overarch-jibber-jabber/tree/main/energy-dashboard
- **Codex Server**: https://jibber-jabber-production.up.railway.app
- **BigQuery Project**: jibber-jabber-knowledge.uk_energy_insights

---

**Status**: ✅ Ready to deploy!
**Created**: November 7, 2025
**Commit**: 5021b50
