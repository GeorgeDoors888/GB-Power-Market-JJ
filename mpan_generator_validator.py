#!/usr/bin/env python3
"""
MPAN Core Generator & Validator
Implements mod-11 checksum algorithm for GB electricity meter points
"""

import random
from typing import Optional, Dict, Tuple

# Prime weights for mod-11 checksum (used by Elexon/MPAS)
MPAN_PRIMES = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]

# DNO Distributor ID mapping (first 2 digits of MPAN core)
DNO_MAP = {
    "10": "UK Power Networks (Eastern)",
    "11": "National Grid (East Midlands)",
    "12": "UK Power Networks (London)",
    "13": "SP Energy Networks (Manweb)",
    "14": "National Grid (West Midlands)",
    "15": "Northern Powergrid (North East)",
    "16": "Electricity North West",
    "17": "SSE (Scottish Hydro)",
    "18": "SP Energy Networks (Southern Scotland)",
    "19": "UK Power Networks (South East)",
    "20": "SSE (Southern Electric)",
    "21": "National Grid (South Wales)",
    "22": "National Grid (South Western)",
    "23": "Northern Powergrid (Yorkshire)",
}


def mpan_check_digit(first_12_digits: str) -> int:
    """
    Calculate MPAN check digit using mod-11 algorithm
    
    Args:
        first_12_digits: First 12 digits of MPAN core
    
    Returns:
        Check digit (0-9)
    """
    if len(first_12_digits) != 12 or not first_12_digits.isdigit():
        raise ValueError("first_12_digits must be a 12-digit numeric string")
    
    # Weighted sum with prime multipliers
    total = sum(int(d) * p for d, p in zip(first_12_digits, MPAN_PRIMES))
    
    # Check digit = (sum mod 11) mod 10
    return (total % 11) % 10


def is_valid_mpan_core(mpan_core_13: str) -> bool:
    """
    Validate 13-digit MPAN core using mod-11 checksum
    
    Args:
        mpan_core_13: Complete 13-digit MPAN core
    
    Returns:
        True if checksum valid
    """
    if len(mpan_core_13) != 13 or not mpan_core_13.isdigit():
        return False
    
    expected = mpan_check_digit(mpan_core_13[:12])
    return expected == int(mpan_core_13[-1])


def generate_valid_mpan_core(dno_id: Optional[str] = None) -> str:
    """
    Generate checksum-valid 13-digit MPAN core
    
    Args:
        dno_id: Optional 2-digit DNO distributor ID (10-23)
                If None, randomly selects from valid DNOs
    
    Returns:
        Valid 13-digit MPAN core with correct checksum
    """
    if dno_id is None:
        dno_id = random.choice(list(DNO_MAP.keys()))
    
    if len(dno_id) != 2 or not dno_id.isdigit():
        raise ValueError("dno_id must be 2 digits (10-23)")
    
    if dno_id not in DNO_MAP:
        raise ValueError(f"Invalid DNO ID: {dno_id}. Must be 10-23")
    
    # Generate random 10 digits for meter identifier
    body10 = "".join(str(random.randint(0, 9)) for _ in range(10))
    
    # Combine: DNO (2) + Body (10) = 12 digits
    first12 = dno_id + body10
    
    # Calculate and append check digit
    cd = mpan_check_digit(first12)
    
    return first12 + str(cd)


def extract_core_from_full_mpan(full_mpan_21: str) -> str:
    """
    Extract 13-digit core from full 21-digit MPAN
    
    Full MPAN format: PC(2) MTC(3) LLFC(3) + Core(13) = 21 digits
    
    Args:
        full_mpan_21: Full MPAN string (may contain spaces)
    
    Returns:
        13-digit core MPAN
    """
    # Remove all non-digit characters
    digits = "".join(ch for ch in full_mpan_21 if ch.isdigit())
    
    if len(digits) < 13:
        raise ValueError(f"MPAN must contain at least 13 digits, got {len(digits)}")
    
    # Extract last 13 digits (core MPAN)
    return digits[-13:]


def mpan_core_lookup(core_13: str) -> Dict[str, str]:
    """
    Extract DNO information from MPAN core
    
    Args:
        core_13: 13-digit MPAN core
    
    Returns:
        Dict with core, dno_id, dno_name, is_valid
    """
    if len(core_13) != 13:
        raise ValueError("MPAN core must be 13 digits")
    
    dno_id = core_13[:2]
    
    return {
        "core": core_13,
        "dno_id": dno_id,
        "dno_name": DNO_MAP.get(dno_id, "Unknown DNO"),
        "is_valid": is_valid_mpan_core(core_13),
        "checksum": core_13[-1],
        "expected_checksum": str(mpan_check_digit(core_13[:12]))
    }


def generate_batch_valid_mpans(count: int, dno_id: Optional[str] = None) -> list:
    """
    Generate multiple valid MPANs for testing
    
    Args:
        count: Number of MPANs to generate
        dno_id: Optional DNO ID (if None, randomly varies)
    
    Returns:
        List of valid MPAN cores
    """
    return [generate_valid_mpan_core(dno_id) for _ in range(count)]


def format_mpan_display(core_13: str) -> str:
    """
    Format MPAN core for human-readable display
    
    Format: S DD DDD DDDD DD DD D
    Example: S 12 345 6789 01 23 4
    
    Args:
        core_13: 13-digit MPAN core
    
    Returns:
        Formatted string
    """
    if len(core_13) != 13:
        raise ValueError("MPAN core must be 13 digits")
    
    return f"S {core_13[0:2]} {core_13[2:5]} {core_13[5:9]} {core_13[9:11]} {core_13[11:13]}"


# ==================== DEMO & TESTS ====================

def test_mpan_generator():
    """Test MPAN generation and validation"""
    print("=" * 80)
    print("MPAN Generator & Validator Test")
    print("=" * 80)
    
    # Test 1: Generate valid MPANs for each DNO
    print("\n1. Generating valid MPANs for each DNO region:")
    for dno_id, dno_name in sorted(DNO_MAP.items()):
        core = generate_valid_mpan_core(dno_id)
        is_valid = is_valid_mpan_core(core)
        print(f"   {dno_id} ({dno_name[:30]:30s}): {format_mpan_display(core)} ✅" if is_valid else f" ❌")
    
    # Test 2: Validate test MPANs
    print("\n2. Validating test MPANs:")
    test_cases = [
        ("1200123456789", "Invalid - wrong checksum"),
        ("1234567890123", "Random digits"),
        (generate_valid_mpan_core("10"), "Generated valid"),
    ]
    
    for mpan, desc in test_cases:
        info = mpan_core_lookup(mpan)
        status = "✅ VALID" if info['is_valid'] else "❌ INVALID"
        print(f"   {mpan} ({desc}): {status}")
        print(f"      DNO: {info['dno_name']}")
        print(f"      Checksum: {info['checksum']} (expected: {info['expected_checksum']})")
    
    # Test 3: Extract core from full MPAN
    print("\n3. Extracting core from full MPAN:")
    full_mpan = "00 801 0840 " + generate_valid_mpan_core("12")
    core = extract_core_from_full_mpan(full_mpan)
    print(f"   Full: {full_mpan}")
    print(f"   Core: {core}")
    print(f"   Valid: {'✅' if is_valid_mpan_core(core) else '❌'}")
    
    # Test 4: Batch generation
    print("\n4. Batch generation (10 valid MPANs for London):")
    batch = generate_batch_valid_mpans(10, "12")
    for i, mpan in enumerate(batch, 1):
        print(f"   {i:2d}. {format_mpan_display(mpan)}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_mpan_generator()
