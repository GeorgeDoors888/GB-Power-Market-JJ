#!/usr/bin/env python3
"""
P114 S0142 Settlement Report Ingestion - BM Unit Period Items (BPI)

Downloads and ingests S0142 (Settlement Report v11) from Elexon P114 Portal.
Provides per-BM-Unit per-settlement-period settlement data for reconciliation
with BMRS balancing mechanism revenue.

**CRITICAL**: S0142 files are PIPE-DELIMITED (|), NOT CSV format
File contains multiple record types:
- AAA: File header
- SRH: Settlement Run Header (date, run type, etc)
- SPI: System Price Information
- TRA: Trading Unit aggregates
- BPI: BM Period Items (PER BM UNIT - THIS IS WHAT WE NEED!)
- MEL/MIL: Metering information

BPI Record Format:
BPI|2__BMUNITID|ZONE|value1|value2|multiplier|value3

Example BPI records for VLP units (FBPGM002, FFSEN005):
BPI|2__FBPGM002|DEFAULT__F|0|-1.652|1.0005681|0|
BPI|2__FFSEN005|DEFAULT__F|-1.3|-0.031|1.0005681|0|

Settlement Run Types:
- II: Interim Information (earliest, released day+1)
- SF: Settlement Final
- R1: Reconciliation Run 1
- R2: Reconciliation Run 2
- R3: Reconciliation Run 3
- RF: Reconciliation Final
- DF: Default Final (last resort if no settlement)

**IMPORTANT**: Requires valid P114 scripting key from Elexon Portal
To generate key:
1. Login to https://www.elexonportal.co.uk/
2. Go to Account Settings → Scripting
3. Generate new scripting key
4. Update SCRIPTING_KEY variable below

Storage: Estimated 3-5M BPI records, 20-30GB for 2022-2025 (4 years)
Coverage: Multiple settlement runs per date (II, SF, R1, R2, R3, RF)
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import gzip
import io
import os
import sys
from typing import List, Dict, Optional

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "elexon_p114_s0142_bpi"  # New table for S0142 BPI records
LOCATION = "US"

# ⚠️ VALID KEY FROM ELEXON PORTAL (Updated: Dec 28, 2025)
SCRIPTING_KEY = "03omen6i9lhv5fa"

# P114 Portal endpoints
PORTAL_LIST_URL = "https://downloads.elexonportal.co.uk/p114/list"
PORTAL_DOWNLOAD_URL = "https://downloads.elexonportal.co.uk/p114/download"

# File filter for S0142
FILE_FILTER = "S0142"  # Settlement Report v11


def check_key_valid():
    """Test if scripting key is valid"""
    # Test key with simple list request
    test_date = datetime.now().strftime("%Y-%m-%d")
    params = {
        "key": SCRIPTING_KEY,
        "date": test_date
    }

    try:
        response = requests.get(PORTAL_LIST_URL, params=params, timeout=30)
        if response.status_code == 200 and "Scripting Error" not in response.text:
            print("✅ P114 scripting key valid")
            return True
        else:
            print(f"❌ Key validation failed: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Key validation error: {e}")
        return False


def list_available_files(date_str):
    """
    List available S0142 files for a given date

    Args:
        date_str: Date in format YYYY-MM-DD

    Returns:
        List of S0142 filenames or None if error
    """
    params = {
        "key": SCRIPTING_KEY,
        "date": date_str
    }

    try:
        response = requests.get(PORTAL_LIST_URL, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Portal returns dict with filenames as KEYS (values are file sizes)
            if isinstance(data, dict):
                all_files = list(data.keys())
                s0142_files = [f for f in all_files if f.startswith('S0142_')]
                return s0142_files
            elif isinstance(data, list):
                # Fallback for list format (older API versions?)
                s0142_files = [f for f in data if f.startswith('S0142_')]
                return s0142_files
            return []
        else:
            print(f"⚠️ List failed for {date_str}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error listing files for {date_str}: {e}")
        return None


def download_file(filename):
    """
    Download specific S0142 file

    Args:
        filename: Filename from list endpoint (e.g., S0142_20251208_II_20251215120209.gz)

    Returns:
        File content as bytes or None if error
    """
    params = {
        "key": SCRIPTING_KEY,
        "filename": filename
    }

    try:
        response = requests.get(PORTAL_DOWNLOAD_URL, params=params, timeout=60)
        if response.status_code == 200:
            return response.content
        else:
            print(f"⚠️ Download failed for {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return None


def parse_filename_metadata(filename):
    """
    Extract metadata from S0142 filename

    Format: S0142_YYYYMMDD_RUN_timestamp.gz
    Example: S0142_20251208_II_20251215120209.gz

    Returns:
        Dict with settlement_date, settlement_run, generation_timestamp
    """
    try:
        parts = filename.replace('.gz', '').split('_')
        return {
            'settlement_date': datetime.strptime(parts[1], '%Y%m%d').date(),
            'settlement_run': parts[2],  # II, SF, R1, R2, R3, RF, DF
            'generation_timestamp': datetime.strptime(parts[3], '%Y%m%d%H%M%S')
        }
    except Exception as e:
        print(f"⚠️ Filename parse error for {filename}: {e}")
        return None


def parse_s0142_file(file_content, filename):
    """
    Parse S0142 pipe-delimited file into BPI records DataFrame

    S0142 is gzipped, pipe-delimited (|), NOT CSV

    Record types:
    - AAA: File header (AAA|S0142013|D|timestamp|...)
    - SRH: Settlement Run Header (SRH|20251208|II|1|1|...)
    - SPI: System Price Info (SPI|1|21.88|21.88|P|...) - **MARKS SETTLEMENT PERIOD BOUNDARIES**
    - TRA: Trading Unit aggregate (TRA|Unit Name|volume|)
    - BPI: BM Period Item (BPI|2__BMUNITID|ZONE|val1|val2|multiplier|val3|)
    - MEL/MIL: Metering info

    **KEY DISCOVERY**: SPI records mark settlement period boundaries.
    Each SPI record has period number in field[1] and system price in field[2].
    All BPI records between two SPI markers belong to the earlier period.
    Typical: ~5,700 BPI records per settlement period, 48 periods per day.

    Returns:
        DataFrame with columns: settlement_date, settlement_period, settlement_run,
                                bm_unit_id, zone, value1, value2, multiplier, value3,
                                system_price, generation_timestamp
    """
    try:
        # Extract filename metadata
        metadata = parse_filename_metadata(filename)
        if metadata is None:
            return None

        # Decompress gzipped content
        decompressed = gzip.decompress(file_content)
        lines = decompressed.decode('utf-8').splitlines()

        print(f"   📄 File has {len(lines)} lines")

        # Parse SRH to get settlement period range
        # SRH format: SRH|YYYYMMDD|RUN|from_period|to_period|...
        period_range = (1, 48)  # Default

        # Find all SPI (System Price Info) records - these mark period boundaries
        spi_markers = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            fields = line.split('|')

            # Extract period range from SRH
            if fields[0] == 'SRH' and len(fields) >= 5:
                try:
                    from_period = int(fields[3])
                    to_period = int(fields[4])
                    period_range = (from_period, to_period)
                except:
                    pass

            # Track SPI markers (settlement period boundaries)
            elif fields[0] == 'SPI' and len(fields) >= 3:
                try:
                    period = int(fields[1])
                    system_price = float(fields[2])
                    spi_markers.append((i, period, system_price))
                except:
                    pass

        if spi_markers:
            print(f"   📊 Found {len(spi_markers)} settlement periods (range {period_range[0]}-{period_range[1]})")
        else:
            print(f"   ⚠️ No SPI markers found - settlement periods will be NULL")

        # Parse BPI records with settlement period tracking
        bpi_records = []
        current_period = None
        current_system_price = None
        spi_index = 0

        for line_num, line in enumerate(lines):
            if not line.strip():
                continue

            fields = line.split('|')

            # Update current period when we hit SPI marker
            if fields[0] == 'SPI':
                if spi_index < len(spi_markers):
                    _, current_period, current_system_price = spi_markers[spi_index]
                    spi_index += 1

            # Extract BPI records with current period
            elif fields[0] == 'BPI':
                # BPI format: BPI|2__BMUNITID|ZONE|value1|value2|multiplier|value3
                if len(fields) >= 7:
                    try:
                        # Extract BM Unit ID (remove "2__" prefix)
                        bm_unit_raw = fields[1]
                        bm_unit_id = bm_unit_raw.replace('2__', '') if bm_unit_raw.startswith('2__') else bm_unit_raw

                        bpi_records.append({
                            'bm_unit_id': bm_unit_id,
                            'zone': fields[2],
                            'value1': float(fields[3]) if fields[3] else None,
                            'value2': float(fields[4]) if fields[4] else None,
                            'multiplier': float(fields[5]) if fields[5] else None,
                            'value3': float(fields[6]) if fields[6] else None,
                            'settlement_period': current_period,
                            'system_price': current_system_price,
                        })
                    except Exception as e:
                        # Skip malformed BPI records
                        pass

        if not bpi_records:
            print(f"   ⚠️ No BPI records found in {filename}")
            return None

        # Create DataFrame
        df = pd.DataFrame(bpi_records)

        # Add metadata columns
        df['settlement_date'] = metadata['settlement_date']
        df['settlement_run'] = metadata['settlement_run']
        df['generation_timestamp'] = metadata['generation_timestamp']

        print(f"   ✅ Parsed {len(df)} BPI records")
        print(f"   📋 Unique BM Units: {df['bm_unit_id'].nunique()}")

        # Show period distribution
        if df['settlement_period'].notna().any():
            periods_with_data = df['settlement_period'].nunique()
            print(f"   ⏱️  Settlement periods: {periods_with_data} periods populated")

        # Show sample VLP units if present
        vlp_units = ['FBPGM002', 'FFSEN005']
        vlp_found = df[df['bm_unit_id'].isin(vlp_units)]
        if not vlp_found.empty:
            print(f"   🎯 VLP units found: {vlp_found['bm_unit_id'].unique().tolist()} ({len(vlp_found)} records)")

        return df

    except Exception as e:
        print(f"❌ Parse error for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_table_if_not_exists(client):
    """
    Create P114 S0142 BPI table in BigQuery

    Schema:
    - settlement_date: DATE (partition key)
    - settlement_period: INT64 (1-48, extracted from SPI markers)
    - settlement_run: STRING (II, SF, R1, R2, R3, RF, DF)
    - bm_unit_id: STRING (cluster key)
    - zone: STRING
    - value1: FLOAT64
    - value2: FLOAT64 (often MWh generation/consumption)
    - multiplier: FLOAT64 (price multiplier)
    - value3: FLOAT64
    - system_price: FLOAT64 (£/MWh from SPI records)
    - generation_timestamp: TIMESTAMP (when file was generated)
    """
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

    try:
        client.get_table(table_id)
        print(f"✅ Table {TABLE_NAME} already exists")
        return True
    except:
        print(f"📝 Creating table {TABLE_NAME}...")

        schema = [
            bigquery.SchemaField("settlement_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("settlement_period", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("settlement_run", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("bm_unit_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("zone", "STRING"),
            bigquery.SchemaField("value1", "FLOAT64"),
            bigquery.SchemaField("value2", "FLOAT64"),  # Often MWh
            bigquery.SchemaField("multiplier", "FLOAT64"),
            bigquery.SchemaField("value3", "FLOAT64"),
            bigquery.SchemaField("system_price", "FLOAT64"),  # £/MWh from SPI
            bigquery.SchemaField("generation_timestamp", "TIMESTAMP"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="settlement_date"
        )
        table.clustering_fields = ["bm_unit_id", "settlement_run"]

        client.create_table(table)
        print(f"✅ Table {TABLE_NAME} created")
        print(f"   Partition: settlement_date (DAY)")
        print(f"   Clustering: bm_unit_id, settlement_run")
        return True


def upload_to_bigquery(client, df, filename):
    """Upload DataFrame to BigQuery"""
    if df is None or df.empty:
        print(f"⚠️ No data to upload for {filename}")
        return False

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema=[
                bigquery.SchemaField("settlement_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("settlement_period", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("settlement_run", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("bm_unit_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("zone", "STRING"),
                bigquery.SchemaField("value1", "FLOAT64"),
                bigquery.SchemaField("value2", "FLOAT64"),
                bigquery.SchemaField("multiplier", "FLOAT64"),
                bigquery.SchemaField("value3", "FLOAT64"),
                bigquery.SchemaField("system_price", "FLOAT64"),
                bigquery.SchemaField("generation_timestamp", "TIMESTAMP"),
            ]
        )

        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion

        print(f"✅ Uploaded {len(df)} BPI records from {filename}")
        return True
    except Exception as e:
        print(f"❌ Upload error for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return False


def ingest_date_range(start_date, end_date, run_types=None):
    """
    Ingest P114 S0142 files for date range

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        run_types: List of run types to filter (e.g., ['RF', 'R3']) or None for all
    """
    print(f"\n🚀 P114 S0142 Settlement Report Ingestion (BPI Records)")
    print(f"📅 Date range: {start_date} to {end_date}")
    print(f"📊 Target: {TABLE_NAME}")
    if run_types:
        print(f"🔍 Filtering run types: {run_types}")
    print("="*80)

    # Validate key first
    if not check_key_valid():
        return

    # Initialize BigQuery client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Create table if needed
    create_table_if_not_exists(client)

    # Process each date
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    current = start

    total_rows = 0
    total_files = 0
    success_count = 0

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n📅 Processing {date_str}...")

        # List available S0142 files
        files = list_available_files(date_str)

        if files is None:
            print(f"⚠️ Skipping {date_str} (list failed)")
            current += timedelta(days=1)
            continue

        if not files:
            print(f"ℹ️ No S0142 files for {date_str}")
            current += timedelta(days=1)
            continue

        # Filter by run type if specified
        if run_types:
            files = [f for f in files if any(f"_{rt}_" in f for rt in run_types)]

        print(f"   Found {len(files)} S0142 file(s)")

        # Download and process each file
        for filename in files:
            print(f"   📥 Downloading {filename}...")
            content = download_file(filename)

            if content is None:
                print(f"   ⚠️ Skipping {filename}")
                continue

            # Parse S0142 pipe-delimited format
            df = parse_s0142_file(content, filename)
            if df is not None:
                # Upload to BigQuery
                if upload_to_bigquery(client, df, filename):
                    total_rows += len(df)
                    total_files += 1
                    success_count += 1

            # Rate limiting
            time.sleep(2)

        current += timedelta(days=1)
        time.sleep(1)  # Rate limit between dates

    print("\n" + "="*80)
    print(f"✅ Ingestion complete!")
    print(f"   Total BPI records uploaded: {total_rows:,}")
    print(f"   Successful files: {total_files}")
    print(f"   Date range: {start_date} to {end_date}")


def verify_data(show_vlp=True):
    """Verify ingested data and check VLP units"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    query = f"""
    SELECT
        MIN(settlement_date) as earliest_date,
        MAX(settlement_date) as latest_date,
        COUNT(*) as total_rows,
        COUNT(DISTINCT settlement_date) as distinct_dates,
        COUNT(DISTINCT bm_unit_id) as distinct_units,
        COUNT(DISTINCT settlement_run) as distinct_runs
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """

    print("\n📊 Data Verification:")
    print("="*80)

    try:
        for row in client.query(query).result():
            print(f"   Date range: {row.earliest_date} to {row.latest_date}")
            print(f"   Total BPI records: {row.total_rows:,}")
            print(f"   Distinct dates: {row.distinct_dates}")
            print(f"   Distinct BM Units: {row.distinct_units}")
            print(f"   Distinct run types: {row.distinct_runs}")

        # Check VLP units
        if show_vlp:
            vlp_query = f"""
            SELECT
                bm_unit_id,
                COUNT(*) as record_count,
                MIN(settlement_date) as earliest,
                MAX(settlement_date) as latest,
                COUNT(DISTINCT settlement_run) as run_types
            FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
            WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')
            GROUP BY bm_unit_id
            ORDER BY bm_unit_id
            """

            print("\n🎯 VLP Units (FBPGM002, FFSEN005):")
            print("-"*80)

            for row in client.query(vlp_query).result():
                print(f"   {row.bm_unit_id}:")
                print(f"      Records: {row.record_count:,}")
                print(f"      Date range: {row.earliest} to {row.latest}")
                print(f"      Settlement runs: {row.run_types}")

    except Exception as e:
        print(f"❌ Verification query failed: {e}")


def compare_with_bmrs():
    """
    Compare S0142 settlement data with BMRS balancing mechanism data

    This is the reconciliation query to validate £2.79M BMRS revenue estimate
    """
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    query = f"""
    WITH s0142_summary AS (
        SELECT
            bm_unit_id,
            settlement_date,
            settlement_run,
            COUNT(*) as bpi_records,
            SUM(value2) as total_value2_mwh
        FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
        WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')
          AND settlement_run = 'RF'  -- Reconciliation Final only
        GROUP BY bm_unit_id, settlement_date, settlement_run
    ),
    bmrs_summary AS (
        SELECT
            bmUnitId as bm_unit_id,
            CAST(settlementDate AS DATE) as settlement_date,
            COUNT(*) as bmrs_acceptances,
            SUM(acceptedVolume) as total_accepted_mwh
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
        WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')
          AND validation_flag = 'Valid'
        GROUP BY bm_unit_id, settlement_date
    )
    SELECT
        COALESCE(s.bm_unit_id, b.bm_unit_id) as bm_unit_id,
        COALESCE(s.settlement_date, b.settlement_date) as settlement_date,
        s.bpi_records,
        s.total_value2_mwh as s0142_mwh,
        b.bmrs_acceptances,
        b.total_accepted_mwh as bmrs_mwh,
        ROUND((s.total_value2_mwh - b.total_accepted_mwh) / NULLIF(b.total_accepted_mwh, 0) * 100, 2) as variance_pct
    FROM s0142_summary s
    FULL OUTER JOIN bmrs_summary b
        ON s.bm_unit_id = b.bm_unit_id
        AND s.settlement_date = b.settlement_date
    WHERE COALESCE(s.settlement_date, b.settlement_date) >= '2024-01-01'
    ORDER BY bm_unit_id, settlement_date
    LIMIT 100
    """

    print("\n🔍 S0142 vs BMRS Reconciliation:")
    print("="*80)

    try:
        results = client.query(query).result()
        for row in results:
            print(f"{row.bm_unit_id} {row.settlement_date}: S0142={row.s0142_mwh:.1f} MWh, BMRS={row.bmrs_mwh:.1f} MWh, Variance={row.variance_pct}%")
    except Exception as e:
        print(f"❌ Reconciliation query failed: {e}")
        print("Note: This requires both S0142 and BMRS data to be present")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 ingest_p114_s0142.py START_DATE END_DATE [RUN_TYPES]")
        print("Example: python3 ingest_p114_s0142.py 2025-12-08 2025-12-08")
        print("Example: python3 ingest_p114_s0142.py 2024-01-01 2024-12-31 RF,R3")
        print("\nSettlement Run Types: II, SF, R1, R2, R3, RF, DF")
        print("  II = Interim Information (earliest)")
        print("  RF = Reconciliation Final (recommended)")
        print("  DF = Default Final")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    run_types = sys.argv[3].split(',') if len(sys.argv) > 3 else None

    ingest_date_range(start_date, end_date, run_types)
    verify_data()

    # Optionally run reconciliation if data exists
    # compare_with_bmrs()
