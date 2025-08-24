# Dashboard Deployment Guide

## Overview

This document outlines the steps required to deploy the UK Energy Dashboard to production. The dashboard uses Streamlit and connects to BigQuery to visualize energy data from various UK sources.

## Prerequisites

- Google Cloud project with BigQuery enabled
- Google Cloud SDK installed and configured
- Docker installed (for local testing)
- Proper IAM permissions to deploy to Cloud Run

## Deployment Steps

### 1. Build and Deploy to Cloud Run

The simplest way to deploy is to use the provided deployment script:

```bash
./deploy_dashboard.sh [PROJECT_ID]
```

This script will:
1. Build the Docker image for the dashboard
2. Push it to Google Container Registry
3. Deploy it to Cloud Run with appropriate settings

### 2. Manual Deployment

If you prefer to deploy manually, follow these steps:

```bash
# Build the Docker image
docker build -t gcr.io/[PROJECT_ID]/uk-energy-dashboard:latest -f Dockerfile.dashboard .

# Push to Google Container Registry
docker push gcr.io/[PROJECT_ID]/uk-energy-dashboard:latest

# Deploy to Cloud Run
gcloud run deploy uk-energy-dashboard \
  --image gcr.io/[PROJECT_ID]/uk-energy-dashboard:latest \
  --platform managed \
  --region europe-west2 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars PROJECT_ID=[PROJECT_ID]
```

### 3. Setting up Continuous Deployment

A GitHub Actions workflow file is included in the repository at `.github/workflows/deploy-dashboard.yml`. This workflow automatically builds and deploys the dashboard when changes are pushed to the main branch.

To set up continuous deployment:

1. Store your Google Cloud credentials as a GitHub secret named `GCP_SA_KEY`
2. Configure your Google Cloud project ID in the workflow file
3. Push changes to the main branch to trigger deployment

## Configuration

The dashboard reads the following environment variables:

- `PROJECT_ID`: Your Google Cloud project ID
- `DATASET_ID`: The BigQuery dataset ID (default: uk_energy_prod)
- `REGION`: The Google Cloud region (default: europe-west2)

## Monitoring

After deployment, you can monitor the dashboard using Cloud Run's built-in monitoring tools. The dashboard logs activity to Stackdriver Logging.

## Troubleshooting

If you encounter issues:

1. Check the Cloud Run logs for any error messages
2. Verify that the service account has proper BigQuery access
3. Ensure the BigQuery dataset exists and contains data
4. Verify that the required tables exist in the dataset

For more detailed troubleshooting, contact your Google Cloud administrator.
