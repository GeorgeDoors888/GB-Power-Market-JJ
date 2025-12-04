-- ============================================================================
-- VLP REVENUE 7-DAY SUMMARY VIEW - PHASE 1 TASK 2
-- ============================================================================
-- Purpose: Pre-aggregated 7-day summary for Dashboard V3 KPIs
-- Depends on: inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp (Task 1)
-- Target: inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary` AS

WITH 
-- Get ALL available revenue data (table has fixed Oct 2025 data until updated)
-- TODO: Change to INTERVAL 7 DAY once table is updated daily
last_7d AS (
  SELECT * 
  FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp`
  -- FIX: Table only has Oct 2025, use all available data for now
  -- WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
),

-- Aggregate for GB total (all BMUs across Great Britain)
gb_total AS (
  SELECT
    'GB_total' AS breakdown,
    CAST(NULL AS STRING) AS dno,
    CAST(NULL AS STRING) AS bm_unit_id,
    
    -- Revenue metrics
    SUM(bm_value_gbp) AS BM_revenue_gbp,
    SUM(delivered_volume_mwh) AS net_balancing_volume_mwh,
    SUM(total_revenue_gbp) AS total_revenue_gbp,
    SUM(wholesale_cost_gbp) AS total_wholesale_cost_gbp,
    SUM(duos_gbp) AS total_duos_gbp,
    SUM(levies_gbp) AS total_levies_gbp,
    
    -- Calculate weighted average prices
    SUM(bm_value_gbp) / NULLIF(SUM(ABS(delivered_volume_mwh)), 0) AS avg_bm_price_gbp_per_mwh,
    SUM(total_revenue_gbp) / NULLIF(SUM(ABS(delivered_volume_mwh)), 0) AS net_margin_gbp_per_mwh,
    
    -- Operational metrics
    COUNT(DISTINCT bm_unit_id) AS active_units,
    COUNT(DISTINCT acceptance_number) AS total_acceptances,
    COUNT(*) AS total_records,
    
    -- Volume breakdown
    SUM(CASE WHEN action_type = 'offer_up' THEN delivered_volume_mwh ELSE 0 END) AS offer_up_volume_mwh,
    SUM(CASE WHEN action_type = 'bid_down' THEN ABS(delivered_volume_mwh) ELSE 0 END) AS bid_down_volume_mwh,
    
    -- SO flag analysis
    SUM(CASE WHEN so_flag = TRUE THEN 1 ELSE 0 END) AS so_initiated_count,
    SUM(CASE WHEN so_flag = TRUE THEN ABS(delivered_volume_mwh) ELSE 0 END) AS so_initiated_volume_mwh
    
  FROM last_7d
),

-- Aggregate by DNO (for selected DNO filtering)
by_dno AS (
  SELECT
    'selected_dno' AS breakdown,
    dno,
    CAST(NULL AS STRING) AS bm_unit_id,
    
    -- Revenue metrics
    SUM(bm_value_gbp) AS BM_revenue_gbp,
    SUM(delivered_volume_mwh) AS net_balancing_volume_mwh,
    SUM(total_revenue_gbp) AS total_revenue_gbp,
    SUM(wholesale_cost_gbp) AS total_wholesale_cost_gbp,
    SUM(duos_gbp) AS total_duos_gbp,
    SUM(levies_gbp) AS total_levies_gbp,
    
    -- Calculate weighted average prices
    SUM(bm_value_gbp) / NULLIF(SUM(ABS(delivered_volume_mwh)), 0) AS avg_bm_price_gbp_per_mwh,
    SUM(total_revenue_gbp) / NULLIF(SUM(ABS(delivered_volume_mwh)), 0) AS net_margin_gbp_per_mwh,
    
    -- Operational metrics
    COUNT(DISTINCT bm_unit_id) AS active_units,
    COUNT(DISTINCT acceptance_number) AS total_acceptances,
    COUNT(*) AS total_records,
    
    -- Volume breakdown
    SUM(CASE WHEN action_type = 'offer_up' THEN delivered_volume_mwh ELSE 0 END) AS offer_up_volume_mwh,
    SUM(CASE WHEN action_type = 'bid_down' THEN ABS(delivered_volume_mwh) ELSE 0 END) AS bid_down_volume_mwh,
    
    -- SO flag analysis
    SUM(CASE WHEN so_flag = TRUE THEN 1 ELSE 0 END) AS so_initiated_count,
    SUM(CASE WHEN so_flag = TRUE THEN ABS(delivered_volume_mwh) ELSE 0 END) AS so_initiated_volume_mwh
    
  FROM last_7d
  WHERE dno IS NOT NULL
  GROUP BY dno
),

-- Aggregate by individual BMU (for VLP portfolio tracking)
by_bmu AS (
  SELECT
    'vlp_portfolio' AS breakdown,
    dno,
    bm_unit_id,
    
    -- Revenue metrics
    SUM(bm_value_gbp) AS BM_revenue_gbp,
    SUM(delivered_volume_mwh) AS net_balancing_volume_mwh,
    SUM(total_revenue_gbp) AS total_revenue_gbp,
    SUM(wholesale_cost_gbp) AS total_wholesale_cost_gbp,
    SUM(duos_gbp) AS total_duos_gbp,
    SUM(levies_gbp) AS total_levies_gbp,
    
    -- Calculate weighted average prices
    SUM(bm_value_gbp) / NULLIF(SUM(ABS(delivered_volume_mwh)), 0) AS avg_bm_price_gbp_per_mwh,
    SUM(total_revenue_gbp) / NULLIF(SUM(ABS(delivered_volume_mwh)), 0) AS net_margin_gbp_per_mwh,
    
    -- Operational metrics
    COUNT(DISTINCT bm_unit_id) AS active_units,  -- Will be 1 for this level
    COUNT(DISTINCT acceptance_number) AS total_acceptances,
    COUNT(*) AS total_records,
    
    -- Volume breakdown
    SUM(CASE WHEN action_type = 'offer_up' THEN delivered_volume_mwh ELSE 0 END) AS offer_up_volume_mwh,
    SUM(CASE WHEN action_type = 'bid_down' THEN ABS(delivered_volume_mwh) ELSE 0 END) AS bid_down_volume_mwh,
    
    -- SO flag analysis
    SUM(CASE WHEN so_flag = TRUE THEN 1 ELSE 0 END) AS so_initiated_count,
    SUM(CASE WHEN so_flag = TRUE THEN ABS(delivered_volume_mwh) ELSE 0 END) AS so_initiated_volume_mwh
    
  FROM last_7d
  GROUP BY dno, bm_unit_id
)

-- Combine all three breakdown levels
SELECT * FROM gb_total
UNION ALL
SELECT * FROM by_dno
UNION ALL
SELECT * FROM by_bmu

ORDER BY 
  CASE breakdown
    WHEN 'GB_total' THEN 1
    WHEN 'selected_dno' THEN 2
    WHEN 'vlp_portfolio' THEN 3
  END,
  dno,
  bm_unit_id;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Get GB total summary
-- SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary`
-- WHERE breakdown = 'GB_total';

-- Example 2: Get specific DNO summary (e.g., UKPN-EPN)
-- SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary`
-- WHERE breakdown = 'selected_dno' AND dno = 'UKPN-EPN';

-- Example 3: Get all BMUs for a specific DNO
-- SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary`
-- WHERE breakdown = 'vlp_portfolio' AND dno = 'UKPN-EPN'
-- ORDER BY total_revenue_gbp DESC;

-- Example 4: Calculate All-GB Net Margin (for Dashboard V3 KPI I9)
-- SELECT net_margin_gbp_per_mwh 
-- FROM `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary`
-- WHERE breakdown = 'GB_total';

-- Example 5: Calculate Selected DNO metrics (for Dashboard V3 KPIs J9, K9, L9)
-- SELECT 
--   net_margin_gbp_per_mwh,  -- J9: Selected DNO Net Margin
--   net_balancing_volume_mwh, -- K9: Selected DNO Volume
--   total_revenue_gbp / 1000  -- L9: Selected DNO Revenue (£k)
-- FROM `inner-cinema-476211-u9.uk_energy_prod.bod_boalf_7d_summary`
-- WHERE breakdown = 'selected_dno' AND dno = 'YOUR_DNO_HERE';

-- ============================================================================
-- POST-CREATE NOTES
-- ============================================================================
-- 1. This view automatically refreshes when queried (uses latest vlp_revenue_sp data)
-- 2. Dashboard V3 KPI formulas should query this view, not raw tables
-- 3. Performance: View queries take ~2-5 seconds on 7 days of data
-- 4. Next steps: Update Dashboard V3 KPI formulas (Tasks 3-7)
-- ============================================================================
