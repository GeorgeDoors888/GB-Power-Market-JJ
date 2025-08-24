#!/bin/bash
# BigQuery Region Migration Shell Script
# Exports BigQuery tables from current location to europe-west2 region

set -e # Exit on error
set -u # Treat unset variables as errors

# Load environment variables or set defaults
PROJECT=${PROJECT:-"jibber-jabber-knowledge"}
SOURCE_DATASET=${SOURCE_DATASET:-"uk_energy"}
DEST_DATASET=${DEST_DATASET:-"${SOURCE_DATASET}_eu"}
US_BUCKET=${US_BUCKET:-"my-us-bucket"} # Replace with your actual US bucket
EU_BUCKET=${EU_BUCKET:-"my-eu-bucket"} # Replace with your actual EU bucket

echo "Starting BigQuery migration to europe-west2 region"
echo "PROJECT: $PROJECT"
echo "SOURCE_DATASET: $SOURCE_DATASET"
echo "DESTINATION_DATASET: $DEST_DATASET"
echo "US_BUCKET: $US_BUCKET"
echo "EU_BUCKET: $EU_BUCKET"

# Create destination dataset if it doesn't exist
echo "Creating destination dataset in europe-west2..."
bq --location=europe-west2 mk --dataset "${PROJECT}:${DEST_DATASET}" || \
  echo "Dataset might already exist, continuing..."

# Define tables to migrate - add or remove from this list as needed
TABLES=(
  "neso_demand_forecasts"
  "neso_wind_forecasts"
  "neso_balancing_services"
  # Add more tables as needed
)

# Process each table
for TABLE in "${TABLES[@]}"; do
  echo "Processing table: $TABLE"
  
  # Step 1: Export table from BigQuery to GCS (US bucket)
  echo "Exporting $TABLE to US bucket..."
  bq extract --destination_format=PARQUET \
    "${PROJECT}:${SOURCE_DATASET}.${TABLE}" \
    "gs://${US_BUCKET}/bq_export/${TABLE}/*.parquet"
  
  # Step 2: Copy data from US bucket to EU bucket
  echo "Copying $TABLE data to EU bucket..."
  gsutil -m cp -r "gs://${US_BUCKET}/bq_export/${TABLE}" \
    "gs://${EU_BUCKET}/bq_export/${TABLE}"
  
  # Step 3: Load data from EU bucket to BigQuery in europe-west2
  echo "Loading $TABLE to europe-west2 BigQuery..."
  bq --location=europe-west2 load --source_format=PARQUET \
    "${PROJECT}:${DEST_DATASET}.${TABLE}" \
    "gs://${EU_BUCKET}/bq_export/${TABLE}/*.parquet"
  
  echo "Successfully migrated table $TABLE to europe-west2"
done

echo "BigQuery region migration completed successfully!"
