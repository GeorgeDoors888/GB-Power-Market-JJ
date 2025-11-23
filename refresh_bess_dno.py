#!/usr/bin/env python3
"""
BESS Sheet DNO Refresh - One-Click Update
Reads MPAN from B6, voltage from A9, updates all DNO info and rates
"""

from dno_lookup_python import refresh_from_sheet

if __name__ == "__main__":
    print("\n🔄 Refreshing BESS sheet from current inputs...")
    print("   Reading MPAN from B6")
    print("   Reading Voltage from A9")
    print("")
    
    success = refresh_from_sheet()
    
    if success:
        print("\n✅ Done! Check your BESS sheet:")
        print("   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit#gid=1291323643")
    else:
        print("\n❌ Update failed - see errors above")
