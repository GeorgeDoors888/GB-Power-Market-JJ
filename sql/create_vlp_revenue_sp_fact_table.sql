-- ============================================================================
-- VLP REVENUE FACT TABLE - PHASE 1 TASK 1
-- ============================================================================
-- Purpose: Central revenue fact table joining BOALF (acceptances) + BOD (prices)
-- Target: inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp
-- Updates: Should be run daily or on-demand to populate revenue data
-- ============================================================================

CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp` AS

WITH 
-- Step 1: Get BOALF acceptances (last 30 days for initial build)
boalf_raw AS (
  SELECT 
    settlementDate,
    settlementPeriodFrom AS settlementPeriod,  -- FIX: Use settlementPeriodFrom
    bmUnit,
    acceptanceNumber,
    levelFrom,
    levelTo,
    -- Calculate volume in MWh (settlement period = 30 min = 0.5 hours)
    (levelTo - levelFrom) * 0.5 AS volume_mwh,
    -- Determine action type
    CASE 
      WHEN levelTo > levelFrom THEN 'offer_up'
      WHEN levelTo < levelFrom THEN 'bid_down'
      ELSE 'no_change'
    END AS action_type,
    soFlag,
    storFlag,
    rrFlag,
    FALSE AS rdFlag  -- FIX: bmrs_boalf doesn't have rdFlag
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE settlementDate >= '2025-10-01'  -- FIX: Historical table ends 2025-10-28, use fixed date
    AND settlementDate <= '2025-10-30'  -- Last available date in historical table
    AND (levelTo - levelFrom) != 0  -- Only non-zero volume changes
),

-- Step 2: Get BOD prices (filter sentinel values 9999)
bod_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    bmUnit,
    pairId,
    -- Filter out sentinel values (9999 = no price)
    CASE WHEN bid > 0 AND bid < 9999 THEN bid ELSE NULL END AS bidPrice,
    CASE WHEN offer > 0 AND offer < 9999 THEN offer ELSE NULL END AS offerPrice
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate >= '2025-10-01'  -- FIX: Match BOALF date range
    AND settlementDate <= '2025-10-30'
),

-- Step 3: Get BMU registration data (for DNO lookup)
bmu_lookup AS (
  SELECT DISTINCT
    elexonbmunit AS bmUnit,  -- FIX: Lowercase column names
    nationalgridbmunit AS ngcBmUnit,
    leadpartyname AS leadPartyName,
    gspgroupid AS gspGroupId,
    -- Extract DNO from GSP group or other identifier
    -- Note: May need to join with neso_dno_reference for proper DNO mapping
    COALESCE(gspgroupid, 'UNKNOWN') AS dno_id
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data`
),

-- Step 4: Get wholesale prices (for arbitrage calculation)
wholesale_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    AVG(price) AS wholesale_price_gbp_per_mwh  -- FIX: Column is 'price' not 'marketIndexPrice'
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= '2025-10-01'  -- FIX: Match BOALF date range
    AND settlementDate <= '2025-10-30'
    AND price IS NOT NULL
  GROUP BY settlementDate, settlementPeriod
),

-- Step 5: Join BOALF + BOD to calculate BM revenue
revenue_base AS (
  SELECT
    boalf.settlementDate AS settlement_date,
    boalf.settlementPeriod AS settlement_period,
    boalf.bmUnit AS bm_unit_id,
    boalf.acceptanceNumber,
    boalf.action_type,
    boalf.volume_mwh AS delivered_volume_mwh,
    
    -- Select appropriate price based on action type
    CASE 
      WHEN boalf.action_type = 'offer_up' THEN bod.offerPrice
      WHEN boalf.action_type = 'bid_down' THEN bod.bidPrice
      ELSE NULL
    END AS bm_price_gbp_per_mwh,
    
    -- Calculate BM value (revenue from balancing mechanism)
    boalf.volume_mwh * CASE 
      WHEN boalf.action_type = 'offer_up' THEN bod.offerPrice
      WHEN boalf.action_type = 'bid_down' THEN bod.bidPrice
      ELSE 0
    END AS bm_value_gbp,
    
    -- Add wholesale price for comparison
    wp.wholesale_price_gbp_per_mwh,
    
    -- Calculate wholesale cost (what energy would have cost)
    ABS(boalf.volume_mwh) * COALESCE(wp.wholesale_price_gbp_per_mwh, 0) AS wholesale_cost_gbp,
    
    -- Add DNO information
    bmu.dno_id,
    bmu.gspGroupId AS region,
    bmu.leadPartyName,
    
    -- Add flags
    boalf.soFlag,
    boalf.storFlag,
    boalf.rrFlag,
    boalf.rdFlag
    
  FROM boalf_raw AS boalf
  
  -- Join BOD to get prices (use DISTINCT to avoid duplicates from multiple pairs)
  LEFT JOIN (
    SELECT settlementDate, settlementPeriod, bmUnit,
           AVG(bidPrice) AS bidPrice,
           AVG(offerPrice) AS offerPrice
    FROM bod_prices
    WHERE bidPrice IS NOT NULL OR offerPrice IS NOT NULL
    GROUP BY settlementDate, settlementPeriod, bmUnit
  ) AS bod
    ON boalf.bmUnit = bod.bmUnit 
    AND boalf.settlementDate = bod.settlementDate
    AND boalf.settlementPeriod = bod.settlementPeriod
  
  -- Join BMU lookup for DNO
  LEFT JOIN bmu_lookup AS bmu
    ON boalf.bmUnit = bmu.bmUnit
  
  -- Join wholesale prices
  LEFT JOIN wholesale_prices AS wp
    ON boalf.settlementDate = wp.settlementDate
    AND boalf.settlementPeriod = wp.settlementPeriod
  
  WHERE 
    -- Only include records where we have a valid price
    (CASE 
      WHEN boalf.action_type = 'offer_up' THEN bod.offerPrice
      WHEN boalf.action_type = 'bid_down' THEN bod.bidPrice
      ELSE NULL
    END) IS NOT NULL
),

-- Step 6: Add costs and calculate total revenue
final_revenue AS (
  SELECT
    settlement_date,
    settlement_period,
    bm_unit_id,
    dno_id AS dno,
    region,
    delivered_volume_mwh,
    bm_price_gbp_per_mwh,
    bm_value_gbp,
    wholesale_price_gbp_per_mwh,
    wholesale_cost_gbp,
    
    -- DUoS costs (placeholder - would need to join duos_unit_rates)
    -- For now, estimate based on volume and average DUoS rate
    ABS(delivered_volume_mwh) * 0.10 AS duos_gbp,  -- ~£10/MWh average
    
    -- Levies (TNUoS + BSUoS + CCL + RO + FIT)
    -- TNUoS = £0/MWh (Dec 2025), BSUoS = £3/MWh, CCL = £0.775/MWh, RO = £6.83/MWh, FIT = £0.54/MWh
    -- Total levies = £11.145/MWh
    ABS(delivered_volume_mwh) * 11.145 AS levies_gbp,
    
    -- Other services (DC, CM, etc.) - placeholder, needs separate allocation
    0.0 AS other_service_gbp,
    
    -- Calculate total revenue
    -- BM value - wholesale cost - DUoS - levies + other services
    bm_value_gbp 
      - wholesale_cost_gbp 
      - (ABS(delivered_volume_mwh) * 0.10)  -- DUoS
      - (ABS(delivered_volume_mwh) * 11.145)  -- Levies
      + 0.0  -- Other services
    AS total_revenue_gbp,
    
    -- Add metadata
    acceptanceNumber,
    action_type,
    soFlag AS so_flag,
    storFlag AS stor_flag,
    rrFlag AS rr_flag,
    rdFlag AS rd_flag,
    leadPartyName
    
  FROM revenue_base
)

-- Final SELECT with calculated net margin
SELECT
  settlement_date,
  settlement_period,
  bm_unit_id,
  dno,
  region,
  delivered_volume_mwh,
  bm_price_gbp_per_mwh,
  bm_value_gbp,
  wholesale_price_gbp_per_mwh,
  wholesale_cost_gbp,
  duos_gbp,
  levies_gbp,
  other_service_gbp,
  total_revenue_gbp,
  
  -- Calculate net margin per MWh
  CASE 
    WHEN delivered_volume_mwh != 0 THEN total_revenue_gbp / ABS(delivered_volume_mwh)
    ELSE 0
  END AS net_margin_gbp_per_mwh,
  
  -- Metadata
  acceptanceNumber AS acceptance_number,
  action_type,
  so_flag,
  stor_flag,
  rr_flag,
  rd_flag,
  leadPartyName AS lead_party_name,
  
  -- Add timestamp
  CURRENT_TIMESTAMP() AS created_at

FROM final_revenue

-- Only include rows with valid revenue calculations
WHERE bm_value_gbp IS NOT NULL
  AND delivered_volume_mwh != 0

ORDER BY settlement_date DESC, settlement_period DESC, bm_unit_id;

-- ============================================================================
-- POST-CREATE NOTES
-- ============================================================================
-- 1. Run this query to create the table initially
-- 2. Set up a daily scheduled query to refresh with new data
-- 3. Consider partitioning by settlement_date for better performance
-- 4. Add indexes on: bm_unit_id, dno, settlement_date
-- 5. Next step: Create bod_boalf_7d_summary view on top of this table
-- ============================================================================
