# Vercel Proxy for Railway Codex Server

## 🎯 Purpose

This Vercel Edge Function acts as a **proxy** between ChatGPT and your Railway Codex Server. It solves the network restriction issue where ChatGPT cannot directly reach Railway's domain.

---

## 🏗️ Architecture

```
ChatGPT → Vercel Edge Function → Railway Codex Server → BigQuery
         (chatgpt can reach)   (your backend)
```

**Why this works:**
- ✅ Vercel's domain is reachable by ChatGPT's browser tool
- ✅ Edge functions = fast cold starts, global anycast
- ✅ Adds security layer (SQL validation, allowlist)
- ✅ Preserves authentication to Railway

---

## 🚀 Deployment Steps

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Deploy from this directory

```bash
cd /workspaces/overarch-jibber-jabber/vercel-proxy
vercel
```

**Follow prompts:**
- Set up and deploy? **Yes**
- Link to existing project? **No** (create new)
- Project name? **railway-codex-proxy** (or your choice)
- Directory? **.** (current)

### 4. Set Environment Variables

```bash
# Set Railway base URL
vercel env add RAILWAY_BASE
# When prompted, enter: https://jibber-jabber-production.up.railway.app

# Set Codex API token
vercel env add CODEX_TOKEN
# When prompted, enter: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA

# Choose: Production, Preview, Development (select ALL)
```

### 5. Redeploy with Environment Variables

```bash
vercel --prod
```

---

## 🔗 Usage

After deployment, you'll get a URL like: `https://railway-codex-proxy.vercel.app`

### API Endpoints:

#### Health Check:
```
GET https://railway-codex-proxy.vercel.app/api/proxy?path=/health
```

#### BigQuery Query (GET):
```
GET https://railway-codex-proxy.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

#### BigQuery Query (POST):
```
POST https://railway-codex-proxy.vercel.app/api/proxy?path=/query_bigquery
Content-Type: application/json

{
  "sql": "SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_data` LIMIT 10"
}
```

#### Stack Check:
```
GET https://railway-codex-proxy.vercel.app/api/proxy?path=/run_stack_check
```

---

## 🔒 Security Features

### 1. **Path Allowlist**
Only these endpoints are allowed:
- `/health`
- `/query_bigquery_get`
- `/query_bigquery`
- `/run_stack_check`

Any other path returns 403 Forbidden.

### 2. **SQL Validation** (Enabled)
- Only `SELECT` statements allowed
- No multiple statements (`;` blocked)
- Max 5000 characters

### 3. **Size Limits**
- POST body max: 200KB
- Prevents abuse and DoS

### 4. **Authentication**
- Your `CODEX_TOKEN` is stored securely in Vercel environment
- Not exposed to clients
- Automatically added to Railway requests

### 5. **CORS Enabled**
- Allows requests from any origin (for ChatGPT access)
- Can be restricted if needed

---

## 🧪 Testing

### From Terminal:

```bash
# Health check
curl -s "https://railway-codex-proxy.vercel.app/api/proxy?path=/health" | jq

# List datasets
curl -s "https://railway-codex-proxy.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60" | jq

# POST query
curl -s -X POST "https://railway-codex-proxy.vercel.app/api/proxy?path=/query_bigquery" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT 1 as test"}' | jq
```

### From Browser:

Just paste the GET URLs directly into your browser!

---

## 📋 For ChatGPT

Once deployed, give ChatGPT this URL:

```
https://railway-codex-proxy.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

**Prompt:**
> "Use your browser tool to GET this URL and tell me what BigQuery datasets you find. This is my Vercel proxy that connects to Railway and BigQuery."

---

## 🔧 Configuration

### Environment Variables (Vercel):

| Variable | Value | Purpose |
|----------|-------|---------|
| `RAILWAY_BASE` | `https://jibber-jabber-production.up.railway.app` | Your Railway Codex Server URL |
| `CODEX_TOKEN` | `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA` | Authentication for Railway |

### Update Environment Variables:

```bash
# Update a variable
vercel env rm RAILWAY_BASE
vercel env add RAILWAY_BASE

# Redeploy
vercel --prod
```

---

## 📊 Monitoring

### Vercel Dashboard:
1. Visit https://vercel.com/dashboard
2. Select your project: **railway-codex-proxy**
3. View:
   - **Deployments** - Build status
   - **Functions** - Edge function logs
   - **Analytics** - Request metrics
   - **Settings** - Environment variables

### Check Logs:
```bash
vercel logs
```

---

## 🎯 Advantages

### vs Direct Railway Access:
- ✅ **Reachable by ChatGPT** (Vercel domain not blocked)
- ✅ **Extra security layer** (SQL validation)
- ✅ **Global edge network** (faster for ChatGPT)
- ✅ **Free tier** (500GB bandwidth/month)
- ✅ **Auto-scaling** (handles traffic spikes)

### vs Other Platforms:
- ✅ **Vercel**: Best ChatGPT compatibility (tested)
- ⚠️ Cloudflare Workers: Good but different syntax
- ⚠️ Netlify: Good but slower cold starts

---

## 🐛 Troubleshooting

### "RAILWAY_BASE not set on proxy"
**Fix:** Set environment variable and redeploy
```bash
vercel env add RAILWAY_BASE
vercel --prod
```

### "path not allowed"
**Fix:** Check the path parameter matches allowlist
- Valid: `?path=/health`
- Invalid: `?path=/some_other_endpoint`

### "only SELECT statements allowed"
**Fix:** Only use SELECT queries, not INSERT/UPDATE/DELETE
- Valid: `SELECT * FROM table`
- Invalid: `DELETE FROM table`

### "SQL too long"
**Fix:** Query exceeds 5000 characters - break into smaller queries

### ChatGPT still can't reach it
**Solution:** Test the URL yourself first:
```bash
curl "https://your-vercel.vercel.app/api/proxy?path=/health"
```
If it works for you, give ChatGPT the EXACT URL.

---

## 📚 Files in This Project

```
vercel-proxy/
├── api/
│   └── proxy.ts          # Edge function code
├── vercel.json           # Vercel configuration
├── package.json          # Node.js project metadata
└── README.md             # This file
```

---

## 💰 Costs

**Vercel Free Tier:**
- ✅ 100GB bandwidth/month
- ✅ 100GB edge network requests
- ✅ Unlimited edge function executions
- ✅ No credit card required

**Your Usage:**
- ~2KB per query
- 50,000 queries = ~100MB (well within free tier)

---

## 🔄 Updates

### Update Proxy Code:
1. Edit `api/proxy.ts`
2. Run `vercel --prod`
3. New version deployed!

### Update Railway URL:
```bash
vercel env rm RAILWAY_BASE
vercel env add RAILWAY_BASE
vercel --prod
```

---

## 🎉 Success Checklist

- [ ] Vercel CLI installed
- [ ] Logged into Vercel
- [ ] Project deployed
- [ ] Environment variables set (RAILWAY_BASE, CODEX_TOKEN)
- [ ] Redeployed with `vercel --prod`
- [ ] Tested health endpoint
- [ ] Tested BigQuery query
- [ ] Gave URL to ChatGPT
- [ ] ChatGPT successfully accessed data

---

**Deployed URL:** `https://railway-codex-proxy.vercel.app` (your actual URL will be different)

**Next Step:** Deploy and test!

```bash
cd /workspaces/overarch-jibber-jabber/vercel-proxy
vercel
```
