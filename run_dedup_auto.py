#!/usr/bin/env python3
"""
Run BigQuery Deduplication - Auto Mode (No Prompts)
"""

from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"

def main():
    print("="*60)
    print("🚀 STARTING AUTOMATIC DEDUPLICATION")
    print("="*60)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # ====================================================================================
    # DEDUPLICATE bmrs_fuelinst
    # ====================================================================================
    
    print("\n📝 Creating bmrs_fuelinst_dedup...")
    
    query1 = f"""
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
    
    try:
        client.query(query1).result()
        print("✅ bmrs_fuelinst_dedup created")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Verify
    query2 = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                             CAST(settlementPeriod AS STRING), '-', fuelType)) as unique_keys
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_dedup`
    """
    
    results = list(client.query(query2).result())
    if results:
        print(f"   Records: {results[0]['total_records']:,}")
        print(f"   Unique keys: {results[0]['unique_keys']:,}")
    
    # ====================================================================================
    # DEDUPLICATE bmrs_mid
    # ====================================================================================
    
    print("\n📝 Creating bmrs_mid_dedup...")
    
    query3 = f"""
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
    
    try:
        client.query(query3).result()
        print("✅ bmrs_mid_dedup created")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Verify
    query4 = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                             CAST(settlementPeriod AS STRING))) as unique_keys
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid_dedup`
    """
    
    results = list(client.query(query4).result())
    if results:
        print(f"   Records: {results[0]['total_records']:,}")
        print(f"   Unique keys: {results[0]['unique_keys']:,}")
    
    print("\n" + "="*60)
    print("✅ DEDUPLICATION COMPLETE!")
    print("="*60)
    print("\nNew tables ready to use:")
    print("  • bmrs_fuelinst_dedup")
    print("  • bmrs_mid_dedup")

if __name__ == "__main__":
    main()
