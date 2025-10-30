-- First, create a temporary table with only the latest versions we want to keep
CREATE OR REPLACE TABLE `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest` AS
WITH LatestVersions AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY settlementDate, settlementPeriod, fuelType
            ORDER BY _ingested_utc DESC
        ) as rn
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
)
SELECT * EXCEPT(rn)
FROM LatestVersions
WHERE rn = 1;

-- Verify the count of records we'll keep
SELECT COUNT(*) as records_to_keep
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest`;

-- Optional: Delete the original table and rename the new one
-- DROP TABLE `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`;
-- ALTER TABLE `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest`
-- RENAME TO `bmrs_fuelinst`;
