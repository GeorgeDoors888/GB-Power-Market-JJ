-- Deduplication Script for bmrs_mid (Market Index Data)
-- Issue: Multiple duplicate records per settlement period (8 records per period)
-- Strategy: Keep the latest record per unique combination of settlementDate, settlementPeriod

-- Project and Dataset
-- inner-cinema-476211-u9.uk_energy_prod.bmrs_mid

-- Step 1: Analyze duplicates first
SELECT 
    settlementDate,
    settlementPeriod,
    COUNT(*) as record_count,
    COUNT(DISTINCT marketIndexPrice) as unique_prices,
    COUNT(DISTINCT marketIndexVolume) as unique_volumes,
    MIN(marketIndexPrice) as min_price,
    MAX(marketIndexPrice) as max_price,
    MIN(ingested_utc) as earliest_ingest,
    MAX(ingested_utc) as latest_ingest
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
GROUP BY settlementDate, settlementPeriod
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
        COUNT(*) as record_count
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
    GROUP BY settlementDate, settlementPeriod
    HAVING COUNT(*) > 1
);

-- Step 3: Check if duplicate records have same or different data
WITH duplicates AS (
    SELECT 
        settlementDate,
        settlementPeriod,
        marketIndexPrice,
        marketIndexVolume,
        ingested_utc,
        ROW_NUMBER() OVER (
            PARTITION BY settlementDate, settlementPeriod 
            ORDER BY ingested_utc DESC
        ) as rn
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
    WHERE CONCAT(CAST(settlementDate AS STRING), '-', CAST(settlementPeriod AS STRING)) IN (
        SELECT CONCAT(CAST(settlementDate AS STRING), '-', CAST(settlementPeriod AS STRING))
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
        GROUP BY settlementDate, settlementPeriod
        HAVING COUNT(*) > 1
        LIMIT 10
    )
)
SELECT * FROM duplicates
ORDER BY settlementDate DESC, settlementPeriod, rn
LIMIT 80;

-- Step 4: DEDUPLICATION - Create new table with deduplicated data
-- CAUTION: This creates a new table. Review data first!

CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_dedup` AS
WITH ranked_records AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY settlementDate, settlementPeriod
            ORDER BY 
                COALESCE(ingested_utc, TIMESTAMP '1970-01-01 00:00:00') DESC,
                COALESCE(_ingested_utc, '1970-01-01 00:00:00') DESC,
                -- If prices differ, prefer non-null and higher confidence
                CASE WHEN marketIndexPrice IS NOT NULL THEN 1 ELSE 0 END DESC,
                marketIndexVolume DESC
        ) as rn
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
)
SELECT * EXCEPT(rn)
FROM ranked_records
WHERE rn = 1;

-- Step 5: Verify deduplication worked
SELECT 
    'Original' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                         CAST(settlementPeriod AS STRING))) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`

UNION ALL

SELECT 
    'Deduplicated' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', 
                         CAST(settlementPeriod AS STRING))) as unique_keys
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_dedup`;

-- Step 6: Check for any remaining duplicates in new table
SELECT 
    settlementDate,
    settlementPeriod,
    COUNT(*) as record_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_dedup`
GROUP BY settlementDate, settlementPeriod
HAVING COUNT(*) > 1;

-- Step 7: Compare sample data before/after
SELECT 
    'BEFORE' as source,
    settlementDate,
    settlementPeriod,
    marketIndexPrice,
    marketIndexVolume,
    ingested_utc
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate = '2024-04-08' AND settlementPeriod = 3
ORDER BY ingested_utc DESC

UNION ALL

SELECT 
    'AFTER' as source,
    settlementDate,
    settlementPeriod,
    marketIndexPrice,
    marketIndexVolume,
    ingested_utc
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_dedup`
WHERE settlementDate = '2024-04-08' AND settlementPeriod = 3;

-- Step 8: Backup original table and swap
-- MANUAL STEPS:
-- 1. In BigQuery Console:
--    a. Rename bmrs_mid → bmrs_mid_backup_20251030
--    b. Rename bmrs_mid_dedup → bmrs_mid
-- 2. Test dashboard and queries work
-- 3. After 7 days of verification, delete bmrs_mid_backup_20251030

-- OR use these commands (CAUTION - DESTRUCTIVE):
-- DROP TABLE IF EXISTS `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_backup_20251030`;
-- ALTER TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` 
--   RENAME TO bmrs_mid_backup_20251030;
-- ALTER TABLE `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_dedup` 
--   RENAME TO bmrs_mid;

-- Step 9: Stats comparison
SELECT 
    'Original' as table_name,
    COUNT(*) as total_records,
    MIN(settlementDate) as earliest_date,
    MAX(settlementDate) as latest_date,
    COUNT(DISTINCT settlementDate) as unique_dates
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`

UNION ALL

SELECT 
    'Deduplicated' as table_name,
    COUNT(*) as total_records,
    MIN(settlementDate) as earliest_date,
    MAX(settlementDate) as latest_date,
    COUNT(DISTINCT settlementDate) as unique_dates
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_dedup`;
