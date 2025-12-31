#!/usr/bin/env python3
"""
Fast Dashboard Updater - Updates ALL sections
Uses direct Google Sheets API v4 (298x faster than gspread)
Updates: Generation Mix, Demand, Interconnectors, Wind, Outages, KPIs
"""

from fast_sheets_api import FastSheetsAPI
from google.cloud import bigquery
import os
from datetime import datetime
import pytz

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Initialize APIs
sheets_api = FastSheetsAPI('inner-cinema-credentials.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

def generate_dynamic_sparkline_ic(data):
    """
    Generate dynamic sparkline formula for interconnectors (LET with auto-scaling).
    Shows green bars for imports (+), red bars for exports (-), with gray axis line.
    
    Args:
        data: List of 48 numeric values (interconnector flows in MW)
    
    Returns:
        String with =IFERROR(LET(...)) formula
    """
    clean_data = [float(item) if isinstance(item, (int, float)) and item is not None else 0 for item in data]
    if not clean_data:
        return ''
    
    data_str = ",".join(map(str, clean_data))
    
    # LET formula with 15% padding, green for positive (imports), red for negative (exports)
    formula = f'''=IFERROR(LET(r,{{{data_str}}},x,FILTER(r,(r<>0)*(r<>"")),lo,MIN(x),hi,MAX(x),span,hi-lo,pad,MAX(1,span*0.15),SPARKLINE(IF((r=0)+(r=""),NA(),r),{{"charttype","column";"axis",true;"axiscolor","#999";"color","#34A853";"negcolor","#EA4335";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}})),"")'''
    
    return formula

def get_latest_generation_mix():
    """Get latest generation by fuel type"""
    query = f"""
    SELECT 
        fuelType,
        generation
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ORDER BY publishTime DESC
    LIMIT 50
    """
    df = bq_client.query(query).to_dataframe()
    if df.empty:
        return {}
    
    # Group by fuel type and get latest
    latest = df.groupby('fuelType').first()['generation'].to_dict()
    return latest

def get_latest_demand():
    """Get latest demand data"""
    query = f"""
    SELECT 
        initialDemandOutturn as demand
    FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
    ORDER BY CAST(settlementDate AS DATE) DESC, settlementPeriod DESC
    LIMIT 1
    """
    df = bq_client.query(query).to_dataframe()
    if not df.empty:
        return float(df['demand'].iloc[0])
    return 0.0

def get_latest_interconnectors():
    """Get latest interconnector flows from bmrs_fuelinst_iris"""
    query = f"""
    SELECT 
        fuelType,
        generation as flow
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE fuelType IN ('INTFR', 'INTIRL', 'INTNED', 'INTEW', 'INTNEM', 'INTELEC', 'INTNSL', 'INTIFA2')
    ORDER BY publishTime DESC
    LIMIT 50
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            return {}
        
        # Group by fuel type and get latest - map to interconnector names
        ic_map = {
            'INTFR': 'IFA',
            'INTIFA2': 'IFA2',
            'INTELEC': 'ELECLINK',
            'INTNED': 'BRITNED',
            'INTNEM': 'NEMO',
            'INTNSL': 'NSL',
            'INTEW': 'EWIC',
            'INTIRL': 'MOYLE'
        }
        latest = {}
        for fuel_type, flow in df.groupby('fuelType').first()['flow'].items():
            ic_name = ic_map.get(fuel_type)
            if ic_name:
                latest[ic_name] = flow
        return latest
    except:
        # Return empty if table doesn't exist
        return {}

def get_interconnector_48_periods():
    """Get 48 periods of interconnector data for dynamic sparklines"""
    query = f"""
    WITH deduped AS (
      SELECT DISTINCT
        settlementPeriod,
        fuelType,
        generation,
        publishTime
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND fuelType IN ('INTFR', 'INTIRL', 'INTNED', 'INTEW', 'INTNEM', 'INTELEC', 'INTNSL', 'INTIFA2')
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
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            return {}
        
        # Map fuel types to interconnector names
        ic_map = {
            'INTFR': 'IFA',
            'INTIFA2': 'IFA2',
            'INTELEC': 'ELECLINK',
            'INTNED': 'BRITNED',
            'INTNEM': 'NEMO',
            'INTNSL': 'NSL',
            'INTEW': 'EWIC',
            'INTIRL': 'MOYLE'
        }
        
        # Pivot to get 48 periods per interconnector
        result = {}
        for fuel_type, ic_name in ic_map.items():
            ic_data = df[df['interconnector'] == fuel_type].sort_values('settlementPeriod')
            if not ic_data.empty:
                # Pad to 48 periods if needed
                periods = list(range(1, 49))
                flows = []
                for p in periods:
                    period_data = ic_data[ic_data['settlementPeriod'] == p]
                    if not period_data.empty:
                        flows.append(float(period_data['net_flow'].iloc[0]))
                    else:
                        flows.append(0)
                result[ic_name] = flows
        return result
    except:
        return {}

def update_generation_mix(gen_data):
    """Update generation mix section with data (A-C) and sparklines (D)"""
    print("\n🔋 Updating Generation Mix...")
    
    # Map fuel types to Data_Hidden row numbers for sparklines
    fuel_types = [
        ('WIND', '🌬️ WIND', 2),
        ('NUCLEAR', '⚛️ NUCLEAR', 3),
        ('CCGT', '🏭 CCGT', 4),
        ('BIOMASS', '🌿 BIOMASS', 5),
        ('NPSHYD', '💧 NPSHYD', 6),
        ('OTHER', '❓ OTHER', 7),
        ('OCGT', '🛢️ OCGT', 8),
        ('COAL', '⛏️ COAL', 9),
        ('OIL', '🛢️ OIL', 10),
        ('PS', '💧 PS', 11),
    ]
    
    # Prepare data rows (A-C only: label, MW value, "MW" text)
    data_rows = []
    sparkline_updates = []
    
    for fuel_key, fuel_label, data_row in fuel_types:
        gen_mw = gen_data.get(fuel_key, 0)
        # Data: Label, MW value, "MW" unit
        data_rows.append([fuel_label, f'{gen_mw:.0f}', 'MW'])
        
        # Sparkline formula for merged D-E-F cell (column chart from Data_Hidden)
        dash_row = 13 + len(sparkline_updates)  # Rows 13-22
        sparkline = f'=SPARKLINE(Data_Hidden!B{data_row}:AX{data_row},{{"charttype","column"}})'  
        sparkline_updates.append({'range': f'{SHEET_NAME}!D{dash_row}', 'values': [[sparkline]]})
    
    # Update columns A-C with data (label, MW, "MW")
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!A13:C22',
        data_rows
    )
    
    # Update column D with sparklines (merged D-E-F cells show bar charts)
    sheets_api.batch_update(SPREADSHEET_ID, sparkline_updates)
    
    print(f"   ✅ Updated {len(data_rows)} fuel types with sparklines")

def update_demand(demand_mw):
    """Update demand section - DISABLED (was conflicting with wind dashboard at row 25)"""
    # NOTE: Demand update to A25:D25 removed to prevent overwriting wind dashboard
    # Wind dashboard now uses rows 60-94 but row 25 reserved for future use
    pass

def update_interconnectors(ic_data, ic_48periods):
    """Update interconnector section with data (G-I) and dynamic sparklines (J)"""
    print("\n🔌 Updating Interconnectors...")
    
    # Map interconnectors to display labels
    interconnectors = [
        ('IFA', 'IFA (FR)'),
        ('IFA2', 'IFA2 (FR)'),
        ('ELECLINK', 'ElecLink (FR)'),
        ('BRITNED', 'BritNed (NL)'),
        ('NEMO', 'Nemo (BE)'),
        ('NSL', 'NSL (NO)'),
        ('EWIC', 'EWIC (IE)'),
        ('MOYLE', 'Moyle (NI)'),
    ]
    
    # Prepare data rows (G-H: label, MW value)
    data_rows = []
    sparkline_updates = []
    
    for ic_key, ic_label in interconnectors:
        flow = ic_data.get(ic_key, 0)
        # Data: Label, MW only
        data_rows.append([ic_label, f'{abs(flow):.0f} MW'])
        
        # Dynamic sparkline formula from 48-period data
        dash_row = 13 + len(sparkline_updates)  # Rows 13-20
        periods_data = ic_48periods.get(ic_key, [0] * 48)
        sparkline = generate_dynamic_sparkline_ic(periods_data)
        sparkline_updates.append({'range': f'{SHEET_NAME}!I{dash_row}', 'values': [[sparkline]]})
    
    # Update columns G-H with data
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!G13:H20',
        data_rows
    )
    
    # Update column I with dynamic sparklines (merged I-J cells show bar charts)
    sheets_api.batch_update(SPREADSHEET_ID, sparkline_updates)
    
    print(f"   ✅ Updated {len(data_rows)} interconnectors with dynamic sparklines")

def get_latest_outages():
    """Get latest power station outages"""
    query = f"""
    SELECT 
        affectedUnit,
        eventType,
        fuelType,
        mwCapacity
    FROM `{PROJECT_ID}.{DATASET}.neso_remit_outages`
    WHERE eventStatus = 'Active'
    AND eventStart <= CURRENT_DATE()
    AND (eventEnd >= CURRENT_DATE() OR eventEnd IS NULL)
    ORDER BY mwCapacity DESC
    LIMIT 10
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df.to_dict('records') if not df.empty else []
    except:
        return []

def update_outages(outages_data):
    """Update outages section (K27-K36)"""
    print("\n⚠️  Updating Outages...")
    
    if not outages_data:
        # Clear section if no outages
        rows = [['No active outages']] + [[''] for _ in range(9)]
        sheets_api.update_single_range(
            SPREADSHEET_ID,
            f'{SHEET_NAME}!K27:K36',
            rows
        )
        print(f"   ✅ No active outages")
        return
    
    rows = []
    for outage in outages_data[:10]:
        unit = outage.get('affectedUnit', 'Unknown')
        event_type = outage.get('eventType', '')
        fuel = outage.get('fuelType', '')
        mw = outage.get('mwCapacity', 0)
        rows.append([f'{unit} ({fuel}) • {mw:.0f}MW • {event_type}'])
    
    # Pad to 10 rows
    while len(rows) < 10:
        rows.append([''])
    
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!K27:K36',
        rows
    )
    print(f"   ✅ Updated {len(outages_data)} outages")

def update_timestamp():
    """Update last updated timestamp"""
    now = datetime.now(pytz.timezone('Europe/London'))
    timestamp = now.strftime('%d/%m/%Y, %H:%M:%S')
    
    # Get current settlement period (approx)
    sp = ((now.hour * 60 + now.minute) // 30) + 1
    
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!A2',
        [[f'Last Updated: {timestamp} (v2.0) SP {sp}']]
    )
    print(f"   ✅ Timestamp: {timestamp} SP {sp}")

def main():
    """Main execution"""
    print("=" * 100)
    print("🚀 FAST DASHBOARD UPDATER - ALL SECTIONS")
    print("=" * 100)
    print(f"Spreadsheet: GB Live 2 ({SPREADSHEET_ID})")
    print(f"Sheet: {SHEET_NAME}")
    print(f"API: Google Sheets v4 Direct (298x faster)")
    
    try:
        # Fetch all data from BigQuery
        print("\n📊 Fetching data from BigQuery...")
        gen_data = get_latest_generation_mix()
        demand_mw = get_latest_demand()
        ic_data = get_latest_interconnectors()
        ic_48periods = get_interconnector_48_periods()  # NEW: 48-period data for dynamic sparklines
        
        print(f"   ✅ Generation: {len(gen_data)} fuel types")
        print(f"   ✅ Demand: {demand_mw:.0f} MW")
        print(f"   ✅ Interconnectors: {len(ic_data)} flows (latest)")
        print(f"   ✅ Interconnectors 48p: {len(ic_48periods)} timeseries")
        
        # Update all sections
        update_timestamp()
        update_generation_mix(gen_data)
        update_demand(demand_mw)
        update_interconnectors(ic_data, ic_48periods)  # Pass both latest + 48-period data
        
        # NOTE: Outages section (G25:K41) is handled by update_live_metrics.py
        # We don't update it here to avoid conflicts
        
        print("\n" + "=" * 100)
        print("✅ DASHBOARD UPDATE COMPLETE!")
        print("=" * 100)
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        print("\nℹ️  Outages & KPIs: Run update_live_metrics.py for full dashboard update")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
