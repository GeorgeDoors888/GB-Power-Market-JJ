#!/usr/bin/env python3
"""
BtM Sheet DNO Lookup - Automatic DUoS Rate Calculator
Reads postcode/MPAN from BtM sheet, calculates DNO and DUoS rates
Integrated with full MPAN parsing and BigQuery rate lookup

Sheet: BtM (Behind the Meter)
Spreadsheet: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import sys
import requests

# Import MPAN parser for correct distributor ID extraction
try:
    from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
    MPAN_PARSER_AVAILABLE = True
except ImportError:
    MPAN_PARSER_AVAILABLE = False
    print("⚠️  MPAN parser not available, using basic mode")

# Configuration
SHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'  # BtM Dashboard
SHEET_NAME = 'BtM'  # Behind the Meter sheet
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_UK = "uk_energy_prod"
DATASET_GB = "gb_power"
POSTCODE_API = "https://api.postcodes.io/postcodes/"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# BtM Sheet Layout (based on actual BtM sheet structure)
# Input cells (3 methods - priority order):
#   Method 1: MPAN (most accurate)
#     I6: MPAN Supplement (8 digits, last 2 = distributor ID 10-23)
#     J6: MPAN Core (13 digits, first 2 = LLFC region indicator)
#   Method 2: Postcode
#     H6: UK Postcode (e.g., "LS1 2TW") - geographic lookup
#   Method 3: Distributor ID
#     K6: Distributor ID (10-23) - direct DNO selection
#   Voltage:
#     B9: Voltage Level (LV/HV/EHV)
# Output cells:
#   C6: DNO_Key (e.g., "SSE-SEPD")
#   D6: DNO_Name (full name)
#   E6: LLFC (Line Loss Factor Class)
#   F6: Voltage Level confirmed
#   B9-D9: DUoS unit rates (Red/Amber/Green p/kWh)
#   B10-D10: Time schedules for each band
#   E9: Fixed charge (p/day)
#   F9: Capacity charge (p/kVA/day)


def lookup_postcode(postcode):
    """
    Get coordinates from UK postcode using postcodes.io API
    Returns: (latitude, longitude) or None if not found
    """
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
                print(f"   ✅ Coordinates: {lat:.4f}, {lng:.4f}")
                return (lat, lng)

        print(f"   ❌ Postcode not found")
        return None

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def coordinates_to_mpan(lat, lng):
    """
    Map coordinates to DNO MPAN ID using regional boundaries
    """
    print(f"📍 Finding DNO for ({lat:.4f}, {lng:.4f})...")

    regional_guess = {
        # Scotland
        (56.0, 60.0, -7.0, -1.0): 17,  # SSE-SHEPD
        (55.0, 56.0, -5.0, -2.0): 18,  # SP-Distribution

        # North England
        (54.0, 55.5, -3.5, -1.0): 15,  # NPg-NE
        (53.0, 54.5, -2.5, -0.5): 23,  # NPg-Y
        (53.0, 54.0, -3.5, -2.0): 16,  # ENWL
        (53.0, 54.0, -4.0, -2.5): 13,  # SP-Manweb

        # Midlands
        (52.0, 53.5, -3.0, -0.5): 11,  # NGED-EM
        (52.0, 53.0, -3.0, -1.5): 14,  # NGED-WM

        # East England
        (51.5, 53.0, 0.0, 2.0): 10,    # UKPN-EPN

        # London & South East
        (51.3, 51.7, -0.5, 0.3): 12,   # UKPN-LPN
        (50.8, 51.8, -0.5, 1.5): 19,   # UKPN-SPN
        (50.5, 52.0, -2.5, 0.0): 20,   # SSE-SEPD

        # South West & Wales
        (51.0, 52.5, -5.5, -2.5): 21,  # NGED-SWales
        (50.0, 51.5, -6.0, -2.0): 22,  # NGED-SW
    }

    for (lat_min, lat_max, lng_min, lng_max), mpan_id in regional_guess.items():
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            print(f"   ✅ Matched to MPAN ID {mpan_id}")
            return mpan_id

    print(f"   ⚠️  No match - defaulting to London (12)")
    return 12


def parse_mpan_input(input_str):
    """
    Parse MPAN input - supports:
    - Full 13-digit core: "1405566778899"
    - Full 21-digit: "00 801 0840 1405566778899"
    - Simple 2-digit: "14"

    Returns: (mpan_id, mpan_core) tuple
    """
    if not input_str:
        return None, None

    input_clean = str(input_str).strip().replace(' ', '')

    # Ignore instructional text
    if 'Enter' in input_str or 'MPAN' in input_str or '←' in input_str or '→' in input_str:
        print(f"⚠️  Skipping instructional text: {input_str[:50]}")
        return None, None

    # Try as simple 2-digit ID (10-23)
    try:
        mpan_id = int(input_clean)
        if 10 <= mpan_id <= 23:
            print(f"✅ Simple MPAN ID: {mpan_id}")
            return mpan_id, None
    except:
        pass

    # Try full MPAN parsing
    if MPAN_PARSER_AVAILABLE and len(input_clean) >= 13:
        try:
            # Extract core from full MPAN if 21 digits
            if len(input_clean) >= 21:
                core = extract_core_from_full_mpan(input_clean)
                print(f"📋 Extracted core: {core}")
            else:
                core = input_clean[:13]  # Assume it's already core

            # Get distributor ID from first 2 digits of core
            mpan_id = int(core[:2])

            if 10 <= mpan_id <= 23:
                print(f"✅ MPAN ID from core: {mpan_id}")
                return mpan_id, core

        except Exception as e:
            print(f"⚠️  MPAN parsing failed: {e}")

    # Fallback: try first 2 digits
    if len(input_clean) >= 2:
        try:
            mpan_id = int(input_clean[:2])
            if 10 <= mpan_id <= 23:
                print(f"⚠️  Using first 2 digits: {mpan_id}")
                return mpan_id, None
        except:
            pass

    return None, None


def lookup_dno_by_mpan(mpan_id):
    """Lookup DNO information from BigQuery"""
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

    print(f"🔍 Querying BigQuery for MPAN ID {mpan_id}...")
    df = client.query(query).to_dataframe()

    if df.empty:
        print(f"   ❌ No DNO found for MPAN ID {mpan_id}")
        return None

    result = df.iloc[0].to_dict()
    print(f"   ✅ Found: {result['dno_name']}")
    return result


def get_duos_rates(dno_key, voltage_level):
    """
    Get DUoS rates for DNO and voltage level
    Returns: dict with Red/Amber/Green rates and time schedules
    NOTE: gb_power dataset is in EU location!
    """
    client = bigquery.Client(project=PROJECT_ID, location="EU")  # gb_power dataset location

    # Clean voltage level (e.g., "LV (<1kV)" -> "LV")
    voltage = voltage_level.split('(')[0].strip() if voltage_level else "LV"

    print(f"💰 Looking up DUoS rates for {dno_key} {voltage}...")

    # Get rates
    rates_query = f"""
    WITH ranked_rates AS (
        SELECT
            time_band_name,
            ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh,
            effective_from,
            ROW_NUMBER() OVER (
                PARTITION BY time_band_name
                ORDER BY ABS(DATE_DIFF(effective_from, CURRENT_DATE(), DAY))
            ) as rank
        FROM `{PROJECT_ID}.{DATASET_GB}.duos_unit_rates`
        WHERE dno_key = '{dno_key}'
          AND voltage_level = '{voltage}'
        GROUP BY time_band_name, effective_from
    )
    SELECT time_band_name, rate_p_kwh
    FROM ranked_rates
    WHERE rank = 1
    ORDER BY time_band_name
    """

    rates_df = client.query(rates_query).to_dataframe()

    if len(rates_df) == 0:
        print(f"   ⚠️  No rates found, using defaults")
        return {
            'Red': {'rate': 0, 'schedule': []},
            'Amber': {'rate': 0, 'schedule': []},
            'Green': {'rate': 0, 'schedule': []}
        }

    print(f"   ✅ Found {len(rates_df)} rate bands")

    # Get time bands
    time_bands_query = f"""
    SELECT
        time_band_name,
        day_type,
        start_time,
        end_time
    FROM `{PROJECT_ID}.{DATASET_GB}.duos_time_bands`
    WHERE dno_key = '{dno_key}'
    ORDER BY day_type DESC, start_time
    """

    time_bands_df = client.query(time_bands_query).to_dataframe()

    # Build result structure
    rates = {
        'Red': {'rate': 0, 'schedule': []},
        'Amber': {'rate': 0, 'schedule': []},
        'Green': {'rate': 0, 'schedule': []}
    }

    # Populate rates
    for _, row in rates_df.iterrows():
        band = row['time_band_name']
        rates[band]['rate'] = float(row['rate_p_kwh'])

    # Build schedules (weekday only for display)
    weekday_schedule = []
    for _, row in time_bands_df.iterrows():
        if row['day_type'] == 'Weekday':
            band = row['time_band_name']
            start = str(row['start_time'])[:5]  # HH:MM
            end = str(row['end_time'])[:5]
            weekday_schedule.append({'band': band, 'start': start, 'end': end})

    weekday_schedule.sort(key=lambda x: x['start'])

    for entry in weekday_schedule:
        rates[entry['band']]['schedule'].append(f"{entry['start']}-{entry['end']}")

    # Add weekend note
    has_weekend = any(row['day_type'] == 'Weekend' for _, row in time_bands_df.iterrows())
    if has_weekend:
        rates['Green']['schedule'].append('All Weekend')

    return rates


def update_btm_sheet(dno_data, rates_data):
    """
    Update BtM sheet with DNO details and DUoS rates

    Output cells:
    - C6: DNO_Key
    - D6: DNO_Name
    - B9: Red rate (p/kWh)
    - C9: Amber rate
    - D9: Green rate
    - B10-D12: Time schedules
    """
    print(f"📝 Updating BtM sheet...")

    # Connect to Google Sheets
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    # Update DNO details (C6:D6)
    sheet.update('C6', [[dno_data['dno_key']]])
    sheet.update('D6', [[dno_data['dno_name']]])

    print(f"   ✅ Updated DNO: {dno_data['dno_key']}")

    # Update DUoS rates (B9:D9)
    rates_row = [
        [
            rates_data['Red']['rate'],
            rates_data['Amber']['rate'],
            rates_data['Green']['rate']
        ]
    ]
    sheet.update('B9:D9', rates_row)

    print(f"   ✅ Updated rates: Red={rates_data['Red']['rate']:.3f}, "
          f"Amber={rates_data['Amber']['rate']:.3f}, "
          f"Green={rates_data['Green']['rate']:.3f} p/kWh")

    # Update time schedules (B10:D12)
    # Row 10: Red times
    # Row 11: Amber times
    # Row 12: Green times

    red_times = ' | '.join(rates_data['Red']['schedule'][:2])
    amber_times = ' | '.join(rates_data['Amber']['schedule'][:2])
    green_times = ' | '.join(rates_data['Green']['schedule'][:2])

    schedules = [
        [red_times, amber_times, green_times]
    ]
    sheet.update('B10:D10', schedules)

    print(f"   ✅ Updated time schedules")

    # Add a status timestamp (optional - if sheet has a status cell)
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return True


def main():
    """
    Main execution flow:
    1. Read postcode/MPAN from BtM sheet
    2. Determine DNO
    3. Lookup DUoS rates
    4. Update sheet with results
    """
    print("=" * 80)
    print("BtM SHEET DNO LOOKUP - DUoS Rate Calculator")
    print("=" * 80)
    print()

    # Connect to Google Sheets to read inputs
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    # Read input cells - 3 methods supported
    # Priority: MPAN > Postcode > Distributor ID
    # I6: MPAN Supplement (e.g., "00801520") - last 2 digits = distributor ID
    # J6: MPAN Core (e.g., "2412345678904") - 13-digit identifier
    # H6: Postcode (e.g., "LS1 2TW") - geographic lookup
    # K6: Distributor ID (10-23) - direct selection
    mpan_supplement = sheet.acell('I6').value or ''
    mpan_core = sheet.acell('J6').value or ''
    postcode = sheet.acell('H6').value or ''
    dist_id_input = sheet.acell('K6').value or ''
    voltage = sheet.acell('B9').value or 'LV'

    # Clean instructional text from cells
    if mpan_supplement and ('Enter' in str(mpan_supplement) or '←' in str(mpan_supplement) or 'Supplement' in str(mpan_supplement)):
        mpan_supplement = ''
    if mpan_core and ('Enter' in str(mpan_core) or '←' in str(mpan_core) or 'Core' in str(mpan_core) or 'MPAN' in str(mpan_core)):
        mpan_core = ''
    if postcode and ('Enter' in str(postcode) or '←' in str(postcode) or 'Postcode' in str(postcode)):
        postcode = ''
    if dist_id_input and ('Enter' in str(dist_id_input) or '←' in str(dist_id_input) or 'ID' in str(dist_id_input)):
        dist_id_input = ''

    print(f"📊 Reading from BtM sheet:")
    print(f"   MPAN Supplement (I6): {mpan_supplement or 'Not set'}")
    print(f"   MPAN Core (J6): {mpan_core or 'Not set'}")
    print(f"   Postcode (H6): {postcode or 'Not set'}")
    print(f"   Distributor ID (K6): {dist_id_input or 'Not set'}")
    print(f"   Voltage (B9): {voltage}")
    print()

    # Determine MPAN ID - try all 3 methods in priority order
    mpan_id = None
    input_method = None

    # Method 1: Extract distributor ID from MPAN supplement (most accurate)
    if mpan_supplement:
        supplement_clean = str(mpan_supplement).strip()
        if len(supplement_clean) >= 2:
            try:
                # Last 2 digits of supplement = distributor ID
                mpan_id = int(supplement_clean[-2:])
                if 10 <= mpan_id <= 23:
                    print(f"✅ Method 1: Extracted distributor ID {mpan_id} from MPAN supplement {supplement_clean}")
                    input_method = "MPAN"
                else:
                    print(f"⚠️  Invalid distributor ID {mpan_id} (must be 10-23)")
                    mpan_id = None
            except ValueError:
                print(f"⚠️  Could not parse supplement: {supplement_clean}")

    # Method 2: Postcode lookup (geographic)
    if not mpan_id and postcode:
        print(f"📍 Method 2: Trying postcode lookup...")
        coords = lookup_postcode(postcode)
        if coords:
            lat, lng = coords
            mpan_id = coordinates_to_mpan(lat, lng)
            if mpan_id:
                input_method = "Postcode"
                print(f"✅ Found distributor ID {mpan_id} from postcode {postcode}")

    # Method 3: Direct distributor ID (manual selection)
    if not mpan_id and dist_id_input:
        try:
            mpan_id = int(str(dist_id_input).strip())
            if 10 <= mpan_id <= 23:
                print(f"✅ Method 3: Using direct distributor ID {mpan_id}")
                input_method = "Direct ID"
            else:
                print(f"⚠️  Invalid distributor ID {mpan_id} (must be 10-23)")
                mpan_id = None
        except ValueError:
            print(f"⚠️  Could not parse distributor ID: {dist_id_input}")


    if not mpan_id:
        print("❌ ERROR: Could not determine DNO")
        print("   Please provide ONE of the following:")
        print("")
        print("   Method 1 - MPAN (most accurate):")
        print("     I6: MPAN Supplement (8 digits, last 2 = distributor ID 10-23)")
        print("     J6: MPAN Core (13 digits)")
        print("     Example: I6='00801520' (ends in 20) → SSE-SEPD")
        print("")
        print("   Method 2 - Postcode (geographic lookup):")
        print("     H6: UK Postcode")
        print("     Example: H6='LS1 2TW' → Northern Powergrid Yorkshire")
        print("")
        print("   Method 3 - Distributor ID (direct):")
        print("     K6: Distributor ID (10-23)")
        print("     Example: K6='20' → SSE-SEPD")
        return 1

    print()
    print(f"🎯 Using MPAN ID: {mpan_id} (via {input_method})")
    print()

    # Lookup DNO details
    dno_data = lookup_dno_by_mpan(mpan_id)
    if not dno_data:
        print("❌ ERROR: DNO lookup failed")
        return 1

    print()
    print(f"✅ DNO Details:")
    print(f"   Key: {dno_data['dno_key']}")
    print(f"   Name: {dno_data['dno_name']}")
    print(f"   Region: {dno_data['gsp_group_name']}")
    print()

    # Get DUoS rates
    rates_data = get_duos_rates(dno_data['dno_key'], voltage)

    print()
    print(f"💰 DUoS Rates ({voltage}):")
    print(f"   Red:   {rates_data['Red']['rate']:.4f} p/kWh - {', '.join(rates_data['Red']['schedule'][:2])}")
    print(f"   Amber: {rates_data['Amber']['rate']:.4f} p/kWh - {', '.join(rates_data['Amber']['schedule'][:2])}")
    print(f"   Green: {rates_data['Green']['rate']:.4f} p/kWh - {', '.join(rates_data['Green']['schedule'][:2])}")
    print()

    # Update sheet
    success = update_btm_sheet(dno_data, rates_data)

    if success:
        print("=" * 80)
        print("✅ BtM SHEET UPDATED SUCCESSFULLY")
        print("=" * 80)
        print()
        print(f"🔗 View sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/")
        return 0
    else:
        print("❌ ERROR: Failed to update sheet")
        return 1


if __name__ == "__main__":
    sys.exit(main())
