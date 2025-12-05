#!/usr/bin/env python3
"""
DETS (System Prices) Gap Backfill Script - Oct 29 - Dec 5, 2025
Downloads missing system price data from Elexon BMRS API to fill the gap in bmrs_costs table

DETS Dataset: Detailed System Prices
- systemSellPrice (SSP)
- systemBuyPrice (SBP)
- netImbalanceVolume
- reserveScarcityPrice
- and more...

This script fills the 38-day gap between historical data (last: Oct 28) and current date.
"""

import requests
import json
from datetime import datetime, timedelta, date
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dets_backfill.log'),
        logging.StreamHandler()
    ]
)

# BigQuery setup
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_costs'

CREDENTIALS_FILE = os.environ.get(
    'GOOGLE_APPLICATION_CREDENTIALS',
    '/home/george/.config/google-cloud/bigquery-credentials.json'
)

# BMRS API endpoint (no auth required for public data)
BMRS_API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
DETS_ENDPOINT = '/datasets/DETS'  # Detailed System Prices

# Gap period to fill (Oct 29 - Dec 5)
GAP_START = '2025-10-29'
GAP_END = '2025-12-05'

# BigQuery schema for bmrs_costs (DETS data)
DETS_SCHEMA = [
    bigquery.SchemaField('settlementDate', 'DATETIME'),
    bigquery.SchemaField('settlementPeriod', 'INTEGER'),
    bigquery.SchemaField('startTime', 'DATETIME'),
    bigquery.SchemaField('createdDateTime', 'DATETIME'),
    bigquery.SchemaField('systemSellPrice', 'FLOAT'),
    bigquery.SchemaField('systemBuyPrice', 'FLOAT'),
    bigquery.SchemaField('bsadDefaulted', 'BOOLEAN'),
    bigquery.SchemaField('priceDerivationCode', 'STRING'),
    bigquery.SchemaField('reserveScarcityPrice', 'FLOAT'),
    bigquery.SchemaField('netImbalanceVolume', 'FLOAT'),
    bigquery.SchemaField('sellPriceAdjustment', 'FLOAT'),
    bigquery.SchemaField('buyPriceAdjustment', 'FLOAT'),
    bigquery.SchemaField('replacementPrice', 'FLOAT'),
    bigquery.SchemaField('replacementPriceReferenceVolume', 'FLOAT'),
    bigquery.SchemaField('totalAcceptedOfferVolume', 'FLOAT'),
    bigquery.SchemaField('totalAcceptedBidVolume', 'FLOAT'),
    bigquery.SchemaField('totalAdjustmentSellVolume', 'FLOAT'),
    bigquery.SchemaField('totalAdjustmentBuyVolume', 'FLOAT'),
    bigquery.SchemaField('totalSystemTaggedAcceptedOfferVolume', 'FLOAT'),
    bigquery.SchemaField('totalSystemTaggedAcceptedBidVolume', 'FLOAT'),
    bigquery.SchemaField('totalSystemTaggedAdjustmentSellVolume', 'FLOAT'),
    bigquery.SchemaField('totalSystemTaggedAdjustmentBuyVolume', 'FLOAT'),
    bigquery.SchemaField('_ingested_utc', 'STRING'),
    bigquery.SchemaField('_source_api', 'STRING'),
]


def download_dets_data(from_date: str, to_date: str) -> list:
    """Download DETS (system prices) data from Elexon API"""
    url = f"{BMRS_API_BASE}{DETS_ENDPOINT}"
    
    params = {
        'settlementDateFrom': from_date,
        'settlementDateTo': to_date,
        'format': 'json'
    }
    
    logging.info(f"📥 Downloading DETS (system prices) from {from_date} to {to_date}...")
    logging.info(f"   URL: {url}")
    logging.info(f"   Params: {params}")
    
    all_records = []
    
    try:
        response = requests.get(url, params=params, timeout=600)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            records = data['data']
            logging.info(f"✅ Downloaded {len(records)} DETS records")
            all_records.extend(records)
        else:
            logging.warning(f"⚠️  No 'data' field in response")
            logging.info(f"   Response keys: {data.keys()}")
            return []
        
        # Check for pagination
        page = 1
        while 'metadata' in data and 'pagination' in data['metadata']:
            pagination = data['metadata']['pagination']
            if 'next' in pagination and pagination['next']:
                page += 1
                logging.info(f"📄 Fetching page {page}...")
                
                next_url = pagination['next']
                response = requests.get(next_url, timeout=600)
                response.raise_for_status()
                data = response.json()
                
                if 'data' in data:
                    records = data['data']
                    logging.info(f"✅ Downloaded {len(records)} more records (page {page})")
                    all_records.extend(records)
            else:
                break
        
        return all_records
            
    except Exception as e:
        logging.error(f"❌ Error downloading DETS: {e}")
        import traceback
        traceback.print_exc()
        return []


def transform_record(record: dict) -> dict:
    """Transform API record to BigQuery format"""
    ingested_utc = datetime.utcnow().isoformat()
    
    transformed = {
        'settlementDate': record.get('settlementDate'),
        'settlementPeriod': record.get('settlementPeriod'),
        'startTime': record.get('startTime'),
        'createdDateTime': record.get('createdDateTime'),
        'systemSellPrice': record.get('systemSellPrice'),
        'systemBuyPrice': record.get('systemBuyPrice'),
        'bsadDefaulted': record.get('bsadDefaulted', False),
        'priceDerivationCode': record.get('priceDerivationCode'),
        'reserveScarcityPrice': record.get('reserveScarcityPrice'),
        'netImbalanceVolume': record.get('netImbalanceVolume'),
        'sellPriceAdjustment': record.get('sellPriceAdjustment'),
        'buyPriceAdjustment': record.get('buyPriceAdjustment'),
        'replacementPrice': record.get('replacementPrice'),
        'replacementPriceReferenceVolume': record.get('replacementPriceReferenceVolume'),
        'totalAcceptedOfferVolume': record.get('totalAcceptedOfferVolume'),
        'totalAcceptedBidVolume': record.get('totalAcceptedBidVolume'),
        'totalAdjustmentSellVolume': record.get('totalAdjustmentSellVolume'),
        'totalAdjustmentBuyVolume': record.get('totalAdjustmentBuyVolume'),
        'totalSystemTaggedAcceptedOfferVolume': record.get('totalSystemTaggedAcceptedOfferVolume'),
        'totalSystemTaggedAcceptedBidVolume': record.get('totalSystemTaggedAcceptedBidVolume'),
        'totalSystemTaggedAdjustmentSellVolume': record.get('totalSystemTaggedAdjustmentSellVolume'),
        'totalSystemTaggedAdjustmentBuyVolume': record.get('totalSystemTaggedAdjustmentBuyVolume'),
        '_ingested_utc': ingested_utc,
        '_source_api': 'ELEXON_BMRS_BACKFILL_GAP'
    }
    
    return transformed


def upload_to_bigquery(records: list):
    """Upload records to BigQuery, avoiding duplicates"""
    if not records:
        logging.warning("⚠️  No records to upload")
        return
    
    logging.info(f"📤 Uploading {len(records)} records to BigQuery...")
    
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    client = bigquery.Client(project=BQ_PROJECT, credentials=creds, location='US')
    
    # Transform all records
    transformed_records = [transform_record(r) for r in records]
    
    # Check for existing records to avoid duplicates
    logging.info("🔍 Checking for existing records...")
    table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    
    # Get list of existing (settlementDate, settlementPeriod) combinations
    check_query = f"""
    SELECT DISTINCT 
        DATE(settlementDate) as date,
        settlementPeriod as period
    FROM `{table_id}`
    WHERE settlementDate BETWEEN '{GAP_START}' AND '{GAP_END}'
    """
    
    try:
        existing_df = client.query(check_query).to_dataframe()
        existing_keys = set(
            (row['date'].strftime('%Y-%m-%d'), row['period']) 
            for _, row in existing_df.iterrows()
        )
        logging.info(f"   Found {len(existing_keys)} existing date-period combinations")
    except Exception as e:
        logging.warning(f"⚠️  Could not check existing records: {e}")
        existing_keys = set()
    
    # Filter out duplicates
    new_records = []
    for record in transformed_records:
        try:
            record_date = datetime.fromisoformat(record['settlementDate'].replace('Z', '+00:00'))
            key = (record_date.strftime('%Y-%m-%d'), record['settlementPeriod'])
            
            if key not in existing_keys:
                new_records.append(record)
        except Exception as e:
            logging.warning(f"⚠️  Error processing record: {e}")
            continue
    
    if not new_records:
        logging.info("✅ No new records to insert (all already exist)")
        return
    
    logging.info(f"📥 Inserting {len(new_records)} new records (skipping {len(transformed_records) - len(new_records)} duplicates)...")
    
    # Insert new records
    try:
        errors = client.insert_rows_json(table_id, new_records)
        
        if errors:
            logging.error(f"❌ Errors during insert:")
            for error in errors[:5]:  # Show first 5 errors
                logging.error(f"   {error}")
        else:
            logging.info(f"✅ Successfully inserted {len(new_records)} records")
            
            # Verify insertion
            verify_query = f"""
            SELECT COUNT(*) as cnt, MIN(settlementDate) as min_d, MAX(settlementDate) as max_d
            FROM `{table_id}`
            WHERE settlementDate BETWEEN '{GAP_START}' AND '{GAP_END}'
            """
            verify_df = client.query(verify_query).to_dataframe()
            logging.info(f"📊 Verification:")
            logging.info(f"   Records in gap period: {verify_df.iloc[0]['cnt']}")
            logging.info(f"   Date range: {verify_df.iloc[0]['min_d']} to {verify_df.iloc[0]['max_d']}")
            
    except Exception as e:
        logging.error(f"❌ Error uploading to BigQuery: {e}")
        import traceback
        traceback.print_exc()


def backfill_by_week():
    """Backfill data week by week to avoid API timeouts"""
    start_date = datetime.strptime(GAP_START, '%Y-%m-%d')
    end_date = datetime.strptime(GAP_END, '%Y-%m-%d')
    
    current_date = start_date
    week_count = 0
    
    while current_date <= end_date:
        week_count += 1
        week_end = min(current_date + timedelta(days=6), end_date)
        
        from_str = current_date.strftime('%Y-%m-%d')
        to_str = week_end.strftime('%Y-%m-%d')
        
        logging.info(f"\n{'='*70}")
        logging.info(f"WEEK {week_count}: {from_str} to {to_str}")
        logging.info(f"{'='*70}")
        
        records = download_dets_data(from_str, to_str)
        
        if records:
            upload_to_bigquery(records)
        else:
            logging.warning(f"⚠️  No data for week {week_count}")
        
        current_date = week_end + timedelta(days=1)


def main():
    logging.info("="*70)
    logging.info("DETS (System Prices) Backfill Script")
    logging.info("="*70)
    logging.info(f"Project: {BQ_PROJECT}")
    logging.info(f"Dataset: {BQ_DATASET}")
    logging.info(f"Table: {BQ_TABLE}")
    logging.info(f"Gap Period: {GAP_START} to {GAP_END}")
    logging.info("="*70)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    try:
        backfill_by_week()
        logging.info("\n" + "="*70)
        logging.info("✅ BACKFILL COMPLETE!")
        logging.info("="*70)
        
    except KeyboardInterrupt:
        logging.info("\n⚠️  Backfill interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\n❌ Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
