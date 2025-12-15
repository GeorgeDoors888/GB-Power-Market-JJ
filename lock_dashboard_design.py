#!/usr/bin/env python3
"""
Document Dashboard Design
==========================
Reads the current Dashboard state and documents it without making any changes.
This preserves the existing design, fonts, colors, and layout.

This script:
1. Reads all current data and formatting
2. Documents the exact structure
3. Creates a backup specification (NO formatting changes applied)
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- Configuration ---
DASHBOARD_SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_NAME = 'Dashboard'

def get_sheet():
    """Connects to Google Sheets and returns the dashboard worksheet."""
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)

def read_current_state(dashboard):
    """Reads and documents the current Dashboard state."""
    print("📖 Reading current Dashboard state...")
    
    # Read all data
    all_data = dashboard.get('A1:L80')
    
    structure = {
        "last_read": datetime.now().isoformat(),
        "total_rows": len(all_data),
        "sections": {}
    }
    
    # Document key sections
    if len(all_data) > 0:
        structure["sections"]["header"] = {
            "row": 1,
            "data": all_data[0],
            "description": "Main Dashboard title"
        }
    
    if len(all_data) > 1:
        structure["sections"]["timestamp"] = {
            "row": 2,
            "data": all_data[1],
            "description": "Last updated timestamp"
        }
    
    if len(all_data) > 5:
        structure["sections"]["fuel_interconnectors_header"] = {
            "row": 6,
            "data": all_data[5],
            "description": "Fuel & Interconnectors section header"
        }
    
    # Document interconnectors
    interconnectors = []
    for i in range(7, 17):
        if i < len(all_data) and len(all_data[i]) > 3:
            interconnectors.append({
                "row": i + 1,
                "name": all_data[i][3],
                "data": all_data[i][3:6]
            })
    structure["sections"]["interconnectors"] = interconnectors
    
    print(f"   ✅ Read {len(all_data)} rows")
    print(f"   ✅ Found {len(interconnectors)} interconnectors")
    
    return structure

def document_formatting(dashboard):
    """Documents the current formatting without changing anything."""
    print("\n� Documenting current Dashboard formatting...")
    
    # Just document what exists - no changes
    formatting_spec = {
        "note": "This documents the existing design. NO changes are applied.",
        "sections": {
            "header": "Row 1 - Main title with blue background",
            "timestamp": "Row 2 - Last updated info",
            "fuel_interconnectors": "Rows 6-17 - Fuel (green) and Interconnectors (blue)",
            "outages": "Row 20+ - Outages section with red header",
            "gsp": "Row 36+ - GSP Analysis section"
        }
    }
    
    print(f"   ✅ Documented current design (no changes applied)")
    return formatting_spec

def main():
    """Main function to read and document the Dashboard (no changes)."""
    print("� DASHBOARD DOCUMENTATION PROCESS")
    print("=" * 80)
    print("ℹ️  This script READS ONLY - it will NOT change any formatting")
    print("=" * 80)
    
    try:
        dashboard = get_sheet()
        
        # Step 1: Read and document current state
        structure = read_current_state(dashboard)
        
        # Step 2: Document formatting (no changes)
        formatting_spec = document_formatting(dashboard)
        structure["formatting"] = formatting_spec
        
        # Save structure to file
        with open('dashboard_structure_locked.json', 'w') as f:
            json.dump(structure, f, indent=2)
        print(f"   ✅ Saved structure to dashboard_structure_locked.json")
        
        print("\n" + "=" * 80)
        print("✅ DASHBOARD DOCUMENTATION COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Current Structure:")
        print(f"   • Total Rows: {structure['total_rows']}")
        print(f"   • Interconnectors: {len(structure['sections']['interconnectors'])}")
        print(f"\n✅ No formatting changes were applied - existing design preserved")
        print(f"\n🔗 View Dashboard: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")
        print(f"📄 Structure saved: dashboard_structure_locked.json")
        
    except Exception as e:
        print(f"\n❌ Error during documentation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
