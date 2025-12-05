#!/usr/bin/env python3
"""
Deduplicate bmrs_costs table - Remove 55k redundant records
Created: 5 December 2025
Purpose: Clean up historical duplicates (2022-Oct 27) from original ingestion
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime
import sys

# Config
CREDENTIALS_FILE = '/home/george/inner-cinema-credentials.json'
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'bmrs_costs'
BACKUP_SUFFIX = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

print("=" * 80)
print("BMRS_COSTS DEDUPLICATION")
print("=" * 80)
print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print()

# Initialize BigQuery client
try:
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    client = bigquery.Client(project=BQ_PROJECT, credentials=creds, location='US')
    print(f"✅ Connected to BigQuery: {BQ_PROJECT}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Step 1: Analyze current state
print("\n" + "=" * 80)
print("STEP 1: Analyze Current Table")
print("=" * 80)

query = f"""
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT CONCAT(CAST(DATE(settlementDate) AS STRING), '-', CAST(settlementPeriod AS STRING))) as unique_periods,
    COUNT(*) - COUNT(DISTINCT CONCAT(CAST(DATE(settlementDate) AS STRING), '-', CAST(settlementPeriod AS STRING))) as duplicate_rows
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
"""

try:
    df = client.query(query).to_dataframe()
    print(df.to_string(index=False))
    
    total_rows = df['total_rows'].iloc[0]
    unique_periods = df['unique_periods'].iloc[0]
    duplicate_rows = df['duplicate_rows'].iloc[0]
    
    print(f"\n📊 Summary:")
    print(f"   Total rows: {total_rows:,}")
    print(f"   Unique settlement periods: {unique_periods:,}")
    print(f"   Duplicate rows to remove: {duplicate_rows:,}")
    print(f"   Reduction: {100 * duplicate_rows / total_rows:.1f}%")
    
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    sys.exit(1)

# Confirmation
print("\n" + "=" * 80)
print("⚠️  WARNING: This will modify production data")
print("=" * 80)
print(f"Operations:")
print(f"  1. Create backup: {BQ_TABLE}_backup_{BACKUP_SUFFIX}")
print(f"  2. Create deduplicated table: {BQ_TABLE}_deduped")
print(f"  3. Verify deduplication (you will review before continuing)")
print(f"  4. Replace original table (manual approval required)")
print()

response = input("Proceed with backup and deduplication? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Aborted by user")
    sys.exit(0)

# Step 2: Create backup
print("\n" + "=" * 80)
print("STEP 2: Create Backup Table")
print("=" * 80)

backup_table = f"{BQ_TABLE}_backup_{BACKUP_SUFFIX}"
print(f"Creating: {BQ_PROJECT}.{BQ_DATASET}.{backup_table}")

query = f"""
CREATE TABLE `{BQ_PROJECT}.{BQ_DATASET}.{backup_table}` AS
SELECT * FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
"""

try:
    job = client.query(query)
    job.result()
    print(f"✅ Backup created: {backup_table}")
    
    # Verify backup
    query_verify = f"SELECT COUNT(*) as count FROM `{BQ_PROJECT}.{BQ_DATASET}.{backup_table}`"
    backup_count = client.query(query_verify).to_dataframe()['count'].iloc[0]
    print(f"   Backup row count: {backup_count:,}")
    
    if backup_count != total_rows:
        print(f"❌ Backup verification failed! Expected {total_rows:,}, got {backup_count:,}")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Backup failed: {e}")
    sys.exit(1)

# Step 3: Create deduplicated table
print("\n" + "=" * 80)
print("STEP 3: Create Deduplicated Table")
print("=" * 80)

deduped_table = f"{BQ_TABLE}_deduped"
print(f"Creating: {BQ_PROJECT}.{BQ_DATASET}.{deduped_table}")
print("Strategy: Keep most recent ingestion (_ingested_utc DESC)")

query = f"""
CREATE OR REPLACE TABLE `{BQ_PROJECT}.{BQ_DATASET}.{deduped_table}` AS
SELECT * EXCEPT(row_num)
FROM (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY DATE(settlementDate), settlementPeriod 
            ORDER BY _ingested_utc DESC
        ) as row_num
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
)
WHERE row_num = 1
"""

try:
    job = client.query(query)
    job.result()
    print(f"✅ Deduplicated table created: {deduped_table}")
    
except Exception as e:
    print(f"❌ Deduplication failed: {e}")
    sys.exit(1)

# Step 4: Verify deduplication
print("\n" + "=" * 80)
print("STEP 4: Verify Deduplication")
print("=" * 80)

# Check row count
query_count = f"SELECT COUNT(*) as count FROM `{BQ_PROJECT}.{BQ_DATASET}.{deduped_table}`"
deduped_count = client.query(query_count).to_dataframe()['count'].iloc[0]
print(f"Deduplicated row count: {deduped_count:,}")
print(f"Expected: ~{unique_periods:,}")
print(f"Match: {'✅ YES' if deduped_count == unique_periods else '❌ NO'}")

# Check for remaining duplicates
query_dup_check = f"""
SELECT COUNT(*) as dup_count
FROM (
    SELECT 
        DATE(settlementDate) as date,
        settlementPeriod,
        COUNT(*) as cnt
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{deduped_table}`
    GROUP BY date, settlementPeriod
    HAVING COUNT(*) > 1
)
"""

dup_check = client.query(query_dup_check).to_dataframe()['dup_count'].iloc[0]
print(f"\nDuplicates remaining: {dup_check}")
if dup_check == 0:
    print("✅ NO DUPLICATES - Deduplication successful!")
else:
    print(f"❌ Still has {dup_check} duplicates - FAILED")
    sys.exit(1)

# Compare date ranges
query_ranges = f"""
SELECT 
    'Original' as table_name,
    MIN(DATE(settlementDate)) as earliest,
    MAX(DATE(settlementDate)) as latest,
    COUNT(DISTINCT DATE(settlementDate)) as distinct_days
FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
UNION ALL
SELECT 
    'Deduplicated' as table_name,
    MIN(DATE(settlementDate)) as earliest,
    MAX(DATE(settlementDate)) as latest,
    COUNT(DISTINCT DATE(settlementDate)) as distinct_days
FROM `{BQ_PROJECT}.{BQ_DATASET}.{deduped_table}`
"""

df_ranges = client.query(query_ranges).to_dataframe()
print("\nDate Range Comparison:")
print(df_ranges.to_string(index=False))

# Sample price comparison
query_price_sample = f"""
WITH sample_periods AS (
    SELECT DATE(settlementDate) as date, settlementPeriod
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
    WHERE DATE(settlementDate) >= '2025-11-01'
    GROUP BY date, settlementPeriod
    HAVING COUNT(*) > 1
    LIMIT 10
)
SELECT 
    'Original' as source,
    sp.date,
    sp.settlementPeriod,
    AVG(o.systemSellPrice) as avg_price
FROM sample_periods sp
JOIN `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}` o
    ON DATE(o.settlementDate) = sp.date 
    AND o.settlementPeriod = sp.settlementPeriod
GROUP BY source, sp.date, sp.settlementPeriod
UNION ALL
SELECT 
    'Deduplicated' as source,
    sp.date,
    sp.settlementPeriod,
    d.systemSellPrice as avg_price
FROM sample_periods sp
JOIN `{BQ_PROJECT}.{BQ_DATASET}.{deduped_table}` d
    ON DATE(d.settlementDate) = sp.date 
    AND d.settlementPeriod = sp.settlementPeriod
ORDER BY date, settlementPeriod, source
"""

df_prices = client.query(query_price_sample).to_dataframe()
print("\nPrice Comparison (sample duplicate periods):")
print(df_prices.to_string(index=False))

# Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print(f"✅ Backup created: {backup_table} ({total_rows:,} rows)")
print(f"✅ Deduplicated table: {deduped_table} ({deduped_count:,} rows)")
print(f"✅ Duplicates removed: {total_rows - deduped_count:,} rows ({100 * (total_rows - deduped_count) / total_rows:.1f}%)")
print(f"✅ No duplicates remaining: {dup_check == 0}")
print(f"✅ Date ranges match: {df_ranges.iloc[0]['earliest'] == df_ranges.iloc[1]['earliest']}")
print()

# Final step - manual approval
print("=" * 80)
print("READY FOR FINAL STEP: Replace Original Table")
print("=" * 80)
print("⚠️  MANUAL ACTION REQUIRED")
print()
print("If verification looks good, run these commands:")
print()
print(f"# 1. Drop original table")
print(f"bq rm -f {BQ_PROJECT}:{BQ_DATASET}.{BQ_TABLE}")
print()
print(f"# 2. Rename deduplicated table to original")
print(f"bq cp {BQ_PROJECT}:{BQ_DATASET}.{deduped_table} {BQ_PROJECT}:{BQ_DATASET}.{BQ_TABLE}")
print()
print(f"# 3. Drop temporary deduped table")
print(f"bq rm -f {BQ_PROJECT}:{BQ_DATASET}.{deduped_table}")
print()
print(f"# 4. (Optional) Drop backup after confirming everything works")
print(f"# bq rm -f {BQ_PROJECT}:{BQ_DATASET}.{backup_table}")
print()
print("=" * 80)
print(f"✅ Deduplication preparation complete!")
print("=" * 80)
