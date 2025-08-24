SELECT
  COUNT(*) as total_records
FROM
  `jibber-jabber-knowledge.uk_energy.elexon_bid_offer_acceptances`
WHERE
  bmu_id = '2__ESTAT001';
