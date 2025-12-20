-- Create deduplicated view of REMIT data
-- Keeps only the LATEST revision (publishTime) per outage event (MRID)
-- Reduces 10,540 records → 1,266 unique outage events

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.remit_latest_revisions` AS
WITH ranked_revisions AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY mrid
      ORDER BY publishTime DESC, revisionNumber DESC
    ) as revision_rank
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_iris`
)
SELECT
  * EXCEPT(revision_rank)
FROM ranked_revisions
WHERE revision_rank = 1;

-- Usage example:
-- SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.remit_latest_revisions`;
-- Expected: ~1,266 records (one per unique MRID)

-- Query for dashboard/analysis (latest state of all outages):
-- SELECT
--   affectedUnit,
--   eventType,
--   unavailableCapacity,
--   eventStartTime,
--   eventEndTime,
--   eventStatus
-- FROM `inner-cinema-476211-u9.uk_energy_prod.remit_latest_revisions`
-- WHERE eventStatus = 'Active'
-- ORDER BY eventStartTime;
