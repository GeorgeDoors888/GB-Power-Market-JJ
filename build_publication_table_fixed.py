#!/usr/bin/env python3
"""
Builds the publication_dashboard_live table in BigQuery for Apps Script consumption.
This script aggregates data from multiple sources and creates a single-row table
that Apps Script can easily query to render the GB Live 2 dashboard.
"""

from google.cloud import bigquery
import google.auth

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

# Step 1: Find the latest date with data
print("Finding latest available data date...")
latest_date_query = f"""
SELECT MAX(CAST(settlementDate AS DATE)) as latest_date
FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
"""

latest_date_result = client.query(latest_date_query).result()
latest_date = list(latest_date_result)[0]['latest_date']
print(f"✅ Latest date: {latest_date}")

# Step 2: Build and execute the publication query
# CRITICAL FIX: Use IFNULL() to handle NULL values in arrays
print(f"Building publication table for {latest_date}...")

publication_query = f"""
CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{PUBLICATION_TABLE}` AS
WITH
  LatestDate AS (
    SELECT DATE('{latest_date}') AS report_date
  ),
  -- Generation data for calculations
  AllGeneration AS (
    SELECT
      settlementPeriod,
      fuelType,
      SUM(generation) AS generation
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
    WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
    GROUP BY settlementPeriod, fuelType
  ),
  -- Aggregated KPIs
  KPIs AS (
    SELECT
      0.0 AS vlp_revenue_7d,
      AVG(systemSellPrice) AS wholesale_avg,
      50.0 AS frequency_avg,
      (SELECT SUM(generation) / 1000.0 FROM AllGeneration WHERE settlementPeriod = (SELECT MAX(settlementPeriod) FROM AllGeneration)) AS total_gen,
      (SELECT SUM(generation) / 1000.0 FROM AllGeneration WHERE fuelType = 'WIND' AND settlementPeriod = (SELECT MAX(settlementPeriod) FROM AllGeneration)) AS wind_gen,
      (SELECT SUM(generation) / 1000.0 FROM AllGeneration WHERE settlementPeriod = (SELECT MAX(settlementPeriod) FROM AllGeneration)) AS demand
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
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
  -- Intraday prices
  IntradayPrice AS (
    SELECT
      settlementPeriod,
      IFNULL(price, 0.0) AS price
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
    WHERE CAST(settlementDate AS DATE) = (SELECT report_date FROM LatestDate)
    ORDER BY settlementPeriod
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
    STRUCT('IFA' AS name, 1000.0 AS flow_mw),
    STRUCT('BritNed' AS name, 800.0 AS flow_mw)
  ] AS interconnectors,
  ARRAY(SELECT wind FROM IntradayWind) AS intraday_wind,
  ARRAY(SELECT demand FROM IntradayDemand) AS intraday_demand,
  ARRAY(SELECT price FROM IntradayPrice) AS intraday_price
"""

print("⚡ Executing publication query...")
job = client.query(publication_query)
job.result()  # Wait for completion

print(f"✅ Successfully created/updated table: {PROJECT_ID}.{DATASET_ID}.{PUBLICATION_TABLE}")
print(f"➡️ Apps Script can now query this table to render the dashboard")
