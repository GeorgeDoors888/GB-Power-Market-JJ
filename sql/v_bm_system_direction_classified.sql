-- BM System Direction Classification (Curtailment-aware)
-- Labels: ESO taking generation OFF vs adding generation TO the system

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_bm_system_direction_classified`
AS
WITH base AS (
  SELECT
    settlementDate,
    settlementPeriodFrom as settlementPeriod,
    acceptanceTime,
    bmUnit,
    CASE 
      WHEN (levelTo - levelFrom) < 0 THEN 'B'  -- Reducing output = BID
      WHEN (levelTo - levelFrom) > 0 THEN 'O'  -- Increasing output = OFFER
      ELSE NULL
    END as bidOfferFlag,
    0 AS price_gbp_per_mwh,  -- Price not in BOALF
    levelFrom,
    levelTo,
    (levelTo - levelFrom) AS delta_mw,
    ABS(levelTo - levelFrom) * 0.5 AS energy_mwh  -- Half-hourly settlement
  FROM
    `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
),

classified AS (
SELECT
  b.*,

  -- Elexon-standard system-direction label
  CASE
    ----------------------------------------------------------------------
    -- ESO TAKING GENERATION OFF THE SYSTEM (too much wind/solar)
    ----------------------------------------------------------------------
    WHEN bidOfferFlag = 'B' AND delta_mw > 0
      THEN 'ESO_TAKING_GENERATION_OFF_THE_SYSTEM'    -- Bid, demand up / charge BESS

    WHEN bidOfferFlag = 'B' AND delta_mw < 0
      THEN 'ESO_TAKING_GENERATION_OFF_THE_SYSTEM'    -- Gen turn-down

    ----------------------------------------------------------------------
    -- ESO ADDING GENERATION TO THE SYSTEM (shortage, tight margins)
    ----------------------------------------------------------------------
    WHEN bidOfferFlag = 'O' AND delta_mw > 0
      THEN 'ESO_ADDING_GENERATION_TO_THE_SYSTEM'     -- Offer, gen up / BESS discharge

    WHEN bidOfferFlag = 'O' AND delta_mw < 0
      THEN 'ESO_ADDING_GENERATION_TO_THE_SYSTEM'     -- Demand reduction

    ELSE 'UNKNOWN'
  END AS system_direction,

  ------------------------------------------------------------------------
  -- Explicit CURTAILMENT flag:
  -- ESO taking generation off = curtailment event
  ------------------------------------------------------------------------
  CASE
    WHEN bidOfferFlag = 'B' THEN TRUE
    ELSE FALSE
  END AS is_curtailment,

  ------------------------------------------------------------------------
  -- Revenue placeholder (prices not in BOALF - use VLP uplift or join BOD)
  ------------------------------------------------------------------------
  0 AS bm_revenue_gbp

FROM
  base b
)

SELECT * FROM classified;
