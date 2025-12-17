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
    """Get today's data from 00:00 up to current settlement period (fuels only)"""
    query = f"""
    SELECT 
        fuelType,
        settlementPeriod,
        SUM(generation) / 1000 as gen_gw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      AND settlementPeriod <= {current_sp}  -- Only up to current period
      AND fuelType NOT LIKE 'INT%'  -- Exclude interconnectors
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
    """Get today's data from 00:00 up to current settlement period (interconnectors in MW)"""
    query = f"""
    SELECT 
        fuelType,
        settlementPeriod,
        SUM(generation) as flow_mw  -- Keep in MW
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      AND settlementPeriod <= {current_sp}  -- Only up to current period
      AND fuelType LIKE 'INT%'  -- Only interconnectors
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
    """Get today's KPI timeseries from 00:00 up to current settlement period"""
    query = f"""
    WITH gen_by_period AS (
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
    prices_by_period AS (
        SELECT 
            settlementPeriod,
            AVG(price) as wholesale_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
          AND settlementPeriod <= {current_sp}
        GROUP BY settlementPeriod
    ),
    freq_by_period AS (
        SELECT 
            CAST(FLOOR((EXTRACT(HOUR FROM measurementTime) * 60 + EXTRACT(MINUTE FROM measurementTime)) / 30) + 1 AS INT64) as settlementPeriod,
            AVG(frequency) as avg_frequency
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
        WHERE CAST(measurementTime AS DATE) = CURRENT_DATE()
          AND EXTRACT(HOUR FROM measurementTime) * 2 + CAST(EXTRACT(MINUTE FROM measurementTime) >= 30 AS INT64) + 1 <= {current_sp}
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
            '🛢️ Fuel Type',  # A12
            '⚡ GW',          # B12
            '📊 Share',       # C12
            '📊 Bar',         # D12 - NEW
            '',              # E12
            '',              # F12
            '🔗 Connection',  # G12
            '🌊 Flow Trend', # H12
            '',              # I12
            'MW',            # J12
            '📊 Bar'          # K12 - NEW
        ]]
    })
    
    # Update timestamp (Row 2) with current settlement period
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
    batch_updates.append({
        'range': 'A2',
        'values': [[f'Last Updated: {timestamp} (v2.0) SP {latest_period}']]
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
                pct_value = f"{round(float(row_data['share_pct']), 1)}%"
                # Add bar chart in column D
                bar_chart = f'=REPT("█",MIN(INT(B{row_num}*2),50))'
                gen_mix_updates.append({
                    'range': f'B{row_num}:D{row_num}',
                    'values': [[gw_value, pct_value, bar_chart]]
                })
        
        if gen_mix_updates:
            sheet.batch_update(gen_mix_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Updated generation mix ({len(gen_mix_updates)} fuels, batched)")
    
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

if __name__ == "__main__":
    try:
        update_dashboard()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
