#!/usr/bin/env python3
"""
MPAN Voltage Level Detector
Determines voltage level (LV/HV/EHV) from MPAN Profile Class and Supplement
"""

# Profile Class (PC) to Voltage Level mapping
# Based on Elexon P272 profile classes
PROFILE_CLASS_VOLTAGE = {
    # Standard Domestic & Small Commercial (LV)
    "01": "LV",  # Domestic Unrestricted
    "02": "LV",  # Domestic Economy 7
    "03": "LV",  # Non-Domestic Unrestricted
    "04": "LV",  # Non-Domestic Economy 7
    "05": "LV",  # Non-Domestic Maximum Demand (LV)
    "06": "LV",  # Non-Domestic Maximum Demand (LV) E7
    "07": "LV",  # Non-Domestic Off-Peak (LV)
    "08": "LV",  # Non-Domestic Off-Peak (LV) with MD
    
    # Half-Hourly Metered (can be LV/HV/EHV)
    "00": None,  # Half-hourly - voltage depends on supplement
    
    # Unmetered
    "09": "LV",  # Unmetered (street lighting, etc.)
}

# Supplement letter to voltage mapping (for PC 00)
# Format: [distributor_id][supplement] = voltage
SUPPLEMENT_VOLTAGE = {
    # Common supplements across DNOs:
    "A": "LV",   # LV Network (<1kV)
    "B": "LV",   # LV Sub Network  
    "C": "HV",   # HV Network (6.6kV / 11kV / 20kV / 33kV)
    "D": "HV",   # HV Sub Network
    "E": "EHV",  # EHV Network (66kV / 132kV)
    "F": "EHV",  # EHV+ (>132kV)
    
    # Some DNOs use different letters:
    "P": "HV",   # HV (alternate)
    "Q": "EHV",  # EHV (alternate)
}

# LLFC (Line Loss Factor Class) can also indicate voltage
# First digit often indicates voltage level
LLFC_VOLTAGE_HINTS = {
    "0": "LV",   # 0xxx = Usually LV
    "1": "LV",   # 1xxx = Usually LV
    "2": "LV",   # 2xxx = Usually LV
    "3": "HV",   # 3xxx = Usually HV
    "4": "HV",   # 4xxx = Usually HV
    "5": "HV",   # 5xxx = Usually HV
    "6": "EHV",  # 6xxx = Usually EHV
    "7": "EHV",  # 7xxx = Usually EHV
}


def determine_voltage_from_mpan(pc: str = None, supplement: str = None, llfc: str = None) -> str:
    """
    Determine voltage level from MPAN components
    
    Args:
        pc: Profile Class (00-09)
        supplement: Supplement letter (A-F, P, Q)
        llfc: Line Loss Factor Class (3-4 digits)
    
    Returns:
        "LV", "HV", "EHV", or "UNKNOWN"
    
    Priority:
        1. Profile Class (if not 00)
        2. Supplement (for PC 00)
        3. LLFC hint (fallback)
        4. Default to LV if unknown
    """
    
    # 1. Check Profile Class first
    if pc and pc in PROFILE_CLASS_VOLTAGE:
        voltage = PROFILE_CLASS_VOLTAGE[pc]
        if voltage:  # Not None (i.e., not PC 00)
            return voltage
    
    # 2. For PC 00 (HH), check Supplement
    if supplement:
        supplement_upper = supplement.upper()
        if supplement_upper in SUPPLEMENT_VOLTAGE:
            return SUPPLEMENT_VOLTAGE[supplement_upper]
    
    # 3. Try LLFC hint (first digit)
    if llfc and len(str(llfc)) >= 1:
        first_digit = str(llfc)[0]
        if first_digit in LLFC_VOLTAGE_HINTS:
            return LLFC_VOLTAGE_HINTS[first_digit]
    
    # 4. Default to LV (most common)
    return "LV"


def parse_mpan_for_voltage(mpan_string: str) -> dict:
    """
    Parse MPAN and determine voltage level
    
    Args:
        mpan_string: Full MPAN string or core
        
    Returns:
        dict with:
            - voltage: "LV", "HV", "EHV", or "UNKNOWN"
            - pc: Profile Class
            - supplement: Supplement letter
            - llfc: LLFC code
            - core_mpan: 13-digit core
            - method: How voltage was determined
    """
    import re
    
    # Clean input
    mpan_clean = mpan_string.replace(" ", "").replace("-", "").upper()
    
    # Try to parse full MPAN format: [S] PC(2) MTC(3) LLFC(3-4) [Supp] Core(13)
    # Examples:
    #   "00 801 0840 1234567890123"     (PC 00, LLFC 0840)
    #   "S 00 801 0840 1234567890123"   (with S prefix)
    #   "00 801 0840 S 1234567890123"   (supplement before core)
    
    pc = None
    llfc = None
    supplement = None
    core_mpan = None
    method = "unknown"
    
    # Pattern 1: Full MPAN with components
    # Format: [S] PC(2) MTC(3) LLFC(3-4) [Supp(1)] Core(13)
    full_pattern = r'S?(\d{2})\s*(\d{3})\s*(\d{3,4})\s*([A-Z])?\s*(\d{13})'
    match = re.search(full_pattern, mpan_clean)
    
    if match:
        pc = match.group(1)
        # MTC not needed for voltage
        llfc = match.group(3)
        supplement = match.group(4) if match.group(4) else None
        core_mpan = match.group(5)
    else:
        # Pattern 2: Core MPAN only (13 digits)
        core_pattern = r'(\d{13})'
        match = re.search(core_pattern, mpan_clean)
        if match:
            core_mpan = match.group(1)
    
    # Determine voltage
    voltage = determine_voltage_from_mpan(pc, supplement, llfc)
    
    # Determine method used
    if pc and pc != "00":
        method = f"Profile Class {pc}"
    elif supplement:
        method = f"Supplement {supplement}"
    elif llfc:
        method = f"LLFC {llfc} hint"
    else:
        method = "Default (LV)"
    
    return {
        "voltage": voltage,
        "pc": pc,
        "supplement": supplement,
        "llfc": llfc,
        "core_mpan": core_mpan,
        "method": method
    }


# Voltage level descriptions
VOLTAGE_DESCRIPTIONS = {
    "LV": "Low Voltage (<1kV)",
    "HV": "High Voltage (6.6-33kV)",
    "EHV": "Extra High Voltage (66-132kV+)",
}


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "00 801 0840 C 1234567890123",  # PC 00, supplement C = HV
        "01 801 0840 1234567890123",    # PC 01 = LV (domestic)
        "00 801 3456 1234567890123",    # PC 00, LLFC 3456 = HV
        "00 801 0840 A 1234567890123",  # PC 00, supplement A = LV
        "1234567890123",                # Core only = LV (default)
    ]
    
    print("=" * 80)
    print("MPAN Voltage Level Detection - Test Cases")
    print("=" * 80)
    
    for mpan in test_cases:
        result = parse_mpan_for_voltage(mpan)
        print(f"\n📍 MPAN: {mpan}")
        print(f"   Voltage: {result['voltage']} - {VOLTAGE_DESCRIPTIONS.get(result['voltage'], '')}")
        print(f"   Method:  {result['method']}")
        if result['pc']:
            print(f"   PC:      {result['pc']}")
        if result['supplement']:
            print(f"   Supp:    {result['supplement']}")
        if result['llfc']:
            print(f"   LLFC:    {result['llfc']}")
    
    print("\n" + "=" * 80)
    print("✅ Voltage detection complete")
