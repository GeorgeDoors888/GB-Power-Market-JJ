#!/usr/bin/env python3
"""
Update Data_Hidden rows 27-32 ONLY
Populates MID_Price, Sys_Buy, Sys_Sell, and spreads for sparkline bar charts
"""

import sys
import logging
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
from fast_sheets import FastSheets

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = 'inner-cinema-credentials.json'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_bm_kpi_data(bq_client, cache=None):
    """
    Get comprehensive BM market KPIs from multiple sources
    Returns timeseries data for all 6 sparkline metrics
    WITH CACHING: 60s TTL for BigQuery results
    """

    # Check cache first
    cache_key = f"bq:bm_kpi_data:{datetime.now().strftime('%Y-%m-%d_%H:%M')}"  # Cache per minute
    if cache:
        cached = cache.get_cached_data(cache_key)
        if cached is not None:
            logging.info("✅ Using cached BigQuery results (instant!)")
            return cached

    # Use TODAY'S data (even if partial) - sparklines update throughout the day
    date_query = f"""
    SELECT CURRENT_DATE() as date
    """

    date_result = bq_client.query(date_query).to_dataframe()
    if date_result.empty:
        logging.warning("No complete BOALF data found")
        return None

    target_date = str(date_result.iloc[0]['date'])
    logging.info(f"📅 Using data from: {target_date}")

    # Query comprehensive BM + Market data for all KPIs
    query = f"""
    WITH periods AS (
      SELECT settlementPeriod
      FROM UNNEST(GENERATE_ARRAY(1, 48)) AS settlementPeriod
    ),
    boalf_data AS (
      SELECT
        settlementPeriod,
        AVG(acceptancePrice) as bm_avg_price,
        SUM(acceptancePrice * ABS(acceptanceVolume)) / NULLIF(SUM(ABS(acceptanceVolume)), 0) as bm_vol_wtd,
        SUM(ABS(acceptanceVolume)) as bm_volume
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{target_date}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
      GROUP BY settlementPeriod
    ),
    market_index AS (
      SELECT
        settlementPeriod,
        AVG(price) as mid_price
      FROM (
        SELECT settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE CAST(settlementDate AS DATE) = '{target_date}'
          AND price > 0  -- Filter zero prices
        UNION ALL
        SELECT settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = '{target_date}'
          AND price > 0  -- Filter zero prices
      )
      GROUP BY settlementPeriod
    ),
    system_prices AS (
      SELECT
        settlementPeriod,
        AVG(systemBuyPrice) as sys_buy,
        AVG(systemSellPrice) as sys_sell
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) = '{target_date}'
      GROUP BY settlementPeriod
    ),
    vlp_revenue AS (
      SELECT
        settlementPeriod,
        SUM(ABS(acceptanceVolume) * ABS(COALESCE(acceptancePrice, 0))) / 1000 as vlp_rev_gbp_k
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{target_date}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
      GROUP BY settlementPeriod
    )
    SELECT
      p.settlementPeriod,
      COALESCE(b.bm_avg_price, 0) as bm_avg_price,
      COALESCE(b.bm_vol_wtd, 0) as bm_vol_wtd,
      COALESCE(b.bm_volume, 0) as bm_volume,
      COALESCE(m.mid_price, 0) as mid_price,
      COALESCE(s.sys_buy, 0) as sys_buy,
      COALESCE(s.sys_sell, 0) as sys_sell,
      COALESCE((m.mid_price - s.sys_buy), 0) as daily_comp,
      COALESCE(v.vlp_rev_gbp_k, 0) as vlp_rev,
      COALESCE((m.mid_price / NULLIF(s.sys_buy, 0) - 1) * 100, 0) as contango
    FROM periods p
    LEFT JOIN boalf_data b USING (settlementPeriod)
    LEFT JOIN market_index m USING (settlementPeriod)
    LEFT JOIN system_prices s USING (settlementPeriod)
    LEFT JOIN vlp_revenue v USING (settlementPeriod)
    ORDER BY p.settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()

        if df.empty:
            return None

        # Count actual periods with data
        periods_with_data = (df['bm_avg_price'] > 0).sum()

        logging.info(f"📊 Retrieved {len(df)} settlement periods ({periods_with_data} with BM data)")

        result = {
            'date': target_date,
            'period_count': periods_with_data,
            'timeseries': df
        }

        # Cache result for 60 seconds
        if cache:
            cache.cache_data(cache_key, result, ttl=60)
            logging.info("💾 Cached BigQuery results (60s TTL)")

        return result
    except Exception as e:
        logging.error(f"Error querying BM KPI data: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("⚡ UPDATE DATA_HIDDEN - SPARKLINE DATA POPULATOR")
    print("="*80 + "\n")

    # Connect to Google Sheets (using FastSheets with 4-layer caching!)
    print("\n🔧 Connecting to Google Sheets (FastSheets with caching)...")
    sheets = FastSheets(SA_FILE, use_cache=True)
    print("✅ Google Sheets connected with caching enabled\n")

    # Get cache manager for BigQuery result caching
    cache = sheets.cache if sheets.cache else None

    # Connect to BigQuery
    print("🔧 Connecting to BigQuery...")
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')
    print("✅ BigQuery connected\n")

    # Get data (with caching!)
    print("📊 Fetching BM + Market data from BigQuery...")
    kpi_data = get_bm_kpi_data(bq_client, cache=cache)

    if not kpi_data:
        print("❌ No data available")
        sys.exit(1)

    # Prepare timeseries for Data_Hidden (48 periods)
    period_stats = kpi_data['timeseries']

    # Calculate derived metrics
    bm_mid_spread = period_stats['bm_avg_price'] - period_stats['mid_price']
    bm_sysbuy_spread = period_stats['bm_avg_price'] - period_stats['sys_buy']
    bm_syssell_spread = period_stats['bm_avg_price'] - period_stats['sys_sell']

    # Build data rows (row label + 48 period values)
    data_rows = [
        ['BM_Avg_Price'] + period_stats['bm_avg_price'].tolist(),      # Row 27 ✅
        ['BM_Vol_Wtd'] + period_stats['bm_vol_wtd'].tolist(),          # Row 28 ✅
        ['MID_Price'] + period_stats['mid_price'].tolist(),             # Row 29 ✨
        ['Sys_Buy'] + period_stats['sys_buy'].tolist(),                 # Row 30 ✨
        ['Sys_Sell'] + period_stats['sys_sell'].tolist(),               # Row 31 ✨
        ['BM_MID_Spread'] + bm_mid_spread.tolist(),                     # Row 32 ✨
        ['BM_SysBuy'] + bm_sysbuy_spread.tolist(),                      # Row 33
        ['BM_SysSell'] + bm_syssell_spread.tolist(),                    # Row 34
        ['Daily_Comp'] + period_stats['daily_comp'].tolist(),           # Row 35 🆕
        ['VLP_Rev'] + period_stats['vlp_rev'].tolist(),                 # Row 36 🆕
        ['Contango'] + period_stats['contango'].tolist(),               # Row 37 🆕
    ]

    # Show data preview
    print("📋 Data Preview (first 5 settlement periods):")
    print(f"   BM Avg Price:  {period_stats['bm_avg_price'].head().tolist()}")
    print(f"   BM Vol Wtd:    {period_stats['bm_vol_wtd'].head().tolist()}")
    print(f"   MID Price:     {period_stats['mid_price'].head().tolist()}")
    print(f"   Sys Buy:       {period_stats['sys_buy'].head().tolist()}")
    print(f"   Sys Sell:      {period_stats['sys_sell'].head().tolist()}")
    print(f"   BM-MID Spread: {bm_mid_spread.head().tolist()}")
    print(f"   Daily Comp:    {period_stats['daily_comp'].head().tolist()}")
    print(f"   VLP Rev:       {period_stats['vlp_rev'].head().tolist()}")
    print(f"   Contango:      {period_stats['contango'].head().tolist()}")

    # Write to Data_Hidden (queued for batch processing)
    print("\n📝 Writing to Data_Hidden rows 27-37 (batch queued)...")
    try:
        sheets.batch_update(SPREADSHEET_ID, [
            {
                'range': 'Data_Hidden!A27:AW37',  # Extended to row 37 for new metrics
                'values': data_rows
            }
        ], queue=True, flush_now=True)  # Queue and flush immediately

        print("✅ SUCCESS! Written 11 metric rows × 48 periods = 528 data points")
        print(f"   Date: {kpi_data['date']}")
        print(f"   Periods with BM data: {kpi_data['period_count']}/48")
        print("\n🎉 All 9 sparkline metrics updated (including Daily Comp, VLP Rev, Contango)!")

        # Show cache stats
        if sheets.cache:
            stats = sheets.get_cache_stats()
            print(f"\n📊 Cache Stats: {stats['request_counts'][0]}/{stats.get('requests_per_minute', 55)} API requests used")
    except Exception as e:
        print(f"❌ Error updating Data_Hidden: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
