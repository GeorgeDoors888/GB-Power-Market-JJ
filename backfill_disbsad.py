#!/usr/bin/env python3
"""
Backfill DISBSAD (Imbalance Settlement Prices) for gap period Dec 15-18, 2025
Similar approach to BOALF backfill - simple and focused.
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_disbsad"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

def download_disbsad_data(from_date, to_date):
    """
    Download DISBSAD data from Elexon API

    Args:
        from_date: datetime.date
        to_date: datetime.date

    Returns:
        List of records
    """
    all_records = []
    current = from_date

    while current <= to_date:
        date_str = current.strftime('%Y-%m-%d')

        # Try settlement date first
        url = f"{BASE_URL}/DISBSAD?settlementDateFrom={date_str}&settlementDateTo={date_str}&format=json"

        print(f"Fetching DISBSAD for {date_str}...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            records = data.get('data', [])

            print(f"  ✅ Retrieved {len(records)} records")
            all_records.extend(records)

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  ❌ Error: {e}")

        current += timedelta(days=1)

    return all_records

def transform_record(record):
    """Transform API record to BigQuery schema"""

    # Fix datetime format (remove Z, replace T with space)
    def fix_datetime(dt_str):
        if dt_str and 'Z' in dt_str:
            return dt_str.replace('Z', '').replace('T', ' ')
        return dt_str

    return {
        'dataset': record.get('dataset'),
        'publishTime': fix_datetime(record.get('publishTime')),
        'settlementDate': fix_datetime(record.get('settlementDate')),
        'settlementPeriod': record.get('settlementPeriod'),
        'price': record.get('price'),
        'volume': record.get('volume'),
        'bsadDefaulted': record.get('bsadDefaulted'),
        'priceDerivationCode': record.get('priceDerivationCode'),
        'reasonCode': record.get('reasonCode'),
        'activeFlag': record.get('activeFlag'),
        '_ingested_utc': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

def upload_to_bigquery(records):
    """Upload records to BigQuery using MERGE to avoid duplicates"""

    if not records:
        print("No records to upload")
        return

    # Create temp table
    temp_table_id = f"{PROJECT_ID}.{DATASET}.disbsad_temp_{int(time.time())}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("dataset", "STRING"),
            bigquery.SchemaField("publishTime", "DATETIME"),
            bigquery.SchemaField("settlementDate", "DATETIME"),
            bigquery.SchemaField("settlementPeriod", "INTEGER"),
            bigquery.SchemaField("price", "FLOAT"),
            bigquery.SchemaField("volume", "FLOAT"),
            bigquery.SchemaField("bsadDefaulted", "BOOLEAN"),
            bigquery.SchemaField("priceDerivationCode", "STRING"),
            bigquery.SchemaField("reasonCode", "STRING"),
            bigquery.SchemaField("activeFlag", "STRING"),
            bigquery.SchemaField("_ingested_utc", "DATETIME"),
        ]
    )

    print(f"Creating temp table with {len(records)} records...")
    job = client.load_table_from_json(records, temp_table_id, job_config=job_config)
    job.result()

    print(f"✅ Temp table created: {len(records)} records")

    # MERGE into main table
    merge_query = f"""
    MERGE `{PROJECT_ID}.{DATASET}.{TABLE}` T
    USING `{temp_table_id}` S
    ON T.settlementDate = S.settlementDate
       AND T.settlementPeriod = S.settlementPeriod
       AND T.publishTime = S.publishTime
    WHEN NOT MATCHED THEN
      INSERT (dataset, publishTime, settlementDate, settlementPeriod, price, volume,
              bsadDefaulted, priceDerivationCode, reasonCode, activeFlag, _ingested_utc)
      VALUES (dataset, publishTime, settlementDate, settlementPeriod, price, volume,
              bsadDefaulted, priceDerivationCode, reasonCode, activeFlag, _ingested_utc)
    """

    print("Merging into main table (deduplication)...")
    merge_job = client.query(merge_query)
    merge_job.result()

    print(f"✅ MERGE complete")

    # Clean up temp table
    client.delete_table(temp_table_id)
    print(f"✅ Temp table deleted")

def main():
    """Main backfill execution"""

    # Gap period: Dec 15-18, 2025
    from_date = datetime(2025, 12, 15).date()
    to_date = datetime(2025, 12, 18).date()

    print(f"=" * 60)
    print(f"DISBSAD Backfill: {from_date} to {to_date}")
    print(f"=" * 60)
    print()

    # Download data
    records = download_disbsad_data(from_date, to_date)

    if not records:
        print("⚠️ No records retrieved - DISBSAD data may not be available yet")
        print("   This dataset typically has a settlement delay")
        return

    print()
    print(f"Total records downloaded: {len(records)}")
    print()

    # Transform records
    transformed = [transform_record(r) for r in records]

    # Upload to BigQuery
    upload_to_bigquery(transformed)

    print()
    print("=" * 60)
    print("✅ DISBSAD Backfill Complete!")
    print(f"   Records processed: {len(transformed)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
