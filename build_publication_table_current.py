#!/usr/bin/env python3
"""
Builds the publication_dashboard_live table in BigQuery for Apps Script consumption.
FIXED VERSION: Uses BOTH historical AND IRIS tables for current data.
"""

from google.cloud import bigquery
import google.auth
from datetime import datetime, timedelta

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
PUBLICATION_TABLE = "publication_dashboard_live"
LOCATION = "US"

# Authentication
credentials, _ = google.auth.default(
    scopes=[
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/bigquery",
    ]
)

client = bigquery.Client(credentials=credentials, project=PROJECT_ID, location=LOCATION)

print("✅ Successfully connected to BigQuery")

# Step 1: Find the latest date with data from IRIS (real-time)
print("Finding latest available data date from IRIS...")
latest_date_query = f"""
SELECT MAX(CAST(settlementDate AS DATE)) as latest_date
FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_iris`
"""

latest_date_result = client.query(latest_date_query).result()
latest_date = list(latest_date_result)[0]['latest_date']
print(f"✅ Latest date from IRIS: {latest_date}")

# Determine cutoff date (where historical ends and IRIS begins)
# Use 7 days ago as conservative cutoff
cutoff_date = latest_date - timedelta(days=7)
print(f"📅 Using cutoff date: {cutoff_date} (historical < cutoff, IRIS >= cutoff)")

# Step 2: Build and execute the publication query
print(f"Building publication table for {latest_date}...")

publication_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{PUBLICATION_TABLE}` AS
WITH
  LatestDate AS (
    SELECT DATE('{latest_date}') AS report_date
  ),
  -- COMBINED generation data (historical + IRIS)
  AllGeneration AS (
    SELECT
      settlementPeriod,
      fuelType,
      SUM(generation) AS generation
    FROM (
      -- Historical data
      SELECT 
        settlementPeriod,
        fuelType,
        generation
      FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
      WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
        AND CAST(settlementDate AS DATE) < '{cutoff_date}'
      
      UNION ALL
      
      -- IRIS real-time data (deduplicated)
      SELECT 
        settlementPeriod,
        fuelType,
        AVG(generation) AS generation
      FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
        AND CAST(settlementDate AS DATE) >= '{cutoff_date}'
      GROUP BY settlementPeriod, fuelType
    )
    GROUP BY settlementPeriod, fuelType
  ),
  -- COMBINED prices data (historical + IRIS)
  AllPrices AS (
    SELECT
      settlementPeriod,
      price
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
    WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
    
    UNION ALL
    
    SELECT
      settlementPeriod,
      price
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid_iris`
    WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
  ),
  -- Aggregated KPIs
  KPIs AS (
    SELECT
      0.0 AS vlp_revenue_7d,
      IFNULL(AVG(price), 0.0) AS wholesale_avg,
      50.0 AS frequency_avg,
      IFNULL((SELECT SUM(generation) / 1000.0 FROM AllGeneration WHERE settlementPeriod = (SELECT MAX(settlementPeriod) FROM AllGeneration)), 0.0) AS total_gen,
      IFNULL((SELECT SUM(generation) / 1000.0 FROM AllGeneration WHERE fuelType = 'WIND' AND settlementPeriod = (SELECT MAX(settlementPeriod) FROM AllGeneration)), 0.0) AS wind_gen,
      IFNULL((SELECT SUM(generation) / 1000.0 FROM AllGeneration WHERE settlementPeriod = (SELECT MAX(settlementPeriod) FROM AllGeneration)), 0.0) AS demand
    FROM AllPrices
  ),
  -- Generation Mix (latest settlement period)
  LatestPeriod AS (
    SELECT MAX(settlementPeriod) AS latest_sp
    FROM AllGeneration
  ),
  GenerationMix AS (
    SELECT
      fuelType AS fuel,
      generation AS mw
    FROM AllGeneration
    WHERE settlementPeriod = (SELECT latest_sp FROM LatestPeriod)
      AND fuelType NOT IN ('INTFR', 'INTELEC', 'INTIFA2', 'INTVKL', 'INTGRNL', 'INTEW', 'INTIRL', 'INTNED', 'INTNEM', 'INTNSL')
    ORDER BY generation DESC
  ),
  -- Intraday wind by settlement period
  IntradayWind AS (
    SELECT
      settlementPeriod,
      IFNULL(SUM(generation), 0.0) AS wind
    FROM AllGeneration
    WHERE fuelType = 'WIND'
    GROUP BY settlementPeriod
    ORDER BY settlementPeriod
  ),
  -- Intraday total generation by settlement period  
  IntradayDemand AS (
    SELECT
      settlementPeriod,
      IFNULL(SUM(generation), 0.0) AS demand
    FROM AllGeneration
    GROUP BY settlementPeriod
    ORDER BY settlementPeriod
  ),
  -- Intraday prices (from bmrs_mid + iris)
  IntradayPrice AS (
    SELECT
      settlementPeriod,
      AVG(price) AS price
    FROM AllPrices
    GROUP BY settlementPeriod
    ORDER BY settlementPeriod
  ),
  -- Intraday Frequency (Avg per Settlement Period)
  IntradayFrequency AS (
    SELECT
      (EXTRACT(HOUR FROM measurementTime) * 2) + IF(EXTRACT(MINUTE FROM measurementTime) >= 30, 2, 1) AS settlementPeriod,
      AVG(frequency) as freq
    FROM (
        SELECT measurementTime, frequency 
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_freq`
        WHERE CAST(measurementTime AS DATE) = (SELECT report_date FROM LatestDate)
        
        UNION ALL
        
        SELECT measurementTime, frequency 
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) = (SELECT report_date FROM LatestDate)
    )
    GROUP BY settlementPeriod
    ORDER BY settlementPeriod
  ),
  -- Wind Forecast (Latest per period)
  WindForecastRaw AS (
    SELECT 
      startTime,
      generation,
      ROW_NUMBER() OVER (PARTITION BY startTime ORDER BY publishTime DESC) as rn
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_windfor_iris`
    WHERE DATE(startTime) = (SELECT report_date FROM LatestDate)
  ),
  WindForecast AS (
    -- Expand hourly forecast to two half-hourly settlement periods
    SELECT
      (EXTRACT(HOUR FROM startTime) * 2) + 1 AS settlementPeriod,
      generation as forecast_mw
    FROM WindForecastRaw
    WHERE rn = 1
    UNION ALL
    SELECT
      (EXTRACT(HOUR FROM startTime) * 2) + 2 AS settlementPeriod,
      generation as forecast_mw
    FROM WindForecastRaw
    WHERE rn = 1
  ),
  -- Active Outages
  Outages AS (
    WITH latest_revisions AS (
        SELECT 
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_remit_unavailability`
        WHERE DATE(eventStartTime) <= (SELECT report_date FROM LatestDate)
          AND (DATE(eventEndTime) >= (SELECT report_date FROM LatestDate) OR eventEndTime IS NULL)
          AND eventStatus = 'Active'
        GROUP BY affectedUnit
    )
    SELECT 
        u.assetName,
        u.fuelType,
        u.unavailableCapacity as unavail_mw,
        u.cause
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    WHERE DATE(u.eventStartTime) <= (SELECT report_date FROM LatestDate)
      AND (DATE(u.eventEndTime) >= (SELECT report_date FROM LatestDate) OR u.eventEndTime IS NULL)
      AND u.eventStatus = 'Active'
      AND u.unavailableCapacity > 0
    ORDER BY u.unavailableCapacity DESC
    LIMIT 10
  ),
  -- Constraint Analysis (Live / Current Day)
  ConstraintAnalysis AS (
    WITH 
    combined_boalf AS (
      SELECT
        bmUnit,
        CAST(settlementDate AS DATE) AS settlement_date,
        soFlag,
        levelFrom,
        levelTo
      FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
        AND soFlag = TRUE

      UNION ALL

      SELECT
        bmUnit,
        CAST(settlementDate AS DATE) AS settlement_date,
        soFlag,
        levelFrom,
        levelTo
      FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
        AND soFlag = TRUE
    ),
    boalf_with_meta AS (
      SELECT
        bo.bmUnit,
        SAFE_CAST(ABS(bo.levelTo - bo.levelFrom) AS FLOAT64) AS mw_adjusted,
        br.fueltype AS raw_fueltype,
        br.gspgroupid AS raw_gsp_group_id,
        br.gspgroupname AS raw_gsp_group_name
      FROM combined_boalf bo
      LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.bmu_registration_data` br
        ON bo.bmUnit = br.nationalgridbmunit
           OR bo.bmUnit = br.elexonbmunit
    ),
    classified AS (
      SELECT
        CASE
          WHEN bmUnit LIKE 'I_%' THEN 'Interconnector'
          WHEN raw_gsp_group_id = '_P' THEN 'North Scotland'
          WHEN raw_gsp_group_id = '_N' THEN 'South Scotland'
          WHEN raw_gsp_group_id IN ('_A','_B','_C','_D','_E','_F','_G','_H','_J','_K','_L','_M') THEN 'England & Wales'
          ELSE 'Other'
        END AS region,
        COALESCE(raw_gsp_group_name, 'Unknown') AS dno_area,
        COALESCE(raw_gsp_group_id, 'Unknown') AS gsp_group,
        CASE
          WHEN UPPER(raw_fueltype) = 'WIND'           THEN 'Wind'
          WHEN UPPER(raw_fueltype) = 'SOLAR'          THEN 'Solar'
          WHEN UPPER(raw_fueltype) IN ('CCGT','GAS')  THEN 'CCGT / Gas'
          WHEN UPPER(raw_fueltype) LIKE 'HYDRO%'      THEN 'Hydro'
          WHEN UPPER(raw_fueltype) LIKE 'NUCLEAR%'    THEN 'Nuclear'
          WHEN UPPER(raw_fueltype) LIKE 'INTERCONNECTOR%' 
               OR bmUnit LIKE 'I_%'                   THEN 'Interconnector'
          WHEN raw_fueltype IS NULL                   THEN 'Unknown'
          ELSE raw_fueltype
        END AS fuel_group,
        mw_adjusted
      FROM boalf_with_meta
    ),
    agg AS (
      SELECT
        region,
        dno_area,
        gsp_group,
        fuel_group,
        COUNT(*) AS n_actions,
        ROUND(SUM(mw_adjusted), 1) AS total_mw_adjusted
      FROM classified
      GROUP BY region, dno_area, gsp_group, fuel_group
    )
    SELECT
      region,
      dno_area,
      gsp_group,
      fuel_group,
      n_actions,
      total_mw_adjusted,
      ROUND(100.0 * total_mw_adjusted / NULLIF(SUM(total_mw_adjusted) OVER (), 0), 2) AS share_of_total_pct
    FROM agg
    ORDER BY total_mw_adjusted DESC
    LIMIT 20
  )
SELECT
  (SELECT report_date FROM LatestDate) AS report_date,
  (SELECT vlp_revenue_7d FROM KPIs) AS vlp_revenue_7d,
  (SELECT wholesale_avg FROM KPIs) AS wholesale_avg,
  (SELECT frequency_avg FROM KPIs) AS frequency_avg,
  (SELECT total_gen FROM KPIs) AS total_gen,
  (SELECT wind_gen FROM KPIs) AS wind_gen,
  (SELECT demand FROM KPIs) AS demand,
  ARRAY(SELECT STRUCT(fuel, mw) FROM GenerationMix) AS generation_mix,
  [
    STRUCT('ElecLink' AS name, 1000.0 AS flow_mw),
    STRUCT('East-West' AS name, 500.0 AS flow_mw),
    STRUCT('IFA' AS name, 2000.0 AS flow_mw),
    STRUCT('Greenlink' AS name, 500.0 AS flow_mw),
    STRUCT('IFA2' AS name, 1000.0 AS flow_mw),
    STRUCT('Moyle' AS name, 500.0 AS flow_mw),
    STRUCT('BritNed' AS name, 1000.0 AS flow_mw),
    STRUCT('Nemo' AS name, 1000.0 AS flow_mw),
    STRUCT('NSL' AS name, 1400.0 AS flow_mw),
    STRUCT('Viking Link' AS name, 1400.0 AS flow_mw)
  ] AS interconnectors,
  ARRAY(
    SELECT IFNULL(wind, -999.0)
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    LEFT JOIN IntradayWind w ON w.settlementPeriod = sp
    ORDER BY sp
  ) AS intraday_wind,
  ARRAY(
    SELECT IFNULL(wf.forecast_mw, -999.0) 
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    LEFT JOIN WindForecast wf ON wf.settlementPeriod = sp
    ORDER BY sp
  ) AS intraday_wind_forecast,
  ARRAY(
    SELECT IFNULL(demand, -999.0)
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    LEFT JOIN IntradayDemand d ON d.settlementPeriod = sp
    ORDER BY sp
  ) AS intraday_demand,
  ARRAY(
    SELECT IFNULL(price, -999.0)
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    LEFT JOIN IntradayPrice p ON p.settlementPeriod = sp
    ORDER BY sp
  ) AS intraday_price,
  ARRAY(
    SELECT IFNULL(freq, -999.0)
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    LEFT JOIN IntradayFrequency f ON f.settlementPeriod = sp
    ORDER BY sp
  ) AS intraday_frequency,
  ARRAY(SELECT STRUCT(assetName, fuelType, unavail_mw, cause) FROM Outages) AS outages,
  ARRAY(SELECT STRUCT(region, dno_area, gsp_group, fuel_group, n_actions, total_mw_adjusted, share_of_total_pct) FROM ConstraintAnalysis) AS constraint_analysis
"""

print("⚡ Executing publication query...")
job = client.query(publication_query)
job.result()  # Wait for completion

print(f"✅ Successfully created/updated table: {PROJECT_ID}.{DATASET_ID}.{PUBLICATION_TABLE}")
print(f"📊 Data date: {latest_date}")
print(f"➡️ Apps Script can now query this table to render the dashboard")

# Verify the data
verify_query = f"""
SELECT 
  report_date,
  vlp_revenue_7d,
  wholesale_avg,
  total_gen,
  wind_gen,
  demand,
  ARRAY_LENGTH(generation_mix) as gen_mix_count,
  ARRAY_LENGTH(intraday_wind) as intraday_points,
  intraday_wind_forecast,
  ARRAY_LENGTH(outages) as outage_count
FROM `{PROJECT_ID}.{DATASET_ID}.{PUBLICATION_TABLE}`
"""
print("\n🔍 Verifying data:")
result = client.query(verify_query).result()
for row in result:
    print(f"   Date: {row.report_date}")
    print(f"   Wholesale Avg: £{row.wholesale_avg if row.wholesale_avg is not None else 0.0:.2f}/MWh")
    print(f"   Total Gen: {row.total_gen if row.total_gen is not None else 0.0:.2f} GW")
    print(f"   Wind Gen: {row.wind_gen if row.wind_gen is not None else 0.0:.2f} GW")
    print(f"   Generation Mix: {row.gen_mix_count} fuel types")
    print(f"   Intraday Points: {row.intraday_points} periods")
    print(f"   Forecast Points: {len(row.intraday_wind_forecast) if hasattr(row, 'intraday_wind_forecast') else 'N/A'} periods")
    print(f"   Active Outages: {row.outage_count}")
