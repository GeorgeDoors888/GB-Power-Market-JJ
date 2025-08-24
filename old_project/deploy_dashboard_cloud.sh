#!/usr/bin/env bash
# deploy_dashboard_cloud.sh
#
# This script deploys the UK Energy Dashboard to Cloud Run using Google Cloud Build
# (no local Docker required)
#
# Usage:
#   ./deploy_dashboard_cloud.sh [project_id]
#

set -e

# Default values
PROJECT_ID=${1:-"jibber-jabber-knowledge"}
REGION="europe-west2"
SERVICE_NAME="uk-energy-dashboard"

echo "===== Deploying UK Energy Dashboard to Project: ${PROJECT_ID} ====="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Create a temporary directory for the build
echo "Creating build files..."
mkdir -p build
cp -f Dockerfile.dashboard build/Dockerfile
cp -f requirements.txt build/
cp -f interactive_dashboard_app.py build/
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
      - '--allow-unauthenticated'
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

# Clean up the build directory
cd ..
rm -rf build

echo "===== Deployment Complete ====="
echo "Dashboard URL: ${SERVICE_URL}"
echo "You can access your dashboard at the URL above."
