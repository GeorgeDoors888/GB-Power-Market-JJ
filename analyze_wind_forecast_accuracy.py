#!/usr/bin/env python3
"""
GB Wind Forecast Accuracy Analysis
===================================
Analyzes wind generation forecast accuracy using:
- bmrs_windfor/bmrs_windfor_iris: Wind forecasts (hourly)
- bmrs_fuelinst/bmrs_fuelinst_iris: Actual wind generation (30min SP)

Creates marts for:
- wind_forecast_sp: Forecast data aligned to settlement periods
- wind_outturn_sp: Actual wind generation by SP
- wind_forecast_error_sp: Joined with error metrics (MW error, WAPE, MAPE, bias, RMSE)
- wind_forecast_error_daily: Daily rollups

Key Metrics:
- WAPE (Weighted Absolute Percentage Error): SUM(|error|) / SUM(actual) - preferred for power
- MAPE (Mean Absolute Percentage Error): AVG(|error/actual|) - sensitive to low values
- Bias: AVG(forecast - actual) - systematic over/under forecasting
- RMSE: SQRT(AVG(error²)) - penalizes large errors
- Ramp Miss: |forecast_ramp - actual_ramp| where ramp = MW change per 30min
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# BigQuery configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
LOCATION = 'US'

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

def create_wind_forecast_sp_view():
    """
    Create view: wind_forecast_sp
    Converts hourly wind forecasts to settlement period alignment
    """
    logging.info("Creating wind_forecast_sp view...")
    
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.wind_forecast_sp` AS
    WITH combined_forecasts AS (
        -- Historical forecasts (bmrs_windfor)
        SELECT
            dataset,
            TIMESTAMP(publishTime) as publishTime,
            TIMESTAMP(startTime) as startTime,
            generation as forecast_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor`
        WHERE DATE(startTime) < DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        
        UNION ALL
        
        -- Recent forecasts (bmrs_windfor_iris - last 48h)
        SELECT
            dataset,
            TIMESTAMP(publishTime) as publishTime,
            TIMESTAMP(startTime) as startTime,
            generation as forecast_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
        WHERE DATE(startTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    ),
    aligned_to_sp AS (
        SELECT
            DATE(startTime) as settlement_date,
            -- Map hour to settlement periods (2 SPs per hour: hours 0-0.5 = SP1, 0.5-1 = SP2, etc.)
            CASE 
                WHEN EXTRACT(MINUTE FROM startTime) < 30 
                THEN EXTRACT(HOUR FROM startTime) * 2 + 1
                ELSE EXTRACT(HOUR FROM startTime) * 2 + 2
            END as settlement_period,
            startTime as forecast_time,
            publishTime,
            forecast_mw,
            -- Calculate forecast age (how far ahead was it published)
            TIMESTAMP_DIFF(startTime, publishTime, HOUR) as forecast_horizon_hours
        FROM combined_forecasts
        WHERE startTime IS NOT NULL
            AND publishTime IS NOT NULL
            AND forecast_mw IS NOT NULL
    )
    SELECT
        settlement_date,
        settlement_period,
        forecast_time,
        publishTime,
        forecast_mw,
        forecast_horizon_hours,
        -- Take most recent forecast for each SP (closest to delivery)
        ROW_NUMBER() OVER (
            PARTITION BY settlement_date, settlement_period 
            ORDER BY publishTime DESC
        ) as forecast_rank
    FROM aligned_to_sp
    """
    
    job = client.query(query)
    job.result()
    logging.info("✅ Created wind_forecast_sp view")

def create_wind_outturn_sp_view():
    """
    Create view: wind_outturn_sp
    Combines actual wind generation from bmrs_fuelinst (historical + IRIS)
    """
    logging.info("Creating wind_outturn_sp view...")
    
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.wind_outturn_sp` AS
    WITH combined_outturn AS (
        -- Historical actual generation (bmrs_fuelinst)
        SELECT
            CAST(settlementDate AS DATE) as settlement_date,
            settlementPeriod as settlement_period,
            TIMESTAMP(startTime) as startTime,
            generation as actual_mw,
            fuelType
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE fuelType = 'WIND'
            AND CAST(settlementDate AS DATE) < DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        
        UNION ALL
        
        -- Recent actual generation (bmrs_fuelinst_iris - last 48h)
        SELECT
            settlementDate as settlement_date,
            settlementPeriod as settlement_period,
            TIMESTAMP(startTime) as startTime,
            generation as actual_mw,
            fuelType
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE fuelType = 'WIND'
            AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    )
    SELECT
        settlement_date,
        settlement_period,
        startTime as actual_time,
        SUM(actual_mw) as actual_mw_total,  -- Total wind (bmrs_fuelinst already aggregates onshore+offshore)
        SUM(actual_mw) as actual_mw_onshore,  -- Placeholder (not split in this table)
        0.0 as actual_mw_offshore  -- Placeholder (not split in this table)
    FROM combined_outturn
    WHERE actual_mw IS NOT NULL
    GROUP BY settlement_date, settlement_period, startTime
    """
    
    job = client.query(query)
    job.result()
    logging.info("✅ Created wind_outturn_sp view")

def create_wind_forecast_error_sp_view():
    """
    Create view: wind_forecast_error_sp
    Joins forecast and actual, calculates error metrics
    """
    logging.info("Creating wind_forecast_error_sp view...")
    
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp` AS
    WITH forecast_actual_joined AS (
        SELECT
            a.settlement_date,
            a.settlement_period,
            a.actual_mw_total,
            a.actual_mw_onshore,
            a.actual_mw_offshore,
            f.forecast_mw,
            f.forecast_horizon_hours,
            f.publishTime as forecast_publish_time,
            -- Error calculations
            f.forecast_mw - a.actual_mw_total as error_mw,
            ABS(f.forecast_mw - a.actual_mw_total) as abs_error_mw,
            SAFE_DIVIDE(
                ABS(f.forecast_mw - a.actual_mw_total),
                a.actual_mw_total
            ) * 100 as abs_percentage_error,
            -- Ramp calculations (change from previous SP)
            a.actual_mw_total - LAG(a.actual_mw_total) OVER (
                ORDER BY a.settlement_date, a.settlement_period
            ) as actual_ramp_mw,
            f.forecast_mw - LAG(f.forecast_mw) OVER (
                ORDER BY a.settlement_date, a.settlement_period
            ) as forecast_ramp_mw
        FROM `{PROJECT_ID}.{DATASET}.wind_outturn_sp` a
        INNER JOIN `{PROJECT_ID}.{DATASET}.wind_forecast_sp` f
            ON a.settlement_date = f.settlement_date
            AND a.settlement_period = f.settlement_period
            AND f.forecast_rank = 1  -- Use most recent forecast
        WHERE a.actual_mw_total > 0  -- Avoid division by zero in MAPE
    )
    SELECT
        *,
        -- Ramp miss (how badly did we miss the MW change)
        ABS(forecast_ramp_mw - actual_ramp_mw) as ramp_miss_mw,
        -- Flag large ramp misses (>500 MW/30min error)
        CASE 
            WHEN ABS(forecast_ramp_mw - actual_ramp_mw) > 500 THEN 1 
            ELSE 0 
        END as large_ramp_miss_flag,
        -- Hour of day (for pattern analysis)
        EXTRACT(HOUR FROM TIMESTAMP(settlement_date) + INTERVAL (settlement_period - 1) * 30 MINUTE) as hour_of_day,
        -- Day of week (1 = Sunday)
        EXTRACT(DAYOFWEEK FROM settlement_date) as day_of_week
    FROM forecast_actual_joined
    """
    
    job = client.query(query)
    job.result()
    logging.info("✅ Created wind_forecast_error_sp view")

def create_wind_forecast_error_daily_view():
    """
    Create view: wind_forecast_error_daily
    Daily rollups of forecast error metrics
    """
    logging.info("Creating wind_forecast_error_daily view...")
    
    query = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.wind_forecast_error_daily` AS
    SELECT
        settlement_date,
        COUNT(*) as num_periods,
        -- Central tendency
        AVG(actual_mw_total) as avg_actual_mw,
        AVG(forecast_mw) as avg_forecast_mw,
        -- Error metrics
        AVG(error_mw) as bias_mw,  -- Systematic over/under forecasting
        AVG(abs_error_mw) as mae_mw,  -- Mean Absolute Error
        SQRT(AVG(POW(error_mw, 2))) as rmse_mw,  -- Root Mean Squared Error
        -- WAPE (preferred): weighted absolute percentage error
        SAFE_DIVIDE(
            SUM(abs_error_mw),
            SUM(actual_mw_total)
        ) * 100 as wape_percent,
        -- MAPE (can be distorted by low values)
        AVG(abs_percentage_error) as mape_percent,
        -- Ramp metrics
        AVG(ABS(actual_ramp_mw)) as avg_actual_ramp_mw,
        AVG(ABS(forecast_ramp_mw)) as avg_forecast_ramp_mw,
        AVG(ramp_miss_mw) as avg_ramp_miss_mw,
        MAX(ramp_miss_mw) as max_ramp_miss_mw,
        SUM(large_ramp_miss_flag) as num_large_ramp_misses,
        -- Range
        MIN(actual_mw_total) as min_actual_mw,
        MAX(actual_mw_total) as max_actual_mw,
        MIN(forecast_mw) as min_forecast_mw,
        MAX(forecast_mw) as max_forecast_mw
    FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp`
    GROUP BY settlement_date
    ORDER BY settlement_date DESC
    """
    
    job = client.query(query)
    job.result()
    logging.info("✅ Created wind_forecast_error_daily view")

def get_latest_forecast_metrics(days=90):
    """
    Fetch latest forecast accuracy metrics for dashboard
    
    Args:
        days: Number of days to retrieve
        
    Returns:
        DataFrame with daily metrics
    """
    logging.info(f"Fetching last {days} days of forecast metrics...")
    
    query = f"""
    SELECT
        settlement_date,
        num_periods,
        avg_actual_mw,
        avg_forecast_mw,
        bias_mw,
        mae_mw,
        rmse_mw,
        wape_percent,
        mape_percent,
        avg_ramp_miss_mw,
        max_ramp_miss_mw,
        num_large_ramp_misses
    FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_daily`
    WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlement_date DESC
    """
    
    df = client.query(query).to_dataframe()
    logging.info(f"✅ Retrieved {len(df)} days of metrics")
    return df

def get_intraday_forecast_comparison(date=None):
    """
    Fetch last 48 settlement periods of actual vs forecast for intraday chart
    
    Args:
        date: Date to retrieve (defaults to yesterday)
        
    Returns:
        DataFrame with SP-level comparison
    """
    if date is None:
        date = datetime.now().date() - timedelta(days=1)
    
    logging.info(f"Fetching intraday comparison for {date}...")
    
    query = f"""
    SELECT
        settlement_date,
        settlement_period,
        actual_mw_total,
        forecast_mw,
        error_mw,
        abs_error_mw,
        abs_percentage_error,
        actual_ramp_mw,
        forecast_ramp_mw,
        ramp_miss_mw
    FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp`
    WHERE settlement_date = '{date}'
    ORDER BY settlement_period
    """
    
    df = client.query(query).to_dataframe()
    logging.info(f"✅ Retrieved {len(df)} settlement periods")
    return df

def get_hour_of_day_error_pattern():
    """
    Analyze forecast error patterns by hour of day (last 30 days)
    
    Returns:
        DataFrame with error metrics by hour
    """
    logging.info("Analyzing hour-of-day error patterns...")
    
    query = f"""
    SELECT
        hour_of_day,
        COUNT(*) as num_periods,
        AVG(abs_error_mw) as avg_abs_error_mw,
        AVG(abs_percentage_error) as avg_abs_pct_error,
        AVG(error_mw) as avg_bias_mw,
        APPROX_QUANTILES(abs_error_mw, 100)[OFFSET(50)] as median_abs_error_mw,
        APPROX_QUANTILES(abs_error_mw, 100)[OFFSET(90)] as p90_abs_error_mw
    FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp`
    WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY hour_of_day
    ORDER BY hour_of_day
    """
    
    df = client.query(query).to_dataframe()
    logging.info(f"✅ Retrieved error patterns for {len(df)} hours")
    return df

def main():
    """
    Main execution: Create all views and sample analysis
    """
    logging.info("Starting wind forecast accuracy analysis setup...")
    
    try:
        # Create core views
        create_wind_forecast_sp_view()
        create_wind_outturn_sp_view()
        create_wind_forecast_error_sp_view()
        create_wind_forecast_error_daily_view()
        
        # Sample analysis
        logging.info("\n=== Sample Analysis ===")
        
        # Daily metrics (last 7 days)
        daily_metrics = get_latest_forecast_metrics(days=7)
        print("\nLast 7 Days Forecast Accuracy:")
        print(daily_metrics[['settlement_date', 'wape_percent', 'bias_mw', 'rmse_mw', 'num_large_ramp_misses']].to_string(index=False))
        
        # Hour-of-day patterns
        hourly_pattern = get_hour_of_day_error_pattern()
        print("\nError Pattern by Hour of Day:")
        print(hourly_pattern[['hour_of_day', 'avg_abs_error_mw', 'avg_bias_mw']].to_string(index=False))
        
        logging.info("\n✅ Wind forecast analysis setup complete!")
        logging.info("\nCreated views:")
        logging.info("  - wind_forecast_sp (forecast data by SP)")
        logging.info("  - wind_outturn_sp (actual generation by SP)")
        logging.info("  - wind_forecast_error_sp (joined with error metrics)")
        logging.info("  - wind_forecast_error_daily (daily rollups)")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
