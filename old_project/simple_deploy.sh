#!/usr/bin/env bash
# simple_deploy.sh
#
# A simplified deployment script for the Streamlit dashboard
#

set -e

# Default values
PROJECT_ID=${1:-"jibber-jabber-knowledge"}
REGION="europe-west2"
SERVICE_NAME="uk-energy-dashboard"

echo "===== Deploying UK Energy Dashboard to Project: ${PROJECT_ID} ====="

# Create a simple Dockerfile for the dashboard
cat > Dockerfile << EOF
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "interactive_dashboard_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
EOF

# Build the image using Google Cloud Build
echo "Building container image using Google Cloud Build..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME} --project ${PROJECT_ID}

# Deploy the image to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars PROJECT_ID=${PROJECT_ID},DATASET_ID=uk_energy_prod \
  --project ${PROJECT_ID} \
  --cpu 1 \
  --timeout 3600 \
  --concurrency 80

# Get the URL of the deployed service
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)' --project ${PROJECT_ID})

echo "===== Deployment Complete ====="
echo "Dashboard URL: ${SERVICE_URL}"
echo "You can access your dashboard at the URL above."
