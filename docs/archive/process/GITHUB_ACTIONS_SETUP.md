# GitHub Actions Auto-Deploy Setup Guide

This guide shows you how to configure your GitHub repository to automatically deploy your BigQuery analysis code to Google Cloud Run with daily scheduled refreshes.

## 📋 What This Does

When you push code to `main`:
1. **GitHub Actions** builds your Python container
2. **Cloud Run** deploys it with auto-authentication to BigQuery
3. **Cloud Scheduler** runs it daily at 04:00 London time
4. **Results** are written to `reports/data/` (can be pushed to GCS or Drive)

## 🔑 Step 1: Create Service Account

```bash
# Create the service account that will run your BigQuery jobs
gcloud iam service-accounts create arbitrage-bq-sa \
  --project=inner-cinema-476211-u9 \
  --description="Runs BigQuery arbitrage analysis" \
  --display-name="Arbitrage Runner"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Grant Cloud Storage permissions (for writing outputs)
gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## 🔐 Step 2: Setup Workload Identity Federation (GitHub OIDC)

This allows GitHub Actions to authenticate to Google Cloud without storing JSON keys.

```bash
# Create a Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --display-name="GitHub Actions Pool"

# Create a provider in that pool
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create a service account for GitHub to impersonate
gcloud iam service-accounts create github-oidc \
  --project=inner-cinema-476211-u9 \
  --description="Service account for GitHub Actions" \
  --display-name="GitHub OIDC"

# Allow GitHub to impersonate this service account
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
gcloud iam service-accounts add-iam-policy-binding github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com \
  --project=inner-cinema-476211-u9 \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe inner-cinema-476211-u9 --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_USERNAME/overarch-jibber-jabber"

# Grant this service account permissions to deploy Cloud Run and manage Scheduler
gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/cloudscheduler.admin"

gcloud projects add-iam-policy-binding inner-cinema-476211-u9 \
  --member="serviceAccount:github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Get the Workload Identity Provider name (you'll need this for GitHub Secrets)
gcloud iam workload-identity-pools providers describe github-provider \
  --project=inner-cinema-476211-u9 \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

Copy the output from the last command — it looks like:
```
projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

## 🔧 Step 3: Configure GitHub Secrets

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `GCP_PROJECT_ID` | `inner-cinema-476211-u9` | Your GCP project ID |
| `GCP_REGION` | `europe-west2` | London region |
| `CLOUD_RUN_SERVICE` | `arbitrage-job` | Name for your Cloud Run service |
| `SERVICE_ACCOUNT_EMAIL` | `arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com` | SA that runs BigQuery |
| `WORKLOAD_IDENTITY_PROVIDER` | `projects/123.../github-provider` | From Step 2 output |
| `SERVICE_ACCOUNT_FOR_GH_OIDC` | `github-oidc@inner-cinema-476211-u9.iam.gserviceaccount.com` | SA for GitHub auth |

## 📦 Step 4: Add Required Files to Your Repo

These files have already been created:

- `.github/workflows/deploy-cloudrun.yml` ✅
- `cloudscheduler_job.json` ✅
- `Dockerfile` (create next)
- `requirements.txt` (create next)
- `battery_arbitrage.py` (your analysis script)

## 🐳 Step 5: Create Dockerfile

Create `Dockerfile` in your repo root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Run the analysis script
CMD ["python", "battery_arbitrage.py"]
```

## 📝 Step 6: Create requirements.txt

Create `requirements.txt` in your repo root:

```
google-cloud-bigquery
google-cloud-storage
pandas
numpy
matplotlib
scipy
statsmodels
db-dtypes
pyarrow
```

## ▶️ Step 7: Test Locally First

Before pushing to GitHub, test locally:

```bash
# Authenticate
gcloud auth application-default login
gcloud config set project inner-cinema-476211-u9

# Run your script
python3 battery_arbitrage.py

# Check outputs
ls -lh reports/data/
```

## 🚀 Step 8: Deploy

```bash
# Commit and push
git add .github/workflows/deploy-cloudrun.yml cloudscheduler_job.json Dockerfile requirements.txt
git commit -m "Add GitHub Actions auto-deploy pipeline"
git push origin main
```

GitHub Actions will:
1. ✅ Build your container
2. ✅ Deploy to Cloud Run
3. ✅ Create Cloud Scheduler job (runs daily at 04:00 London time)

## 📱 Step 9: Trigger from Your Phone (Optional)

To manually trigger a run from your phone:

### Option A: GitHub App
1. Open GitHub mobile app
2. Go to your repo → Actions
3. Select "Deploy Arbitrage Job"
4. Click "Run workflow"

### Option B: iOS Shortcut (curl)
Create a shortcut with this command (requires gcloud CLI on your phone):

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token \
  --impersonate-service-account=arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com)" \
  "https://YOUR-CLOUD-RUN-URL"
```

Replace `YOUR-CLOUD-RUN-URL` with the URL from Cloud Run console.

## 🔍 Monitoring

### View Logs
```bash
# Cloud Run logs
gcloud run services logs read arbitrage-job \
  --project=inner-cinema-476211-u9 \
  --region=europe-west2 \
  --limit=50

# Scheduler logs
gcloud logging read "resource.type=cloud_scheduler_job" \
  --project=inner-cinema-476211-u9 \
  --limit=20 \
  --format=json
```

### Check Schedule Status
```bash
gcloud scheduler jobs describe arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9
```

### Force Run Now
```bash
gcloud scheduler jobs run arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9
```

## 🔧 Troubleshooting

### "Permission denied" errors
```bash
# Check service account has correct roles
gcloud projects get-iam-policy inner-cinema-476211-u9 \
  --flatten="bindings[].members" \
  --filter="bindings.members:arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com"
```

### "Workload Identity Federation" errors
```bash
# Verify GitHub OIDC setup
gcloud iam workload-identity-pools providers describe github-provider \
  --workload-identity-pool=github-pool \
  --location=global \
  --project=inner-cinema-476211-u9
```

### Scheduler not running
```bash
# Check job exists
gcloud scheduler jobs list \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9

# View recent attempts
gcloud scheduler jobs describe arbitrage-refresh \
  --location=europe-west2 \
  --project=inner-cinema-476211-u9 \
  --format="value(status.lastAttemptTime, status.code)"
```

## 💾 Writing Outputs to Drive

To automatically upload results to Google Drive, modify your `battery_arbitrage.py`:

```python
from google.cloud import storage
import datetime

# At the end of your script:
def upload_to_gcs():
    client = storage.Client()
    bucket = client.bucket("upowerenergy-reports")  # Create this bucket first
    
    # Upload all CSVs
    for csv_file in pathlib.Path("reports/data").glob("*.csv"):
        blob = bucket.blob(f"arbitrage/{datetime.date.today()}/{csv_file.name}")
        blob.upload_from_filename(csv_file)
        print(f"✅ Uploaded {csv_file.name} to GCS")

if __name__ == "__main__":
    main()
    upload_to_gcs()
```

## ✅ Success Checklist

- [ ] Service accounts created with correct permissions
- [ ] Workload Identity Federation configured
- [ ] GitHub Secrets set
- [ ] Dockerfile and requirements.txt in repo
- [ ] Tested script locally (produces CSVs)
- [ ] Committed and pushed to GitHub
- [ ] GitHub Actions workflow succeeded
- [ ] Cloud Run service deployed
- [ ] Cloud Scheduler job created
- [ ] First scheduled run completed (check logs next morning)

## 📚 Related Documentation

- `API.md` - BigQuery data reference (391M+ rows, 2022-2025)
- `PROJECT_IDS.md` - Correct project IDs to use
- `DOCUMENTATION_INDEX.md` - All project docs

## 🎯 What You Get

✅ **Always-live data**: Pulls fresh BigQuery data daily  
✅ **Zero maintenance**: Runs automatically, no manual triggers  
✅ **Mobile access**: Trigger ad-hoc runs from your phone  
✅ **Audit trail**: All runs logged in Cloud Logging  
✅ **Cost efficient**: Cloud Run scales to zero when idle (~£1-5/month)  
✅ **Reproducible**: Exact code version tracked in Git commits  

---

**Next Steps**: After setup, wait until tomorrow morning and check `reports/data/` or your GCS bucket for fresh outputs!
