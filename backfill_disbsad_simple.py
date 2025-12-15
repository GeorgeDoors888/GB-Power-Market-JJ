#!/usr/bin/env python3
"""
Simple DISBSAD Backfill - Standalone script with no external dependencies
Fetches DISBSAD data from Elexon API and uploads to BigQuery
Run every 15 minutes via cron to keep data current
"""

import sys
import json
import requests
import logging
from datetime import datetime, timedelta, date
from google.cloud import bigquery
from google.api_core import exceptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/home/george/GB-Power-Market-JJ/logs/disbsad_backfill.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TABLE = 'bmrs_disbsad'
ELEXON_API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/DISBSAD'


def fetch_disbsad_data(from_date, to_date):
    """
    Fetch DISBSAD data from Elexon API
    
    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    
    Returns:
        list: DISBSAD records
    """
    # Convert to datetime with timezone
    from datetime import datetime, timezone, timedelta
    
    start_dt = datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
    
    params = {
        'from': start_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': end_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    
    url = ELEXON_API_BASE
    
    logger.info(f"Fetching DISBSAD: {from_date} to {to_date}")
    logger.info(f"URL: {url}")
    logger.info(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            logger.info(f"✅ Fetched {len(data['data'])} DISBSAD records")
            return data['data']
        else:
            logger.warning(f"⚠️  No DISBSAD data returned for {from_date} to {to_date}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error processing response: {e}")
        return []


def transform_disbsad_record(record):
    """
    Transform DISBSAD API record to BigQuery schema
    
    Args:
        record: Raw API record
    
    Returns:
        dict: Transformed record for BigQuery
    """
    # Convert settlementDate to DATETIME (ISO 8601 format)
    settlement_date = record.get('settlementDate', '')
    if settlement_date and not settlement_date.endswith('Z'):
        settlement_date = f"{settlement_date}T00:00:00"
    
    return {
        'dataset': record.get('dataset', 'DISBSAD'),
        'settlementDate': settlement_date,
        'settlementPeriod': int(record.get('settlementPeriod', 0)),
        'id': int(record.get('id', 0)),
        'cost': float(record.get('cost', 0.0)),
        'volume': float(record.get('volume', 0.0)),
        'soFlag': bool(record.get('soFlag', False)),
        'storFlag': bool(record.get('storFlag', False)),
        'partyId': record.get('partyId', ''),
        'assetId': record.get('assetId', ''),
        'isTendered': record.get('isTendered', ''),
        'service': record.get('service', ''),
        '_ingested_utc': datetime.utcnow().isoformat(),
        '_source_api': 'BMRS',
    }


def upload_to_bigquery(records, project_id=PROJECT_ID, dataset=DATASET, table=TABLE):
    """
    Upload DISBSAD records to BigQuery
    
    Args:
        records: List of transformed records
        project_id: GCP project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not records:
        logger.warning("No records to upload")
        return True
    
    try:
        client = bigquery.Client(project=project_id, location='US')
        table_ref = f"{project_id}.{dataset}.{table}"
        
        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
            ],
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )
        
        # Convert records to newline-delimited JSON
        json_data = '\n'.join(json.dumps(record) for record in records)
        
        # Load data
        job = client.load_table_from_json(
            records,
            table_ref,
            job_config=job_config
        )
        
        # Wait for completion
        job.result()
        
        logger.info(f"✅ Uploaded {len(records)} records to {table_ref}")
        logger.info(f"   Rows in table: {client.get_table(table_ref).num_rows:,}")
        
        return True
        
    except exceptions.NotFound:
        logger.error(f"❌ Table {table_ref} not found")
        return False
    except Exception as e:
        logger.error(f"❌ BigQuery upload failed: {e}")
        return False


def delete_existing_data(from_date, to_date, project_id=PROJECT_ID, dataset=DATASET, table=TABLE):
    """
    Delete existing data for date range (to avoid duplicates)
    
    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    """
    try:
        client = bigquery.Client(project=project_id, location='US')
        table_ref = f"{project_id}.{dataset}.{table}"
        
        # Delete query
        query = f"""
        DELETE FROM `{table_ref}`
        WHERE DATE(settlementDate) >= '{from_date}'
          AND DATE(settlementDate) <= '{to_date}'
        """
        
        logger.info(f"Deleting existing data for {from_date} to {to_date}...")
        job = client.query(query)
        job.result()
        
        logger.info(f"✅ Deleted existing records for date range")
        
    except Exception as e:
        logger.warning(f"⚠️  Delete failed (may not exist): {e}")


def main():
    """Main backfill logic - fetches last 3 days to ensure no gaps"""
    logger.info("=" * 80)
    logger.info("🔧 DISBSAD BACKFILL STARTING")
    logger.info("=" * 80)
    
    # Fetch last 3 days (DISBSAD typically lags 1-2 days)
    # Fetch day-by-day since API has 1-day limit
    today = date.today()
    days_to_fetch = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(3, 0, -1)]
    
    logger.info(f"Fetching {len(days_to_fetch)} days: {days_to_fetch[0]} to {days_to_fetch[-1]}")
    
    all_records = []
    
    for day in days_to_fetch:
        # Fetch one day at a time
        raw_records = fetch_disbsad_data(day, day)
        if raw_records:
            all_records.extend(raw_records)
            logger.info(f"  ✅ {day}: {len(raw_records)} records")
        else:
            logger.warning(f"  ⚠️  {day}: No data")
    
    if not all_records:
        logger.warning("No data fetched across all days - exiting")
        return
    
    logger.info(f"\n📊 Total records fetched: {len(all_records)}")
    
    # Transform records
    logger.info("Transforming records...")
    transformed = [transform_disbsad_record(r) for r in all_records]
    
    # Delete existing data for this date range (avoid duplicates)
    delete_existing_data(days_to_fetch[0], days_to_fetch[-1])
    
    # Upload to BigQuery
    success = upload_to_bigquery(transformed)
    
    if success:
        logger.info("=" * 80)
        logger.info(f"✅ DISBSAD BACKFILL COMPLETE - {len(transformed)} records")
        logger.info("=" * 80)
    else:
        logger.error("=" * 80)
        logger.error("❌ DISBSAD BACKFILL FAILED")
        logger.error("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
