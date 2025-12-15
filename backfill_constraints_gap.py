#!/usr/bin/env python3
"""
Backfill script to fill the gap in constraint data (Oct 29 - Nov 3, 2025)
Uses Elexon BMRS API to fetch BOALF and DISBSAD data for missing dates.

This fills the gap between:
- Historical data (ends Oct 28, 2025)
- IRIS real-time data (starts Nov 4, 2025)

Usage:
    python3 backfill_constraints_gap.py
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import pandas as pd
import requests
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Configuration
BMRS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TIMEOUT = (10, 90)  # (connect, read) timeout

# Gap period to backfill
GAP_START = datetime(2025, 10, 29)
GAP_END = datetime(2025, 11, 4)  # Exclusive

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fetch_boalf_date(date: datetime, api_key: Optional[str] = None) -> pd.DataFrame:
    """Fetch BOALF (Balancing Mechanism Accepted Offers/Bids) data for a specific date"""
    date_str = date.strftime('%Y-%m-%d')
    url = f"{BMRS_BASE}/BOALF"
    
    # Use RFC3339 format with 'from' and 'to' parameters (NOT settlementDateFrom/To)
    start_dt = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    
    params = {
        'from': start_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': end_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    
    if api_key:
        params['apiKey'] = api_key
    
    headers = {'Accept': 'application/json'}
    
    try:
        logging.info(f"  📡 Fetching BOALF for {date_str}...")
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                # Add metadata
                df['_dataset'] = 'BOALF'
                df['_window_from_utc'] = start_dt.isoformat()
                df['_window_to_utc'] = end_dt.isoformat()
                df['_ingested_utc'] = datetime.utcnow().isoformat()
                logging.info(f"    ✅ Retrieved {len(df)} BOALF records for {date_str}")
                return df
        elif response.status_code == 404:
            logging.info(f"    ℹ️  No BOALF data for {date_str}")
        else:
            logging.warning(f"    ⚠️  Failed to fetch BOALF for {date_str}: HTTP {response.status_code}")
    
    except Exception as e:
        logging.error(f"    ❌ Error fetching BOALF for {date_str}: {e}")
    
    return pd.DataFrame()

def fetch_disbsad_date(date: datetime, api_key: Optional[str] = None) -> pd.DataFrame:
    """Fetch DISBSAD (Derived Imbalance System Adjustment Data) for a specific date"""
    date_str = date.strftime('%Y-%m-%d')
    url = f"{BMRS_BASE}/DISBSAD"
    
    # Use RFC3339 format with 'from' and 'to' parameters (NOT settlementDateFrom/To)
    start_dt = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    
    params = {
        'from': start_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': end_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    
    if api_key:
        params['apiKey'] = api_key
    
    headers = {'Accept': 'application/json'}
    
    try:
        logging.info(f"  📡 Fetching DISBSAD for {date_str}...")
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                # Add metadata
                df['_dataset'] = 'DISBSAD'
                df['_window_from_utc'] = start_dt.isoformat()
                df['_window_to_utc'] = end_dt.isoformat()
                df['_ingested_utc'] = datetime.utcnow().isoformat()
                logging.info(f"    ✅ Retrieved {len(df)} DISBSAD records for {date_str}")
                return df
        elif response.status_code == 404:
            logging.info(f"    ℹ️  No DISBSAD data for {date_str}")
        else:
            logging.warning(f"    ⚠️  Failed to fetch DISBSAD for {date_str}: HTTP {response.status_code}")
    
    except Exception as e:
        logging.error(f"    ❌ Error fetching DISBSAD for {date_str}: {e}")
    
    return pd.DataFrame()

def load_to_bigquery(df: pd.DataFrame, table_name: str, client: bigquery.Client) -> bool:
    """Load DataFrame to BigQuery table"""
    if df.empty:
        logging.info(f"    ⏭️  No data to load for {table_name}")
        return True
    
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    try:
        # Convert settlementDate and acceptanceTime (full datetimes)
        # Keep timeFrom/timeTo as strings (they're just time values like "16:00:00")
        if 'settlementDate' in df.columns:
            df['settlementDate'] = pd.to_datetime(df['settlementDate'], errors='coerce', utc=True)
        if 'acceptanceTime' in df.columns:
            df['acceptanceTime'] = pd.to_datetime(df['acceptanceTime'], errors='coerce', utc=True)
        
        # Drop problematic columns that cause pyarrow conversion issues
        problem_cols = ['isTendered']  # Drop if exists
        for col in problem_cols:
            if col in df.columns:
                df = df.drop(columns=[col])
                logging.debug(f"    Dropped problematic column: {col}")
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
                bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
            ],
            autodetect=True
        )
        
        # Load data
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        logging.info(f"    ✅ Loaded {len(df)} rows to {table_name}")
        return True
        
    except Exception as e:
        logging.error(f"    ❌ Failed to load to {table_name}: {e}")
        return False

def backfill_gap():
    """Main backfill function"""
    logging.info("=" * 80)
    logging.info("🔧 BACKFILLING CONSTRAINT DATA GAP (Oct 29 - Nov 3, 2025)")
    logging.info("=" * 80)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # Get API key from environment (optional)
    import os
    api_key = os.getenv('ELEXON_API_KEY')
    if api_key:
        logging.info("✅ Using Elexon API key from environment")
    else:
        logging.info("ℹ️  No API key found, using public endpoints")
    
    # Iterate through gap dates
    current_date = GAP_START
    total_boalf = 0
    total_disbsad = 0
    
    while current_date < GAP_END:
        date_str = current_date.strftime('%Y-%m-%d')
        logging.info("")
        logging.info(f"📅 Processing {date_str}")
        logging.info("-" * 80)
        
        # Fetch BOALF data
        boalf_df = fetch_boalf_date(current_date, api_key)
        if not boalf_df.empty:
            if load_to_bigquery(boalf_df, 'bmrs_boalf', client):
                total_boalf += len(boalf_df)
        
        # Fetch DISBSAD data
        disbsad_df = fetch_disbsad_date(current_date, api_key)
        if not disbsad_df.empty:
            if load_to_bigquery(disbsad_df, 'bmrs_disbsad', client):
                total_disbsad += len(disbsad_df)
        
        current_date += timedelta(days=1)
    
    # Summary
    logging.info("")
    logging.info("=" * 80)
    logging.info("✅ BACKFILL COMPLETE")
    logging.info("=" * 80)
    logging.info(f"  BOALF records added: {total_boalf:,}")
    logging.info(f"  DISBSAD records added: {total_disbsad:,}")
    logging.info("")
    logging.info("💡 Next steps:")
    logging.info("   1. Run: python3 update_bg_live_dashboard.py")
    logging.info("   2. Check dashboard for updated constraint costs")
    logging.info("=" * 80)

if __name__ == '__main__':
    try:
        backfill_gap()
    except KeyboardInterrupt:
        logging.info("\n⚠️  Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\n❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
