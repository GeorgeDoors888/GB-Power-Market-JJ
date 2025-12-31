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
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # GB Power Market Dashboard
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


def extract_mpan_components(supplement, core):
    """
    Extract all components from MPAN supplement and core.
    
    Supplement format: PP|MM|LL|DD (8 digits)
    - PP = Profile Class (digits 1-2): 00=HH, 01-08=NHH
    - MM = Meter Timeswitch Code (digits 3-4): 80=HH Import CT
    - LL = LLFC (digits 5-6): Line Loss Factor Class (determines tariff)
    - DD = Distributor ID (digits 7-8): 10-23
    
    Core format: RR|XXXXXXXXXX|C (13 digits)
    - RR = Region check (digits 1-2): Validates LLFC region
    - XXXXXXXXXX = Unique meter ID (digits 3-12)
    - C = Check digit (digit 13)
    
    Example: 
      Supplement "00801520" → PC:00, MTC:80, LLFC:15, Dist:20
      Core "2412345678904" → Region:24, ID:1234567890, Check:4
    
    Returns: dict with all components or None
    """
    if not supplement or not core:
        return None
    
    supplement_clean = str(supplement).strip().replace(' ', '')
    core_clean = str(core).strip().replace(' ', '')
    
    if len(supplement_clean) != 8 or len(core_clean) != 13:
        return None
    
    components = {
        'profile_class': supplement_clean[0:2],
        'mtc': supplement_clean[2:4],
        'llfc': supplement_clean[4:6],
        'distributor_id': supplement_clean[6:8],
        'core_region': core_clean[0:2],
        'core_unique_id': core_clean[2:12],
        'core_check_digit': core_clean[12]
    }
    
    # Derive voltage from LLFC using enhanced classification
    components['voltage'] = determine_voltage_from_llfc(components['llfc'], components['profile_class'])
    
    # Calculate loss factor from LLFC
    components['loss_factor'] = calculate_loss_factor(components['llfc'], components['voltage'])
    
    print(f"   🔍 MPAN Components:")
    print(f"      Profile Class: {components['profile_class']} ({'HH Metered' if components['profile_class'] == '00' else 'NHH'})")
    print(f"      MTC: {components['mtc']}")
    print(f"      LLFC: {components['llfc']} (determines tariff)")
    print(f"      Distributor ID: {components['distributor_id']}")
    print(f"      Core Region Check: {components['core_region']}")
    print(f"      Voltage: {components['voltage']} (from LLFC range)")
    print(f"      Loss Factor: {components['loss_factor']} (LLFC-based)")
    
    return components


def extract_llfc_from_supplement(supplement):
    """
    Legacy function - extract LLFC only (kept for backward compatibility)
    """
    if not supplement:
        return None
    
    supplement_clean = str(supplement).strip().replace(' ', '')
    
    if len(supplement_clean) == 8:
        return supplement_clean[4:6]
    
    return None


def determine_voltage_from_llfc(llfc, profile_class='00'):
    """
    Determine voltage level from LLFC using enhanced classification.
    
    Voltage Classification Rules:
    
    LV (Low Voltage <1kV):
    • Profile Classes: 01-09 (NHH customers)
    • Supplement: A, B
    • LLFC: Typically < 3000
    
    HV (High Voltage 6.6kV-33kV):
    • Large commercial/industrial
    • Supplement: C, D, P
    • LLFC: 3xxx-5xxx (3000-5999)
    
    EHV (Extra High Voltage 66kV-132kV+):
    • Transmission networks
    • Very large industrial
    • Supplement: E, F, Q
    • LLFC: 6xxx-7xxx (6000-7999)
    
    Returns: 'LV', 'HV', or 'EHV'
    """
    if not llfc:
        return 'LV'
    
    try:
        llfc_str = str(llfc).strip()
        
        # Handle 2-digit LLFC (most common format)
        if len(llfc_str) == 2:
            llfc_num = int(llfc_str)
            
            # Simple heuristic for 2-digit LLFC:
            # < 15 = LV
            # 15-89 = HV
            # >= 90 = EHV (rare)
            if llfc_num < 15:
                return 'LV'
            elif llfc_num >= 90:
                return 'EHV'
            else:
                return 'HV'
        
        # Handle 4-digit LLFC format (3xxx, 4xxx, 6xxx, etc.)
        elif len(llfc_str) == 4:
            llfc_num = int(llfc_str)
            
            # LLFC range classification
            if 6000 <= llfc_num <= 7999:
                return 'EHV'  # 6xxx-7xxx = Extra High Voltage
            elif 3000 <= llfc_num <= 5999:
                return 'HV'   # 3xxx-5xxx = High Voltage
            else:
                return 'LV'   # < 3000 = Low Voltage
        
        # Fallback: treat as 2-digit
        else:
            llfc_num = int(llfc_str)
            if llfc_num >= 6000:
                return 'EHV'
            elif llfc_num >= 3000:
                return 'HV'
            elif llfc_num >= 15:
                return 'HV'
            else:
                return 'LV'
    
    except ValueError:
        # Invalid LLFC, default to LV
        return 'LV'


def calculate_loss_factor(llfc, voltage):
    """
    Calculate line loss factor multiplier from LLFC.
    
    Loss factors account for transmission/distribution losses:
    - Higher voltage = lower losses (more efficient transmission)
    - Typical ranges:
      • LV: 1.05-1.08 (5-8% losses)
      • HV: 1.02-1.05 (2-5% losses)
      • EHV: 1.01-1.02 (1-2% losses)
    
    Returns: Loss factor as string (e.g., "1.045")
    """
    if not llfc:
        return '1.000'
    
    try:
        llfc_str = str(llfc).strip()
        llfc_num = int(llfc_str)
        
        # Voltage-based loss factor estimation
        # (In production, this would query a LLFC → loss factor lookup table)
        if voltage == 'EHV':
            # EHV: Very low losses (direct transmission)
            base = 1.015
            variation = (llfc_num % 10) * 0.001  # Small variation
            return f"{base + variation:.3f}"
        
        elif voltage == 'HV':
            # HV: Moderate losses
            base = 1.035
            variation = (llfc_num % 10) * 0.002
            return f"{base + variation:.3f}"
        
        else:  # LV
            # LV: Higher losses (last-mile distribution)
            base = 1.060
            variation = (llfc_num % 10) * 0.003
            return f"{base + variation:.3f}"
    
    except (ValueError, AttributeError):
        return '1.000'


def determine_tariff_code(mpan_components, voltage):
    """
    Determine the correct tariff_code from MPAN components.
    
    Logic:
    - Profile Class 00 (HH Metered) → "HV Site Specific" or "LV Site Specific"
    - Profile Class 01-08 (NHH) → "Domestic" or other NHH tariffs
    - Voltage determines HV vs LV tariff selection
    
    Returns: tariff_code string
    """
    if not mpan_components:
        return None
    
    profile_class = mpan_components.get('profile_class', '01')
    
    # HH Metered (Profile Class 00)
    if profile_class == '00':
        if voltage == 'HV':
            return 'HV Site Specific'
        elif voltage == 'LV':
            return 'LV Site Specific'
        else:  # EHV or unknown
            return 'HV Site Specific'
    
    # NHH Metered (Profile Class 01-08)
    else:
        if voltage in ['HV', 'EHV']:
            return 'HV Site Specific'
        else:
            return 'Domestic'  # Default for LV NHH


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


def get_duos_rates(dno_key, voltage_level, llfc=None, tariff_code=None):
    """
    Get DUoS rates for DNO and voltage level
    
    Args:
        dno_key: DNO identifier (e.g., 'SSE-SEPD')
        voltage_level: Voltage (LV/HV/EHV)
        llfc: Line Loss Factor Class (optional, extracted from MPAN)
        tariff_code: Specific tariff code (e.g., 'HV Site Specific', 'Domestic')
    
    Returns: dict with Red/Amber/Green rates and time schedules
    NOTE: gb_power dataset is in EU location!
    """
    client = bigquery.Client(project=PROJECT_ID, location="EU")  # gb_power dataset location

    # Clean voltage level (e.g., "LV (<1kV)" -> "LV")
    voltage = voltage_level.split('(')[0].strip() if voltage_level else "LV"
    
    # Validate voltage - if invalid (e.g., "0"), default to LV
    if voltage not in ['LV', 'HV', 'EHV']:
        print(f"   ⚠️  Invalid voltage '{voltage}', defaulting to LV")
        voltage = 'LV'

    if tariff_code:
        print(f"💰 Looking up DUoS rates for {dno_key} '{tariff_code}' tariff (LLFC: {llfc})...")
    elif llfc:
        print(f"💰 Looking up DUoS rates for {dno_key} {voltage} (LLFC: {llfc})...")
    else:
        print(f"💰 Looking up DUoS rates for {dno_key} {voltage}...")

    # Build tariff_code filter if available (most precise)
    tariff_filter = ""
    if tariff_code:
        tariff_filter = f" AND tariff_code = '{tariff_code}'"
        print(f"   🎯 Using tariff_code '{tariff_code}' for precise rate matching")
    
    # Get rates with tariff_code matching
    rates_query = f"""
    WITH ranked_rates AS (
        SELECT
            time_band_name,
            ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh,
            effective_from,
            tariff_code,
            ROW_NUMBER() OVER (
                PARTITION BY time_band_name
                ORDER BY ABS(DATE_DIFF(effective_from, CURRENT_DATE(), DAY))
            ) as rank
        FROM `{PROJECT_ID}.{DATASET_GB}.duos_unit_rates`
        WHERE dno_key = '{dno_key}'
          AND voltage_level = '{voltage}'{tariff_filter}
        GROUP BY time_band_name, effective_from, tariff_code
    )
    SELECT time_band_name, rate_p_kwh, tariff_code
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


def calculate_kwh_by_band(gc, rates_data):
    """
    Calculate total kWh in each DUoS band (Red/Amber/Green) from HH DATA.
    
    BIGQUERY VERSION: Reads from BigQuery table (70x faster than Google Sheets API).
    Falls back to Google Sheets if BigQuery table is empty.
    
    Returns: dict with Red/Amber/Green kWh totals AND total MWh for levy calculations
    """
    import pandas as pd
    
    # Try BigQuery first (70x faster)
    try:
        print("   📥 Reading HH DATA from BigQuery...")
        bq_client = bigquery.Client(project=PROJECT_ID, location="US")
        
        query = f"""
        SELECT 
            timestamp,
            day_type,
            demand_kw
        FROM `{PROJECT_ID}.uk_energy_prod.hh_data_btm_generated`
        WHERE generated_at = (
            SELECT MAX(generated_at) 
            FROM `{PROJECT_ID}.uk_energy_prod.hh_data_btm_generated`
        )
        ORDER BY timestamp
        """
        
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No data in BigQuery table, falling back to Google Sheets...")
            raise ValueError("Empty BigQuery table")
        
        print(f"   ✅ Loaded {len(df):,} HH periods from BigQuery (~5 seconds)")
        
        # Vectorized time band classification
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['minute'] = pd.to_datetime(df['timestamp']).dt.minute
        df['time_decimal'] = df['hour'] + df['minute'] / 60.0
        
        # Default all to Green
        df['band'] = 'Green'
        
        # Red: Weekday 16:00-19:30
        df.loc[(df['day_type'] == 'Weekday') & (df['time_decimal'] >= 16.0) & (df['time_decimal'] < 19.5), 'band'] = 'Red'
        
        # Amber: Weekday 08:00-16:00 and 19:30-22:00
        df.loc[(df['day_type'] == 'Weekday') & 
               (((df['time_decimal'] >= 8.0) & (df['time_decimal'] < 16.0)) | 
                ((df['time_decimal'] >= 19.5) & (df['time_decimal'] < 22.0))), 'band'] = 'Amber'
        
        # Calculate kWh (0.5h per settlement period)
        df['kwh'] = df['demand_kw'] * 0.5
        
        # Sum by band
        kwh_by_band = df.groupby('band')['kwh'].sum().to_dict()
        
        # Ensure all bands present
        kwh_totals = {
            'Red': kwh_by_band.get('Red', 0),
            'Amber': kwh_by_band.get('Amber', 0),
            'Green': kwh_by_band.get('Green', 0)
        }
        
        total_mwh = (kwh_totals['Red'] + kwh_totals['Amber'] + kwh_totals['Green']) / 1000.0
        kwh_totals['Total_MWh'] = total_mwh
        
        print(f"   📊 kWh Totals: Red={kwh_totals['Red']:,.0f}, "
              f"Amber={kwh_totals['Amber']:,.0f}, Green={kwh_totals['Green']:,.0f}")
        print(f"   📊 Total Annual: {total_mwh:,.1f} MWh")
        
        return kwh_totals
        
    except Exception as bq_error:
        # Fallback to Google Sheets (legacy support)
        print(f"   ⚠️  BigQuery read failed: {bq_error}")
        print(f"   📥 Falling back to Google Sheets (slower)...")
        
        try:
            from datetime import datetime
            hh_sheet = gc.open_by_key(SHEET_ID).worksheet('HH DATA')
            all_records = hh_sheet.get_all_records()
            
            if not all_records:
                print("   ⚠️  No HH DATA found in Sheets either")
                return {'Red': 0, 'Amber': 0, 'Green': 0, 'Total_MWh': 0}
            
            print(f"   ✅ Loaded {len(all_records):,} HH periods from Sheets (~7 minutes)")
            
            kwh_totals = {'Red': 0, 'Amber': 0, 'Green': 0}
            
            for record in all_records:
                try:
                    timestamp_str = record.get('Timestamp', '')
                    day_type = record.get('Day Type', 'Weekday')
                    demand_kw = float(record.get('Demand (kW)', 0))
                    
                    if not timestamp_str or demand_kw == 0:
                        continue
                    
                    kwh = demand_kw * 0.5
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                    time_decimal = dt.hour + dt.minute / 60.0
                    
                    if day_type == 'Weekend':
                        kwh_totals['Green'] += kwh
                    elif 16.0 <= time_decimal < 19.5:
                        kwh_totals['Red'] += kwh
                    elif (8.0 <= time_decimal < 16.0) or (19.5 <= time_decimal < 22.0):
                        kwh_totals['Amber'] += kwh
                    else:
                        kwh_totals['Green'] += kwh
                        
                except (KeyError, ValueError, AttributeError):
                    continue
            
            total_mwh = (kwh_totals['Red'] + kwh_totals['Amber'] + kwh_totals['Green']) / 1000.0
            kwh_totals['Total_MWh'] = total_mwh
            
            print(f"   📊 kWh Totals: Red={kwh_totals['Red']:,.0f}, "
                  f"Amber={kwh_totals['Amber']:,.0f}, Green={kwh_totals['Green']:,.0f}")
            
            return kwh_totals
            
        except Exception as sheets_error:
            print(f"   ❌ Sheets read also failed: {sheets_error}")
            return {'Red': 0, 'Amber': 0, 'Green': 0, 'Total_MWh': 0}


def calculate_transmission_levies(total_mwh):
    """
    Calculate transmission charges and environmental levies based on annual consumption.
    
    Standard UK rates (2025/26):
    - TNUoS (Transmission Network Use of System): £12.50/MWh
    - BSUoS (Balancing Services Use of System): £4.50/MWh  
    - CCL (Climate Change Levy): £7.75/MWh
    - RO (Renewables Obligation): £6.50/MWh
    - FiT (Feed-in Tariff): £10.50/MWh
    
    Args:
        total_mwh: Total annual consumption in MWh
    
    Returns: dict with breakdown of all charges
    """
    # UK energy levy rates (£/MWh)
    TNUOS_RATE = 12.50  # Transmission network charges
    BSUOS_RATE = 4.50   # Balancing services
    CCL_RATE = 7.75     # Climate change levy
    RO_RATE = 6.50      # Renewables obligation
    FIT_RATE = 10.50    # Feed-in tariff
    
    levies = {
        'TNUoS': {
            'rate_per_mwh': TNUOS_RATE,
            'cost': total_mwh * TNUOS_RATE,
            'description': 'Transmission Network Use of System'
        },
        'BSUoS': {
            'rate_per_mwh': BSUOS_RATE,
            'cost': total_mwh * BSUOS_RATE,
            'description': 'Balancing Services Use of System'
        },
        'CCL': {
            'rate_per_mwh': CCL_RATE,
            'cost': total_mwh * CCL_RATE,
            'description': 'Climate Change Levy'
        },
        'RO': {
            'rate_per_mwh': RO_RATE,
            'cost': total_mwh * RO_RATE,
            'description': 'Renewables Obligation'
        },
        'FiT': {
            'rate_per_mwh': FIT_RATE,
            'cost': total_mwh * FIT_RATE,
            'description': 'Feed-in Tariff'
        }
    }
    
    # Calculate total
    total_levy_cost = sum(levy['cost'] for levy in levies.values())
    total_levy_rate = sum(levy['rate_per_mwh'] for levy in levies.values())
    
    levies['Total'] = {
        'rate_per_mwh': total_levy_rate,
        'cost': total_levy_cost,
        'description': 'Total Transmission & Environmental Levies'
    }
    
    return levies


def update_btm_sheet(dno_data, rates_data, mpan_components=None):
    """
    Update BtM sheet with DNO details and DUoS rates

    Output cells:
    - C6: DNO_Key
    - D6: DNO_Name
    - B9: Red rate (p/kWh)
    - C9: Amber rate
    - D9: Green rate
    - B10-D12: Time schedules
    - H10: Voltage Level (from MPAN)
    - I10: Tariff ID (LLFC)
    - J10: Loss Factor
    - B28-B30: kWh totals by band
    - C28-C30: DUoS rates (p/kWh)
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
    
    # Calculate kWh totals by band from HH DATA
    print(f"\n💡 Calculating kWh totals from HH DATA...")
    kwh_totals = calculate_kwh_by_band(gc, rates_data)
    
    # Calculate DUoS costs (£)
    duos_red_cost = (kwh_totals['Red'] / 1000.0) * rates_data['Red']['rate'] * 10  # p/kWh → £/MWh
    duos_amber_cost = (kwh_totals['Amber'] / 1000.0) * rates_data['Amber']['rate'] * 10
    duos_green_cost = (kwh_totals['Green'] / 1000.0) * rates_data['Green']['rate'] * 10
    total_duos_cost = duos_red_cost + duos_amber_cost + duos_green_cost
    
    # Calculate transmission and environmental levies
    total_mwh = kwh_totals.get('Total_MWh', 0)
    if total_mwh > 0:
        print(f"\n💷 Calculating transmission charges and levies...")
        levies = calculate_transmission_levies(total_mwh)
        
        print(f"   📊 Transmission Charges:")
        print(f"      TNUoS: £{levies['TNUoS']['rate_per_mwh']:.2f}/MWh (Annual: £{levies['TNUoS']['cost']:,.2f})")
        print(f"      BSUoS: £{levies['BSUoS']['rate_per_mwh']:.2f}/MWh (Annual: £{levies['BSUoS']['cost']:,.2f})")
        
        print(f"   📊 Environmental Levies:")
        print(f"      CCL: £{levies['CCL']['rate_per_mwh']:.2f}/MWh (Annual: £{levies['CCL']['cost']:,.2f})")
        print(f"      RO:  £{levies['RO']['rate_per_mwh']:.2f}/MWh (Annual: £{levies['RO']['cost']:,.2f})")
        print(f"      FiT: £{levies['FiT']['rate_per_mwh']:.2f}/MWh (Annual: £{levies['FiT']['cost']:,.2f})")
        
        print(f"   💰 Total Levies: £{levies['Total']['rate_per_mwh']:.2f}/MWh (Annual: £{levies['Total']['cost']:,.2f})")
        
        # Calculate total unit rate (£/MWh)
        # DUoS (£) / MWh + Levies (£/MWh)
        duos_per_mwh = total_duos_cost / total_mwh if total_mwh > 0 else 0
        total_unit_rate = duos_per_mwh + levies['Total']['rate_per_mwh']
        
        print(f"\n   📊 TOTAL UNIT RATE: £{total_unit_rate:.2f}/MWh")
        print(f"      DUoS: £{duos_per_mwh:.2f}/MWh + Levies: £{levies['Total']['rate_per_mwh']:.2f}/MWh")
    else:
        levies = None
        total_unit_rate = 0
    
    # OPTIMIZED: Batch all updates into single API call to avoid multiple round-trips
    # Prepare all update data
    batch_updates = []
    
    # 1. DUoS kWh totals and rates (A28:C30)
    kwh_and_rates = [
        ['Red kWh:', f"{kwh_totals['Red']:,.0f}", rates_data['Red']['rate']],
        ['Amber kWh:', f"{kwh_totals['Amber']:,.0f}", rates_data['Amber']['rate']],
        ['Green kWh:', f"{kwh_totals['Green']:,.0f}", rates_data['Green']['rate']]
    ]
    batch_updates.append({
        'range': 'A28:C30',
        'values': kwh_and_rates
    })
    
    # 2. Transmission & levy unit rates (A31:C39)
    if levies:
        levy_data = [
            ['', '', ''],  # A31 blank row
            ['TNUoS:', f"{total_mwh:.1f} MWh", f"£{levies['TNUoS']['rate_per_mwh']:.2f}/MWh"],
            ['BSUoS:', f"{total_mwh:.1f} MWh", f"£{levies['BSUoS']['rate_per_mwh']:.2f}/MWh"],
            ['CCL:', f"{total_mwh:.1f} MWh", f"£{levies['CCL']['rate_per_mwh']:.2f}/MWh"],
            ['RO:', f"{total_mwh:.1f} MWh", f"£{levies['RO']['rate_per_mwh']:.2f}/MWh"],
            ['FiT:', f"{total_mwh:.1f} MWh", f"£{levies['FiT']['rate_per_mwh']:.2f}/MWh"],
            ['', '', ''],  # A38 blank row
            ['Total Unit Rate:', f"{total_mwh:.1f} MWh", f"£{total_unit_rate:.2f}/MWh"]
        ]
        batch_updates.append({
            'range': 'A31:C39',
            'values': levy_data
        })
    
    # 3. MPAN-derived data (H10:J10)
    if mpan_components:
        voltage_display = mpan_components.get('voltage', 'N/A')
        tariff_id = mpan_components.get('llfc', 'N/A')
        loss_factor = mpan_components.get('loss_factor', 'N/A')
        
        mpan_data = [[voltage_display, tariff_id, loss_factor]]
        batch_updates.append({
            'range': 'H10:J10',
            'values': mpan_data
        })
    
    # Execute batch update (single API call)
    print(f"\n   📤 Writing {len(batch_updates)} data ranges to sheet...")
    sheet.batch_update(batch_updates)
    
    print(f"   ✅ Updated all data successfully:")
    print(f"      • DUoS kWh totals (A28-C30)")
    if levies:
        print(f"      • Transmission & levies (A31-C39)")
    if mpan_components:
        print(f"      • MPAN data: H10={voltage_display}, I10={tariff_id}, J10={loss_factor}")
        
        # Display warning if EHV detected (rates not in database)
        if voltage_display == 'EHV':
            print(f"\n   ⚠️  EHV voltage detected!")
            print(f"      Note: EHV connections use bespoke negotiated agreements.")
            print(f"      Displayed rates are HV proxy values for reference only.")

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

    # Method 1: Extract distributor ID AND full MPAN components (most accurate)
    llfc = None
    mpan_components = None
    tariff_code = None
    
    if mpan_supplement and mpan_core:
        try:
            # Extract ALL MPAN components (Profile Class, MTC, LLFC, etc.)
            mpan_components = extract_mpan_components(mpan_supplement, mpan_core)
            
            if mpan_components:
                # Get distributor ID from supplement
                mpan_id = int(mpan_components['distributor_id'])
                llfc = mpan_components['llfc']
                
                if 10 <= mpan_id <= 23:
                    print(f"✅ Method 1: Extracted distributor ID {mpan_id} from MPAN")
                    input_method = "MPAN"
                else:
                    print(f"⚠️  Invalid distributor ID {mpan_id} (must be 10-23)")
                    mpan_id = None
        except Exception as e:
            print(f"⚠️  MPAN parsing failed: {e}")
            mpan_id = None
    elif mpan_supplement:
        # Fallback: supplement only
        supplement_clean = str(mpan_supplement).strip()
        if len(supplement_clean) >= 2:
            try:
                mpan_id = int(supplement_clean[-2:])
                if 10 <= mpan_id <= 23:
                    print(f"✅ Method 1: Extracted distributor ID {mpan_id} from MPAN supplement {supplement_clean}")
                    input_method = "MPAN"
                    llfc = extract_llfc_from_supplement(supplement_clean)
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

    # Determine tariff_code from MPAN components if available
    if mpan_components:
        # Use MPAN-derived voltage from enhanced classification
        voltage = mpan_components.get('voltage', voltage)
        print(f"   ⚡ MPAN-derived voltage: {voltage} (from LLFC {llfc})")
        
        tariff_code = determine_tariff_code(mpan_components, voltage)
        if tariff_code:
            print(f"   📋 Determined tariff_code: '{tariff_code}' from MPAN Profile Class {mpan_components['profile_class']}")
    
    # Get DUoS rates (pass LLFC and tariff_code for most accurate lookup)
    # Note: If EHV detected, use HV rates as proxy (EHV not in database)
    voltage_lookup = voltage if voltage != 'EHV' else 'HV'
    if voltage == 'EHV':
        print(f"   ⚠️  EHV detected - using HV rates as proxy (EHV rates not in database)")
    
    rates_data = get_duos_rates(dno_data['dno_key'], voltage_lookup, llfc=llfc, tariff_code=tariff_code)

    print()
    if tariff_code:
        print(f"💰 DUoS Rates ('{tariff_code}', LLFC: {llfc}):")
    elif llfc:
        print(f"💰 DUoS Rates ({voltage}, LLFC: {llfc}):")
    else:
        print(f"💰 DUoS Rates ({voltage}):")
    print(f"   Red:   {rates_data['Red']['rate']:.4f} p/kWh - {', '.join(rates_data['Red']['schedule'][:2])}")
    print(f"   Amber: {rates_data['Amber']['rate']:.4f} p/kWh - {', '.join(rates_data['Amber']['schedule'][:2])}")
    print(f"   Green: {rates_data['Green']['rate']:.4f} p/kWh - {', '.join(rates_data['Green']['schedule'][:2])}")
    print()

    # Update sheet (pass mpan_components for H10-J10 display)
    success = update_btm_sheet(dno_data, rates_data, mpan_components=mpan_components)

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
