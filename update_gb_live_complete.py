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

def get_48_period_timeseries(bq_client):
    """Get 48 settlement periods of generation data for sparklines"""
    query = f"""
    WITH periods_48 AS (
        SELECT 
            settlementPeriod,
            fuelType,
            SUM(generation) / 1000 as gen_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
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
    """Get current outages from bmrs_remit_unavailability with proper asset names"""
    query = f"""
    WITH latest_revisions AS (
        SELECT 
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
        GROUP BY affectedUnit
    )
    SELECT 
        u.affectedUnit as bmu_id,
        COALESCE(bmu.bmunitname, u.assetName, u.affectedUnit) as asset_name,
        COALESCE(bmu.fueltype, u.fuelType, 'Unknown') as fuel_type,
        CAST(u.unavailableCapacity AS INT64) as quantity,
        u.cause,
        u.eventType,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', u.eventStartTime) as start_time
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
        ON u.affectedUnit = bmu.nationalgridbmunit
        OR u.affectedUnit = bmu.elexonbmunit
    WHERE u.eventStatus = 'Active'
      AND TIMESTAMP(u.eventStartTime) <= CURRENT_TIMESTAMP()
      AND (TIMESTAMP(u.eventEndTime) >= CURRENT_TIMESTAMP() OR u.eventEndTime IS NULL)
      AND u.unavailableCapacity > 50
    ORDER BY u.unavailableCapacity DESC
    LIMIT 15
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            logging.info(f"   Sample: {df.iloc[0]['bmu_id']} | {df.iloc[0]['asset_name']} | {df.iloc[0]['fuel_type']} - {df.iloc[0]['quantity']} MW")
            return df
    except Exception as e:
        logging.warning(f"Could not get outages: {e}")
    
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
    -- Deduplicate by latest publishTime (handles revised IRIS data)
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
            SUM(generation) / 1000 as gen_gw
        FROM deduplicated
        WHERE rn = 1
        GROUP BY fuelType
    )
    SELECT 
        fuelType,
        gen_gw,
        gen_gw / (SELECT SUM(gen_gw) FROM latest) * 100 as share_pct
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
        gb_live = spreadsheet.worksheet('GB Live')
        
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
    
    outages = get_outages_data(bq_client)
    print(f"   Outages: {len(outages) if outages is not None else 0} units")
    
    constraints = get_geographic_constraints(bq_client)
    print(f"   Geographic constraints: {len(constraints) if constraints is not None else 0} regions")
    
    print("\n✍️  Writing to Google Sheets...")
    
    # Update timestamp
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    gb_live.update_acell('A2', f'Last Updated: {timestamp}')
    print(f"   ✅ Timestamp: {timestamp}")
    
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
    
    # Update Generation Mix (Rows 13-22)
    if gen_mix is not None:
        fuel_row_map = {
            'WIND': 13, 'NUCLEAR': 14, 'CCGT': 15, 'BIOMASS': 16,
            'NPSHYD': 17, 'OTHER': 18, 'OCGT': 19, 'COAL': 20, 'OIL': 21, 'PS': 22
        }
        
        for _, row_data in gen_mix.iterrows():
            fuel = row_data['fuelType']
            if fuel in fuel_row_map:
                row_num = fuel_row_map[fuel]
                gw_value = round(float(row_data['gen_gw']), 1)
                pct_value = f"{round(float(row_data['share_pct']), 1)}%"
                
                gb_live.update_acell(f'B{row_num}', gw_value)
                gb_live.update_acell(f'C{row_num}', pct_value)
        
        print(f"   ✅ Generation mix updated ({len(gen_mix)} fuels)")
    
    # Update Interconnectors (Rows 13-22, column J) - BATCHED
    if interconnectors is not None:
        ic_map = {
            'INTELEC': 13, 'INTEW': 14, 'INTIFA': 15, 'INTGRNL': 16,
            'INTIFA2': 17, 'INTIRL': 18, 'INTNED': 19, 'INTNEM': 20,
            'INTNSL': 21, 'INTVKL': 22
        }
        
        ic_updates = []
        for _, row_data in interconnectors.iterrows():
            fuel = row_data['fuelType']
            if fuel in ic_map:
                row_num = ic_map[fuel]
                flow_mw = round(float(row_data['flow_mw']))
                ic_updates.append({'range': f'J{row_num}', 'values': [[flow_mw]]})
        
        if ic_updates:
            gb_live.batch_update(ic_updates)
        
        print(f"   ✅ Interconnectors updated ({len(interconnectors)} connections, batched)")
    
    # Update Outages section (starting row 40, NOT 25!)
    if outages is not None and len(outages) > 0:
        # Add fuel emojis
        fuel_emoji = {
            'Fossil Gas': '🏭', 'CCGT': '🏭', 'Gas': '🏭',
            'Nuclear': '⚛️', 'NUCLEAR': '⚛️',
            'Wind Onshore': '🌬️', 'Wind Offshore': '🌬️', 'WIND': '🌬️',
            'Hydro': '💧', 'NPSHYD': '💧', 'Hydro Pumped Storage': '🔋',
            'Pumped Storage': '🔋', 'PS': '🔋',
            'Biomass': '🌿', 'BIOMASS': '🌿',
            'Coal': '🪨', 'COAL': '🪨',
            'Oil': '🛢️', 'OIL': '🛢️',
            'Other': '❓', 'OTHER': '❓',
            'INTFR': '🇫🇷', 'INTEW': '🇮🇪', 'INTNED': '🇳🇱', 'INTIRL': '🇮🇪'
        }
        
        outage_data = []
        for _, row in outages.iterrows():
            bmu = str(row['bmu_id']) if pd.notna(row['bmu_id']) else ''
            asset = str(row['asset_name']) if pd.notna(row['asset_name']) else bmu
            fuel = row['fuel_type'] if pd.notna(row['fuel_type']) else 'Unknown'
            # Add emoji to fuel type
            fuel_display = f"{fuel_emoji.get(fuel, '❓')} {fuel}" if fuel != 'Unknown' else 'Unknown'
            
            outage_data.append([
                bmu,  # BM Unit ID (column D)
                asset,  # Asset Name (column E)
                fuel_display,  # Fuel Type (column F)
                int(row['quantity']),  # Unavail MW (column G)
                row['cause'] if pd.notna(row['cause']) else 'Unknown'  # Cause (column H)
            ])
        
        # Clear old data first (rows 41-60)
        gb_live.batch_update([
            {'range': 'D41:H60', 'values': [[''] * 5] * 20}
        ])
        
        # Write outage headers and data starting at row 40
        gb_live.batch_update([
            {'range': 'D40:H40', 'values': [['BM Unit', 'Asset Name', 'Fuel Type', 'Unavail (MW)', 'Cause']]},
            {'range': f'D41:H{40 + len(outage_data)}', 'values': outage_data}
        ])
        print(f"   ✅ Outages updated ({len(outage_data)} units at row 40)")
        print(f"   First: {outage_data[0][0]} | {outage_data[0][1]} | {outage_data[0][2]} - {outage_data[0][3]} MW")
    
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
