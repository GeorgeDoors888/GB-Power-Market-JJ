#!/usr/bin/env python3
"""
Backfill DISBSAD from Nov 5 to present (Dec 9)
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd
import requests
from google.cloud import bigquery

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
BMRS_BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets'
GAP_START = datetime(2025, 11, 5)
GAP_END = datetime(2025, 12, 10)  # Tomorrow to be safe
TIMEOUT = (10, 90)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fetch_disbsad_date(date: datetime) -> pd.DataFrame:
    """Fetch DISBSAD for a specific date"""
    date_str = date.strftime('%Y-%m-%d')
    url = f"{BMRS_BASE}/DISBSAD"
    
    start_dt = date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    
    params = {
        'from': start_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': end_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    
    headers = {'Accept': 'application/json'}
    
    try:
        logging.info(f"  📡 Fetching DISBSAD for {date_str}...")
        response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                df['_dataset'] = 'DISBSAD'
                df['_window_from_utc'] = start_dt.isoformat()
                df['_window_to_utc'] = end_dt.isoformat()
                df['_ingested_utc'] = datetime.utcnow().isoformat()
                logging.info(f"    ✅ Retrieved {len(df)} DISBSAD records for {date_str}")
                return df
        elif response.status_code == 404:
            logging.info(f"    ℹ️  No DISBSAD data for {date_str}")
        else:
            logging.warning(f"    ⚠️  HTTP {response.status_code} for {date_str}")
    
    except Exception as e:
        logging.error(f"    ❌ Error fetching DISBSAD for {date_str}: {e}")
    
    return pd.DataFrame()

def load_to_bigquery(df: pd.DataFrame, client: bigquery.Client) -> bool:
    """Load DataFrame to BigQuery"""
    if df.empty:
        return True
    
    table_id = f"{PROJECT_ID}.{DATASET}.bmrs_disbsad"
    
    try:
        # Convert settlementDate
        if 'settlementDate' in df.columns:
            df['settlementDate'] = pd.to_datetime(df['settlementDate'], errors='coerce', utc=True)
        
        # Drop problematic columns
        if 'isTendered' in df.columns:
            df = df.drop(columns=['isTendered'])
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
                bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
            ],
            autodetect=True
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logging.info(f"    ✅ Loaded {len(df)} rows to bmrs_disbsad")
        return True
        
    except Exception as e:
        logging.error(f"    ❌ Failed to load: {e}")
        return False

def main():
    logging.info("=" * 80)
    logging.info(f"🔧 BACKFILLING DISBSAD: Nov 5 - Dec 9, 2025")
    logging.info("=" * 80)
    
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    current_date = GAP_START
    total_records = 0
    
    while current_date < GAP_END:
        logging.info(f"\n📅 Processing {current_date.date()}")
        logging.info("-" * 80)
        
        df = fetch_disbsad_date(current_date)
        if not df.empty:
            if load_to_bigquery(df, client):
                total_records += len(df)
        
        current_date += timedelta(days=1)
    
    logging.info("\n" + "=" * 80)
    logging.info("✅ BACKFILL COMPLETE")
    logging.info("=" * 80)
    logging.info(f"   DISBSAD records added: {total_records:,}")

if __name__ == '__main__':
    main()
