#!/usr/bin/env bash
# deploy_scheduled_ingestion.sh
#
# This script sets up Cloud Scheduler jobs to run the data ingestion pipeline
# regularly on Google Cloud Run.
#
# Usage:
#   ./deploy_scheduled_ingestion.sh

set -e

# Configuration
PROJECT_ID="jibber-jabber-knowledge"
REGION="europe-west2"
SERVICE_ACCOUNT="data-ingestion-sa@${PROJECT_ID}.iam.gserviceaccount.com"
CONTAINER_IMAGE="gcr.io/${PROJECT_ID}/uk-energy-ingestion:latest"

echo "Deploying scheduled data ingestion for UK Energy Dashboard"

# Check if service account exists, create if it doesn't
echo "Checking service account..."
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT} &>/dev/null; then
    echo "Creating service account ${SERVICE_ACCOUNT}..."
    gcloud iam service-accounts create data-ingestion-sa \
        --display-name="UK Energy Data Ingestion Service Account"
fi

# Grant necessary permissions to the service account
echo "Granting permissions to service account..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin"

# Build and push Docker image
echo "Building Docker image..."
docker build -t ${CONTAINER_IMAGE} \
    -f Dockerfile.ingestion .

echo "Pushing Docker image to Container Registry..."
docker push ${CONTAINER_IMAGE}

# Deploy Cloud Run service
echo "Deploying Cloud Run service..."
gcloud run deploy uk-energy-ingestion \
    --image=${CONTAINER_IMAGE} \
    --region=${REGION} \
    --platform=managed \
    --service-account=${SERVICE_ACCOUNT} \
    --no-allow-unauthenticated \
    --memory=2Gi \
    --timeout=3600 \
    --set-env-vars="PROJECT_ID=${PROJECT_ID},DATASET_ID=uk_energy_prod,BUCKET_NAME=jibber-jabber-knowledge-bmrs-data"

# Get service URL
SERVICE_URL=$(gcloud run services describe uk-energy-ingestion --region=${REGION} --format='value(status.url)')

# Create Cloud Scheduler jobs
echo "Creating Cloud Scheduler jobs..."

# Daily incremental job (runs every day at 01:00 UTC)
gcloud scheduler jobs create http uk-energy-daily-ingestion \
    --schedule="0 1 * * *" \
    --uri="${SERVICE_URL}/run" \
    --http-method=POST \
    --oidc-service-account-email=${SERVICE_ACCOUNT} \
    --oidc-token-audience=${SERVICE_URL} \
    --headers="Content-Type=application/json" \
    --message-body='{"mode":"incremental"}' \
    --location=${REGION}

# Weekly backfill job (runs every Sunday at 03:00 UTC)
gcloud scheduler jobs create http uk-energy-weekly-backfill \
    --schedule="0 3 * * 0" \
    --uri="${SERVICE_URL}/run" \
    --http-method=POST \
    --oidc-service-account-email=${SERVICE_ACCOUNT} \
    --oidc-token-audience=${SERVICE_URL} \
    --headers="Content-Type=application/json" \
    --message-body='{"mode":"backfill","days":14}' \
    --location=${REGION}

# Monthly full backfill (runs on 1st of each month at 04:00 UTC)
gcloud scheduler jobs create http uk-energy-monthly-backfill \
    --schedule="0 4 1 * *" \
    --uri="${SERVICE_URL}/run" \
    --http-method=POST \
    --oidc-service-account-email=${SERVICE_ACCOUNT} \
    --oidc-token-audience=${SERVICE_URL} \
    --headers="Content-Type=application/json" \
    --message-body='{"mode":"backfill","days":90}' \
    --location=${REGION}

echo "Deployment completed successfully!"
echo "Scheduled jobs:"
echo "  - Daily incremental updates: Every day at 01:00 UTC"
echo "  - Weekly backfill (14 days): Every Sunday at 03:00 UTC"
echo "  - Monthly backfill (90 days): 1st of each month at 04:00 UTC"
