# 🚀 Quick Start - Deploy Vercel Proxy for ChatGPT

## ⚡ 5-Minute Setup

This proxy solves the "ChatGPT can't reach Railway" problem by putting a Vercel Edge Function in the middle.

---

## 📋 Prerequisites

- ✅ GitHub account (for Vercel login)
- ✅ Your Railway Codex Server running
- ✅ 5 minutes

---

## 🎯 Step-by-Step

### 1️⃣ Install Vercel CLI

```bash
npm install -g vercel
```

**Or if npm is slow:**
```bash
curl -sf https://vercel.com/install | sh
```

### 2️⃣ Go to the Proxy Directory

```bash
cd /workspaces/overarch-jibber-jabber/vercel-proxy
```

### 3️⃣ Login to Vercel

```bash
vercel login
```

**Follow prompts:**
- Opens browser → Login with GitHub
- Confirm in terminal

### 4️⃣ Deploy

```bash
./deploy.sh
```

**OR manually:**
```bash
vercel
```

**Answer prompts:**
- Set up and deploy? **Y**
- Link to existing project? **N**
- Project name? **railway-codex-proxy** (or your choice)
- In which directory is your code located? **./**

### 5️⃣ Set Environment Variables

**Option A - Automated:**
```bash
./setup-env.sh
```

**Option B - Manual:**
```bash
# Set Railway URL
vercel env add RAILWAY_BASE
# → Enter: https://jibber-jabber-production.up.railway.app
# → Select: Production, Preview, Development (all)

# Set API token
vercel env add CODEX_TOKEN
# → Enter: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
# → Select: Production, Preview, Development (all)

# Redeploy with environment variables
vercel --prod
```

### 6️⃣ Get Your URL

```bash
vercel inspect --prod
```

**Example output:**
```
URL: https://railway-codex-proxy-xyz123.vercel.app
```

### 7️⃣ Test It!

```bash
# Test health endpoint
curl "https://railway-codex-proxy-xyz123.vercel.app/api/proxy?path=/health"

# Test BigQuery
curl "https://railway-codex-proxy-xyz123.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60"
```

**Expected Response:**
```json
{
  "success": true,
  "data": [
    {"schema_name": "uk_energy_insights"},
    {"schema_name": "bmrs_data"},
    ...
  ],
  "row_count": 6
}
```

---

## 🎉 Success!

Your proxy is now live and ChatGPT can access it!

### Give ChatGPT This URL:

```
https://railway-codex-proxy-xyz123.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

**Prompt for ChatGPT:**

> I've deployed a Vercel proxy for my Railway BigQuery server. Use your browser tool to GET this URL and tell me what datasets you find:
>
> https://railway-codex-proxy-xyz123.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60

---

## 🔧 Common Commands

### View Deployment URL:
```bash
vercel inspect --prod
```

### View Logs:
```bash
vercel logs
```

### Redeploy:
```bash
vercel --prod
```

### Update Environment Variable:
```bash
vercel env rm RAILWAY_BASE
vercel env add RAILWAY_BASE
vercel --prod
```

---

## 🐛 Troubleshooting

### "vercel: command not found"
**Fix:** Install globally
```bash
npm install -g vercel
# OR
curl -sf https://vercel.com/install | sh
```

### "Not logged in"
**Fix:**
```bash
vercel login
```

### "RAILWAY_BASE not set on proxy"
**Fix:** Environment variable missing
```bash
vercel env add RAILWAY_BASE
vercel --prod
```

### Proxy returns error but Railway works
**Fix:** Check environment variables
```bash
vercel env ls
# Should see RAILWAY_BASE and CODEX_TOKEN
```

---

## 📊 Monitoring

### Vercel Dashboard:
https://vercel.com/dashboard

**View:**
- Deployments (build status)
- Functions (logs and metrics)
- Analytics (requests/bandwidth)
- Settings (environment variables)

---

## 💰 Cost

**Free Tier:**
- ✅ Unlimited edge function executions
- ✅ 100GB bandwidth/month
- ✅ 100GB edge network requests
- ✅ Global CDN
- ✅ No credit card required

**Your Expected Usage:**
- ~2KB per query
- Even 50,000 queries = ~100MB (well within free)

---

## 🔐 Security

### Enabled by Default:
- ✅ **SQL Validation** - Only SELECT queries allowed
- ✅ **Path Allowlist** - Only 4 endpoints exposed
- ✅ **Size Limits** - Max 200KB POST body
- ✅ **Token Hidden** - CODEX_TOKEN not exposed to clients
- ✅ **HTTPS Only** - All traffic encrypted

---

## ✅ Success Checklist

- [ ] Vercel CLI installed
- [ ] Logged into Vercel (`vercel whoami` works)
- [ ] Deployed (`vercel` command succeeded)
- [ ] Environment variables set (RAILWAY_BASE, CODEX_TOKEN)
- [ ] Redeployed with `vercel --prod`
- [ ] Tested health endpoint (returns `{"status":"healthy"}`)
- [ ] Tested BigQuery query (returns datasets)
- [ ] Saved Vercel URL for ChatGPT
- [ ] Tested with ChatGPT (it can reach the proxy)

---

## 🎯 Next Steps

1. ✅ Deploy proxy (you're here!)
2. ⏭️ Test with ChatGPT
3. ⏭️ Build Custom GPT with your data schema
4. ⏭️ Automate data analysis workflows

---

**Ready? Let's deploy!**

```bash
cd /workspaces/overarch-jibber-jabber/vercel-proxy
./deploy.sh
```
