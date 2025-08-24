#!/bin/bash

# Exit on error
set -e

# Load environment variables
source api.env

# Configuration
PROJECT_ID="jibber-jabber-knowledge"
REGION="us-central1"
COLLECTOR_SERVICE="bmrs-data-collector"
MONITOR_SERVICE="bmrs-monitor"
BUCKET_NAME="jibber-jabber-knowledge-bmrs-data"

echo "🔄 Building and deploying BMRS services to Cloud Run..."

# Create Cloud Storage bucket if it doesn't exist
echo "📦 Setting up Cloud Storage..."
gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME || true

# Deploy Collector Service
echo "� Deploying collector service..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$COLLECTOR_SERVICE

gcloud run deploy $COLLECTOR_SERVICE \
  --image gcr.io/$PROJECT_ID/$COLLECTOR_SERVICE \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --timeout 3600 \
  --set-env-vars "BUCKET_NAME=$BUCKET_NAME" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --allow-unauthenticated

# Deploy Monitor Service
echo "📊 Deploying monitor service..."
gcloud builds submit . --config=cloudbuild.monitor.yaml \
  --timeout 1800 \
  --gcs-log-dir gs://$BUCKET_NAME/build_logs \
  --gcs-source-staging-dir gs://$BUCKET_NAME/source

gcloud run deploy $MONITOR_SERVICE \
  --image gcr.io/$PROJECT_ID/$MONITOR_SERVICE \
  --platform managed \
  --region $REGION \
  --memory 512Mi \
  --set-env-vars "BUCKET_NAME=$BUCKET_NAME" \
  --allow-unauthenticated

# Set up Cloud Scheduler
echo "⏰ Setting up Cloud Scheduler..."
gcloud scheduler jobs create http bmrs-data-collection \
  --schedule="0 */3 * * *" \
  --uri="$(gcloud run services describe $COLLECTOR_SERVICE --region $REGION --format 'value(status.url)')" \
  --http-method=POST \
  --attempt-deadline=3600s \
  || echo "Scheduler job already exists"

echo "✅ Deployment complete!"
echo "🔄 Collector URL: $(gcloud run services describe $COLLECTOR_SERVICE --region $REGION --format 'value(status.url)')"
echo "📊 Monitor URL: $(gcloud run services describe $MONITOR_SERVICE --region $REGION --format 'value(status.url)')"
echo ""
echo "To monitor progress, visit: $(gcloud run services describe $MONITOR_SERVICE --region $REGION --format 'value(status.url)')/status"
