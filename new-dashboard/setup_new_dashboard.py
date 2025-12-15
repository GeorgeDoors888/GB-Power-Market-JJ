#!/usr/bin/env python3
"""
Set up new dashboard with existing automation infrastructure
"""
import sys
sys.path.append('..')

# Copy realtime updater pattern
NEW_SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

print("=" * 80)
print("DASHBOARD V2 SETUP")
print("=" * 80)
print()
print("✅ Spreadsheet created with clasp")
print("✅ Apps Script deployed with version control")
print()
print("🔗 New Dashboard: https://docs.google.com/spreadsheets/d/" + NEW_SHEET_ID)
print()
print("=" * 80)
print("MANUAL STEPS NEEDED")
print("=" * 80)
print()
print("1. ✅ Share spreadsheet with: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com")
print("   (Check if you did this - wait 1-2 minutes for permissions to propagate)")
print()
print("2. Copy old dashboard structure:")
print("   - Open old: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
print("   - Copy rows 1-10 (KPIs) → paste in new Dashboard sheet")
print("   - Copy rows 116-126 (Constraints) → paste in new Dashboard A116")
print()
print("3. Test constraint map:")
print("   - Refresh new spreadsheet")
print("   - Menu: Maps → Constraint Map")
print()
print("=" * 80)
print("AUTOMATED REFRESH (NEXT)")
print("=" * 80)
print()
print("Will adapt realtime_dashboard_updater.py to work with new sheet")
print("Run: python3 setup_auto_refresh.py")
print()
