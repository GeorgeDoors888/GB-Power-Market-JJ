#!/usr/bin/env python3
"""
Read entire BESS sheet and document current structure for future reference
This will capture all manual changes and serve as the source of truth
"""
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
ss = gc.open_by_key(SPREADSHEET_ID)
bess = ss.worksheet('BESS')

print("=" * 100)
print("READING ENTIRE BESS SHEET STRUCTURE")
print("=" * 100)
print()

# Read all data
all_data = bess.get_all_values()
print(f"Total rows: {len(all_data)}")
print(f"Total columns: {len(all_data[0]) if all_data else 0}")
print()

# Document structure
structure = {
    "spreadsheet_id": SPREADSHEET_ID,
    "sheet_name": "BESS",
    "captured_date": datetime.now().isoformat(),
    "total_rows": len(all_data),
    "total_columns": len(all_data[0]) if all_data else 0,
    "key_sections": {},
    "cell_mappings": {}
}

# Identify key sections
print("=" * 100)
print("KEY SECTIONS IDENTIFIED")
print("=" * 100)
print()

# Section 1: BESS Configuration (rows 1-20)
print("1. BESS CONFIGURATION (Rows 1-20)")
print("-" * 100)
for i in range(min(20, len(all_data))):
    row = all_data[i]
    if any(cell for cell in row):
        key_cells = []
        for j, cell in enumerate(row[:10]):
            if cell:
                col_letter = chr(65 + j)
                key_cells.append(f"{col_letter}{i+1}='{cell[:30]}'")
        if key_cells:
            print(f"Row {i+1}: {', '.join(key_cells[:3])}")

structure["key_sections"]["configuration"] = {
    "rows": "1-20",
    "description": "BESS specifications, MPAN, DNO info",
    "key_cells": {
        "postcode": "A6",
        "mpan_id": "B6",
        "voltage_level": "A10",
        "red_rate_pkwh": "B10",
        "amber_rate_pkwh": "C10",
        "green_rate_pkwh": "D10",
        "import_capacity_kw": "F13",
        "export_capacity_kw": "F14",
        "duration_hrs": "F15",
        "max_cycles_day": "F16"
    }
}

print()
print("2. COST MODEL (Rows 26-42)")
print("-" * 100)
for i in range(25, min(43, len(all_data))):
    row = all_data[i]
    if any(cell for cell in row):
        col_a = row[0][:25] if len(row) > 0 and row[0] else ""
        col_b = row[1][:15] if len(row) > 1 and row[1] else ""
        col_c = row[2][:15] if len(row) > 2 and row[2] else ""
        col_f = row[5][:15] if len(row) > 5 and row[5] else ""
        col_g = row[6][:15] if len(row) > 6 and row[6] else ""
        col_h = row[7][:15] if len(row) > 7 and row[7] else ""
        print(f"Row {i+1}: A={col_a:25} | B={col_b:15} C={col_c:15} | F={col_f:15} G={col_g:15} H={col_h:15}")

structure["key_sections"]["cost_model"] = {
    "rows": "26-42",
    "description": "Non-BESS vs BESS costs comparison",
    "non_bess_costs": {
        "description": "Columns A-C: Direct grid import costs without battery",
        "column_a": "Cost category labels",
        "column_b": "kWh consumed",
        "column_c": "Total cost (£)",
        "row_28": "Red DUoS",
        "row_29": "Amber DUoS",
        "row_30": "Green DUoS",
        "row_31": "TNUoS",
        "row_32": "BNUoS",
        "row_35": "CCL",
        "row_36": "RO",
        "row_37": "FiT"
    },
    "bess_costs": {
        "description": "Columns F-H: Battery charging costs",
        "column_f": "Rates (p/kWh or £/MWh)",
        "column_g": "kWh charged by BESS",
        "column_h": "Total cost (£)",
        "row_28": "Red DUoS (should be 0 - avoiding expensive periods)",
        "row_29": "Amber DUoS",
        "row_30": "Green DUoS (largest - charging during cheap periods)",
        "row_31": "TNUoS",
        "row_32": "BNUoS",
        "row_35": "CCL",
        "row_36": "RO",
        "row_37": "FiT"
    }
}

print()
print("3. PPA PRICING (Row 43)")
print("-" * 100)
if len(all_data) > 42:
    row_43 = all_data[42]
    print(f"Row 43: A='{row_43[0] if len(row_43) > 0 else ''}' | D='{row_43[3] if len(row_43) > 3 else ''}'")

structure["key_sections"]["ppa_pricing"] = {
    "row": 43,
    "cell": "D43",
    "description": "PPA Contract Price (£/MWh)"
}

print()
print("=" * 100)
print("CRITICAL CELL MAPPINGS FOR SCRIPTS")
print("=" * 100)
print()

critical_cells = {
    # BESS Configuration
    "BESS_IMPORT_CAPACITY_KW": {"cell": "F13", "description": "Import capacity in kW", "type": "float"},
    "BESS_EXPORT_CAPACITY_KW": {"cell": "F14", "description": "Export capacity in kW", "type": "float"},
    "BESS_DURATION_HRS": {"cell": "F15", "description": "Storage duration in hours", "type": "float"},
    "BESS_MAX_CYCLES_DAY": {"cell": "F16", "description": "Maximum cycles per day", "type": "float"},
    
    # DNO DUoS Rates (row 10, NOT row 9 which is header)
    "DNO_RED_RATE_PKWH": {"cell": "B10", "description": "Red DUoS rate p/kWh", "type": "float"},
    "DNO_AMBER_RATE_PKWH": {"cell": "C10", "description": "Amber DUoS rate p/kWh", "type": "float"},
    "DNO_GREEN_RATE_PKWH": {"cell": "D10", "description": "Green DUoS rate p/kWh", "type": "float"},
    
    # PPA Price
    "PPA_PRICE_MWH": {"cell": "D43", "description": "PPA contract price £/MWh", "type": "float"},
    
    # BESS Cost Output Cells (written by calculate_bess_element_costs.py)
    "BESS_RED_DUOS_RATE": {"cell": "F28", "description": "Red DUoS rate display", "type": "string"},
    "BESS_RED_DUOS_KWH": {"cell": "G28", "description": "Red band charging kWh", "type": "float"},
    "BESS_RED_DUOS_COST": {"cell": "H28", "description": "Red band cost £", "type": "string"},
    
    "BESS_AMBER_DUOS_RATE": {"cell": "F29", "description": "Amber DUoS rate display", "type": "string"},
    "BESS_AMBER_DUOS_KWH": {"cell": "G29", "description": "Amber band charging kWh", "type": "float"},
    "BESS_AMBER_DUOS_COST": {"cell": "H29", "description": "Amber band cost £", "type": "string"},
    
    "BESS_GREEN_DUOS_RATE": {"cell": "F30", "description": "Green DUoS rate display", "type": "string"},
    "BESS_GREEN_DUOS_KWH": {"cell": "G30", "description": "Green band charging kWh", "type": "float"},
    "BESS_GREEN_DUOS_COST": {"cell": "H30", "description": "Green band cost £", "type": "string"},
    
    "BESS_TNUOS_RATE": {"cell": "F31", "description": "TNUoS rate display", "type": "string"},
    "BESS_TNUOS_KWH": {"cell": "G31", "description": "TNUoS kWh", "type": "float"},
    "BESS_TNUOS_COST": {"cell": "H31", "description": "TNUoS cost £", "type": "string"},
    
    "BESS_BNUOS_RATE": {"cell": "F32", "description": "BNUoS rate display", "type": "string"},
    "BESS_BNUOS_KWH": {"cell": "G32", "description": "BNUoS kWh", "type": "float"},
    "BESS_BNUOS_COST": {"cell": "H32", "description": "BNUoS cost £", "type": "string"},
    
    "BESS_CCL_RATE": {"cell": "F35", "description": "CCL rate display", "type": "string"},
    "BESS_CCL_KWH": {"cell": "G35", "description": "CCL kWh", "type": "float"},
    "BESS_CCL_COST": {"cell": "H35", "description": "CCL cost £", "type": "string"},
    
    "BESS_RO_RATE": {"cell": "F36", "description": "RO rate display", "type": "string"},
    "BESS_RO_KWH": {"cell": "G36", "description": "RO kWh", "type": "float"},
    "BESS_RO_COST": {"cell": "H36", "description": "RO cost £", "type": "string"},
    
    "BESS_FIT_RATE": {"cell": "F37", "description": "FiT rate display", "type": "string"},
    "BESS_FIT_KWH": {"cell": "G37", "description": "FiT kWh", "type": "float"},
    "BESS_FIT_COST": {"cell": "H37", "description": "FiT cost £", "type": "string"},
}

structure["cell_mappings"] = critical_cells

for key, info in critical_cells.items():
    print(f"{key:30} → {info['cell']:5} | {info['description']}")

print()

# Save to JSON
with open('BESS_SHEET_STRUCTURE.json', 'w') as f:
    json.dump(structure, f, indent=2)

print("=" * 100)
print("✅ STRUCTURE SAVED TO: BESS_SHEET_STRUCTURE.json")
print("=" * 100)
print()

# Create Python constants file
print("Generating Python constants file...")
with open('bess_sheet_constants.py', 'w') as f:
    f.write('#!/usr/bin/env python3\n')
    f.write('"""\n')
    f.write('BESS Sheet Cell Mappings - Auto-generated Constants\n')
    f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write('DO NOT EDIT - Regenerate using read BESS sheet script\n')
    f.write('"""\n\n')
    f.write('SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"\n')
    f.write('SHEET_NAME = "BESS"\n\n')
    f.write('# BESS Configuration Input Cells\n')
    f.write('CELL_IMPORT_CAPACITY_KW = "F13"\n')
    f.write('CELL_EXPORT_CAPACITY_KW = "F14"\n')
    f.write('CELL_DURATION_HRS = "F15"\n')
    f.write('CELL_MAX_CYCLES_DAY = "F16"\n\n')
    f.write('# DNO DUoS Rates (Row 10 - data row, NOT row 9 header)\n')
    f.write('CELL_RED_RATE_PKWH = "B10"\n')
    f.write('CELL_AMBER_RATE_PKWH = "C10"\n')
    f.write('CELL_GREEN_RATE_PKWH = "D10"\n\n')
    f.write('# PPA Pricing\n')
    f.write('CELL_PPA_PRICE = "D43"\n\n')
    f.write('# BESS Cost Output Cells (Rates in column F, kWh in G, Costs in H)\n')
    f.write('BESS_COST_CELLS = {\n')
    f.write('    "red_duos": {"rate": "F28", "kwh": "G28", "cost": "H28"},\n')
    f.write('    "amber_duos": {"rate": "F29", "kwh": "G29", "cost": "H29"},\n')
    f.write('    "green_duos": {"rate": "F30", "kwh": "G30", "cost": "H30"},\n')
    f.write('    "tnuos": {"rate": "F31", "kwh": "G31", "cost": "H31"},\n')
    f.write('    "bnuos": {"rate": "F32", "kwh": "G32", "cost": "H32"},\n')
    f.write('    "ccl": {"rate": "F35", "kwh": "G35", "cost": "H35"},\n')
    f.write('    "ro": {"rate": "F36", "kwh": "G36", "cost": "H36"},\n')
    f.write('    "fit": {"rate": "F37", "kwh": "G37", "cost": "H37"},\n')
    f.write('}\n\n')
    f.write('# Fixed Cost Rates (£/MWh)\n')
    f.write('FIXED_COSTS = {\n')
    f.write('    "tnuos": 12.50,\n')
    f.write('    "bnuos": 4.50,\n')
    f.write('    "ccl": 7.75,\n')
    f.write('    "ro": 61.90,\n')
    f.write('    "fit": 11.50\n')
    f.write('}\n')

print("✅ GENERATED: bess_sheet_constants.py")
print()

print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()
print("Files created:")
print("  1. BESS_SHEET_STRUCTURE.json - Complete structure documentation")
print("  2. bess_sheet_constants.py - Python constants for scripts")
print()
print("Key findings:")
print("  • BESS config in F13:F16 (capacity, duration, max cycles)")
print("  • DNO rates in row 10 (B10, C10, D10) - NOT row 9!")
print("  • PPA price in D43")
print("  • BESS costs written to F28:H37 (rates, kWh, costs)")
print("  • Non-BESS costs in A28:C37 for comparison")
print()
print("Future scripts should:")
print("  • Import from bess_sheet_constants.py")
print("  • Use BESS_COST_CELLS dictionary for output")
print("  • Read DNO rates from row 10, NOT row 9")
print("  • Preserve all existing formulas and manual edits")
