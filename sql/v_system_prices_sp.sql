-- System Prices by Settlement Period
-- SSP/SBP with spread for arbitrage analysis

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_system_prices_sp`
AS
SELECT
  settlementDate,
  settlementPeriod,
  systemSellPrice AS ssp_gbp_per_mwh,
  systemBuyPrice  AS sbp_gbp_per_mwh,
  (systemBuyPrice - systemSellPrice) AS spread_gbp_per_mwh
FROM
  `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`;
