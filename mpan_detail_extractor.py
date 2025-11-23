#!/usr/bin/env python3
"""
MPAN Detail Extractor
Extracts comprehensive MPAN details for display in BESS sheet
"""

from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"

# Profile Class to voltage mapping
PROFILE_CLASS_VOLTAGE = {
    '00': 'HH',  # Half-hourly metered
    '01': 'LV', '02': 'LV', '03': 'LV', '04': 'LV',
    '05': 'LV', '06': 'LV', '07': 'LV', '08': 'LV'
}

# Supplement to Profile Class hints
SUPPLEMENT_PC = {
    'A': '01-04', 'B': '05-08',  # LV
    'C': '00', 'D': '00',         # HV (usually HH)
    'P': '00',                    # HV (HH)
    'E': '00', 'F': '00',         # EHV (usually HH)
    'Q': '00'                     # EHV (HH)
}

# Meter Timeswitch Code descriptions
MTC_DESCRIPTIONS = {
    '801': 'Non-Domestic',
    '851': 'Non-Domestic HH',
    '491': 'Domestic Unrestricted',
    '510': 'Domestic Economy 7'
}

def extract_mpan_details(supplement=None, llfc=None, voltage=None, dno_key=None):
    """
    Extract comprehensive MPAN details
    
    Args:
        supplement: MPAN supplement letter (A-F, P, Q)
        llfc: Line Loss Factor Class (3-4 digits)
        voltage: Voltage level (LV/HV/EHV)
        dno_key: DNO key for tariff lookup
        
    Returns:
        dict with keys: profile_class, meter_registration, voltage_level,
                       duos_charging_class, tariff_id, loss_factor
    """
    
    result = {
        'profile_class': '',
        'meter_registration': '',
        'voltage_level': voltage or 'Unknown',
        'duos_charging_class': '',
        'tariff_id': llfc or '',
        'loss_factor': ''
    }
    
    # Extract Profile Class from supplement
    if supplement:
        pc_hint = SUPPLEMENT_PC.get(supplement.upper())
        result['profile_class'] = pc_hint or '00-08'
    
    # Extract Meter Registration (MTC hint)
    if voltage:
        if voltage == 'LV':
            result['meter_registration'] = '801 (Non-Domestic)'
        elif voltage in ['HV', 'EHV']:
            result['meter_registration'] = '851 (HH)'
    
    # Query DUoS Charging Class if we have DNO and LLFC
    if dno_key and llfc:
        try:
            charging_class = get_duos_charging_class(dno_key, llfc)
            result['duos_charging_class'] = charging_class
        except Exception as e:
            print(f"   ⚠️  Could not fetch DUoS charging class: {e}")
            result['duos_charging_class'] = 'Non-Domestic'
    
    # Get Loss Factor
    if llfc:
        try:
            loss_factor = get_loss_factor(dno_key, llfc)
            if not loss_factor:
                # Fallback to estimation if not in database
                loss_factor = estimate_loss_factor(llfc, voltage)
            result['loss_factor'] = loss_factor
        except Exception as e:
            print(f"   ⚠️  Could not fetch loss factor: {e}")
            result['loss_factor'] = estimate_loss_factor(llfc, voltage)
    
    return result


def get_duos_charging_class(dno_key, llfc):
    """Query DUoS charging class from BigQuery"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT tariff_class
    FROM `{PROJECT_ID}.gb_power.duos_unit_rates`
    WHERE dno_key = '{dno_key}'
      AND tariff_code LIKE '%{llfc}%'
    LIMIT 1
    """
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty and 'tariff_class' in df.columns:
            return df['tariff_class'].iloc[0]
    except:
        pass
    
    return 'Non-Domestic'


def get_loss_factor(dno_key, llfc):
    """Query loss factor from BigQuery"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT DISTINCT loss_factor
    FROM `{PROJECT_ID}.gb_power.duos_unit_rates`
    WHERE dno_key = '{dno_key}'
      AND tariff_code LIKE '%{llfc}%'
    LIMIT 1
    """
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty and 'loss_factor' in df.columns:
            lf = df['loss_factor'].iloc[0]
            return f"{lf:.3f}" if lf else ''
    except:
        pass
    
    return ''


def estimate_loss_factor(llfc, voltage):
    """Estimate loss factor from LLFC and voltage"""
    
    if not llfc:
        return ''
    
    # LLFC first digit hints at voltage and thus typical loss factors
    first_digit = int(llfc[0]) if llfc and llfc[0].isdigit() else 0
    
    if first_digit <= 2:  # LV
        return '1.045'  # ~4.5% line losses
    elif first_digit <= 5:  # HV
        return '1.025'  # ~2.5% line losses
    else:  # EHV
        return '1.015'  # ~1.5% line losses


def generate_tou_description(rates_dict):
    """
    Generate human-readable TOU structure description
    
    Args:
        rates_dict: Dict with 'Red', 'Amber', 'Green' keys containing schedule info
        
    Returns:
        str: TOU description
    """
    
    if not rates_dict:
        return 'Standard 3-rate TOU structure'
    
    red_times = rates_dict.get('Red', {}).get('schedule', [])
    amber_times = rates_dict.get('Amber', {}).get('schedule', [])
    
    if red_times:
        red_desc = ', '.join(red_times[:2]) if len(red_times) > 1 else red_times[0] if red_times else 'Peak'
        return f"Peak: {red_desc} | Mid: Day/Evening | Off-peak: Night/Weekend"
    
    return 'Red/Amber/Green time bands'


if __name__ == "__main__":
    # Test extraction
    print("Testing MPAN detail extraction...\n")
    
    test_cases = [
        {'supplement': 'C', 'llfc': '3456', 'voltage': 'HV', 'dno_key': 'UKPN-SPN'},
        {'supplement': 'A', 'llfc': '0840', 'voltage': 'LV', 'dno_key': 'UKPN-EPN'},
        {'supplement': 'E', 'llfc': '6789', 'voltage': 'EHV', 'dno_key': 'NGED-WM'},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  Input: {test}")
        details = extract_mpan_details(**test)
        print(f"  Output:")
        for key, value in details.items():
            print(f"    {key}: {value}")
        print()
