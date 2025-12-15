#!/usr/bin/env python3
"""
BG Live Dashboard Updater
Updates the BG Live sheet with real-time grid data from BigQuery

Fills in #REF! errors for:
- VLP Revenue
- Wholesale prices
- Grid frequency  
- Total generation
- DNO-specific metrics

Author: Generated for GB Power Market JJ
Date: 7 December 2025
"""

import sys
import logging
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration
SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SHEET_NAME = 'GB Live'  # Fixed: was 'BG Live'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = '/home/george/inner-cinema-credentials.json'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_latest_system_price(bq_client):
    """Get latest system imbalance price (SBP/SSP) - single price since P305 Nov 2015"""
    # Get most recent system sell price from bmrs_costs (may be a few days old)
    query = f"""
    SELECT 
        systemSellPrice as price,
        settlementDate,
        settlementPeriod
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty and result['price'][0]:
            return round(float(result['price'][0]), 2)
    except Exception as e:
        logging.error(f"Error getting system price: {e}")
    
    return 0.0

def get_wholesale_avg(bq_client):
    """Get average wholesale price from last 7 days"""
    query = f"""
    SELECT 
        AVG(CAST(price AS FLOAT64)) as avg_price,
        SUM(CAST(volume AS FLOAT64)) as total_volume
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      AND price IS NOT NULL
      AND CAST(price AS FLOAT64) > 0
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        price = 0.0
        
        if not result.empty and result['avg_price'][0] is not None:
            price_val = result['avg_price'][0]
            # Check if valid number (not NaN)
            if price_val == price_val:  # NaN != NaN, so this checks for valid numbers
                price = float(price_val)
        
        # Fallback to bmrs_costs if bmrs_mid has no valid data
        if price == 0:
            fallback_query = f"""
            SELECT AVG(systemSellPrice) as avg_price
            FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
            WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
              AND systemSellPrice IS NOT NULL
            """
            fallback = bq_client.query(fallback_query).to_dataframe()
            if not fallback.empty and fallback['avg_price'][0] is not None:
                fallback_val = fallback['avg_price'][0]
                if fallback_val == fallback_val:  # Check not NaN
                    price = float(fallback_val)
        
        return {
            'price': round(price, 2),
            'volume_pct': 100.0  # Placeholder - needs market share calculation
        }
    except Exception as e:
        logging.error(f"Error getting wholesale avg: {e}")
    
    return {'price': 0.0, 'volume_pct': 0.0}

def get_grid_frequency(bq_client):
    """Get latest grid frequency from last hour"""
    query = f"""
    SELECT frequency
    FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
    WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    ORDER BY measurementTime DESC
    LIMIT 1
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty and result['frequency'][0]:
            return round(float(result['frequency'][0]), 3)
    except Exception as e:
        logging.error(f"Error getting frequency: {e}")
    
    return 50.0  # Default

def get_total_generation(bq_client):
    """Get CURRENT total generation (not cumulative) - latest settlement period"""
    query = f"""
    WITH latest_period AS (
      SELECT MAX(settlementPeriod) as max_period
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    )
    SELECT SUM(avg_gen) / 1000 as total_gen_gw
    FROM (
      SELECT fuelType, AVG(generation) as avg_gen
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND settlementPeriod = (SELECT max_period FROM latest_period)
      GROUP BY fuelType
    )
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty and result['total_gen_gw'][0]:
            gen_gw = round(float(result['total_gen_gw'][0]), 2)
            logging.info(f"  🔌 Total Generation (current period, deduplicated): {gen_gw} GW")
            return gen_gw
    except Exception as e:
        logging.error(f"Error getting total gen: {e}")
    
    return 0.0

def get_dno_metrics(bq_client, dno_region='All GB'):
    """Get DNO-specific volume and revenue from generation data"""
    # Use fuelinst for volume data
    query = f"""
    WITH combined AS (
      SELECT generation
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      UNION ALL
      SELECT generation
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    )
    SELECT 
        SUM(generation) / 2 as total_volume_mwh,
        SUM(generation) * 50 / 1000 as total_revenue_k
    FROM combined
    WHERE generation IS NOT NULL
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty:
            return {
                'volume': round(float(result['total_volume_mwh'][0] or 0), 2),
                'revenue': round(float(result['total_revenue_k'][0] or 0), 2)
            }
    except Exception as e:
        logging.error(f"Error getting DNO metrics: {e}")
    
    return {'volume': 0.0, 'revenue': 0.0}

def get_generation_mix(bq_client):
    """Get current generation mix by fuel type (excluding interconnectors) - FIXED ORDER"""
    query = f"""
    WITH latest_generation AS (
      SELECT 
        fuelType,
        AVG(generation) as avg_generation_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = (
          -- Get most recent date with data (may be yesterday if today's data not yet available)
          SELECT MAX(CAST(settlementDate AS DATE))
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        )
        AND settlementPeriod = (
          SELECT MAX(settlementPeriod) 
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE CAST(settlementDate AS DATE) = (
            SELECT MAX(CAST(settlementDate AS DATE))
            FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          )
        )
        AND fuelType NOT LIKE 'INT%'  -- Exclude interconnectors
      GROUP BY fuelType
    ),
    ordered_generation AS (
      SELECT 
        fuelType,
        avg_generation_mw / 1000 as generation_gw,
        avg_generation_mw / (SELECT SUM(avg_generation_mw) FROM latest_generation) as percentage,
        -- Fixed order as per WIND_FORECAST_DASHBOARD_DEPLOYMENT.md (6 PM Dec 8)
        CASE fuelType
          WHEN 'WIND' THEN 1
          WHEN 'CCGT' THEN 2
          WHEN 'NUCLEAR' THEN 3
          WHEN 'BIOMASS' THEN 4
          WHEN 'OTHER' THEN 5
          WHEN 'PS' THEN 6
          WHEN 'NPSHYD' THEN 7
          WHEN 'OCGT' THEN 8
          WHEN 'COAL' THEN 9
          WHEN 'OIL' THEN 10
          ELSE 99
        END as display_order
      FROM latest_generation
    )
    SELECT 
        fuelType,
        generation_gw,
        percentage
    FROM ordered_generation
    ORDER BY display_order
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        return result
    except Exception as e:
        logging.error(f"Error getting generation mix: {e}")
        return None

def get_interconnector_flows(bq_client):
    """Get current interconnector flows separately"""
    query = f"""
    WITH latest_flows AS (
      SELECT 
        fuelType,
        AVG(generation) as avg_flow_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = (
          -- Get most recent date with data
          SELECT MAX(CAST(settlementDate AS DATE))
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        )
        AND settlementPeriod = (
          SELECT MAX(settlementPeriod) 
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE CAST(settlementDate AS DATE) = (
            SELECT MAX(CAST(settlementDate AS DATE))
            FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          )
        )
        AND fuelType LIKE 'INT%'  -- Only interconnectors
      GROUP BY fuelType
    )
    SELECT 
        fuelType,
        avg_flow_mw
    FROM latest_flows
    ORDER BY avg_flow_mw DESC
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        return result
    except Exception as e:
        logging.error(f"Error getting interconnector flows: {e}")
        return None

def get_active_outages(bq_client):
    """Get top 10 active outages by unavailable capacity - deduplicated by asset with station names from BMU registration"""
    query = f"""
    WITH latest_outages AS (
      SELECT 
        assetId,
        assetName,
        fuelType,
        normalCapacity,
        unavailableCapacity,
        ROUND(100.0 * unavailableCapacity / NULLIF(normalCapacity, 0), 1) as pct_unavailable,
        eventStatus,
        eventStartTime,
        eventEndTime,
        cause,
        affectedUnit,
        ROW_NUMBER() OVER (PARTITION BY assetId ORDER BY createdTime DESC) as rn
      FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
      WHERE eventStatus = 'Active'
        AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
        AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
        AND unavailableCapacity > 50  -- Only significant outages
    )
    SELECT 
      o.assetId,
      o.assetName,
      CASE 
        WHEN o.assetId LIKE 'I_%' THEN 'Interconnector'
        WHEN o.fuelType IS NULL OR o.fuelType = '' THEN 'Unknown'
        ELSE o.fuelType
      END as fuelType,
      o.normalCapacity,
      o.unavailableCapacity,
      o.pct_unavailable,
      o.eventStatus,
      o.eventStartTime,
      o.eventEndTime,
      o.cause,
      o.affectedUnit,
      -- Calculate duration in days
      CASE 
        WHEN o.eventEndTime IS NOT NULL THEN 
          DATE_DIFF(DATE(o.eventEndTime), DATE(o.eventStartTime), DAY)
        ELSE NULL
      END as duration_days,
      -- Join with BMU registration to get proper station name
      -- Try both nationalgridbmunit and elexonbmunit since outage data uses either
      bmu.bmunitname as station_name,
      bmu.leadpartyname as operator_name
    FROM latest_outages o
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
      ON (o.affectedUnit = bmu.nationalgridbmunit OR o.affectedUnit = bmu.elexonbmunit)
    WHERE o.rn = 1  -- Only latest record per asset
    ORDER BY o.unavailableCapacity DESC
    LIMIT 10
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        logging.info(f"  ⚠️  Retrieved {len(result)} unique active outages (deduplicated) with station names from BMU registry")
        return result
    except Exception as e:
        logging.error(f"Error getting active outages: {e}")
        return None

def get_geographic_constraints(bq_client):
    """Get geographic constraint data for map visualization"""
    
    # 1. Top constrained regions by action count (last 7 days) - UNION historical + IRIS
    # Include transmission-connected units (T_ prefix) as separate category
    regions_query = f"""
    WITH combined_boalf AS (
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as date,
        levelFrom,
        levelTo,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND soFlag = TRUE
      UNION ALL
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as date,
        levelFrom,
        levelTo,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND soFlag = TRUE
    )
    SELECT 
      CASE
        -- Categorize transmission units by fuel type and location hints
        WHEN STARTS_WITH(boalf.bmUnit, 'T_') AND bmu.fueltype = 'WIND' THEN 'Transmission Wind'
        WHEN STARTS_WITH(boalf.bmUnit, 'T_') AND bmu.fueltype IN ('NPSHYD', 'PS') THEN 'Transmission Hydro/Pumped'
        WHEN STARTS_WITH(boalf.bmUnit, 'T_') THEN 'Transmission Other'
        -- Interconnectors
        WHEN STARTS_WITH(boalf.bmUnit, 'I_') OR bmu.bmunittype = 'I' THEN 'Interconnectors'
        -- Distribution-connected with GSP groups
        WHEN bmu.gspgroupname IS NOT NULL AND bmu.gspgroupname != '' THEN bmu.gspgroupname
        -- Unmapped
        ELSE 'Other/Unmapped'
      END as region,
      COUNT(DISTINCT boalf.bmUnit) as units_constrained,
      COUNT(*) as action_count,
      ROUND(SUM(ABS(boalf.levelTo - boalf.levelFrom)), 1) as total_mw_adjusted
    FROM combined_boalf boalf
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu 
      ON (boalf.bmUnit = bmu.nationalgridbmunit OR boalf.bmUnit = bmu.elexonbmunit)
    GROUP BY region
    HAVING region NOT IN ('Other/Unmapped')  -- Exclude unmapped units
    ORDER BY action_count DESC
    LIMIT 15
    """
    
    # 2. Regional constraint costs (last 7 days) - only historical DISBSAD (no IRIS version)
    # Note: DISBSAD data typically lags by 1-2 days due to settlement processing
    costs_query = f"""
    SELECT 
      CASE
        -- Categorize transmission units by fuel type
        WHEN STARTS_WITH(disbsad.assetId, 'T_') AND bmu.fueltype = 'WIND' THEN 'Transmission Wind'
        WHEN STARTS_WITH(disbsad.assetId, 'T_') AND bmu.fueltype IN ('NPSHYD', 'PS') THEN 'Transmission Hydro/Pumped'
        WHEN STARTS_WITH(disbsad.assetId, 'T_') THEN 'Transmission Other'
        -- Interconnectors
        WHEN STARTS_WITH(disbsad.assetId, 'I_') OR bmu.bmunittype = 'I' THEN 'Interconnectors'
        -- Distribution-connected with GSP groups
        WHEN bmu.gspgroupname IS NOT NULL AND bmu.gspgroupname != '' THEN bmu.gspgroupname
        -- Unmapped
        ELSE 'Other/Unmapped'
      END as region,
      ROUND(SUM(disbsad.cost) / 1000, 2) as cost_thousands,
      MAX(CAST(disbsad.settlementDate AS DATE)) as latest_cost_date
    FROM `{PROJECT_ID}.{DATASET}.bmrs_disbsad` disbsad
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu 
      ON (disbsad.assetId = bmu.nationalgridbmunit OR disbsad.assetId = bmu.elexonbmunit)
    WHERE CAST(disbsad.settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      AND disbsad.cost > 0
    GROUP BY region
    HAVING region NOT IN ('Other/Unmapped')
    ORDER BY cost_thousands DESC
    LIMIT 15
    """
    
    # 3. Scotland wind curtailment (last 7 days, not just today) - UNION historical + IRIS
    scotland_query = f"""
    WITH combined_boalf AS (
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as date,
        levelFrom,
        levelTo,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND soFlag = TRUE
      UNION ALL
      SELECT 
        bmUnit,
        CAST(settlementDate AS DATE) as date,
        levelFrom,
        levelTo,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND soFlag = TRUE
    )
    SELECT 
      COUNT(DISTINCT boalf.bmUnit) as wind_units,
      COUNT(*) as curtailment_actions,
      ROUND(SUM(ABS(boalf.levelFrom - boalf.levelTo)), 1) as mw_curtailed
    FROM combined_boalf boalf
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu 
      ON (boalf.bmUnit = bmu.nationalgridbmunit OR boalf.bmUnit = bmu.elexonbmunit)
    WHERE (bmu.gspgroupname IN ('North Scotland', 'South Scotland')
           OR boalf.bmUnit LIKE 'T_%')  -- Include transmission wind
      AND UPPER(COALESCE(bmu.fueltype, '')) = 'WIND'
      AND boalf.levelTo < boalf.levelFrom  -- Downward adjustment = curtailment
    """
    
    try:
        regions = bq_client.query(regions_query).to_dataframe()
        costs = bq_client.query(costs_query).to_dataframe()
        scotland = bq_client.query(scotland_query).to_dataframe()
        
        # Merge costs into regions dataframe
        if not regions.empty and not costs.empty:
            regions = regions.merge(costs, on='region', how='left')
            regions['cost_thousands'] = regions['cost_thousands'].fillna(0)
            # Get the latest cost date to show data freshness
            latest_cost_date = costs['latest_cost_date'].max() if 'latest_cost_date' in costs.columns else None
        else:
            latest_cost_date = None
        
        result = {
            'regions': regions,
            'scotland_curtailment': scotland if not scotland.empty else None,
            'cost_data_date': latest_cost_date
        }
        
        logging.info(f"  🗺️  Retrieved geographic constraints: {len(regions)} regions, Scotland curtailment data")
        return result
    except Exception as e:
        logging.error(f"Error getting geographic constraints: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_historical_metrics_48periods(bq_client):
    """Get last 48 settlement periods of historical data for all metrics"""
    query = f"""
    WITH recent_periods AS (
      SELECT DISTINCT
        settlementDate,
        settlementPeriod
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
      ORDER BY settlementDate DESC, settlementPeriod DESC
      LIMIT 48
    ),
    ordered_periods AS (
      SELECT * FROM recent_periods ORDER BY settlementDate, settlementPeriod
    ),
    generation_data AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        SUM(avg_gen) / 1000 as total_gen_gw
      FROM (
        SELECT 
          settlementDate, 
          settlementPeriod, 
          fuelType,
          AVG(generation) as avg_gen
        FROM (
          SELECT settlementDate, settlementPeriod, fuelType, generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
          UNION ALL
          SELECT settlementDate, settlementPeriod, fuelType, generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        )
        GROUP BY settlementDate, settlementPeriod, fuelType
      )
      GROUP BY date, settlementPeriod
    ),
    prices_data AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        AVG(systemSellPrice) as wholesale_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
      GROUP BY date, settlementPeriod
    )
    SELECT 
      o.settlementDate,
      o.settlementPeriod,
      COALESCE(p.wholesale_price, 0) as wholesale_price,
      COALESCE(g.total_gen_gw, 0) as total_gen_gw,
      50.0 as frequency
    FROM ordered_periods o
    LEFT JOIN prices_data p ON CAST(o.settlementDate AS DATE) = p.date AND o.settlementPeriod = p.settlementPeriod
    LEFT JOIN generation_data g ON CAST(o.settlementDate AS DATE) = g.date AND o.settlementPeriod = g.settlementPeriod
    ORDER BY o.settlementDate, o.settlementPeriod
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        return result
    except Exception as e:
        logging.error(f"Error getting historical metrics: {e}")
        return None

def get_fuel_specific_timeseries(bq_client, fuel_types):
    """Get last 48 periods (full day) of generation data for each fuel type for sparklines"""
    fuel_list_str = "', '".join(fuel_types)
    query = f"""
    WITH recent_data AS (
      SELECT 
        fuelType,
        settlementPeriod,
        AVG(generation) / 1000 as generation_gw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND fuelType IN ('{fuel_list_str}')
      GROUP BY fuelType, settlementPeriod
      ORDER BY settlementPeriod ASC  -- Start from period 1 (00:00)
    )
    SELECT * FROM recent_data
    ORDER BY fuelType, settlementPeriod
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        return result
    except Exception as e:
        logging.error(f"Error getting fuel timeseries: {e}")
        return None

def get_intraday_charts_data(bq_client):
    """Get today's intraday data for wind, demand, and price"""
    query = f"""
    WITH today_data AS (
      SELECT 
        settlementPeriod,
        SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) / 1000 as wind_gw,
        SUM(generation) / 1000 as total_demand_gw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
      ORDER BY settlementPeriod
    ),
    prices AS (
      SELECT 
        settlementPeriod,
        AVG(CAST(price AS FLOAT64)) as avg_price
      FROM (
        SELECT settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        UNION ALL
        SELECT settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      )
      GROUP BY settlementPeriod
    )
    SELECT 
        t.settlementPeriod,
        t.wind_gw,
        t.total_demand_gw,
        COALESCE(p.avg_price, 0) as price
    FROM today_data t
    LEFT JOIN prices p ON t.settlementPeriod = p.settlementPeriod
    ORDER BY t.settlementPeriod
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        return result
    except Exception as e:
        logging.error(f"Error getting intraday data: {e}")
        return None

def get_wind_forecast_vs_actual(bq_client):
    """Get wind forecast vs actual for last 48 periods with error analysis"""
    query = f"""
    WITH 
    -- Get actual wind generation by settlement period (last 48 periods)
    actual_wind AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            AVG(generation) / 1000 as actual_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE fuelType = 'WIND'
        AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        GROUP BY settlementDate, settlementPeriod
    ),
    -- Get wind forecasts (match to settlement periods)
    forecast_wind AS (
        SELECT 
            DATE(startTime) as settlementDate,
            EXTRACT(HOUR FROM startTime) * 2 + 
            CASE WHEN EXTRACT(MINUTE FROM startTime) >= 30 THEN 2 ELSE 1 END as settlementPeriod,
            AVG(generation) / 1000 as forecast_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
        WHERE startTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)
        GROUP BY settlementDate, settlementPeriod
    ),
    -- Join forecast and actual
    combined AS (
        SELECT 
            a.settlementDate,
            a.settlementPeriod,
            a.actual_gw,
            COALESCE(f.forecast_gw, a.actual_gw) as forecast_gw,
            (a.actual_gw - COALESCE(f.forecast_gw, a.actual_gw)) as error_gw,
            CASE 
                WHEN f.forecast_gw IS NOT NULL AND f.forecast_gw > 0 
                THEN ((a.actual_gw - f.forecast_gw) / f.forecast_gw * 100)
                ELSE 0
            END as error_pct
        FROM actual_wind a
        LEFT JOIN forecast_wind f 
            ON a.settlementDate = f.settlementDate 
            AND a.settlementPeriod = f.settlementPeriod
        ORDER BY a.settlementDate DESC, a.settlementPeriod DESC
        LIMIT 48
    )
    SELECT * FROM combined
    ORDER BY settlementDate ASC, settlementPeriod ASC
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty:
            # Calculate summary statistics
            current_actual = float(result.iloc[-1]['actual_gw'])
            current_forecast = float(result.iloc[-1]['forecast_gw'])
            current_error_pct = float(result.iloc[-1]['error_pct'])
            
            # 24h trend (48 periods ago)
            day_ago_actual = float(result.iloc[0]['actual_gw'])
            trend_pct = ((current_actual - day_ago_actual) / day_ago_actual * 100) if day_ago_actual > 0 else 0
            
            # Average error over 48 periods
            avg_error_pct = float(result['error_pct'].mean())
            
            return {
                'dataframe': result,
                'current_actual_gw': current_actual,
                'current_forecast_gw': current_forecast,
                'current_error_pct': current_error_pct,
                'trend_24h_pct': trend_pct,
                'avg_error_pct': avg_error_pct,
                'forecast_bias': 'UNDER' if avg_error_pct > 0 else 'OVER'
            }
    except Exception as e:
        logging.error(f"Error getting wind forecast vs actual: {e}")
    
    return None

def update_dashboard():
    """Main update function"""
    try:
        logging.info("=" * 80)
        logging.info("🔄 BG LIVE DASHBOARD UPDATE STARTED")
        logging.info("=" * 80)
        
        # Initialize clients
        logging.info("🔧 Connecting to Google Sheets and BigQuery...")
        
        # Google Sheets
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        sheets_creds = service_account.Credentials.from_service_account_file(
            SA_FILE, scopes=SCOPES
        )
        gc = gspread.authorize(sheets_creds)
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        
        # BigQuery
        bq_credentials = service_account.Credentials.from_service_account_file(
            SA_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_credentials, location="US")
        
        logging.info("✅ Connected successfully")
        
        # Clear error message and update timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status_updates = [
            {'range': 'A2', 'values': [[f'✅ LIVE — Updated: {timestamp}']]},
            {'range': 'B2', 'values': [[timestamp]]}
        ]
        sheet.batch_update(status_updates)
        logging.info(f"📅 Updated timestamp: {timestamp}")
        
        # Get DNO region from sheet
        dno_region = sheet.acell('F3').value or 'All GB'
        logging.info(f"🗺️  DNO Region: {dno_region}")
        
        # Fetch all metrics
        logging.info("📊 Fetching metrics from BigQuery...")
        
        system_price = get_latest_system_price(bq_client)
        logging.info(f"  💰 System Price (SBP/SSP): £{system_price}/MWh")
        
        wholesale = get_wholesale_avg(bq_client)
        logging.info(f"  💷 Wholesale Avg: £{wholesale['price']}/MWh")
        
        frequency = get_grid_frequency(bq_client)
        logging.info(f"  ⚡ Grid Frequency: {frequency} Hz")
        
        total_gen = get_total_generation(bq_client)
        logging.info(f"  🔌 Total Generation: {total_gen} GW")
        
        dno_metrics = get_dno_metrics(bq_client, dno_region)
        logging.info(f"  📍 DNO Volume: {dno_metrics['volume']} MWh")
        logging.info(f"  💵 DNO Revenue: £{dno_metrics['revenue']}k")
        
        # Update sheet cells - row 6/7 layout for dashboard
        logging.info("✍️  Writing to sheet...")
        
        # Update KPI in combined "Label: Value" format (row 7 only, row 6 cleared)
        kpi_updates = [
            ('A6', ''),  # Clear header
            ('A7', f'SBP/SSP Price: £{system_price}/MWh'),
            ('B6', ''),
            ('B7', f'Wholesale Price: £{wholesale["price"]:.2f}/MWh'),
            ('C6', ''),
            ('C7', f'Generation: {total_gen:.2f} GW'),
            ('D6', ''),
            ('D7', f'Grid Frequency: {frequency} Hz'),
            ('E6', ''),
            ('E7', 'Demand: TBD'),  # Will be updated after gen mix calculation
            ('F6', ''),
            ('F7', 'Net IC Flow: TBD'),  # Will be updated after interconnector calculation
        ]
        
        for cell, value in kpi_updates:
            sheet.update_acell(cell, value)
            logging.info(f"  ✅ Updated {cell}: {value}")
        
        # Legacy cells for compatibility
        updates = [
            ('F3', system_price),
            ('G3', 0 if wholesale['price'] != wholesale['price'] else wholesale['price']),
            ('H3', wholesale['volume_pct']),
            ('I3', frequency),
            ('J3', total_gen),
            ('K3', dno_metrics['volume']),
            ('L3', dno_metrics['revenue']),
        ]
        
        for cell, value in updates:
            if value != value:  # NaN check
                value = 0
            sheet.update_acell(cell, value)
        
        # Get and update generation mix table
        logging.info("📊 Updating generation mix table...")
        gen_mix = get_generation_mix(bq_client)
        interconnectors = get_interconnector_flows(bq_client)
        
        # DEBUG: Check what we got
        logging.info(f"DEBUG: gen_mix is None: {gen_mix is None}")
        if gen_mix is not None:
            logging.info(f"DEBUG: gen_mix is empty: {gen_mix.empty}")
            logging.info(f"DEBUG: gen_mix shape: {gen_mix.shape}")
            logging.info(f"DEBUG: gen_mix first row: {gen_mix.head(1).to_dict() if not gen_mix.empty else 'EMPTY'}")
        
        if gen_mix is not None and not gen_mix.empty:
            # Calculate totals
            total_fuel_gen_gw = gen_mix['generation_gw'].sum()
            total_interconnector_mw = interconnectors['avg_flow_mw'].sum() if interconnectors is not None and not interconnectors.empty else 0
            total_interconnector_gw = total_interconnector_mw / 1000
            
            # Calculate totals for display
            total_with_interconnectors = total_fuel_gen_gw + total_interconnector_gw
            total_demand = total_with_interconnectors
            
            # Update KPI row 7 with calculated values in "Label: Value" format
            ic_flow_text = f'+{total_interconnector_gw:.2f} GW' if total_interconnector_gw >= 0 else f'{total_interconnector_gw:.2f} GW'
            sheet.update_acell('E7', f'Demand: {total_demand:.2f} GW')
            sheet.update_acell('F7', f'Net IC Flow: {ic_flow_text}')
            
            # Update C7 and C8 with generation and demand totals
            sheet.update_acell('C7', f'{total_with_interconnectors:.2f} GW')
            sheet.update_acell('C8', f'Total Demand: {total_demand:.2f} GW')
            sheet.update_acell('A8', '')  # Clear old location
            
            logging.info(f"  ✅ Updated C7: Total Gen {total_with_interconnectors:.2f} GW (Fuel: {total_fuel_gen_gw:.2f} + IC: {total_interconnector_gw:.2f})")
            logging.info(f"  ✅ Updated E7: Demand {total_demand:.2f} GW")
            logging.info(f"  ✅ Updated F7: Net IC Flow {total_interconnector_gw:+.2f} GW")
            logging.info(f"  ✅ Updated C8: Total Demand {total_demand:.2f} GW")
            
            # Update generation mix rows (A10:C21)
            # Fuel type emoji mapping - matches WIND_FORECAST_DASHBOARD_DEPLOYMENT.md (6 PM Dec 8)
            fuel_emojis = {
                'WIND': '💨 Wind',
                'CCGT': '🔥 CCGT',
                'NUCLEAR': '⚛️ Nuclear',
                'BIOMASS': '🔌 Biomass',
                'OTHER': '⚡ Other',
                'PS': '💧 Pumped Storage',
                'NPSHYD': '🌊 Hydro',
                'OCGT': '🔥 OCGT',
                'COAL': '⛏️ Coal',
                'OIL': '🛢️ Oil',
            }
            
            interconnector_emojis = {
                'INTFR': '🇫🇷 INTFR',
                'INTEM': '🇧🇪 INTEM',
                'INTIRL': '🇮🇪 INTIRL',
                'INTNED': '🇳🇱 INTNED',
                'INTEW': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 INTEW',
                'INTIFA2': '🇫🇷 INTIFA2',
                'INTELEC': '⚡ INTELEC',
                'INTNEM': '🇧🇪 INTNEM',
                'INTNSL': '🇳🇴 INTNSL',
                'INTVKL': '🇩🇰 INTVKL',
                'INTGRNL': '🇬🇱 INTGRNL',
            }
            
            # Update fuel types in column A & B & C (GW, percentage) with inline format
            # Use batch update to avoid API quota
            fuel_updates = []
            row_num = 11  # Fixed: Start at row 11 (not 10)
            
            # Clear all rows first (A11:H22) to remove old data and prevent duplicates
            clear_updates = []
            for clear_row in range(11, 21):  # rows 11-20: fuel/IC data
                clear_updates.append({
                    'range': f'A{clear_row}:H{clear_row}',
                    'values': [[''] * 8]  # Clear A-H to remove old duplicate data
                })
            # Also clear rows 21-22 which had old headers
            clear_updates.append({'range': 'A21:H22', 'values': [[''] * 8, [''] * 8]})
            sheet.batch_update(clear_updates)
            logging.info(f"  ✅ Cleared rows 11-22 (columns A-H) to remove old data")
            
            # Now add fuel types - INLINE format (all in one cell column B)
            logging.info(f"📝 Building fuel updates for {len(gen_mix)} fuel types...")
            
            # Define colors and scales for sparklines
            sparkline_colors = ['#4ECDC4', '#FF6B6B', '#FFA07A', '#52B788', '#F7DC6F', '#45B7D1', '#BB8FCE', '#E76F51', '#264653', '#85C1E9']
            sparkline_max_vals = [20, 10, 5, 5, 2, 2, 1, 1, 1, 1]
            
            for idx, (_, row) in enumerate(gen_mix.iterrows()):
                if row_num > 20:  # Stop at row 20
                    break
                    
                fuel = row['fuelType']
                fuel_display = fuel_emojis.get(fuel, fuel)
                gen_gw = row['generation_gw']  # Already in GW
                percentage = row['percentage']  # Keep as decimal (0.463)
                percentage_display = percentage * 100  # For display (46.3%)
                
                # Calculate trend indicator
                trend_indicator = '→'
                if gen_gw > (total_gen * percentage * 1.05):
                    trend_indicator = '↑'
                elif gen_gw < (total_gen * percentage * 0.95):
                    trend_indicator = '↓'
                
                # Status with emoji
                if fuel == 'PS' and gen_gw < 0:
                    status = '⚫ Offline'
                elif gen_gw > 0.01:
                    status = '🟢 Active'
                else:
                    status = '⚫ Offline'
                
                # Column B: INLINE format combining everything in one cell
                inline_text = f'{gen_gw:.2f} GW | {percentage_display:.1f}% | {trend_indicator} | {status}'
                
                # Write to columns A-B (text data only, sparklines in C are manual)
                fuel_updates.append({
                    'range': f'A{row_num}:B{row_num}',
                    'values': [[fuel_display, inline_text]]
                })
                
                logging.info(f"  📝 Row {row_num}: {fuel_display} | {inline_text}")
                row_num += 1
            
            logging.info(f"📤 Batch updating {len(fuel_updates)} fuel rows...")
            if fuel_updates:
                # DEBUG: Print what we're sending
                logging.info(f"DEBUG: First fuel_update: {fuel_updates[0]}")
                sheet.batch_update(fuel_updates)
            
            logging.info(f"⏭️ Column C sparklines must be written via Apps Script (API limitation)")
            
            logging.info(f"⏭️ Skipping Column C sparkline writes (preserve manual formulas)...")
            # ⚠️ IMPORTANT: Google Sheets API cannot write cross-sheet SPARKLINE formulas
            # Solution: Enter formulas manually ONCE using generate_sparkline_formulas.py
            # The formulas will persist as long as we don't overwrite column C
            
            # Update interconnectors starting at row 11 in columns D-E (alongside fuel types)
            if interconnectors is not None and not interconnectors.empty:
                ic_updates = []
                ic_row = 11  # Start at row 11, align with fuel types
                
                for idx, row in interconnectors.iterrows():
                    if ic_row > 20:  # Stay within fuel type rows (11-20)
                        break
                        
                    ic_name = row['fuelType']
                    ic_display = interconnector_emojis.get(ic_name, ic_name)
                    flow_mw = int(row['avg_flow_mw'])
                    
                    # Extract country/name for display
                    country_map = {
                        'INTFR': '🇫🇷 France',
                        'INTEM': '🇧🇪 Belgium', 
                        'INTIRL': '🇮🇪 Ireland',
                        'INTNED': '🇳🇱 Netherlands',
                        'INTEW': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 E-W',
                        'INTIFA2': '🇫🇷 IFA2',
                        'INTELEC': '⚡ ElecLink',
                        'INTNEM': '🇧🇪 Belgium',
                        'INTNSL': '🇳🇴 Norway',
                        'INTVKL': '🇩🇰 Denmark',
                        'INTGRNL': '🇬🇱 Greenlink',
                    }
                    country_display = country_map.get(ic_name, ic_name)
                    
                    # Direction and status
                    if flow_mw > 10:
                        direction = '← Import'
                        status = '🟢 Active'
                    elif flow_mw < -10:
                        direction = '→ Export'
                        status = '🟢 Active'
                    else:
                        direction = '—'
                        status = '⚫ Idle'
                    
                    # Column E: INLINE format combining everything in one cell
                    ic_inline_text = f'{abs(flow_mw)} MW | {direction} | {status}'
                    
                    # Write to columns D-E (text data only, sparklines in F are manual)
                    ic_updates.append({
                        'range': f'D{ic_row}:E{ic_row}',
                        'values': [[country_display, ic_inline_text]]
                    })
                    
                    logging.info(f"  ✅ Row {ic_row}: {country_display} | {ic_inline_text}")
                    ic_row += 1
                
                # Batch update interconnectors
                if ic_updates:
                    sheet.batch_update(ic_updates)
                
                logging.info(f"⏭️ Column F sparklines must be written via Apps Script (API limitation)")
            
            # Get fuel-specific timeseries data for individual sparklines (48 periods)
            logging.info("📈 Fetching fuel-specific timeseries for sparklines (48 periods)...")
            fuel_types_list = gen_mix['fuelType'].tolist() if gen_mix is not None else []
            fuel_timeseries = get_fuel_specific_timeseries(bq_client, fuel_types_list)
            
            # Write fuel timeseries to Data_Hidden sheet (rows 10+, all 48 periods)
            if fuel_timeseries is not None and not fuel_timeseries.empty:
                try:
                    data_sheet = spreadsheet.worksheet('Data_Hidden')
                except:
                    data_sheet = spreadsheet.add_worksheet(title='Data_Hidden', rows=100, cols=100)
                
                timeseries_updates = []
                for idx, fuel in enumerate(fuel_types_list):
                    fuel_data = fuel_timeseries[fuel_timeseries['fuelType'] == fuel].sort_values('settlementPeriod')
                    gen_values = fuel_data['generation_gw'].tolist()
                    # Pad with zeros at the end for periods that haven't happened yet (future periods)
                    while len(gen_values) < 48:
                        gen_values.append(0)
                    
                    timeseries_updates.append({
                        'range': f'A{10+idx}:AV{10+idx}',
                        'values': [gen_values[:48]]  # All 48 periods
                    })
                
                if timeseries_updates:
                    data_sheet.batch_update(timeseries_updates)
                    logging.info(f"  ✅ Stored timeseries for {len(timeseries_updates)} fuel types")
        
        # Get 48-period historical data for metric sparklines
        logging.info("📈 Fetching 48-period historical data...")
        historical = get_historical_metrics_48periods(bq_client)
        
        if historical is not None and not historical.empty:
            logging.info(f"  ✅ Retrieved {len(historical)} historical periods")
            
            # Calculate VLP revenue for each period (proxy using wholesale price * 1000)
            vlp_revenue_series = (historical['wholesale_price'] * 1000).tolist()
            wholesale_series = historical['wholesale_price'].tolist()
            total_gen_series = historical['total_gen_gw'].tolist()
            frequency_series = historical['frequency'].tolist()
            
            # Write historical data to hidden area (rows 30-36, columns M onwards for 48 periods = M:BL)
            historical_data_updates = [
                {'range': 'M30:BL30', 'values': [vlp_revenue_series[:48]]},  # VLP Revenue
                {'range': 'M31:BL31', 'values': [wholesale_series[:48]]},  # Wholesale
                {'range': 'M32:BL32', 'values': [[100] * min(48, len(historical))]},  # Market Vol (constant 100%)
                {'range': 'M33:BL33', 'values': [frequency_series[:48]]},  # Frequency
                {'range': 'M34:BL34', 'values': [total_gen_series[:48]]},  # Total Gen
                {'range': 'M35:BL35', 'values': [[0] * min(48, len(historical))]},  # DNO Volume (placeholder)
                {'range': 'M36:BL36', 'values': [[0] * min(48, len(historical))]},  # DNO Revenue (placeholder)
                {'range': 'L30:L36', 'values': [['VLP Rev £k'], ['Wholesale £/MWh'], ['Market %'], ['Freq Hz'], ['Gen GW'], ['Vol MWh'], ['Rev £k']]}
            ]
            
            sheet.batch_update(historical_data_updates)
            
            # ⚠️ REMOVED: E12:F15 sparklines conflicted with interconnector data in column E
            # Historical sparklines moved to separate dashboard section or removed entirely
            logging.info(f"  ✅ Stored 48-period historical data in M30:BL36 (hidden area)")
        
        # Get intraday chart data
        logging.info("📈 Fetching intraday chart data...")
        intraday = get_intraday_charts_data(bq_client)
        
        if intraday is not None and not intraday.empty:
            logging.info(f"  ✅ Retrieved {len(intraday)} settlement periods")
            
            # Write intraday data to hidden area (rows 25-27, columns M onwards)
            # Row 25: Wind GW data
            # Row 26: Demand GW data  
            # Row 27: Price £/MWh data
            
            wind_data = intraday['wind_gw'].tolist()
            demand_data = intraday['total_demand_gw'].tolist()
            price_data = intraday['price'].tolist()
            
            # Write to hidden Data_Hidden sheet instead of GB Live
            try:
                data_sheet = spreadsheet.worksheet('Data_Hidden')
            except:
                data_sheet = spreadsheet.add_worksheet(title='Data_Hidden', rows=100, cols=100)
                # Hide the sheet
                requests = [{
                    'updateSheetProperties': {
                        'properties': {'sheetId': data_sheet.id, 'hidden': True},
                        'fields': 'hidden'
                    }
                }]
                spreadsheet.batch_update({'requests': requests})
            
            intraday_updates = [
                {
                    'range': f'A1:AV1',  # All 48 settlement periods (columns A-AV)
                    'values': [wind_data[:48]]  # All 48 periods (00:00-23:59)
                },
                {
                    'range': f'A2:AV2',
                    'values': [demand_data[:48]]
                },
                {
                    'range': f'A3:AV3',
                    'values': [price_data[:48]]
                }
            ]
            
            data_sheet.batch_update(intraday_updates)
            
            # Add chart headers and sparkline formulas
            # Sparklines placed in A24:E36 (left) and F24:H36 (right) ranges for visual charts
            # Note: For best display, manually merge A24:E36 and F24:H36 in Google Sheets
            # This will make the sparklines display as large charts
            
            # Write headers (plain text)
            header_updates = [
                {
                    'range': 'A23',
                    'values': [['📊 System Demand (GW) - 48 Periods']]
                },
                {
                    'range': 'F23',
                    'values': [['💷 Wholesale Price (£/MWh) - 48 Periods']]
                },
                {
                    'range': 'A37',
                    'values': [['🔴 Demand (Red Bars) | Scale: 0-60 GW']]
                },
                {
                    'range': 'F37',
                    'values': [['🟢 Price | Scale: 0-150 £/MWh']]
                }
            ]
            sheet.batch_update(header_updates)
            
            # Unmerge cells first (in case they're already merged from previous run)
            sheet_id = sheet.id
            try:
                unmerge_requests = {
                    'requests': [
                        {
                            'unmergeCells': {
                                'range': {
                                    'sheetId': sheet_id,
                                    'startRowIndex': 23,  # Row 24
                                    'endRowIndex': 36,    # Row 36
                                    'startColumnIndex': 0,  # Column A
                                    'endColumnIndex': 8     # Column H
                                }
                            }
                        }
                    ]
                }
                spreadsheet.batch_update(unmerge_requests)
                logging.info(f"  ✅ Unmerged chart area (rows 24-36)")
            except Exception as e:
                logging.info(f"  ℹ️ No cells to unmerge (probably first run): {str(e)[:50]}")
            
            # Write sparkline formulas using Google Sheets API
            demand_sparkline = '=SPARKLINE(Data_Hidden!A2:AV2,{"charttype","column";"color","#FF6B6B";"max",60;"ymin",0;"axis",true;"axiscolor","#333"})'
            price_sparkline = '=SPARKLINE(Data_Hidden!A3:AV3,{"charttype","line";"linewidth",3;"color","#2ca02c";"max",150;"ymin",0;"axis",true;"axiscolor","#333"})'
            
            # Use direct Google Sheets API for formula updates
            try:
                from googleapiclient.discovery import build
                from google.oauth2.service_account import Credentials as APICredentials
                
                api_creds = APICredentials.from_service_account_file(
                    '/home/george/inner-cinema-credentials.json',
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                sheets_service = build('sheets', 'v4', credentials=api_creds)
                
                # Write formulas using values.update with USER_ENTERED
                sheets_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={
                        'valueInputOption': 'USER_ENTERED',
                        'data': [
                            {
                                'range': 'GB Live!A24',
                                'values': [[demand_sparkline]]
                            },
                            {
                                'range': 'GB Live!F24',
                                'values': [[price_sparkline]]
                            }
                        ]
                    }
                ).execute()
                
                logging.info(f"  ✅ Written chart sparkline formulas (A24, F24) via Sheets API")
                
                # DEBUG: Verify they were written
                verify_result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range='GB Live!A24:F24',
                    valueRenderOption='FORMULA'
                ).execute()
                verify_values = verify_result.get('values', [[]])[0]
                a24_present = len(verify_values) > 0 and 'SPARKLINE' in str(verify_values[0]).upper()
                f24_present = len(verify_values) > 5 and 'SPARKLINE' in str(verify_values[5]).upper()
                logging.info(f"  🔍 DEBUG: A24 has sparkline: {a24_present}, F24 has sparkline: {f24_present}")
                
            except Exception as e:
                logging.error(f"  ❌ Failed to write sparkline formulas: {e}")
                import traceback
                logging.error(traceback.format_exc())
            
            logging.info(f"  ✅ Written chart headers and sparkline formulas (rows 23-24)")
            
            # Merge cells for large chart display using Google Sheets API
            sheet_id = sheet.id
            merge_requests = {
                'requests': [
                    {
                        'mergeCells': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 23,  # Row 24 (0-indexed)
                                'endRowIndex': 36,    # Row 36 (exclusive, so up to row 36)
                                'startColumnIndex': 0,  # Column A
                                'endColumnIndex': 5     # Column E (exclusive, so A-E)
                            },
                            'mergeType': 'MERGE_ALL'
                        }
                    },
                    {
                        'mergeCells': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 23,  # Row 24
                                'endRowIndex': 36,    # Row 36
                                'startColumnIndex': 5,  # Column F
                                'endColumnIndex': 8     # Column H (exclusive, so F-H)
                            },
                            'mergeType': 'MERGE_ALL'
                        }
                    }
                ]
            }
            
            try:
                spreadsheet.batch_update(merge_requests)
                logging.info(f"  ✅ Merged chart ranges: A24:E36 and F24:H36")
            except Exception as e:
                logging.warning(f"  ⚠️ Could not merge cells (may already be merged): {e}")
            
            logging.info(f"  📊 Wind: {intraday['wind_gw'].iloc[-1]:.2f} GW (latest)")
            logging.info(f"  📊 Demand: {intraday['total_demand_gw'].iloc[-1]:.2f} GW (latest)")
            logging.info(f"  📊 Price: £{intraday['price'].iloc[-1]:.2f}/MWh (latest)")
            logging.info(f"  ✅ Updated sparklines with {len(wind_data)} periods")
        
        # Get wind forecast vs actual analysis
        logging.info("🌬️  Fetching wind forecast analysis...")
        wind_analysis = get_wind_forecast_vs_actual(bq_client)
        
        if wind_analysis:
            logging.info(f"  ✅ Retrieved wind forecast data")
            logging.info(f"  💨 Current Wind: {wind_analysis['current_actual_gw']:.2f} GW (actual)")
            logging.info(f"  📊 Forecast: {wind_analysis['current_forecast_gw']:.2f} GW")
            logging.info(f"  📈 Forecast Error: {wind_analysis['current_error_pct']:+.1f}%")
            logging.info(f"  📊 24h Trend: {wind_analysis['trend_24h_pct']:+.1f}%")
            
            df = wind_analysis['dataframe']
            
            # Write wind analysis section to rows 37-45
            # Row 37: Section Header
            # Row 38: Empty
            # Row 39: Wind Actual (current)
            # Row 40: Wind Forecast (current)
            # Row 41: Forecast Error %
            # Row 42: 24h Trend %
            # Row 43: Avg Error (48 periods)
            # Row 44: Forecast Bias
            # Row 45: Empty
            
            wind_section_updates = [
                {'range': 'A37', 'values': [['🌬️ WIND FORECAST ANALYSIS']]},
                {'range': 'A39', 'values': [['Wind Generation (Actual)']]},
                {'range': 'B39', 'values': [[f"{wind_analysis['current_actual_gw']:.2f} GW"]]},
                {'range': 'A40', 'values': [['Wind Forecast']]},
                {'range': 'B40', 'values': [[f"{wind_analysis['current_forecast_gw']:.2f} GW"]]},
                {'range': 'A41', 'values': [['Forecast Error']]},
                {'range': 'B41', 'values': [[f"{wind_analysis['current_error_pct']:+.1f}%"]]},
                {'range': 'A42', 'values': [['24h Wind Trend']]},
                {'range': 'B42', 'values': [[f"{wind_analysis['trend_24h_pct']:+.1f}%"]]},
                {'range': 'A43', 'values': [['Avg Error (48 periods)']]},
                {'range': 'B43', 'values': [[f"{wind_analysis['avg_error_pct']:+.1f}%"]]},
                {'range': 'A44', 'values': [['Forecast Bias']]},
                {'range': 'B44', 'values': [[wind_analysis['forecast_bias'] + '-FORECASTING']]},
            ]
            
            sheet.batch_update(wind_section_updates)
            
            # Write sparkline data to hidden area (rows 38-40, columns M onwards)
            # Row 38: Actual Wind GW (48 periods)
            # Row 39: Forecast Wind GW (48 periods)
            # Row 40: Error % (48 periods)
            
            actual_series = df['actual_gw'].tolist()
            forecast_series = df['forecast_gw'].tolist()
            error_series = df['error_pct'].tolist()
            
            wind_sparkline_data = [
                {'range': 'M38:BL38', 'values': [actual_series[:48]]},  # Actual Wind
                {'range': 'M39:BL39', 'values': [forecast_series[:48]]},  # Forecast Wind
                {'range': 'M40:BL40', 'values': [error_series[:48]]},  # Error %
                {'range': 'L38:L40', 'values': [['Wind Actual GW'], ['Wind Forecast GW'], ['Error %']]}
            ]
            
            sheet.batch_update(wind_sparkline_data)
            
            # Add wind sparklines with headers starting at row 45
            wind_sparklines = [
                # Row 45: Headers
                {'range': 'A45', 'values': [['📊 Visual Analysis']]},
                {'range': 'D45', 'values': [['Forecast vs Actual']]},
                {'range': 'E45', 'values': [['Forecast Error Trend']]},
                # Row 46-47: Sparklines in columns D-E
                # D46: Actual wind (green line)
                {'range': 'D46', 'values': [['=SPARKLINE(M38:BL38,{"charttype","line";"linewidth",2;"color","#2ca02c"})']]},
                # D47: Forecast wind (blue line)
                {'range': 'D47', 'values': [['=SPARKLINE(M39:BL39,{"charttype","line";"linewidth",2;"color","#1f77b4"})']]},
                # E46: Error percentage bar chart (red = under-forecast, blue = over-forecast)
                {'range': 'E46', 'values': [['=SPARKLINE(M40:BL40,{"charttype","column";"color1","#d62728";"color2","#1f77b4"})']]},
            ]
            
            sheet.batch_update(wind_sparklines, value_input_option='USER_ENTERED')
            
            logging.info(f"  ✅ Added wind forecast section with sparklines (rows 37-47)")
        
        # Add live outages section starting at row 50
        logging.info("⚠️  Fetching live outages data...")
        outages = get_active_outages(bq_client)
        
        # Also get total count of ALL outages (including small ones)
        total_outages_query = f"""
        WITH latest_outages AS (
          SELECT 
            unavailableCapacity,
            ROW_NUMBER() OVER (PARTITION BY assetId ORDER BY createdTime DESC) as rn
          FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
          WHERE eventStatus = 'Active'
            AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
            AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
            AND unavailableCapacity > 0
        )
        SELECT 
          COUNT(*) as total_count,
          SUM(unavailableCapacity) as total_mw
        FROM latest_outages
        WHERE rn = 1
        """
        total_stats = bq_client.query(total_outages_query).to_dataframe()
        total_outage_count = int(total_stats['total_count'].iloc[0]) if not total_stats.empty else 0
        total_unavailable_mw = total_stats['total_mw'].iloc[0] if not total_stats.empty else 0
        
        if outages is not None and not outages.empty:
            # Calculate unavailable capacity for TOP 10 shown
            top10_unavailable_gw = outages['unavailableCapacity'].sum() / 1000
            total_unavailable_gw = total_unavailable_mw / 1000
            
            # Section header at row 49
            outages_section = [
                {'range': 'A49', 'values': [['⚠️  LIVE OUTAGES ANALYSIS']]},
                {'range': 'A50', 'values': [['Total System Outages']]},
                {'range': 'B50', 'values': [[f"{total_outage_count} outages | {total_unavailable_gw:.2f} GW offline"]]},
                {'range': 'A51', 'values': [['Showing Top 10 (≥50 MW)']]},
                {'range': 'B51', 'values': [[f"{len(outages)} major outages | {top10_unavailable_gw:.2f} GW"]]},
            ]
            
            # Outage table header at row 53 (wider layout with BM Unit, Station Name, Duration)
            outages_section.append({'range': 'A53', 'values': [['BM Unit']]})
            outages_section.append({'range': 'B53', 'values': [['Station Name']]})
            outages_section.append({'range': 'C53', 'values': [['Fuel | MW Lost | % | Duration | Status']]})
            outages_section.append({'range': 'D53', 'values': [['Cause']]})
            
            # Add top 10 outages (rows 54-63)
            outage_row = 54
            for idx, row in outages.iterrows():
                if outage_row > 63:  # Limit to 10 rows
                    break
                
                asset_id = row['assetId']
                asset_name = row['assetName'] if row['assetName'] else asset_id
                # Use station name from BMU registration if available
                station_name = row['station_name'] if row['station_name'] and str(row['station_name']) != 'nan' else asset_name
                fuel = row['fuelType']
                unavail_mw = int(row['unavailableCapacity'])
                normal_mw = int(row['normalCapacity']) if row['normalCapacity'] else unavail_mw
                pct = row['pct_unavailable']
                cause = str(row['cause'])[:40]  # Truncate long causes
                bm_unit = str(row['affectedUnit']) if row['affectedUnit'] else asset_id
                operator = row['operator_name'] if row['operator_name'] and str(row['operator_name']) != 'nan' else ''
                
                # Duration info
                duration_days = row['duration_days']
                if duration_days and duration_days > 0:
                    duration_text = f"{int(duration_days)}d"
                elif row['eventEndTime']:
                    duration_text = "<1d"
                else:
                    duration_text = "Ongoing"
                
                # Add severity emoji based on MW lost
                if unavail_mw >= 1000:
                    severity = '🔴'
                elif unavail_mw >= 500:
                    severity = '🟠'
                else:
                    severity = '🟡'
                
                # Status indicator
                if pct >= 100:
                    status = '⚫ Offline'
                elif pct >= 50:
                    status = '🟠 Limited'
                else:
                    status = '🟡 Partial'
                
                # Column A: BM Unit ID
                outages_section.append({
                    'range': f'A{outage_row}',
                    'values': [[bm_unit]]
                })
                
                # Column B: Station Name from BMU registration (no VLOOKUP needed)
                outages_section.append({
                    'range': f'B{outage_row}',
                    'values': [[f"{severity} {station_name}"]]
                })
                
                # Column C: Comprehensive inline format (fuel, MW, %, duration, status)
                inline_info = f"{fuel} | {unavail_mw}/{normal_mw} MW | {pct:.0f}% | {duration_text} | {status}"
                outages_section.append({
                    'range': f'C{outage_row}',
                    'values': [[inline_info]]
                })
                
                # Column D: Cause
                outages_section.append({
                    'range': f'D{outage_row}',
                    'values': [[cause]]
                })
                
                outage_row += 1
            
            # Write all outages data
            sheet.batch_update(outages_section)
            logging.info(f"  ✅ Added live outages section (rows 49-63, {len(outages)} outages)")
        
        # Add geographic constraints section starting at row 65
        logging.info("🗺️  Fetching geographic constraints data...")
        geo_data = get_geographic_constraints(bq_client)
        
        if geo_data and not geo_data['regions'].empty:
            regions = geo_data['regions']
            scotland = geo_data['scotland_curtailment']
            cost_date = geo_data.get('cost_data_date')
            
            # Section header at row 65 with cost data freshness note
            if cost_date:
                cost_note = f"(Costs as of {cost_date.strftime('%b %d')})"
            else:
                cost_note = "(Cost data unavailable)"
            
            geo_section = [
                {'range': 'A65', 'values': [[f'🗺️  GEOGRAPHIC CONSTRAINTS (Last 7 Days) {cost_note}']]},
            ]
            
            # Scotland wind curtailment summary (row 66-67)
            if scotland is not None and not scotland.empty and scotland['mw_curtailed'].iloc[0] > 0:
                mw_curt = scotland['mw_curtailed'].iloc[0]
                wind_units = int(scotland['wind_units'].iloc[0])
                actions = int(scotland['curtailment_actions'].iloc[0])
                geo_section.extend([
                    {'range': 'A66', 'values': [['🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Wind Curtailment (Last 7 Days)']]},
                    {'range': 'B66', 'values': [[f"{mw_curt:,.0f} MW curtailed | {wind_units} units | {actions} actions"]]},
                ])
            else:
                geo_section.extend([
                    {'range': 'A66', 'values': [['🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scotland Wind Curtailment (Last 7 Days)']]},
                    {'range': 'B66', 'values': [['No significant curtailment in past 7 days']]},
                ])
            
            # Table header at row 68
            geo_section.extend([
                {'range': 'A68', 'values': [['Region']]},
                {'range': 'B68', 'values': [['Actions']]},
                {'range': 'C68', 'values': [['Units Affected']]},
                {'range': 'D68', 'values': [['MW Adjusted']]},
                {'range': 'E68', 'values': [['Cost (£k)']]},
            ])
            
            # Add top 10 constrained regions (rows 69-78)
            geo_row = 69
            for idx, row in regions.iterrows():
                if geo_row > 78:  # Limit to 10 rows
                    break
                
                region = row['region']
                actions = int(row['action_count'])
                units = int(row['units_constrained'])
                mw_adjusted = row['total_mw_adjusted']
                cost = row.get('cost_thousands', 0)
                
                # Add emoji based on activity level
                if actions >= 100:
                    emoji = '🔴'
                elif actions >= 50:
                    emoji = '🟠'
                else:
                    emoji = '🟡'
                
                geo_section.extend([
                    {'range': f'A{geo_row}', 'values': [[f"{emoji} {region}"]]},
                    {'range': f'B{geo_row}', 'values': [[actions]]},
                    {'range': f'C{geo_row}', 'values': [[units]]},
                    {'range': f'D{geo_row}', 'values': [[f"{mw_adjusted:,.0f}"]]},
                    {'range': f'E{geo_row}', 'values': [[f"£{cost:,.1f}k" if cost > 0 else "N/A"]]},
                ])
                
                geo_row += 1
            
            # Write all geographic constraints data
            sheet.batch_update(geo_section)
            logging.info(f"  ✅ Added geographic constraints section (rows 65-78, {len(regions)} regions)")
        else:
            # Write placeholder if no data
            geo_section = [
                {'range': 'A65', 'values': [['🗺️  GEOGRAPHIC CONSTRAINTS (Last 7 Days)']]},
                {'range': 'A66', 'values': [['No constraint data available for recent periods']]},
            ]
            sheet.batch_update(geo_section)
            logging.info(f"  ⚠️  No geographic constraints data available (historical data may be lagging)")
        
        logging.info("=" * 80)
        logging.info("✅ BG LIVE DASHBOARD UPDATE COMPLETE")
        logging.info("=" * 80)
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error updating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = update_dashboard()
    sys.exit(0 if success else 1)
