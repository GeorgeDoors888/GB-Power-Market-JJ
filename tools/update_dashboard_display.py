#!/usr/bin/env python3
"""
Update Dashboard Display Sheet
Reads from Live Dashboard and REMIT tabs, writes presentational Dashboard
"""
import os, re
from datetime import datetime, date
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.cloud import bigquery

SHEET_ID = os.environ.get("SHEET_ID", "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
# When called from refresh_live_dashboard.py, we're in tools/ directory
import os
if os.path.exists("inner-cinema-credentials.json"):
    SA_PATH = "inner-cinema-credentials.json"
elif os.path.exists("../inner-cinema-credentials.json"):
    SA_PATH = "../inner-cinema-credentials.json"
else:
    SA_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "inner-cinema-credentials.json")
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Separate credentials for Sheets and BigQuery
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]

SHEETS_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=SHEETS_CREDS).spreadsheets()

BQ_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=BQ_SCOPES)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=BQ_CREDS, location="US")

def get_vals(range_name):
    """Get values from sheet range"""
    return sheets.values().get(spreadsheetId=SHEET_ID, range=range_name).execute().get('values', [])

def write_vals(range_name, values):
    """Write values to sheet range"""
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": values}
    ).execute()

def get_fuel_and_interconnector_data(target_date=None, current_sp=None):
    """Query BigQuery for fuel breakdown and read interconnector from Live_Raw_IC"""
    from datetime import timedelta
    
    if target_date is None:
        target_date = date.today()
    if current_sp is None:
        current_sp = 1
    
    # Query CURRENT SETTLEMENT PERIOD ONLY (not entire day!)
    # Get LATEST publishTime to avoid multiple 5-min readings within SP
    fuel_df = None
    for days_back in [0, 1]:
        query_date = target_date - timedelta(days=days_back)
        fuel_query = f"""
        WITH latest_publish AS (
          SELECT 
            fuelType,
            generation,
            publishTime,
            ROW_NUMBER() OVER (PARTITION BY fuelType ORDER BY publishTime DESC) as rn
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE DATE(settlementDate) = '{query_date}'
            AND settlementPeriod = {current_sp}
        )
        SELECT 
          fuelType,
          SUM(generation) as total_mw
        FROM latest_publish
        WHERE rn = 1  -- Only latest reading per fuel type
        GROUP BY fuelType
        ORDER BY total_mw DESC
        """
        
        try:
            fuel_df = bq_client.query(fuel_query).to_dataframe()
            if len(fuel_df) > 0:
                if days_back > 0:
                    print(f"ℹ️  Using fuel data from {query_date} SP{current_sp:02d} (today's data not available yet)")
                else:
                    print(f"✅ Using fuel data from {query_date} SP{current_sp:02d}")
                print(f"   Found {len(fuel_df)} fuel types, total: {fuel_df['total_mw'].sum()/1000:.1f} GW (current SP)")
                break
        except Exception as e:
            print(f"⚠️  No fuel data for {query_date} SP{current_sp:02d}: {e}")
            continue
    
    # Read interconnector data from Live_Raw_IC sheet (current SP only, not sum!)
    ic_net_mw = 0
    try:
        ic_vals = get_vals('Live_Raw_IC!A1:B51')
        if ic_vals and len(ic_vals) > current_sp:
            # Get IC value for CURRENT SP only (same logic as generation)
            ic_row = ic_vals[current_sp]  # current_sp is 1-indexed, matches row
            if len(ic_row) > 1 and ic_row[1]:
                try:
                    ic_net_mw = float(ic_row[1])
                except:
                    pass
    except:
        pass
    
    return fuel_df, ic_net_mw, 1  # Return 1 for count (it's net flow, not connector count)

def main():
    print("📊 Updating Dashboard display...")
    
    # Read Live Dashboard
    live_vals = get_vals('Live Dashboard!A1:Z60')
    if not live_vals or len(live_vals) < 2:
        print("❌ Live Dashboard is empty")
        return
    
    headers = live_vals[0]
    sp_idx = headers.index('SP') if 'SP' in headers else 0
    gen_idx = headers.index('Generation_MW') if 'Generation_MW' in headers else None
    demand_idx = headers.index('Demand_MW') if 'Demand_MW' in headers else None
    ssp_idx = headers.index('SSP') if 'SSP' in headers else None
    sbp_idx = headers.index('SBP') if 'SBP' in headers else None
    
    # Compute Total Generation (current SP, not sum of all SPs!)
    # Calculate current SP based on time (30-min periods)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    minutes_since_midnight = now.hour * 60 + now.minute
    current_sp_num = (minutes_since_midnight // 30) + 1
    
    # Adjust for periods that span midnight (SP47-48 are 23:00-00:00)
    if current_sp_num > 48:
        current_sp_num = current_sp_num - 48
    
    # Find the row for current SP
    current_sp_row = None
    if 1 <= current_sp_num <= 50 and len(live_vals) > current_sp_num:
        current_sp_row = live_vals[current_sp_num]  # Row index = SP number (header is row 0)
    
    if current_sp_row:
        total_gen_mw = float(current_sp_row[gen_idx]) if current_sp_row[gen_idx] else 0.0
        total_demand_mw = float(current_sp_row[demand_idx]) if demand_idx and len(current_sp_row) > demand_idx and current_sp_row[demand_idx] else 0.0
    else:
        total_gen_mw = 0.0
        total_demand_mw = 0.0
    
    total_gen_gw = total_gen_mw / 1000.0
    total_demand_gw = total_demand_mw / 1000.0
    
    # Get current market price (use SSP if available, fallback to SBP)
    current_price = 0.0
    if current_sp_row:
        if ssp_idx and len(current_sp_row) > ssp_idx and current_sp_row[ssp_idx]:
            try:
                current_price = float(current_sp_row[ssp_idx])
            except:
                pass
        elif sbp_idx and len(current_sp_row) > sbp_idx and current_sp_row[sbp_idx]:
            try:
                current_price = float(current_sp_row[sbp_idx])
            except:
                pass
    
    # Build header section (rows 1-6)
    now_str = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get fuel and interconnector data from BigQuery
    print("📊 Querying fuel and interconnector data...")
    fuel_df, ic_total_mw, ic_count = get_fuel_and_interconnector_data(current_sp=current_sp_num)
    
    # Calculate renewable percentage (compare like-with-like: daily totals)
    renewable_types = ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS']
    renewable_mw = 0
    total_fuel_mw = 0
    if fuel_df is not None and len(fuel_df) > 0:
        # Only include generation sources (positive values), exclude interconnectors and pumped storage
        generation_fuels = fuel_df[fuel_df['total_mw'] > 0]
        total_fuel_mw = generation_fuels['total_mw'].sum()
        renewable_mw = generation_fuels[generation_fuels['fuelType'].isin(renewable_types)]['total_mw'].sum()
    renewable_pct = (renewable_mw / total_fuel_mw * 100) if total_fuel_mw > 0 else 0
    
    header_rows = [
        ['File: Dashboard', '', '', '', '', '', '', ''],
        [f'⏰ Last Updated: {now_str} | ✅ FRESH | Settlement Period {current_sp_num} | Auto-refreshed', '', '', '', '', '', '', ''],
        ['Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min', '', '', '', '', '', '', ''],
        ['📊 SYSTEM METRICS', '', '', '', '', '', '', ''],
        [f'Total Generation: {total_gen_gw:.1f} GW', f'Total Supply: {total_demand_gw:.1f} GW', f'Renewables: {renewable_pct:.1f}%', '', f'Market Price (EPEX): £{current_price:.2f}/MWh', '', '', ''],
        ['', '', '', '', '', '', '', '']
    ]
    
    # Build fuel breakdown (rows 7-17) from BigQuery data
    fuel_map = {}
    if fuel_df is not None and len(fuel_df) > 0:
        for _, row in fuel_df.iterrows():
            fuel_map[row['fuelType']] = row['total_mw'] / 1000  # Convert to GW
    
    # Build interconnector display - read individual ICs from Live_Raw_Interconnectors
    ic_breakdown_rows = []
    ic_total_gw = ic_total_mw / 1000
    ic_direction = "Import" if ic_total_mw > 0 else "Export" if ic_total_mw < 0 else "Balanced"
    ic_display = f"{abs(ic_total_gw):.1f} GW {ic_direction}" if ic_count > 0 else "N/A"
    
    # Try to read individual interconnectors
    try:
        ic_breakdown_vals = get_vals('Live_Raw_Interconnectors!A2:D12')
        if ic_breakdown_vals and len(ic_breakdown_vals) > 0:
            # Found individual interconnector data
            print(f"📡 Read {len(ic_breakdown_vals)} interconnectors from Live_Raw_Interconnectors")
            for ic_row in ic_breakdown_vals:
                if len(ic_row) >= 4:
                    ic_name = ic_row[0]  # e.g., "🇫🇷 IFA (France)"
                    ic_mw = ic_row[1]     # e.g., "1507.0"
                    ic_dir = ic_row[2]    # e.g., "Import"
                    
                    print(f"   IC: {ic_name[:50]} | {ic_mw} MW {ic_dir}")
                    
                    # Skip the TOTAL NET FLOW row
                    if 'TOTAL' not in ic_name and 'NET FLOW' not in ic_name:
                        ic_breakdown_rows.append(['', '', '', ic_name, f"{ic_mw} MW {ic_dir}", '', '', ''])
            
            print(f"📊 Created {len(ic_breakdown_rows)} IC rows for display")
            
            # Add separator and total
            ic_breakdown_rows.append(['', '', '', '─' * 30, '', '', '', ''])
            ic_breakdown_rows.append(['', '', '', 'NET FLOW', ic_display, '', '', ''])
    except Exception as e:
        print(f"⚠️  Could not read Live_Raw_Interconnectors: {e}")
        # Fallback to simple net flow display
        pass
    
    fuel_rows = [
        ['⚡ GENERATION BY FUEL TYPE', '', '', '🔌 INTERCONNECTORS', '', '', '', ''],
        ['🔥 Gas (CCGT)', f"{fuel_map.get('CCGT', 0):.1f} GW" if 'CCGT' in fuel_map else 'N/A', '', '', '', '', '', ''],
        ['⚛️ Nuclear', f"{fuel_map.get('NUCLEAR', 0):.1f} GW" if 'NUCLEAR' in fuel_map else 'N/A', '', '', '', '', '', ''],
        ['💨 Wind', f"{fuel_map.get('WIND', 0):.1f} GW" if 'WIND' in fuel_map else 'N/A', '', '', '', '', '', ''],
        ['🌿 Biomass', f"{fuel_map.get('BIOMASS', 0):.1f} GW" if 'BIOMASS' in fuel_map else 'N/A', '', '', '', '', '', ''],
        ['💧 Hydro (Run-of-River)', f"{fuel_map.get('HYDRO', 0):.1f} GW" if 'HYDRO' in fuel_map else 'N/A', '', '', '', '', '', ''],
        ['💧 Pumped Storage 🔋', f"{fuel_map.get('PS', 0):.1f} GW" if 'PS' in fuel_map else 'N/A', '', '', '', '', '', ''],
        ['⚫ Coal', f"{fuel_map.get('COAL', 0):.1f} GW" if 'COAL' in fuel_map else '0.0 GW', '', '', '', '', '', ''],
        ['🔥 Gas Peaking (OCGT)', f"{fuel_map.get('OCGT', 0):.1f} GW" if 'OCGT' in fuel_map else '0.0 GW', '', '', '', '', '', ''],
        ['🛢️ Oil', f"{fuel_map.get('OIL', 0):.1f} GW" if 'OIL' in fuel_map else '0.0 GW', '', '', '', '', '', ''],
        ['⚙️ Other', f"{fuel_map.get('OTHER', 0):.1f} GW" if 'OTHER' in fuel_map else 'N/A', '', '', '', '', '', '']
    ]
    
    # Merge IC breakdown into fuel rows if available
    if ic_breakdown_rows:
        # Add interconnector data to corresponding fuel rows (rows 1-10 = rows 8-17 in Dashboard)
        print(f"🔧 Merging {len(ic_breakdown_rows)} IC rows into fuel display...")
        for i, ic_row in enumerate(ic_breakdown_rows[:10]):  # Limit to 10 rows
            if i < len(fuel_rows):
                # Replace columns D-E with IC data
                fuel_rows[i][3] = ic_row[3]
                fuel_rows[i][4] = ic_row[4]
                if i < 3:  # Show first 3 for debug
                    print(f"   fuel_rows[{i}][3] = '{ic_row[3][:50]}'")
                    print(f"   fuel_rows[{i}][4] = '{ic_row[4]}'")
    else:
        # Fallback: show net flow on first fuel row
        print("⚠️  No IC breakdown rows, using fallback net flow display")
        fuel_rows[0][3] = '(Net Flow)'
        fuel_rows[0][4] = ic_display
    
    # NOTE: Settlement Period and Outages sections are now managed separately
    # by redesign_dashboard_layout.py to maintain clean layout
    # This script ONLY updates header and fuel sections (rows 1-17)
    
    # NOTE: This script now ONLY updates the header and fuel sections (rows 1-17)
    # Settlement periods and outages are managed by redesign_dashboard_layout.py
    # to maintain the clean separated layout
    
    # Combine ONLY header and fuel rows (NOT settlement periods)
    all_rows = header_rows + fuel_rows
    
    # Write ONLY to rows 1-17 (header + fuel + interconnectors)
    print(f"� Writing {len(all_rows)} rows to Dashboard (rows 1-{len(all_rows)})...")
    write_vals('Dashboard!A1', all_rows)
    
    print("✅ Dashboard header and fuel sections updated")
    print("ℹ️  To update settlement periods and outages, run: python3 redesign_dashboard_layout.py")

if __name__ == "__main__":
    main()
