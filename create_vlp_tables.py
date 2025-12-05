#!/usr/bin/env python3
"""
Create missing VLP tables in BigQuery
Todos #3-5: site_metered_flows, esoservices_dc_site, capacity_market_site
"""

from google.cloud import bigquery
import json

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def create_site_metered_flows():
    """Todo #3: Create site_metered_flows table with realistic battery/CHP flows"""
    
    print('\n📊 Creating site_metered_flows table...')
    
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.site_metered_flows` AS
    WITH periods AS (
      SELECT
        c.settlementDate,
        c.settlementPeriod,
        c.systemBuyPrice AS wholesale_price,
        EXTRACT(DAYOFWEEK FROM c.settlementDate) AS day_of_week,
        CASE
          WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 'GREEN'
          WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
          WHEN c.settlementPeriod BETWEEN 17 AND 32 OR c.settlementPeriod BETWEEN 40 AND 44 THEN 'AMBER'
          ELSE 'GREEN'
        END AS duos_band
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs` c
      WHERE c.settlementDate >= '2025-10-17'
        AND c.settlementDate <= '2025-10-23'
    )
    SELECT
      settlementDate,
      settlementPeriod,
      'VLP_SITE_001' AS site_id,
      
      -- Battery charging (GREEN periods when price low)
      CASE 
        WHEN duos_band = 'GREEN' AND wholesale_price < 50 THEN 1.0  -- Charge 1 MWh (2 MW * 0.5h)
        ELSE 0.0
      END AS batt_charge_mwh,
      
      -- Battery discharging (RED periods when price high)
      CASE 
        WHEN duos_band = 'RED' AND wholesale_price > 60 THEN 1.2  -- Discharge 1.2 MWh (2.4 MW * 0.5h)
        WHEN duos_band = 'AMBER' AND wholesale_price > 70 THEN 0.8
        ELSE 0.0
      END AS batt_discharge_mwh,
      
      -- CHP export (run during high-price periods)
      CASE 
        WHEN duos_band = 'RED' THEN 0.5  -- 1 MW * 0.5h
        WHEN duos_band = 'AMBER' THEN 0.3
        ELSE 0.0
      END AS chp_export_mwh,
      
      -- CHP onsite consumption (meets site heat demand)
      CASE 
        WHEN day_of_week BETWEEN 2 AND 6 THEN 0.4  -- Weekdays: 0.8 MW * 0.5h
        ELSE 0.2  -- Weekends: 0.4 MW * 0.5h
      END AS chp_onsite_mwh,
      
      -- Grid import (when battery not discharging and CHP not covering full load)
      CASE 
        WHEN duos_band = 'RED' THEN 0.1
        WHEN duos_band = 'GREEN' THEN 0.3
        ELSE 0.2
      END AS site_import_mwh,
      
      -- Site total load (relatively constant baseload)
      1.0 AS site_load_mwh,  -- 2 MW average * 0.5h
      
      -- CHP thermal fuel input (total CHP output / electrical efficiency)
      CASE 
        WHEN duos_band = 'RED' THEN (0.5 + 0.4) / 0.40  -- 2.25 MWh thermal
        WHEN duos_band = 'AMBER' THEN (0.3 + 0.4) / 0.40
        WHEN day_of_week BETWEEN 2 AND 6 THEN 0.4 / 0.40
        ELSE 0.2 / 0.40
      END AS chp_fuel_mwh_th
      
    FROM periods
    ORDER BY settlementDate, settlementPeriod
    """
    
    client = bigquery.Client(project=PROJECT_ID)
    job = client.query(sql)
    job.result()
    
    # Verify
    verify_sql = f"""
    SELECT 
      COUNT(*) as row_count,
      MIN(settlementDate) as earliest,
      MAX(settlementDate) as latest,
      AVG(batt_charge_mwh) as avg_charge,
      AVG(batt_discharge_mwh) as avg_discharge,
      SUM(batt_charge_mwh) as total_charge,
      SUM(batt_discharge_mwh) as total_discharge
    FROM `{PROJECT_ID}.{DATASET}.site_metered_flows`
    """
    result = client.query(verify_sql).to_dataframe()
    
    print(f'   ✅ Created with {result.iloc[0]["row_count"]:,} rows')
    print(f'   Date range: {result.iloc[0]["earliest"]} to {result.iloc[0]["latest"]}')
    print(f'   Total battery charge: {result.iloc[0]["total_charge"]:.1f} MWh')
    print(f'   Total battery discharge: {result.iloc[0]["total_discharge"]:.1f} MWh')


def create_esoservices_dc_site():
    """Todo #4: Create ESO Dynamic Containment services table"""
    
    print('\n📊 Creating esoservices_dc_site table...')
    
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.esoservices_dc_site` AS
    SELECT
      c.settlementDate,
      c.settlementPeriod,
      
      -- Dynamic Containment availability (2 MW continuous)
      2.0 AS dc_avail_mw,
      
      -- DC availability price (typical £8-10/MW/h, varies by period)
      CASE
        WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 12.0  -- Higher during peak
        WHEN c.settlementPeriod BETWEEN 1 AND 12 THEN 6.0    -- Lower at night
        ELSE 9.0
      END AS dc_price_avail_gbp_per_mw_h,
      
      -- DC utilization (actual MW called, ~10-20% of availability)
      CASE
        WHEN MOD(c.settlementPeriod, 5) = 0 THEN 0.3  -- Occasional utilization
        ELSE 0.0
      END AS dc_util_mwh,
      
      -- DC utilization price (£40-60/MWh when called)
      50.0 AS dc_price_util_gbp_per_mwh
      
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs` c
    WHERE c.settlementDate >= '2025-10-17'
      AND c.settlementDate <= '2025-10-23'
    ORDER BY settlementDate, settlementPeriod
    """
    
    client = bigquery.Client(project=PROJECT_ID)
    job = client.query(sql)
    job.result()
    
    # Verify
    verify_sql = f"""
    SELECT 
      COUNT(*) as row_count,
      SUM(dc_avail_mw * dc_price_avail_gbp_per_mw_h * 0.5) as total_avail_revenue,
      SUM(dc_util_mwh * dc_price_util_gbp_per_mwh) as total_util_revenue
    FROM `{PROJECT_ID}.{DATASET}.esoservices_dc_site`
    """
    result = client.query(verify_sql).to_dataframe()
    
    print(f'   ✅ Created with {result.iloc[0]["row_count"]:,} rows')
    print(f'   Total availability revenue: £{result.iloc[0]["total_avail_revenue"]:,.0f}')
    print(f'   Total utilization revenue: £{result.iloc[0]["total_util_revenue"]:,.0f}')


def create_capacity_market_site():
    """Todo #5: Create Capacity Market pricing table"""
    
    print('\n📊 Creating capacity_market_site table...')
    
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.capacity_market_site` AS
    SELECT
      'VLP_SITE_001' AS site_id,
      15.08 AS cm_price_gbp_per_kw_year,    -- 2026/27 T-4 clearing price
      2400.0 AS derated_kw,                  -- 2.4 MW de-rated (from 2.5 MW)
      4000.0 AS expected_dispatched_mwh_year -- Conservative estimate for 2.5 MW battery
    """
    
    client = bigquery.Client(project=PROJECT_ID)
    job = client.query(sql)
    job.result()
    
    # Verify
    verify_sql = f"""
    SELECT 
      site_id,
      cm_price_gbp_per_kw_year,
      derated_kw,
      (cm_price_gbp_per_kw_year * derated_kw) AS annual_cm_revenue,
      (cm_price_gbp_per_kw_year * derated_kw) / NULLIF(expected_dispatched_mwh_year, 0) AS cm_per_mwh_eq
    FROM `{PROJECT_ID}.{DATASET}.capacity_market_site`
    """
    result = client.query(verify_sql).to_dataframe()
    
    print(f'   ✅ Created for site: {result.iloc[0]["site_id"]}')
    print(f'   Annual CM revenue: £{result.iloc[0]["annual_cm_revenue"]:,.0f}')
    print(f'   CM per MWh equivalent: £{result.iloc[0]["cm_per_mwh_eq"]:.2f}/MWh')


def main():
    print('🚀 CREATING VLP DATA TABLES')
    print('='*60)
    
    try:
        # Todo #3
        create_site_metered_flows()
        
        # Todo #4
        create_esoservices_dc_site()
        
        # Todo #5
        create_capacity_market_site()
        
        print('\n' + '='*60)
        print('✅ ALL TABLES CREATED SUCCESSFULLY')
        print('\n🎯 Ready for Phase 3: Create BigQuery view (Todo #6)')
        
        # Update prerequisites
        with open('vlp_prerequisites.json', 'r') as f:
            config = json.load(f)
        config['tables_created'] = True
        with open('vlp_prerequisites.json', 'w') as f:
            json.dump(config, f, indent=2)
            
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        raise


if __name__ == '__main__':
    main()
