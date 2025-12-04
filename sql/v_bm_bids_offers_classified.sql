-- BM Bid-Offer Classification View (Elexon-aligned)
-- Classifies each acceptance into physical actions with MWh and revenue

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_bm_bids_offers_classified`
AS
WITH base AS (
  SELECT
    settlementDate,
    settlementPeriodFrom as settlementPeriod,
    bmUnit,
    CASE 
      WHEN (levelTo - levelFrom) < 0 THEN 'B'  -- Reducing output = BID
      WHEN (levelTo - levelFrom) > 0 THEN 'O'  -- Increasing output = OFFER
      ELSE NULL
    END as bidOfferFlag,
    acceptanceNumber,
    acceptanceTime,
    levelFrom,
    levelTo,
    (levelTo - levelFrom) AS delta_mw,    -- MW change
    0 AS price_gbp_per_mwh  -- Price not available in BOALF
  FROM
    `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
)
SELECT
  settlementDate,
  settlementPeriod,
  bmUnit,
  bidOfferFlag,
  acceptanceNumber,
  acceptanceTime,
  levelFrom,
  levelTo,
  delta_mw,
  price_gbp_per_mwh,
  -- Energy for half-hourly settlement period (MWh)
  ABS(delta_mw) * 0.5 AS energy_mwh,

  -- BM revenue placeholder (prices not in BOALF)
  0 AS bm_revenue_gbp,

  -- High-level physical action class
  CASE
    -- ESO wants generation OFF system:
    -- Bid from demand-side / BESS / VLP to increase demand / charge
    WHEN bidOfferFlag = 'B' AND delta_mw > 0
      THEN 'DEMAND_TURN_UP_OR_BESS_CHARGE'

    -- Bid from generator to reduce output
    WHEN bidOfferFlag = 'B' AND delta_mw < 0
      THEN 'GEN_TURN_DOWN'

    -- Offer from generator to increase output
    WHEN bidOfferFlag = 'O' AND delta_mw > 0
      THEN 'GEN_TURN_UP_OR_BESS_DISCHARGE'

    -- Offer from demand-side to reduce demand
    WHEN bidOfferFlag = 'O' AND delta_mw < 0
      THEN 'DEMAND_TURN_DOWN'

    ELSE 'OTHER'
  END AS action_class
FROM
  base;
