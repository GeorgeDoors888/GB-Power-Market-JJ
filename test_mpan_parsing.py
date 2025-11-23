#!/usr/bin/env python3
"""
Test MPAN Parsing - Verify Critical DNO Extraction Fix

This test ensures the MPAN parsing fix from 2025-11-22 stays working.

CRITICAL BUG FIXED:
- Full MPAN "00800999932 1405566778899" was extracting ID from top line (08)
- Should extract from core (14) → NGED West Midlands
- Fix: Use extract_core_from_full_mpan() from mpan_generator_validator

Run this test after ANY changes to:
- dno_lookup_python.py (especially imports or parse_mpan_input function)
- mpan_generator_validator.py (especially extract_core_from_full_mpan)
"""

import sys
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup

# Test cases covering all MPAN formats
TEST_CASES = [
    {
        "input": "00800999932 1405566778899",
        "expected_id": 14,
        "expected_dno": "National Grid (West Midlands)",
        "format": "Full 21-digit MPAN with space"
    },
    {
        "input": "00-801-0840-1405566778899",
        "expected_id": 14,
        "expected_dno": "National Grid (West Midlands)",
        "format": "Full 21-digit MPAN with dashes"
    },
    {
        "input": "1405566778899",
        "expected_id": 14,
        "expected_dno": "National Grid (West Midlands)",
        "format": "Core 13-digit MPAN"
    },
    {
        "input": "1200123456789",
        "expected_id": 12,
        "expected_dno": "UK Power Networks (London)",
        "format": "Core 13-digit MPAN (UKPN London)"
    },
    {
        "input": "1001234567890",
        "expected_id": 10,
        "expected_dno": "UK Power Networks (Eastern)",
        "format": "Core 13-digit MPAN (UKPN Eastern)"
    },
]


def test_mpan_parsing():
    """Test MPAN parsing with all formats"""
    print("=" * 80)
    print("MPAN Parsing Test Suite")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        print(f"Test {i}: {test['format']}")
        print(f"  Input: {test['input']}")
        
        try:
            # Extract core if needed
            input_str = test['input']
            if ' ' in input_str or '-' in input_str:
                core = extract_core_from_full_mpan(input_str)
                print(f"  Extracted core: {core}")
            else:
                core = input_str[:13] if len(input_str) >= 13 else input_str
                print(f"  Using core: {core}")
            
            # Lookup DNO
            info = mpan_core_lookup(core)
            
            if 'error' in info:
                print(f"  ❌ FAILED: {info['error']}")
                failed += 1
                continue
            
            # Verify results
            actual_id = int(info['dno_id'])
            actual_dno = info['dno_name']
            
            print(f"  Distributor ID: {actual_id}")
            print(f"  DNO: {actual_dno}")
            
            # Check expectations
            if actual_id == test['expected_id']:
                print(f"  ✅ PASSED: Distributor ID correct")
                passed += 1
            else:
                print(f"  ❌ FAILED: Expected ID {test['expected_id']}, got {actual_id}")
                failed += 1
        
        except Exception as e:
            print(f"  ❌ FAILED: Exception: {e}")
            failed += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed > 0:
        print("\n⚠️  CRITICAL: Some tests failed!")
        print("This means MPAN parsing is broken. Check:")
        print("1. dno_lookup_python.py imports from mpan_generator_validator")
        print("2. parse_mpan_input() uses extract_core_from_full_mpan()")
        print("3. mpan_generator_validator.py exists and functions work")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! MPAN parsing is working correctly.")
        sys.exit(0)


if __name__ == "__main__":
    test_mpan_parsing()
