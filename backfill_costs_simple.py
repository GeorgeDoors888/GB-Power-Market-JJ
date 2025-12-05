#!/usr/bin/env python3
"""
Simple COSTS backfill - Oct 29 to Dec 5, 2025
Uses the SAME method as ingest_elexon_fixed.py
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd

# Config
CREDENTIALS_FILE = '/home/george/inner-cinema-credentials.json'
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_costs'
START_DATE = '2025-10-29'
END_DATE = '2025-12-05'
TIMEOUT = (10, 90)

# System prices API endpoint (the CORRECT endpoint, not /datasets/COSTS!)
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices"

print("=" * 80)
print("BMRS COSTS BACKFILL - Oct 29 to Dec 5, 2025")
print("=" * 80)
print(f"\n📡 Endpoint: {BASE_URL}")
print(f"📅 Date range: {START_DATE} to {END_DATE}")
print(f"📦 Target table: {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}\n")

# Initialize BigQuery client
creds = Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project=BQ_PROJECT, credentials=creds, location='US')

# Fetch data day by day
start_dt = datetime.strptime(START_DATE, '%Y-%m-%d')
end_dt = datetime.strptime(END_DATE, '%Y-%m-%d')
current_date = start_dt.date()

all_records = []
days_processed = 0
days_with_data = 0

while current_date <= end_dt.date():
    date_str = current_date.strftime('%Y-%m-%d')
    url = f"{BASE_URL}/{date_str}"
    
    try:
        response = requests.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                records = data['data']
                print(f"✅ {date_str}: {len(records)} records")
                
                # Add metadata
                ingested_utc = datetime.utcnow().isoformat()
                for record in records:
                    record['_source_api'] = 'BMRS'
                    record['_dataset'] = 'COSTS'
                    record['_ingested_utc'] = ingested_utc
                
                all_records.extend(records)
                days_with_data += 1
            else:
                print(f"⚠️  {date_str}: No data")
        
        elif response.status_code == 404:
            print(f"⚠️  {date_str}: 404 Not Found (no data published yet)")
        
        else:
            print(f"❌ {date_str}: HTTP {response.status_code}")
    
    except Exception as e:
        print(f"❌ {date_str}: Error - {e}")
    
    days_processed += 1
    current_date += timedelta(days=1)

print(f"\n📊 Summary:")
print(f"   Days processed: {days_processed}")
print(f"   Days with data: {days_with_data}")
print(f"   Total records: {len(all_records)}")

if not all_records:
    print("\n❌ No data to upload - EXITING")
    exit(1)

# Convert to DataFrame
df = pd.DataFrame(all_records)
print(f"\n✅ DataFrame created: {len(df)} rows")
print(f"   Columns: {list(df.columns)}")

# Fix data types for BigQuery compatibility
print(f"\n🔧 Converting data types...")
df['settlementDate'] = pd.to_datetime(df['settlementDate'])
df['startTime'] = pd.to_datetime(df['startTime'])
df['createdDateTime'] = pd.to_datetime(df['createdDateTime'])
df['settlementPeriod'] = df['settlementPeriod'].astype(int)

# Convert numeric columns
numeric_cols = ['systemSellPrice', 'systemBuyPrice', 'reserveScarcityPrice', 
                'netImbalanceVolume', 'sellPriceAdjustment', 'buyPriceAdjustment',
                'replacementPrice', 'replacementPriceReferenceVolume',
                'totalAcceptedOfferVolume', 'totalAcceptedBidVolume',
                'totalAdjustmentSellVolume', 'totalAdjustmentBuyVolume',
                'totalSystemTaggedAcceptedOfferVolume', 'totalSystemTaggedAcceptedBidVolume',
                'totalSystemTaggedAdjustmentSellVolume', 'totalSystemTaggedAdjustmentBuyVolume']

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"   ✅ Data types converted")

# Check for duplicates in target table
print(f"\n🔍 Checking for existing records...")
check_query = f"""
SELECT DISTINCT 
    DATE(settlementDate) as date,
    settlementPeriod as period
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
WHERE DATE(settlementDate) >= '{START_DATE}'
  AND DATE(settlementDate) <= '{END_DATE}'
"""

existing_df = client.query(check_query).to_dataframe()
print(f"   Found {len(existing_df)} existing settlement periods in target date range")

if len(existing_df) > 0:
    # Filter out duplicates
    df['date'] = pd.to_datetime(df['settlementDate']).dt.date
    df['period'] = df['settlementPeriod'].astype(int)
    
    existing_set = set(zip(existing_df['date'], existing_df['period']))
    df_set = set(zip(df['date'], df['period']))
    
    new_set = df_set - existing_set
    duplicate_set = df_set & existing_set
    
    print(f"   Duplicates found: {len(duplicate_set)} settlement periods")
    print(f"   New records: {len(new_set)} settlement periods")
    
    if len(new_set) == 0:
        print("\n⚠️  All records already exist in BigQuery - EXITING")
        exit(0)
    
    # Keep only new records
    df = df[df.apply(lambda row: (row['date'], row['period']) in new_set, axis=1)]
    df = df.drop(columns=['date', 'period'])
    print(f"   Filtered to {len(df)} new records")

# Upload to BigQuery
print(f"\n📤 Uploading to BigQuery...")
table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

job_config = bigquery.LoadJobConfig(
    write_disposition='WRITE_APPEND',
    schema_update_options=[
        bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
        bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION,
    ],
)

job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()  # Wait for completion

print(f"✅ Upload complete!")
print(f"   Rows inserted: {job.output_rows}")
print(f"   Job ID: {job.job_id}")

# Verify
verify_query = f"""
SELECT 
    COUNT(*) as total_rows,
    MIN(DATE(settlementDate)) as earliest_date,
    MAX(DATE(settlementDate)) as latest_date,
    COUNT(DISTINCT DATE(settlementDate)) as distinct_days
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
WHERE DATE(settlementDate) >= '{START_DATE}'
  AND DATE(settlementDate) <= '{END_DATE}'
"""

verify_df = client.query(verify_query).to_dataframe()
print(f"\n📊 Verification:")
print(verify_df.to_string(index=False))

print(f"\n✅ BACKFILL COMPLETE!")
