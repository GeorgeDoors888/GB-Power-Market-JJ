-- ============================================================================
-- VLP REVENUE MONTHLY SPARKLINES - LAST 12 MONTHS
-- ============================================================================
-- Purpose: Monthly aggregates (max, min, avg) for sparkline graphs in Dashboard
-- Combines: Historical (bmrs_boalf) + IRIS (bmrs_boalf_iris) for complete coverage
-- Output: 12 months × 3 metrics (max, min, avg) for each KPI
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_monthly_sparklines` AS

WITH 
-- Combine historical + IRIS BOALF data for complete 12-month coverage
combined_boalf AS (
  -- Historical data (up to 2025-10-28)
  SELECT 
    settlementDate,
    settlementPeriodFrom as settlementPeriod,
    bmUnit,
    acceptanceNumber,
    levelFrom,
    levelTo,
    soFlag,
    storFlag,
    rrFlag,
    FALSE AS rdFlag
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
    AND settlementDate < '2025-11-01'  -- Historical ends Oct 28
    AND (levelTo - levelFrom) != 0
  
  UNION ALL
  
  -- IRIS real-time data (from 2025-11-04 onwards)
  SELECT 
    settlementDate,
    settlementPeriodFrom as settlementPeriod,
    bmUnit,
    acceptanceNumber,
    levelFrom,
    levelTo,
    soFlag,
    storFlag,
    rrFlag,
    FALSE AS rdFlag
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
  WHERE settlementDate >= '2025-11-01'  -- IRIS covers Nov onwards
    AND settlementDate <= CURRENT_DATE()
    AND (levelTo - levelFrom) != 0
),

-- Get BOD prices (combined historical + IRIS if available)
combined_bod AS (
  SELECT
    settlementDate,
    settlementPeriod,
    bmUnit,
    CASE WHEN bid > 0 AND bid < 9999 THEN bid ELSE NULL END AS bidPrice,
    CASE WHEN offer > 0 AND offer < 9999 THEN offer ELSE NULL END AS offerPrice
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
    AND settlementDate <= CURRENT_DATE()
),

-- BMU lookup for DNO
bmu_lookup AS (
  SELECT DISTINCT
    elexonbmunit AS bmUnit,
    nationalgridbmunit AS ngcBmUnit,
    leadpartyname AS leadPartyName,
    gspgroupid AS gspGroupId,
    COALESCE(gspgroupid, 'UNKNOWN') AS dno_id
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data`
),

-- Wholesale prices
wholesale_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    AVG(price) AS wholesale_price_gbp_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
    AND settlementDate <= CURRENT_DATE()
    AND price IS NOT NULL
  GROUP BY settlementDate, settlementPeriod
),

-- Calculate daily revenue (join BOALF + BOD + wholesale)
daily_revenue AS (
  SELECT
    DATE_TRUNC(CAST(a.settlementDate AS DATE), MONTH) as month_start,
    CAST(a.settlementDate AS DATE) as settlement_date,
    a.bmUnit as bm_unit_id,
    b.gspGroupId as dno,
    
    -- Volume calculation
    (a.levelTo - a.levelFrom) * 0.5 AS delivered_volume_mwh,
    
    -- Action type
    CASE 
      WHEN a.levelTo > a.levelFrom THEN 'offer_up'
      WHEN a.levelTo < a.levelFrom THEN 'bid_down'
      ELSE 'no_change'
    END AS action_type,
    
    -- Select correct price based on action
    CASE 
      WHEN a.levelTo > a.levelFrom THEN p.offerPrice
      WHEN a.levelTo < a.levelFrom THEN p.bidPrice
    END AS bm_price_gbp_per_mwh,
    
    -- BM value
    ((a.levelTo - a.levelFrom) * 0.5) * 
    CASE 
      WHEN a.levelTo > a.levelFrom THEN p.offerPrice
      WHEN a.levelTo < a.levelFrom THEN p.bidPrice
    END AS bm_value_gbp,
    
    -- Wholesale cost
    ((a.levelTo - a.levelFrom) * 0.5) * COALESCE(w.wholesale_price_gbp_per_mwh, 0) AS wholesale_cost_gbp,
    
    -- DUoS and levies
    ABS((a.levelTo - a.levelFrom) * 0.5) * 10.0 AS duos_gbp,
    ABS((a.levelTo - a.levelFrom) * 0.5) * 11.145 AS levies_gbp,
    
    a.soFlag
    
  FROM combined_boalf a
  LEFT JOIN combined_bod p 
    ON a.bmUnit = p.bmUnit 
    AND CAST(a.settlementDate AS DATE) = CAST(p.settlementDate AS DATE)
    AND a.settlementPeriod = p.settlementPeriod
  LEFT JOIN bmu_lookup b ON a.bmUnit = b.bmUnit
  LEFT JOIN wholesale_prices w 
    ON CAST(a.settlementDate AS DATE) = CAST(w.settlementDate AS DATE)
    AND a.settlementPeriod = w.settlementPeriod
  WHERE 
    -- Must have valid price
    (p.offerPrice IS NOT NULL OR p.bidPrice IS NOT NULL)
    AND p.offerPrice < 9999
    AND p.bidPrice < 9999
),

-- Calculate total revenue per day
daily_revenue_with_total AS (
  SELECT
    *,
    bm_value_gbp - wholesale_cost_gbp - duos_gbp - levies_gbp AS total_revenue_gbp,
    bm_value_gbp - wholesale_cost_gbp - duos_gbp - levies_gbp / NULLIF(ABS(delivered_volume_mwh), 0) AS net_margin_gbp_per_mwh
  FROM daily_revenue
),

-- Monthly aggregates for GB total
monthly_gb_total AS (
  SELECT
    'GB_total' as breakdown,
    CAST(NULL AS STRING) as dno,
    month_start,
    FORMAT_DATE('%Y-%m', month_start) as month_label,
    
    -- BM Revenue metrics
    MAX(bm_value_gbp) as max_bm_value_daily,
    MIN(bm_value_gbp) as min_bm_value_daily,
    AVG(bm_value_gbp) as avg_bm_value_daily,
    SUM(bm_value_gbp) as total_bm_value_monthly,
    
    -- Net Revenue metrics
    MAX(total_revenue_gbp) as max_net_revenue_daily,
    MIN(total_revenue_gbp) as min_net_revenue_daily,
    AVG(total_revenue_gbp) as avg_net_revenue_daily,
    SUM(total_revenue_gbp) as total_net_revenue_monthly,
    
    -- Net Margin metrics (£/MWh)
    MAX(net_margin_gbp_per_mwh) as max_margin,
    MIN(net_margin_gbp_per_mwh) as min_margin,
    AVG(net_margin_gbp_per_mwh) as avg_margin,
    
    -- Volume metrics
    MAX(ABS(delivered_volume_mwh)) as max_volume_daily,
    MIN(ABS(delivered_volume_mwh)) as min_volume_daily,
    AVG(ABS(delivered_volume_mwh)) as avg_volume_daily,
    SUM(delivered_volume_mwh) as total_volume_monthly,
    
    -- Operational metrics
    COUNT(DISTINCT bm_unit_id) as active_units,
    COUNT(*) as total_acceptances,
    SUM(CASE WHEN soFlag = TRUE THEN 1 ELSE 0 END) as so_initiated_count
    
  FROM daily_revenue_with_total
  GROUP BY month_start
),

-- Monthly aggregates by DNO
monthly_by_dno AS (
  SELECT
    'by_dno' as breakdown,
    dno,
    month_start,
    FORMAT_DATE('%Y-%m', month_start) as month_label,
    
    -- BM Revenue metrics
    MAX(bm_value_gbp) as max_bm_value_daily,
    MIN(bm_value_gbp) as min_bm_value_daily,
    AVG(bm_value_gbp) as avg_bm_value_daily,
    SUM(bm_value_gbp) as total_bm_value_monthly,
    
    -- Net Revenue metrics
    MAX(total_revenue_gbp) as max_net_revenue_daily,
    MIN(total_revenue_gbp) as min_net_revenue_daily,
    AVG(total_revenue_gbp) as avg_net_revenue_daily,
    SUM(total_revenue_gbp) as total_net_revenue_monthly,
    
    -- Net Margin metrics
    MAX(net_margin_gbp_per_mwh) as max_margin,
    MIN(net_margin_gbp_per_mwh) as min_margin,
    AVG(net_margin_gbp_per_mwh) as avg_margin,
    
    -- Volume metrics
    MAX(ABS(delivered_volume_mwh)) as max_volume_daily,
    MIN(ABS(delivered_volume_mwh)) as min_volume_daily,
    AVG(ABS(delivered_volume_mwh)) as avg_volume_daily,
    SUM(delivered_volume_mwh) as total_volume_monthly,
    
    -- Operational metrics
    COUNT(DISTINCT bm_unit_id) as active_units,
    COUNT(*) as total_acceptances,
    SUM(CASE WHEN soFlag = TRUE THEN 1 ELSE 0 END) as so_initiated_count
    
  FROM daily_revenue_with_total
  WHERE dno IS NOT NULL
  GROUP BY dno, month_start
)

-- Combine both breakdowns
SELECT * FROM monthly_gb_total
UNION ALL
SELECT * FROM monthly_by_dno

ORDER BY 
  CASE breakdown
    WHEN 'GB_total' THEN 1
    WHEN 'by_dno' THEN 2
  END,
  dno,
  month_start DESC;

-- ============================================================================
-- USAGE EXAMPLES FOR SPARKLINES
-- ============================================================================

-- Example 1: Get 12-month sparkline data for GB total net margin
-- SELECT month_label, avg_margin, max_margin, min_margin
-- FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_monthly_sparklines`
-- WHERE breakdown = 'GB_total'
-- ORDER BY month_start DESC
-- LIMIT 12;

-- Example 2: Get revenue trend for specific DNO
-- SELECT month_label, total_net_revenue_monthly, avg_margin
-- FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_monthly_sparklines`
-- WHERE breakdown = 'by_dno' AND dno = 'YOUR_DNO'
-- ORDER BY month_start DESC
-- LIMIT 12;

-- Example 3: Sparkline array for Google Sheets SPARKLINE function
-- =SPARKLINE(
--   QUERY(vlp_revenue_monthly_sparklines, 
--     "SELECT avg_margin WHERE breakdown='GB_total' ORDER BY month_start DESC LIMIT 12"),
--   {"charttype", "line"; "color", "blue"}
-- )
