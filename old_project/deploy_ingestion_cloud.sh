#!/usr/bin/env bash
# deploy_ingestion_cloud.sh
#
# This script sets up Cloud Scheduler jobs for scheduled data ingestion
# using Google Cloud Build (no local Docker required)
#
# Usage:
#   ./deploy_ingestion_cloud.sh [project_id]
#

set -e

# Default values
PROJECT_ID=${1:-"jibber-jabber-knowledge"}
REGION="europe-west2"
SERVICE_NAME="uk-energy-data-collector"

echo "===== Setting up Scheduled Data Ingestion for Project: ${PROJECT_ID} ====="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Create a service account for the scheduler if it doesn't exist
SCHEDULER_SA="data-ingestion-scheduler"
SCHEDULER_SA_EMAIL="${SCHEDULER_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Checking service account..."
if ! gcloud iam service-accounts describe ${SCHEDULER_SA_EMAIL} --project ${PROJECT_ID} &> /dev/null; then
    echo "Creating service account ${SCHEDULER_SA_EMAIL}..."
    gcloud iam service-accounts create ${SCHEDULER_SA} \
        --display-name="Data Ingestion Scheduler" \
        --project ${PROJECT_ID}
    
    # Grant required permissions
    echo "Granting permissions to service account..."
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SCHEDULER_SA_EMAIL}" \
        --role="roles/bigquery.dataEditor"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${SCHEDULER_SA_EMAIL}" \
        --role="roles/storage.objectAdmin"
fi

# Create a temporary directory for the build
echo "Creating build files..."
mkdir -p build
cp -f Dockerfile build/
cp -f requirements.txt build/
cp -f scheduled_data_ingestion.py build/
cp -f flask_wrapper.py build/
cp -f ingestion_loader.py build/
cp -f cloud_data_collector.py build/
cp -f *.json build/ 2>/dev/null || true
cp -f *.env build/ 2>/dev/null || true

# Change to the build directory
cd build

# Create a cloudbuild.yaml file
cat > cloudbuild.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - '${SERVICE_NAME}'
      - '--image'
      - 'gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest'
      - '--platform'
      - 'managed'
      - '--region'
      - '${REGION}'
      - '--no-allow-unauthenticated'
      - '--memory'
      - '2Gi'
      - '--set-env-vars'
      - 'PROJECT_ID=${PROJECT_ID},DATASET_ID=uk_energy_prod'
images:
  - 'gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest'
EOF

# Submit the build to Google Cloud Build
echo "Submitting build to Google Cloud Build..."
gcloud builds submit --project ${PROJECT_ID} .

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

# Grant invoker role to service account
echo "Granting invoker role to service account..."
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
    --member="serviceAccount:${SCHEDULER_SA_EMAIL}" \
    --role="roles/run.invoker" \
    --region=${REGION} \
    --project=${PROJECT_ID}

# Create the scheduler jobs
echo "Creating Cloud Scheduler jobs..."

# Hourly ingestion for time-sensitive data
gcloud scheduler jobs create http hourly-energy-data-ingestion \
    --schedule="0 * * * *" \
    --uri="${SERVICE_URL}/ingest" \
    --http-method=POST \
    --oidc-service-account-email=${SCHEDULER_SA_EMAIL} \
    --oidc-token-audience=${SERVICE_URL} \
    --message-body='{"type": "hourly", "sources": ["demand", "wind", "carbon_intensity", "interconnector_flows"]}' \
    --headers="Content-Type=application/json" \
    --location=${REGION} \
    --project=${PROJECT_ID}

# Daily ingestion for less time-sensitive data
gcloud scheduler jobs create http daily-energy-data-ingestion \
    --schedule="0 3 * * *" \
    --uri="${SERVICE_URL}/ingest" \
    --http-method=POST \
    --oidc-service-account-email=${SCHEDULER_SA_EMAIL} \
    --oidc-token-audience=${SERVICE_URL} \
    --message-body='{"type": "daily", "sources": ["balancing_services", "system_warnings"]}' \
    --headers="Content-Type=application/json" \
    --location=${REGION} \
    --project=${PROJECT_ID}

# Clean up the build directory
cd ..
rm -rf build

echo "===== Scheduled Data Ingestion Setup Complete ====="
echo "Ingestion service URL: ${SERVICE_URL}"
echo "Created the following scheduler jobs:"
echo "  - hourly-energy-data-ingestion (runs every hour)"
echo "  - daily-energy-data-ingestion (runs at 3 AM daily)"
