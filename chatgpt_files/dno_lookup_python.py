#!/usr/bin/env python3
"""
DNO Lookup via Python - No Apps Script Required
Directly queries BigQuery and updates Google Sheets
Now supports full MPAN parsing with LLFC-based tariff lookup
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import sys
import re

# ⚠️ CRITICAL: Import MPAN parser for correct distributor ID extraction
# DO NOT CHANGE: Must import from mpan_generator_validator (not mpan_parser)
# Context: Full MPAN "00800999932 1405566778899" has distributor ID in CORE (14)
#          not in top line (08 would be wrong). Parser extracts core correctly.
# Fixed: 2025-11-22 - Import was pointing to non-existent mpan_parser module
try:
    from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
    MPAN_PARSER_AVAILABLE = True
except ImportError:
    MPAN_PARSER_AVAILABLE = False
    print("⚠️  MPAN parser not available, using legacy mode")

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_UK = "uk_energy_prod"
DATASET_GB = "gb_power"
DATASET = "uk_energy_prod"  # Alias for compatibility

POSTCODE_API = "https://api.postcodes.io/postcodes/"

def lookup_postcode(postcode):
    """
    Get coordinates from UK postcode using postcodes.io API
    Returns: (latitude, longitude) or None if not found
    """
    import requests
    
    # Clean postcode
    postcode_clean = postcode.strip().upper().replace(' ', '')
    
    print(f"🌍 Looking up postcode: {postcode}")
    
    try:
        response = requests.get(f"{POSTCODE_API}{postcode_clean}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200:
                result = data['result']
                lat = result['latitude']
                lng = result['longitude']
                print(f"   Coordinates: {lat:.4f}, {lng:.4f}")
                return (lat, lng)
        
        print(f"   ❌ Postcode not found or invalid")
        return None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def lookup_dno_by_coordinates(lat, lng):
    """
    Find DNO by checking which boundary contains the coordinates
    """
    print(f"📍 Finding DNO for coordinates ({lat:.4f}, {lng:.4f})...")
    
    # Regional fallback approximation (basic UK regional boundaries)
    regional_guess = {
        # Scotland
        (56.0, 60.0, -7.0, -1.0): 17,  # SSE-SHEPD (North Scotland)
        (55.0, 56.0, -5.0, -2.0): 18,  # SP-Distribution (South Scotland)
        
        # North England
        (54.0, 55.5, -3.5, -1.0): 15,  # NPg-NE (North East)
        (53.0, 54.5, -2.5, -0.5): 23,  # NPg-Y (Yorkshire)
        (53.0, 54.0, -3.5, -2.0): 16,  # ENWL (North West)
        (53.0, 54.0, -4.0, -2.5): 13,  # SP-Manweb (Merseyside & N Wales)
        
        # Midlands
        (52.0, 53.5, -3.0, -0.5): 11,  # NGED-EM (East Midlands)
        (52.0, 53.0, -3.0, -1.5): 14,  # NGED-WM (West Midlands)
        
        # East England
        (51.5, 53.0, 0.0, 2.0): 10,    # UKPN-EPN (Eastern)
        
        # London & South East
        (51.3, 51.7, -0.5, 0.3): 12,   # UKPN-LPN (London)
        (50.8, 51.8, -0.5, 1.5): 19,   # UKPN-SPN (South Eastern)
        (50.5, 52.0, -2.5, 0.0): 20,   # SSE-SEPD (Southern)
        
        # South West & Wales
        (51.0, 52.5, -5.5, -2.5): 21,  # NGED-SWales (South Wales)
        (50.0, 51.5, -6.0, -2.0): 22,  # NGED-SW (South Western)
    }
    
    # Find matching region
    for (lat_min, lat_max, lng_min, lng_max), mpan_id in regional_guess.items():
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            print(f"   ✅ Matched to region (MPAN {mpan_id})")
            return mpan_id
    
    # Default to closest major city if no match
    print(f"   ⚠️  No exact match - defaulting to London (MPAN 12)")
    return 12

def parse_mpan_input(input_str):
    """
    Parse MPAN input - supports:
    - Full 13-digit core MPAN (e.g., "1200123456789")
    - Full MPAN with top line (e.g., "00 801 0840 1200123456789")
    - Legacy MPAN ID (10-23)
    
    Returns: (mpan_id, mpan_data, use_advanced)
    """
    if not input_str:
        return None, None, False
    
    input_clean = str(input_str).strip()
    
    # Try MPAN parser first if available
    if MPAN_PARSER_AVAILABLE and len(input_clean) >= 13:
        try:
            parser = MPANParser()
            mpan_data = parser.parse_full_mpan(input_clean)
            
            if mpan_data['valid']:
                print(f"✅ Valid MPAN (checksum verified)")
                print(f"   Distributor ID: {mpan_data['distributor_id']}")
                if mpan_data['has_top_line']:
                    print(f"   LLFC: {mpan_data['llfc']}")
                
                return mpan_data['distributor_id'], mpan_data, True
            else:
                print(f"⚠️  MPAN checksum invalid, using distributor ID anyway")
                return mpan_data['distributor_id'], mpan_data, False
                
        except Exception as e:
            print(f"⚠️  MPAN parsing failed: {e}")
    
    # Fallback: try as legacy MPAN ID (10-23)
    try:
        mpan_id = int(input_clean)
        if 10 <= mpan_id <= 23:
            return mpan_id, None, False
    except:
        pass
    
    return None, None, False

def lookup_dno_by_mpan(mpan_id):
    """Lookup DNO information by MPAN ID"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        mpan_distributor_id,
        dno_key,
        dno_name,
        dno_short_code,
        market_participant_id,
        gsp_group_id,
        gsp_group_name
    FROM `{PROJECT_ID}.{DATASET_UK}.neso_dno_reference`
    WHERE mpan_distributor_id = {mpan_id}
    LIMIT 1
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        return None
    
    return df.iloc[0].to_dict()

def get_duos_rates(dno_key, voltage_level, llfc=None):
    """
    Get DUoS rates for DNO and voltage level with time band details
    
    Args:
        dno_key: DNO identifier (e.g., "UKPN-EPN")
        voltage_level: "LV", "HV", or "EHV"
        llfc: Optional LLFC code for more specific tariff lookup
    """
    client = bigquery.Client(project=PROJECT_ID, location="EU")
    
    # Build query - if LLFC provided AND it's valid (3-4 digits), try to use it
    llfc_filter = ""
    if llfc and len(str(llfc)) <= 4 and str(llfc).isdigit():
        llfc_filter = f" AND tariff_code LIKE '%{llfc}%'"
        print(f"   ℹ️  Using LLFC {llfc} for more specific rate lookup")
    elif llfc:
        print(f"   ⚠️  LLFC {llfc} looks invalid (too long or not numeric), ignoring")
    
    # Get rates - try current first, then closest future if none found
    rates_query = f"""
    WITH ranked_rates AS (
        SELECT 
            time_band_name,
            ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh,
            effective_from,
            ROW_NUMBER() OVER (PARTITION BY time_band_name ORDER BY ABS(DATE_DIFF(effective_from, CURRENT_DATE(), DAY))) as rank
        FROM `{PROJECT_ID}.gb_power.duos_unit_rates`
        WHERE dno_key = '{dno_key}'
          AND voltage_level = '{voltage_level}'
          {llfc_filter}
        GROUP BY time_band_name, effective_from
    )
    SELECT time_band_name, rate_p_kwh
    FROM ranked_rates
    WHERE rank = 1
    ORDER BY time_band_name
    """
    
    rates_df = client.query(rates_query).to_dataframe()
    
    # Debug: Show what we got
    if len(rates_df) == 0:
        print(f"   ⚠️  WARNING: No rates found for {dno_key} {voltage_level}")
        print(f"   Query: {rates_query}")
    else:
        print(f"   ✅ Found {len(rates_df)} rate bands")
    
    # Get time band details
    time_bands_query = f"""
    SELECT 
        time_band_name,
        day_type,
        start_time,
        end_time
    FROM `{PROJECT_ID}.gb_power.duos_time_bands`
    WHERE dno_key = '{dno_key}'
    ORDER BY 
        day_type DESC,
        start_time
    """
    
    time_bands_df = client.query(time_bands_query).to_dataframe()
    
    rates = {
        'Red': {'rate': 0, 'schedule': []},
        'Amber': {'rate': 0, 'schedule': []},
        'Green': {'rate': 0, 'schedule': []}
    }
    
    # Populate rates
    for _, row in rates_df.iterrows():
        band = row['time_band_name']
        rates[band]['rate'] = float(row['rate_p_kwh'])
    
    # Build daily schedule (weekday)
    weekday_schedule = []
    for _, row in time_bands_df.iterrows():
        if row['day_type'] == 'Weekday':
            band = row['time_band_name']
            start = str(row['start_time'])[:5]
            end = str(row['end_time'])[:5]
            weekday_schedule.append({'band': band, 'start': start, 'end': end})
    
    # Sort by start time
    weekday_schedule.sort(key=lambda x: x['start'])
    
    # Build schedule entries
    for entry in weekday_schedule:
        rates[entry['band']]['schedule'].append(f"{entry['start']}-{entry['end']}")
    
    # Add weekend note to green
    has_weekend = any(row['day_type'] == 'Weekend' for _, row in time_bands_df.iterrows())
    if has_weekend:
        rates['Green']['schedule'].append('All Weekend')
    
    return rates

def parse_mpan_input(mpan_input):
    """
    Parse MPAN input - handles full MPAN (21-digit), core (13-digit), or simple ID (2-digit)
    
    ⚠️ CRITICAL FUNCTION: Correct parsing ensures right DNO is identified
    
    MPAN Formats Supported:
    - Full 21-digit: "00 801 0840 1405566778899" → extracts core → ID 14
    - Core 13-digit: "1405566778899" → ID 14  
    - Simple 2-digit: "14" → ID 14
    
    Common Error: Extracting ID from TOP LINE (08) instead of CORE (14)
    This function MUST use extract_core_from_full_mpan() for full MPAN format
    
    Returns:
        tuple: (mpan_id, mpan_core, use_advanced_parser)
    """
    if not mpan_input:
        return None, None, False
    
    # Convert to string and clean
    mpan_str = str(mpan_input).strip()
    
    # Check if it's a simple 2-digit ID (10-23)
    if mpan_str.isdigit() and len(mpan_str) <= 2:
        mpan_id = int(mpan_str)
        return mpan_id, None, False
    
    # Try full MPAN parsing if available
    if MPAN_PARSER_AVAILABLE:
        try:
            # Handle full MPAN format (with spaces/dashes) or core MPAN
            if len(mpan_str) >= 13:
                # ⚠️ CRITICAL: Detect full MPAN by spaces/dashes
                # Full MPAN has top line (PC/MTC/LLFC) + core
                # Must extract CORE to get correct distributor ID
                if ' ' in mpan_str or '-' in mpan_str:
                    core = extract_core_from_full_mpan(mpan_str)
                    print(f"   ✅ Extracted core from full MPAN: {core}")
                else:
                    # Already a core MPAN
                    core = mpan_str[:13] if len(mpan_str) >= 13 else mpan_str
                    print(f"   ✅ Using core MPAN: {core}")
                
                # Lookup DNO info from core
                # First 2 digits of CORE = distributor ID (10-23)
                info = mpan_core_lookup(core)
                if 'error' not in info:
                    mpan_id = int(info['dno_id'])
                    print(f"   Distributor ID: {mpan_id} ({info['dno_name']})")
                    return mpan_id, core, True
                else:
                    print(f"   ⚠️  {info['error']}")
            
        except Exception as e:
            print(f"   ⚠️  MPAN parsing failed: {e}")
            # Fall back to simple extraction
    
    # Legacy fallback: extract 2-digit ID from start of string
    if len(mpan_str) >= 2:
        try:
            # Try to find 2-digit number at start
            match = re.match(r'^(\d{2})', mpan_str)
            if match:
                mpan_id = int(match.group(1))
                print(f"   ℹ️  Extracted Distributor ID (legacy): {mpan_id}")
                return mpan_id, None, False
        except:
            pass
    
    # Last resort: try direct conversion
    try:
        mpan_id = int(mpan_str)
        return mpan_id, None, False
    except ValueError:
        print(f"   ❌ Could not parse MPAN: {mpan_str}")
        return None, None, False
    try:
        mpan_id = int(mpan_str)
        return mpan_id, None, False
    except:
        raise ValueError(f"Invalid MPAN format: {mpan_input}")

def update_bess_sheet(mpan_id=None, postcode=None, voltage='LV'):
    """Main function to update BESS sheet with DNO info and rates"""
    
    print("=" * 80)
    print("🔌 DNO Lookup & DUoS Rates Update (with MPAN parsing)")
    print("=" * 80)
    
    # Authenticate with Google Sheets
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key(SHEET_ID)
    bess_ws = sh.worksheet("BESS")
    
    # Get inputs from sheet if not provided
    if mpan_id is None:
        mpan_cell = bess_ws.acell('B6').value
        if mpan_cell:
            mpan_id = mpan_cell
    
    if postcode is None:
        postcode = bess_ws.acell('A6').value
    
    # Read supplement and LLFC from I6 and J6 if available
    supplement_cell = bess_ws.acell('I6').value
    llfc_cell = bess_ws.acell('J6').value
    supplement = supplement_cell.strip() if supplement_cell else None
    llfc = llfc_cell.strip() if llfc_cell else None
    
    voltage_cell = bess_ws.acell('A10').value
    if voltage_cell:
        # Extract voltage level from dropdown (e.g., "LV (<1kV)" -> "LV")
        if '(' in voltage_cell:
            voltage = voltage_cell.split('(')[0].strip()
        else:
            voltage = voltage_cell.strip()
    
    # If supplement is provided, use it to auto-detect voltage
    if supplement and not voltage_cell:
        from mpan_voltage_detector import determine_voltage_from_mpan
        voltage = determine_voltage_from_mpan(supplement=supplement, llfc=llfc)
        print(f"   ℹ️  Auto-detected voltage from supplement: {voltage}")
    
    print(f"\n📋 Inputs:")
    print(f"   Postcode: {postcode or 'Not provided'}")
    print(f"   MPAN/ID: {mpan_id or 'Not provided'}")
    print(f"   Supplement: {supplement or 'Not provided'}")
    print(f"   LLFC: {llfc or 'Not provided'}")
    print(f"   Voltage: {voltage}")
    
    mpan_data = None
    use_advanced = False
    
    # Prioritize postcode lookup if provided
    if postcode and postcode.strip():
        coords = lookup_postcode(postcode)
        if coords:
            lat, lng = coords
            mpan_id = lookup_dno_by_coordinates(lat, lng)
            print(f"   ✅ Determined MPAN from postcode: {mpan_id}")
    
    # Parse MPAN input (supports full MPAN or legacy ID)
    if mpan_id:
        mpan_id, mpan_data, use_advanced = parse_mpan_input(mpan_id)
    
    if not mpan_id:
        print("\n❌ No valid MPAN ID or postcode provided")
        return False
    
    if mpan_id < 10 or mpan_id > 23:
        print(f"❌ Invalid MPAN ID: {mpan_id} (must be 10-23)")
        return False
    
    # Lookup DNO
    print(f"\n🔍 Looking up MPAN {mpan_id}...")
    dno_info = lookup_dno_by_mpan(mpan_id)
    
    if not dno_info:
        print(f"❌ No DNO found for MPAN ID {mpan_id}")
        bess_ws.update([['Not found', '', '', '', '', '']], 'C6:H6')
        return False
    
    print(f"✅ Found: {dno_info['dno_name']} ({dno_info['dno_key']})")
    
    # Update DNO info in B6:H6 (now includes full MPAN in B6)
    if mpan_data and mpan_data.get('core_mpan'):
        # Store full core MPAN in B6
        bess_ws.update([[mpan_data['core_mpan']]], 'B6')
        print(f"✅ Stored full MPAN: {mpan_data['core_mpan']}")
    else:
        # Legacy: store just MPAN ID
        bess_ws.update([[mpan_id]], 'B6')
    
    dno_row = [[
        dno_info['dno_key'],
        dno_info['dno_name'],
        dno_info['dno_short_code'],
        dno_info['market_participant_id'],
        dno_info['gsp_group_id'],
        dno_info['gsp_group_name']
    ]]
    
    bess_ws.update(dno_row, 'C6:H6')
    print(f"✅ Updated DNO info in C6:H6")
    
    # Get DUoS rates
    print(f"\n💰 Looking up {voltage} DUoS rates for {dno_info['dno_key']}...")
    
    # If LLFC is provided, add it to the lookup context
    if llfc:
        print(f"   ℹ️  Using LLFC {llfc} for more specific rate lookup")
    
    try:
        rates = get_duos_rates(dno_info['dno_key'], voltage, llfc=llfc)
        print(f"   Red: {rates['Red']['rate']:.4f} p/kWh")
        for time in rates['Red']['schedule']:
            print(f"      {time}")
        print(f"   Amber: {rates['Amber']['rate']:.4f} p/kWh")
        for time in rates['Amber']['schedule']:
            print(f"      {time}")
        print(f"   Green: {rates['Green']['rate']:.4f} p/kWh")
        for time in rates['Green']['schedule']:
            print(f"      {time}")
        
        # Update rates in B10:D10
        rates_row = [[rates['Red']['rate'], rates['Amber']['rate'], rates['Green']['rate']]]
        bess_ws.update(rates_row, 'B10:D10')
        print(f"✅ Updated DUoS rates in B10:D10")
        
        # Update schedule - each time period on separate row
        max_rows = max(len(rates['Red']['schedule']), len(rates['Amber']['schedule']), len(rates['Green']['schedule']))
        
        schedule_rows = []
        for i in range(max_rows):
            row = [
                rates['Red']['schedule'][i] if i < len(rates['Red']['schedule']) else '',
                rates['Amber']['schedule'][i] if i < len(rates['Amber']['schedule']) else '',
                rates['Green']['schedule'][i] if i < len(rates['Green']['schedule']) else ''
            ]
            schedule_rows.append(row)
        
        # Clear any old data first
        bess_ws.batch_clear(['A13:C15'])
        
        # Write schedule
        if schedule_rows:
            # Update time bands starting at row 13
            bess_ws.update(schedule_rows, f'A13:C{12+max_rows}')
            print(f"✅ Updated schedule in A13:C{12+max_rows}")
        
    except Exception as e:
        print(f"⚠️ Could not fetch DUoS rates: {e}")
    
    # Update MPAN details in E10:J10 if supplement or LLFC provided
    try:
        from mpan_detail_extractor import extract_mpan_details
        
        # Get supplement and LLFC from sheet
        supplement_cell = bess_ws.acell('I6').value
        llfc_cell = bess_ws.acell('J6').value
        supplement = supplement_cell.strip() if supplement_cell else None
        llfc = llfc_cell.strip() if llfc_cell else None
        
        if supplement or llfc:
            print(f"\n📋 Extracting MPAN details...")
            mpan_details = extract_mpan_details(
                supplement=supplement,
                llfc=llfc,
                voltage=voltage,
                dno_key=dno_info['dno_key']
            )
            
            # Populate E10:J10
            details_row = [[
                mpan_details['profile_class'],
                mpan_details['meter_registration'],
                mpan_details['voltage_level'],
                mpan_details['duos_charging_class'],
                mpan_details['tariff_id'],
                mpan_details['loss_factor']
            ]]
            
            bess_ws.update(details_row, 'E10:J10')
            print(f"✅ Updated MPAN details in E10:J10")
            print(f"   Profile Class: {mpan_details['profile_class']}")
            print(f"   Meter Registration: {mpan_details['meter_registration']}")
            print(f"   Voltage Level: {mpan_details['voltage_level']}")
            print(f"   DUoS Charging Class: {mpan_details['duos_charging_class']}")
            print(f"   Tariff ID: {mpan_details['tariff_id']}")
            print(f"   Loss Factor: {mpan_details['loss_factor']}")
    
    except Exception as e:
        print(f"   ⚠️  Could not update MPAN details: {e}")
    
    # Update status indicator
    status = [[
        f'✅ {dno_info["dno_name"]}',
        f'MPAN {mpan_id} | {voltage}',
        f'Red: {rates["Red"]["rate"]:.3f} p/kWh',
        f'Updated: {pd.Timestamp.now().strftime("%H:%M:%S")}',
        '',
        '',
        '',
        ''
    ]]
    
    bess_ws.update(status, 'A4:H4')
    bess_ws.format('A4:H4', {
        'backgroundColor': {'red': 0.5, 'green': 0.9, 'blue': 0.5},
        'textFormat': {'bold': True}
    })
    
    print("\n" + "=" * 80)
    print("✅ BESS SHEET UPDATED!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   DNO: {dno_info['dno_name']} ({dno_info['dno_key']})")
    print(f"   MPAN: {mpan_id}")
    print(f"   GSP Group: {dno_info['gsp_group_id']} - {dno_info['gsp_group_name']}")
    print(f"   Voltage: {voltage}")
    print(f"   Red Rate: {rates['Red']['rate']:.4f} p/kWh = £{rates['Red']['rate']*10:.2f}/MWh")
    for time in rates['Red']['schedule']:
        print(f"      {time}")
    print(f"   Amber Rate: {rates['Amber']['rate']:.4f} p/kWh = £{rates['Amber']['rate']*10:.2f}/MWh")
    for time in rates['Amber']['schedule']:
        print(f"      {time}")
    print(f"   Green Rate: {rates['Green']['rate']:.4f} p/kWh = £{rates['Green']['rate']*10:.2f}/MWh")
    for time in rates['Green']['schedule']:
        print(f"      {time}")
    
    return True

def refresh_from_sheet():
    """Read inputs from BESS sheet and update"""
    return update_bess_sheet()

def quick_lookup(mpan_id, voltage='LV'):
    """Quick lookup with command-line args"""
    return update_bess_sheet(mpan_id=mpan_id, voltage=voltage)

if __name__ == "__main__":
    import pandas as pd
    
    if len(sys.argv) > 1:
        # Command-line mode
        mpan = int(sys.argv[1])
        voltage = sys.argv[2] if len(sys.argv) > 2 else 'LV'
        success = quick_lookup(mpan, voltage)
    else:
        # Read from sheet mode
        print("📖 Reading inputs from BESS sheet...")
        success = refresh_from_sheet()
    
    sys.exit(0 if success else 1)
