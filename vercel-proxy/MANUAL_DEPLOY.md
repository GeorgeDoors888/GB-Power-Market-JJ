# 🔧 Manual Vercel Deployment (Token Issue Workaround)

## The Problem
Vercel CLI authentication tokens aren't persisting in this Codespace environment, causing an infinite login loop.

## ✅ Solution: Deploy via Vercel Dashboard (Web UI)

This is actually **easier** and takes **2 minutes**!

---

## Step 1: Connect GitHub to Vercel

1. **On your tablet**, go to: **https://vercel.com/new**
2. Click **"Continue with GitHub"**
3. Authorize Vercel to access your GitHub

---

## Step 2: Import Your Project

1. You'll see a list of your GitHub repositories
2. Find: **GeorgeDoors888/overarch-jibber-jabber**
3. Click **"Import"** next to it

---

## Step 3: Configure Project

**Root Directory:**
- Click **"Edit"** next to Root Directory
- Type: `vercel-proxy`
- This tells Vercel to deploy only the proxy folder

**Framework Preset:**
- Leave as **"Other"** (it will auto-detect)

**Build Settings:**
- Leave everything as default

---

## Step 4: Add Environment Variables

Click **"Environment Variables"** to expand, then add these **two** variables:

### Variable 1:
- **Name:** `RAILWAY_BASE`
- **Value:** `https://jibber-jabber-production.up.railway.app`
- **Environment:** Select all three (Production, Preview, Development)

### Variable 2:
- **Name:** `CODEX_TOKEN`
- **Value:** `codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA`
- **Environment:** Select all three (Production, Preview, Development)

---

## Step 5: Deploy!

1. Click **"Deploy"** button at the bottom
2. Wait ~60 seconds for build to complete
3. You'll see: **"Congratulations! Your project has been deployed."**

---

## Step 6: Get Your URL

After deployment:
1. Click **"Visit"** or copy the URL shown
2. It will look like: `https://overarch-jibber-jabber-vercel-proxy.vercel.app`

---

## Step 7: Test It

Replace `YOUR-URL` with your actual Vercel URL:

```bash
curl "https://YOUR-URL.vercel.app/api/proxy?path=/health"
```

**Expected response:**
```json
{"status":"healthy","version":"1.0.0"...}
```

Then test BigQuery:
```bash
curl "https://YOUR-URL.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60"
```

**Expected:** List of 6 datasets!

---

## 🎉 Done!

Now give ChatGPT your Vercel URL and it can access your BigQuery data!

**Example prompt for ChatGPT:**

---

I've deployed a Vercel proxy at `https://YOUR-URL.vercel.app` that connects to my Railway BigQuery server.

Use your browser tool to GET this URL and tell me what datasets you find:

```
https://YOUR-URL.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60
```

Then list all tables in the `uk_energy_insights` dataset!

---

## 📝 Notes

- **Free tier:** Unlimited requests, no credit card needed
- **Auto-deploys:** Any push to GitHub will automatically redeploy
- **Custom domain:** You can add your own domain later in Vercel settings

**This is actually the BETTER way to deploy!** 🚀
