-- Check for duplicates in historic BigQuery tables
-- Example for bmrs_boalf (Bid-Offer Acceptances)
-- Adjust for other tables as needed

SELECT
  settlement_date,
  settlement_period,
  bmu_id,
  bid_offer_level,
  COUNT(*) AS num_records
FROM
  `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
GROUP BY
  settlement_date, settlement_period, bmu_id, bid_offer_level
HAVING
  COUNT(*) > 1
ORDER BY
  num_records DESC, settlement_date DESC
LIMIT 100;

-- Repeat for other tables by changing table name and key fields as appropriate.
