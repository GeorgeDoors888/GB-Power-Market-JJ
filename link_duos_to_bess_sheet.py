#!/usr/bin/env python3
"""
Link DUoS Red/Amber/Green rates to BESS sheet dropdown
Updates rates automatically based on DNO selection and voltage level
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "gb_power"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_duos_rates():
    """Get all DUoS rates from BigQuery"""
    client = bigquery.Client(project=PROJECT_ID, location="EU")
    
    query = f"""
    SELECT 
      dno_key,
      voltage_level,
      time_band_name,
      ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh
    FROM `{PROJECT_ID}.{DATASET}.duos_unit_rates`
    WHERE tariff_code LIKE '%Non-Domestic%' OR tariff_code LIKE '%Site Specific%'
    GROUP BY dno_key, voltage_level, time_band_name
    ORDER BY dno_key, voltage_level, time_band_name
    """
    
    df = client.query(query).to_dataframe()
    return df

def setup_bess_sheet():
    """Setup BESS sheet with DUoS rates linked to dropdowns"""
    
    # Authenticate with Google Sheets
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess_ws = sh.worksheet("BESS")
    
    print("📊 Setting up BESS sheet with DUoS rates...")
    
    # Get DUoS rates
    df = get_duos_rates()
    
    # Create a lookup sheet for the rates
    try:
        lookup_ws = sh.worksheet("DUoS_Rates_Lookup")
        print("   Found existing DUoS_Rates_Lookup sheet, clearing...")
        lookup_ws.clear()
    except gspread.WorksheetNotFound:
        print("   Creating new DUoS_Rates_Lookup sheet...")
        lookup_ws = sh.add_worksheet("DUoS_Rates_Lookup", rows=200, cols=10)
    
    # Prepare lookup data
    headers = ['DNO_Key', 'Voltage_Level', 'Red (p/kWh)', 'Amber (p/kWh)', 'Green (p/kWh)']
    lookup_data = [headers]
    
    # Pivot data for each DNO + voltage combination
    for dno in sorted(df['dno_key'].unique()):
        for voltage in ['LV', 'HV', 'EHV']:
            dno_voltage_data = df[(df['dno_key'] == dno) & (df['voltage_level'] == voltage)]
            
            if not dno_voltage_data.empty:
                red_rate = dno_voltage_data[dno_voltage_data['time_band_name'] == 'Red']['rate_p_kwh'].values
                amber_rate = dno_voltage_data[dno_voltage_data['time_band_name'] == 'Amber']['rate_p_kwh'].values
                green_rate = dno_voltage_data[dno_voltage_data['time_band_name'] == 'Green']['rate_p_kwh'].values
                
                row = [
                    dno,
                    voltage,
                    float(red_rate[0]) if len(red_rate) > 0 else 0,
                    float(amber_rate[0]) if len(amber_rate) > 0 else 0,
                    float(green_rate[0]) if len(green_rate) > 0 else 0
                ]
                lookup_data.append(row)
    
    # Write lookup data
    lookup_ws.update(lookup_data, 'A1', value_input_option='USER_ENTERED')
    print(f"   ✅ Wrote {len(lookup_data)-1} rate combinations to lookup sheet")
    
    # Now setup the BESS sheet with formulas
    print("\n📝 Setting up BESS sheet formulas...")
    
    # Add voltage dropdown options
    voltage_options = ['LV (<1kV)', 'HV (1-132kV)', 'EHV (132kV+)']
    
    # Update headers
    bess_ws.update([[headers[0]] for headers in [['Voltage Level']]], 'A8')
    bess_ws.update([[headers[0]] for headers in [['Red (p/kWh)']]], 'B8')
    bess_ws.update([[headers[0]] for headers in [['Amber (p/kWh)']]], 'C8')
    bess_ws.update([[headers[0]] for headers in [['Green (p/kWh)']]], 'D8')
    bess_ws.update([[headers[0]] for headers in [['Total (p/kWh)']]], 'E8')
    
    # Add instructions
    bess_ws.update([['↓ Select voltage level:']], 'A7')
    
    # Create dropdown for voltage in A9 using data validation
    from gspread.utils import rowcol_to_a1
    voltage_validation = {
        "requests": [{
            "setDataValidation": {
                "range": {
                    "sheetId": bess_ws.id,
                    "startRowIndex": 8,  # A9 (0-indexed, so row 9 = index 8)
                    "endRowIndex": 9,
                    "startColumnIndex": 0,
                    "endColumnIndex": 1
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": opt} for opt in voltage_options]
                    },
                    "showCustomUi": True
                }
            }
        }]
    }
    sh.batch_update(voltage_validation)
    bess_ws.update([['LV (<1kV)']], 'A9')  # Default value
    
    print("   ✅ Added voltage dropdown to A9")
    
    # Add formulas to lookup rates based on DNO (C6) and Voltage (A9)
    # Extract voltage code from dropdown (LV, HV, or EHV)
    voltage_formula = '=LEFT(A9, FIND(" ", A9)-1)'
    
    # VLOOKUP formulas for rates
    # Format: =VLOOKUP(C6&"_"&voltage, DUoS_Rates_Lookup!A:E, column, FALSE)
    red_formula = '=IFERROR(VLOOKUP(C6&"_"&LEFT(A9,FIND(" ",A9)-1), DUoS_Rates_Lookup!A:E, 3, FALSE), "N/A")'
    amber_formula = '=IFERROR(VLOOKUP(C6&"_"&LEFT(A9,FIND(" ",A9)-1), DUoS_Rates_Lookup!A:E, 4, FALSE), "N/A")'
    green_formula = '=IFERROR(VLOOKUP(C6&"_"&LEFT(A9,FIND(" ",A9)-1), DUoS_Rates_Lookup!A:E, 5, FALSE), "N/A")'
    
    # Update formulas
    bess_ws.update([[red_formula]], 'B9')
    bess_ws.update([[amber_formula]], 'C9')
    bess_ws.update([[green_formula]], 'D9')
    bess_ws.update([['=SUM(B9:D9)']], 'E9')
    
    print("   ✅ Added VLOOKUP formulas for Red/Amber/Green rates")
    
    # Format the lookup sheet data
    print("\n🎨 Formatting lookup sheet...")
    lookup_ws.format('A1:E1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}})
    
    print("\n✅ Setup complete!")
    print("\n📋 How to use:")
    print("   1. Select a DNO in cell C6 (DNO_Key column)")
    print("   2. Select voltage level from dropdown in A9")
    print("   3. Red/Amber/Green rates will auto-populate in B9:D9")
    print("   4. Total rate shown in E9")
    
    return True

if __name__ == "__main__":
    setup_bess_sheet()
