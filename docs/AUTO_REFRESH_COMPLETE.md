# ✅ Self-Refreshing BigQuery Analysis - Complete Setup

**Status**: Ready to deploy  
**Project**: inner-cinema-476211-u9  
**Repository**: overarch-jibber-jabber  
**Purpose**: Automatically run BigQuery analysis daily and keep results always fresh

---

## 🎯 What You Now Have

### Files Created ✅
1. **`.github/workflows/deploy-cloudrun.yml`** - GitHub Actions workflow
2. **`cloudscheduler_job.json`** - Scheduler configuration (04:00 London time)
3. **`Dockerfile`** - Container definition for Cloud Run
4. **`requirements.txt`** - Already exists with all dependencies ✅
5. **`GITHUB_ACTIONS_SETUP.md`** - Complete setup guide

### How It Works 🔄

```
GitHub Push → Actions Build → Cloud Run Deploy → Scheduler (Daily 04:00)
     ↓              ↓                ↓                    ↓
  Your Code    Container       Auto-auth BigQuery    Fresh Reports
```

---

## ⚡ Quick Start (5 Steps)

### 1️⃣ Create Service Accounts (5 min)

```bash
# Service account for BigQuery access
gcloud iam service-accounts create arbitrage-bq-sa \
  --project=inner-cinema-476211-u9 \
  --display-name="Arbitrage Runner"

# Grant permissions
gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### 2️⃣ Setup GitHub Authentication (10 min)

```bash
# Create Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create OIDC provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create GitHub service account
gcloud iam service-accounts create github-oidc \
  --project=inner-cinema-476211-u9 \
  --display-name="GitHub OIDC"

# Get your project number
PROJECT_NUMBER=$(gcloud projects describe inner-cinema-476211-u9 --format='value(projectNumber)')

# Replace YOUR_GITHUB_USERNAME with: GeorgeDoors888
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

# Get the provider name (save this for GitHub Secrets)
gcloud iam workload-identity-pools providers describe github-provider \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

**Copy the output** - it looks like: `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

### 3️⃣ Add GitHub Secrets (2 min)

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|------------|-------|
| `GCP_PROJECT_ID` | `inner-cinema-476211-u9` |
| `GCP_REGION` | `europe-west2` |
| `CLOUD_RUN_SERVICE` | `arbitrage-job` |
| `SERVICE_ACCOUNT_EMAIL` | `arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com` |
| `WORKLOAD_IDENTITY_PROVIDER` | *Paste output from step 2* |
| `SERVICE_ACCOUNT_FOR_GH_OIDC` | `github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com` |

### 4️⃣ Create Your Analysis Script

Create `battery_arbitrage.py` (or use your existing script):

```python
import os
import pathlib
from google.cloud import bigquery
import pandas as pd

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT)

def main():
    # Your BigQuery analysis here
    query = f"""
    SELECT 
        DATE(settlement_date) AS d,
        settlement_period AS sp,
        AVG(system_sell_price) AS avg_ssp,
        AVG(system_buy_price) AS avg_sbp
    FROM `{PROJECT}.{DATASET}.bmrs_mid`
    WHERE DATE(settlement_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY d, sp
    ORDER BY d DESC, sp
    """
    
    df = client.query(query).to_dataframe()
    
    # Save results
    outdir = pathlib.Path("reports/data")
    outdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(outdir / "latest_prices.csv", index=False)
    
    print(f"✅ Analysis complete. Saved {len(df)} rows.")

if __name__ == "__main__":
    main()
```

### 5️⃣ Deploy!

```bash
# Commit all files
git add .github/workflows/deploy-cloudrun.yml cloudscheduler_job.json Dockerfile battery_arbitrage.py
git commit -m "Add self-refreshing BigQuery analysis pipeline"
git push origin main
```

**GitHub Actions will now**:
- ✅ Build your container
- ✅ Deploy to Cloud Run (with auto-auth)
- ✅ Create daily schedule (04:00 London time)

---

## 📱 Running from Your Phone

### Method 1: GitHub App
1. Open GitHub mobile app
2. Go to **Actions** tab
3. Select "Deploy Arbitrage Job"
4. Tap **"Run workflow"**

### Method 2: Cloud Console App
1. Download **Google Cloud Console** app (iOS/Android)
2. Go to **Cloud Run** → `arbitrage-job`
3. Tap the URL to trigger manually

### Method 3: Trigger via URL (iOS Shortcut)
Once deployed, you can hit the Cloud Run URL from anywhere:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "https://arbitrage-job-XXXX.a.run.app"
```

---

## 🔍 Monitoring & Debugging

### Check if it's running
```bash
# View Cloud Run service status
gcloud run services describe arbitrage-job \
  --region=europe-west2 \
  --project=inner-cinema-476211-u9

# Check scheduler job
gcloud scheduler jobs describe arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9

# View recent logs
gcloud run services logs read arbitrage-job \
  --region=europe-west2 \
  --project=inner-cinema-476211-u9 \
  --limit=50
```

### Force run now (don't wait for 04:00)
```bash
gcloud scheduler jobs run arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9
```

### Check last run status
```bash
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=arbitrage-refresh" \
  --project=inner-cinema-476211-u9 \
  --limit=10 \
  --format=json
```

---

## 💰 Costs (Estimated)

| Service | Usage | Monthly Cost |
|---------|-------|-------------|
| Cloud Run | 5 min/day @ 2GB | ~£0.50 |
| Cloud Scheduler | 1 job | Free tier |
| BigQuery | Queries only | Depends on query size |
| **Total** | | **~£1-3/month** |

Cloud Run scales to zero when idle, so you only pay during the 5-10 minutes it runs each day.

---

## 🎓 How Auto-Authentication Works

No JSON keys stored anywhere! Here's the flow:

```
GitHub Action starts
    ↓
Uses Workload Identity Federation (OIDC token)
    ↓
Authenticates as github-oidc@... service account
    ↓
Deploys Cloud Run with arbitrage-bq-sa@... service account
    ↓
Cloud Run automatically gets BigQuery credentials via metadata server
    ↓
Your Python code: bigquery.Client() ← Works automatically!
```

**Key point**: The `google-cloud-bigquery` library automatically uses Application Default Credentials (ADC) from the Cloud Run environment. No `GOOGLE_APPLICATION_CREDENTIALS` file needed!

---

## 📊 Next Steps - Extend the Pipeline

### Option A: Write to Google Drive
Add to your script:
```python
from google.cloud import storage

def upload_to_gcs():
    client = storage.Client()
    bucket = client.bucket("upowerenergy-reports")
    blob = bucket.blob(f"arbitrage/{datetime.date.today()}/latest_prices.csv")
    blob.upload_from_filename("reports/data/latest_prices.csv")
```

### Option B: Update Google Sheets
Use the service account you already verified:
```python
import gspread
from google.oauth2.service_account import Credentials

# Cloud Run will have ADC, but for Sheets you need explicit scope
# Use your smart_grid_credentials.json mounted as secret
creds = Credentials.from_service_account_file(
    'smart_grid_credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)
sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
worksheet = sheet.worksheet('Live Dashboard')
worksheet.update('A1', [[df.to_csv(index=False)]])
```

### Option C: Send Email Reports
Add SendGrid or Gmail API to email yourself a PDF summary.

---

## ✅ Success Checklist

- [ ] Service accounts created (`arbitrage-bq-sa`, `github-oidc`)
- [ ] Workload Identity Federation configured
- [ ] GitHub Secrets added (6 secrets)
- [ ] All files committed and pushed
- [ ] GitHub Actions workflow succeeded (green checkmark)
- [ ] Cloud Run service deployed
- [ ] Cloud Scheduler job created (04:00 London time)
- [ ] Tested with manual trigger
- [ ] Checked logs show BigQuery queries executing
- [ ] CSV outputs appear in `reports/data/`
- [ ] (Optional) Connected to Drive/Sheets for output storage

---

## 🆘 Troubleshooting

### "Permission denied" on BigQuery
```bash
# Verify service account has correct roles
gcloud projects get-iam-policy inner-cinema-476211-u9 \
  --flatten="bindings[].members" \
  --filter="bindings.members:arbitrage-bq-sa@"
```

Expected output should show:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`

### GitHub Actions fails at "Auth to Google Cloud"
- Check `WORKLOAD_IDENTITY_PROVIDER` secret is correct full path
- Verify `github-oidc` service account has `workloadIdentityUser` role
- Confirm repository name exactly matches: `GeorgeDoors888/overarch-jibber-jabber`

### Cloud Run builds but query fails
```bash
# Check Cloud Run logs for actual error
gcloud run services logs read arbitrage-job \
  --region=europe-west2 \
  --project=inner-cinema-476211-u9 \
  --limit=100 | grep ERROR
```

Common issues:
- Table name typo (check `uk_energy_prod.bmrs_mid` vs `uk_energy_insights`)
- Wrong project ID (use `inner-cinema-476211-u9`, not `jibber-jabber-knowledge`)
- Column name mismatch (see `API.md` for correct schema)

### Scheduler not triggering
```bash
# Check job is enabled
gcloud scheduler jobs describe arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9 \
  --format="value(state)"
```

Should show `ENABLED`. If `PAUSED`:
```bash
gcloud scheduler jobs resume arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9
```

---

## 📚 Related Documentation

- **`API.md`** - BigQuery dataset reference (391M+ rows, 200+ tables)
- **`PROJECT_IDS.md`** - Which project ID to use where
- **`GITHUB_ACTIONS_SETUP.md`** - This guide (detailed version)
- **`verify_chatgpt_sheets_integration.py`** - Service account verification (already passed ✅)

---

## 🎯 Summary

You now have:

✅ **Auto-authentication** - No JSON keys needed  
✅ **Daily refresh** - Runs at 04:00 London time automatically  
✅ **Mobile control** - Trigger runs from your phone  
✅ **Always live** - Results stay current without manual intervention  
✅ **Fully audited** - All runs logged in Cloud Logging  
✅ **Cost efficient** - Only runs 5-10 min/day (~£1-3/month)  

**ChatGPT can write code for you**, but this infrastructure now **runs it automatically** even when you're not around! 🚀

---

**Questions?** Check `GITHUB_ACTIONS_SETUP.md` for the full detailed guide.
