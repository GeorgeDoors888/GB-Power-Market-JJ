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
    """Get all KPIs - VLP Revenue, Wholesale Price, Frequency, Demand, Wind"""
    
    # Get 7-day average price for VLP revenue and wholesale
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
            'vlp_revenue': round(avg_price * 1000, 2),  # Convert to £k
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
            'vlp_revenue': 0, 'wholesale': 0, 'frequency': 50.0,
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
    print(f"   KPIs: VLP={kpis['vlp_revenue']}, Price={kpis['wholesale']}, Freq={kpis['frequency']}")
    
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
    
    print("\n✍️  Writing to Google Sheet...")
    
    # BATCH UPDATES to avoid API rate limits
    # Prepare all updates in a list for batch_update
    batch_updates = []
    
    # Update timestamp (Row 2) with current settlement period
    timestamp = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
    batch_updates.append({
        'range': 'A2',
        'values': [[f'Last Updated: {timestamp} (v2.0) SP {latest_period}']]
    })
    
    # Update KPIs (Row 6) - batch update all at once
    # Headers: A5=VLP Revenue, C5=Wholesale Price, E5=Grid Frequency, G5=Total Gen, I5=Wind, K5=Demand
    batch_updates.append({
        'range': 'A6:K6',
        'values': [[
            kpis['vlp_revenue'],  # A6
            '',                    # B6
            kpis['wholesale'],     # C6
            '',                    # D6
            kpis['frequency'],     # E6
            '',                    # F6
            kpis['total_gen'],     # G6
            '',                    # H6
            kpis['wind'],          # I6
            '',                    # J6
            kpis['demand']         # K6
        ]]
    })
    
    # Execute batch update for timestamp + KPIs
    sheet.batch_update(batch_updates, value_input_option='USER_ENTERED')
    print(f"   ✅ Updated timestamp & KPIs (batched)")
    
    # NEW: Update 48-period timeseries in Data_Hidden sheet for sparklines
    if timeseries_48 is not None:
        # Fuel type order matching the dashboard
        fuel_order = ['WIND', 'CCGT', 'NUCLEAR', 'BIOMASS', 'NPSHYD', 'OTHER', 'OCGT', 'COAL', 'OIL', 'PS']
        
        data_rows = []
        for fuel in fuel_order:
            if fuel in timeseries_48.index:
                row_data = timeseries_48.loc[fuel].tolist()
                # Pad to exactly 48 values with empty strings for future periods
                if len(row_data) < 48:
                    row_data.extend([''] * (48 - len(row_data)))
                elif len(row_data) > 48:
                    row_data = row_data[:48]
                data_rows.append(row_data)
            else:
                # No data for this fuel type - use empty strings
                data_rows.append([''] * 48)
        
        # Write to Data_Hidden sheet (rows 1-10, columns A-AV for 48 periods)
        if data_rows:
            try:
                data_hidden.update(values=data_rows, range_name='A1:AV10')
                print(f"   ✅ Updated fuel sparkline data ({len(data_rows)} fuel types × {latest_period} periods)")
            except Exception as e:
                print(f"   ⚠️  Could not update Data_Hidden: {e}")
    else:
        print(f"   ⚠️  No 48-period data available for fuel sparklines")
    
    # NEW: Update interconnector timeseries in Data_Hidden (rows 11-20)
    if ic_timeseries_48 is not None:
        # Interconnector order matching dashboard (INTFR not INTIFA!)
        ic_order = ['INTELEC', 'INTEW', 'INTFR', 'INTGRNL', 'INTIFA2', 'INTIRL', 'INTNED', 'INTNEM', 'INTNSL', 'INTVKL']
        
        ic_rows = []
        for ic in ic_order:
            if ic in ic_timeseries_48.index:
                row_data = ic_timeseries_48.loc[ic].tolist()
                # Pad to exactly 48 values with empty strings for future periods
                if len(row_data) < 48:
                    row_data.extend([''] * (48 - len(row_data)))
                elif len(row_data) > 48:
                    row_data = row_data[:48]
                ic_rows.append(row_data)
            else:
                # No data for this IC - use zeros (not empty strings) to avoid #N/A
                ic_rows.append([0] * latest_period + [''] * (48 - latest_period))
        
        # Write to Data_Hidden sheet (rows 11-20, columns A-AV for 48 periods)
        if ic_rows:
            try:
                data_hidden.update(values=ic_rows, range_name='A11:AV20')
                print(f"   ✅ Updated IC sparkline data ({len(ic_rows)} interconnectors × {latest_period} periods)")
            except Exception as e:
                print(f"   ⚠️  Could not update IC Data_Hidden: {e}")
    else:
        print(f"   ⚠️  No 48-period data available for IC sparklines")
    
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
                gen_mix_updates.append({
                    'range': f'B{row_num}:C{row_num}',
                    'values': [[gw_value, pct_value]]
                })
        
        if gen_mix_updates:
            sheet.batch_update(gen_mix_updates, value_input_option='USER_ENTERED')
            print(f"   ✅ Updated generation mix ({len(gen_mix_updates)} fuels, batched)")
    
    # Update Interconnectors (Starting Row 13, column J) - BATCH UPDATE
    if interconnectors is not None and not interconnectors.empty:
        # Map interconnector fuel types to names and row numbers
        ic_map = {
            'INTELEC': ('🇫🇷 ElecLink', 13),
            'INTEW': ('🇮🇪 East-West', 14),
            'INTFR': ('🇫🇷 IFA', 16),  # INTFR not INTIFA
            'INTGRNL': ('🇮🇪 Greenlink', 18),
            'INTIFA2': ('🇫🇷 IFA2', 20),
            'INTIRL': ('🇮🇪 Moyle', 22),
            'INTNED': ('🇳🇱 BritNed', 24),
            'INTNEM': ('🇧🇪 Nemo', 26),
            'INTNSL': ('🇳🇴 NSL', 28),
            'INTVKL': ('🇩🇰 Viking Link', 30)
        }
        
        # Prepare batch update for interconnectors (all in one call)
        ic_updates = []
        for fuel, (name, row_num) in ic_map.items():
            if fuel in interconnectors['fuelType'].values:
                row_data = interconnectors[interconnectors['fuelType'] == fuel].iloc[0]
                flow_mw = round(float(row_data['flow_mw']))
                ic_updates.append({
                    'range': f'J{row_num}',
                    'values': [[flow_mw]]
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
