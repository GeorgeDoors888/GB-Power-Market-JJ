#!/usr/bin/env python3
"""Create BigQuery dataset in GB Power Market JJ project."""

from google.cloud import bigquery
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file('/secrets/sa.json')
client = bigquery.Client(project="inner-cinema-476211-u9", credentials=credentials)

# Create dataset
dataset_id = "uk_energy_insights"
dataset_ref = bigquery.Dataset(f"{client.project}.{dataset_id}")
dataset_ref.location = "europe-west2"

try:
    dataset = client.create_dataset(dataset_ref, timeout=30)
    print(f"✅ Created dataset: {dataset.dataset_id}")
    print(f"   Project: {client.project}")
    print(f"   Location: {dataset.location}")
except Exception as e:
    if "Already Exists" in str(e):
        print(f"✅ Dataset already exists: {dataset_id}")
    else:
        print(f"❌ Error: {e}")
        raise
