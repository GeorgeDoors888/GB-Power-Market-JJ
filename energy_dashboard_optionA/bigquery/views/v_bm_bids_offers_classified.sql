CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_bm_bids_offers_classified`
AS
WITH base AS (
  SELECT
    settlementDate,
    settlementPeriod,
    bmUnit,
    bidOfferFlag,
    acceptanceNumber,
    acceptanceTime,
    levelFrom,
    levelTo,
    (levelTo - levelFrom) AS delta_mw,
    (levelTo - levelFrom) * 0.5 AS energy_mwh,
    acceptancePrice AS price_gbp_per_mwh
  FROM
    `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
)
SELECT
  *,
  energy_mwh * price_gbp_per_mwh AS bm_revenue_gbp
FROM base;
