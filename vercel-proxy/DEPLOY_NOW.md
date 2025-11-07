# 🚀 Deploy Vercel Proxy NOW - Simple 3-Step Guide

## Current Status
✅ Code ready and committed to GitHub  
✅ Vercel CLI installed (version 48.8.2)  
⚠️ Need to complete deployment

---

## STEP 1: Login to Vercel

Run this command:
```bash
vercel login
```

When you see a device code like `XXXX-XXXX`:
1. Open your tablet browser
2. Go to: **https://vercel.com/device**
3. Enter the code shown
4. Approve the device

**Wait for:** ✅ Logged in to Vercel

---

## STEP 2: Deploy (Do this IMMEDIATELY after login)

As soon as you see "✅ Logged in", run:
```bash
vercel
```

Answer the prompts:
- **Set up and deploy?** → `yes` (or just press ENTER)
- **Which scope?** → Select your account (press ENTER)
- **Link to existing project?** → `n` (new project)
- **Project name?** → Type: `railway-codex-proxy` (or press ENTER)
- **In which directory is your code?** → Press ENTER (current directory)
- **Want to modify settings?** → `n` (no)

**Wait for:** Deployment URL like `https://railway-codex-proxy-abc123.vercel.app`

**⚠️ IMPORTANT:** Copy this URL! You'll need it.

---

## STEP 3: Set Environment Variables

Run these commands one at a time:

### Set Railway URL:
```bash
vercel env add RAILWAY_BASE production
```
When prompted for value, paste:
```
https://jibber-jabber-production.up.railway.app
```

### Set Codex Token:
```bash
vercel env add CODEX_TOKEN production
```
When prompted for value, paste:
```
codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA
```

### Deploy to Production:
```bash
vercel --prod
```

**Wait for:** Production URL (this is your final URL)

---

## STEP 4: Test It

Replace `YOUR-URL` with your actual Vercel URL:

```bash
curl "https://YOUR-URL.vercel.app/api/proxy?path=/health"
```

**Expected:** `{"status":"healthy"...}`

Then test BigQuery:
```bash
curl "https://YOUR-URL.vercel.app/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60"
```

**Expected:** List of 6 datasets

---

## ⚠️ If You Get "Token is not valid" Error

This means too much time passed between login and deployment. Solution:

1. Run `vercel login` again
2. Authenticate on tablet again
3. **IMMEDIATELY** run `vercel` (don't wait!)

---

## 📋 Quick Copy-Paste Commands

```bash
# 1. Login
vercel login

# 2. Deploy (IMMEDIATELY after login)
vercel

# 3. Set Railway URL
vercel env add RAILWAY_BASE production
# Paste: https://jibber-jabber-production.up.railway.app

# 4. Set Token
vercel env add CODEX_TOKEN production
# Paste: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA

# 5. Production Deploy
vercel --prod
```

---

## ✅ Success Looks Like

```
✅ Deployed to https://railway-codex-proxy-abc123.vercel.app
✅ Production: https://railway-codex-proxy.vercel.app
```

Then you can give ChatGPT this URL and it will work! 🎉

---

## 🆘 Need Help?

If you get stuck, paste the exact error message and I'll help troubleshoot.

**Ready?** Start with: `vercel login`
