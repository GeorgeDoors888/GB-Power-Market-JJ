# ✅ READY TO DEPLOY - Self-Refreshing BigQuery Pipeline

**Status**: All files created ✅  
**Time to deploy**: ~20 minutes  
**Result**: Daily automated BigQuery analysis at 04:00 London time

---

## 📦 What Was Created

✅ `.github/workflows/deploy-cloudrun.yml` - GitHub Actions workflow  
✅ `cloudscheduler_job.json` - Daily schedule configuration  
✅ `Dockerfile` - Container for Cloud Run  
✅ `requirements.txt` - Already exists with all dependencies  
✅ `AUTO_REFRESH_COMPLETE.md` - Quick start guide  
✅ `GITHUB_ACTIONS_SETUP.md` - Detailed technical guide  
✅ `DOCUMENTATION_INDEX.md` - Updated with new sections

---

## 🚀 Deploy in 3 Steps

### Step 1: Create Service Accounts (Copy-paste these commands)

```bash
# 1. BigQuery service account
gcloud iam service-accounts create arbitrage-bq-sa \
  --project=inner-cinema-476211-u9 \
  --display-name="Arbitrage Runner"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# 2. GitHub OIDC setup
gcloud iam workload-identity-pools create github-pool \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

gcloud iam service-accounts create github-oidc \
  --project=inner-cinema-476211-u9 \
  --display-name="GitHub OIDC"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe inner-cinema-476211-u9 --format='value(projectNumber)')

# Allow GitHub to use this SA (replace YOUR_GITHUB_USERNAME if not GeorgeDoors888)
gcloud iam service-accounts add-iam-policy-binding \
  github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com \
  --project=inner-cinema-476211-u9 \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/GeorgeDoors888/overarch-jibber-jabber"

# Grant deployment permissions
gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/cloudscheduler.admin"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# 3. Get the Workload Identity Provider name (SAVE THIS!)
echo "=== COPY THIS VALUE FOR GITHUB SECRETS ==="
gcloud iam workload-identity-pools providers describe github-provider \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
echo "==========================================="
```

**IMPORTANT**: Copy the output from the last command. You'll need it for GitHub Secrets!

### Step 2: Add GitHub Secrets

1. Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber/settings/secrets/actions
2. Click **"New repository secret"**
3. Add these 6 secrets:

| Secret Name | Value |
|------------|-------|
| `GCP_PROJECT_ID` | `inner-cinema-476211-u9` |
| `GCP_REGION` | `europe-west2` |
| `CLOUD_RUN_SERVICE` | `arbitrage-job` |
| `SERVICE_ACCOUNT_EMAIL` | `arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com` |
| `WORKLOAD_IDENTITY_PROVIDER` | Paste the value from Step 1 (projects/xxx/...) |
| `SERVICE_ACCOUNT_FOR_GH_OIDC` | `github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com` |

### Step 3: Deploy!

```bash
# Commit and push
git add .github/workflows/deploy-cloudrun.yml cloudscheduler_job.json Dockerfile AUTO_REFRESH_COMPLETE.md GITHUB_ACTIONS_SETUP.md DEPLOYMENT_READY.md DOCUMENTATION_INDEX.md
git commit -m "Add self-refreshing BigQuery analysis pipeline"
git push origin main
```

**GitHub Actions will now**:
1. ✅ Build your container
2. ✅ Deploy to Cloud Run
3. ✅ Create daily schedule (04:00 London time)

---

## 📝 Create Your Analysis Script

You need to create `battery_arbitrage.py` (or name it whatever you want and update the `Dockerfile` CMD).

**Example starter script**:

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
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Saved to: {output_file}")

if __name__ == "__main__":
    main()
```

**Add this to your repo**:
```bash
# Create the script
nano battery_arbitrage.py
# (paste the code above, save with Ctrl+X)

# Commit and push
git add battery_arbitrage.py
git commit -m "Add BigQuery analysis script"
git push origin main
```

---

## 🔍 Verify It's Working

### Check GitHub Actions
1. Go to: https://github.com/GeorgeDoors888/overarch-jibber-jabber/actions
2. Look for "Deploy Arbitrage Job" workflow
3. Should see green checkmark ✅

### Check Cloud Run
```bash
gcloud run services describe arbitrage-job \
  --region=europe-west2 \
  --project=inner-cinema-476211-u9
```

### Check Scheduler
```bash
gcloud scheduler jobs describe arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9
```

### Force a Test Run Now
```bash
gcloud scheduler jobs run arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9
```

### View Logs
```bash
gcloud run services logs read arbitrage-job \
  --region=europe-west2 \
  --project=inner-cinema-476211-u9 \
  --limit=50
```

---

## 📱 Running from Your Phone

### Method 1: GitHub App
1. Install GitHub mobile app
2. Go to **Actions** tab
3. Tap **"Run workflow"**

### Method 2: Google Cloud Console App
1. Install "Google Cloud Console" app
2. Go to **Cloud Run** → `arbitrage-job`
3. Tap to trigger

---

## 💾 Where Do Results Go?

Currently, results are written to `reports/data/` **inside the container**.

**To persist them**, add to your script:

### Option A: Write to Google Cloud Storage
```python
from google.cloud import storage

def upload_to_gcs():
    client = storage.Client()
    bucket = client.bucket("upowerenergy-reports")  # Create this bucket first
    
    for csv_file in pathlib.Path("reports/data").glob("*.csv"):
        blob = bucket.blob(f"arbitrage/{datetime.date.today()}/{csv_file.name}")
        blob.upload_from_filename(csv_file)
        print(f"✅ Uploaded {csv_file.name} to GCS")

# Add to main():
if __name__ == "__main__":
    main()
    upload_to_gcs()
```

### Option B: Write to Google Sheets
Use your verified service account from `verify_sheets_access.gs`:
```python
import gspread
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

# Note: You'll need to mount smart_grid_credentials.json as a secret
creds = service_account.Credentials.from_service_account_file(
    'smart_grid_credentials.json', scopes=SCOPES
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet('Live Dashboard')

# Write summary
worksheet.update('A1', [['Last Updated', datetime.utcnow().isoformat()]])
```

---

## 💰 Cost Estimate

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| Cloud Run | 5 min/day @ 2GB | ~£0.50 |
| Cloud Scheduler | 1 job | Free tier |
| BigQuery | Queries only | Depends on data scanned |
| **Total** | | **~£1-3/month** |

Cloud Run scales to zero when idle!

---

## 📚 Documentation

- **`AUTO_REFRESH_COMPLETE.md`** - Quick start guide (this summary expanded)
- **`GITHUB_ACTIONS_SETUP.md`** - Full technical details
- **`API.md`** - BigQuery tables reference (391M+ rows, 2022-2025)
- **`PROJECT_IDS.md`** - Which project to use where

---

## ✅ Final Checklist

- [ ] Ran all Step 1 commands (service accounts created)
- [ ] Saved Workload Identity Provider value
- [ ] Added 6 GitHub Secrets
- [ ] Created `battery_arbitrage.py` script
- [ ] Committed and pushed all files
- [ ] GitHub Actions workflow succeeded
- [ ] Cloud Run service deployed
- [ ] Cloud Scheduler job created
- [ ] Tested with manual trigger
- [ ] Checked logs show successful query
- [ ] (Optional) Set up GCS/Sheets output persistence

---

## 🎯 What You Get

✅ **Always-live data** - Pulls fresh BigQuery data daily  
✅ **Zero maintenance** - Runs automatically at 04:00 London time  
✅ **Mobile control** - Trigger from GitHub or Cloud Console apps  
✅ **Secure** - No JSON keys stored anywhere (Workload Identity)  
✅ **Cost efficient** - Scales to zero, ~£1-3/month  
✅ **Reproducible** - All code in Git, all runs logged  

---

**🎉 You're ready to deploy! Follow the 3 steps above and you'll have a self-refreshing pipeline in 20 minutes.**

Questions? Check:
- `AUTO_REFRESH_COMPLETE.md` for quick answers
- `GITHUB_ACTIONS_SETUP.md` for troubleshooting
- `DOCUMENTATION_INDEX.md` for all docs
