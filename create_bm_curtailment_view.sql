-- ============================================================================
-- BigQuery View: v_bm_curtailment_classified
-- Purpose: Classify BOALF bid-offer acceptances per BSC definitions
-- Date: 2025-12-05
-- 
-- BSC Definitions (from Elexon guidance):
-- - BID: Reduce generation OR increase demand (ESO taking generation off)
-- - OFFER: Increase generation OR reduce demand (ESO adding generation)
--
-- VLP/VTP Routes:
-- - VLPs can register Secondary BM Units (sBMUs) and submit bids/offers
-- - VTPs participate via same BM definitions but focus on wholesale trading
-- - Both avoid expensive direct BSC accreditation by aggregating via VLP role
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_bm_curtailment_classified` AS

WITH boalf_base AS (
  SELECT
    settlementDate,
    settlementPeriodFrom,
    settlementPeriodTo,
    bmUnit,
    acceptanceNumber,
    acceptanceTime,
    deemedBoFlag,
    soFlag,
    storFlag,
    rrFlag,
    levelFrom,
    levelTo,
    timeFrom,
    timeTo,
    nationalGridBmUnit,
    
    -- Extract bid/offer indicator from deemedBoFlag (BOOLEAN: true=bid, false=offer?)
    -- Or use pattern matching on bmUnit/nationalGridBmUnit
    CASE 
      WHEN deemedBoFlag = TRUE THEN 'BID'
      WHEN deemedBoFlag = FALSE THEN 'OFFER'
      ELSE 'UNKNOWN'
    END AS bid_offer_type,
    
    -- Calculate accepted volume (levelTo - levelFrom)
    -- Negative = reducing, Positive = increasing
    COALESCE(levelTo, 0) - COALESCE(levelFrom, 0) AS accepted_volume_mw,
    
    -- Calculate duration in hours
    -- timeFrom/timeTo are strings like "2024-08-01T20:31:00Z"
    TIMESTAMP_DIFF(
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', timeTo),
      PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', timeFrom),
      MINUTE
    ) / 60.0 AS duration_hours,
    
    _ingested_utc
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE settlementDate >= '2024-01-01'  -- Include 2024 data
),

-- Join with bid-offer data (bmrs_bod) to get prices
boalf_with_prices AS (
  SELECT
    b.*,
    
    -- Get bid/offer price from bmrs_bod
    -- Match on bmUnit and settlement period
    CASE 
      WHEN b.bid_offer_type = 'BID' THEN bod.bid
      WHEN b.bid_offer_type = 'OFFER' THEN bod.offer
      ELSE NULL
    END AS acceptance_price_gbp_mwh,
    
    -- Classify BMU type from bmUnit patterns
    -- VLP units: typically end in -VLP or registered as secondary BMUs
    -- BESS: battery energy storage (look for BESS, STOR, FLEX patterns)
    -- GEN: generators (typical format: T_<SITE><GEN>)
    CASE
      WHEN REGEXP_CONTAINS(UPPER(b.bmUnit), r'VLP|VIRTUAL') THEN 'VLP'
      WHEN REGEXP_CONTAINS(UPPER(b.bmUnit), r'BESS|BATT|STOR|FLEX') THEN 'BESS'
      WHEN REGEXP_CONTAINS(UPPER(b.bmUnit), r'WIND|SOLAR|PV') THEN 'RENEWABLE_GEN'
      WHEN REGEXP_CONTAINS(UPPER(b.bmUnit), r'LOAD|DEMAND') THEN 'LOAD'
      WHEN REGEXP_CONTAINS(UPPER(b.bmUnit), r'INTELEC|INTER|IFA|ELEC') THEN 'INTERCONNECTOR'
      ELSE 'GENERATOR'
    END AS bmu_type
    
  FROM boalf_base b
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` bod
    ON b.bmUnit = bod.bmUnit
    AND b.settlementDate = bod.settlementDate
    AND b.settlementPeriodFrom = bod.settlementPeriod
    -- Note: Could also match on timeFrom but settlement period sufficient
)

SELECT
  settlementDate,
  settlementPeriodFrom,
  settlementPeriodTo,
  bmUnit,
  bmu_type,
  bid_offer_type,
  accepted_volume_mw,
  duration_hours,
  
  -- Calculate accepted energy (MWh)
  accepted_volume_mw * duration_hours AS accepted_energy_mwh,
  
  acceptance_price_gbp_mwh,
  
  -- Classify ESO action per BSC definitions
  CASE
    -- CURTAILMENT: ESO taking generation off the system
    WHEN bid_offer_type = 'BID' AND bmu_type IN ('GENERATOR', 'RENEWABLE_GEN') 
      THEN 'CURTAIL_GEN'
    
    -- TURN UP DEMAND: ESO soaking up excess (BESS charging, load increasing)
    WHEN bid_offer_type = 'BID' AND bmu_type IN ('LOAD', 'VLP', 'BESS') 
      THEN 'TURN_UP_DEMAND'
    
    -- TURN UP GEN: ESO adding generation to system
    WHEN bid_offer_type = 'OFFER' AND bmu_type IN ('GENERATOR', 'RENEWABLE_GEN') 
      THEN 'TURN_UP_GEN'
    
    -- TURN DOWN DEMAND: ESO reducing demand (BESS discharging, load shedding)
    WHEN bid_offer_type = 'OFFER' AND bmu_type IN ('LOAD', 'VLP', 'BESS') 
      THEN 'TURN_DOWN_DEMAND'
    
    -- Interconnectors are special case
    WHEN bid_offer_type = 'BID' AND bmu_type = 'INTERCONNECTOR' 
      THEN 'REDUCE_IMPORT'
    WHEN bid_offer_type = 'OFFER' AND bmu_type = 'INTERCONNECTOR' 
      THEN 'INCREASE_IMPORT'
    
    ELSE 'UNKNOWN'
  END AS eso_action_type,
  
  -- Calculate revenue (positive = payment to BMU, negative = payment by BMU)
  -- For BM actions, ESO pays the acceptance price
  (accepted_volume_mw * duration_hours) * COALESCE(acceptance_price_gbp_mwh, 0) AS bm_revenue_gbp,
  
  -- Flags for special actions
  soFlag AS is_system_operator_flag,
  storFlag AS is_short_term_operating_reserve,
  rrFlag AS is_replacement_reserve,
  deemedBoFlag,
  
  acceptanceNumber,
  nationalGridBmUnit,
  acceptanceTime,
  timeFrom,
  timeTo,
  levelFrom,
  levelTo,
  _ingested_utc

FROM boalf_with_prices

WHERE 
  -- Exclude zero-volume acceptances
  ABS(accepted_volume_mw) > 0.01
  
  -- Exclude unknown types for clean analysis
  AND bid_offer_type != 'UNKNOWN'

ORDER BY 
  settlementDate DESC, 
  settlementPeriodFrom DESC,
  acceptanceTime DESC;

-- ============================================================================
-- Usage Examples:
-- ============================================================================

-- 1. VLP/BESS curtailment revenue (demand turn-up)
-- SELECT
--   DATE(settlementDate) as date,
--   bmu_type,
--   COUNT(*) as acceptance_count,
--   SUM(accepted_energy_mwh) as total_mwh,
--   SUM(bm_revenue_gbp) as curtailment_revenue_gbp
-- FROM `inner-cinema-476211-u9.uk_energy_prod.v_bm_curtailment_classified`
-- WHERE eso_action_type = 'TURN_UP_DEMAND'
-- GROUP BY date, bmu_type
-- ORDER BY date DESC;

-- 2. Generator curtailment vs BESS arbitrage
-- SELECT
--   DATE(settlementDate) as date,
--   SUM(CASE WHEN eso_action_type = 'CURTAIL_GEN' THEN bm_revenue_gbp ELSE 0 END) as gen_curtailment,
--   SUM(CASE WHEN eso_action_type = 'TURN_UP_DEMAND' THEN bm_revenue_gbp ELSE 0 END) as bess_charge_payment,
--   SUM(CASE WHEN eso_action_type = 'TURN_DOWN_DEMAND' THEN bm_revenue_gbp ELSE 0 END) as bess_discharge_payment
-- FROM `inner-cinema-476211-u9.uk_energy_prod.v_bm_curtailment_classified`
-- GROUP BY date
-- ORDER BY date DESC;

-- 3. Top VLP units by revenue
-- SELECT
--   bmUnitId,
--   bmu_type,
--   COUNT(*) as total_acceptances,
--   SUM(accepted_energy_mwh) as total_energy_mwh,
--   SUM(bm_revenue_gbp) as total_revenue_gbp,
--   AVG(acceptance_price_gbp_mwh) as avg_price_gbp_mwh
-- FROM `inner-cinema-476211-u9.uk_energy_prod.v_bm_curtailment_classified`
-- WHERE bmu_type IN ('VLP', 'BESS')
--   AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
-- GROUP BY bmUnitId, bmu_type
-- ORDER BY total_revenue_gbp DESC
-- LIMIT 20;
