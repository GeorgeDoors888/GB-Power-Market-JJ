#!/usr/bin/env bash
# deploy_dashboard.sh
#
# This script builds and deploys the UK Energy Dashboard to Cloud Run
#
# Usage:
#   ./deploy_dashboard.sh [project_id]
#

set -e

# Default values
PROJECT_ID=${1:-"jibber-jabber-knowledge"}
REGION="europe-west2"
SERVICE_NAME="uk-energy-dashboard"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "===== Deploying UK Energy Dashboard to Project: ${PROJECT_ID} ====="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed. Please install it first."
    exit 1
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME}:latest -f Dockerfile.dashboard .

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Deploy to Cloud Run
echo "Deploying to Cloud Run in ${REGION}..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars PROJECT_ID=${PROJECT_ID},DATASET_ID=uk_energy_prod \
  --project ${PROJECT_ID}

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "===== Deployment Complete ====="
echo "Dashboard URL: ${SERVICE_URL}"
echo "You can access your dashboard at the URL above."
