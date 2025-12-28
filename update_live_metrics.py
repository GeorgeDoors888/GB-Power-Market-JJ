#!/usr/bin/env python3
"""
Unified Dashboard Updater - All Live Dashboard Updates
Runs twice per hour at :16 and :46 (after settlement data available)
Updates:
- Data_Hidden: Fuel generation, interconnectors, market metrics (48 periods)
- Live Dashboard v2: IRIS freshness, KPIs, market metrics (L14-L18), spreads (O14-O18)
"""

import sys
import socket
import logging
import pandas as pd
import pytz
from datetime import datetime, timedelta
from google.cloud import bigquery
from cache_manager import CacheManager
import gspread
from google.oauth2.service_account import Credentials
# from unicode_sparkline import generate_unicode_sparkline # Deprecated

# --- New Sparkline Generation ---
SPARKLINE_COLORS = {
    # Fuel Types
    'WIND': "#00A86B",      # Emerald Green
    'NUCLEAR': "#FFD700",   # Gold
    'CCGT': "#FF6347",      # Tomato Red
    'BIOMASS': "#228B22",   # Forest Green
    'NPSHYD': "#4682B4",    # Steel Blue
    'OTHER': "#D3D3D3",     # Light Grey
    'OCGT': "#FFA500",      # Orange
    'COAL': "#555555",      # Dark Grey
    'OIL': "#8B4513",       # Saddle Brown
    'PS': "#8A2BE2",        # Blue Violet (Pumped Storage)
    # Interconnectors
    '🇫🇷 ElecLink': "#0055A4",
    '🇮🇪 East-West': "#169B62",
    '🇫🇷 IFA': "#0055A4",
    '🇮🇪 Greenlink': "#169B62",
    '🇫🇷 IFA2': "#0055A4",
    '🇮🇪 Moyle': "#169B62",
    '🇳🇱 BritNed': "#AE1C28",
    '🇧🇪 Nemo': "#FFD100",
    '🇳🇴 NSL': "#EF2B2D",
    '🇩🇰 Viking Link': "#C8102E",
    # KPIs
    'Wholesale Price': "#DA70D6", # Orchid
    'Frequency': "#6495ED",      # Cornflower Blue
    'Total Generation': "#32CD32", # Lime Green
    'Wind Output': "#00A86B",      # Emerald Green
    'System Demand': "#FF4500",     # Orange Red
}

def generate_gs_sparkline_formula(data, options, add_spacing=True):
    """
    Generates a native Google Sheets =SPARKLINE() formula with correctly formatted options.
    Shows only current settlement periods (1 to current), not padded to 48.
    This is the VERIFIED working version from test_sparkline_formula.py

    Args:
        data: List of numeric values
        options: Dict of sparkline options (charttype, color, etc.)
        add_spacing: If True, adds 2 spaces (0 values) between each data point for better visibility
                     Note: Spacing is automatically disabled for line charts (looks choppy)
    """
    # Ensure data is a list of numbers, handle potential None or non-numeric values
    clean_data = [item if isinstance(item, (int, float)) else 0 for item in data]

    # Disable spacing for line charts (makes them look broken/choppy)
    charttype = options.get('charttype', 'column')
    if charttype == 'line':
        add_spacing = False

    # Add 2 spaces between each data point for better bar/column visibility
    if add_spacing and len(clean_data) > 1:
        spaced_data = []
        for val in clean_data:
            spaced_data.append(val)
            spaced_data.append(0)  # Space 1
            spaced_data.append(0)  # Space 2
        # Remove trailing spaces
        clean_data = spaced_data[:-2] if len(spaced_data) > 2 else spaced_data

    # Build the options string: {"option1","value1";"option2","value2"}
    option_pairs = []
    for key, value in options.items():
        # Enclose string values in quotes, but not numbers or booleans
        if isinstance(value, str):
            option_pairs.append(f'"{key}","{value}"')
        else:
            option_pairs.append(f'"{key}",{value}')

    options_string = ";".join(option_pairs)

    # Final formula structure: =SPARKLINE(data, {options})
    # NOTE: Use COMMA between data and options (English locale), SEMICOLON within options
    formula = f'=SPARKLINE({{{",".join(map(str, clean_data))}}},{{{options_string}}})'
    return formula


def generate_gs_sparkline_with_let(data, color, charttype="column", negcolor=None):
    """
    Generates a Google Sheets =LET() formula with SPARKLINE that auto-scales using MIN/MAX with 15% padding.
    This provides better visual scaling than hardcoded ymin/ymax values.

    Args:
        data: List of numeric values
        color: Primary color (hex string like "#FFD700")
        charttype: "column" or "line" (default: "column")
        negcolor: Color for negative values (optional, for column charts)

    Returns:
        String containing the =LET(SPARKLINE(...)) formula
    """
    # Ensure data is a list of numbers
    clean_data = [float(item) if isinstance(item, (int, float)) and item is not None else 0 for item in data]

    if not clean_data:
        return ''

    # Build data string
    data_str = ",".join(map(str, clean_data))

    # Build sparkline options based on chart type
    if charttype == "column" and negcolor:
        sparkline_options = f'{{"charttype","column";"color","{color}";"negcolor","{negcolor}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'
    else:
        sparkline_options = f'{{"charttype","{charttype}";"color","{color}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'

    # LET formula with 15% padding - wrap in IFERROR to show blank instead of #N/A for all-zero data
    formula = f'''=IFERROR(LET(r,{{{data_str}}},x,FILTER(r,(r<>0)*(r<>"")),lo,MIN(x),hi,MAX(x),span,hi-lo,pad,MAX(1,span*0.15),SPARKLINE(IF((r=0)+(r=""),NA(),r),{sparkline_options})),"")'''

    return formula


def generate_gs_sparkline_posneg_bar(data):
    """
    Generates a Google Sheets SPARKLINE formula with COLUMN (bar) chart using LET for auto-scaling.
    Uses MIN/MAX of data with 15% padding for optimal visualization of interconnector flows.

    Args:
        data: List of numeric values (can be positive or negative for interconnector flows)

    Returns:
        String containing the =LET(SPARKLINE(...)) formula with column chart
    """
    # Use LET formula with purple bars for positive, red for negative
    return generate_gs_sparkline_with_let(data, color="#8A2BE2", charttype="column", negcolor="#DC143C")

def generate_gs_sparkline_with_symmetric_let(data, color, negcolor):
    """
    Generates =LET() formula with SYMMETRIC padding around zero for PS (Pumped Storage).
    Uses MAX(ABS(x)) to balance positive/negative ranges equally.
    Args:
        data: List of numeric values (can be negative for charging)
        color: Primary color for positive values (hex like "#8A2BE2")
        negcolor: Color for negative values (hex like "#DC143C")
    Returns:
        =LET(SPARKLINE(...)) formula string with symmetric ymin/ymax
    """
    clean_data = [float(item) if isinstance(item, (int, float)) and item is not None else 0 for item in data]
    if not clean_data:
        return ''
    data_str = ",".join(map(str, clean_data))

    # Symmetric padding: MAX(ABS(x)) creates balanced range around zero
    # pad = MAX(10, m*0.08) ensures minimum 10 MW padding or 8% of max absolute value
    # IFERROR wrapper shows blank instead of #N/A for all-zero data
    formula = f'''=IFERROR(LET(r,{{{data_str}}},x,FILTER(r,r<>0),m,MAX(ABS(x)),pad,MAX(10,m*0.08),SPARKLINE(IF(r=0,NA(),r),{{"charttype","column";"color","{color}";"negcolor","{negcolor}";"empty","ignore";"axis",TRUE;"axiscolor","#999999";"ymin",-m-pad;"ymax",m+pad}})),"")'''
    return formula
# ---------------------------------
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set global socket timeout to prevent infinite hangs
socket.setdefaulttimeout(120)

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def timed_query(func_name):
    """Decorator to time query functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = datetime.now()
            result = func(*args, **kwargs)
            elapsed = (datetime.now() - start).total_seconds()
            logging.info(f"  ⏱️  {func_name}: {elapsed:.1f}s")
            return result
        return wrapper
    return decorator

def get_fuel_data(bq_client):
    """Get 48 periods of fuel generation data - DEDUPED then averaged"""
    query = f"""
    WITH deduped AS (
      SELECT DISTINCT
        settlementPeriod,
        fuelType,
        generation,
        publishTime
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    ),
    latest_per_period AS (
      SELECT
        settlementPeriod,
        fuelType,
        MAX(publishTime) as max_publish
      FROM deduped
      GROUP BY settlementPeriod, fuelType
    )
    SELECT
      d.settlementPeriod,
      d.fuelType,
      AVG(d.generation) as total_generation
    FROM deduped d
    JOIN latest_per_period l
      ON d.settlementPeriod = l.settlementPeriod
      AND d.fuelType = l.fuelType
      AND d.publishTime = l.max_publish
    GROUP BY d.settlementPeriod, d.fuelType
    ORDER BY d.settlementPeriod, d.fuelType
    """
    return bq_client.query(query).to_dataframe()

def get_interconnector_data(bq_client):
    """Get 48 periods of interconnector data - DEDUPED then averaged"""
    query = f"""
    WITH deduped AS (
      SELECT DISTINCT
        settlementPeriod,
        fuelType,
        generation,
        publishTime
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND fuelType LIKE 'INT%'
    ),
    latest_per_period AS (
      SELECT
        settlementPeriod,
        fuelType,
        MAX(publishTime) as max_publish
      FROM deduped
      GROUP BY settlementPeriod, fuelType
    )
    SELECT
      d.settlementPeriod,
      d.fuelType as interconnector,
      AVG(d.generation) as net_flow
    FROM deduped d
    JOIN latest_per_period l
      ON d.settlementPeriod = l.settlementPeriod
      AND d.fuelType = l.fuelType
      AND d.publishTime = l.max_publish
    GROUP BY d.settlementPeriod, d.fuelType
    ORDER BY d.settlementPeriod, interconnector
    """
    return bq_client.query(query).to_dataframe()

def get_kpi_history(bq_client):
    """Get 48 periods of KPI data for sparklines - LATEST publishTime only"""
    query = f"""
    WITH wholesale AS (
      SELECT
        settlementPeriod,
        AVG(price) as wholesale_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    frequency AS (
      SELECT
        EXTRACT(HOUR FROM measurementTime) * 2 +
        CASE WHEN EXTRACT(MINUTE FROM measurementTime) >= 30 THEN 2 ELSE 1 END as settlementPeriod,
        AVG(frequency) as freq
      FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
      WHERE CAST(measurementTime AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    latest_fuel_publish AS (
      SELECT
        settlementPeriod,
        fuelType,
        MAX(publishTime) as max_publish
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod, fuelType
    ),
    deduped_fuel AS (
      -- CRITICAL: IRIS data has triplication bug - deduplicate BEFORE aggregating
      SELECT DISTINCT
        i.settlementPeriod,
        i.fuelType,
        i.generation,
        i.publishTime
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris` i
      JOIN latest_fuel_publish l
        ON i.settlementPeriod = l.settlementPeriod
        AND i.fuelType = l.fuelType
        AND i.publishTime = l.max_publish
      WHERE CAST(i.settlementDate AS DATE) = CURRENT_DATE()
    ),
    generation AS (
      SELECT
        settlementPeriod,
        SUM(generation) as total_gen,
        SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) as wind
      FROM deduped_fuel
      GROUP BY settlementPeriod
    )
    SELECT
      COALESCE(w.settlementPeriod, f.settlementPeriod, g.settlementPeriod) as period,
      COALESCE(w.wholesale_price, 0) as wholesale,
      COALESCE(f.freq, 50.0) as frequency,
      COALESCE(g.total_gen, 0) as total_gen,
      COALESCE(g.wind, 0) as wind,
      COALESCE(g.total_gen, 0) as demand
    FROM wholesale w
    FULL OUTER JOIN frequency f ON w.settlementPeriod = f.settlementPeriod
    FULL OUTER JOIN generation g ON COALESCE(w.settlementPeriod, f.settlementPeriod) = g.settlementPeriod
    ORDER BY period
    """
    return bq_client.query(query).to_dataframe()

def get_market_metrics(bq_client):
    """Get 48 periods of market metrics

    Uses system prices (SSP/SBP from bmrs_costs) as BM price since:
    - BOALF acceptance prices require BOD matching (lags for real-time)
    - System prices = imbalance settlement (what batteries trade at)
    - SSP = SBP since BSC P305 (Nov 2015) - single imbalance price

    Note: System prices typically lag by 1-2 periods (~30-60 min)
    """
    query = f"""
    WITH system_prices AS (
      SELECT
        settlementPeriod,
        AVG(systemSellPrice) as bm_price  -- SSP = SBP (single imbalance price)
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    market_index AS (
      SELECT
        settlementPeriod,
        AVG(price) as mid_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    )
    SELECT
      s.settlementPeriod as period,
      s.bm_price as bm_avg,
      s.bm_price as bm_vol_wtd,  -- Same as bm_avg (single price)
      m.mid_price as mid_price,
      s.bm_price as sys_buy,
      s.bm_price as sys_sell,
      s.bm_price - m.mid_price as bm_mid_spread,
      0 as bm_sysbuy_spread,  -- No spread (single price)
      0 as bm_syssell_spread,  -- No spread (single price)
      0 as daily_comp,
      0 as vlp_rev,
      0 as contango
    FROM system_prices s
    INNER JOIN market_index m ON s.settlementPeriod = m.settlementPeriod
    WHERE s.bm_price IS NOT NULL AND m.mid_price IS NOT NULL
      AND s.bm_price > 0 AND m.mid_price > 0
    ORDER BY period
    """
    df = bq_client.query(query).to_dataframe()

    # If current period has no data, return most recent available
    if df.empty or (not df.empty and df.iloc[-1]['bm_avg'] == 0):
        # Find last non-zero period
        non_zero = df[df['bm_avg'] > 0]
        if not non_zero.empty:
            logging.info(f"⚠️  System price not available for current period, using period {int(non_zero.iloc[-1]['period'])}")

    return df

def get_iris_freshness(bq_client):
    """Get IRIS data freshness indicator"""
    query = f"""
    SELECT
      MAX(publishTime) as latest_publish,
      MAX(settlementDate) as latest_settlement,
      MAX(settlementPeriod) as latest_period
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    """
    df = bq_client.query(query).to_dataframe()
    if df.empty:
        return "⚠️ No IRIS data"

    latest = df['latest_publish'].iloc[0]
    # Convert to timezone-aware if needed
    if latest.tzinfo is None:
        latest = pytz.UTC.localize(latest)

    now_utc = datetime.now(pytz.UTC)
    age_minutes = (now_utc - latest).total_seconds() / 60

    if age_minutes < 5:
        return f"✅ IRIS Live ({int(age_minutes)}m ago)"
    elif age_minutes < 15:
        return f"⚠️ IRIS Delayed ({int(age_minutes)}m ago)"
    else:
        return f"❌ IRIS Stale ({int(age_minutes)}m ago)"

def get_current_kpis(bq_client):
    """Get current settlement period KPIs - LATEST publishTime only"""
    # Use MAX period from actual data (not calculated from time)
    period_query = f"""
    SELECT MAX(settlementPeriod) as current_period
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    """
    period_df = bq_client.query(period_query).to_dataframe()
    if period_df.empty or pd.isna(period_df['current_period'].iloc[0]):
        logging.warning("⚠️  No current period data in bmrs_fuelinst_iris - using period 1")
        current_period = 1
    else:
        current_period = int(period_df['current_period'].iloc[0])

    query = f"""
    WITH latest_mid AS (
      SELECT AVG(price) as wholesale
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND settlementPeriod = {current_period}
    ),
    latest_freq AS (
      SELECT AVG(frequency) as freq
      FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
      WHERE CAST(measurementTime AS DATE) = CURRENT_DATE()
        AND CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
    ),
    latest_fuel AS (
      SELECT
        i.fuelType,
        i.generation,
        ROW_NUMBER() OVER (PARTITION BY i.fuelType ORDER BY i.publishTime DESC) as rn
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris` i
      WHERE CAST(i.settlementDate AS DATE) = CURRENT_DATE()
        AND i.settlementPeriod = {current_period}
    ),
    fuel_totals AS (
      SELECT
        SUM(generation) as total_gen,
        SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) as wind
      FROM latest_fuel
      WHERE rn = 1
    )
    SELECT
      COALESCE(m.wholesale, 0) as wholesale,
      COALESCE(f.freq, 50.0) as freq,
      COALESCE(g.total_gen, 0) as total_gen,
      COALESCE(g.wind, 0) as wind,
      COALESCE(g.total_gen, 0) as demand
    FROM latest_mid m
    CROSS JOIN latest_freq f
    CROSS JOIN fuel_totals g
    """
    return bq_client.query(query).to_dataframe()

def get_system_price_weekly_timeseries(bq_client):
    """Get 7 daily price datapoints for sparklines"""
    query = f"""
    SELECT
      DATE(settlementDate) as date,
      AVG(systemSellPrice) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY date
    ORDER BY date ASC
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Weekly timeseries query failed: {e}")
        return pd.DataFrame()

def get_system_price_weekly(bq_client):
    """Get 7-day aggregated KPIs with daily averages"""
    query = f"""
    WITH daily_prices AS (
      SELECT
        DATE(settlementDate) as date,
        AVG(systemSellPrice) as avg_price,
        MAX(systemSellPrice) as max_price,
        MIN(systemSellPrice) as min_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      GROUP BY date
    ),
    daily_bm AS (
      SELECT
        DATE(settlementDate) as date,
        SUM(totalCashflow) as total_cashflow,
        COUNT(DISTINCT bmUnit) as active_units
      FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
      GROUP BY date
    )
    SELECT
      AVG(p.avg_price) as period_avg,
      MAX(p.max_price) as period_high,
      MIN(p.min_price) as period_low,
      STDDEV(p.avg_price) as volatility,
      AVG(b.total_cashflow) as avg_daily_cashflow,
      0.0 as avg_offer,
      0.0 as avg_bid,
      AVG(b.active_units) as avg_active_units
    FROM daily_prices p
    LEFT JOIN daily_bm b ON p.date = b.date
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Weekly KPI query failed: {e}")
        return pd.DataFrame()

def get_system_price_monthly_timeseries(bq_client):
    """Get 30 daily price datapoints for sparklines"""
    query = f"""
    SELECT
      DATE(settlementDate) as date,
      AVG(systemSellPrice) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY date
    ORDER BY date ASC
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Monthly timeseries query failed: {e}")
        return pd.DataFrame()

def get_system_price_monthly(bq_client):
    """Get 30-day aggregated KPIs with daily averages"""
    query = f"""
    WITH daily_prices AS (
      SELECT
        DATE(settlementDate) as date,
        AVG(systemSellPrice) as avg_price,
        MAX(systemSellPrice) as max_price,
        MIN(systemSellPrice) as min_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
      GROUP BY date
    ),
    daily_bm AS (
      SELECT
        DATE(settlementDate) as date,
        SUM(totalCashflow) as total_cashflow,
        COUNT(DISTINCT bmUnit) as active_units
      FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
      GROUP BY date
    )
    SELECT
      AVG(p.avg_price) as period_avg,
      MAX(p.max_price) as period_high,
      MIN(p.min_price) as period_low,
      STDDEV(p.avg_price) as volatility,
      AVG(b.total_cashflow) as avg_daily_cashflow,
      0.0 as avg_offer,
      0.0 as avg_bid,
      AVG(b.active_units) as avg_active_units
    FROM daily_prices p
    LEFT JOIN daily_bm b ON p.date = b.date
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Monthly KPI query failed: {e}")
        return pd.DataFrame()

def get_system_price_yearly_timeseries(bq_client):
    """Get 12 monthly price datapoints for sparklines"""
    query = f"""
    SELECT
      DATE_TRUNC(DATE(settlementDate), MONTH) as month,
      AVG(systemSellPrice) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    GROUP BY month
    ORDER BY month ASC
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Yearly timeseries query failed: {e}")
        return pd.DataFrame()

def get_system_price_yearly(bq_client):
    """Get 12-month aggregated KPIs with monthly averages"""
    query = f"""
    WITH monthly_prices AS (
      SELECT
        DATE_TRUNC(DATE(settlementDate), MONTH) as month,
        AVG(systemSellPrice) as avg_price,
        MAX(systemSellPrice) as max_price,
        MIN(systemSellPrice) as min_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
      GROUP BY month
    ),
    monthly_bm AS (
      SELECT
        month,
        AVG(totalCashflow) as avg_daily_cashflow,
        AVG(active_units) as avg_active_units
      FROM (
        SELECT
          DATE_TRUNC(DATE(settlementDate), MONTH) as month,
          SUM(totalCashflow) as totalCashflow,
          COUNT(DISTINCT bmUnit) as active_units
        FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
        GROUP BY month
      )
      GROUP BY month
    )
    SELECT
      AVG(p.avg_price) as period_avg,
      MAX(p.max_price) as period_high,
      MIN(p.min_price) as period_low,
      STDDEV(p.avg_price) as volatility,
      AVG(b.avg_daily_cashflow) as avg_daily_cashflow,
      0.0 as avg_offer,
      0.0 as avg_bid,
      AVG(b.avg_active_units) as avg_active_units
    FROM monthly_prices p
    LEFT JOIN monthly_bm b ON p.month = b.month
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Yearly KPI query failed: {e}")
        return pd.DataFrame()

def get_system_price_analysis(bq_client):
    """
    Get System Price Analysis with historical context:
    - Current price (£/MWh)
    - 7-day & 30-day averages
    - 30-day high/low (volatility range)
    - Deviation % from 7-day baseline
    - Market condition flags (🔥 Short/💧 Long/⚖ Balanced)
    Uses bmrs_costs for system price (SSP=SBP post-P305)
    """
    query = f"""
    WITH
    current_prices AS (
      SELECT
        settlementPeriod as period,
        systemSellPrice as current_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    ),
    hist_7d AS (
      SELECT
        settlementPeriod as period,
        AVG(systemSellPrice) as avg_7d
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE settlementDate BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                                AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
      GROUP BY settlementPeriod
    ),
    hist_30d AS (
      SELECT
        settlementPeriod as period,
        AVG(systemSellPrice) as avg_30d,
        MAX(systemSellPrice) as high_30d,
        MIN(systemSellPrice) as low_30d
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE settlementDate BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                                AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
      GROUP BY settlementPeriod
    )
    SELECT
      c.period,
      c.current_price,
      COALESCE(h7.avg_7d, 0) as avg_7d,
      COALESCE(h30.avg_30d, 0) as avg_30d,
      COALESCE(h30.high_30d, 0) as high_30d,
      COALESCE(h30.low_30d, 0) as low_30d,
      CASE
        WHEN COALESCE(h7.avg_7d, 0) > 0
        THEN ((c.current_price - h7.avg_7d) / h7.avg_7d * 100)
        ELSE 0
      END as deviation_pct
    FROM current_prices c
    LEFT JOIN hist_7d h7 ON c.period = h7.period
    LEFT JOIN hist_30d h30 ON c.period = h30.period
    WHERE c.current_price IS NOT NULL
    ORDER BY period
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            logging.warning("⚠️  System Price Analysis: No data available")
        return df
    except Exception as e:
        logging.error(f"❌ System Price Analysis query failed: {e}")
        return pd.DataFrame(columns=['period', 'current_price', 'avg_7d', 'avg_30d',
                                    'high_30d', 'low_30d', 'deviation_pct'])

def get_active_outages(bq_client):
    """
    Get currently active REMIT power station outages
    Returns top 15 by unavailable capacity
    Note: assetName often NULL, use affectedUnit or registrationCode as fallback
    FILTERS OUT interconnectors (I_IEG, I_IED prefixes) to show real power plants only
    Uses ROW_NUMBER() to eliminate duplicates (same asset with different timestamps)
    """
    query = f"""
    WITH ranked_outages AS (
      SELECT
        COALESCE(assetName, affectedUnit, registrationCode, 'Unknown Asset') as asset_name,
        COALESCE(fuelType, assetType, 'Unknown') as fuel_type,
        unavailableCapacity,
        normalCapacity,
        COALESCE(cause, 'Not specified') as cause,
        eventStartTime,
        eventEndTime,
        ROW_NUMBER() OVER (
          PARTITION BY
            COALESCE(assetName, affectedUnit, registrationCode, 'Unknown Asset'),
            CAST(unavailableCapacity AS INT64),
            COALESCE(fuelType, assetType, 'Unknown')
          ORDER BY eventStartTime DESC
        ) as rn
      FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
      WHERE eventStatus = 'Active'
        AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
        AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
        AND unavailableCapacity > 0
        AND COALESCE(assetName, affectedUnit, registrationCode, '') NOT LIKE 'I_IEG%'
        AND COALESCE(assetName, affectedUnit, registrationCode, '') NOT LIKE 'I_IED%'
        AND COALESCE(assetName, affectedUnit, registrationCode, '') NOT LIKE 'I_%'
    )
    SELECT
      asset_name, fuel_type, unavailableCapacity, normalCapacity, cause, eventStartTime, eventEndTime
    FROM ranked_outages
    WHERE rn = 1
    ORDER BY unavailableCapacity DESC
    LIMIT 15
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            logging.warning("⚠️  Active Outages: No data available")
        return df
    except Exception as e:
        logging.error(f"❌ Active Outages query failed: {e}")
        return pd.DataFrame(columns=['asset_name', 'fuel_type', 'unavailableCapacity',
                                    'normalCapacity', 'cause', 'eventStartTime', 'eventEndTime'])

def get_frequency_physics(bq_client):
    """
    Get grid frequency and Net Imbalance Volume (NIV) for today
    """
    query = f"""
    WITH freq AS (
      SELECT
        CAST(EXTRACT(HOUR FROM measurementTime) * 2 +
             CASE WHEN EXTRACT(MINUTE FROM measurementTime) >= 30 THEN 2 ELSE 1 END AS INT64) as period,
        AVG(frequency) as avg_frequency,
        MIN(frequency) as min_frequency,
        MAX(frequency) as max_frequency
      FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
      WHERE CAST(measurementTime AS DATE) = CURRENT_DATE()
      GROUP BY period
    ),
    niv AS (
      SELECT
        settlementPeriod as period,
        SUM(imbalanceVolume) as net_imbalance_mwh
      FROM `{PROJECT_ID}.{DATASET}.bmrs_imbalngc_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    )
    SELECT
      COALESCE(f.period, n.period) as period,
      COALESCE(f.avg_frequency, 0) as avg_frequency,
      COALESCE(f.min_frequency, 0) as min_frequency,
      COALESCE(f.max_frequency, 0) as max_frequency,
      COALESCE(n.net_imbalance_mwh, 0) as net_imbalance_mwh
    FROM freq f
    FULL OUTER JOIN niv n ON f.period = n.period
    ORDER BY period
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            logging.warning("⚠️  Frequency/Physics: No data available")
        return df
    except Exception as e:
        logging.error(f"❌ Frequency/Physics query failed: {e}")
        return pd.DataFrame(columns=['period', 'avg_frequency', 'min_frequency',
                                    'max_frequency', 'net_imbalance_mwh'])

def get_vlp_revenue_analysis(bq_client):
    """
    Get VLP (Virtual Lead Party) revenue analysis - top operators by total revenue (last 60 days)
    NOTE: Total revenue calculated in pandas, not SQL (BigQuery treats `total_revenue_gbp` as aggregated)
    """
    query = f"""
    SELECT
      lead_party_name,
      delivered_volume_mwh,
      total_revenue_gbp,
      bm_price_gbp_per_mwh,
      wholesale_price_gbp_per_mwh
    FROM `{PROJECT_ID}.{DATASET}.vlp_revenue_sp`
    WHERE CAST(settlement_date AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            logging.warning("⚠️  VLP Revenue Analysis: No data available")
            return pd.DataFrame(columns=['lead_party_name', 'total_mwh', 'total_revenue_gbp',
                                        'avg_margin_per_mwh', 'avg_bm_price', 'avg_wholesale_price'])

        # Aggregate in pandas (BigQuery has issues with total_revenue_gbp field)
        agg_df = df.groupby('lead_party_name').agg({
            'delivered_volume_mwh': 'sum',
            'total_revenue_gbp': 'sum',
            'bm_price_gbp_per_mwh': 'mean',
            'wholesale_price_gbp_per_mwh': 'mean'
        }).reset_index()

        agg_df.rename(columns={
            'delivered_volume_mwh': 'total_mwh',
            'bm_price_gbp_per_mwh': 'avg_bm_price',
            'wholesale_price_gbp_per_mwh': 'avg_wholesale_price'
        }, inplace=True)

        # Calculate margin
        agg_df['avg_margin_per_mwh'] = agg_df['total_revenue_gbp'] / agg_df['total_mwh']

        # Sort by revenue, top 10
        agg_df = agg_df.sort_values('total_revenue_gbp', ascending=False).head(10)

        return agg_df
    except Exception as e:
        logging.error(f"❌ VLP Revenue Analysis query failed: {e}")
        return pd.DataFrame(columns=['lead_party_name', 'total_mwh', 'total_revenue_gbp',
                                    'avg_margin_per_mwh', 'avg_bm_price', 'avg_wholesale_price'])

def get_bm_market_kpis(bq_client):
    """
    Get BM Market KPIs for today (48 periods):
    - Total £ (EBOCF bid + offer cashflow)
    - Total MWh (BOAV bid + offer volumes)
    - Net MWh (offer - bid)
    - EWAP (cashflow ÷ volume)
    - Dispatch Intensity (acceptances/hour)
    - Workhorse Index (active SPs/48)
    """
    query = f"""
    WITH
    cashflows AS (
      SELECT
        settlementPeriod as period,
        SUM(CASE WHEN _direction = 'offer' THEN totalCashflow ELSE 0 END) as offer_cashflow_gbp,
        SUM(CASE WHEN _direction = 'bid' THEN ABS(totalCashflow) ELSE 0 END) as bid_cashflow_gbp,
        COUNT(DISTINCT bmUnit) as active_units_cf
      FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    volumes AS (
      SELECT
        settlementPeriod as period,
        SUM(CASE WHEN _direction = 'offer' THEN totalVolumeAccepted ELSE 0 END) as offer_mwh,
        SUM(CASE WHEN _direction = 'bid' THEN totalVolumeAccepted ELSE 0 END) as bid_mwh,
        COUNT(DISTINCT bmUnit) as active_units_vol
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    acceptances AS (
      SELECT
        settlementPeriodFrom as period,
        COUNT(DISTINCT acceptanceNumber) as acceptance_count,
        COUNT(DISTINCT bmUnit) as active_units_accept
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriodFrom
    )
    SELECT
      COALESCE(c.period, v.period, a.period) as period,
      COALESCE(c.offer_cashflow_gbp, 0) + COALESCE(c.bid_cashflow_gbp, 0) as total_cashflow_gbp,
      COALESCE(v.offer_mwh, 0) + COALESCE(v.bid_mwh, 0) as total_volume_mwh,
      COALESCE(v.offer_mwh, 0) - COALESCE(v.bid_mwh, 0) as net_mwh,
      CASE WHEN COALESCE(v.offer_mwh, 0) > 0 THEN COALESCE(c.offer_cashflow_gbp, 0) / v.offer_mwh ELSE 0 END as ewap_offer,
      CASE WHEN COALESCE(v.bid_mwh, 0) > 0 THEN COALESCE(c.bid_cashflow_gbp, 0) / v.bid_mwh ELSE 0 END as ewap_bid,
      COALESCE(a.acceptance_count, 0) / 0.5 as acceptances_per_hour,
      GREATEST(COALESCE(c.active_units_cf, 0), COALESCE(v.active_units_vol, 0), COALESCE(a.active_units_accept, 0)) as active_units
    FROM cashflows c
    FULL OUTER JOIN volumes v ON c.period = v.period
    FULL OUTER JOIN acceptances a ON COALESCE(c.period, v.period) = a.period
    ORDER BY period
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            logging.warning("⚠️  BM Market KPIs: No data available")
        return df
    except Exception as e:
        logging.error(f"❌ BM Market KPIs query failed: {e}")
        return pd.DataFrame(columns=['period', 'total_cashflow_gbp', 'total_volume_mwh', 'net_mwh',
                                    'ewap_offer', 'ewap_bid', 'acceptances_per_hour', 'active_units'])

def main():
    print("=" * 80)
    print("⚡ UNIFIED DASHBOARD UPDATER - COMPLETE UPDATE")
    print("=" * 80)

    now = datetime.now()

    # Initialize clients
    logging.info("🔧 Connecting to BigQuery and Sheets...")
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')

    # Get current period from actual data (not calculated time)
    period_query = f"""
    SELECT MAX(settlementPeriod) as current_period
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    """
    period_result = bq_client.query(period_query).to_dataframe()['current_period'].iloc[0]
    current_period = int(period_result) if pd.notna(period_result) else int((now.hour * 2) + (1 if now.minute >= 30 else 0))

    logging.info(f"⏰ Time: {now.strftime('%H:%M:%S')} (Period {current_period})")

    # Use absolute path for credentials
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cred_files = [
        os.path.join(script_dir, 'inner-cinema-credentials.json'),
        os.path.join(script_dir, 'inner-cinema-credentials-2.json'),
        os.path.join(script_dir, 'inner-cinema-credentials-3.json'),
        os.path.join(script_dir, 'inner-cinema-credentials-4.json'),
        os.path.join(script_dir, 'inner-cinema-credentials-5.json'),
    ]
    cache = CacheManager(cred_files)
    logging.info("✅ Connected\n")

    # ===========================
    # 1. UPDATE DATA_HIDDEN (Parallel BigQuery queries)
    # ===========================
    t_parallel_start = datetime.now()
    logging.info("📊 Querying BigQuery in parallel (14 queries)...")

    # Run all BigQuery queries in parallel (including new weekly/monthly/yearly)
    with ThreadPoolExecutor(max_workers=14) as executor:
        future_fuel = executor.submit(get_fuel_data, bq_client)
        future_inter = executor.submit(get_interconnector_data, bq_client)
        future_metrics = executor.submit(get_market_metrics, bq_client)
        future_kpi_hist = executor.submit(get_kpi_history, bq_client)
        future_freshness = executor.submit(get_iris_freshness, bq_client)
        future_kpi_current = executor.submit(get_current_kpis, bq_client)
        future_bm_kpis = executor.submit(get_bm_market_kpis, bq_client)
        future_sysprice = executor.submit(get_system_price_analysis, bq_client)
        future_outages = executor.submit(get_active_outages, bq_client)
        future_physics = executor.submit(get_frequency_physics, bq_client)
        future_vlp = executor.submit(get_vlp_revenue_analysis, bq_client)
        future_weekly = executor.submit(get_system_price_weekly, bq_client)
        future_monthly = executor.submit(get_system_price_monthly, bq_client)
        future_yearly = executor.submit(get_system_price_yearly, bq_client)
        future_weekly_ts = executor.submit(get_system_price_weekly_timeseries, bq_client)
        future_monthly_ts = executor.submit(get_system_price_monthly_timeseries, bq_client)
        future_yearly_ts = executor.submit(get_system_price_yearly_timeseries, bq_client)

        # Wait for all to complete
        fuel_df = future_fuel.result()
        inter_df = future_inter.result()
        metrics_df = future_metrics.result()
        kpi_hist_df = future_kpi_hist.result()
        iris_freshness = future_freshness.result()
        current_kpis = future_kpi_current.result()
        bm_kpis_df = future_bm_kpis.result()
        sysprice_df = future_sysprice.result()
        outages_df = future_outages.result()
        physics_df = future_physics.result()
        vlp_df = future_vlp.result()
        weekly_df = future_weekly.result()
        monthly_df = future_monthly.result()
        yearly_df = future_yearly.result()
        weekly_ts_df = future_weekly_ts.result()
        monthly_ts_df = future_monthly_ts.result()
        yearly_ts_df = future_yearly_ts.result()

    logging.info(f"  ⏱️  All BigQuery queries: {(datetime.now()-t_parallel_start).total_seconds():.1f}s (parallel)")

    t2 = datetime.now()
    # Pivot fuel data to rows
    fuel_types = ['WIND', 'NUCLEAR', 'CCGT', 'BIOMASS', 'NPSHYD', 'OTHER', 'OCGT', 'COAL', 'OIL', 'PS']
    fuel_rows = []
    for fuel in fuel_types:
        row = [fuel]
        fuel_data = fuel_df[fuel_df['fuelType'] == fuel]
        for period in range(1, 49):
            period_data = fuel_data[fuel_data['settlementPeriod'] == period]
            value = period_data['total_generation'].sum() if not period_data.empty else 0
            row.append(value)
        fuel_rows.append(row)
    logging.info(f"  ⏱️  Fuel pivot: {(datetime.now()-t2).total_seconds():.1f}s")

    t4 = datetime.now()

    # Pivot interconnector data - these are in bmrs_fuelinst_iris as fuelType
    # Complete mapping with display names
    interconnectors = [
        ('INTELEC', '🇫🇷 ElecLink'),   # France (Channel Tunnel)
        ('INTEW', '🇮🇪 East-West'),     # Ireland (EWIC)
        ('INTFR', '🇫🇷 IFA'),           # France (IFA)
        ('INTGRNL', '🇮🇪 Greenlink'),   # Ireland
        ('INTIFA2', '🇫🇷 IFA2'),        # France (IFA2)
        ('INTIRL', '🇮🇪 Moyle'),        # N.Ireland
        ('INTNED', '🇳🇱 BritNed'),      # Netherlands
        ('INTNEM', '🇧🇪 Nemo'),         # Belgium (NEMO)
        ('INTNSL', '🇳🇴 NSL'),          # Norway
        ('INTVKL', '🇩🇰 Viking Link')   # Denmark
    ]
    inter_rows = []
    for inter_code, inter_name in interconnectors:
        row = [inter_name]  # Use display name instead of code
        inter_data = inter_df[inter_df['interconnector'] == inter_code]
        for period in range(1, 49):
            period_data = inter_data[inter_data['settlementPeriod'] == period]
            value = period_data['net_flow'].sum() if not period_data.empty else 0
            row.append(value)
        inter_rows.append(row)
    logging.info(f"  ⏱️  Interconnector pivot: {(datetime.now()-t4).total_seconds():.1f}s")

    t5 = datetime.now()
    # Pad rows to 49 values
    for row in fuel_rows + inter_rows:
        if len(row) < 49:
            row.extend([''] * (49 - len(row)))

    # Add current period to B1 for formulas to reference
    header_row = [['Period', current_period]]
    cache.queue_update(SPREADSHEET_ID, 'Data_Hidden', 'A1:B1', header_row)

    cache.queue_update(SPREADSHEET_ID, 'Data_Hidden', 'A2:AW11', fuel_rows)
    cache.queue_update(SPREADSHEET_ID, 'Data_Hidden', 'A12:AW21', inter_rows)
    logging.info(f"  ⏱️  Data prep & queue: {(datetime.now()-t5).total_seconds():.1f}s")

    t7 = datetime.now()

    # Pivot metrics to rows (already fetched in parallel)
    metric_rows = [
        ['BM_Avg_Price'] + metrics_df['bm_avg'].tolist(),
        ['BM_Vol_Wtd'] + metrics_df['bm_vol_wtd'].tolist(),
        ['MID_Price'] + metrics_df['mid_price'].tolist(),
        ['Sys_Buy'] + metrics_df['sys_buy'].tolist(),
        ['Sys_Sell'] + metrics_df['sys_sell'].tolist(),
        ['BM_MID_Spread'] + metrics_df['bm_mid_spread'].tolist(),
        ['BM_SysBuy'] + metrics_df['bm_sysbuy_spread'].tolist(),
        ['BM_SysSell'] + metrics_df['bm_syssell_spread'].tolist(),
        ['Daily_Comp'] + metrics_df['daily_comp'].tolist(),
        ['VLP_Rev'] + metrics_df['vlp_rev'].tolist(),
        ['Contango'] + metrics_df['contango'].tolist(),
    ]

    # Pad to 49 values
    for row in metric_rows:
        if len(row) < 49:
            row.extend([''] * (49 - len(row)))

    cache.queue_update(SPREADSHEET_ID, 'Data_Hidden', 'A27:AW37', metric_rows)
    logging.info(f"  ⏱️  Metrics pivot: {(datetime.now()-t7).total_seconds():.1f}s")

    t9 = datetime.now()

    # Pivot KPI history to rows (already fetched in parallel)
    # Convert MW to GW for Total Generation, Wind, Demand (for proper sparkline scaling)
    kpi_rows = [
        ['Wholesale Price'] + kpi_hist_df['wholesale'].tolist(),
        ['Frequency'] + kpi_hist_df['frequency'].tolist(),
        ['Total Generation'] + (kpi_hist_df['total_gen'] / 1000).tolist(),  # MW → GW
        ['Wind Output'] + (kpi_hist_df['wind'] / 1000).tolist(),  # MW → GW
        ['System Demand'] + (kpi_hist_df['demand'] / 1000).tolist(),  # MW → GW
    ]

    # Pad to 49 values
    for row in kpi_rows:
        if len(row) < 49:
            row.extend([''] * (49 - len(row)))

    cache.queue_update(SPREADSHEET_ID, 'Data_Hidden', 'A22:AW26', kpi_rows)

    logging.info(f"✅ Queued Data_Hidden: {len(fuel_rows)} fuels + {len(inter_rows)} interconnectors + {len(metric_rows)} metrics + {len(kpi_rows)} KPI history")
    logging.info(f"  ⏱️  KPI pivot: {(datetime.now()-t9).total_seconds():.1f}s")
    logging.info(f"  ⏱️  TOTAL Data_Hidden prep: {(datetime.now()-t_parallel_start).total_seconds():.1f}s\n")

    # ===========================
    # 2. UPDATE LIVE DASHBOARD (using pre-fetched parallel data)
    # ===========================

    if not current_kpis.empty:
        wholesale = float(current_kpis['wholesale'].iloc[0])
        freq = float(current_kpis['freq'].iloc[0])
        total_gen = float(current_kpis['total_gen'].iloc[0])
        wind = float(current_kpis['wind'].iloc[0])
        demand = float(current_kpis['demand'].iloc[0])

        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A3', [[iris_freshness]])

        # Set PYTHON_MANAGED flag to prevent Apps Script data conflicts
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'AA1', [['PYTHON_MANAGED']])

        # Generate sparklines for row 7 (C7, E7, G7, I7, K7) - 48 periods (24 hours)
        # Get data from kpi_hist_df which has all metrics over 48 periods
        if not kpi_hist_df.empty:
            # Wholesale price sparkline (from MID)
            spark_wholesale = generate_gs_sparkline_formula(kpi_hist_df['wholesale'].tolist(), {"charttype": "column", "color": "#DA70D6"})

            # Frequency sparkline
            spark_frequency = generate_gs_sparkline_formula(kpi_hist_df['frequency'].tolist(), {"charttype": "line", "color": "#FFD700"})

            # Total generation sparkline
            spark_total_gen = generate_gs_sparkline_formula(kpi_hist_df['total_gen'].tolist(), {"charttype": "column", "color": "#4169E1"})

            # Wind sparkline
            spark_wind = generate_gs_sparkline_formula(kpi_hist_df['wind'].tolist(), {"charttype": "column", "color": "#00CED1"})

            # Demand sparkline (same as total_gen in current setup)
            spark_demand = generate_gs_sparkline_formula(kpi_hist_df['demand'].tolist(), {"charttype": "column", "color": "#FF4500"})
        else:
            # Fallback: use current values if no history
            spark_wholesale = generate_gs_sparkline_formula([wholesale], {"charttype": "column", "color": "#DA70D6"})
            spark_frequency = generate_gs_sparkline_formula([freq], {"charttype": "line", "color": "#FFD700"})
            spark_total_gen = generate_gs_sparkline_formula([total_gen], {"charttype": "column", "color": "#4169E1"})
            spark_wind = generate_gs_sparkline_formula([wind], {"charttype": "column", "color": "#00CED1"})
            spark_demand = generate_gs_sparkline_formula([demand], {"charttype": "column", "color": "#FF4500"})

        # Write sparklines to row 7 (merged with row 8)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'C7', [[spark_wholesale]])
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'E7', [[spark_frequency]])
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'G7', [[spark_total_gen]])
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'I7', [[spark_wind]])
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K7', [[spark_demand]])

        logging.info(f"  ⏱️  Generated 5 fuel sparklines: C7/E7/G7/I7/K7")

        # Calculate frequency deviation from 50 Hz for E6 display
        freq_deviation = freq - 50.0
        # Add ' prefix to force Google Sheets to treat as text (not formula)
        freq_display = f"'{freq_deviation:+.3f} Hz"  # Format as '+0.015 Hz' or '-0.020 Hz'
        logging.info(f"  📊 Frequency: {freq:.3f} Hz, Deviation: {freq_display}")

        # Update KPI values in row 6 (E6 shows deviation from 50 Hz)
        # Sparklines are now in row 7 (C7, E7, G7, I7, K7, merged with row 8)
        kpi_values = [f'£{wholesale:.2f}', '', freq_display, '', f'{total_gen/1000:.1f} GW', '', f'{wind/1000:.1f} GW', '', f'{demand/1000:.1f} GW']
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'C6:K6', [kpi_values])

    # Update fuel breakdown (rows 13-22) with current period values
    if not current_kpis.empty:
        # Get individual fuel values from fuel_df for current period
        fuel_current = fuel_df[fuel_df['settlementPeriod'] == current_period]

        # Calculate total generation (excluding interconnectors)
        total_gen_current = fuel_current[~fuel_current['fuelType'].str.startswith('INT')]['total_generation'].sum()

        # Map fuel types to rows (B13-B22) and Data_Hidden rows for sparklines
        fuel_map = {
            'WIND': {'row': 13, 'data_row': 2},
            'NUCLEAR': {'row': 14, 'data_row': 3},
            'CCGT': {'row': 15, 'data_row': 4},
            'BIOMASS': {'row': 16, 'data_row': 5},
            'NPSHYD': {'row': 17, 'data_row': 6},
            'OTHER': {'row': 18, 'data_row': 7},
            'OCGT': {'row': 19, 'data_row': 8},
            'COAL': {'row': 20, 'data_row': 9},
            'OIL': {'row': 21, 'data_row': 10},
            'PS': {'row': 22, 'data_row': 11}
        }

        # Build batched arrays for B, C, D columns (much faster than 30 individual updates)
        fuel_values_b = []  # GW values
        fuel_values_c = []  # Percentages
        fuel_values_d = []  # Sparkline images

        t_spark = datetime.now()
        for fuel_type, mapping in fuel_map.items():
            data_row = mapping['data_row']

            # Get fuel value (can be negative for PS when charging)
            fuel_val = fuel_current[fuel_current['fuelType'] == fuel_type]['total_generation'].sum()
            fuel_gw = fuel_val / 1000  # Keep sign for PS charging/discharging

            # Calculate percentage share (absolute value for PS)
            fuel_pct = (abs(fuel_val) / total_gen_current * 100) if total_gen_current > 0 else 0

            # Build row data (show negative for PS when charging)
            fuel_values_b.append([f'{fuel_gw:.1f}'])
            fuel_values_c.append([f'{fuel_pct:.1f}%'])

            # Generate Google Sheets sparkline formula
            fuel_row_data = fuel_df[fuel_df['fuelType'] == fuel_type].sort_values('settlementPeriod')
            sparkline_data = []
            for period in range(1, 49):
                period_val = fuel_row_data[fuel_row_data['settlementPeriod'] == period]['total_generation'].sum()
                sparkline_data.append(period_val)  # Keep in MW for proper scaling

            color = SPARKLINE_COLORS.get(fuel_type, "#808080")

            # For Pumped Storage, use symmetric LET formula for balanced charge/discharge visualization
            if fuel_type == 'PS':
                sparkline = generate_gs_sparkline_with_symmetric_let(sparkline_data, color=color, negcolor="#DC143C")
            else:
                # Use LET formula with auto-padding for better visual scaling
                sparkline = generate_gs_sparkline_with_let(sparkline_data, color=color, charttype="column")

            fuel_values_d.append([sparkline])

        logging.info(f"  ⏱️  Generated 10 fuel sparklines: {(datetime.now()-t_spark).total_seconds():.3f}s")

        # Batched updates: 3 updates instead of 30 (10x faster)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'B13:B22', fuel_values_b)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'C13:C22', fuel_values_c)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'D13:D22', fuel_values_d)

    # Get latest period market metrics for L and O columns
    # Use most recent available data (system prices lag by 1-2 periods)
    if not metrics_df.empty:
        # Find last period with actual system price data
        non_zero_metrics = metrics_df[metrics_df['bm_avg'] > 0]
        if not non_zero_metrics.empty:
            latest_metrics = non_zero_metrics.tail(1).iloc[0]
            current_period = int(latest_metrics['period'])
        else:
            latest_metrics = metrics_df.tail(1).iloc[0]
            current_period = int(latest_metrics['period'])
            logging.warning("⚠️  No non-zero system prices found - early morning period?")

        bm_avg = float(latest_metrics['bm_avg'])
        bm_vol_wtd = float(latest_metrics['bm_vol_wtd'])
        mid_price = float(latest_metrics['mid_price'])
        bm_mid_spread = float(latest_metrics['bm_mid_spread'])
        bm_sysbuy_spread = float(latest_metrics['bm_sysbuy_spread'])
        bm_syssell_spread = float(latest_metrics['bm_syssell_spread'])

        logging.info(f"✅ Latest metrics (Period {current_period}):")
        logging.info(f"   System Price:  £{bm_avg:.2f}/MWh (imbalance settlement)")
        logging.info(f"   Market Index:  £{mid_price:.2f}/MWh (MID wholesale)")
        logging.info(f"   Spread:        £{bm_mid_spread:.2f}/MWh")

        # Generate Google Sheets sparklines for market metrics (pad to 48 periods)
        t_market_spark = datetime.now()

        # Filter to periods with actual price data (prevents rendering issues)
        active_price_periods = metrics_df[(metrics_df['bm_avg'] != 0) | (metrics_df['mid_price'] != 0)]

        if len(active_price_periods) > 0:
            df_for_market_sparklines = active_price_periods
            logging.info(f"  📊 Using {len(active_price_periods)}/{len(metrics_df)} periods with price data")
        else:
            df_for_market_sparklines = metrics_df
            logging.warning(f"  ⚠️  No active price periods found")

        # Generate market sparklines (current periods only)
        spark_bm_avg = generate_gs_sparkline_formula(df_for_market_sparklines['bm_avg'].tolist(), {"charttype": "column", "color": "#FF6347"})
        spark_mid = generate_gs_sparkline_formula(df_for_market_sparklines['mid_price'].tolist(), {"charttype": "column", "color": "#DA70D6"})

        logging.info(f"  ⏱️  Generated 2 market sparklines: {(datetime.now()-t_market_spark).total_seconds():.3f}s")

        # --- Market Dynamics Section ---
        logging.info("📊 Creating Market Dynamics section...")

        # Generate sparklines for the enhanced section (current periods only)
        spread_sparkline = generate_gs_sparkline_posneg_bar(df_for_market_sparklines['bm_mid_spread'].tolist())  # Can be positive or negative
        imb_sparkline = generate_gs_sparkline_formula(df_for_market_sparklines['bm_avg'].tolist(), {"charttype": "column", "color": "#4682B4"})

        logging.info(f"  📊 Generated spread_sparkline length: {len(spread_sparkline)} chars")

        # NEW COMPACT LAYOUT - Row 5 headers
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A5', [['BM-MID Spread £/MWh']])

        # NEW COMPACT LAYOUT - Row 6 values (A6, C6)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A6', [[f'£{bm_mid_spread:.2f}']])  # BM-MID Spread
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'C6', [[f'£{mid_price:.2f}']])  # Market Index (MID)

        # NEW COMPACT LAYOUT - A7:B9 (BM-MID Spread sparkline - merged 3 rows × 2 cols)
        # Write sparkline to merged cell range A7:B9
        logging.info(f"  📊 Queueing A7:B9 sparkline (merged cell): {spread_sparkline[:50]}...")
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A7', [[spread_sparkline]])

        logging.info("✅ Market metrics section updated (A5-B9)")
    else:
        logging.warning("⚠️  Market metrics DataFrame is empty - skipping market metrics update")

    # --- COMBINED KPI SECTION (K13:O22) - System Price + BM Market KPIs ---
    # This section combines both System Price Analysis and BM Market KPIs in rows 13-22
    if not sysprice_df.empty and not bm_kpis_df.empty:
        logging.info("📊 Creating Combined KPI Section (K13:O22)...")

        # Clear legacy garbage in columns A-F (rows 25-43) - old Data_Hidden bleed-through
        clear_garbage_rows = [['', '', '', '', '', ''] for _ in range(19)]  # 19 rows (25-43), 6 columns (A-F)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A25:F43', clear_garbage_rows)

        t_bm_spark = datetime.now()

        # Get current period values
        latest_bm = bm_kpis_df.iloc[-1]
        current_period_bm = int(latest_bm['period'])

        # Filter to only periods with actual data (prevents sparkline rendering issues with zeros)
        # Use cashflow > 0 OR volume > 0 as indicator of actual activity
        active_periods = bm_kpis_df[
            (bm_kpis_df['total_cashflow_gbp'] != 0) |
            (bm_kpis_df['total_volume_mwh'] != 0)
        ]

        # If we have active data, use it; otherwise fall back to all data
        if len(active_periods) > 0:
            df_for_sparklines = active_periods
            logging.info(f"  📊 Using {len(active_periods)}/{len(bm_kpis_df)} periods with activity")
        else:
            df_for_sparklines = bm_kpis_df
            logging.warning(f"  ⚠️  No active periods found, using all {len(bm_kpis_df)} periods")

        # Generate sparklines for 7 key metrics (using filtered data)
        spark_cashflow = generate_gs_sparkline_formula(df_for_sparklines['total_cashflow_gbp'].tolist(), {"charttype": "column", "color": "#FF6347"})
        spark_volume = generate_gs_sparkline_formula(df_for_sparklines['total_volume_mwh'].tolist(), {"charttype": "column", "color": "#4682B4"})
        spark_net_mwh = generate_gs_sparkline_formula(df_for_sparklines['net_mwh'].tolist(), {"charttype": "column", "color": "#32CD32"})

        # EWAP: use all data (not filtered) since EBOCF/BOAV lag real-time, may be all zeros
        ewap_offer_data = bm_kpis_df['ewap_offer'].tolist()
        ewap_bid_data = bm_kpis_df['ewap_bid'].tolist()
        spark_ewap_offer = generate_gs_sparkline_formula(ewap_offer_data if any(v > 0 for v in ewap_offer_data) else [0], {"charttype": "column", "color": "#FFD700"})
        spark_ewap_bid = generate_gs_sparkline_formula(ewap_bid_data if any(v > 0 for v in ewap_bid_data) else [0], {"charttype": "column", "color": "#DA70D6"})

        spark_dispatch = generate_gs_sparkline_formula(df_for_sparklines['acceptances_per_hour'].tolist(), {"charttype": "column", "color": "#FFA500"})
        spark_workhorse = generate_gs_sparkline_formula(df_for_sparklines['active_units'].tolist(), {"charttype": "column", "color": "#00A86B"})

        logging.info(f"  ⏱️  Generated 7 BM KPI sparklines: {(datetime.now()-t_bm_spark).total_seconds():.3f}s")

        # Calculate BM metrics
        total_cashflow = bm_kpis_df['total_cashflow_gbp'].sum()
        total_volume = bm_kpis_df['total_volume_mwh'].sum()
        total_net_mwh = bm_kpis_df['net_mwh'].sum()
        avg_ewap_offer = bm_kpis_df[bm_kpis_df['ewap_offer'] > 0]['ewap_offer'].mean() if len(bm_kpis_df[bm_kpis_df['ewap_offer'] > 0]) > 0 else 0
        avg_dispatch = bm_kpis_df['acceptances_per_hour'].mean()
        workhorse_index = latest_bm['active_units'] / 48 * 100  # Percentage

        # System Price metrics
        latest_price = sysprice_df['current_price'].iloc[-1] if len(sysprice_df) > 0 else 0
        avg_7d = sysprice_df['avg_7d'].mean()
        avg_30d = sysprice_df['avg_30d'].mean()
        max_30d = sysprice_df['high_30d'].max()
        min_30d = sysprice_df['low_30d'].min()
        deviation = sysprice_df['deviation_pct'].mean()

        # Generate System Price sparklines (use last 48 periods = 24 hours)
        max_periods = 48
        spark_current = generate_gs_sparkline_formula(sysprice_df['current_price'].tail(max_periods).tolist(), {"charttype": "line", "color": "#FF0000"})
        spark_7d = generate_gs_sparkline_formula(sysprice_df['avg_7d'].tail(max_periods).tolist(), {"charttype": "line", "color": "#999999"})
        spark_30d = generate_gs_sparkline_formula(sysprice_df['avg_30d'].tail(max_periods).tolist(), {"charttype": "line", "color": "#666666"})
        spark_dev = generate_gs_sparkline_posneg_bar(sysprice_df['deviation_pct'].tail(max_periods).tolist())
        spark_high = generate_gs_sparkline_formula(sysprice_df['high_30d'].tail(max_periods).tolist(), {"charttype": "column", "color": "#FF6347"})
        spark_low = generate_gs_sparkline_formula(sysprice_df['low_30d'].tail(max_periods).tolist(), {"charttype": "line", "color": "#4682B4"})

        # Market condition flag
        if deviation > 20:
            condition = "🔥 Short"
        elif deviation < -20:
            condition = "💧 Long"
        else:
            condition = "⚖ Balanced"

        # K12 HEADER ROW (merged K12:S12 - 9 columns wide)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K12', [['📊 MARKET DYNAMICS - 24 HOUR VIEW']])

        # POPULATE K13:S22 (10 rows: K=Name, L=Value, M=Desc, N:S=Sparkline merged 6 cols)
        # Format: K=KPI Name, L=Value with units, M=Description, N:S=Sparkline (6 columns merged)
        kpi_names = [
            'Real-time imbalance price',
            '7-Day Average',
            '30-Day Average',
            'Deviation from 7d',
            '30-Day High',
            '30-Day Low',
            'Total BM Cashflow',
            'EWAP Offer',
            'EWAP Bid',
            'Dispatch Intensity'
        ]
        kpi_values = [
            f'£{latest_price:.2f}/MWh',
            f'£{avg_7d:.2f}/MWh',
            f'£{avg_30d:.2f}/MWh',
            f'{deviation:+.1f}%',
            f'£{max_30d:.2f}/MWh',
            f'£{min_30d:.2f}/MWh',
            f'£{total_cashflow/1000:.1f}k',
            f'£{avg_ewap_offer:.2f}/MWh',
            f'£{latest_bm["ewap_bid"]:.2f}/MWh',
            f'{avg_dispatch:.1f}/hr'
        ]
        kpi_descs = [
            f'SSP=SBP {condition}',
            'Rolling mean',
            'Rolling mean',
            'vs 7-day avg',
            'Max price',
            'Min price',
            'Σ(Vol × Price)',
            'Energy-weighted avg',
            'Energy-weighted avg',
            f'Acceptances/hour • {workhorse_index:.1f}% active'
        ]
        sparklines = [
            spark_current, spark_7d, spark_30d, spark_dev,
            spark_high, spark_low, spark_cashflow,
            spark_ewap_offer, spark_ewap_bid, spark_dispatch
        ]

        # Write K, L, M columns (spaced rows: 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
        rows = [13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
        for i, (name, val, desc) in enumerate(zip(kpi_names, kpi_values, kpi_descs)):
            row = rows[i]
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', f'K{row}', [[name]])
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', f'L{row}', [[val]])
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', f'M{row}', [[desc]])

        # Write sparklines to N:S columns (6 cols wide, spaced rows)
        for i, sparkline in enumerate(sparklines):
            row = rows[i]
            # Write sparkline to all 6 columns in the merged range
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', f'N{row}:S{row}', [[sparkline, '', '', '', '', '']])

        logging.info(f"✅ Combined KPIs (K13:K31 spaced): £{latest_price:.2f}/MWh system price, £{total_cashflow/1000:.1f}k BM cashflow")

        # Clear old Weekly/Monthly position that overlapped with Combined KPIs (K23-K44)
        clear_overlap = [['', ''] for _ in range(22)]  # 22 rows (K23:L44)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K23:L44', clear_overlap)

        # --- WEEKLY KPI Section (K33:L43) - 7-DAY VIEW ---
        if not weekly_df.empty and not weekly_ts_df.empty:
            row = weekly_df.iloc[0]
            price_range = row["period_high"] - row["period_low"]

            # Generate sparklines from timeseries data
            prices_7d = weekly_ts_df['avg_price'].tolist()
            spark_7d_avg = generate_gs_sparkline_formula(prices_7d, {"charttype": "line", "color": "#4682B4"})
            spark_7d_high = generate_gs_sparkline_formula(prices_7d, {"charttype": "column", "color": "#FF6347"})
            spark_7d_low = generate_gs_sparkline_formula(prices_7d, {"charttype": "line", "color": "#32CD32"})
            spark_7d_range = generate_gs_sparkline_formula(prices_7d, {"charttype": "column", "color": "#999999"})
            spark_7d_vol = generate_gs_sparkline_formula(prices_7d, {"charttype": "line", "color": "#FFA500"})

            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K33', [['⚡ MARKET DYNAMICS - 7 DAY VIEW']])
            weekly_kpis = [
                [f'7-Day Average Price • £{row["period_avg"]:.2f}/MWh • Daily avg', spark_7d_avg],
                [f'7-Day High • £{row["period_high"]:.2f}/MWh • Peak daily', spark_7d_high],
                [f'7-Day Low • £{row["period_low"]:.2f}/MWh • Min daily', spark_7d_low],
                [f'Price Range • £{price_range:.2f}/MWh • High - Low', spark_7d_range],
                [f'Volatility (StdDev) • £{row["volatility"]:.2f}/MWh • Price variance', spark_7d_vol],
                [f'Avg Daily Cashflow • £{row["avg_daily_cashflow"]/1000:.1f}k • BM settlement', ''],
                [f'Avg Active Units • {row["avg_active_units"]:.1f} units • Daily avg', ''],
                ['', ''],
                ['', ''],
                ['', '']
            ]
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K34:L43', weekly_kpis)
            logging.info(f"✅ Weekly KPIs (K33:L43): £{row['period_avg']:.2f}/MWh avg, {len(prices_7d)} daily sparklines")
        else:
            logging.warning("⚠️  Weekly KPI Section: No data - skipping")

        # --- MONTHLY KPI Section (K45:L55) - 30-DAY VIEW ---
        if not monthly_df.empty and not monthly_ts_df.empty:
            row = monthly_df.iloc[0]
            price_range = row["period_high"] - row["period_low"]

            # Generate sparklines from timeseries data
            prices_30d = monthly_ts_df['avg_price'].tolist()
            spark_30d_avg = generate_gs_sparkline_formula(prices_30d, {"charttype": "line", "color": "#4682B4"})
            spark_30d_high = generate_gs_sparkline_formula(prices_30d, {"charttype": "column", "color": "#FF6347"})
            spark_30d_low = generate_gs_sparkline_formula(prices_30d, {"charttype": "line", "color": "#32CD32"})
            spark_30d_range = generate_gs_sparkline_formula(prices_30d, {"charttype": "column", "color": "#999999"})
            spark_30d_vol = generate_gs_sparkline_formula(prices_30d, {"charttype": "line", "color": "#FFA500"})

            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K45', [['⚡ MARKET DYNAMICS - 30 DAY VIEW']])
            monthly_kpis = [
                [f'30-Day Average Price • £{row["period_avg"]:.2f}/MWh • Daily avg', spark_30d_avg],
                [f'30-Day High • £{row["period_high"]:.2f}/MWh • Peak daily', spark_30d_high],
                [f'30-Day Low • £{row["period_low"]:.2f}/MWh • Min daily', spark_30d_low],
                [f'Price Range • £{price_range:.2f}/MWh • High - Low', spark_30d_range],
                [f'Volatility (StdDev) • £{row["volatility"]:.2f}/MWh • Price variance', spark_30d_vol],
                [f'Avg Daily Cashflow • £{row["avg_daily_cashflow"]/1000:.1f}k • BM settlement', ''],
                [f'Avg Active Units • {row["avg_active_units"]:.1f} units • Daily avg', ''],
                ['', ''],
                ['', ''],
                ['', '']
            ]
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K46:L55', monthly_kpis)
            logging.info(f"✅ Monthly KPIs (K45:L55): £{row['period_avg']:.2f}/MWh avg, {len(prices_30d)} daily sparklines")
        else:
            logging.warning("⚠️  Monthly KPI Section: No data - skipping")

        # --- YEARLY KPI Section (K57:L66) - 12-MONTH VIEW ---
        # RELOCATED: Was K45:L55, moved to avoid conflict with Frequency (L46) and VLP (L54-L55)
        if not yearly_df.empty and not yearly_ts_df.empty:
            row = yearly_df.iloc[0]
            price_range = row["period_high"] - row["period_low"]

            # Generate sparklines from timeseries data
            prices_12m = yearly_ts_df['avg_price'].tolist()
            spark_12m_avg = generate_gs_sparkline_formula(prices_12m, {"charttype": "line", "color": "#4682B4"})
            spark_12m_high = generate_gs_sparkline_formula(prices_12m, {"charttype": "column", "color": "#FF6347"})
            spark_12m_low = generate_gs_sparkline_formula(prices_12m, {"charttype": "line", "color": "#32CD32"})
            spark_12m_range = generate_gs_sparkline_formula(prices_12m, {"charttype": "column", "color": "#999999"})
            spark_12m_vol = generate_gs_sparkline_formula(prices_12m, {"charttype": "line", "color": "#FFA500"})

            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K57', [['⚡ MARKET DYNAMICS - 12 MONTH VIEW']])
            yearly_kpis = [
                [f'12-Month Average Price • £{row["period_avg"]:.2f}/MWh • Monthly avg', spark_12m_avg],
                [f'12-Month High • £{row["period_high"]:.2f}/MWh • Peak monthly', spark_12m_high],
                [f'12-Month Low • £{row["period_low"]:.2f}/MWh • Min monthly', spark_12m_low],
                [f'Price Range • £{price_range:.2f}/MWh • High - Low', spark_12m_range],
                [f'Volatility (StdDev) • £{row["volatility"]:.2f}/MWh • Price variance', spark_12m_vol],
                [f'Avg Daily Cashflow • £{row["avg_daily_cashflow"]/1000:.1f}k • BM settlement', ''],
                [f'Avg Active Units • {row["avg_active_units"]:.1f} units • Daily avg', ''],
                ['', ''],
                ['', ''],
                ['', '']
            ]
            cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K58:L67', yearly_kpis)
            logging.info(f"✅ Yearly KPIs (K58:L67): £{row['period_avg']:.2f}/MWh avg, {len(prices_12m)} monthly sparklines")
        else:
            logging.warning("⚠️  Yearly KPI Section: No data - skipping")

    else:
        logging.warning("⚠️  Combined KPI Section: Missing sysprice or BM data - skipping")

    # --- SYSTEM PRICE ANALYSIS Section - REMOVED (now in K13:O22) ---
    # --- BM MARKET KPIs Section - REMOVED (now in K13:O22) ---

    # --- FREQUENCY & PHYSICS Section (L46:O53) ---
    if not physics_df.empty:
        logging.info("📊 Creating Frequency & Physics section...")

        # Filter active periods
        active_physics = physics_df[(physics_df['avg_frequency'] > 0) | (physics_df['net_imbalance_mwh'] != 0)]
        df_physics = active_physics if len(active_physics) > 0 else physics_df

        # Generate sparklines
        spark_freq = generate_gs_sparkline_formula(df_physics['avg_frequency'].tolist(), {"charttype": "line", "color": "#FFD700"})
        spark_freq_min = generate_gs_sparkline_formula(df_physics['min_frequency'].tolist(), {"charttype": "line", "color": "#FFA500"})
        spark_freq_max = generate_gs_sparkline_formula(df_physics['max_frequency'].tolist(), {"charttype": "line", "color": "#FF6347"})
        spark_niv = generate_gs_sparkline_formula(df_physics['net_imbalance_mwh'].tolist(), {"charttype": "column", "color": "#4682B4"})

        # Calculate metrics
        latest_freq = df_physics['avg_frequency'].iloc[-1] if len(df_physics) > 0 else 0
        avg_freq = df_physics['avg_frequency'].mean()
        min_freq_overall = df_physics['min_frequency'].min()
        max_freq_overall = df_physics['max_frequency'].max()
        total_niv = df_physics['net_imbalance_mwh'].sum()

        # System state flag
        if latest_freq < 49.8:
            freq_state = "🔴 Low (Short)"
        elif latest_freq > 50.2:
            freq_state = "🔵 High (Long)"
        else:
            freq_state = "✅ Normal"

        niv_state = "🔥 Short" if total_niv > 0 else "💧 Long"

        # Query latest frequency directly (FIX for 0 Hz issue)
        try:
            freq_direct_query = f"""
            SELECT AVG(frequency) as freq
            FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
            WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
            """
            freq_direct_df = bq_client.query(freq_direct_query).to_dataframe()
            if not freq_direct_df.empty and freq_direct_df['freq'].iloc[0] > 0:
                latest_freq = freq_direct_df['freq'].iloc[0]
            elif latest_freq == 0:
                # Fallback to historical data
                freq_hist_query = f"""
                SELECT AVG(frequency) as freq
                FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
                WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 MINUTE)
                """
                freq_hist_df = bq_client.query(freq_hist_query).to_dataframe()
                if not freq_hist_df.empty and freq_hist_df['freq'].iloc[0] > 0:
                    latest_freq = freq_hist_df['freq'].iloc[0]
        except Exception as e:
            logging.warning(f"⚠️  Direct frequency query failed: {e}, using physics_df value")

        # Title
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'L46', [['⚡ FREQUENCY & SYSTEM PHYSICS']])

        # Metrics (4 rows) - FIXED: No '+' sign for frequency display
        physics_rows = [
            ['Grid Frequency', f'{latest_freq:.3f} Hz', spark_freq, freq_state],
            ['Freq Range (Min-Max)', f'{min_freq_overall:.3f} - {max_freq_overall:.3f} Hz', spark_freq_min, ''],
            ['Net Imbalance Vol (NIV)', f'{total_niv:+.0f} MWh', spark_niv, niv_state],
            ['Avg Frequency', f'{avg_freq:.3f} Hz', spark_freq_max, '']
        ]
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'L48:O51', physics_rows)

        logging.info(f"✅ Physics: {latest_freq:.3f} Hz, NIV {total_niv:+.0f} MWh ({niv_state})")
    else:
        logging.warning("⚠️  Frequency/Physics: No data - skipping section")

    # --- VLP REVENUE ANALYSIS Section (L54:O70) ---
    if not vlp_df.empty:
        logging.info("📊 Creating VLP Revenue Analysis section...")

        # Title
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'L54',
                          [['⚡ VLP REVENUE - TOP 10 OPERATORS (28 DAYS - Oct 1-28)']])

        # Column headers (L55:R55 = 7 columns)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'L55:R55',
                          [['Rank', 'Operator', 'Total MWh', 'Revenue (£k)', 'Margin (£/MWh)', 'BM Price', 'Wholesale']])

        # Data rows with sparklines
        vlp_rows = []
        for idx, (_, row) in enumerate(vlp_df.iterrows(), start=1):
            operator = str(row['lead_party_name'])[:20]  # Truncate long names
            total_mwh = row['total_mwh']
            revenue_gbp = row['total_revenue_gbp']
            margin = row.get('avg_margin_per_mwh', 0)
            bm_price = row.get('avg_bm_price', 0)
            wholesale = row.get('avg_wholesale_price', 0)

            # Generate mini sparkline for revenue (just using the value for now)
            # TODO: Pull 30-day trend data for proper sparklines
            spark_revenue = f"=SPARKLINE({{{revenue_gbp/1000:.1f}}})"

            vlp_rows.append([
                idx,  # Rank
                operator,
                f"{total_mwh:,.0f}",
                f"£{revenue_gbp/1000:.1f}k",
                f"£{margin:.2f}",
                f"£{bm_price:.2f}",
                f"£{wholesale:.2f}"
            ])

        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'L56:R65', vlp_rows)

        # Summary stats
        total_vlp_revenue = vlp_df['total_revenue_gbp'].sum()
        total_vlp_mwh = vlp_df['total_mwh'].sum()
        avg_all_margin = total_vlp_revenue / total_vlp_mwh if total_vlp_mwh > 0 else 0

        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'L67:R67',
                          [['TOTAL', f'{len(vlp_df)} operators',
                            f'{total_vlp_mwh:,.0f} MWh',
                            f'£{total_vlp_revenue/1000:.1f}k',
                            f'£{avg_all_margin:.2f}',
                            '', '']])  # Empty cells for BM/Wholesale columns

        logging.info(f"✅ VLP: Top {len(vlp_df)} operators, £{total_vlp_revenue/1000:.1f}k revenue, {total_vlp_mwh:,.0f} MWh")
    else:
        logging.warning("⚠️  VLP Revenue: No data - skipping section")

    # --- ACTIVE OUTAGES Section (G25:K40) ---
    if not outages_df.empty:
        logging.info("📊 Updating Active Outages section...")

        # Map fuel types to emojis with text labels for better visibility
        # VERIFIED FUEL TYPES from bmrs_remit_unavailability (Dec 2025):
        # - Biomass, Fossil Gas, Hydro Pumped Storage, Hydro Water Reservoir
        # - Nuclear, Other, Wind Offshore, Wind Onshore
        # - assetType fallbacks: Production, Consumption, Transmission, Unknown
        fuel_emoji = {
            # Generation types (current data)
            'Nuclear': '⚛️ Nuclear',
            'NUCLEAR': '⚛️ Nuclear',
            'Fossil Gas': '🔥 Fossil Gas',
            'CCGT': '🏭 CCGT',
            'OCGT': '🔥 OCGT',
            'Wind Offshore': '🌬️ Wind Offshore',
            'Wind Onshore': '🌬️ Wind Onshore',
            'Biomass': '🌿 Biomass',
            'Hydro Pumped Storage': '💧 Hydro PS',
            'Hydro Water Reservoir': '💧 Hydro Res',
            'Hydro Run-of-river and poundage': '💧 Hydro RoR',
            'PS': '🔋 Storage',
            'Other': '⚙️ Other',
            # assetType fallbacks (when fuelType is NULL)
            'Production': '⚡ Production',
            'Consumption': '🔌 Consumption',
            'Transmission': '⚡ Transmission',
            'Unknown': '❓ Unknown',
            # Coal (legacy - not in current data but keep for historical)
            'Fossil Hard coal': '🪨 Coal',
            'Coal': '🪨 Coal',
            # Interconnectors - with full names for clarity
            'INTFR': '🇫🇷 IFA',
            'INTIFA2': '🇫🇷 IFA2',
            'INTELEC': '🇫🇷 ElecLink',
            'INTIRL': '🇮🇪 Moyle',
            'INTMOYL': '🇮🇪 Moyle',
            'INTEW': '🇮🇪 E-W',
            'INTGRNL': '🇮🇪 Greenlink',
            'INTNED': '🇳🇱 BritNed',
            'INTNEM': '🇧🇪 Nemo',
            # Legacy codes
            'IFA': '🇫🇷 IFA',
            'IFA2': '🇫🇷 IFA2',
            'Moyle': '🇮🇪 Moyle'
        }

        # Calculate totals
        total_units = len(outages_df)
        total_unavail_mw = outages_df['unavailableCapacity'].sum()
        total_normal_mw = outages_df['normalCapacity'].sum()

        # Title row with totals
        header = f"⚠️ ACTIVE OUTAGES - Top {total_units} by Capacity | Total: {total_units} units | Offline: {total_unavail_mw:,.0f} MW | Normal Capacity: {total_normal_mw:,.0f} MW"
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'G25', [[header]])

        # Column headers
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'G26:K26',
                          [['Asset Name', 'Fuel Type', 'Unavail (MW)', 'Normal (MW)', 'Cause']])

        # Data rows
        outages_rows = []
        for _, row in outages_df.iterrows():
            fuel = str(row['fuel_type'])
            # Get emoji+text display, fallback to fuel type if not mapped
            fuel_display = fuel_emoji.get(fuel, f"⚡ {fuel}")

            outages_rows.append([
                str(row['asset_name']),
                fuel_display,
                int(row['unavailableCapacity']),
                int(row['normalCapacity']),
                str(row['cause'])[:30]  # Truncate long causes
            ])

        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'G27:K41', outages_rows)

        logging.info(f"✅ Outages: {total_units} units, {total_unavail_mw:,.0f} MW offline")
    else:
        logging.warning("⚠️  Active Outages: No data - skipping section")

    # Update interconnector display (G13:I22) from Data_Hidden
    # Get current period interconnector flows from Data_Hidden (columns represent settlement periods)
    logging.info("📊 Updating interconnector display...")

    # Map interconnector names to dashboard rows (Data_Hidden rows 12-21 map to dashboard rows 13-22)
    interconnector_codes = [
        ('INTELEC', '🇫🇷 ElecLink'),
        ('INTEW', '🇮🇪 East-West'),
        ('INTFR', '🇫🇷 IFA'),
        ('INTGRNL', '🇮🇪 Greenlink'),
        ('INTIFA2', '🇫🇷 IFA2'),
        ('INTIRL', '🇮🇪 Moyle'),
        ('INTNED', '🇳🇱 BritNed'),
        ('INTNEM', '🇧🇪 Nemo'),
        ('INTNSL', '🇳🇴 NSL'),
        ('INTVKL', '🇩🇰 Viking Link')
    ]

    # Batch update: Build 3-column array for G13:I22 (names + values + sparklines)
    t_inter_spark = datetime.now()
    interconnector_rows = []
    for inter_code, inter_name in interconnector_codes:
        # Column G: Interconnector name
        # Column H: Current period value (MW)
        inter_current = inter_df[inter_df['interconnector'] == inter_code]
        current_val = inter_current[inter_current['settlementPeriod'] == current_period]['net_flow'].sum()

        # Column I: Google Sheets sparkline formula with positive/negative bars
        # Add 2 spaces between each data point for better bar visibility
        sparkline_data = []
        for period in range(1, current_period + 1):
            period_val = inter_current[inter_current['settlementPeriod'] == period]['net_flow'].sum()
            sparkline_data.append(period_val)
            sparkline_data.append(0)  # Add space
            sparkline_data.append(0)  # Add second space

        # Use positive/negative bar chart: green for import (+), red for export (-)
        sparkline = generate_gs_sparkline_posneg_bar(sparkline_data)

        # Format MW value with sign (+ for import, - for export)
        # CRITICAL: Prefix with ' to prevent Google Sheets from treating "+123 MW" as a formula
        mw_text = f"'+{current_val:.0f} MW" if current_val > 0 else (f"'{current_val:.0f} MW" if current_val < 0 else "'0 MW")

        # 3 columns: G=name, H=MW value, I=sparkline
        interconnector_rows.append([inter_name, mw_text, sparkline])

    logging.info(f"  ⏱️  Generated 10 interconnector sparklines: {(datetime.now()-t_inter_spark).total_seconds():.3f}s")

    # DEBUG: Log what we're sending
    logging.info(f"  🔍 Interconnector rows to send: {len(interconnector_rows)} rows")
    for i, row in enumerate(interconnector_rows[:3], start=13):
        logging.info(f"    Row {i}: cols={len(row)}, name={row[0][:20]}, mw={row[1]}, sparkline_len={len(row[2]) if len(row)>2 else 0}")

    # BYPASS CACHE: Write interconnectors directly due to cache manager issue with 3-column writes
    # The cache manager doesn't properly handle G13:I22 writes (column I gets lost)
    try:
        scopes_inter = ['https://www.googleapis.com/auth/spreadsheets']
        creds_inter = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes_inter)
        gc_inter = gspread.authorize(creds_inter)
        ws_inter = gc_inter.open_by_key(SPREADSHEET_ID).worksheet('Live Dashboard v2')
        # gspread 6.x: values FIRST, then range_name
        ws_inter.update(values=interconnector_rows, range_name='G13:I22', value_input_option='USER_ENTERED')
        logging.info(f"  ✅ Wrote interconnectors directly (G13:I22) - bypassed cache")
    except Exception as e:
        logging.error(f"  ❌ Direct interconnector write failed: {e}")
        # Fallback to cache (will likely fail but try anyway)
        cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'G13:I22', interconnector_rows)

    # Update timestamp in A2
    from datetime import datetime as dt
    current_time = dt.now().strftime('%d/%m/%Y, %H:%M:%S')
    current_period = (dt.now().hour * 2) + (1 if dt.now().minute < 30 else 2)
    timestamp_text = f"Last Updated: {current_time} (v2.0) SP {current_period}"
    cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A2', [[timestamp_text]])

    # CRITICAL: Unmerge H:J in rows 13-22 BEFORE flushing (leftover merges block column I writes)
    logging.info("\n🔓 Unmerging old cell merges...")
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
        gc = gspread.authorize(creds)
        worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet('Live Dashboard v2')

        unmerge_requests = []
        for row_idx in range(12, 22):  # Rows 13-22 (0-indexed: 12-21)
            # Unmerge H:J (columns 7-9)
            unmerge_requests.append({
                'unmergeCells': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1,
                        'startColumnIndex': 7,  # Column H (0-indexed)
                        'endColumnIndex': 10     # Through column J
                    }
                }
            })
            # ALSO unmerge I:J (columns 8-9) separately
            unmerge_requests.append({
                'unmergeCells': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1,
                        'startColumnIndex': 8,  # Column I (0-indexed)
                        'endColumnIndex': 10     # Through column J
                    }
                }
            })

        if unmerge_requests:
            worksheet.spreadsheet.batch_update({'requests': unmerge_requests})
            logging.info(f"  ✅ Unmerged H:J and I:J in rows 13-22 ({len(unmerge_requests)} ranges)")
    except Exception as e:
        logging.warning(f"  ⚠️  Unmerge skipped: {e}")

    # Flush all updates
    logging.info("\n📤 Flushing all updates to Google Sheets...")
    t_flush = datetime.now()
    cache.flush_all()
    logging.info(f"  ⏱️  Sheets API flush: {(datetime.now()-t_flush).total_seconds():.1f}s")

    # Apply cell merges for header only (K12:S12 - CONSOLIDATED LAYOUT)
    logging.info("\n🔗 Applying cell merges for consolidated header...")
    try:
        # Re-use worksheet object from unmerge step above

        # Merge K12:S12 for header (9 columns wide)
        try:
            worksheet.merge_cells('K12:S12', merge_type='MERGE_ALL')
            logging.info("  ✅ Merged K12:S12 (header - 9 columns)")
        except Exception as e:
            logging.info(f"  ℹ️  K12:S12 already merged (skipped)")

        # Merge N:S sparkline columns for each KPI row (rows: 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
        kpi_rows = [13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
        merged_count = 0
        for row in kpi_rows:
            try:
                worksheet.merge_cells(f'N{row}:S{row}', merge_type='MERGE_ALL')
                merged_count += 1
            except:
                pass  # Already merged
        logging.info(f"  ✅ Merged {merged_count} sparkline ranges (N:S for rows {kpi_rows})")

        # Set row heights for better spacing using batch_update
        # Interconnectors (G12=50px header, G13:I22=60px data), K12=60px header, KPI rows (13,15,17...)=80px each, empty spacer rows=10px
        row_height_requests = []

        # Interconnector header row (G12) = 50px
        row_height_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': worksheet.id,
                    'dimension': 'ROWS',
                    'startIndex': 11,  # Row 12 (0-indexed)
                    'endIndex': 12
                },
                'properties': {'pixelSize': 50},
                'fields': 'pixelSize'
            }
        })

        # Interconnector data rows (G13:I22) = 60px each for BIGGER EMOJIS
        for row in range(13, 23):  # Rows 13-22
            row_height_requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': worksheet.id,
                        'dimension': 'ROWS',
                        'startIndex': row - 1,  # 0-indexed
                        'endIndex': row
                    },
                    'properties': {'pixelSize': 60},
                    'fields': 'pixelSize'
                }
            })

        # Combined KPIs Header row (K12) = 60px (already set above but reinforced)
        row_height_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': worksheet.id,
                    'dimension': 'ROWS',
                    'startIndex': 11,  # Row 12 (0-indexed)
                    'endIndex': 12
                },
                'properties': {'pixelSize': 60},
                'fields': 'pixelSize'
            }
        })

        # KPI data rows (13, 15, 17, 19, 21, 23, 25, 27, 29, 31) = 80px each
        for row in kpi_rows:
            row_height_requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': worksheet.id,
                        'dimension': 'ROWS',
                        'startIndex': row - 1,  # 0-indexed
                        'endIndex': row
                    },
                    'properties': {'pixelSize': 80},
                    'fields': 'pixelSize'
                }
            })

        # Spacer rows ONLY in KPI section (24, 26, 28, 30) = 10px each
        # NOTE: Rows 14,16,18,20,22 are DATA rows (fuel generation), NOT spacers!
        spacer_rows = [24, 26, 28, 30]
        for row in spacer_rows:
            row_height_requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': worksheet.id,
                        'dimension': 'ROWS',
                        'startIndex': row - 1,  # 0-indexed
                        'endIndex': row
                    },
                    'properties': {'pixelSize': 10},
                    'fields': 'pixelSize'
                }
            })

        # Active Outages header row (G25) = 50px
        row_height_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': worksheet.id,
                    'dimension': 'ROWS',
                    'startIndex': 24,  # Row 25 (0-indexed)
                    'endIndex': 25
                },
                'properties': {'pixelSize': 50},
                'fields': 'pixelSize'
            }
        })

        # Active Outages column headers row (G26) = 40px
        row_height_requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': worksheet.id,
                    'dimension': 'ROWS',
                    'startIndex': 25,  # Row 26 (0-indexed)
                    'endIndex': 26
                },
                'properties': {'pixelSize': 40},
                'fields': 'pixelSize'
            }
        })

        # Active Outages data rows (G27:K41) = 60px each for BIGGER EMOJIS
        for row in range(27, 42):  # Rows 27-41
            row_height_requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': worksheet.id,
                        'dimension': 'ROWS',
                        'startIndex': row - 1,  # 0-indexed
                        'endIndex': row
                    },
                    'properties': {'pixelSize': 60},
                    'fields': 'pixelSize'
                }
            })

        worksheet.spreadsheet.batch_update({'requests': row_height_requests})
        logging.info(f"  ✅ Set row heights: Interconnectors=60px, header=60px, KPIs=80px, spacers=10px, Outages=60px")

        # Highlight OCGT (row 19), COAL (row 20), OIL (row 21) in bold red when they ARE generating
        # These are legacy/emergency fuels - highlighting alerts when they're in use (unusual event)
        # COAL last used: May 2025 (0.6 years ago, 449 active days since 2022)
        # OIL last used: May 2025 (0.6 years ago, only 9 active days since 2023)
        # OCGT: Still used for peak demand (637 MW peak, 38 days in last 90)
        legacy_gen_format_requests = []
        for row_idx, fuel_type in [(19, 'OCGT'), (20, 'COAL'), (21, 'OIL')]:
            # Check if this fuel IS generating (alert condition)
            fuel_val = fuel_current[fuel_current['fuelType'] == fuel_type]['total_generation'].sum()
            if fuel_val > 10:  # More than 10 MW = actively generating
                # Format columns A, B, C, D (fuel name, MW, %, sparkline) in bold red
                legacy_gen_format_requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': worksheet.id,
                            'startRowIndex': row_idx - 1,  # 0-indexed
                            'endRowIndex': row_idx,
                            'startColumnIndex': 0,  # Column A
                            'endColumnIndex': 4     # Columns A-D
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'foregroundColor': {'red': 0.8, 'green': 0.0, 'blue': 0.0},
                                    'bold': True,
                                    'fontSize': 11
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat'
                    }
                })

        if legacy_gen_format_requests:
            worksheet.spreadsheet.batch_update({'requests': legacy_gen_format_requests})
            logging.info(f"  🔴 ALERT: {len(legacy_gen_format_requests)} legacy fuels actively generating (highlighted in bold red)")

    except Exception as e:
        logging.warning(f"  ⚠️  Cell merge/formatting failed (non-critical): {e}")

    stats = cache.get_stats()
    total_requests = sum(stats.get('per_account_requests', stats.get('request_counts', [0])))
    total_accounts = stats.get('total_accounts', len(stats.get('per_account_requests', [1])))
    logging.info(f"📊 Cache Stats: {total_requests} total requests across {total_accounts} accounts")

    logging.info("\n✅ COMPLETE UPDATE FINISHED")
    logging.info(f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
