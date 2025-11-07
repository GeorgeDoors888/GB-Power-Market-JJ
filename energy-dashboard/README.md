# UK Energy Dashboard

Live energy dashboard that connects to your Codex Server on Railway and visualizes BigQuery data from `jibber-jabber-knowledge.uk_energy_insights`.

## 🎯 Features

- **Current Demand**: Latest GB power demand
- **Generation Mix**: Fuel type breakdown (pie chart)
- **24h Demand**: Historical demand trend (line chart)
- **Top 10 BMUs**: Balancing Mechanism Units by output (bar chart)
- **Balancing Costs**: Last 30 days trend
- **Auto-refresh**: Every 5 minutes (configurable)
- **Adaptive**: Automatically detects available tables in BigQuery

## 🏗️ Architecture

```
Browser
   ↓
Energy Dashboard (FastAPI)
   ↓ HTTP POST
Codex Server (Railway)
   ↓ BigQuery API
Google BigQuery (jibber-jabber-knowledge.uk_energy_insights)
```

## 🚀 Quick Deploy to Railway

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Create New Project

```bash
cd energy-dashboard
railway init
```

### 3. Set Environment Variables

```bash
railway variables set CODEX_BASE=https://jibber-jabber-production.up.railway.app
railway variables set CODEX_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
railway variables set BQ_PROJECT=jibber-jabber-knowledge
railway variables set BQ_DATASET=uk_energy_insights
railway variables set REFRESH_MIN=5
```

### 4. Deploy

```bash
railway up
```

### 5. Get URL

```bash
railway status
```

Your dashboard will be live at: `https://your-project.up.railway.app`

## 🌐 Local Development

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CODEX_BASE=https://jibber-jabber-production.up.railway.app
export CODEX_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
export BQ_PROJECT=jibber-jabber-knowledge
export BQ_DATASET=uk_energy_insights
export REFRESH_MIN=5

# Run server
uvicorn app:app --reload --port 8000
```

Visit: http://localhost:8000

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Get dashboard data
curl http://localhost:8000/api/summary
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CODEX_BASE` | Yes | - | Codex Server URL |
| `CODEX_TOKEN` | No | - | API token for Codex (optional) |
| `BQ_PROJECT` | Yes | `jibber-jabber-knowledge` | BigQuery project ID |
| `BQ_DATASET` | Yes | `uk_energy_insights` | BigQuery dataset |
| `REFRESH_MIN` | No | `5` | Dashboard auto-refresh interval (minutes) |

### Override Table Names

If you want to use specific tables:

```bash
railway variables set TABLE_DEMAND=my_demand_table
railway variables set TABLE_FUEL=my_fuel_table
railway variables set TABLE_BMU=bmrs_data
railway variables set TABLE_BAL_COSTS=constraint_breakdown
```

## 📊 Endpoints

### `GET /`
- **Returns**: HTML dashboard with live charts
- **Refresh**: Auto-refreshes every `REFRESH_MIN` minutes

### `GET /api/summary`
- **Returns**: JSON with all dashboard data
```json
{
  "now": "2025-11-07T00:30:00Z",
  "current_demand": {"value": 35000, "unit": "MW", "ts": "..."},
  "fuel_mix": [{"fuel": "Gas", "mw": 15000}, ...],
  "demand_24h": [{"ts": "...", "demand_mw": 34000}, ...],
  "top_bmus": [{"bmu": "T_DRAXX-1", "mw": 600}, ...],
  "balancing_costs": [{"ts": "...", "cost_gbp": 1500000}, ...],
  "used_tables": {...},
  "refresh_minutes": 5
}
```

### `GET /health`
- **Returns**: `{"ok": true, "time": "..."}`

## 🔧 Advanced Usage

### Connect to ChatGPT

Once deployed, you can tell ChatGPT:

```
I have an energy dashboard at: https://your-project.up.railway.app

It connects to my Codex Server and shows UK energy data from BigQuery.

Can you:
1. Analyze the current data
2. Suggest improvements to the dashboard
3. Add a new chart for renewable percentage
```

### Add Google Sheets Export

Ask ChatGPT:

```
Can you modify my energy dashboard to also export data to Google Sheets?

Dashboard: https://your-project.up.railway.app
Sheet ID: [your-sheet-id]
```

### Schedule Alerts

```
Set up an alert system:
- If demand > 40,000 MW, send notification
- If balancing costs spike > £2M/day, alert
- Use the /api/summary endpoint to check every 5 minutes
```

## 📝 Files

```
energy-dashboard/
├── app.py              # FastAPI application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image
├── railway.json        # Railway deployment config
└── README.md          # This file
```

## 🎯 Next Steps

1. **Deploy**: Follow "Quick Deploy" above
2. **Verify**: Check `/health` and `/api/summary` endpoints
3. **View**: Open dashboard in browser
4. **Extend**: Ask ChatGPT to add features:
   - Google Sheets integration
   - Email alerts
   - More charts (renewable %, carbon intensity)
   - Regional breakdowns
   - Forecasting

## 🆘 Troubleshooting

### Dashboard shows "—" for all values

**Check:**
1. Codex Server is running: `curl https://jibber-jabber-production.up.railway.app/health`
2. Environment variables are set: `railway variables`
3. View logs: `railway logs`

### "Codex error 502"

**Fix:**
- Verify `CODEX_BASE` URL is correct
- Check `CODEX_TOKEN` if Codex requires auth
- Test Codex directly: `curl -X POST https://jibber-jabber-production.up.railway.app/query_bigquery -H "Content-Type: application/json" -d '{"sql":"SELECT 1 as test"}'`

### "BigQuery error"

**Fix:**
- Check table names in BigQuery
- Verify column names match what app.py expects
- Override table names using environment variables

### Charts not loading

**Fix:**
- Open browser console (F12)
- Check for JavaScript errors
- Verify `/api/summary` returns valid JSON
- Check Chart.js is loading (CDN might be blocked)

## 📚 Resources

- **Codex Server**: https://github.com/GeorgeDoors888/overarch-jibber-jabber/tree/main/codex-server
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Chart.js Docs**: https://www.chartjs.org/docs/

---

**Status**: ✅ Ready to deploy
**Last Updated**: November 7, 2025
