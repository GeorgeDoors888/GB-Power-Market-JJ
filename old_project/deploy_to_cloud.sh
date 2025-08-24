#!/bin/bash
# Google Cloud Deployment Script for BMRS Data Collector

set -e

echo "🚀 BMRS Data Collector - Google Cloud Deployment"
echo "================================================"

# Configuration - Update these values
PROJECT_ID="bmrs-data-collection-$(date +%s)"  # Unique project ID
SERVICE_NAME="bmrs-data-collector"
REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-bmrs-data"

# Detect if project ID needs to be set
if [[ "$PROJECT_ID" == *"$(date +%s)"* ]]; then
    echo "🔧 Creating unique project ID..."
    PROJECT_ID="bmrs-data-$(whoami)-$(date +%Y%m%d)"
    echo "   Project ID: $PROJECT_ID"
fi

echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Bucket: $BUCKET_NAME"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "🔧 Setting up Google Cloud environment..."

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

# Create storage bucket
echo "🪣 Creating storage bucket..."
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME || echo "Bucket already exists"

# Build and deploy to Cloud Run
echo "🏗️  Building and deploying service..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "✅ Deployment completed!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test endpoints:"
echo "   Health check: curl $SERVICE_URL/"
echo "   Start collection: curl -X POST $SERVICE_URL/collect -H 'Content-Type: application/json' -d '{\"start_date\":\"2024-01-01\",\"end_date\":\"2024-01-31\"}'"
echo ""
echo "📊 Monitor at: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
echo "💾 Data at: https://console.cloud.google.com/storage/browser/$BUCKET_NAME"
