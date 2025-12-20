#!/usr/bin/env python3
"""
Backfill missing days in bmrs_costs (DISEBSP - system prices)
Fills 91 scattered missing days from 2022-2025
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_costs"

client = bigquery.Client(project=PROJECT_ID, location="US")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def get_missing_dates():
    """Get list of missing dates from BigQuery"""
    query = """
    WITH date_range AS (
      SELECT DATE_ADD(DATE('2022-01-01'), INTERVAL day DAY) as date
      FROM UNNEST(GENERATE_ARRAY(0, DATE_DIFF(DATE('2025-12-18'), DATE('2022-01-01'), DAY))) as day
    ),
    actual_dates AS (
      SELECT DISTINCT CAST(settlementDate AS DATE) as date
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
    )
    SELECT dr.date as missing_date
    FROM date_range dr
    LEFT JOIN actual_dates ad ON dr.date = ad.date
    WHERE ad.date IS NULL
    ORDER BY dr.date
    """

    result = client.query(query).to_dataframe()
    return [row.missing_date for _, row in result.iterrows()]

def fetch_system_prices(date, settlement_period):
    """Fetch system prices for a specific date and settlement period"""
    date_str = date.strftime('%Y-%m-%d')

    # Path-based API endpoint
    url = f"{BASE_URL}/balancing/settlement/system-prices/{date_str}/{settlement_period}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data.get('data', [])

    except Exception as e:
        print(f"  ⚠️ Error fetching {date_str} SP{settlement_period}: {e}")
        return []

def fix_datetime(dt_str):
    """Fix datetime format for BigQuery"""
    if dt_str and 'Z' in dt_str:
        return dt_str.replace('Z', '').replace('T', ' ')
    return dt_str

def transform_record(record):
    """Transform API record to BigQuery schema (all 30 fields including metadata)"""
    ingested_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    return {
        # Core DISEBSP fields
        'settlementDate': fix_datetime(record.get('settlementDate')),
        'settlementPeriod': record.get('settlementPeriod'),
        'startTime': fix_datetime(record.get('startTime')),
        'createdDateTime': fix_datetime(record.get('createdDateTime')),
        'systemSellPrice': record.get('systemSellPrice'),
        'systemBuyPrice': record.get('systemBuyPrice'),
        'bsadDefaulted': record.get('bsadDefaulted'),
        'priceDerivationCode': record.get('priceDerivationCode'),
        'reserveScarcityPrice': record.get('reserveScarcityPrice', 0.0),
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

        # Metadata fields (underscore prefix - critical!)
        '_dataset': 'COSTS',
        '_window_from_utc': fix_datetime(record.get('startTime', '')),
        '_window_to_utc': fix_datetime(record.get('startTime', '')),
        '_ingested_utc': ingested_utc,
        '_source_columns': 'settlementDate,settlementPeriod,systemSellPrice,systemBuyPrice',
        '_source_api': 'DISEBSP',
        '_hash_source_cols': '',
        '_hash_key': f"{record.get('settlementDate', '')}_{record.get('settlementPeriod', '')}"
    }

def backfill_date(date):
    """Backfill all settlement periods for a specific date"""
    all_records = []

    for sp in range(1, 51):  # 50 settlement periods per day
        records = fetch_system_prices(date, sp)

        if records:
            for record in records:
                all_records.append(transform_record(record))

        time.sleep(0.05)  # Rate limiting

    return all_records

def upload_to_bigquery(records):
    """Upload records to BigQuery"""
    if not records:
        return 0

    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    # Use load job for reliability
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    try:
        job = client.load_table_from_json(records, table_ref, job_config=job_config)
        job.result()
        return len(records)
    except Exception as e:
        print(f"  ❌ Upload error: {e}")
        return 0

def main():
    """Main backfill execution"""

    print("=" * 70)
    print("bmrs_costs Backfill - Missing Days")
    print("=" * 70)
    print()

    # Get missing dates
    missing_dates = get_missing_dates()

    print(f"Total missing dates: {len(missing_dates)}")
    print()

    if not missing_dates:
        print("✅ No missing dates - table is complete!")
        return

    total_uploaded = 0

    for idx, date in enumerate(missing_dates, 1):
        print(f"[{idx}/{len(missing_dates)}] Processing {date}...")

        records = backfill_date(date)

        if records:
            uploaded = upload_to_bigquery(records)
            total_uploaded += uploaded
            print(f"  ✅ Uploaded {uploaded} records")
        else:
            print(f"  ⚠️ No data available")

        # Brief pause between dates
        time.sleep(0.5)

    print()
    print("=" * 70)
    print(f"✅ Backfill Complete!")
    print(f"   Total records uploaded: {total_uploaded:,}")
    print("=" * 70)

if __name__ == "__main__":
    main()
