SELECT
  COUNT(*) as total_records
FROM
  `jibber-jabber-knowledge.uk_energy.elexon_bid_offer_acceptances`
WHERE
  bmu_id = '2__ESTAT001'
  AND settlement_date >= '2016-01-01' AND settlement_date <= '2025-08-20';
