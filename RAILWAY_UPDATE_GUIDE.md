# 🚂 Railway Environment Variable Update Guide

## Step-by-Step: How to Update BQ_PROJECT_ID in Railway

### Current Location:
You're in: **Project Settings** (General tab)

### Where to Go:
You need to find the **SERVICE** (not project settings), then go to its Variables tab.

---

## Step 1: Navigate to the Service

1. **Click the back/close button** to exit Project Settings
2. You should see the **Railway Dashboard** with your services/deployments
3. Look for a service named something like:
   - `jibber-jabber` or
   - `api-gateway` or
   - `driveindexer` or
   - Just a deployment card/box

---

## Step 2: Click on the Service Card

When you're back on the main project view, you should see one or more **service cards** (boxes showing your deployments).

Click on the service card that handles the API (likely the one running `api_gateway.py`).

---

## Step 3: Find the Variables Tab

Once inside the service, you should see tabs like:
- **Settings**
- **Variables** ← Click this one!
- **Deployments**
- **Metrics**
- **Logs**

Click on **"Variables"**

---

## Step 4: Look for BQ_PROJECT_ID

In the Variables section, you should see a list of environment variables. Look for:

```
BQ_PROJECT_ID = jibber-jabber-knowledge
```

---

## Step 5: Update the Variable

**Option A: If you see BQ_PROJECT_ID:**
1. Click on the variable or the edit/pencil icon
2. Change the value from `jibber-jabber-knowledge` to `inner-cinema-476211-u9`
3. Click Save

**Option B: If you DON'T see BQ_PROJECT_ID:**
1. Click "+ New Variable" or "Add Variable"
2. Variable name: `BQ_PROJECT_ID`
3. Variable value: `inner-cinema-476211-u9`
4. Click Add/Save

---

## Step 6: The Service Will Auto-Redeploy

After saving the variable:
- Railway will automatically trigger a new deployment
- Wait 1-2 minutes for the deployment to complete
- The service will restart with the new configuration

---

## Step 7: Verify the Change

After deployment completes, test it:

```bash
# Run this in your terminal:
curl "https://jibber-jabber-production.up.railway.app/query_bigquery_get?sql=SELECT%20COUNT(*)%20as%20cnt%20FROM%20\`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\`"
```

**Expected result:**
```json
{
  "success": true,
  "data": [{"cnt": <some number>}],
  ...
}
```

If you see `"success": true`, it worked! 🎉

---

## Visual Guide

```
Railway Dashboard
├── Project Settings (← You are here now - GO BACK)
└── Service Card(s)
    ├── Click on service →
    └── Tabs appear:
        ├── Settings
        ├── Variables ← GO HERE
        ├── Deployments
        ├── Metrics
        └── Logs
```

---

## What to Look For

### Service Card Appearance:
```
┌─────────────────────────────┐
│  🚂 jibber-jabber           │
│  ✅ Deployed                │
│  https://jibber-jabber...   │
└─────────────────────────────┘
```

### Variables Tab:
```
Environment Variables

+ New Variable

Name                    Value
BQ_PROJECT_ID          jibber-jabber-knowledge  ← Change this!
BQ_DATASET             uk_energy_prod
GOOGLE_CREDENTIALS     { ... }
```

---

## Troubleshooting

### Can't find Variables tab?
- Make sure you clicked on the **service card** (not project settings)
- The service card is on the main dashboard view

### Don't see BQ_PROJECT_ID in variables?
- Add it manually as a new variable
- Name: `BQ_PROJECT_ID`
- Value: `inner-cinema-476211-u9`

### Multiple services showing?
- Look for the one with the URL: `jibber-jabber-production.up.railway.app`
- Or the one that has Python/API-related variables

---

## After Update

Once you've updated `BQ_PROJECT_ID` to `inner-cinema-476211-u9`:

1. **Wait** for auto-deployment (1-2 minutes)
2. **Test** the curl command above
3. **Go to Google Sheet** and click: ⚡ Power Market → 🔄 Refresh Now
4. **Check** Live Dashboard for SSP, SBP, BOALF, BOD data
5. **Celebrate!** 🎉 All data should now appear!

---

## Quick Navigation Steps

From where you are now:

1. Click **"← Back"** or close settings
2. You should see **service card(s)** on the dashboard
3. Click on the **service card**
4. Click **"Variables"** tab
5. Find or add **BQ_PROJECT_ID**
6. Set value to **inner-cinema-476211-u9**
7. Save
8. Done!
