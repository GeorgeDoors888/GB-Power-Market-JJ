#!/usr/bin/env python3
"""
Upload missing CSV files to BigQuery:
- gsp_wind_data_latest.csv
- bmu_registration_data.csv
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime
import sys
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

FILES_TO_UPLOAD = [
    {
        'file': 'gsp_wind_data_latest.csv',
        'table': 'gsp_wind_data_latest',
        'description': 'Latest GSP wind generation data by Grid Supply Point'
    },
    {
        'file': 'bmu_registration_data.csv',
        'table': 'bmu_registration_data',
        'description': 'BMU (Balancing Mechanism Unit) registration data from Elexon'
    }
]

print("=" * 80)
print("📊 CSV Files → BigQuery Upload")
print("=" * 80)

# Load credentials
print("\n🔐 Loading credentials...")
credentials = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json'
)
client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location="US")

uploaded = 0
skipped = 0
failed = 0

for file_info in FILES_TO_UPLOAD:
    csv_file = file_info['file']
    table_id = file_info['table']
    description = file_info['description']
    
    print(f"\n{'=' * 80}")
    print(f"📄 Processing: {csv_file}")
    print(f"   Target table: {table_id}")
    print(f"   Description: {description}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"   ⚠️  File not found, skipping...")
        skipped += 1
        continue
    
    try:
        # Read CSV
        print(f"\n📖 Reading {csv_file}...")
        df = pd.read_csv(csv_file)
        print(f"   ✅ Loaded {len(df):,} rows, {len(df.columns)} columns")
        
        # Clean column names
        df.columns = [
            col.strip()
            .replace(' ', '_')
            .replace('/', '_')
            .replace('-', '_')
            .replace('(', '')
            .replace(')', '')
            .lower()
            if isinstance(col, str) else f'column_{i}'
            for i, col in enumerate(df.columns)
        ]
        
        # Add metadata
        df['_uploaded_at'] = datetime.utcnow().isoformat()
        df['_source_file'] = csv_file
        
        # Upload to BigQuery
        print(f"\n☁️  Uploading to {PROJECT_ID}.{DATASET}.{table_id}...")
        
        table_ref = f"{PROJECT_ID}.{DATASET}.{table_id}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
        )
        
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # Wait for completion
        
        # Update table description
        table = client.get_table(table_ref)
        table.description = description
        client.update_table(table, ["description"])
        
        print(f"   ✅ Upload complete!")
        print(f"      Table: {table_ref}")
        print(f"      Rows: {table.num_rows:,}")
        print(f"      Size: {table.num_bytes / 1024 / 1024:.2f} MB")
        
        uploaded += 1
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        failed += 1
        continue

# Summary
print("\n" + "=" * 80)
print("📊 UPLOAD SUMMARY")
print("=" * 80)
print(f"\n✅ Successfully uploaded: {uploaded}")
print(f"⚠️  Skipped (not found): {skipped}")
print(f"❌ Failed: {failed}")

if uploaded > 0:
    print(f"\n🎉 Successfully uploaded {uploaded} file(s) to BigQuery!")
else:
    print("\n⚠️  No files were uploaded")

print("=" * 80)
