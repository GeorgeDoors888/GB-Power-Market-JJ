#!/usr/bin/env python3
"""
Run BigQuery Deduplication
Removes duplicate records from bmrs_fuelinst and bmrs_mid tables
"""

from google.cloud import bigquery
from datetime import datetime
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"

def run_query(client, query, description):
    """Run a BigQuery query and print results"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print('='*60)
    
    try:
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert to list to get row count
        rows = list(results)
        
        if not rows:
            print("✅ No results (query successful)")
            return None
        
        # Print results
        for row in rows:
            print(dict(row))
        
        print(f"\n✅ {len(rows)} rows returned")
        return rows
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║  BIGQUERY DATA DEDUPLICATION                                ║
║  Tables: bmrs_fuelinst, bmrs_mid                           ║
╚════════════════════════════════════════════════════════════╝
""")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # =================================================================
    # PART 1: ANALYZE bmrs_fuelinst DUPLICATES
    # =================================================================
    
    print("\n\n📊 PART 1: ANALYZE bmrs_fuelinst DUPLICATES")
    
    # Check duplicate count
    query1 = f"""
    SELECT 
        COUNT(*) as duplicate_groups,
        SUM(record_count - 1) as records_to_delete,
        SUM(record_count) as total_duplicate_records
    FROM (
        SELECT 
            settlementDate,
            settlementPeriod,
            fuelType,
            COUNT(*) as record_count
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
        GROUP BY settlementDate, settlementPeriod, fuelType
        HAVING COUNT(*) > 1
    )
    """
    
    results = run_query(client, query1, "bmrs_fuelinst: Duplicate Statistics")
    
    if results and results[0]['duplicate_groups'] > 0:
        print(f"\n⚠️  Found {results[0]['duplicate_groups']} duplicate groups")
        print(f"⚠️  {results[0]['records_to_delete']} records will be deleted")
        print(f"⚠️  {results[0]['total_duplicate_records']} total duplicate records")
    else:
        print("\n✅ No duplicates found in bmrs_fuelinst")
    
    # Sample duplicates
    query2 = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        fuelType,
        COUNT(*) as record_count
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
    GROUP BY settlementDate, settlementPeriod, fuelType
    HAVING COUNT(*) > 1
    ORDER BY record_count DESC
    LIMIT 10
    """
    
    run_query(client, query2, "bmrs_fuelinst: Top 10 Duplicate Groups")
    
    # =================================================================
    # PART 2: ANALYZE bmrs_mid DUPLICATES
    # =================================================================
    
    print("\n\n📊 PART 2: ANALYZE bmrs_mid DUPLICATES")
    
    # Check duplicate count
    query3 = f"""
    SELECT 
        COUNT(*) as duplicate_groups,
        SUM(record_count - 1) as records_to_delete,
        SUM(record_count) as total_duplicate_records
    FROM (
        SELECT 
            settlementDate,
            settlementPeriod,
            COUNT(*) as record_count
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
        GROUP BY settlementDate, settlementPeriod
        HAVING COUNT(*) > 1
    )
    """
    
    results = run_query(client, query3, "bmrs_mid: Duplicate Statistics")
    
    if results and results[0]['duplicate_groups'] > 0:
        print(f"\n⚠️  Found {results[0]['duplicate_groups']} duplicate groups")
        print(f"⚠️  {results[0]['records_to_delete']} records will be deleted")
    else:
        print("\n✅ No duplicates found in bmrs_mid")
    
    # Sample duplicates
    query4 = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        COUNT(*) as record_count
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
    GROUP BY settlementDate, settlementPeriod
    HAVING COUNT(*) > 1
    ORDER BY record_count DESC
    LIMIT 10
    """
    
    run_query(client, query4, "bmrs_mid: Top 10 Duplicate Groups")
    
    # =================================================================
    # PART 3: DEDUPLICATION CONFIRMATION
    # =================================================================
    
    print("\n\n" + "="*60)
    print("⚠️  READY TO DEDUPLICATE")
    print("="*60)
    print("\nThis will:")
    print("1. Create bmrs_fuelinst_dedup with unique records")
    print("2. Create bmrs_mid_dedup with unique records")
    print("3. Keep latest publishTime/ingested_utc per unique key")
    print("\nOriginal tables will NOT be modified yet.")
    print("\nAfter review, you can manually rename tables in BigQuery Console.")
    
    response = input("\n🔴 Proceed with deduplication? (type 'YES' to continue): ")
    
    if response != 'YES':
        print("\n❌ Deduplication cancelled")
        sys.exit(0)
    
    # =================================================================
    # PART 4: CREATE DEDUPLICATED bmrs_fuelinst
    # =================================================================
    
    print("\n\n📝 PART 4: CREATING bmrs_fuelinst_dedup")
    
    query5 = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_dedup` AS
    WITH ranked_records AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY settlementDate, settlementPeriod, fuelType 
                ORDER BY publishTime DESC
            ) as rn
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
    )
    SELECT * EXCEPT(rn)
    FROM ranked_records
    WHERE rn = 1
    """
    
    print("🔄 Creating deduplicated table (this may take a few minutes)...")
    run_query(client, query5, "Creating bmrs_fuelinst_dedup")
    
    # Verify
    query6 = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                             CAST(settlementPeriod AS STRING), '-', fuelType)) as unique_keys,
        MIN(settlementDate) as earliest_date,
        MAX(settlementDate) as latest_date
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_dedup`
    """
    
    run_query(client, query6, "bmrs_fuelinst_dedup: Statistics")
    
    # Check for remaining duplicates
    query7 = f"""
    SELECT COUNT(*) as remaining_duplicates
    FROM (
        SELECT 
            settlementDate,
            settlementPeriod,
            fuelType,
            COUNT(*) as cnt
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_dedup`
        GROUP BY settlementDate, settlementPeriod, fuelType
        HAVING COUNT(*) > 1
    )
    """
    
    results = run_query(client, query7, "bmrs_fuelinst_dedup: Duplicate Check")
    if results and results[0]['remaining_duplicates'] == 0:
        print("✅ No duplicates in new table!")
    
    # =================================================================
    # PART 5: CREATE DEDUPLICATED bmrs_mid
    # =================================================================
    
    print("\n\n📝 PART 5: CREATING bmrs_mid_dedup")
    
    query8 = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.bmrs_mid_dedup` AS
    WITH ranked_records AS (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY settlementDate, settlementPeriod
                ORDER BY ingested_utc DESC
            ) as rn
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
    )
    SELECT * EXCEPT(rn)
    FROM ranked_records
    WHERE rn = 1
    """
    
    print("🔄 Creating deduplicated table...")
    run_query(client, query8, "Creating bmrs_mid_dedup")
    
    # Verify
    query9 = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                             CAST(settlementPeriod AS STRING))) as unique_keys,
        MIN(settlementDate) as earliest_date,
        MAX(settlementDate) as latest_date
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid_dedup`
    """
    
    run_query(client, query9, "bmrs_mid_dedup: Statistics")
    
    # Check for remaining duplicates
    query10 = f"""
    SELECT COUNT(*) as remaining_duplicates
    FROM (
        SELECT 
            settlementDate,
            settlementPeriod,
            COUNT(*) as cnt
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid_dedup`
        GROUP BY settlementDate, settlementPeriod
        HAVING COUNT(*) > 1
    )
    """
    
    results = run_query(client, query10, "bmrs_mid_dedup: Duplicate Check")
    if results and results[0]['remaining_duplicates'] == 0:
        print("✅ No duplicates in new table!")
    
    # =================================================================
    # PART 6: SUMMARY
    # =================================================================
    
    print("\n\n" + "="*60)
    print("✅ DEDUPLICATION COMPLETE")
    print("="*60)
    print("\nNew tables created:")
    print("  • bmrs_fuelinst_dedup")
    print("  • bmrs_mid_dedup")
    print("\nNext steps:")
    print("1. Review the new tables in BigQuery Console")
    print("2. Test queries with new tables")
    print("3. When ready, rename tables:")
    print("   a. bmrs_fuelinst → bmrs_fuelinst_backup_20251030")
    print("   b. bmrs_fuelinst_dedup → bmrs_fuelinst")
    print("   c. bmrs_mid → bmrs_mid_backup_20251030")
    print("   d. bmrs_mid_dedup → bmrs_mid")
    print("4. Test dashboard")
    print("5. Delete backup tables after 7 days")
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
