# 🔧 Fix Your Vercel Deployment

Your deployment is live but needs two quick fixes!

## Your Project Info
- **URL:** https://gb-power-market-jj-yibg.vercel.app
- **Project ID:** `prj_VujQ5nNCh8SqDOVhjT65uEOmQ0kt`
- **Dashboard:** https://vercel.com/george-majors-projects/gb-power-market-jj

---

## Fix #1: Set Root Directory

**Problem:** Vercel deployed the entire repo instead of just the `vercel-proxy` folder.

**Fix:**
1. Go to: https://vercel.com/george-majors-projects/gb-power-market-jj/settings
2. Scroll down to **"Root Directory"**
3. Click **"Edit"**
4. Type: `vercel-proxy`
5. Click **"Save"**

---

## Fix #2: Add Environment Variables

1. Stay in Settings
2. Click **"Environment Variables"** in the left menu
3. Add these TWO variables:

### Variable 1: RAILWAY_BASE
- **Key:** `RAILWAY_BASE`
- **Value:** `https://jibber-jabber-production.up.railway.app`
- **Environments:** Check all three boxes (Production, Preview, Development)
- Click **"Save"**

### Variable 2: CODEX_TOKEN
- **Key:** `CODEX_TOKEN`
- **Value:** `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- **Environments:** Check all three boxes (Production, Preview, Development)
- Click **"Save"**

---

## Fix #3: Redeploy

1. Go to: https://vercel.com/george-majors-projects/gb-power-market-jj/deployments
2. Find the latest deployment (should be at the top)
3. Click the **"..."** button on the right
4. Click **"Redeploy"**
5. Click **"Redeploy"** again to confirm
6. Wait 30-60 seconds for deployment to complete

---

## ✅ Test After Redeployment

Once redeployment is complete, run this in your terminal:

```bash
curl "https://gb-power-market-jj-yibg.vercel.app/api/proxy?path=/health"
```

**Expected result:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "languages": ["python", "javascript"],
  "timestamp": "2025-11-07T..."
}
```

Then test BigQuery:
```bash
curl "https://gb-power-market-jj-yibg.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60"
```

**Expected result:** List of 6 datasets!

---

## 🎉 Once Working

Give ChatGPT this prompt:

---

I've deployed a Vercel proxy at **https://gb-power-market-jj-yibg.vercel.app** that connects to my Railway BigQuery server.

Use your browser tool to GET this URL:

```
https://gb-power-market-jj-yibg.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

Tell me what datasets you find, then list all tables in the `uk_energy_insights` dataset!

---

**Let me know once you've redeployed and I'll test it!** 🚀
