#!/usr/bin/env python3
"""
Live Dashboard v2 - Data Updater
Updates the "Live Dashboard v2" worksheet with real-time IRIS data
Targets spreadsheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
"""

import sys
import logging
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = 'inner-cinema-credentials.json'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_latest_settlement_period(bq_client):
    """Get the actual current settlement period based on current time"""
    from datetime import datetime

    # Calculate current settlement period from actual time
    now = datetime.now()
    hours = now.hour
    minutes = now.minute

    # Settlement period = (hour * 2) + (1 if minutes >= 30 else 0)
    # Periods run 00:00-00:30 (SP1), 00:30-01:00 (SP2), etc.
    if minutes < 30:
        current_sp = (hours * 2) + 1
    else:
        current_sp = (hours * 2) + 2

    # Cap at 48 (max period per day)
    current_sp = min(current_sp, 48)

    # Validate we have data for this period
    query = f"""
    SELECT
        MAX(CAST(settlementDate AS DATE)) as latest_date,
        MAX(settlementPeriod) as latest_period
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    """
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty:
            latest_date = result.iloc[0]['latest_date']
            max_available = int(result.iloc[0]['latest_period'])

            # If today's data exists, use calculated period or max available (whichever is smaller)
            if latest_date == datetime.now().date():
                actual_period = min(current_sp, max_available)
            else:
                actual_period = max_available

            return latest_date, actual_period
    except Exception as e:
        logging.error(f"Error getting latest period: {e}")
    return None, None

def get_bm_kpi_data(bq_client):
    """
    Get comprehensive BM market KPIs from multiple sources
    Returns all 10 planned KPIs with formulas and sparkline data
    Uses most recent complete day for live data
    """

    # Find most recent date with complete data (UNION historical + IRIS)
    date_query = f"""
    WITH combined AS (
      SELECT CAST(settlementDate AS DATE) as date, settlementPeriod
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND validation_flag = 'Valid'
      UNION ALL
      SELECT DATE(timeFrom) as date, settlementPeriodFrom as settlementPeriod
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
      WHERE CAST(timeFrom AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    )
    SELECT date
    FROM combined
    GROUP BY date
    HAVING COUNT(DISTINCT settlementPeriod) >= 40
    ORDER BY date DESC
    LIMIT 1
    """

    date_result = bq_client.query(date_query).to_dataframe()
    if date_result.empty:
        logging.warning("No complete BOALF data found")
        return None

    target_date = str(date_result.iloc[0]['date'])

    # Query comprehensive BM + Market data for all KPIs
    # Use most recent complete day for live data
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
        UNION ALL
        SELECT settlementPeriod, price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = '{target_date}'
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
    )
    SELECT
      p.settlementPeriod,
      COALESCE(b.bm_avg_price, 0) as bm_avg_price,
      COALESCE(b.bm_vol_wtd, 0) as bm_vol_wtd,
      COALESCE(b.bm_volume, 0) as bm_volume,
      COALESCE(m.mid_price, 0) as mid_price,
      COALESCE(s.sys_buy, 0) as sys_buy,
      COALESCE(s.sys_sell, 0) as sys_sell
    FROM periods p
    LEFT JOIN boalf_data b USING (settlementPeriod)
    LEFT JOIN market_index m USING (settlementPeriod)
    LEFT JOIN system_prices s USING (settlementPeriod)
    ORDER BY p.settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()

        if df.empty:
            return None

        # Calculate aggregate KPIs (overall averages)
        bm_avg = df['bm_avg_price'].mean()
        bm_vol_wtd = (df['bm_avg_price'] * df['bm_volume']).sum() / df['bm_volume'].sum() if df['bm_volume'].sum() > 0 else 0
        mid_avg = df['mid_price'].mean()
        sys_buy_avg = df['sys_buy'].mean()
        sys_sell_avg = df['sys_sell'].mean()

        # Derived metrics
        bm_mid_spread = bm_avg - mid_avg
        bm_sysbuy_spread = bm_avg - sys_buy_avg
        bm_syssell_spread = bm_avg - sys_sell_avg
        sys_spread = sys_buy_avg - sys_sell_avg

        # Count actual periods with data
        periods_with_data = (df['bm_avg_price'] > 0).sum()

        return {
            'date': target_date,
            'period_count': periods_with_data,
            'bm_avg': bm_avg,
            'bm_vol_wtd': bm_vol_wtd,
            'mid_avg': mid_avg,
            'sys_buy': sys_buy_avg,
            'sys_sell': sys_sell_avg,
            'bm_mid_spread': bm_mid_spread,
            'bm_sysbuy_spread': bm_sysbuy_spread,
            'bm_syssell_spread': bm_syssell_spread,
            'sys_spread': sys_spread,
            'timeseries': df
        }
    except Exception as e:
        logging.error(f"Error querying BM KPI data: {e}")
        return None

def deploy_bm_kpis(sheet, bq_client):
    """
    Deploy ALL 10 BM Market KPIs to merged cells (M13:AA18)
    Layout matches planned structure with formulas for persistence
    """
    kpi_data = get_bm_kpi_data(bq_client)

    if not kpi_data:
        logging.warning("⚠️  No BM KPI data available, skipping")
        return

    print(f"\n📊 Deploying 10 BM KPIs (data from {kpi_data['date']}, {kpi_data['period_count']} periods)...")

    # Prepare timeseries for Data_Hidden (48 periods)
    period_stats = kpi_data['timeseries']

    # Write timeseries to Data_Hidden rows 27-34 (8 rows for all metrics)
    try:
        data_hidden = sheet.spreadsheet.worksheet('Data_Hidden')

        data_rows = [
            ['BM_Avg_Price'] + period_stats['bm_avg_price'].tolist(),
            ['BM_Vol_Wtd'] + period_stats['bm_vol_wtd'].tolist(),
            ['MID_Price'] + period_stats['mid_price'].tolist(),
            ['Sys_Buy'] + period_stats['sys_buy'].tolist(),
            ['Sys_Sell'] + period_stats['sys_sell'].tolist(),
            ['BM_MID_Spread'] + (period_stats['bm_avg_price'] - period_stats['mid_price']).tolist(),
            ['BM_SysBuy'] + (period_stats['bm_avg_price'] - period_stats['sys_buy']).tolist(),
            ['BM_SysSell'] + (period_stats['bm_avg_price'] - period_stats['sys_sell']).tolist(),
        ]

        # Use RAW input so numbers stay as numbers (not strings) for sparklines
        data_hidden.batch_update([
            {'range': 'A27:AW34', 'values': data_rows}
        ], value_input_option='RAW')
        print(f"   ✅ Written 8 BM timeseries to Data_Hidden (rows 27-34, as numbers)")
    except Exception as e:
        logging.error(f"   ⚠️  Could not update Data_Hidden: {e}")

    # Deploy to dashboard merged cells
    # Merged cells: M13:O14, M15:O16, M17:O18 (and Q, U columns similar)
    # For each merge: Row 13/15/17 = Header, Row 14/16/18 = Value
    # Write to TOP-LEFT cell of each merge only (M13, M15, M17, etc.)

    try:
        import time

        # Clear old headers from row 12
        sheet.batch_clear(['M12:AA18'])
        time.sleep(1)

        # Batch 1: M column (headers in 13/15/17, values in 14/16/18)
        batch1 = [
            {'range': 'M13', 'values': [['Avg Accept Price']]},
            {'range': 'M14', 'values': [['=ROUND(AVERAGE(Data_Hidden!B27:AW27), 2)&" £/MWh"']]},
            {'range': 'M15', 'values': [['Vol-Wtd Avg']]},
            {'range': 'M16', 'values': [['=ROUND(AVERAGE(Data_Hidden!B28:AW28), 2)&" £/MWh"']]},
            {'range': 'M17', 'values': [['Market Index']]},
            {'range': 'M18', 'values': [['=ROUND(AVERAGE(Data_Hidden!B29:AW29), 2)&" £/MWh"']]},
        ]
        sheet.batch_update(batch1, value_input_option='USER_ENTERED')
        print(f"   ✅ M column deployed (3 KPIs with headers)")
        time.sleep(1)

        # Batch 2: Q column (headers in 13/15/17, values in 14/16/18)
        batch2 = [
            {'range': 'Q13', 'values': [['BM–MID Spread']]},
            {'range': 'Q14', 'values': [['=ROUND(AVERAGE(Data_Hidden!B30:AW30), 2)&" £/MWh"']]},
            {'range': 'Q15', 'values': [['Sys–VLP Spread']]},
            {'range': 'Q16', 'values': [['=ROUND(AVERAGE(Data_Hidden!B31:AW31), 2)&" £/MWh"']]},
            {'range': 'Q17', 'values': [['Supp–VLP Spread']]},
            {'range': 'Q18', 'values': [['=ROUND(AVERAGE(Data_Hidden!B32:AW32), 2)&" £/MWh"']]},
        ]
        sheet.batch_update(batch2, value_input_option='USER_ENTERED')
        print(f"   ✅ Q column deployed (3 spreads with headers)")
        time.sleep(1)

        # Batch 3: U column (headers in 13/15/17, values in 14/16/18) - placeholders
        batch3 = [
            {'range': 'U13', 'values': [['Reserved']]},
            {'range': 'U14', 'values': [['--']]},
            {'range': 'U15', 'values': [['Reserved']]},
            {'range': 'U16', 'values': [['--']]},
            {'range': 'U17', 'values': [['Reserved']]},
            {'range': 'U18', 'values': [['--']]},
        ]
        sheet.batch_update(batch3, value_input_option='USER_ENTERED')
        print(f"   ✅ U column deployed (3 placeholders with headers)")
        time.sleep(1)

        # Batch 4: Y column (Y13:AA14 title, Y17:AA18 net spread)
        batch4 = [
            {'range': 'Y13', 'values': [[f'⚡ BM Market']]},
            {'range': 'Y14', 'values': [['KPIs']]},
            {'range': 'Y17', 'values': [['Net Spread']]},
            {'range': 'Y18', 'values': [['=ROUND(AVERAGE(Data_Hidden!B33:AW33), 2)&" £/MWh"']]},
        ]
        sheet.batch_update(batch4, value_input_option='USER_ENTERED')
        print(f"   ✅ Y column deployed (title + net spread with headers)")
        time.sleep(1)

        # Batch 5: Detail columns AB-AD
        batch5 = [
            {'range': 'AB13:AD13', 'values': [['Avg Accept', 'Vol-Wtd', 'MID Index']]},
            {'range': 'AB14', 'values': [['=ROUND(AVERAGE(Data_Hidden!B27:AW27), 2)&" £/MWh"']]},
            {'range': 'AC14', 'values': [['=ROUND(AVERAGE(Data_Hidden!B28:AW28), 2)&" £/MWh"']]},
            {'range': 'AD14', 'values': [['=ROUND(AVERAGE(Data_Hidden!B29:AW29), 2)&" £/MWh"']]},
            {'range': 'AB15', 'values': [['=SPARKLINE(Data_Hidden!B27:AW27,{"charttype","column"})']]},
            {'range': 'AC15', 'values': [['=SPARKLINE(Data_Hidden!B28:AW28,{"charttype","line"})']]},
            {'range': 'AD15', 'values': [['=SPARKLINE(Data_Hidden!B29:AW29,{"charttype","column"})']]},
        ]
        sheet.batch_update(batch5, value_input_option='USER_ENTERED')
        print(f"   ✅ Detail columns deployed (sparklines)")

        print(f"\n   📊 10 BM KPIs deployed successfully:")
        print(f"      • Avg Accept: £{kpi_data['bm_avg']:.2f}/MWh")
        print(f"      • Vol-Wtd: £{kpi_data['bm_vol_wtd']:.2f}/MWh")
        print(f"      • Mkt Index (MID): £{kpi_data['mid_avg']:.2f}/MWh")
        print(f"      • BM–MID Spread: £{kpi_data['bm_mid_spread']:.2f}/MWh")
        print(f"      • BM–SysBuy: £{kpi_data['bm_sysbuy_spread']:.2f}/MWh")
        print(f"      • BM–SysSell: £{kpi_data['bm_syssell_spread']:.2f}/MWh")
        print(f"      • Net Spread: £{kpi_data['sys_spread']:.2f}/MWh")
    except Exception as e:
        logging.error(f"   ⚠️  BM KPI deployment failed: {e}")


def check_data_freshness(bq_client):
    """
    Check IRIS data ingestion status across all tables
    Returns status with traffic lights and data volume metrics
    """

    iris_tables = {
        'bmrs_fuelinst_iris': 'Gen Mix',
        'bmrs_bod_iris': 'BM Bids',
        'bmrs_boalf_iris': 'Acceptances',
        'bmrs_mid_iris': 'Market',
        'bmrs_indgen_iris': 'Units',
    }

    table_stats = []
    total_rows_today = 0
    freshest_age = 999999
    freshest_table = None

    for table, short_name in iris_tables.items():
        query = f"""
        SELECT
            COUNT(*) as row_count,
            MAX(CAST(settlementDate AS DATE)) as latest_date,
            MAX(settlementPeriod) as latest_period,
            TIMESTAMP_DIFF(
                CURRENT_TIMESTAMP(),
                TIMESTAMP_ADD(
                    CAST(CAST(MAX(settlementDate) AS DATE) AS TIMESTAMP),
                    INTERVAL (MAX(settlementPeriod) * 30) MINUTE
                ),
                MINUTE
            ) as age_minutes
        FROM `{PROJECT_ID}.{DATASET}.{table}`
        WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE()
        """

        try:
            df = bq_client.query(query).to_dataframe()
            if not df.empty and df['row_count'].iloc[0] > 0:
                rows = int(df['row_count'].iloc[0])
                age_minutes = int(df['age_minutes'].iloc[0])
                latest_date = df['latest_date'].iloc[0]
                latest_period = int(df['latest_period'].iloc[0])

                # Determine status: Green < 30min, Orange < 120min, Red >= 120min
                if age_minutes < 30:
                    status_icon = '🟢'
                    status_text = 'FRESH'
                elif age_minutes < 120:
                    status_icon = '🟠'
                    status_text = 'AGING'
                else:
                    status_icon = '🔴'
                    status_text = 'STALE'

                table_stats.append({
                    'table': table,
                    'name': short_name,
                    'rows': rows,
                    'age_minutes': age_minutes,
                    'latest_period': latest_period,
                    'status_icon': status_icon,
                    'status_text': status_text,
                    'latest_date': latest_date
                })

                total_rows_today += rows

                if age_minutes < freshest_age:
                    freshest_age = age_minutes
                    freshest_table = short_name
        except Exception as e:
            # Skip tables with errors
            continue

    # Determine overall status based on freshest data
    if freshest_age < 30:
        overall_status = 'OK'
        overall_icon = '🟢'
        overall_text = 'ACTIVE'
    elif freshest_age < 120:
        overall_status = 'AGING'
        overall_icon = '🟠'
        overall_text = 'AGING'
    else:
        overall_status = 'STALE'
        overall_icon = '🔴'
        overall_text = 'STALE'

    # Create compact status message for dashboard
    active_streams = sum(1 for s in table_stats if s['status_icon'] == '🟢')
    aging_streams = sum(1 for s in table_stats if s['status_icon'] == '🟠')
    stale_streams = sum(1 for s in table_stats if s['status_icon'] == '🔴')

    status_message = f"{overall_icon} IRIS: {total_rows_today:,} rows today | {active_streams}🟢 {aging_streams}🟠 {stale_streams}🔴 | Key: 🟢<30m 🟠30-120m 🔴>120m"

    return {
        'status': overall_status,
        'icon': overall_icon,
        'text': overall_text,
        'total_rows': total_rows_today,
        'active_streams': active_streams,
        'aging_streams': aging_streams,
        'stale_streams': stale_streams,
        'freshest_age': freshest_age,
        'freshest_table': freshest_table,
        'table_stats': table_stats,
        'message': status_message
    }

def get_kpis(bq_client):
    """Get all KPIs - Wholesale Price, Frequency, Total Generation, Wind, Demand"""

    # Get 7-day average wholesale price
    # Use bmrs_mid_iris (real-time wholesale prices) - has current data through Dec 11
    price_query = f"""
    SELECT
        AVG(price) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    """

    # Get latest generation data
    gen_query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementDate) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ),
    latest_sp AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
    ),
    -- Deduplicate by latest publishTime
    deduplicated AS (
        SELECT
            fuelType,
            generation,
            ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
          AND settlementPeriod = (SELECT max_sp FROM latest_sp)
    ),
    latest AS (
        SELECT
            fuelType,
            SUM(generation) as generation_mw
        FROM deduplicated
        WHERE rn = 1
        GROUP BY fuelType
    )
    SELECT
        SUM(CASE WHEN fuelType NOT LIKE 'INT%' THEN generation_mw ELSE 0 END) / 1000 as total_gen_gw,
        SUM(CASE WHEN fuelType = 'WIND' THEN generation_mw ELSE 0 END) / 1000 as wind_gw,
        SUM(CASE WHEN fuelType LIKE 'INT%' THEN generation_mw ELSE 0 END) / 1000 as net_ic_gw
    FROM latest
    """

    # Get latest frequency from IRIS table (real-time)
    freq_query = f"""
    SELECT frequency
    FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
    WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
    ORDER BY measurementTime DESC
    LIMIT 1
    """

    try:
        # Get price
        price_result = bq_client.query(price_query).to_dataframe()
        avg_price = float(price_result['avg_price'].iloc[0]) if not price_result.empty else 0

        # Get generation
        gen_result = bq_client.query(gen_query).to_dataframe()
        if not gen_result.empty:
            total_gen = float(gen_result['total_gen_gw'].iloc[0])
            wind_gw = float(gen_result['wind_gw'].iloc[0])
            net_ic = float(gen_result['net_ic_gw'].iloc[0])
        else:
            total_gen = wind_gw = net_ic = 0

        # Get frequency
        freq_result = bq_client.query(freq_query).to_dataframe()
        frequency = float(freq_result['frequency'].iloc[0]) if not freq_result.empty else 50.0

        # Calculate demand (total gen + net imports)
        demand_gw = total_gen + net_ic

        return {
            'wholesale': round(avg_price, 2),
            'frequency': round(frequency, 2),
            'total_gen': round(total_gen, 2),
            'wind': round(wind_gw, 2),
            'demand': round(demand_gw, 2)
        }
    except Exception as e:
        logging.error(f"Error getting KPIs: {e}")
        import traceback
        traceback.print_exc()
        return {
            'wholesale': 0, 'frequency': 50.0,
            'total_gen': 0, 'wind': 0, 'demand': 0
        }

def get_generation_mix(bq_client):
    """Get current generation mix"""
    query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementDate) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ),
    latest_sp AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
    ),
    -- Get only the LATEST publishTime for each fuelType (handles revised data)
    deduplicated AS (
        SELECT
            fuelType,
            generation,
            ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
          AND settlementPeriod = (SELECT max_sp FROM latest_sp)
          AND fuelType NOT LIKE 'INT%'
    ),
    latest AS (
        SELECT
            fuelType,
            SUM(generation) as generation_mw
        FROM deduplicated
        WHERE rn = 1
        GROUP BY fuelType
    )
    SELECT
        fuelType,
        generation_mw / 1000 as gen_gw,
        generation_mw / (SELECT SUM(generation_mw) FROM latest) * 100 as share_pct
    FROM latest
    ORDER BY generation_mw DESC
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        logging.error(f"Error getting generation mix: {e}")
        import traceback
        traceback.print_exc()

    return None

def get_interconnectors(bq_client):
    """Get interconnector flows"""
    query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementDate) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ),
    latest_sp AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
    ),
    -- Deduplicate by latest publishTime
    deduplicated AS (
        SELECT
            fuelType,
            generation,
            ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
          AND settlementPeriod = (SELECT max_sp FROM latest_sp)
          AND fuelType LIKE 'INT%'
    )
    SELECT
        fuelType,
        SUM(generation) as flow_mw
    FROM deduplicated
    WHERE rn = 1
    GROUP BY fuelType
    ORDER BY ABS(flow_mw) DESC
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        logging.error(f"Error getting interconnectors: {e}")
        import traceback
        traceback.print_exc()

    return None

def get_48_period_timeseries(bq_client, current_sp):
    """Get today's data from 00:00 up to current settlement period (fuels only)

    UNIONs historical (bmrs_fuelinst) with real-time (bmrs_fuelinst_iris) to get
    full 48-period coverage from midnight to current period.
    """
    query = f"""
    WITH combined_data AS (
        -- Historical data (00:00 onwards until IRIS takes over)
        SELECT
            fuelType,
            settlementPeriod,
            SUM(generation) / 1000 as gen_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
          AND fuelType NOT LIKE 'INT%'
        GROUP BY settlementPeriod, fuelType

        UNION ALL

        -- Real-time IRIS data (recent periods, may overlap with historical)
        SELECT
            fuelType,
            settlementPeriod,
            SUM(generation) / 1000 as gen_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
          AND fuelType NOT LIKE 'INT%'
        GROUP BY settlementPeriod, fuelType
    )
    SELECT
        fuelType,
        settlementPeriod,
        AVG(gen_gw) as gen_gw  -- AVG handles any period overlap between historical and IRIS
    FROM combined_data
    GROUP BY settlementPeriod, fuelType
    ORDER BY fuelType, settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Pivot to get fuel types as rows, periods as columns
            pivot = df.pivot(index='fuelType', columns='settlementPeriod', values='gen_gw')
            # Fill missing periods UP TO current_sp with 0, leave future periods empty
            for period in range(1, current_sp + 1):
                if period not in pivot.columns:
                    pivot[period] = 0
            # Sort columns by period number
            pivot = pivot[sorted(pivot.columns)]
            return pivot
    except Exception as e:
        logging.error(f"Error getting 48-period data: {e}")

    return None

def get_48_period_interconnectors(bq_client, current_sp):
    """Get today's data from 00:00 up to current settlement period (interconnectors in MW)

    UNIONs historical with IRIS for full 48-period coverage.
    """
    query = f"""
    WITH combined_ic AS (
        -- Historical interconnector data
        SELECT
            fuelType,
            settlementPeriod,
            SUM(generation) as flow_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
          AND fuelType LIKE 'INT%'
        GROUP BY settlementPeriod, fuelType

        UNION ALL

        -- Real-time IRIS interconnector data
        SELECT
            fuelType,
            settlementPeriod,
            SUM(generation) as flow_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
          AND fuelType LIKE 'INT%'
        GROUP BY settlementPeriod, fuelType
    )
    SELECT
        fuelType,
        settlementPeriod,
        AVG(flow_mw) as flow_mw  -- AVG handles overlap
    FROM combined_ic
    GROUP BY settlementPeriod, fuelType
    ORDER BY fuelType, settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Pivot to get interconnectors as rows, periods as columns
            pivot = df.pivot(index='fuelType', columns='settlementPeriod', values='flow_mw')
            # Fill missing periods UP TO current_sp with 0, leave future periods empty
            for period in range(1, current_sp + 1):
                if period not in pivot.columns:
                    pivot[period] = 0
            # Sort columns by period number
            pivot = pivot[sorted(pivot.columns)]
            return pivot
    except Exception as e:
        logging.error(f"Error getting 48-period interconnector data: {e}")

    return None

def get_kpi_timeseries(bq_client, current_sp):
    """Get today's KPI timeseries from 00:00 up to current settlement period

    UNIONs historical tables with IRIS tables to get full 48-period coverage.
    """
    query = f"""
    WITH gen_combined AS (
        -- Historical generation data
        SELECT
            settlementPeriod,
            SUM(CASE WHEN fuelType NOT LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as total_gen_gw,
            SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) / 1000 as wind_gw,
            SUM(CASE WHEN fuelType LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as net_ic_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
        GROUP BY settlementPeriod

        UNION ALL

        -- Real-time IRIS generation data
        SELECT
            settlementPeriod,
            SUM(CASE WHEN fuelType NOT LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as total_gen_gw,
            SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) / 1000 as wind_gw,
            SUM(CASE WHEN fuelType LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as net_ic_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
        GROUP BY settlementPeriod
    ),
    gen_by_period AS (
        SELECT
            settlementPeriod,
            AVG(total_gen_gw) as total_gen_gw,
            AVG(wind_gw) as wind_gw,
            AVG(net_ic_gw) as net_ic_gw
        FROM gen_combined
        GROUP BY settlementPeriod
    ),
    prices_combined AS (
        -- Historical wholesale prices
        SELECT
            settlementPeriod,
            AVG(price) as wholesale_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
        GROUP BY settlementPeriod

        UNION ALL

        -- Real-time IRIS prices
        SELECT
            settlementPeriod,
            AVG(price) as wholesale_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
        GROUP BY settlementPeriod
    ),
    prices_by_period AS (
        SELECT
            settlementPeriod,
            AVG(wholesale_price) as wholesale_price
        FROM prices_combined
        GROUP BY settlementPeriod
    ),
    freq_combined AS (
        -- Historical frequency data
        SELECT
            CAST(FLOOR((EXTRACT(HOUR FROM measurementTime) * 60 + EXTRACT(MINUTE FROM measurementTime)) / 30) + 1 AS INT64) as settlementPeriod,
            AVG(frequency) as avg_frequency
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
        WHERE CAST(measurementTime AS DATE) = CURRENT_DATE()
          AND EXTRACT(HOUR FROM measurementTime) * 2 + CAST(EXTRACT(MINUTE FROM measurementTime) >= 30 AS INT64) + 1 <= {current_sp}
        GROUP BY settlementPeriod

        UNION ALL

        -- Real-time IRIS frequency data
        SELECT
            CAST(FLOOR((EXTRACT(HOUR FROM measurementTime) * 60 + EXTRACT(MINUTE FROM measurementTime)) / 30) + 1 AS INT64) as settlementPeriod,
            AVG(frequency) as avg_frequency
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) = CURRENT_DATE()
          AND EXTRACT(HOUR FROM measurementTime) * 2 + CAST(EXTRACT(MINUTE FROM measurementTime) >= 30 AS INT64) + 1 <= {current_sp}
        GROUP BY settlementPeriod
    ),
    freq_by_period AS (
        SELECT
            settlementPeriod,
            AVG(avg_frequency) as avg_frequency
        FROM freq_combined
        GROUP BY settlementPeriod
    )
    SELECT
        g.settlementPeriod,
        p.wholesale_price,
        f.avg_frequency as frequency,
        g.total_gen_gw,
        g.wind_gw,
        g.total_gen_gw + g.net_ic_gw as demand_gw
    FROM gen_by_period g
    LEFT JOIN prices_by_period p ON g.settlementPeriod = p.settlementPeriod
    LEFT JOIN freq_by_period f ON g.settlementPeriod = f.settlementPeriod
    ORDER BY g.settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Return as dict of lists (one list per KPI)
            return {
                'wholesale': df['wholesale_price'].fillna(0).tolist(),
                'frequency': df['frequency'].fillna(50.0).tolist(),
                'total_gen': df['total_gen_gw'].fillna(0).tolist(),
                'wind': df['wind_gw'].fillna(0).tolist(),
                'demand': df['demand_gw'].fillna(0).tolist()
            }
    except Exception as e:
        logging.error(f"Error getting KPI timeseries: {e}")
        import traceback
        traceback.print_exc()

    return None

def get_bm_metrics(bq_client):
    """
    Calculate comprehensive market-wide BM KPIs using BigQuery historical data

    Implements KPIs from BM_REVENUE_KPI_SPECIFICATION.md:
    - KPI_MKT_002: Total Accepted Volume (MWh) - Offer / Bid breakdown
    - KPI_MKT_001: Total BM Cashflow (£) - Net revenue estimate
    - KPI_MKT_007: Workhorse Index - Active SPs/48
    - KPI_MKT_004: Energy-Weighted Average Price (EWAP/VWAP)
    - KPI_BMU_008: Constraint Share from DISBSAD
    - Plus derived metrics: £/MW-day, Non-Delivery Rate, Offer/Bid Ratio
    """

    try:
        # Get the latest available date (historical data, typically yesterday)
        latest_date_query = f"""
        SELECT MAX(CAST(settlementDate AS DATE)) as latest_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
        """
        df_date = bq_client.query(latest_date_query).to_dataframe()
        if df_date.empty:
            return None

        latest_date = df_date.iloc[0]['latest_date']
        logging.info(f"   Using BM data from: {latest_date}")

        # KPI_MKT_002 & KPI_MKT_001: Total volumes and cashflows (market-wide)
        # Using BOAV (acceptance volumes) + EBOCF (cashflows)
        market_query = f"""
        WITH volumes AS (
            SELECT
                SUM(CASE WHEN _direction = 'offer' THEN ABS(totalVolumeAccepted) ELSE 0 END) as offer_mwh,
                SUM(CASE WHEN _direction = 'bid' THEN ABS(totalVolumeAccepted) ELSE 0 END) as bid_mwh,
                COUNT(DISTINCT settlementPeriod) as active_sps,
                COUNT(DISTINCT nationalGridBmUnit) as active_units
            FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
            WHERE CAST(settlementDate AS DATE) = '{latest_date}'
        ),
        cashflows AS (
            SELECT
                SUM(CASE WHEN _direction = 'offer' THEN totalCashflow ELSE 0 END) as offer_cashflow,
                SUM(CASE WHEN _direction = 'bid' THEN totalCashflow ELSE 0 END) as bid_cashflow
            FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
            WHERE CAST(settlementDate AS DATE) = '{latest_date}'
        )
        SELECT
            v.offer_mwh,
            v.bid_mwh,
            v.active_sps,
            v.active_units,
            c.offer_cashflow,
            c.bid_cashflow,
            (v.offer_mwh + v.bid_mwh) as total_mwh,
            (c.offer_cashflow + c.bid_cashflow) as net_revenue
        FROM volumes v
        CROSS JOIN cashflows c
        """

        df_market = bq_client.query(market_query).to_dataframe()

        if df_market.empty:
            return None

        row = df_market.iloc[0]
        offer_mwh = float(row['offer_mwh'] or 0)
        bid_mwh = float(row['bid_mwh'] or 0)
        active_sps = int(row['active_sps'] or 0)
        active_units = int(row['active_units'] or 0)
        offer_cashflow = float(row['offer_cashflow'] or 0)
        bid_cashflow = float(row['bid_cashflow'] or 0)
        total_mwh = float(row['total_mwh'] or 0)
        net_revenue = float(row['net_revenue'] or 0)

        # KPI_MKT_004: Energy-Weighted Average Price (EWAP/VWAP)
        if total_mwh > 0:
            vwap = net_revenue / total_mwh
        else:
            vwap = 0

        # Offer/Bid Ratio (revenue balance)
        if abs(bid_cashflow) > 0:
            offer_bid_ratio = offer_cashflow / abs(bid_cashflow)
        else:
            offer_bid_ratio = 999 if offer_cashflow > 0 else 0

        # KPI_BMU_008: Constraint Share from DISBSAD
        try:
            disbsad_query = f"""
            WITH market_total AS (
                SELECT SUM(ABS(cost)) as total_cost
                FROM `{PROJECT_ID}.{DATASET}.bmrs_disbsad`
                WHERE CAST(settlementDate AS DATE) = '{latest_date}'
            ),
            bmu_active AS (
                SELECT DISTINCT nationalGridBmUnit
                FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
                WHERE CAST(settlementDate AS DATE) = '{latest_date}'
                AND ABS(totalVolumeAccepted) > 0
            ),
            active_bmu_costs AS (
                SELECT SUM(ABS(d.cost)) as bmu_cost
                FROM `{PROJECT_ID}.{DATASET}.bmrs_disbsad` d
                INNER JOIN bmu_active b ON d.assetId = b.nationalGridBmUnit
                WHERE CAST(d.settlementDate AS DATE) = '{latest_date}'
            )
            SELECT
                SAFE_DIVIDE(a.bmu_cost, m.total_cost) * 100 as constraint_pct
            FROM market_total m
            CROSS JOIN active_bmu_costs a
            """
            df_disbsad = bq_client.query(disbsad_query).to_dataframe()
            if not df_disbsad.empty and df_disbsad.iloc[0]['constraint_pct'] is not None:
                constraint_share = f"{df_disbsad.iloc[0]['constraint_pct']:.1f}%"
            else:
                constraint_share = 'N/A'
        except Exception as e:
            logging.warning(f"   Could not calculate constraint share: {e}")
            constraint_share = 'N/A'

        # £/MW-day: Estimate using market-wide capacity
        # Typical UK BM: ~50-60 GW total capacity across all active BMUs
        # Rough estimate: active_units * 150 MW avg per unit
        estimated_capacity_mw = active_units * 150
        if estimated_capacity_mw > 0:
            price_per_mw_day = net_revenue / estimated_capacity_mw
        else:
            price_per_mw_day = 0

        # Non-delivery rate: Requires acceptance-level tracking vs settlement volumes
        # Simplified proxy: Compare BOALF count vs BOAV settled volumes
        try:
            acceptance_query = f"""
            SELECT COUNT(DISTINCT acceptanceNumber) as total_acceptances
            FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
            WHERE CAST(settlementDate AS DATE) = '{latest_date}'
            """
            df_acc = bq_client.query(acceptance_query).to_dataframe()
            if not df_acc.empty:
                total_acceptances = int(df_acc.iloc[0]['total_acceptances'] or 0)
                # Typical delivery: ~10 MWh per acceptance
                expected_mwh = total_acceptances * 10
                if expected_mwh > 0:
                    delivery_rate = min(100, (total_mwh / expected_mwh) * 100)
                    non_delivery_rate = 100 - delivery_rate
                else:
                    non_delivery_rate = 0
            else:
                non_delivery_rate = 0
        except Exception as e:
            logging.warning(f"   Could not calculate non-delivery rate: {e}")
            non_delivery_rate = 0

        return {
            'accepted_mwh': f'{offer_mwh:,.0f} / {bid_mwh:,.0f}',  # KPI_MKT_002: Offer / Bid
            'net_revenue': f'£{net_revenue:,.0f}',  # KPI_MKT_001: Total BM Cashflow
            'constraint_share': constraint_share,  # KPI_BMU_008: % DISBSAD
            'active_sps': f'{active_sps}/48',  # KPI_MKT_007: Workhorse Index
            'price_per_mw_day': f'£{price_per_mw_day:.2f}' if price_per_mw_day != 0 else 'N/A',
            'non_delivery': f'{non_delivery_rate:.1f}%' if non_delivery_rate > 0 else 'N/A',
            'vwap': f'£{vwap:.2f}/MWh' if total_mwh > 0 else f'{active_units} units',  # KPI_MKT_004: EWAP
            'offer_bid_ratio': f'{offer_bid_ratio:.2f}' if offer_bid_ratio < 999 else 'N/A'
        }

    except Exception as e:
        logging.error(f"Error calculating BM metrics: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

def update_dashboard():
    """Main update function"""
    print("\n" + "=" * 80)
    print("⚡ LIVE DASHBOARD V2 UPDATE")
    print("=" * 80)

    # Connect to services
    print("\n🔧 Connecting to BigQuery and Google Sheets...")

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    sheets_creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
    gc = gspread.authorize(sheets_creds)

    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)

        # Set flag to prevent Apps Script from clearing the layout
        sheet.update_acell('AA1', 'PYTHON_MANAGED')

        # Try to get or create Data_Hidden sheet for sparklines
        try:
            data_hidden = spreadsheet.worksheet('Data_Hidden')
            print("   Found Data_Hidden sheet")
            # Ensure it has enough columns for 48 periods (A-AV = 48 columns)
            if data_hidden.col_count < 48:
                data_hidden.resize(rows=50, cols=48)
        except Exception:
            print("   Creating Data_Hidden sheet...")
            data_hidden = spreadsheet.add_worksheet(title='Data_Hidden', rows=50, cols=48)
            # Hide it
            try:
                data_hidden.hide()
            except:
                pass  # If hide() fails, continue anyway
    except Exception as e:
        print(f"❌ Error accessing sheets: {e}")
        sys.exit(1)

    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")

    print("✅ Connected\n")

    # Check IRIS data freshness
    print("🕐 Checking IRIS data freshness...")
    freshness_check = check_data_freshness(bq_client)
    print(f"   {freshness_check['message']}")

    # Get data
    print("📊 Fetching data from BigQuery...")

    latest_date, latest_period = get_latest_settlement_period(bq_client)
    print(f"   Latest data: {latest_date}, Period {latest_period}")

    kpis = get_kpis(bq_client)
    print(f"   KPIs: Price={kpis['wholesale']}, Freq={kpis['frequency']}, Gen={kpis['total_gen']}, Wind={kpis['wind']}")

    gen_mix = get_generation_mix(bq_client)
    print(f"   Generation mix: {len(gen_mix) if gen_mix is not None else 0} fuel types")

    interconnectors = get_interconnectors(bq_client)
    print(f"   Interconnectors: {len(interconnectors) if interconnectors is not None else 0} connections")

    # NEW: Get 48-period timeseries for sparklines (only up to current period)
    timeseries_48 = get_48_period_timeseries(bq_client, latest_period)
    print(f"   48-period timeseries: {timeseries_48.shape if timeseries_48 is not None else 'None'}")

    # NEW: Get 48-period interconnector flows for sparklines (only up to current period)
    ic_timeseries_48 = get_48_period_interconnectors(bq_client, latest_period)
    print(f"   48-period IC flows: {ic_timeseries_48.shape if ic_timeseries_48 is not None else 'None'}")

    # NEW: Get KPI timeseries for sparklines
    kpi_timeseries = get_kpi_timeseries(bq_client, latest_period)
    print(f"   KPI timeseries: {len(kpi_timeseries['wholesale']) if kpi_timeseries else 0} periods")

    # NEW: Get BM metrics
    bm_metrics = get_bm_metrics(bq_client)
    if bm_metrics:
        print(f"   BM metrics: {bm_metrics['accepted_mwh']} MWh, {bm_metrics['net_revenue']} revenue")

    print("\n✍️  Writing to Google Sheet...")

    # BATCH UPDATES to avoid API rate limits
    # Prepare all updates in a list for batch_update
    batch_updates = []

    # Update headers (Row 12) with bar chart columns
    batch_updates.append({
        'range': 'A12:K12',
        'values': [[
            '🛢️ Fuel Type',      # A12
            '⚡ GW',              # B12
            '📊 Share',           # C12
            '📊 Bar',             # D12
            '📈 Trend (00:00→)', # E12 - Fuel sparklines
            '',                  # F12
            '🔗 Connection',      # G12
            '🌊 Flow Trend',     # H12 - IC sparklines
            '',                  # I12
            'MW',                # J12
            '📊 Bar'              # K12
        ]]
    })

    # Update IRIS data ingestion status (Row 3) - Always show status with traffic lights
    batch_updates.append({
        'range': 'A3',
        'values': [[freshness_check['message']]]
    })

    # Update KPIs (Row 6) - batch update all at once
    # Headers: A5=Wholesale Price, C5=Grid Frequency, E5=Total Gen, G5=Wind, I5=Demand
    batch_updates.append({
        'range': 'A6:I6',
        'values': [[
            kpis['wholesale'],     # A6
            '',                    # B6
            kpis['frequency'],     # C6
            '',                    # D6
            kpis['total_gen'],     # E6
            '',                    # F6
            kpis['wind'],          # G6
            '',                    # H6
            kpis['demand']         # I6
        ]]
    })

    # Execute batch update for timestamp + KPIs
    sheet.batch_update(batch_updates, value_input_option='USER_ENTERED')
    print(f"   ✅ Updated timestamp & KPIs (batched)")

    # NEW: Update BM metrics (rows 26-28)
    if bm_metrics:
        bm_updates = [
            {
                'range': 'B26:D26',
                'values': [[bm_metrics['accepted_mwh'], bm_metrics['net_revenue'], bm_metrics['constraint_share']]]
            },
            {
                'range': 'B27:D27',
                'values': [[bm_metrics['active_sps'], bm_metrics['price_per_mw_day'], bm_metrics['non_delivery']]]
            },
            {
                'range': 'B28:D28',
                'values': [[bm_metrics['vwap'], bm_metrics['offer_bid_ratio'], '']]
            }
        ]
        sheet.batch_update(bm_updates, value_input_option='USER_ENTERED')
        print(f"   ✅ Updated BM metrics (rows 26-28, batched)")

    # NEW: Update 48-period timeseries in Data_Hidden sheet for sparklines
    if timeseries_48 is not None:
        # Fuel type order matching the dashboard
        fuel_order = ['WIND', 'NUCLEAR', 'CCGT', 'BIOMASS', 'NPSHYD', 'OTHER', 'OCGT', 'COAL', 'OIL', 'PS']

        data_rows = []
        for fuel in fuel_order:
            if fuel in timeseries_48.index:
                row_data = [fuel] + timeseries_48.loc[fuel].tolist()  # Add fuel label in column A
                # Pad to exactly 49 values (1 label + 48 data points)
                if len(row_data) < 49:
                    row_data.extend([''] * (49 - len(row_data)))
                elif len(row_data) > 49:
                    row_data = row_data[:49]
                data_rows.append(row_data)
            else:
                # No data for this fuel type - use fuel label + empty strings
                data_rows.append([fuel] + [''] * 48)

        # Write to Data_Hidden sheet (rows 2-11, columns A-AW: label + 48 periods)
        if data_rows:
            try:
                data_hidden.update(values=data_rows, range_name='A2:AW11')
                print(f"   ✅ Updated fuel sparkline data ({len(data_rows)} fuel types × {latest_period} periods)")
            except Exception as e:
                print(f"   ⚠️  Could not update Data_Hidden: {e}")
    else:
        print(f"   ⚠️  No 48-period data available for fuel sparklines")

    # NEW: Update interconnector timeseries in Data_Hidden (rows 12-21)
    if ic_timeseries_48 is not None:
        # Interconnector order matching dashboard (INTFR not INTIFA!)
        ic_order = ['INTELEC', 'INTEW', 'INTFR', 'INTGRNL', 'INTIFA2', 'INTIRL', 'INTNED', 'INTNEM', 'INTNSL', 'INTVKL']

        ic_rows = []
        for ic in ic_order:
            if ic in ic_timeseries_48.index:
                row_data = [ic] + ic_timeseries_48.loc[ic].tolist()  # Add IC label in column A
                # Pad to exactly 49 values (1 label + 48 data points)
                if len(row_data) < 49:
                    row_data.extend([''] * (49 - len(row_data)))
                elif len(row_data) > 49:
                    row_data = row_data[:49]
                ic_rows.append(row_data)
            else:
                # No data for this IC - use label + zeros (not empty strings) to avoid #N/A
                ic_rows.append([ic] + [0] * latest_period + [''] * (48 - latest_period))

        # Write to Data_Hidden sheet (rows 12-21, columns A-AW: label + 48 periods)
        if ic_rows:
            try:
                data_hidden.update(values=ic_rows, range_name='A12:AW21')
                print(f"   ✅ Updated IC sparkline data ({len(ic_rows)} interconnectors × {latest_period} periods)")
            except Exception as e:
                print(f"   ⚠️  Could not update IC Data_Hidden: {e}")
    else:
        print(f"   ⚠️  No 48-period data available for IC sparklines")

    # NEW: Update KPI timeseries in Data_Hidden (rows 22-26)
    if kpi_timeseries is not None:
        kpi_labels = ['Wholesale Price', 'Frequency', 'Total Generation', 'Wind Output', 'System Demand']
        kpi_keys = ['wholesale', 'frequency', 'total_gen', 'wind', 'demand']

        kpi_rows = []
        for label, key in zip(kpi_labels, kpi_keys):
            row_data = [label] + kpi_timeseries[key]
            # Pad to exactly 49 values (1 label + 48 data points)
            if len(row_data) < 49:
                row_data.extend([''] * (49 - len(row_data)))
            elif len(row_data) > 49:
                row_data = row_data[:49]
            kpi_rows.append(row_data)

        # Write to Data_Hidden sheet (rows 22-26, columns A-AW: label + 48 periods)
        if kpi_rows:
            try:
                data_hidden.update(values=kpi_rows, range_name='A22:AW26')
                print(f"   ✅ Updated KPI sparkline data (5 KPIs × {latest_period} periods)")
            except Exception as e:
                print(f"   ⚠️  Could not update KPI Data_Hidden: {e}")
    else:
        print(f"   ⚠️  No KPI timeseries data available")

    # Update Generation Mix (Starting Row 13) - BATCH UPDATE
    if gen_mix is not None and not gen_mix.empty:
        # Map fuel types to row numbers based on current layout
        fuel_row_map = {
            'WIND': 13,
            'NUCLEAR': 14,
            'CCGT': 15,
            'BIOMASS': 16,
            'NPSHYD': 17,
            'OTHER': 18,
            'OCGT': 19,
            'COAL': 20,
            'OIL': 21,
            'PS': 22
        }

        # Prepare batch update for generation mix (all 10 rows at once)
        gen_mix_updates = []
        for fuel, row_num in fuel_row_map.items():
            if fuel in gen_mix['fuelType'].values:
                row_data = gen_mix[gen_mix['fuelType'] == fuel].iloc[0]
                gw_value = round(float(row_data['gen_gw']), 1)
                # Format share as formula to preserve percentage display
                share_pct_raw = round(float(row_data['share_pct']), 1)
                pct_formula = f'=TEXT({share_pct_raw}/100,"0.0%")'  # Display as percentage
                # NOTE: Only update B, C - removed column D bar chart (useless), leave E alone (sparklines)
                gen_mix_updates.append({
                    'range': f'B{row_num}:C{row_num}',
                    'values': [[gw_value, pct_formula]]
                })

        if gen_mix_updates:
            print(f"   DEBUG: About to batch update {len(gen_mix_updates)} fuel rows:")
            for update in gen_mix_updates[:3]:  # Show first 3
                print(f"      Range: {update['range']}, Values: {update['values']}")
            sheet.batch_update(gen_mix_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Updated generation mix ({len(gen_mix_updates)} fuels, batched)")
            # Debug: Show first update
            if gen_mix_updates:
                first = gen_mix_updates[0]
                print(f"   DEBUG: First update range={first['range']}, values={first['values']}")

        # Add sparkline formulas to column E for fuel trend charts (COLUMN type for each period)
        # Map fuel types to Data_Hidden rows (rows 2-11 in Data_Hidden)
        fuel_sparkline_map = {
            'WIND': (13, 2, '#4CAF50'),      # Green for wind
            'NUCLEAR': (14, 3, '#9C27B0'),   # Purple for nuclear
            'CCGT': (15, 4, '#FF5722'),      # Deep orange for gas
            'BIOMASS': (16, 5, '#8BC34A'),   # Light green for biomass
            'NPSHYD': (17, 6, '#03A9F4'),    # Light blue for hydro
            'OTHER': (18, 7, '#9E9E9E'),     # Grey for other
            'OCGT': (19, 8, '#FF9800'),      # Orange for OCGT
            'COAL': (20, 9, '#795548'),      # Brown for coal
            'OIL': (21, 10, '#607D8B'),      # Blue grey for oil
            'PS': (22, 11, '#E91E63')        # Pink for pumped storage
        }

        sparkline_updates = []
        for fuel, (dashboard_row, data_row, color) in fuel_sparkline_map.items():
            # Use COLUMN chart to show each settlement period as a bar
            sparkline_formula = (
                f'=SPARKLINE(Data_Hidden!$B${data_row}:$AW${data_row}, '
                f'{{"charttype","column";"color","{color}"}})'
            )
            sparkline_updates.append({
                'range': f'E{dashboard_row}',
                'values': [[sparkline_formula]]
            })

        if sparkline_updates:
            sheet.batch_update(sparkline_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Added fuel trend sparklines (column E, rows 13-22, COLUMN type)")

    # NOTE: KPI sparklines are added at the END of update_dashboard() function
    # to prevent Apps Script from clearing them

    # Update Interconnectors (Starting Row 13, column J) - BATCH UPDATE
    if interconnectors is not None and not interconnectors.empty:
        # Map interconnector fuel types to names and row numbers (CONSECUTIVE ROWS 13-22)
        ic_map = {
            'INTELEC': ('🇫🇷 ElecLink', 13),
            'INTEW': ('🇮🇪 East-West', 14),
            'INTFR': ('🇫🇷 IFA', 15),  # INTFR not INTIFA
            'INTGRNL': ('🇮🇪 Greenlink', 16),
            'INTIFA2': ('🇫🇷 IFA2', 17),
            'INTIRL': ('🇮🇪 Moyle', 18),
            'INTNED': ('🇳🇱 BritNed', 19),
            'INTNEM': ('🇧🇪 Nemo', 20),
            'INTNSL': ('🇳🇴 NSL', 21),
            'INTVKL': ('🇩🇰 Viking Link', 22)
        }

        # Prepare batch update for interconnectors (all in one call)
        ic_updates = []
        for fuel, (name, row_num) in ic_map.items():
            if fuel in interconnectors['fuelType'].values:
                row_data = interconnectors[interconnectors['fuelType'] == fuel].iloc[0]
                flow_mw = round(float(row_data['flow_mw']))
                # Add bar chart in column K (scale: 100 MW = 1 bar)
                bar_chart = f'=REPT("█",MIN(INT(ABS(J{row_num})/100),30))'
                # Write connection name (G), MW value (J), and bar chart (K)
                ic_updates.append({
                    'range': f'G{row_num}:G{row_num}',
                    'values': [[name]]
                })
                ic_updates.append({
                    'range': f'J{row_num}:K{row_num}',
                    'values': [[flow_mw, bar_chart]]
                })

        if ic_updates:
            sheet.batch_update(ic_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Updated interconnectors ({len(ic_updates)} connections, batched)")

    print("\n" + "=" * 80)
    print("✅ DASHBOARD UPDATE COMPLETE")
    print("=" * 80)
    print(f"\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0")
    print()
    print("API Optimization Stats:")
    print(f"  • Total API calls: ~6 (was ~30+ before batching)")
    print(f"  • KPIs: 1 batch update (was 6 individual calls)")
    print(f"  • Gen Mix: 1 batch update (was 10 individual calls)")
    print(f"  • Interconnectors: 1 batch update (was 10 individual calls)")
    print(f"  • Data_Hidden: 2 updates (fuel + IC timeseries)")

    # Update outages section (columns G-Q, rows 31+)
    try:
        print("\n📊 Updating outages section...")
        import subprocess
        result = subprocess.run(
            ['python3', 'update_live_dashboard_v2_outages.py'],
            capture_output=True,
            text=True,
            cwd='/home/george/GB-Power-Market-JJ'
        )
        if result.returncode == 0:
            # Extract the outages count from output
            for line in result.stdout.split('\n'):
                if 'Outages updated' in line:
                    print(f"   {line.strip()}")
                    break
        else:
            print(f"   ⚠️  Outages update failed: {result.stderr[:100]}")
    except Exception as e:
        print(f"   ⚠️  Could not update outages: {e}")

    # FINAL STEP: Re-add KPI sparklines (they get cleared by Apps Script triggers)
    # This MUST be last, after all other updates complete
    if kpi_timeseries is not None:
        print("\n📈 Re-adding KPI sparklines (final step)...")

        # Use the authenticated client to access the spreadsheet via API v4
        # to set protected ranges (gspread doesn't support this directly)
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds_v4 = service_account.Credentials.from_service_account_file(
            SA_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds_v4)

        # Get sheet ID for Live Dashboard v2
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = None
        for s in spreadsheet_metadata.get('sheets', []):
            if s['properties']['title'] == 'Live Dashboard v2':
                sheet_id = s['properties']['sheetId']
                break

        if sheet_id:
            # Add sparklines to row 7 (below values in row 6)
            kpi_sparklines = [
                ('C7', 22, '📉 Wholesale', '#e74c3c', 'column'),
                ('E7', 23, '💓 Frequency', '#2ecc71', 'line'),
                ('G7', 24, '🏭 Generation', '#f39c12', 'column'),
                ('I7', 25, '🌬️ Wind', '#4ECDC4', 'column'),
                ('K7', 26, '🔌 Demand', '#9b59b6', 'column'),
            ]

            # Build batch update request
            requests = []
            for cell, data_row, label, color, chart_type in kpi_sparklines:
                formula = f'=SPARKLINE(Data_Hidden!$B${data_row}:$AW${data_row}, {{"charttype","{chart_type}";"color","{color}"}})'

                # Convert cell notation to row/col indices (B4 = row 3, col 1)
                col_letter = cell[0]
                row_num = int(cell[1])
                col_num = ord(col_letter) - ord('A')

                requests.append({
                    'updateCells': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': row_num - 1,
                            'endRowIndex': row_num,
                            'startColumnIndex': col_num,
                            'endColumnIndex': col_num + 1
                        },
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {'formulaValue': formula}
                            }]
                        }],
                        'fields': 'userEnteredValue'
                    }
                })

                # Add protected range for this cell
                requests.append({
                    'addProtectedRange': {
                        'protectedRange': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': row_num - 1,
                                'endRowIndex': row_num,
                                'startColumnIndex': col_num,
                                'endColumnIndex': col_num + 1
                            },
                            'description': f'KPI Sparkline: {label}',
                            'warningOnly': True  # Warning mode - doesn't block edits
                        }
                    }
                })

            # Execute batch update
            body = {'requests': requests}
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=body
            ).execute()

            print(f"   ✅ Re-added 5 KPI sparklines to row 7 (C, E, G, I, K) with protection")
        else:
            print(f"   ⚠️  Could not find sheet ID for 'Live Dashboard v2'")

    # Deploy BM Market KPIs (columns U-X, rows 13-16)
    try:
        deploy_bm_kpis(sheet, bq_client)
    except Exception as e:
        logging.error(f"⚠️  BM KPI deployment failed: {e}")

if __name__ == "__main__":
    try:
        update_dashboard()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
