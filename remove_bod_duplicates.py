#!/usr/bin/env python3
"""
Remove duplicate BOD entries from BigQuery based on the _dedup_key column.
Keeps only one record per unique dedup key.
"""

from google.cloud import bigquery
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def remove_duplicates_from_table(project_id, dataset_id, table_name):
    """
    Remove duplicates from a BigQuery table using _hash_key.
    Creates a new table with unique records and replaces the original.
    """
    client = bigquery.Client(project=project_id)
    
    full_table_id = f"{project_id}.{dataset_id}.{table_name}"
    temp_table_id = f"{project_id}.{dataset_id}.{table_name}_dedup_temp"
    
    logging.info(f"Checking for duplicates in {full_table_id}...")
    
    # First, check if _hash_key column exists and count duplicates
    check_query = f"""
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT _hash_key) as unique_keys,
        COUNT(*) - COUNT(DISTINCT _hash_key) as duplicate_count
    FROM `{full_table_id}`
    WHERE _hash_key IS NOT NULL
    """
    
    try:
        result = client.query(check_query).result()
        row = list(result)[0]
        total_rows = row.total_rows
        unique_keys = row.unique_keys
        duplicate_count = row.duplicate_count
        
        logging.info(f"Total rows: {total_rows:,}")
        logging.info(f"Unique keys: {unique_keys:,}")
        logging.info(f"Duplicates to remove: {duplicate_count:,}")
        
        if duplicate_count == 0:
            logging.info("✅ No duplicates found!")
            return
            
    except Exception as e:
        logging.error(f"Error checking for duplicates: {e}")
        return
    
    # Create deduplicated table using ROW_NUMBER to keep only the first occurrence
    logging.info(f"Creating deduplicated table at {temp_table_id}...")
    
    dedup_query = f"""
    CREATE OR REPLACE TABLE `{temp_table_id}` AS
    SELECT * EXCEPT(row_num)
    FROM (
        SELECT 
            *,
            ROW_NUMBER() OVER (
                PARTITION BY _hash_key 
                ORDER BY _ingested_utc DESC
            ) as row_num
        FROM `{full_table_id}`
        WHERE _hash_key IS NOT NULL
    )
    WHERE row_num = 1
    
    UNION ALL
    
    -- Also include any rows without a hash key (shouldn't exist but just in case)
    SELECT *
    FROM `{full_table_id}`
    WHERE _hash_key IS NULL
    """
    
    try:
        job = client.query(dedup_query)
        job.result()  # Wait for completion
        logging.info(f"✅ Created deduplicated temp table")
        
        # Verify the new table
        verify_query = f"SELECT COUNT(*) as count FROM `{temp_table_id}`"
        result = client.query(verify_query).result()
        new_count = list(result)[0].count
        logging.info(f"New table has {new_count:,} rows (removed {total_rows - new_count:,} duplicates)")
        
        # Drop the original table
        logging.info(f"Dropping original table {full_table_id}...")
        client.delete_table(full_table_id, not_found_ok=True)
        
        # Rename temp table to original name
        logging.info(f"Renaming temp table to {table_name}...")
        rename_query = f"""
        CREATE OR REPLACE TABLE `{full_table_id}` AS
        SELECT * FROM `{temp_table_id}`
        """
        job = client.query(rename_query)
        job.result()
        
        # Drop temp table
        client.delete_table(temp_table_id, not_found_ok=True)
        
        logging.info(f"✅ Successfully deduplicated {table_name}!")
        logging.info(f"   Removed {total_rows - new_count:,} duplicate rows")
        logging.info(f"   Final count: {new_count:,} rows")
        
    except Exception as e:
        logging.error(f"Error during deduplication: {e}")
        # Try to clean up temp table if it exists
        try:
            client.delete_table(temp_table_id, not_found_ok=True)
        except:
            pass
        raise


if __name__ == "__main__":
    PROJECT_ID = "inner-cinema-476211-u9"
    DATASET_ID = "uk_energy_prod"
    TABLE_NAME = "bmrs_bod"
    
    logging.info("=" * 60)
    logging.info("BOD Duplicate Removal Script")
    logging.info("=" * 60)
    
    try:
        remove_duplicates_from_table(PROJECT_ID, DATASET_ID, TABLE_NAME)
        logging.info("=" * 60)
        logging.info("✅ Deduplication complete!")
        logging.info("=" * 60)
    except Exception as e:
        logging.error(f"❌ Deduplication failed: {e}")
        exit(1)
