#!/usr/bin/env bash
# deploy_streamlit_only.sh
#
# This script deploys just the Streamlit dashboard to Cloud Run 
# without requiring Docker locally.
#
# Usage:
#   ./deploy_streamlit_only.sh [project_id]
#

set -e

# Default values
PROJECT_ID=${1:-"jibber-jabber-knowledge"}
REGION="europe-west2"
SERVICE_NAME="uk-energy-dashboard"

echo "===== Deploying UK Energy Dashboard to Project: ${PROJECT_ID} ====="

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated with gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "You need to authenticate with gcloud first. Run 'gcloud auth login'."
    exit 1
fi

# Deploy the Streamlit app directly from source code using buildpacks
echo "Deploying Streamlit app directly to Cloud Run using buildpacks..."
gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars PROJECT_ID=${PROJECT_ID},DATASET_ID=uk_energy_prod,STREAMLIT_SERVER_PORT=8080 \
  --project ${PROJECT_ID} \
  --command "streamlit run interactive_dashboard_app.py --server.port=8080 --server.address=0.0.0.0" \
  --cpu 1 \
  --timeout 3600 \
  --concurrency 80

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "===== Deployment Complete ====="
echo "Dashboard URL: ${SERVICE_URL}"
echo "You can access your dashboard at the URL above."
