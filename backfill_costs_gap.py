#!/usr/bin/env python3
"""
COSTS Gap Backfill Script - Oct 29 - Dec 5, 2025
Downloads missing system price data (COSTS) from Elexon BMRS API to fill the gap in bmrs_costs table

COSTS Dataset contains:
- systemSellPrice (SSP)
- systemBuyPrice (SBP)  
- netImbalanceVolume
- And other system imbalance pricing fields
"""

import requests
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/costs_backfill.log'),
        logging.StreamHandler()
    ]
)

# BigQuery setup
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_costs'

# BMRS API endpoint (no auth required for public data)
BMRS_API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
COSTS_ENDPOINT = '/datasets/COSTS'

# Gap period to fill (Oct 29 - Dec 5, 2025)
GAP_START = '2025-10-29'
GAP_END = '2025-12-05'

# BigQuery schema for bmrs_costs (COSTS data)
COSTS_SCHEMA = [
    bigquery.SchemaField('_dataset', 'STRING'),
    bigquery.SchemaField('settlementDate', 'DATETIME'),
    bigquery.SchemaField('settlementPeriod', 'INTEGER'),
    bigquery.SchemaField('startTime', 'DATETIME'),
    bigquery.SchemaField('systemSellPrice', 'FLOAT'),
    bigquery.SchemaField('systemBuyPrice', 'FLOAT'),
    bigquery.SchemaField('netImbalanceVolume', 'FLOAT'),
    bigquery.SchemaField('reserveScarcityPrice', 'FLOAT'),
    bigquery.SchemaField('sellPriceAdjustment', 'FLOAT'),
    bigquery.SchemaField('buyPriceAdjustment', 'FLOAT'),
    bigquery.SchemaField('replacementPrice', 'FLOAT'),
    bigquery.SchemaField('totalAcceptedOfferVolume', 'FLOAT'),
    bigquery.SchemaField('totalAcceptedBidVolume', 'FLOAT'),
    bigquery.SchemaField('bsadDefaulted', 'BOOLEAN'),
    bigquery.SchemaField('priceDerivationCode', 'STRING'),
    bigquery.SchemaField('paidSystemSellPrice', 'FLOAT'),
    bigquery.SchemaField('paidSystemBuyPrice', 'FLOAT'),
    bigquery.SchemaField('informationIncomplete', 'BOOLEAN'),
    bigquery.SchemaField('imbalancePriceCapplicationNotice', 'BOOLEAN'),
    bigquery.SchemaField('nivolStatus', 'STRING'),
    bigquery.SchemaField('_ingested_utc', 'STRING'),
    bigquery.SchemaField('_source_api', 'STRING'),
]


def download_costs_data(from_date, to_date):
    """Download COSTS (system prices) data from Elexon API"""
    url = f"{BMRS_API_BASE}{COSTS_ENDPOINT}"
    
    params = {
        'settlementDateFrom': from_date,
        'settlementDateTo': to_date,
        'format': 'json'
    }
    
    logging.info(f"📥 Downloading COSTS (system prices) from {from_date} to {to_date}...")
    logging.info(f"   URL: {url}")
    logging.info(f"   Params: {params}")
    
    all_records = []
    
    try:
        response = requests.get(url, params=params, timeout=600)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            records = data['data']
            logging.info(f"✅ Downloaded {len(records)} COSTS records")
            all_records.extend(records)
        else:
            logging.warning(f"⚠️  No 'data' field in response")
            logging.info(f"   Response keys: {data.keys()}")
            logging.info(f"   Full response: {json.dumps(data, indent=2)[:500]}")
        
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
            
    except requests.exceptions.HTTPError as e:
        logging.error(f"❌ HTTP Error downloading COSTS: {e}")
        logging.error(f"   Status code: {e.response.status_code}")
        logging.error(f"   Response: {e.response.text[:500]}")
        return []
    except Exception as e:
        logging.error(f"❌ Error downloading COSTS: {e}")
        import traceback
        traceback.print_exc()
        return []


def transform_record(record):
    """Transform API record to BigQuery format"""
    ingested_utc = datetime.utcnow().isoformat()
    
    transformed = {
        '_dataset': record.get('dataset', 'COSTS'),
        'settlementDate': record.get('settlementDate'),
        'settlementPeriod': record.get('settlementPeriod'),
        'startTime': record.get('startTime'),
        'systemSellPrice': record.get('systemSellPrice'),
        'systemBuyPrice': record.get('systemBuyPrice'),
        'netImbalanceVolume': record.get('netImbalanceVolume'),
        'reserveScarcityPrice': record.get('reserveScarcityPrice'),
        'sellPriceAdjustment': record.get('sellPriceAdjustment'),
        'buyPriceAdjustment': record.get('buyPriceAdjustment'),
        'replacementPrice': record.get('replacementPrice'),
        'totalAcceptedOfferVolume': record.get('totalAcceptedOfferVolume'),
        'totalAcceptedBidVolume': record.get('totalAcceptedBidVolume'),
        'bsadDefaulted': record.get('bsadDefaulted', False),
        'priceDerivationCode': record.get('priceDerivationCode'),
        'paidSystemSellPrice': record.get('paidSystemSellPrice'),
        'paidSystemBuyPrice': record.get('paidSystemBuyPrice'),
        'informationIncomplete': record.get('informationIncomplete', False),
        'imbalancePriceCapplicationNotice': record.get('imbalancePriceCapplicationNotice', False),
        'nivolStatus': record.get('nivolStatus'),
        '_ingested_utc': ingested_utc,
        '_source_api': 'ELEXON_BMRS_BACKFILL_COSTS_GAP'
    }
    
    return transformed


def upload_to_bigquery(records):
    """Upload records to BigQuery, avoiding duplicates"""
    if not records:
        logging.warning("⚠️  No records to upload")
        return 0
    
    client = bigquery.Client(project=BQ_PROJECT)
    table_ref = f"{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    
    # Transform records
    transformed = [transform_record(r) for r in records]
    
    # Check for existing records to avoid duplicates
    settlement_dates = list(set([r['settlementDate'] for r in transformed if r.get('settlementDate')]))
    
    if settlement_dates:
        # Query existing data
        date_list_str = "', '".join([d[:10] for d in settlement_dates])  # Extract date only
        check_query = f"""
        SELECT DISTINCT settlementDate, settlementPeriod
        FROM `{table_ref}`
        WHERE DATE(settlementDate) IN ('{date_list_str}')
        """
        
        try:
            existing_df = client.query(check_query).to_dataframe()
            existing_keys = set(existing_df.apply(lambda r: f"{r['settlementDate'].date()}_{r['settlementPeriod']}", axis=1))
            logging.info(f"📋 Found {len(existing_keys)} existing records in BigQuery")
            
            # Filter out duplicates
            unique_records = []
            for r in transformed:
                if r.get('settlementDate') and r.get('settlementPeriod'):
                    key = f"{r['settlementDate'][:10]}_{r['settlementPeriod']}"
                    if key not in existing_keys:
                        unique_records.append(r)
            
            logging.info(f"📊 {len(unique_records)} new records to insert (filtered {len(transformed) - len(unique_records)} duplicates)")
            transformed = unique_records
        except Exception as e:
            logging.warning(f"⚠️  Could not check for duplicates: {e}")
            logging.info("   Proceeding with all records...")
    
    if not transformed:
        logging.info("✅ No new records to insert (all already exist)")
        return 0
    
    # Insert records
    try:
        errors = client.insert_rows_json(table_ref, transformed)
        
        if errors:
            logging.error(f"❌ Errors inserting rows:")
            for error in errors[:5]:  # Show first 5 errors
                logging.error(f"   {error}")
            return 0
        else:
            logging.info(f"✅ Successfully inserted {len(transformed)} records into {BQ_TABLE}")
            return len(transformed)
            
    except Exception as e:
        logging.error(f"❌ Failed to insert records: {e}")
        import traceback
        traceback.print_exc()
        return 0


def backfill_by_week():
    """Backfill data week by week to avoid timeouts"""
    start_date = datetime.strptime(GAP_START, '%Y-%m-%d')
    end_date = datetime.strptime(GAP_END, '%Y-%m-%d')
    
    total_inserted = 0
    current_date = start_date
    week_num = 1
    
    while current_date <= end_date:
        week_end = min(current_date + timedelta(days=6), end_date)
        
        from_str = current_date.strftime('%Y-%m-%d')
        to_str = week_end.strftime('%Y-%m-%d')
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Week {week_num}: {from_str} to {to_str}")
        logging.info(f"{'='*60}")
        
        # Download data for this week
        records = download_costs_data(from_str, to_str)
        
        if records:
            # Upload to BigQuery
            inserted = upload_to_bigquery(records)
            total_inserted += inserted
            logging.info(f"✅ Week {week_num} complete: {inserted} records inserted")
        else:
            logging.warning(f"⚠️  Week {week_num}: No data downloaded")
        
        # Move to next week
        current_date = week_end + timedelta(days=1)
        week_num += 1
    
    return total_inserted


def main():
    logging.info("="*60)
    logging.info("COSTS (System Prices) Backfill Script")
    logging.info(f"Gap Period: {GAP_START} to {GAP_END}")
    logging.info(f"Target Table: {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}")
    logging.info("="*60)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run weekly backfill
    total = backfill_by_week()
    
    logging.info("\n" + "="*60)
    logging.info(f"🎉 BACKFILL COMPLETE")
    logging.info(f"   Total records inserted: {total}")
    logging.info(f"   Gap period: {GAP_START} to {GAP_END}")
    logging.info("="*60)


if __name__ == '__main__':
    main()
