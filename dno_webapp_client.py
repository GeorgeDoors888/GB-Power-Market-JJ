#!/usr/bin/env python3
"""
DNO Lookup via Apps Script Web App
Supports BOTH postcode and MPAN/Distributor ID lookup
Simple HTTP POST to update BESS sheet - no Apps Script API needed!
"""

import json
import requests
from google.cloud import bigquery
import sys
import re

# ⚠️ CONFIGURE THESE AFTER DEPLOYMENT
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzM2B4EVzKnY1vG27wzdkdPc7PqZFKYLZxaaYvYYIQLixR6CmRyY6mJOuR9brSIky9x/exec"
API_SECRET = "gb_power_dno_lookup_2025"  # Must match Apps Script

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_UK = "uk_energy_prod"
DATASET_GB = "gb_power"

POSTCODE_API = "https://api.postcodes.io/postcodes/"

def lookup_postcode(postcode):
    """
    Get coordinates from UK postcode using postcodes.io API
    Returns: (latitude, longitude) or None if not found
    """
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
    Uses BigQuery spatial query if boundary data available
    Falls back to regional approximation
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

def lookup_dno_by_mpan(mpan_id):
    """Query BigQuery for DNO info by MPAN/Distributor ID"""
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

def get_duos_rates(dno_key, voltage_level):
    """Query BigQuery for DUoS rates
    NOTE: gb_power dataset is in EU location!
    """
    client = bigquery.Client(project=PROJECT_ID, location="EU")  # gb_power dataset location
    
    query = f"""
    SELECT 
        time_band_name,
        ROUND(AVG(unit_rate_p_kwh), 4) as rate_p_kwh
    FROM `{PROJECT_ID}.{DATASET_GB}.duos_unit_rates`
    WHERE dno_key = '{dno_key}'
      AND voltage_level = '{voltage_level}'
      AND (tariff_code LIKE '%Non-Domestic%' OR tariff_code LIKE '%Site Specific%')
    GROUP BY time_band_name
    ORDER BY time_band_name
    """
    
    df = client.query(query).to_dataframe()
    
    rates = {'red': 0, 'amber': 0, 'green': 0}
    for _, row in df.iterrows():
        rates[row['time_band_name'].lower()] = float(row['rate_p_kwh'])
    
    return rates

def read_sheet_inputs():
    """Read current inputs from BESS sheet"""
    payload = {
        "secret": API_SECRET,
        "action": "read_inputs"
    }
    
    res = requests.post(
        WEB_APP_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    
    if res.status_code == 200:
        data = res.json()
        return data.get('inputs', {})
    else:
        raise Exception(f"Failed to read inputs: {res.text}")

def update_sheet_full(mpan_id, dno_data, rates):
    """Send updates to BESS sheet via web app (using 3 separate calls)"""
    from datetime import datetime
    
    headers = {"Content-Type": "application/json"}
    results = []
    
    # Step 1: Update DNO info (A6:H6)
    print("📤 Step 1: Updating DNO info...")
    payload1 = {
        "secret": API_SECRET,
        "action": "update_dno_info",
        "postcode": postcode if postcode else "",
        "mpan_id": int(mpan_id),
        "dno_data": {
            "dno_key": str(dno_data['dno_key']),
            "dno_name": str(dno_data['dno_name']),
            "dno_short_code": str(dno_data['dno_short_code']),
            "market_participant_id": str(dno_data['market_participant_id']),
            "gsp_group_id": str(dno_data['gsp_group_id']),
            "gsp_group_name": str(dno_data['gsp_group_name'])
        }
    }
    
    try:
        res1 = requests.post(WEB_APP_URL, json=payload1, headers=headers, timeout=10)
        if res1.status_code == 200:
            print(f"   ✅ DNO info updated")
            results.append("DNO info")
        else:
            print(f"   ❌ Error {res1.status_code}: {res1.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Step 2: Update DUoS rates (B9:E9)
    print("📤 Step 2: Updating DUoS rates...")
    payload2 = {
        "secret": API_SECRET,
        "action": "update_duos_rates",
        "rates": {
            "red": float(rates['red']),
            "amber": float(rates['amber']),
            "green": float(rates['green'])
        }
    }
    
    try:
        res2 = requests.post(WEB_APP_URL, json=payload2, headers=headers, timeout=10)
        if res2.status_code == 200:
            print(f"   ✅ DUoS rates updated")
            results.append("Rates")
        else:
            print(f"   ❌ Error {res2.status_code}: {res2.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Step 3: Update status (A4:H4)
    print("📤 Step 3: Updating status banner...")
    timestamp = datetime.now().strftime('%H:%M:%S')
    payload3 = {
        "secret": API_SECRET,
        "action": "update_status",
        "status_data": [
            f"✅ {dno_data['dno_name']}",
            f"{dno_data['dno_key']}",
            f"MPAN {mpan_id}",
            f"Updated: {timestamp}",
            "", "", "", ""
        ]
    }
    
    try:
        res3 = requests.post(WEB_APP_URL, json=payload3, headers=headers, timeout=10)
        if res3.status_code == 200:
            print(f"   ✅ Status updated")
            results.append("Status")
        else:
            print(f"   ❌ Error {res3.status_code}: {res3.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    if len(results) == 3:
        return {"status": "ok", "message": "All updates complete"}
    else:
        return {"status": "partial", "message": f"Completed: {', '.join(results)}"}

def refresh_dno_lookup(mpan_id=None, postcode=None, voltage='LV'):
    """
    Main function: lookup DNO and update sheet
    Supports BOTH postcode and MPAN lookup - whichever is provided
    """
    
    print("=" * 80)
    print("🔌 DNO Lookup via Web App (Postcode or MPAN)")
    print("=" * 80)
    
    # Read from sheet if no inputs provided
    if mpan_id is None and postcode is None:
        print("\n📖 Reading inputs from BESS sheet...")
        inputs = read_sheet_inputs()
        postcode = inputs.get('postcode', '').strip()
        mpan_id = inputs.get('mpan_id')
        voltage_raw = inputs.get('voltage', 'LV')
        
        # Extract voltage level (e.g., "LV (<1kV)" -> "LV")
        if voltage_raw and '(' in voltage_raw:
            voltage = voltage_raw.split('(')[0].strip()
        
        print(f"   Postcode: {postcode if postcode else '(not provided)'}")
        print(f"   MPAN: {mpan_id if mpan_id else '(not provided)'}")
        print(f"   Voltage: {voltage}")
    
    # Prioritize postcode lookup if provided
    if postcode and postcode.strip():
        coords = lookup_postcode(postcode)
        if coords:
            lat, lng = coords
            mpan_id = lookup_dno_by_coordinates(lat, lng)
            print(f"   ✅ Determined MPAN from postcode: {mpan_id}")
        else:
            print("   ⚠️  Postcode lookup failed, trying MPAN if provided...")
    
    # Fall back to MPAN if provided
    if not mpan_id:
        print("❌ No valid MPAN ID or postcode provided")
        return False
    
    mpan_id = int(mpan_id)
    
    if mpan_id < 10 or mpan_id > 23:
        print(f"❌ Invalid MPAN: {mpan_id} (must be 10-23)")
        return False
    
    # Lookup DNO
    print(f"\n🔍 Looking up MPAN {mpan_id}...")
    dno_info = lookup_dno_by_mpan(mpan_id)
    
    if not dno_info:
        print(f"❌ No DNO found for MPAN {mpan_id}")
        return False
    
    print(f"✅ Found: {dno_info['dno_name']} ({dno_info['dno_key']})")
    
    # Get DUoS rates
    print(f"\n💰 Getting {voltage} DUoS rates for {dno_info['dno_key']}...")
    rates = get_duos_rates(dno_info['dno_key'], voltage)
    
    print(f"   Red: {rates['red']:.4f} p/kWh")
    print(f"   Amber: {rates['amber']:.4f} p/kWh")
    print(f"   Green: {rates['green']:.4f} p/kWh")
    
    # Update sheet via web app
    print(f"\n📤 Sending update to BESS sheet...")
    result = update_sheet_full(mpan_id, dno_info, rates)
    
    if result.get('status') == 'ok':
        print("\n✅ BESS SHEET UPDATED!")
        print(f"\n📊 Summary:")
        print(f"   DNO: {dno_info['dno_name']} ({dno_info['dno_key']})")
        print(f"   MPAN: {mpan_id}")
        print(f"   GSP Group: {dno_info['gsp_group_id']} - {dno_info['gsp_group_name']}")
        print(f"   Voltage: {voltage}")
        print(f"   Red: £{rates['red']*10:.2f}/MWh")
        print(f"   Amber: £{rates['amber']*10:.2f}/MWh")
        print(f"   Green: £{rates['green']*10:.2f}/MWh")
        return True
    else:
        print(f"❌ Update failed: {result}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        
        # Check if first arg is a postcode (contains letters) or MPAN (numeric)
        if re.match(r'^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$', arg1.upper().replace(' ', '')):
            # Postcode format (e.g., "LS1 2TW", "SW1A 1AA")
            postcode = arg1
            voltage = sys.argv[2] if len(sys.argv) > 2 else 'LV'
            success = refresh_dno_lookup(postcode=postcode, voltage=voltage)
        else:
            # MPAN ID (numeric)
            mpan = int(arg1)
            voltage = sys.argv[2] if len(sys.argv) > 2 else 'LV'
            success = refresh_dno_lookup(mpan_id=mpan, voltage=voltage)
    else:
        # Read from sheet: python3 dno_webapp_client.py
        success = refresh_dno_lookup()
    
    sys.exit(0 if success else 1)
