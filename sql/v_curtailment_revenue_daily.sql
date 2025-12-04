-- Curtailment Revenue Aggregation (Daily)
-- Tracks revenue from ESO taking generation off the system

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_curtailment_revenue_daily`
AS
SELECT
  settlementDate,
  bmUnit,

  -- Curtailment = ESO taking generation off system = Bids (both gen-down or demand-up)
  SUM(CASE WHEN is_curtailment THEN energy_mwh     ELSE 0 END) AS curtailment_mwh,
  SUM(CASE WHEN is_curtailment THEN bm_revenue_gbp ELSE 0 END) AS curtailment_revenue_gbp,

  -- Non-curtailment (adding generation)
  SUM(CASE WHEN NOT is_curtailment THEN energy_mwh     ELSE 0 END) AS generation_add_mwh,
  SUM(CASE WHEN NOT is_curtailment THEN bm_revenue_gbp ELSE 0 END) AS generation_add_revenue_gbp,

  -- Total BM activity
  SUM(energy_mwh) AS total_bm_mwh,
  SUM(bm_revenue_gbp) AS total_bm_revenue_gbp

FROM
  `inner-cinema-476211-u9.uk_energy_prod.v_bm_system_direction_classified`
GROUP BY
  settlementDate, bmUnit;
