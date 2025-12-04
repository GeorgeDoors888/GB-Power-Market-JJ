#!/usr/bin/env python3
"""
Energy Cost Calculator for BESS
Calculates CCL, RO, FiT, BSUoS, TNUoS, DUoS based on Elexon VLP guidance
Uses NFD (Non-Final Demand) data from BigQuery
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime

# Configuration
DASHBOARD_V2_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'

# Energy cost rates (2025/26)
RATES = {
    'ccl': 0.00775,  # Climate Change Levy (£/kWh) - 2025/26
    'ro': 0.0619,    # Renewables Obligation (£/kWh) - 2025/26
    'fit': 0.0115,   # Feed-in Tariff (£/kWh) - 2025/26
    'bsuos_avg': 0.0045,  # BSUoS average (£/kWh) - varies daily
    'tnuos_hv': 0.0125,   # TNUoS HV (£/kWh) - varies by zone
    'ppa_rate': 150.0,    # PPA Contract Price (£/MWh) - from BESS sheet B39
}

# DUoS rates from BESS spreadsheet (EMID HV)
DUOS_RATES_EMID_HV = {
    'red': 0.01764,    # 1.764 p/kWh - from BESS sheet B10
    'amber': 0.00205,  # 0.205 p/kWh - from BESS sheet C10  
    'green': 0.00011   # 0.011 p/kWh - from BESS sheet D10
}

# Custom time bands from BESS spreadsheet
TIME_BANDS_CUSTOM = {
    'red': '08:00-16:00',    # Daytime peak (weekdays) - from BESS sheet B13
    'amber': '19:30-22:00',  # Evening (weekdays) - from BESS sheet B14
    'green': 'All other times'  # Overnight + weekends
}

def connect():
    """Connect to Google Sheets and BigQuery"""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/bigquery'
        ]
    )
    
    gs_client = gspread.authorize(creds)
    bq_client = bigquery.Client(credentials=creds, project=PROJECT_ID)
    
    return gs_client, bq_client

def get_duos_rates(bq_client, dno_short_code, voltage_level):
    """
    Get DUoS rates from BigQuery
    Tries multiple table schemas
    """
    # Try multiple possible table names
    queries = [
        # Option 1: duos_tariff_rates
        f"""
        SELECT 
          red_rate_p_kwh,
          amber_rate_p_kwh,
          green_rate_p_kwh
        FROM `{PROJECT_ID}.uk_energy_prod.duos_tariff_rates`
        WHERE dno_short_code = '{dno_short_code}'
          AND voltage_level = '{voltage_level}'
          AND effective_from <= CURRENT_DATE()
          AND (effective_to IS NULL OR effective_to >= CURRENT_DATE())
        LIMIT 1
        """,
        # Option 2: dno_duos_rates
        f"""
        SELECT 
          red_rate as red_rate_p_kwh,
          amber_rate as amber_rate_p_kwh,
          green_rate as green_rate_p_kwh
        FROM `{PROJECT_ID}.uk_energy_prod.dno_duos_rates`
        WHERE dno_code = '{dno_short_code}'
          AND voltage = '{voltage_level}'
        LIMIT 1
        """,
    ]
    
    for query in queries:
        try:
            result = list(bq_client.query(query).result())
            if result:
                row = result[0]
                return {
                    'red': row.red_rate_p_kwh / 100,  # Convert p/kWh to £/kWh
                    'amber': row.amber_rate_p_kwh / 100,
                    'green': row.green_rate_p_kwh / 100
                }
        except Exception:
            continue
    
    # Fallback to hardcoded rates
    print("   ⚠️  Using fallback DUoS rates")
    return {
        'red': 0.01764,    # 1.764 p/kWh
        'amber': 0.00205,  # 0.205 p/kWh
        'green': 0.00011   # 0.011 p/kWh
    }

def calculate_costs(consumption_kwh, rates_dict, band_distribution):
    """Calculate energy costs for given consumption"""
    costs = {}
    
    # DUoS costs (by time band)
    duos_red = consumption_kwh * band_distribution['red'] * rates_dict['red']
    duos_amber = consumption_kwh * band_distribution['amber'] * rates_dict['amber']
    duos_green = consumption_kwh * band_distribution['green'] * rates_dict['green']
    costs['duos'] = duos_red + duos_amber + duos_green
    
    # Non-time-based costs
    costs['ccl'] = consumption_kwh * RATES['ccl']
    costs['ro'] = consumption_kwh * RATES['ro']
    costs['fit'] = consumption_kwh * RATES['fit']
    costs['bsuos'] = consumption_kwh * RATES['bsuos_avg']
    costs['tnuos'] = consumption_kwh * RATES['tnuos_hv']
    
    # Total
    costs['total'] = sum(costs.values())
    costs['per_kwh'] = costs['total'] / consumption_kwh if consumption_kwh > 0 else 0
    
    return costs

def main():
    print("=" * 80)
    print("💰 BESS ENERGY COST CALCULATOR")
    print("=" * 80)
    print("\n✅ What this does:")
    print("   1. Reads your BESS configuration (DNO, voltage)")
    print("   2. Fetches DUoS rates from BigQuery")
    print("   3. Reads your HH profile (rows 22-69)")
    print("   4. Calculates all energy costs:")
    print("      • DUoS (Distribution Use of System)")
    print("      • CCL (Climate Change Levy)")
    print("      • RO (Renewables Obligation)")
    print("      • FiT (Feed-in Tariff)")
    print("      • BSUoS (Balancing Services)")
    print("      • TNUoS (Transmission Network)")
    print("   5. Writes breakdown to rows 71-83")
    print("   6. Shows daily & annual estimates")
    
    try:
        # Connect
        print("\n🔐 Connecting...")
        gs_client, bq_client = connect()
        ss = gs_client.open_by_key(DASHBOARD_V2_ID)
        bess = ss.worksheet('BESS')
        print("   ✅ Connected")
        
        # Read configuration
        print("\n📊 Reading BESS configuration...")
        dno_code = bess.acell('C6').value
        voltage = bess.acell('A10').value
        
        voltage_code = 'HV'
        if voltage:
            if 'EHV' in voltage.upper():
                voltage_code = 'EHV'
            elif 'LV' in voltage.upper():
                voltage_code = 'LV'
        
        print(f"   DNO: {dno_code}")
        print(f"   Voltage: {voltage_code}")
        
        # Get DUoS rates
        print("\n🔍 Fetching DUoS rates from BigQuery...")
        duos_rates = get_duos_rates(bq_client, dno_code, voltage_code)
        print(f"   Red: £{duos_rates['red']:.5f}/kWh ({duos_rates['red']*100:.3f} p/kWh)")
        print(f"   Amber: £{duos_rates['amber']:.5f}/kWh ({duos_rates['amber']*100:.3f} p/kWh)")
        print(f"   Green: £{duos_rates['green']:.5f}/kWh ({duos_rates['green']*100:.3f} p/kWh)")
        
        # Update rates in sheet
        bess.update(values=[[
            f'{duos_rates["red"]*100:.3f} p/kWh',
            f'{duos_rates["amber"]*100:.3f} p/kWh',
            f'{duos_rates["green"]*100:.3f} p/kWh'
        ]], range_name='B10:D10')
        
        # Read HH profile
        print("\n📈 Reading HH profile...")
        try:
            hh_data = bess.get('A22:C69')
            if hh_data and len(hh_data) == 48:
                # Calculate consumption
                total_kwh = sum(float(row[2]) for row in hh_data if len(row) >= 3) / 2
                red_kwh = sum(float(row[2]) for row in hh_data if len(row) >= 3 and row[1] == 'RED') / 2
                amber_kwh = sum(float(row[2]) for row in hh_data if len(row) >= 3 and row[1] == 'AMBER') / 2
                green_kwh = sum(float(row[2]) for row in hh_data if len(row) >= 3 and row[1] == 'GREEN') / 2
                
                band_dist = {
                    'red': red_kwh / total_kwh,
                    'amber': amber_kwh / total_kwh,
                    'green': green_kwh / total_kwh
                }
                
                print(f"   Total: {total_kwh:.2f} kWh/day")
                print(f"   RED: {red_kwh:.2f} kWh ({band_dist['red']*100:.1f}%)")
                print(f"   AMBER: {amber_kwh:.2f} kWh ({band_dist['amber']*100:.1f}%)")
                print(f"   GREEN: {green_kwh:.2f} kWh ({band_dist['green']*100:.1f}%)")
                
                # Calculate costs
                print("\n💰 Calculating costs...")
                costs = calculate_costs(total_kwh, duos_rates, band_dist)
                
                print(f"\n   DUoS:   £{costs['duos']:.2f}/day")
                print(f"   CCL:    £{costs['ccl']:.2f}/day")
                print(f"   RO:     £{costs['ro']:.2f}/day")
                print(f"   FiT:    £{costs['fit']:.2f}/day")
                print(f"   BSUoS:  £{costs['bsuos']:.2f}/day")
                print(f"   TNUoS:  £{costs['tnuos']:.2f}/day")
                print(f"   ───────────────────")
                print(f"   TOTAL:  £{costs['total']:.2f}/day")
                print(f"   Per kWh: £{costs['per_kwh']:.4f}/kWh ({costs['per_kwh']*100:.2f} p/kWh)")
                
                # Write costs to sheet
                print("\n📝 Writing cost breakdown to sheet...")
                cost_data = [
                    ["", "", ""],
                    ["Daily Cost Breakdown", "", ""],
                    ["DUoS (Distribution)", f"£{costs['duos']:.2f}", f"{costs['duos']/costs['total']*100:.1f}%"],
                    ["Climate Change Levy", f"£{costs['ccl']:.2f}", f"{costs['ccl']/costs['total']*100:.1f}%"],
                    ["Renewables Obligation", f"£{costs['ro']:.2f}", f"{costs['ro']/costs['total']*100:.1f}%"],
                    ["Feed-in Tariff", f"£{costs['fit']:.2f}", f"{costs['fit']/costs['total']*100:.1f}%"],
                    ["BSUoS", f"£{costs['bsuos']:.2f}", f"{costs['bsuos']/costs['total']*100:.1f}%"],
                    ["TNUoS", f"£{costs['tnuos']:.2f}", f"{costs['tnuos']/costs['total']*100:.1f}%"],
                    ["", "", ""],
                    ["Total Daily Cost", f"£{costs['total']:.2f}", "100%"],
                    ["Per kWh Rate", f"£{costs['per_kwh']:.4f}", f"{costs['per_kwh']*100:.2f} p/kWh"],
                    ["", "", ""],
                    ["Annual Estimate", f"£{costs['total']*365:.2f}", f"{total_kwh*365:.0f} kWh"],
                ]
                
                bess.update(values=cost_data, range_name='A71:C83')
                print("   ✅ Cost breakdown written to A71:C83")
                
            else:
                print("   ⚠️  No HH profile found!")
                print("      Run: python3 generate_hh_profile.py first")
                
        except Exception as e:
            print(f"   ⚠️  Could not read HH profile: {e}")
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE!")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
