#!/usr/bin/env python3
"""
GB Live Complete Dashboard Updater
Updates ALL sections:
1. KPIs (Row 7)
2. 48-period sparkline data (Data_Hidden sheet)
3. Generation mix (Rows 13-22)
4. Interconnector flows (Rows 13-22)
5. Wind analysis & outages (Rows 21+)
"""

import sys
import logging
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # Live Dashboard v2 - CORRECT!
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = '/home/george/inner-cinema-credentials.json'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def check_data_freshness(bq_client):
    """Check if IRIS data is fresh (within last 2 hours)"""
    query = f"""
    SELECT
        MAX(settlementDate) as latest_timestamp,
        TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), TIMESTAMP(MAX(settlementDate)), MINUTE) as age_minutes
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            age_minutes = int(df['age_minutes'].iloc[0])
            latest_ts = df['latest_timestamp'].iloc[0]

            # IRIS data should be < 2 hours old (4 settlement periods)
            if age_minutes > 120:
                return {
                    'status': 'STALE',
                    'age_minutes': age_minutes,
                    'latest_timestamp': latest_ts,
                    'message': f'⚠️ DATA STALE: {age_minutes} minutes old (last: {latest_ts})'
                }
            else:
                return {
                    'status': 'OK',
                    'age_minutes': age_minutes,
                    'latest_timestamp': latest_ts,
                    'message': f'✅ Data fresh ({age_minutes} min old)'
                }
    except Exception as e:
        return {
            'status': 'ERROR',
            'age_minutes': None,
            'latest_timestamp': None,
            'message': f'❌ ERROR checking data: {str(e)}'
        }

    return {
        'status': 'ERROR',
        'age_minutes': None,
        'latest_timestamp': None,
        'message': '❌ No IRIS data found'
    }

def get_frequency_timeseries(bq_client):
    """Get recent frequency readings for sparkline (last ~100 readings = ~25 min at 15s intervals)"""
    query = f"""
    SELECT
        frequency - 50.0 as deviation_from_50
    FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
    ORDER BY measurementTime DESC
    LIMIT 100
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Reverse to show oldest to newest (left to right)
            return df['deviation_from_50'].tolist()[::-1]
    except Exception as e:
        logging.error(f"Error getting frequency data: {e}")

    return None

def get_wholesale_price_timeseries(bq_client):
    """Get 48 settlement periods of wholesale prices for sparkline"""
    query = f"""
    WITH latest_date AS (
        SELECT MAX(CAST(settlementDate AS DATE)) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    ),
    periods_48 AS (
        SELECT
            settlementPeriod,
            AVG(price) as avg_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = (SELECT max_date FROM latest_date)
        GROUP BY settlementPeriod
    )
    SELECT
        settlementPeriod,
        avg_price
    FROM periods_48
    ORDER BY settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Create array of 48 values (fill missing periods with 0)
            price_array = [0.0] * 48
            for _, row in df.iterrows():
                period = int(row['settlementPeriod'])
                if 1 <= period <= 48:
                    price_array[period - 1] = round(float(row['avg_price']), 2)
            return price_array
    except Exception as e:
        logging.error(f"Error getting wholesale price data: {e}")

    return None

def get_interconnector_timeseries(bq_client):
    """Get 48 settlement periods of interconnector flows for sparklines"""
    query = f"""
    WITH latest_date AS (
        SELECT MAX(CAST(settlementDate AS DATE)) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ),
    periods_48 AS (
        SELECT
            settlementPeriod,
            fuelType,
            SUM(generation) as flow_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = (SELECT max_date FROM latest_date)
          AND fuelType LIKE 'INT%'
        GROUP BY settlementPeriod, fuelType
    )
    SELECT
        fuelType,
        settlementPeriod,
        flow_mw
    FROM periods_48
    ORDER BY fuelType, settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Pivot to get interconnectors as rows, periods as columns
            pivot = df.pivot(index='fuelType', columns='settlementPeriod', values='flow_mw')
            # Fill missing periods with 0
            for period in range(1, 49):
                if period not in pivot.columns:
                    pivot[period] = 0
            # Sort columns by period number
            pivot = pivot[sorted(pivot.columns)]
            return pivot
    except Exception as e:
        logging.error(f"Error getting interconnector timeseries: {e}")

    return None

def get_48_period_timeseries(bq_client):
    """Get 48 settlement periods of generation data for sparklines"""
    query = f"""
    WITH latest_date AS (
        SELECT MAX(CAST(settlementDate AS DATE)) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ),
    periods_48 AS (
        SELECT
            settlementPeriod,
            fuelType,
            SUM(generation) / 1000 as gen_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = (SELECT max_date FROM latest_date)
        GROUP BY settlementPeriod, fuelType
    )
    SELECT
        fuelType,
        settlementPeriod,
        gen_gw
    FROM periods_48
    ORDER BY fuelType, settlementPeriod
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            # Pivot to get fuel types as rows, periods as columns
            pivot = df.pivot(index='fuelType', columns='settlementPeriod', values='gen_gw')
            # Fill missing periods with 0
            for period in range(1, 49):
                if period not in pivot.columns:
                    pivot[period] = 0
            # Sort columns by period number
            pivot = pivot[sorted(pivot.columns)]
            return pivot
    except Exception as e:
        logging.error(f"Error getting 48-period data: {e}")
        import traceback
        traceback.print_exc()

    return None

def get_outages_data(bq_client):
    """Get current outages from bmrs_remit_iris with proper asset names and calculations"""
    query = f"""
    WITH latest_revisions AS (
        SELECT
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_iris`
        WHERE eventStatus = 'Active'
          AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
        GROUP BY affectedUnit
    )
    SELECT
        u.affectedUnit as bmu_id,
        COALESCE(bmu.bmunitname, u.assetId, u.affectedUnit) as asset_name,
        COALESCE(u.fuelType, 'Unknown') as fuel_type,
        CAST(u.unavailableCapacity AS INT64) as unavail_mw,
        CAST(u.normalCapacity AS INT64) as normal_mw,
        u.cause,
        u.eventType,
        u.unavailabilityType,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', TIMESTAMP(u.eventStartTime)) as start_time,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', TIMESTAMP(u.eventEndTime)) as end_time,
        u.participantId,
        u.affectedArea,
        u.biddingZone,
        TIMESTAMP_DIFF(TIMESTAMP(u.eventEndTime), CURRENT_TIMESTAMP(), HOUR) as hours_remaining
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_iris` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
        ON u.assetId = bmu.elexonbmunit
        OR u.assetId = bmu.nationalgridbmunit
    WHERE u.eventStatus = 'Active'
      AND TIMESTAMP(u.eventStartTime) <= CURRENT_TIMESTAMP()
      AND (TIMESTAMP(u.eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
      AND u.unavailableCapacity > 50
    ORDER BY u.unavailableCapacity DESC
    LIMIT 15
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            logging.info(f"   Sample: {df.iloc[0]['bmu_id']} | {df.iloc[0]['asset_name']} | {df.iloc[0]['fuel_type']} - {df.iloc[0]['unavail_mw']} MW")
            return df
    except Exception as e:
        logging.warning(f"Could not get outages: {e}")
        import traceback
        traceback.print_exc()

    return None

def get_wind_forecast_vs_actual(bq_client):
    """Get wind forecast vs actual generation for today (48 settlement periods)"""
    query = f"""
    WITH actual_wind AS (
        SELECT
            settlementPeriod as sp,
            ROUND(generation / 1000, 2) as actual_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND fuelType = 'WIND'
        ORDER BY settlementPeriod
    ),
    forecast_wind AS (
        SELECT
            EXTRACT(HOUR FROM startTime) * 2 +
            CASE WHEN EXTRACT(MINUTE FROM startTime) >= 30 THEN 2 ELSE 1 END as sp,
            ROUND(generation / 1000, 2) as forecast_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor`
        WHERE CAST(startTime AS DATE) = CURRENT_DATE()
        ORDER BY startTime
        LIMIT 48
    ),
    all_periods AS (
        SELECT sp FROM UNNEST(GENERATE_ARRAY(1, 48)) as sp
    )
    SELECT
        p.sp,
        COALESCE(a.actual_gw, 0) as actual,
        COALESCE(f.forecast_gw, 0) as forecast
    FROM all_periods p
    LEFT JOIN actual_wind a ON p.sp = a.sp
    LEFT JOIN forecast_wind f ON p.sp = f.sp
    ORDER BY p.sp
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            logging.info(f"   Wind forecast vs actual: {len(df)} periods")
            return df
    except Exception as e:
        logging.warning(f"Could not get wind forecast data: {e}")

    return None

def get_geographic_constraints(bq_client):
    """Get geographic constraint actions by GSP Group"""
    query = f"""
    WITH recent_actions AS (
        SELECT
            boalf.bmUnit,
            boalf.soFlag,
            bmu.gspGroup,
            bmu.fueltype,
            COUNT(*) as action_count,
            SUM(ABS(boalf.acceptanceLevel)) as total_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf` boalf
        LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
            ON boalf.bmUnit = bmu.nationalgridbmunit
            OR boalf.bmUnit = bmu.elexonbmunit
        WHERE CAST(boalf.settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            AND boalf.soFlag = TRUE
        GROUP BY boalf.bmUnit, boalf.soFlag, bmu.gspGroup, bmu.fueltype
    )
    SELECT
        COALESCE(gspGroup, 'Unknown') as gsp_group,
        COALESCE(fueltype, 'Unknown') as fuel_type,
        SUM(action_count) as actions,
        ROUND(SUM(total_mw), 0) as total_mw,
        ROUND(SUM(total_mw) / (SELECT SUM(total_mw) FROM recent_actions) * 100, 2) as share_pct
    FROM recent_actions
    WHERE total_mw > 0
    GROUP BY gsp_group, fuel_type
    HAVING total_mw > 100
    ORDER BY total_mw DESC
    LIMIT 10
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        logging.warning(f"Could not get geographic constraints: {e}")

    return None

def get_kpis(bq_client):
    """Get all KPIs"""
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
    ),
    latest_gen AS (
        SELECT
            SUM(CASE WHEN fuelType NOT LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as total_gen_gw,
            SUM(CASE WHEN fuelType LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as net_ic_gw
        FROM deduplicated
        WHERE rn = 1
    ),
    prices AS (
        SELECT
            AVG(price) as avg_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    ),
    freq AS (
        SELECT frequency
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
        ORDER BY measurementTime DESC
        LIMIT 1
    )
    SELECT
        p.avg_price * 1000 as vlp_revenue_k,
        p.avg_price as wholesale_price,
        g.total_gen_gw,
        COALESCE(f.frequency, 50.0) as frequency,
        g.total_gen_gw + g.net_ic_gw as demand_gw,
        g.net_ic_gw as net_ic_flow_gw
    FROM prices p, latest_gen g, freq f
    """

    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty:
            return {
                'vlp_revenue': round(float(result['vlp_revenue_k'].iloc[0]), 2),
                'wholesale': round(float(result['wholesale_price'].iloc[0]), 2),
                'total_gen': round(float(result['total_gen_gw'].iloc[0]), 2),
                'frequency': round(float(result['frequency'].iloc[0]), 2),
                'demand': round(float(result['demand_gw'].iloc[0]), 2),
                'net_ic_flow': round(float(result['net_ic_flow_gw'].iloc[0]), 2)
            }
    except Exception as e:
        logging.error(f"Error getting KPIs: {e}")

    return {
        'vlp_revenue': 0, 'wholesale': 0, 'total_gen': 0,
        'frequency': 50.0, 'demand': 0, 'net_ic_flow': 0
    }

def get_generation_mix(bq_client):
    """Get current generation mix and settlement period"""
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
    -- Deduplicate by latest publishTime (handles revised IRIS data)
    deduplicated AS (
        SELECT
            fuelType,
            generation,
            settlementPeriod,
            ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = (SELECT max_date FROM latest_period)
          AND settlementPeriod = (SELECT max_sp FROM latest_sp)
          AND fuelType NOT LIKE 'INT%'
    ),
    latest AS (
        SELECT
            fuelType,
            SUM(generation) / 1000 as gen_gw,
            MAX(settlementPeriod) as settlement_period
        FROM deduplicated
        WHERE rn = 1
        GROUP BY fuelType
    )
    SELECT
        fuelType,
        gen_gw,
        gen_gw / (SELECT SUM(gen_gw) FROM latest) * 100 as share_pct,
        settlement_period
    FROM latest
    ORDER BY gen_gw DESC
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        logging.error(f"Error getting generation mix: {e}")

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

    return None

def update_dashboard():
    """Main update function"""
    print("\n" + "=" * 80)
    print("⚡ GB LIVE COMPLETE DASHBOARD UPDATE")
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
        gb_live = spreadsheet.worksheet('Live Dashboard v2')  # FIXED: was 'GB Live'
        print(f"   ✅ Opened sheet: '{gb_live.title}' (gid={gb_live.id})")

        # Try to get or create Data_Hidden sheet
        try:
            data_hidden = spreadsheet.worksheet('Data_Hidden')
            print("   Found Data_Hidden sheet")
            # Ensure it has enough columns for 48 periods (A-AV = 48 columns)
            if data_hidden.col_count < 48:
                data_hidden.resize(rows=50, cols=48)
        except gspread.exceptions.WorksheetNotFound:
            print("   Creating Data_Hidden sheet...")
            data_hidden = spreadsheet.add_worksheet(title='Data_Hidden', rows=50, cols=48)
            # Hide it
            data_hidden.hide()

    except Exception as e:
        print(f"❌ Error accessing sheets: {e}")
        sys.exit(1)

    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")

    print("✅ Connected\n")

    # Check data freshness
    print("🔍 Checking IRIS data freshness...")
    freshness_check = check_data_freshness(bq_client)

    # Get all data
    print("📊 Fetching data from BigQuery...")

    kpis = get_kpis(bq_client)
    print(f"   KPIs: £{kpis['wholesale']}/MWh, {kpis['total_gen']} GW, {kpis['frequency']} Hz")

    gen_mix = get_generation_mix(bq_client)
    print(f"   Generation mix: {len(gen_mix) if gen_mix is not None else 0} fuel types")

    interconnectors = get_interconnectors(bq_client)
    print(f"   Interconnectors: {len(interconnectors) if interconnectors is not None else 0} connections")

    timeseries_48 = get_48_period_timeseries(bq_client)
    print(f"   48-period timeseries: {timeseries_48.shape if timeseries_48 is not None else 'None'}")

    freq_timeseries = get_frequency_timeseries(bq_client)
    print(f"   Frequency timeseries: {len(freq_timeseries) if freq_timeseries else 0} readings")

    wholesale_timeseries = get_wholesale_price_timeseries(bq_client)
    print(f"   Wholesale price timeseries: {len(wholesale_timeseries) if wholesale_timeseries else 0} periods")

    ic_timeseries = get_interconnector_timeseries(bq_client)
    print(f"   Interconnector timeseries: {ic_timeseries.shape if ic_timeseries is not None else 'None'}")

    outages = get_outages_data(bq_client)
    print(f"   Outages: {len(outages) if outages is not None else 0} units")

    constraints = get_geographic_constraints(bq_client)
    print(f"   Geographic constraints: {len(constraints) if constraints is not None else 0} regions")

    wind_forecast_actual = get_wind_forecast_vs_actual(bq_client)
    print(f"   Wind forecast vs actual: {len(wind_forecast_actual) if wind_forecast_actual is not None else 0} periods")

    print("\n✍️  Writing to Google Sheets...")

    # Update timestamp with SP in row 2 (combined format)
    if gen_mix is not None and not gen_mix.empty:
        settlement_period = int(gen_mix.iloc[0]['settlement_period'])
        timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M')
        gb_live.update_acell('A2', f'Last Updated: {timestamp} (v2.0) SP {settlement_period}')
        print(f"   ✅ Timestamp: {timestamp} SP {settlement_period}")

    # Update data freshness warning (Row 3)
    if freshness_check['status'] == 'STALE':
        warning_msg = f"⚠️ WARNING: IRIS data is {freshness_check['age_minutes']} minutes old!"
        gb_live.update_acell('A3', warning_msg)
        print(f"   {warning_msg}")
    elif freshness_check['status'] == 'ERROR':
        gb_live.update_acell('A3', freshness_check['message'])
        print(f"   {freshness_check['message']}")
    else:
        # Clear warning if data is fresh
        gb_live.update_acell('A3', '')
        print(f"   ✅ Data freshness OK ({freshness_check['age_minutes']} min old)")

    # Add time range label for sparklines (Row 6)
    time_labels = [
        '',  # A6 - VLP Revenue (no time label needed)
        '00:00→',  # B6 - Wholesale Price sparkline time indicator (48 SPs)
        '',  # C6 - merged with B
        '',  # D6 - spacing
        '00:00→',  # E6 - Frequency sparkline time indicator (recent 100 readings)
        '',  # F6 - merged with E
        ''   # G6 - Total Gen (no time label)
    ]
    gb_live.update(values=[time_labels], range_name='A6:G6')

    # Update KPIs (Row 7)
    kpi_row = [
        f"£{kpis['vlp_revenue']}k",
        f"£{kpis['wholesale']}/MWh",
        f"{kpis['total_gen']} GW",
        f"{kpis['frequency']} Hz",
        f"{kpis['demand']} GW",
        f"{'+' if kpis['net_ic_flow'] >= 0 else ''}{kpis['net_ic_flow']} GW"
    ]
    gb_live.update(values=[kpi_row], range_name='A7:F7')
    print(f"   ✅ KPIs updated")

    # Add wholesale price sparkline (Row 7, Column B - merged B7:C7)
    if wholesale_timeseries:
        # Write timeseries to Data_Hidden row 25 for wholesale price
        data_hidden.update(values=[wholesale_timeseries], range_name='A25:AV25')
        # Create sparkline referencing Data_Hidden
        sparkline_formula = f'=IF(ISBLANK(Data_Hidden!A25:AV25),\"\",SPARKLINE(Data_Hidden!A25:AV25,{{\"charttype\",\"column\";\"color\",\"#f39c12\"}}))'
        gb_live.update(values=[[sparkline_formula]], range_name='B7', value_input_option='USER_ENTERED')
        print(f"   ✅ Wholesale price sparkline added (row 7 col B, 48 periods)")

    # Add frequency deviation sparkline (Row 7, Column E - merged E7:F7)
    if freq_timeseries:
        # Write frequency deviation to Data_Hidden row 26
        data_hidden.update(values=[freq_timeseries], range_name='A26:CV26')  # 100 readings
        # Create sparkline showing deviation from 50 Hz (green above, red below)
        freq_sparkline = f'=IF(ISBLANK(Data_Hidden!A26:CV26),\"\",SPARKLINE(Data_Hidden!A26:CV26,{{\"charttype\",\"column\";\"color\",\"#34A853\";\"negcolor\",\"#EA4335\";\"axis\",true}}))'
        gb_live.update(values=[[freq_sparkline]], range_name='E7', value_input_option='USER_ENTERED')
        print(f"   ✅ Frequency deviation sparkline added (row 7 col E-F, 100 readings)")

    # Update 48-period timeseries in Data_Hidden sheet
    if timeseries_48 is not None:
        # Fuel type order matching the dashboard
        fuel_order = ['WIND', 'CCGT', 'NUCLEAR', 'BIOMASS', 'NPSHYD', 'OTHER', 'OCGT', 'COAL', 'OIL', 'PS']

        data_rows = []
        for i, fuel in enumerate(fuel_order, start=1):
            if fuel in timeseries_48.index:
                row_data = timeseries_48.loc[fuel].tolist()
                data_rows.append(row_data)
            else:
                data_rows.append([0] * 48)

        # Write to Data_Hidden sheet (rows 1-10, columns A-AV for 48 periods)
        if data_rows:
            # Convert to proper range format - column AV is the 48th column
            # A=1, B=2, ... Z=26, AA=27, AB=28, ... AV=48
            # AV = 26 + 22 = 48th column
            data_hidden.update(values=data_rows, range_name='A1:AV10')
            print(f"   ✅ 48-period sparkline data updated ({len(data_rows)} fuel types)")

    # Update Generation Mix (Rows 13-22) - Column A: fuel name, Column B: GW value
    if gen_mix is not None:
        fuel_row_map = {
            'WIND': 13, 'NUCLEAR': 14, 'CCGT': 15, 'BIOMASS': 16,
            'NPSHYD': 17, 'OTHER': 18, 'OCGT': 19, 'COAL': 20, 'OIL': 21, 'PS': 22
        }

        fuel_emojis = {
            'WIND': '🌬️ WIND', 'NUCLEAR': '⚛️ NUCLEAR', 'CCGT': '🏭 CCGT',
            'BIOMASS': '🌿 BIOMASS', 'NPSHYD': '💧 NPSHYD', 'OTHER': '❓ OTHER',
            'OCGT': '🛢️ OCGT', 'COAL': '⛏️ COAL', 'OIL': '🛢️ OIL', 'PS': '💧 PS'
        }

        # Prepare batch update with formatting preservation
        gen_updates = []
        for _, row_data in gen_mix.iterrows():
            fuel = row_data['fuelType']
            if fuel in fuel_row_map:
                row_num = fuel_row_map[fuel]
                fuel_name = fuel_emojis.get(fuel, fuel)
                gw_value = round(float(row_data['gen_gw']), 1)

                # Update values only (preserves existing formatting)
                gen_updates.append({
                    'range': f'A{row_num}:B{row_num}',
                    'values': [[fuel_name, gw_value]]
                })

        if gen_updates:
            # DEBUG: Show what we're about to write
            print(f"   📝 DEBUG: Preparing to write {len(gen_updates)} fuel updates:")
            for update in gen_updates:
                print(f"      {update['range']}: {update['values']}")

            # Use RAW value input to preserve cell formatting (colors, fonts)
            gb_live.batch_update(gen_updates, value_input_option='USER_ENTERED')

        print(f"   ✅ Generation mix updated ({len(gen_mix)} fuels) - Columns A-B (formatting preserved)")

    # Add sparklines in column C (rows 13-22) referencing Data_Hidden sheet
    if timeseries_48 is not None:
        # Map fuel types to Data_Hidden rows (row order: WIND, CCGT, NUCLEAR, BIOMASS, NPSHYD, OTHER, OCGT, COAL, OIL, PS)
        fuel_to_hidden_row = {
            'WIND': 1, 'CCGT': 2, 'NUCLEAR': 3, 'BIOMASS': 4,
            'NPSHYD': 5, 'OTHER': 6, 'OCGT': 7, 'COAL': 8, 'OIL': 9, 'PS': 10
        }

        fuel_row_map = {
            'WIND': 13, 'NUCLEAR': 14, 'CCGT': 15, 'BIOMASS': 16,
            'NPSHYD': 17, 'OTHER': 18, 'OCGT': 19, 'COAL': 20, 'OIL': 21, 'PS': 22
        }

        sparkline_updates = []
        for fuel, dashboard_row in fuel_row_map.items():
            if fuel in fuel_to_hidden_row:
                hidden_row = fuel_to_hidden_row[fuel]
                # SPARKLINE bar chart formula - positive bars only
                formula = f'=SPARKLINE(Data_Hidden!A{hidden_row}:AV{hidden_row},{{\"charttype\",\"column\";\"color\",\"#4285F4\";\"negcolor\",\"#4285F4\"}})'
                sparkline_updates.append({
                    'range': f'C{dashboard_row}',
                    'values': [[formula]]
                })

        if sparkline_updates:
            gb_live.batch_update(sparkline_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Sparklines added to column C ({len(sparkline_updates)} fuels)")

    # Update Interconnectors (Rows 13-22, columns D-E) - BATCHED
    if interconnectors is not None:
        ic_country_map = {
            'INTFR': '🇫🇷 France', 'INTIFA2': '🇫🇷 IFA2', 'INTELEC': '⚡ ElecLink',
            'INTIRL': '🇮🇪 Ireland', 'INTEW': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 E-W',
            'INTNED': '🇳🇱 Netherlands', 'INTNEM': '🇧🇪 Belgium',
            'INTNSL': '🇳🇴 Norway', 'INTVKL': '🇩🇰 Denmark', 'INTGRNL': '🇬🇱 Greenlink'
        }

        ic_updates = []
        row_num = 13  # Start at row 13
        for _, row_data in interconnectors.iterrows():
            if row_num > 22:  # Stop at row 22
                break
            fuel = row_data['fuelType']
            country_name = ic_country_map.get(fuel, fuel)
            flow_mw = round(float(row_data['flow_mw']))
            ic_updates.append({'range': f'D{row_num}:E{row_num}', 'values': [[country_name, flow_mw]]})
            row_num += 1
        if ic_updates:
            # Use USER_ENTERED to preserve cell formatting (colors, fonts)
            gb_live.batch_update(ic_updates, value_input_option='USER_ENTERED')

        print(f"   ✅ Interconnectors updated ({len(interconnectors)} connections) - Columns D-E (formatting preserved)")
        print(f"   ✅ Interconnectors updated ({len(interconnectors)} connections) - Columns D-E")

    # Write interconnector timeseries to Data_Hidden (rows 11-20) and add sparklines
    if ic_timeseries is not None:
        ic_order = ['INTNSL', 'INTVKL', 'INTFR', 'INTIFA2', 'INTELEC', 'INTNED', 'INTNEM', 'INTGRNL', 'INTIRL', 'INTEW']

        # Write IC timeseries to Data_Hidden (rows 11-20)
        ic_data_rows = []
        for ic_code in ic_order:
            if ic_code in ic_timeseries.index:
                row_data = ic_timeseries.loc[ic_code].tolist()
                ic_data_rows.append(row_data)
            else:
                ic_data_rows.append([0] * 48)

        if ic_data_rows:
            data_hidden.update(values=ic_data_rows, range_name='A11:AV20')
            print(f"   ✅ Interconnector timeseries data updated (10 ICs)")

        # Add sparklines in column H (rows 13-22) - UPDATED LOCATION
        ic_sparkline_updates = []
        ic_row_map = {'INTNSL': 13, 'INTVKL': 14, 'INTFR': 15, 'INTIFA2': 16, 'INTELEC': 17,
                      'INTNED': 18, 'INTNEM': 19, 'INTGRNL': 20, 'INTIRL': 21, 'INTEW': 22}

        # Map IC to Data_Hidden rows (offset by 2: IC row in sheet - 11 = Data_Hidden row offset)
        ic_to_data_row = {
            'INTNSL': 11, 'INTVKL': 12, 'INTFR': 13, 'INTIFA2': 14, 'INTELEC': 15,
            'INTNED': 16, 'INTNEM': 17, 'INTGRNL': 18, 'INTIRL': 19, 'INTEW': 20
        }

        for ic_code, dashboard_row in ic_row_map.items():
            hidden_row = ic_to_data_row[ic_code]  # Use correct Data_Hidden row mapping
            # SPARKLINE showing import/export (positive=import green, negative=export red)
            # Data starts at column C in Data_Hidden (skipping A-B)
            formula = f'=SPARKLINE(Data_Hidden!C{hidden_row}:AX{hidden_row},{{\"charttype\",\"column\";\"color\",\"#34A853\";\"negcolor\",\"#EA4335\";\"axis\",true}})'
            ic_sparkline_updates.append({
                'range': f'H{dashboard_row}',
                'values': [[formula]]
            })

        if ic_sparkline_updates:
            gb_live.batch_update(ic_sparkline_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Interconnector sparklines added to column H ({len(ic_sparkline_updates)} ICs)")

    # Update Outages section (starting row 25)
    if outages is not None and len(outages) > 0:
        # Calculate totals
        total_units = len(outages)
        total_unavail = int(outages['unavail_mw'].sum())
        total_normal = int(outages['normal_mw'].sum())

        # Add header with totals in row 25
        header_text = f"⚠️ ACTIVE OUTAGES - Top 15 by Capacity | Total: {total_units} units | Offline: {total_unavail:,} MW | Normal Capacity: {total_normal:,} MW"

        # Add fuel emojis
        fuel_emoji = {
            'Fossil Gas': '🏭', 'CCGT': '🏭', 'Gas': '🏭',
            'Nuclear': '⚛️', 'NUCLEAR': '⚛️', 'Nuclear Reactor': '⚛️',
            'Wind Onshore': '🌬️', 'Wind Offshore': '🌬️', 'WIND': '🌬️',
            'Hydro': '💧', 'NPSHYD': '💧', 'Hydro Pumped Storage': '🔋',
            'Pumped Storage': '🔋', 'PS': '🔋',
            'Biomass': '🌿', 'BIOMASS': '🌿',
            'Coal': '🪨', 'COAL': '🪨',
            'Oil': '🛢️', 'OIL': '🛢️',
            'Other': '❓', 'OTHER': '❓',
            'INTFR': '🇫🇷', 'INTEW': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'INTNED': '🇳🇱', 'INTIRL': '🇮🇪'
        }

        # Classify event types
        def classify_event(row):
            if row['unavailabilityType'] == 'Planned':
                return '📅 Planned'
            else:
                return '⚡ Unplanned'

        # Calculate duration
        def format_duration(hours):
            if pd.isna(hours) or hours < 0:
                return ''
            days = int(hours // 24)
            remaining_hours = int(hours % 24)
            if days > 0:
                return f"{days}d {remaining_hours}h"
            else:
                return f"{remaining_hours}h"

        outage_data = []
        for _, row in outages.iterrows():
            asset = str(row['asset_name']) if pd.notna(row['asset_name']) else str(row['bmu_id'])
            fuel = row['fuel_type'] if pd.notna(row['fuel_type']) else 'Unknown'
            # Add emoji to fuel type
            fuel_display = f"{fuel_emoji.get(fuel, '❓')} {fuel}"

            # Format cause/event type
            cause = str(row['cause']) if pd.notna(row['cause']) else str(row['eventType'])

            # Get operator (removed area/zone - redundant EIC codes)
            operator = str(row['participantId']) if pd.notna(row['participantId']) else ''

            outage_data.append([
                asset,  # Asset Name
                fuel_display,  # Fuel Type
                int(row['unavail_mw']),  # Unavail MW
                int(row['normal_mw']),  # Normal MW
                cause,  # Type/Cause
                classify_event(row),  # Planned/Unplanned
                str(row['end_time']) if pd.notna(row['end_time']) else 'TBD',  # Expected Return
                format_duration(row['hours_remaining']) if pd.notna(row['hours_remaining']) else '',  # Duration
                operator,  # Operator
            ])

        # Clear old data first (rows 25-47, now 9 columns instead of 11)
        gb_live.batch_update([
            {'range': 'G25:O47', 'values': [[''] * 9] * 23}
        ])

        # Write outage headers and data (removed Area/Zone columns - redundant EIC codes)
        # Row 25: Main header with totals
        # Row 26: Column headers
        # Row 27+: Data
        gb_live.batch_update([
            {'range': 'G25', 'values': [[header_text]]},
            {'range': 'G26:O26', 'values': [['Asset Name', 'Fuel Type', 'Unavail (MW)', 'Normal (MW)', 'Type', 'Category', 'Expected Return', 'Duration', 'Operator']]},
            {'range': f'G27:O{26 + len(outage_data)}', 'values': outage_data}
        ])
        print(f"   ✅ Outages updated ({len(outage_data)} units at row 27)")
        print(f"   Total offline: {total_unavail:,} MW of {total_normal:,} MW normal capacity")
        if len(outage_data) > 0:
            print(f"   First: {outage_data[0][0]} | {outage_data[0][1]} - {outage_data[0][2]} MW")

    # Update Geographic Constraints (starting row 22)
    if constraints is not None and len(constraints) > 0:
        constraint_data = []
        for _, row in constraints.iterrows():
            # Add emoji for fuel type
            fuel_emoji = {
                'WIND': '🌬️', 'CCGT': '🏭', 'NPSHYD': '💧',
                'PS': '🔋', 'OTHER': '❓', 'NUCLEAR': '⚛️'
            }
            fuel = row['fuel_type']
            fuel_display = f"{fuel_emoji.get(fuel, '❓')} {fuel}"

            constraint_data.append([
                row['gsp_group'],
                fuel_display,
                int(row['actions']),
                int(row['total_mw']),
                f"{round(row['share_pct'], 2)}%"
            ])

        # Write constraint data
        gb_live.update(values=[['GSP Group', 'Fuel', 'Actions', 'Total MW', '% Share']], range_name='A22:E22')
        gb_live.update(values=constraint_data, range_name=f'A23:E{22 + len(constraint_data)}')
        print(f"   ✅ Geographic constraints updated ({len(constraint_data)} regions)")

    # Update Wind Forecast vs Actual data in Data_Hidden (row 35, columns A-C for 48 periods)
    if wind_forecast_actual is not None and len(wind_forecast_actual) > 0:
        # Prepare data: settlement periods (1-48), actual GW, forecast GW
        wind_data = []
        for _, row in wind_forecast_actual.iterrows():
            wind_data.append([
                int(row['sp']),
                float(row['actual']),
                float(row['forecast'])
            ])

        # Write to Data_Hidden starting at row 35
        # Transpose the data so each metric is in its own row
        sp_row = [w[0] for w in wind_data]  # Row 35: Settlement periods
        actual_row = [w[1] for w in wind_data]  # Row 36: Actual GW
        forecast_row = [w[2] for w in wind_data]  # Row 37: Forecast GW

        data_hidden.batch_update([
            {'range': 'A35:AV35', 'values': [sp_row]},
            {'range': 'A36:AV36', 'values': [actual_row]},
            {'range': 'A37:AV37', 'values': [forecast_row]}
        ])
        print(f"   ✅ Wind forecast vs actual data updated (48 periods in Data_Hidden rows 35-37)")

    print("\n" + "=" * 80)
    print("✅ DASHBOARD UPDATE COMPLETE")
    print("=" * 80)
    print(f"\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0\n")

if __name__ == "__main__":
    try:
        update_dashboard()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
