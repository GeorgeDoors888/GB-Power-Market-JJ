# ✅ SERVICE ACCOUNTS CREATED - Next Steps

## 🎉 What's Been Done

✅ **Service accounts created**:
- `arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com` - Runs BigQuery queries
- `github-deploy@inner-cinema-476211-u9.iam.gserviceaccount.com` - Deploys from GitHub Actions

✅ **Permissions granted**:
- `arbitrage-bq-sa`: BigQuery data viewer + job user
- `github-deploy`: Cloud Run admin, Cloud Scheduler admin, Service Account user

✅ **JSON key created**: `github-deploy-key.json` (in your repo root)

✅ **Workflow updated**: Simplified to use JSON key authentication

---

## 📋 Next: Add GitHub Secrets (5 minutes)

### Step 1: Copy the Service Account Key

```bash
# View the key contents
cat github-deploy-key.json
```

**Copy the ENTIRE contents** (it's JSON starting with `{` and ending with `}`)

### Step 2: Add to GitHub Secrets

1. Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber/settings/secrets/actions

2. Click **"New repository secret"**

3. Add these **4 secrets**:

| Secret Name | Value | Where to Get It |
|------------|-------|-----------------|
| `GCP_SA_KEY` | Contents of `github-deploy-key.json` | Paste entire JSON file |
| `GCP_PROJECT_ID` | `inner-cinema-476211-u9` | Type this exactly |
| `GCP_REGION` | `europe-west2` | Type this exactly |
| `CLOUD_RUN_SERVICE` | `arbitrage-job` | Type this exactly |
| `SERVICE_ACCOUNT_EMAIL` | `arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com` | Type this exactly |

### Step 3: Create Your Analysis Script

Create `battery_arbitrage.py` in your repo root:

```python
import os
import pathlib
from datetime import datetime
from google.cloud import bigquery
import pandas as pd

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT)

def main():
    print(f"🚀 Starting analysis at {datetime.utcnow():%Y-%m-%d %H:%M UTC}")
    
    # Example query: Last 7 days of price data
    query = f"""
    SELECT 
        DATE(settlement_date) AS date,
        settlement_period AS sp,
        AVG(system_sell_price) AS avg_sell_price,
        AVG(system_buy_price) AS avg_buy_price,
        COUNT(*) AS records
    FROM `{PROJECT}.{DATASET}.bmrs_mid`
    WHERE DATE(settlement_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY date, sp
    ORDER BY date DESC, sp
    LIMIT 336  -- 7 days * 48 periods
    """
    
    print("📊 Querying BigQuery...")
    df = client.query(query).to_dataframe()
    
    # Save results
    outdir = pathlib.Path("reports/data")
    outdir.mkdir(parents=True, exist_ok=True)
    
    output_file = outdir / f"latest_prices_{datetime.utcnow():%Y%m%d}.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✅ Analysis complete!")
    print(f"   Rows: {len(df)}")
    if len(df) > 0:
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Saved to: {output_file}")

if __name__ == "__main__":
    main()
```

---

## 🚀 Deploy!

### Option A: Quick Test (Create Script + Push)

```bash
# Create the script (copy code above into this file)
nano battery_arbitrage.py

# Add and commit all files
git add .github/workflows/deploy-cloudrun.yml cloudscheduler_job.json Dockerfile battery_arbitrage.py AUTO_REFRESH_COMPLETE.md GITHUB_ACTIONS_SETUP.md DEPLOYMENT_READY.md DOCUMENTATION_INDEX.md SETUP_COMPLETE.md

# Commit
git commit -m "Add self-refreshing BigQuery analysis pipeline"

# Push to GitHub (triggers deployment)
git push origin main
```

### Option B: Just Documentation First

If you want to add the secrets first before pushing code:

```bash
# Add documentation files only
git add .github/workflows/deploy-cloudrun.yml cloudscheduler_job.json Dockerfile AUTO_REFRESH_COMPLETE.md GITHUB_ACTIONS_SETUP.md DEPLOYMENT_READY.md DOCUMENTATION_INDEX.md SETUP_COMPLETE.md

git commit -m "Add GitHub Actions deployment configuration"

# DON'T push yet - add secrets first on GitHub
```

---

## 🔍 After Pushing - Watch It Deploy

1. Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber/actions

2. Look for the "Deploy Arbitrage Job" workflow

3. Click on it to watch the deployment (takes ~5 minutes)

4. You should see:
   - ✅ Checkout
   - ✅ Auth to Google Cloud
   - ✅ Setup gcloud
   - ✅ Enable required services
   - ✅ Build & Deploy to Cloud Run
   - ✅ Get Cloud Run URL
   - ✅ Create Cloud Scheduler job

---

## ⏰ Scheduling

The `cloudscheduler_job.json` file is configured for:
- **Schedule**: Daily at 04:00 London time
- **Retries**: Up to 3 attempts if it fails
- **Timeout**: 15 minutes per run

---

## 🔐 Security Note

**IMPORTANT**: The `github-deploy-key.json` file contains credentials!

```bash
# Add it to .gitignore so it's never committed
echo "github-deploy-key.json" >> .gitignore
git add .gitignore
git commit -m "Ignore service account key file"
```

The key is safely stored as a GitHub Secret and will never be in your repository.

---

## ✅ Success Checklist

- [ ] Copied contents of `github-deploy-key.json`
- [ ] Added 5 GitHub Secrets (GCP_SA_KEY, GCP_PROJECT_ID, GCP_REGION, CLOUD_RUN_SERVICE, SERVICE_ACCOUNT_EMAIL)
- [ ] Created `battery_arbitrage.py` script
- [ ] Added `github-deploy-key.json` to `.gitignore`
- [ ] Committed all files
- [ ] Pushed to GitHub
- [ ] Watched GitHub Actions workflow succeed
- [ ] Confirmed Cloud Run service deployed
- [ ] Confirmed Cloud Scheduler job created

---

## 📱 Test It Manually

Once deployed, force a test run:

```bash
# Get the scheduler job name
gcloud scheduler jobs list \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9

# Force run now (don't wait for 04:00)
gcloud scheduler jobs run arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9

# View logs
gcloud run services logs read arbitrage-job \
  --region=europe-west2 \
  --project=inner-cinema-476211-u9 \
  --limit=50
```

---

## 🎯 What Happens Next

Every day at 04:00 London time:
1. Cloud Scheduler triggers the Cloud Run service
2. Container starts with your `battery_arbitrage.py` script
3. Automatically authenticated to BigQuery as `arbitrage-bq-sa`
4. Queries run, results saved
5. Container shuts down (cost = £0 until next run)

**Total cost: ~£1-3/month** ✅

---

**You're almost there! Just add the GitHub Secrets and push!** 🚀
