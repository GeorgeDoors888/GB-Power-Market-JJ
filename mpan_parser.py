#!/usr/bin/env python3
"""
MPAN Parser & Validator
Handles full MPAN parsing including checksum validation and component extraction
"""

import re
from typing import Dict, Optional, Tuple

class MPANParser:
    """Parse and validate UK MPAN (Meter Point Administration Number)"""
    
    # DNO mappings (Distributor ID to DNO details)
    DNO_MAP = {
        10: {"key": "UKPN-EPN", "name": "UK Power Networks (Eastern)", "region": "Eastern"},
        11: {"key": "NGED-EM", "name": "National Grid (East Midlands)", "region": "East Midlands"},
        12: {"key": "UKPN-LPN", "name": "UK Power Networks (London)", "region": "London"},
        13: {"key": "SP-Manweb", "name": "SP Energy Networks (Manweb)", "region": "North Wales/Merseyside"},
        14: {"key": "NGED-WM", "name": "National Grid (West Midlands)", "region": "West Midlands"},
        15: {"key": "NPg-NE", "name": "Northern Powergrid (North East)", "region": "North East"},
        16: {"key": "ENWL", "name": "Electricity North West", "region": "North West"},
        17: {"key": "SSE-SHEPD", "name": "SSE (Scottish Hydro)", "region": "North Scotland"},
        18: {"key": "SP-Distribution", "name": "SP Energy Networks", "region": "South Scotland"},
        19: {"key": "UKPN-SPN", "name": "UK Power Networks (South East)", "region": "South East"},
        20: {"key": "SSE-SEPD", "name": "SSE (Southern Electric)", "region": "Southern"},
        21: {"key": "NGED-SWales", "name": "National Grid (South Wales)", "region": "South Wales"},
        22: {"key": "NGED-SW", "name": "National Grid (South Western)", "region": "South West"},
        23: {"key": "NPg-Y", "name": "Northern Powergrid (Yorkshire)", "region": "Yorkshire"}
    }
    
    @staticmethod
    def validate_checksum(core_mpan: str) -> bool:
        """
        Validate MPAN checksum using mod-11 algorithm (S-number check)
        
        Args:
            core_mpan: 13-digit core MPAN string
            
        Returns:
            True if checksum valid
        """
        if len(core_mpan) != 13 or not core_mpan.isdigit():
            return False
        
        # Weights for mod-11 check (right to left, excluding check digit)
        weights = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
        
        # Extract check digit (last digit) and 12 data digits
        check_digit = int(core_mpan[-1])
        data_digits = [int(d) for d in core_mpan[:12]]
        
        # Calculate weighted sum
        weighted_sum = sum(d * w for d, w in zip(data_digits, weights))
        
        # Calculate expected check digit
        remainder = weighted_sum % 11
        expected = (11 - remainder) % 11
        
        return check_digit == expected
    
    @staticmethod
    def parse_full_mpan(mpan_string: str) -> Dict:
        """
        Parse full MPAN including top line (PC/MTC/LLFC) and core MPAN
        
        Format examples:
            "00 801 0840 12 3456 7890 123"  (with top line)
            "1234567890123"                  (core only)
            "S 00 801 0840 1234567890123"   (S-prefix)
        
        Returns dict with:
            - core_mpan: 13-digit core MPAN
            - distributor_id: First 2 digits (10-23)
            - dno_key: DNO identifier (e.g., "UKPN-EPN")
            - dno_name: Full DNO name
            - pc: Profile Class (if available)
            - mtc: Meter Timeswitch Code (if available)
            - llfc: Line Loss Factor Class / DUoS Tariff ID (if available)
            - import_export: 'import' or 'export'
            - valid: Checksum validation result
        """
        # Remove spaces and common prefixes
        clean = re.sub(r"\s+", "", mpan_string.upper())
        clean = clean.lstrip("S")
        
        # Try to parse top line format: PC(2) MTC(3) LLFC(3-4) CORE(13)
        full_match = re.match(r"^(\d{2})(\d{3})(\d{3,4})(\d{13})$", clean)
        
        if full_match:
            pc, mtc, llfc, core = full_match.groups()
            has_top_line = True
        else:
            # Core MPAN only (13 digits)
            core_match = re.match(r"^(\d{13})$", clean)
            if not core_match:
                raise ValueError(f"Invalid MPAN format: {mpan_string}")
            core = core_match.group(1)
            pc = mtc = llfc = None
            has_top_line = False
        
        # Validate checksum
        valid = MPANParser.validate_checksum(core)
        
        # Extract distributor ID (first 2 digits of core MPAN)
        distributor_id = int(core[:2])
        
        # Determine import/export
        # Export MPANs typically start with 'E' or have specific PC codes
        # For now, assume import unless specified
        import_export = "export" if (pc and pc.startswith("8")) else "import"
        
        # Get DNO details
        dno_info = MPANParser.DNO_MAP.get(distributor_id)
        if not dno_info:
            raise ValueError(f"Unknown distributor ID: {distributor_id}")
        
        return {
            "core_mpan": core,
            "distributor_id": distributor_id,
            "dno_key": dno_info["key"],
            "dno_name": dno_info["name"],
            "dno_region": dno_info["region"],
            "pc": pc,
            "mtc": mtc,
            "llfc": llfc,
            "has_top_line": has_top_line,
            "import_export": import_export,
            "valid": valid,
            "raw_input": mpan_string
        }
    
    @staticmethod
    def format_mpan(core_mpan: str, pc: str = None, mtc: str = None, llfc: str = None) -> str:
        """
        Format MPAN with proper spacing for display
        
        Returns: "S 00 801 0840 12 3456 7890 123" format
        """
        if len(core_mpan) != 13:
            raise ValueError("Core MPAN must be 13 digits")
        
        # Split core MPAN: Profile(2) MTC-Region(3) Distributor-Identifier(4) Check(4)
        formatted = f"S {core_mpan[0:2]} {core_mpan[2:5]} {core_mpan[5:9]} {core_mpan[9:11]} {core_mpan[11:13]}"
        
        if pc and mtc and llfc:
            formatted = f"{pc} {mtc} {llfc} " + formatted
        
        return formatted


def test_parser():
    """Test MPAN parser with various formats"""
    test_cases = [
        "1234567890123",  # Core only
        "00 801 0840 12 3456 7890 123",  # Full with top line
        "S 10 123 4567 8901 23",  # S-prefix
        "10 123 456 1234567890123"  # PC/MTC/LLFC + core
    ]
    
    print("=" * 80)
    print("MPAN Parser Tests")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\nInput: {test}")
        try:
            result = MPANParser.parse_full_mpan(test)
            print(f"  ✅ Valid: {result['valid']}")
            print(f"  DNO: {result['dno_name']} ({result['dno_key']})")
            print(f"  Distributor ID: {result['distributor_id']}")
            if result['has_top_line']:
                print(f"  PC: {result['pc']}, MTC: {result['mtc']}, LLFC: {result['llfc']}")
            print(f"  Type: {result['import_export']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    test_parser()
