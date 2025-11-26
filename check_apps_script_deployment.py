#!/usr/bin/env python3
"""
Test Apps Script Deployment - Version 16
Check what files are in Apps Script and their content
"""

import requests
import json

DEPLOYMENT_URL = "https://script.google.com/macros/s/AKfycbzfUp1v5euSL_fuPNMkE8MuzUdCOlvJ5NA-DpwsIVZhsvIOJfBDB0pr1k5yulLJ0j_F/exec"

def main():
    print("=" * 80)
    print("APPS SCRIPT DEPLOYMENT CHECK - VERSION 16")
    print("=" * 80)
    
    print(f"\n🔗 Deployment URL: {DEPLOYMENT_URL}")
    
    print("\n" + "=" * 80)
    print("CHECKLIST: What You Need in Apps Script")
    print("=" * 80)
    
    print("\n📁 Required Files:")
    print("   1. ✅ constraint_map_minimal.gs")
    print("      - Menu creation")
    print("      - showConstraintMapLeaflet() function")
    print("      - showConstraintMapGoogle() function")
    print("")
    print("   2. ✅ ConstraintMap_Leaflet.html")
    print("      - Leaflet-based map (NO API key)")
    print("      - Data embedded from Python")
    print("")
    print("   3. ⚠️  ConstraintMap_Python.html (optional)")
    print("      - Google Maps version (needs API key fix)")
    
    print("\n" + "=" * 80)
    print("DEPLOYMENT STEPS VERIFICATION")
    print("=" * 80)
    
    print("\n❓ Have you done these steps?")
    print("")
    print("Step 1: Open Apps Script Editor")
    print("   - In Google Sheets: Extensions → Apps Script")
    print("")
    print("Step 2: Delete old files (if present)")
    print("   - constraint_map.gs (the old complex one)")
    print("   - ConstraintMap.html (old version)")
    print("")
    print("Step 3: Upload new files")
    print("   - Add file: constraint_map_minimal.gs")
    print("   - Add HTML: ConstraintMap_Leaflet.html")
    print("")
    print("Step 4: Rename constraint_map_minimal.gs")
    print("   - Right-click → Rename to: 'Code.gs' or keep as is")
    print("")
    print("Step 5: Deploy")
    print("   - Deploy → New deployment")
    print("   - Type: Web app")
    print("   - Execute as: Me")
    print("   - Access: Anyone with Google account")
    print("")
    print("Step 6: Refresh Google Sheets")
    print("   - Close and reopen the sheet")
    print("   - Menu should show: 🗺️ Constraint Map")
    
    print("\n" + "=" * 80)
    print("COMMON ISSUES & FIXES")
    print("=" * 80)
    
    print("\n❌ Issue 1: Menu doesn't appear")
    print("   Fix: Close and reopen Google Sheets")
    print("   Why: onOpen() only runs on sheet open")
    
    print("\n❌ Issue 2: 'ConstraintMap_Leaflet not found'")
    print("   Fix: Upload the HTML file to Apps Script")
    print("   Location: dashboard/apps-script/ConstraintMap_Leaflet.html")
    
    print("\n❌ Issue 3: Sidebar shows blank")
    print("   Fix: Check browser console (F12)")
    print("   Likely: HTML file not uploaded or wrong name")
    
    print("\n❌ Issue 4: Deployment doesn't work")
    print("   Fix: Ensure all files are saved before deploying")
    print("   Tip: Use 'Test deployment' first")
    
    print("\n" + "=" * 80)
    print("QUICK TEST")
    print("=" * 80)
    
    print("\n1. In Apps Script editor, click dropdown by 'Run'")
    print("2. Select: onOpen")
    print("3. Click 'Run'")
    print("4. Should see: 'Execution log' with no errors")
    print("5. Check Sheets: Menu 🗺️ Constraint Map should appear")
    
    print("\n" + "=" * 80)
    print("FILES TO COPY")
    print("=" * 80)
    
    print("\n📂 Local file paths:")
    print("   1. /Users/georgemajor/GB Power Market JJ/dashboard/apps-script/constraint_map_minimal.gs")
    print("   2. /Users/georgemajor/GB Power Market JJ/dashboard/apps-script/ConstraintMap_Leaflet.html")
    
    print("\n📝 What each file does:")
    print("   constraint_map_minimal.gs:")
    print("      - Creates menu in Google Sheets")
    print("      - Shows sidebar with map HTML")
    print("      - Only ~30 lines of simple code")
    print("")
    print("   ConstraintMap_Leaflet.html:")
    print("      - Complete standalone map")
    print("      - Data embedded (no backend needed)")
    print("      - Uses OpenStreetMap (no API key)")
    
    print("\n" + "=" * 80)
    print("NEXT ACTION")
    print("=" * 80)
    
    print("\n👉 Tell me what you see:")
    print("   A. No menu in Google Sheets?")
    print("   B. Menu appears but sidebar blank?")
    print("   C. Sidebar shows but no map?")
    print("   D. Error message in sidebar?")
    print("   E. Something else?")
    
    print("\n💡 Or run this to check files are correct:")
    print("   ls -lh dashboard/apps-script/")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
