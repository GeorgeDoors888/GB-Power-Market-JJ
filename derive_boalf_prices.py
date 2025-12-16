#!/usr/bin/env python3
"""
BOALF Price Derivation Script
==============================

PURPOSE:
Derive acceptancePrice, acceptanceVolume, acceptanceType for BOALF acceptances
by matching with BOD (bid-offer data) submissions.

PROBLEM:
Elexon BMRS API /datasets/BOALF does NOT include price fields:
- ❌ acceptancePrice (£/MWh)
- ❌ acceptanceVolume (MWh) 
- ❌ acceptanceType (BID/OFFER)

SOLUTION:
Join bmrs_boalf (acceptances) + bmrs_bod (bid-offer submissions WITH prices)
to derive missing fields.

MATCHING LOGIC:
1. Join on: bmUnit, settlementDate, settlementPeriod
2. Derive acceptanceType:
   - OFFER if levelTo > levelFrom (generator increasing output)
   - BID if levelTo < levelFrom (generator decreasing output)
   - UNKNOWN if levelFrom == levelTo (no MW change)
3. Derive acceptancePrice:
   - OFFER → use BOD.offer price
   - BID → use BOD.bid price
4. Derive acceptanceVolume: ABS(levelTo - levelFrom) MW
5. Handle duplicates: Same acceptance may match multiple BOD pairIds
   → Use DISTINCT ON or filter to single best match
6. Filter extremes: BOD prices of ±£99999 indicate missing/default values

DATA COVERAGE:
- bmrs_bod: 2022-01-01 to 2025-10-28 (391M rows, 1957 units)
- bmrs_boalf: 2022-01-01 to 2025-11-04 (11.5M rows, 672 units)

USAGE:
python3 derive_boalf_prices.py --start 2025-10-01 --end 2025-10-31
python3 derive_boalf_prices.py --start 2025-10-17 --end 2025-10-17  # Single day test
"""

import argparse
import logging
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('derive_boalf_prices.log'),
        logging.StreamHandler()
    ]
)

# BigQuery configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# Schema for bmrs_boalf_complete
BOALF_COMPLETE_SCHEMA = [
    bigquery.SchemaField('acceptanceNumber', 'STRING'),
    bigquery.SchemaField('acceptanceTime', 'TIMESTAMP'),
    bigquery.SchemaField('bmUnit', 'STRING'),
    bigquery.SchemaField('settlementDate', 'TIMESTAMP'),
    bigquery.SchemaField('settlementPeriod', 'INTEGER'),
    bigquery.SchemaField('timeFrom', 'STRING'),
    bigquery.SchemaField('timeTo', 'STRING'),
    bigquery.SchemaField('levelFrom', 'INTEGER'),
    bigquery.SchemaField('levelTo', 'INTEGER'),
    
    # Derived fields
    bigquery.SchemaField('acceptancePrice', 'FLOAT'),
    bigquery.SchemaField('acceptanceVolume', 'FLOAT'),
    bigquery.SchemaField('acceptanceType', 'STRING'),
    
    # Elexon B1610 Section 4.3 compliance validation
    bigquery.SchemaField('validation_flag', 'STRING'),  # Valid, Outlier, SO_Test, Low_Volume, Unmatched
    
    # Metadata fields
    bigquery.SchemaField('soFlag', 'BOOLEAN'),
    bigquery.SchemaField('storFlag', 'BOOLEAN'),
    bigquery.SchemaField('rrFlag', 'BOOLEAN'),
    bigquery.SchemaField('deemedBoFlag', 'BOOLEAN'),
    
    # Source tracking
    bigquery.SchemaField('_price_source', 'STRING'),  # BOD_MATCH, BOD_REALTIME, UNMATCHED
    bigquery.SchemaField('_matched_pairId', 'STRING'),
    bigquery.SchemaField('_ingested_utc', 'TIMESTAMP'),
]


def derive_prices_for_period(start_date, end_date):
    """
    Derive acceptance prices for a date range by joining BOALF + BOD
    
    Returns: pandas DataFrame with complete BOALF data including derived prices
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    logging.info(f"Deriving acceptance prices for {start_date} to {end_date}")
    
    query = f"""
    WITH boalf_data AS (
      -- Get all acceptances in period
      SELECT 
        acceptanceNumber,
        acceptanceTime,
        bmUnit,
        settlementDate,
        settlementPeriodFrom as settlementPeriod,
        timeFrom,
        timeTo,
        levelFrom,
        levelTo,
        soFlag,
        storFlag,
        rrFlag,
        deemedBoFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE DATE(settlementDate) BETWEEN '{start_date}' AND '{end_date}'
    ),
    
    bod_data AS (
      -- Get bid-offer submissions for matching
      -- Filter per Elexon B1610 Section 4.3: |Price| > £1,000/MWh = non-physical
      SELECT 
        bmUnit,
        settlementDate,
        settlementPeriod,
        pairId,
        offer,
        bid
      FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
      WHERE DATE(settlementDate) BETWEEN '{start_date}' AND '{end_date}'
        -- Elexon regulatory limit: ±£1,000/MWh for valid commercial acceptances
        AND ABS(COALESCE(offer, 0)) <= 1000
        AND ABS(COALESCE(bid, 0)) <= 1000
    ),
    
    matched AS (
      SELECT 
        boalf.acceptanceNumber,
        boalf.acceptanceTime,
        boalf.bmUnit,
        boalf.settlementDate,
        boalf.settlementPeriod,
        boalf.timeFrom,
        boalf.timeTo,
        boalf.levelFrom,
        boalf.levelTo,
        boalf.soFlag,
        boalf.storFlag,
        boalf.rrFlag,
        boalf.deemedBoFlag,
        
        -- Derive acceptance type
        CASE 
          WHEN boalf.levelTo > boalf.levelFrom THEN 'OFFER'
          WHEN boalf.levelTo < boalf.levelFrom THEN 'BID'
          ELSE 'UNKNOWN'
        END as acceptanceType,
        
        -- Derive acceptance price
        CASE
          WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer
          WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid
          ELSE NULL
        END as acceptancePrice,
        
        -- Derive acceptance volume (MW)
        ABS(boalf.levelTo - boalf.levelFrom) as acceptanceVolume,
        
        -- Validation flag per Elexon B1610 Section 4.3 guidance
        CASE
          WHEN boalf.soFlag = TRUE THEN 'SO_Test'  -- System Operator test records
          WHEN ABS(boalf.levelTo - boalf.levelFrom) < 0.001 THEN 'Low_Volume'
          WHEN bod.pairId IS NOT NULL AND ABS(
            CASE WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer
                 WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid
                 ELSE 0 END
          ) > 1000 THEN 'Price_Outlier'
          WHEN bod.pairId IS NOT NULL THEN 'Valid'
          ELSE 'Unmatched'
        END as validation_flag,
        
        -- Source tracking
        CASE
          WHEN bod.pairId IS NOT NULL THEN 'BOD_MATCH'
          ELSE 'UNMATCHED'
        END as _price_source,
        
        bod.pairId as _matched_pairId,
        
        -- Rank to handle duplicates (same acceptance matched to multiple BOD pairs)
        ROW_NUMBER() OVER (
          PARTITION BY boalf.acceptanceNumber 
          ORDER BY bod.pairId
        ) as match_rank
        
      FROM boalf_data boalf
      LEFT JOIN bod_data bod
        ON boalf.bmUnit = bod.bmUnit
        AND DATE(boalf.settlementDate) = DATE(bod.settlementDate)
        AND boalf.settlementPeriod = bod.settlementPeriod
    )
    
    -- Return only best match per acceptance (rank 1)
    SELECT 
      acceptanceNumber,
      acceptanceTime,
      bmUnit,
      settlementDate,
      settlementPeriod,
      timeFrom,
      timeTo,
      levelFrom,
      levelTo,
      acceptancePrice,
      acceptanceVolume,
      acceptanceType,
      validation_flag,
      soFlag,
      storFlag,
      rrFlag,
      deemedBoFlag,
      _price_source,
      _matched_pairId,
      CURRENT_TIMESTAMP() as _ingested_utc
    FROM matched
    WHERE match_rank = 1  -- Only take first match to avoid duplicates
    ORDER BY settlementDate, settlementPeriod, acceptanceNumber
    """
    
    logging.info("Executing query...")
    df = client.query(query).to_dataframe()
    
    # Convert data types for BigQuery compatibility
    if 'acceptanceNumber' in df.columns:
        df['acceptanceNumber'] = df['acceptanceNumber'].astype(str)
    if '_matched_pairId' in df.columns:
        df['_matched_pairId'] = df['_matched_pairId'].astype(str)
    if 'settlementPeriod' in df.columns:
        df['settlementPeriod'] = df['settlementPeriod'].fillna(0).astype(int)
    if 'levelFrom' in df.columns:
        df['levelFrom'] = df['levelFrom'].fillna(0).astype(int)
    if 'levelTo' in df.columns:
        df['levelTo'] = df['levelTo'].fillna(0).astype(int)
    
    # Log statistics
    total = len(df)
    matched = df['_price_source'].eq('BOD_MATCH').sum()
    match_pct = (matched / total * 100) if total > 0 else 0
    
    logging.info(f"Results: {total:,} acceptances")
    logging.info(f"  Matched with BOD prices: {matched:,} ({match_pct:.1f}%)")
    logging.info(f"  Unmatched: {total - matched:,} ({100 - match_pct:.1f}%)")
    
    # Validation flag breakdown
    if 'validation_flag' in df.columns:
        flag_counts = df['validation_flag'].value_counts()
        logging.info(f"\n  Validation Breakdown (Elexon B1610 Section 4.3):")
        for flag, count in flag_counts.items():
            pct = (count / total * 100) if total > 0 else 0
            logging.info(f"    {flag}: {count:,} ({pct:.1f}%)")
    
    if matched > 0:
        price_stats = df[df['acceptancePrice'].notna()]['acceptancePrice'].describe()
        logging.info(f"\n  Price Statistics:")
        logging.info(f"    Range: £{price_stats['min']:.2f} to £{price_stats['max']:.2f}/MWh")
        logging.info(f"    Average: £{price_stats['mean']:.2f}/MWh")
        logging.info(f"    Median: £{price_stats['50%']:.2f}/MWh")
    
    # Type breakdown
    type_counts = df['acceptanceType'].value_counts()
    logging.info(f"\n  Acceptance Types: {type_counts.to_dict()}")
    
    return df


def upload_to_bigquery(df, table_name='bmrs_boalf_complete', mode='append'):
    """Upload derived data to BigQuery"""
    
    if df.empty:
        logging.warning("No data to upload")
        return 0
    
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    # Create table if it doesn't exist
    try:
        client.get_table(table_id)
        logging.info(f"Table {table_id} exists")
    except Exception:
        logging.info(f"Creating table {table_id}...")
        table = bigquery.Table(table_id, schema=BOALF_COMPLETE_SCHEMA)
        
        # Partition by date, cluster by bmUnit for efficient VLP queries
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="settlementDate"
        )
        table.clustering_fields = ["bmUnit"]
        
        client.create_table(table)
        logging.info(f"✅ Created table {table_id}")
    
    # Upload data
    logging.info(f"Uploading {len(df)} rows to {table_id}...")
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND if mode == 'append' else bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=BOALF_COMPLETE_SCHEMA
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    logging.info(f"✅ Uploaded {len(df):,} rows to {table_id}")
    
    return len(df)


def main():
    parser = argparse.ArgumentParser(description='Derive BOALF acceptance prices from BOD data')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Generate data but do not upload')
    parser.add_argument('--table', default='bmrs_boalf_complete', help='Destination table name')
    
    args = parser.parse_args()
    
    logging.info("=" * 100)
    logging.info("BOALF Price Derivation - BOD Matching Approach")
    logging.info("=" * 100)
    logging.info(f"Period: {args.start} to {args.end}")
    logging.info(f"Destination: {PROJECT_ID}.{DATASET}.{args.table}")
    logging.info(f"Dry run: {args.dry_run}")
    logging.info("=" * 100)
    
    # Derive prices
    df = derive_prices_for_period(args.start, args.end)
    
    if df.empty:
        logging.warning("No data generated - check date range and source tables")
        return
    
    # Upload to BigQuery
    if not args.dry_run:
        rows_uploaded = upload_to_bigquery(df, table_name=args.table)
        logging.info(f"✅ Process complete - {rows_uploaded:,} rows uploaded")
    else:
        logging.info("DRY RUN - Data generated but not uploaded")
        logging.info(f"\n📋 Preview (first 10 rows):")
        preview_cols = ['acceptanceNumber', 'bmUnit', 'settlementPeriod', 'acceptanceType', 'acceptancePrice', 'acceptanceVolume', '_price_source']
        print(df[preview_cols].head(10).to_string(index=False))
        
        # Show price distribution by type
        logging.info(f"\n📊 Price Distribution by Acceptance Type:")
        for acc_type in ['BID', 'OFFER', 'UNKNOWN']:
            type_df = df[df['acceptanceType'] == acc_type]['acceptancePrice']
            if len(type_df) > 0:
                logging.info(f"\n{acc_type}:")
                logging.info(f"  Count: {len(type_df):,}")
                logging.info(f"  Avg: £{type_df.mean():.2f}/MWh")
                logging.info(f"  Min: £{type_df.min():.2f}/MWh")
                logging.info(f"  Max: £{type_df.max():.2f}/MWh")
                logging.info(f"  Median: £{type_df.median():.2f}/MWh")
    
    logging.info("\n" + "=" * 100)


if __name__ == '__main__':
    main()
