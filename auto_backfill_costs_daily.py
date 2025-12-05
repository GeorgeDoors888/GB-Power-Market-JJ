#!/usr/bin/env python3
"""
Automated Daily COSTS Backfill
Checks for missing dates in bmrs_costs and backfills from Elexon API
Safe to run multiple times - has duplicate prevention
"""

import requests
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
import sys

# Config
CREDENTIALS_FILE = '/home/george/inner-cinema-credentials.json'
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_costs'
LOOKBACK_DAYS = 7  # Check last 7 days for gaps
TIMEOUT = (10, 90)

# System prices API endpoint
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def main():
    log("=" * 80)
    log("AUTOMATED DAILY COSTS BACKFILL")
    log("=" * 80)
    
    # Initialize BigQuery client
    try:
        creds = Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        client = bigquery.Client(project=BQ_PROJECT, credentials=creds, location='US')
        log(f"✅ Connected to BigQuery: {BQ_PROJECT}")
    except Exception as e:
        log(f"❌ Failed to connect to BigQuery: {e}")
        sys.exit(1)
    
    # Find missing dates in last LOOKBACK_DAYS
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    log(f"🔍 Checking for gaps from {start_date} to {end_date}")
    
    # Get existing dates from BigQuery
    existing_query = f"""
    SELECT DISTINCT DATE(settlementDate) as date
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
    WHERE DATE(settlementDate) >= '{start_date}'
      AND DATE(settlementDate) <= '{end_date}'
    ORDER BY date
    """
    
    try:
        existing_df = client.query(existing_query).to_dataframe()
        existing_dates = set(existing_df['date'].astype(str))
        log(f"   Found {len(existing_dates)} dates already in BigQuery")
    except Exception as e:
        log(f"❌ Failed to query existing dates: {e}")
        sys.exit(1)
    
    # Generate all dates in range
    all_dates = []
    current = start_date
    while current <= end_date:
        all_dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    # Find missing dates
    missing_dates = sorted(set(all_dates) - existing_dates)
    
    if not missing_dates:
        log("✅ No missing dates - table is up to date!")
        log("=" * 80)
        sys.exit(0)
    
    log(f"⚠️  Found {len(missing_dates)} missing dates: {missing_dates}")
    
    # Fetch data for missing dates
    all_records = []
    success_count = 0
    
    for date_str in missing_dates:
        url = f"{BASE_URL}/{date_str}"
        
        try:
            response = requests.get(url, headers={"Accept": "application/json"}, timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    records = data['data']
                    log(f"✅ {date_str}: {len(records)} records")
                    
                    # Add metadata
                    ingested_utc = datetime.utcnow().isoformat()
                    for record in records:
                        record['_source_api'] = 'BMRS'
                        record['_dataset'] = 'COSTS'
                        record['_ingested_utc'] = ingested_utc
                    
                    all_records.extend(records)
                    success_count += 1
                else:
                    log(f"⚠️  {date_str}: No data returned")
            
            elif response.status_code == 404:
                log(f"⚠️  {date_str}: 404 Not Found (data not published yet)")
            
            else:
                log(f"❌ {date_str}: HTTP {response.status_code}")
        
        except Exception as e:
            log(f"❌ {date_str}: Error - {e}")
    
    if not all_records:
        log("⚠️  No data retrieved - nothing to upload")
        log("=" * 80)
        sys.exit(0)
    
    log(f"\n📊 Retrieved {len(all_records)} records from {success_count} dates")
    
    # Convert to DataFrame
    try:
        df = pd.DataFrame(all_records)
        log(f"✅ DataFrame created: {len(df)} rows")
        
        # Fix data types
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
        
        log("✅ Data types converted")
    
    except Exception as e:
        log(f"❌ Failed to process DataFrame: {e}")
        sys.exit(1)
    
    # Double-check for duplicates (safety check)
    log("🔍 Final duplicate check...")
    check_query = f"""
    SELECT DISTINCT 
        DATE(settlementDate) as date,
        settlementPeriod as period
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
    WHERE DATE(settlementDate) IN ({','.join(f"'{d}'" for d in missing_dates)})
    """
    
    try:
        existing_df = client.query(check_query).to_dataframe()
        
        if len(existing_df) > 0:
            log(f"⚠️  Found {len(existing_df)} existing settlement periods - filtering...")
            
            df['date'] = pd.to_datetime(df['settlementDate']).dt.date
            df['period'] = df['settlementPeriod'].astype(int)
            
            existing_set = set(zip(existing_df['date'], existing_df['period']))
            df_set = set(zip(df['date'], df['period']))
            new_set = df_set - existing_set
            
            if len(new_set) == 0:
                log("⚠️  All records already exist - nothing to upload")
                log("=" * 80)
                sys.exit(0)
            
            df = df[df.apply(lambda row: (row['date'], row['period']) in new_set, axis=1)]
            df = df.drop(columns=['date', 'period'])
            log(f"   Filtered to {len(df)} new records")
    
    except Exception as e:
        log(f"❌ Duplicate check failed: {e}")
        sys.exit(1)
    
    # Upload to BigQuery
    log("📤 Uploading to BigQuery...")
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_APPEND',
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION,
        ],
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        log(f"✅ Upload complete!")
        log(f"   Rows inserted: {job.output_rows}")
        log(f"   Job ID: {job.job_id}")
    
    except Exception as e:
        log(f"❌ Upload failed: {e}")
        sys.exit(1)
    
    # Verify
    verify_query = f"""
    SELECT 
        COUNT(*) as total_rows,
        MIN(DATE(settlementDate)) as earliest_date,
        MAX(DATE(settlementDate)) as latest_date,
        COUNT(DISTINCT DATE(settlementDate)) as distinct_days
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
    """
    
    try:
        verify_df = client.query(verify_query).to_dataframe()
        log("\n📊 Table Status After Upload:")
        log(verify_df.to_string(index=False))
    except Exception as e:
        log(f"⚠️  Verification query failed: {e}")
    
    log("\n✅ DAILY BACKFILL COMPLETE!")
    log("=" * 80)

if __name__ == "__main__":
    main()
