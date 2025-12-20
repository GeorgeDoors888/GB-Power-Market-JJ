#!/usr/bin/env python3
"""
REMIT Historical Backfill - Ingest Last 30 Days
Fetches REMIT (outages/unavailability) data from Elexon API and uploads to BigQuery
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "bmrs_remit_iris"  # Match IRIS real-time table (30 fields)

client = bigquery.Client(project=PROJECT_ID, location="US")

# Elexon REMIT API endpoint
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ENDPOINT = "/datasets/REMIT"

def fetch_remit_data(from_date, to_date):
    """
    Fetch REMIT data for date range

    Args:
        from_date: datetime object (start)
        to_date: datetime object (end)

    Returns:
        List of REMIT records
    """
    # Format dates as RFC 3339 (required by Elexon API)
    from_str = from_date.strftime('%Y-%m-%dT00:00:00Z')
    to_str = to_date.strftime('%Y-%m-%dT23:59:59Z')

    url = f"{BASE_URL}{ENDPOINT}"
    params = {
        'publishDateTimeFrom': from_str,
        'publishDateTimeTo': to_str,
        'format': 'json'
    }

    print(f"Fetching REMIT data: {from_str} to {to_str}")

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    return data.get('data', [])

def create_table_if_not_exists():
    """Create REMIT table in BigQuery if it doesn't exist"""
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    schema = [
        bigquery.SchemaField("mrid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("participantId", "STRING"),
        bigquery.SchemaField("assetId", "STRING"),
        bigquery.SchemaField("assetType", "STRING"),
        bigquery.SchemaField("eventType", "STRING"),
        bigquery.SchemaField("unavailabilityType", "STRING"),
        bigquery.SchemaField("fuelType", "STRING"),
        bigquery.SchemaField("eventStatus", "STRING"),
        bigquery.SchemaField("eventStartTime", "TIMESTAMP"),
        bigquery.SchemaField("eventEndTime", "TIMESTAMP"),
        bigquery.SchemaField("normalCapacity", "FLOAT"),
        bigquery.SchemaField("availableCapacity", "FLOAT"),
        bigquery.SchemaField("unavailableCapacity", "FLOAT"),
        bigquery.SchemaField("affectedUnit", "STRING"),
        bigquery.SchemaField("cause", "STRING"),
        bigquery.SchemaField("remarks", "STRING"),
        bigquery.SchemaField("publishDateTime", "TIMESTAMP"),
        bigquery.SchemaField("bmUnit", "STRING"),
        bigquery.SchemaField("nationalGridBmUnit", "STRING"),
        bigquery.SchemaField("ingestion_timestamp", "TIMESTAMP"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="eventStartTime"
    )
    table.clustering_fields = ["bmUnit", "fuelType", "unavailabilityType"]

    try:
        table = client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"Table {table_id} already exists")
        else:
            raise e

def upload_to_bigquery(records):
    """Upload REMIT records to BigQuery"""
    if not records:
        print("No records to upload")
        return

    # Transform records to match schema
    import json
    from datetime import datetime

    # Get current timestamp for ingestion
    now_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    for record in records:
        # Add ingested_utc as TIMESTAMP (YYYY-MM-DD HH:MM:SS format, no Z)
        record['ingested_utc'] = now_timestamp

        # Convert ISO 8601 strings to DATETIME format (remove Z suffix)
        for field in ['publishTime', 'createdTime', 'eventStartTime', 'eventEndTime']:
            if field in record and record[field]:
                record[field] = record[field].replace('Z', '')

        # Convert outageProfile array to JSON string if present
        if 'outageProfile' in record and isinstance(record['outageProfile'], list):
            record['outageProfile'] = json.dumps(record['outageProfile'])

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    errors = client.insert_rows_json(table_id, records)

    if errors:
        print(f"❌ Errors uploading to BigQuery: {errors}")
    else:
        print(f"✅ Uploaded {len(records)} REMIT records to {table_id}")

def ingest_date_range(start_date, end_date, chunk_days=1):
    """
    Ingest REMIT data for date range in chunks

    Args:
        start_date: datetime.date
        end_date: datetime.date
        chunk_days: Number of days per API call (default 1 - API maximum confirmed)
    """
    current = start_date

    while current <= end_date:
        chunk_end = min(current + timedelta(days=chunk_days - 1), end_date)

        try:
            records = fetch_remit_data(
                datetime.combine(current, datetime.min.time()),
                datetime.combine(chunk_end, datetime.max.time())
            )

            if records:
                upload_to_bigquery(records)
            else:
                print(f"No data for {current} to {chunk_end}")

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error processing {current} to {chunk_end}: {e}")

        current = chunk_end + timedelta(days=1)

def main():
    """Main function to backfill last 30 days of REMIT data"""
    print("=" * 80)
    print("REMIT Historical Backfill - Last 30 Days")
    print("=" * 80)

    # Skip table creation - bmrs_remit_iris already exists with correct schema
    # create_table_if_not_exists()  # DISABLED - table exists

    # Calculate date range (last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    print(f"\nIngesting REMIT data from {start_date} to {end_date}")
    print(f"Target table: {PROJECT_ID}.{DATASET}.{TABLE}")
    print()

    # Ingest data
    ingest_date_range(start_date, end_date)

    # Verify results
    print("\n" + "=" * 80)
    print("Verification Query")
    print("=" * 80)

    query = f"""
    SELECT
        COUNT(*) as total_records,
        MIN(eventStartTime) as earliest_event,
        MAX(eventStartTime) as latest_event,
        COUNT(DISTINCT affectedUnit) as unique_units,
        COUNT(DISTINCT fuelType) as fuel_types
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    WHERE eventStartTime >= DATETIME('{start_date}')
    """

    result = client.query(query).to_dataframe()
    print(result.to_string(index=False))

    print("\n✅ REMIT backfill complete!")
    print("\nNext steps:")
    print("1. SSH to AlmaLinux server: ssh root@94.237.55.234")
    print("2. Restart IRIS pipeline: systemctl restart iris-pipeline")
    print("3. Monitor logs: tail -f /opt/iris-pipeline/logs/iris_uploader.log")

if __name__ == "__main__":
    main()
