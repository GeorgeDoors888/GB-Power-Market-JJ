#!/usr/bin/env python3
"""
Parse actual MPAN format and update BESS sheet with correct details
Format: PC (2) + MTC (3) + LLFC (3-4) in I6
        Distributor (2) + Unique ID (10) + Check digit (1) in J6
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
PROJECT_ID = "inner-cinema-476211-u9"

def parse_actual_mpan(supplement_field, core_field):
    """
    Parse actual MPAN format
    
    Args:
        supplement_field: e.g., "00801520" = PC(00) + MTC(801) + LLFC(520)
        core_field: e.g., "2412345678904" = Distributor(24) + ID(10) + Check(1)
    
    Returns:
        dict with parsed components
    """
    
    result = {
        'profile_class': '',
        'mtc': '',
        'llfc': '',
        'distributor_id': '',
        'full_mpan': '',
        'voltage': '',
        'dno_key': ''
    }
    
    # Parse supplement field (PC + MTC + LLFC)
    if supplement_field and len(supplement_field) >= 8:
        result['profile_class'] = supplement_field[0:2]  # First 2 digits
        result['mtc'] = supplement_field[2:5]            # Next 3 digits
        result['llfc'] = supplement_field[5:9]           # Next 3-4 digits
    
    # Parse core field (Distributor ID + Unique ID + Check digit)
    if core_field and len(core_field) == 13:
        result['distributor_id'] = core_field[0:2]
        result['full_mpan'] = core_field
    
    # Determine voltage from Profile Class
    pc = result['profile_class']
    if pc == '00':
        result['voltage'] = 'HH'  # Half-hourly, typically HV/EHV
    elif pc in ['01', '02', '03', '04', '05', '06', '07', '08']:
        result['voltage'] = 'LV'
    
    # Determine voltage from LLFC (more accurate)
    llfc = result['llfc']
    if llfc:
        first_digit = llfc[0] if llfc else '0'
        if first_digit in ['0', '1', '2']:
            result['voltage'] = 'LV'
        elif first_digit in ['3', '4', '5']:
            result['voltage'] = 'HV'
        elif first_digit in ['6', '7']:
            result['voltage'] = 'EHV'
    
    return result


def get_dno_from_distributor_id(distributor_id):
    """Look up DNO from distributor ID (MPAN area ID)"""
    
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDS_FILE
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # The distributor_id is the MPAN area ID (10-29)
    query = f"""
    SELECT dno_key, dno_name, dno_short_code as short_code, market_participant_id, 
           gsp_group_id, gsp_group_name
    FROM `{PROJECT_ID}.uk_energy_prod.neso_dno_reference`
    WHERE mpan_distributor_id = {int(distributor_id)}
    LIMIT 1
    """
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return {
                'dno_key': df['dno_key'].iloc[0],
                'dno_name': df['dno_name'].iloc[0],
                'short_code': df['short_code'].iloc[0],
                'market_participant_id': df['market_participant_id'].iloc[0],
                'gsp_group_id': df['gsp_group_id'].iloc[0],
                'gsp_group_name': df['gsp_group_name'].iloc[0]
            }
    except Exception as e:
        print(f"⚠️  Error looking up DNO: {e}")
    
    return None


def get_duos_rates_by_llfc(dno_key, llfc, voltage):
    """Get DUoS rates filtered by specific LLFC"""
    
    import os
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDS_FILE
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Try with LLFC filter first
    query = f"""
    SELECT time_band_name, ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh
    FROM `{PROJECT_ID}.gb_power.duos_unit_rates`
    WHERE dno_key = '{dno_key}'
      AND voltage_level = '{voltage}'
      AND tariff_code LIKE '%{llfc}%'
    GROUP BY time_band_name
    ORDER BY time_band_name
    """
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            rates = {}
            for _, row in df.iterrows():
                band = row['time_band_name']
                rates[band] = row['rate_p_kwh']
            return rates
    except Exception as e:
        print(f"⚠️  Error querying rates: {e}")
    
    return {'Red': 0, 'Amber': 0, 'Green': 0}


def update_sheet_with_parsed_mpan():
    """Read MPAN from sheet, parse, and update with details"""
    
    print("=" * 80)
    print("PARSING ACTUAL MPAN DATA")
    print("=" * 80)
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess = sh.worksheet('BESS')
    
    # Read current MPAN data
    supplement = bess.acell('I6').value or ''
    core = bess.acell('J6').value or ''
    
    print(f"\n📥 Input:")
    print(f"   I6 (Supplement): {supplement}")
    print(f"   J6 (Core): {core}")
    
    # Parse MPAN
    mpan_data = parse_actual_mpan(supplement, core)
    
    print(f"\n🔍 Parsed Components:")
    print(f"   Profile Class: {mpan_data['profile_class']}")
    print(f"   MTC: {mpan_data['mtc']}")
    print(f"   LLFC: {mpan_data['llfc']}")
    print(f"   Distributor ID: {mpan_data['distributor_id']}")
    print(f"   Voltage: {mpan_data['voltage']}")
    
    # Look up DNO from distributor ID
    print(f"\n🔍 Looking up DNO for distributor ID {mpan_data['distributor_id']}...")
    dno_info = get_dno_from_distributor_id(mpan_data['distributor_id'])
    
    if dno_info:
        print(f"✅ Found: {dno_info['dno_name']} ({dno_info['dno_key']})")
        
        # Update DNO info in C6:H6
        dno_row = [[
            dno_info['dno_key'],
            dno_info['dno_name'],
            dno_info['short_code'],
            dno_info['market_participant_id'],
            dno_info['gsp_group_id'],
            dno_info['gsp_group_name']
        ]]
        bess.update(dno_row, 'C6:H6')
        print(f"✅ Updated DNO info in C6:H6")
        
        # Get DUoS rates
        print(f"\n💰 Looking up DUoS rates for {mpan_data['voltage']} with LLFC {mpan_data['llfc']}...")
        rates = get_duos_rates_by_llfc(dno_info['dno_key'], mpan_data['llfc'], mpan_data['voltage'])
        
        if rates:
            red = rates.get('Red', 0)
            amber = rates.get('Amber', 0)
            green = rates.get('Green', 0)
            
            print(f"   Red: {red:.4f} p/kWh")
            print(f"   Amber: {amber:.4f} p/kWh")
            print(f"   Green: {green:.4f} p/kWh")
            
            # Update rates in B10:D10
            rates_row = [[red, amber, green]]
            bess.update(rates_row, 'B10:D10')
            print(f"✅ Updated rates in B10:D10")
        
        # Update MPAN details in E10:J10
        mtc_desc = 'HH Metered' if mpan_data['profile_class'] == '00' else 'Non-Domestic'
        loss_factor = '1.045' if mpan_data['voltage'] == 'LV' else '1.025' if mpan_data['voltage'] == 'HV' else '1.015'
        
        details_row = [[
            mpan_data['profile_class'],
            f"{mpan_data['mtc']} ({mtc_desc})",
            mpan_data['voltage'],
            'Non-Domestic',
            mpan_data['llfc'],
            loss_factor
        ]]
        bess.update(details_row, 'E10:J10')
        print(f"✅ Updated MPAN details in E10:J10")
        
        # Update B6 with distributor ID
        bess.update([[mpan_data['distributor_id']]], 'B6')
        print(f"✅ Updated B6 with distributor ID")
        
    else:
        print(f"❌ Could not find DNO for distributor ID {mpan_data['distributor_id']}")
    
    print("\n" + "=" * 80)
    print("✅ COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    update_sheet_with_parsed_mpan()
