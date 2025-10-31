-- Deduplication Script for bmrs_fuelinst
-- Issue: Multiple duplicate records per settlement period (120 records = 20 fuel types × 6 duplicates)
-- Strategy: Keep the latest record per unique combination of settlementDate, settlementPeriod, fuelType

-- Project and Dataset
-- inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst

-- Step 1: Analyze duplicates first
SELECT 
    settlementDate,
    settlementPeriod,
    fuelType,
    COUNT(*) as record_count,
    COUNT(DISTINCT publishTime) as unique_publish_times,
    MAX(publishTime) as latest_publish_time
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
GROUP BY settlementDate, settlementPeriod, fuelType
HAVING COUNT(*) > 1
ORDER BY record_count DESC, settlementDate DESC
LIMIT 100;

-- Step 2: See total duplicate count
SELECT 
    COUNT(*) as duplicate_groups,
    SUM(record_count - 1) as records_to_delete
FROM (
    SELECT 
        settlementDate,
        settlementPeriod,
        fuelType,
        COUNT(*) as record_count
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    GROUP BY settlementDate, settlementPeriod, fuelType
    HAVING COUNT(*) > 1
);

-- Step 3: Preview records that will be KEPT (latest publishTime per group)
WITH ranked_records AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY settlementDate, settlementPeriod, fuelType 
            ORDER BY publishTime DESC
        ) as rn
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
)
SELECT 
    settlementDate,
    settlementPeriod,
    fuelType,
    generation,
    publishTime,
    rn
FROM ranked_records
WHERE settlementDate IN (
    SELECT DISTINCT settlementDate 
    FROM ranked_records 
    WHERE rn > 1 
    LIMIT 5
)
ORDER BY settlementDate DESC, settlementPeriod, fuelType, rn
LIMIT 100;

-- Step 4: DEDUPLICATION - Create new table with deduplicated data
-- CAUTION: This creates a new table. Review data first!

CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_dedup` AS
WITH ranked_records AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY settlementDate, settlementPeriod, fuelType 
            ORDER BY publishTime DESC, 
                     COALESCE(ingested_utc, TIMESTAMP '1970-01-01 00:00:00') DESC,
                     COALESCE(_ingested_utc, '1970-01-01 00:00:00') DESC
        ) as rn
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
)
SELECT * EXCEPT(rn)
FROM ranked_records
WHERE rn = 1;

-- Step 5: Verify deduplication worked
SELECT 
    'Original' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                         CAST(settlementPeriod AS STRING), '-', fuelType)) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`

UNION ALL

SELECT 
    'Deduplicated' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                         CAST(settlementPeriod AS STRING), '-', fuelType)) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_dedup`;

-- Step 6: Check for any remaining duplicates in new table
SELECT 
    settlementDate,
    settlementPeriod,
    fuelType,
    COUNT(*) as record_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_dedup`
GROUP BY settlementDate, settlementPeriod, fuelType
HAVING COUNT(*) > 1;

-- Step 7: Backup original table and swap
-- MANUAL STEPS:
-- 1. In BigQuery Console:
--    a. Rename bmrs_fuelinst → bmrs_fuelinst_backup_20251030
--    b. Rename bmrs_fuelinst_dedup → bmrs_fuelinst
-- 2. Test dashboard and queries work
-- 3. After 7 days of verification, delete bmrs_fuelinst_backup_20251030

-- OR use these commands (CAUTION - DESTRUCTIVE):
-- DROP TABLE IF EXISTS `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_backup_20251030`;
-- ALTER TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst` 
--   RENAME TO bmrs_fuelinst_backup_20251030;
-- ALTER TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_dedup` 
--   RENAME TO bmrs_fuelinst;

-- Step 8: Sample data comparison
SELECT 
    settlementDate,
    settlementPeriod,
    fuelType,
    generation,
    publishTime
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_dedup`
WHERE settlementDate = '2025-07-10'
  AND settlementPeriod = 25
ORDER BY fuelType;
