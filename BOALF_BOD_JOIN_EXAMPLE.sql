-- BOALF + BOD Join Example: Extract Acceptance Prices (Level 1 Cashflow)
-- Purpose: Show one BOALF acceptance row + matching BOD price ladder
-- Use Case: Calculate indicative/operational cashflow (NOT guaranteed = settlement)
-- Warning: Level 1 (operational) ≠ Level 2 (P114 SAA-settled)

-- ==============================================================================
-- PART 1: Basic Join (One Acceptance → Its Bid Price)
-- ==============================================================================

WITH acceptance_sample AS (
  -- Pick one BOALF acceptance for demonstration
  SELECT 
    settlementDate,
    settlementPeriod,
    bmUnitId,
    acceptanceNumber,
    acceptanceTime,
    acceptanceType,  -- 'BID' or 'OFFER'
    timeFrom,
    timeTo,
    levelFrom,      -- MW before
    levelTo,        -- MW after
    soFlag          -- TRUE = SO-flagged (special/constructed)
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE settlementDate = '2024-10-17'
    AND bmUnitId LIKE 'T_%'  -- Gas CCGTs typically start with T_
    AND acceptanceType = 'BID'
    AND levelTo < levelFrom   -- Turn-down (reduction)
  LIMIT 1
),

bod_prices AS (
  -- Get BOD price ladder for same unit/date/period
  SELECT 
    settlementDate,
    settlementPeriod,
    bmUnitId,
    pairId,         -- Bid-offer pair ID (may have multiple pairs = ladder)
    bid AS bidPrice,    -- £/MWh for BID acceptances
    offer AS offerPrice -- £/MWh for OFFER acceptances (not used here)
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate = '2024-10-17'
    AND bmUnitId IN (SELECT bmUnitId FROM acceptance_sample)
    AND settlementPeriod IN (SELECT settlementPeriod FROM acceptance_sample)
    AND bid IS NOT NULL  -- Must have bid price for BID acceptances
)

-- Join acceptance to price
SELECT 
  a.settlementDate,
  a.settlementPeriod,
  a.bmUnitId,
  a.acceptanceNumber,
  a.acceptanceType,
  a.levelFrom AS mw_before,
  a.levelTo AS mw_after,
  (a.levelTo - a.levelFrom) AS delta_mw,  -- Negative = reduction
  a.timeFrom,
  a.timeTo,
  TIMESTAMP_DIFF(a.timeTo, a.timeFrom, MINUTE) / 60.0 AS duration_hours,
  
  -- Price from BOD
  b.pairId,
  b.bidPrice AS price_per_mwh,
  
  -- Indicative cashflow (Level 1)
  ABS(a.levelTo - a.levelFrom) * 
    (TIMESTAMP_DIFF(a.timeTo, a.timeFrom, MINUTE) / 60.0) * 
    ABS(b.bidPrice) AS indicative_cost_gbp,
  
  -- Metadata
  a.soFlag AS is_so_flagged
  
FROM acceptance_sample a
LEFT JOIN bod_prices b
  ON a.bmUnitId = b.bmUnitId
  AND a.settlementDate = b.settlementDate
  AND a.settlementPeriod = b.settlementPeriod
;

-- ==============================================================================
-- PART 2: Handle Multiple BOD Pairs (Ladder Stacking)
-- ==============================================================================

-- Some units submit multiple bid-offer pairs forming a price ladder:
-- Pair 1: -50 MW @ £40/MWh
-- Pair 2: -100 MW @ £60/MWh  
-- Pair 3: -150 MW @ £80/MWh

-- If acceptance = -120 MW, should map to Pair 2 (middle tier)
-- This requires ladder matching logic (volume bands)

-- Simplified approach: Take first available BOD price (may be inaccurate)
-- Proper approach: Match acceptance volume to correct ladder tier

WITH acceptance_with_ladder AS (
  SELECT 
    a.settlementDate,
    a.settlementPeriod,
    a.bmUnitId,
    a.acceptanceNumber,
    a.acceptanceType,
    (a.levelTo - a.levelFrom) AS delta_mw,
    TIMESTAMP_DIFF(a.timeTo, a.timeFrom, MINUTE) / 60.0 AS duration_hours,
    
    -- Get ALL BOD pairs for this unit/date/period
    ARRAY_AGG(
      STRUCT(b.pairId, b.bidPrice, b.offerPrice) 
      ORDER BY b.pairId
    ) AS bod_ladder
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` a
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
    ON a.bmUnitId = b.bmUnitId
    AND a.settlementDate = b.settlementDate
    AND a.settlementPeriod = b.settlementPeriod
  WHERE a.settlementDate = '2024-10-17'
    AND a.acceptanceType = 'BID'
  GROUP BY 1,2,3,4,5,6,7
)

SELECT 
  settlementDate,
  settlementPeriod,
  bmUnitId,
  acceptanceNumber,
  delta_mw,
  duration_hours,
  ARRAY_LENGTH(bod_ladder) AS num_bod_pairs,
  
  -- Simple approach: Use first BOD price (may be wrong if ladder exists)
  bod_ladder[OFFSET(0)].bidPrice AS simple_price,
  
  -- Better approach would iterate ladder to find correct tier
  -- (requires volume band matching - not shown here)
  
FROM acceptance_with_ladder
LIMIT 10;

-- ==============================================================================
-- PART 3: Join BOALF to P114 (Compare Level 1 vs Level 2)
-- ==============================================================================

-- Level 1: BOALF + BOD (operational estimate)
-- Level 2: P114 (SAA-settled outcome)

WITH boalf_indicative AS (
  SELECT 
    a.settlementDate,
    a.settlementPeriod,
    a.bmUnitId,
    a.acceptanceNumber,
    (a.levelTo - a.levelFrom) AS delta_mw,
    TIMESTAMP_DIFF(a.timeTo, a.timeFrom, MINUTE) / 60.0 AS duration_hours,
    b.bidPrice,
    
    -- Level 1 indicative cashflow
    ABS(a.levelTo - a.levelFrom) * 
      (TIMESTAMP_DIFF(a.timeTo, a.timeFrom, MINUTE) / 60.0) * 
      ABS(b.bidPrice) AS level1_cashflow_gbp
      
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` a
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
    ON a.bmUnitId = b.bmUnitId
    AND a.settlementDate = b.settlementDate
    AND a.settlementPeriod = b.settlementPeriod
  WHERE a.settlementDate = '2024-10-17'
    AND a.acceptanceType = 'BID'
    AND a.levelTo < a.levelFrom  -- Turn-down
),

p114_settled AS (
  SELECT 
    bm_unit_id AS bmUnitId,
    CAST(settlement_date AS DATE) AS settlementDate,
    settlement_period AS settlementPeriod,
    value2 AS settled_mwh,
    system_price AS price_per_mwh,
    multiplier,
    
    -- Level 2 SAA-settled cashflow (Section T Trading Charges)
    value2 * system_price * multiplier AS level2_cashflow_gbp
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
  WHERE settlement_date = '2024-10-17'
    AND settlement_run = 'RF'
    AND value2 < 0  -- Negative energy = payment to generator
)

-- Compare Level 1 vs Level 2
SELECT 
  l1.bmUnitId,
  l1.settlementDate,
  l1.settlementPeriod,
  l1.acceptanceNumber,
  l1.delta_mw AS level1_delta_mw,
  l1.bidPrice AS level1_bid_price,
  l1.level1_cashflow_gbp,
  
  l2.settled_mwh AS level2_settled_mwh,
  l2.price_per_mwh AS level2_system_price,
  l2.level2_cashflow_gbp,
  
  -- Difference (expect non-zero due to settlement adjustments)
  (l1.level1_cashflow_gbp - ABS(l2.level2_cashflow_gbp)) AS cashflow_difference_gbp,
  
  CASE 
    WHEN ABS(l1.level1_cashflow_gbp - ABS(l2.level2_cashflow_gbp)) < 100 
    THEN 'CLOSE MATCH'
    WHEN ABS(l1.level1_cashflow_gbp - ABS(l2.level2_cashflow_gbp)) < 1000
    THEN 'MODERATE DIFFERENCE'
    ELSE 'LARGE DIFFERENCE'
  END AS match_quality
  
FROM boalf_indicative l1
LEFT JOIN p114_settled l2
  ON l1.bmUnitId = l2.bmUnitId
  AND l1.settlementDate = l2.settlementDate
  AND l1.settlementPeriod = l2.settlementPeriod
ORDER BY ABS(cashflow_difference_gbp) DESC
LIMIT 20;

-- ==============================================================================
-- KEY INSIGHTS
-- ==============================================================================

-- 1. BOALF fields (BigQuery):
--    - bmUnitId, settlementDate, settlementPeriod
--    - acceptanceNumber, acceptanceTime, acceptanceType
--    - levelFrom, levelTo (MW before/after)
--    - timeFrom, timeTo (duration)
--    - soFlag (TRUE = SO-flagged/constructed)

-- 2. BOD fields (BigQuery):
--    - bmUnitId, settlementDate, settlementPeriod
--    - pairId (ladder identifier)
--    - bid, offer (prices in £/MWh)

-- 3. P114 fields (BigQuery):
--    - bm_unit_id, settlement_date, settlement_period
--    - value2 (settled MWh)
--    - system_price (imbalance price, NOT acceptance price)
--    - multiplier (typically 0.5)
--    - settlement_run (II/R3/RF)

-- 4. Join keys:
--    BOALF.bmUnitId = BOD.bmUnitId
--    BOALF.settlementDate = BOD.settlementDate
--    BOALF.settlementPeriod = BOD.settlementPeriod
--    (Optional: BOALF.bidOfferPairId = BOD.pairId if available)

-- 5. Differences between Level 1 and Level 2:
--    - Level 1 uses BOD acceptance price (operational)
--    - Level 2 uses P114 system price (settlement)
--    - Level 1 NOT guaranteed to match Level 2 due to:
--      * Delivery/non-delivery adjustments (Section T)
--      * NGSEA post-event construction/committee changes (P448, BSCP18)
--      * Settlement run corrections (II → R3 → RF)

-- 6. NGSEA special case:
--    - soFlag = TRUE indicates constructed/special acceptance
--    - May not have real-time BOALF trail
--    - P114 shows post-committee constructed data
--    - "A Network Gas Supply Emergency Acceptance will always be a Bid" (BSCP18)

-- 7. For NGSEA detection:
--    - Filter: acceptanceType = 'BID' AND levelTo < levelFrom (turn-down)
--    - Check: soFlag = TRUE (constructed acceptance)
--    - Correlate: High system_price (£80+ suggests gas stress)
--    - Validate: Multiple gas units curtailed same period

-- ==============================================================================
-- REFERENCES
-- ==============================================================================

-- BSC Section Q: Bid-Offer Acceptance definitions
-- BSC Section T: Trading Charges (SAA settlement calculations)
-- BSCP18: Corrections to Bid-Offer Acceptance Related Data (NGSEA specific)
-- P448 Ofgem Decision: NGSEA settlement construct
-- Elexon NGSEA Guidance: Two-stage process (construction + committee review)
