#!/usr/bin/env python3
"""
Install DNO Lookup Apps Script to BESS Sheet
Adds menu-driven DNO lookup functionality
"""

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

def install_apps_script():
    """Instructions to install the Apps Script"""
    
    print("=" * 80)
    print("📋 DNO Lookup Apps Script Installation Instructions")
    print("=" * 80)
    
    print("\n✅ Apps Script file created: bess_dno_lookup.gs")
    print("\n📝 To install in Google Sheets:")
    print("\n1. Open your Google Sheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    
    print("\n2. Go to: Extensions → Apps Script")
    
    print("\n3. Click the + button to create a new script file")
    
    print("\n4. Copy the contents of 'bess_dno_lookup.gs' and paste into the script editor")
    
    print("\n5. Save the script (Ctrl+S or Cmd+S)")
    
    print("\n6. Close the Apps Script editor and reload your spreadsheet")
    
    print("\n7. You'll see a new menu: 🔌 DNO Lookup")
    
    print("\n" + "=" * 80)
    print("🎯 How to Use:")
    print("=" * 80)
    
    print("\n📍 Method 1: Lookup by MPAN ID (Recommended)")
    print("   1. Enter MPAN ID (10-23) in cell B6")
    print("   2. Menu: 🔌 DNO Lookup → 🔄 Refresh DNO Data")
    print("   3. DNO info auto-populates in C6:H6")
    
    print("\n📍 Method 2: Postcode Lookup")
    print("   1. Enter postcode in cell A6")
    print("   2. Menu: 🔌 DNO Lookup → 📍 Lookup by Postcode")
    print("   3. (Currently shows instructions to use MPAN instead)")
    
    print("\n🔌 Then select voltage level:")
    print("   1. Choose from dropdown in A9 (LV/HV/EHV)")
    print("   2. Red/Amber/Green DUoS rates auto-populate in B9:D9")
    
    print("\n" + "=" * 80)
    print("📊 MPAN IDs by Region:")
    print("=" * 80)
    
    mpan_regions = {
        10: "Eastern (UKPN-EPN)",
        11: "East Midlands (NGED-EM)",
        12: "London (UKPN-LPN)",
        13: "Merseyside & N Wales (SP-Manweb)",
        14: "West Midlands (NGED-WM)",
        15: "North East (NPg-NE)",
        16: "North West (ENWL)",
        17: "North Scotland (SSE-SHEPD)",
        18: "South Scotland (SP-Distribution)",
        19: "South Eastern (UKPN-SPN)",
        20: "Southern (SSE-SEPD)",
        21: "South Wales (NGED-SWales)",
        22: "South Western (NGED-SW)",
        23: "Yorkshire (NPg-Y)"
    }
    
    for mpan_id, region in mpan_regions.items():
        print(f"   {mpan_id:2d} - {region}")
    
    print("\n" + "=" * 80)
    print("✅ Features:")
    print("=" * 80)
    print("   • 🔄 Auto-refresh DNO data from BigQuery")
    print("   • 🆔 MPAN ID lookup (10-23)")
    print("   • 📍 Postcode lookup (instructions provided)")
    print("   • 📊 Auto-populate: DNO_Key, Name, Short Code, MPAN, GSP Group")
    print("   • 🔌 Integrated with DUoS rates lookup")
    print("   • ℹ️ Built-in instructions menu")
    
    print("\n" + "=" * 80)
    print("🔐 Data Source:")
    print("=" * 80)
    print(f"   Project: inner-cinema-476211-u9")
    print(f"   Dataset: uk_energy_prod")
    print(f"   Table: neso_dno_reference (14 DNOs)")
    print(f"   Proxy: https://gb-power-market-jj.vercel.app/api/proxy-v2")
    
    print("\n" + "=" * 80)
    
    # Also update the BESS sheet with instructions
    try:
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        bess_ws = sh.worksheet("BESS")
        
        # Add instruction text
        instructions = [
            ['Site Post Code', 'MPAN or Distributor ID', 'DNO_Key', 'DNO_Name', 'DNO_Short_Code', 'Market_Participant_ID', 'GSP_Group_ID', 'GSP_Group_Name'],  # Row 5 headers
            ['← Enter postcode', '← Enter MPAN (10-23), then use menu: DNO Lookup → Refresh', '', '', '', '', '', '']  # Row 6 instructions
        ]
        
        bess_ws.update(instructions, 'A5:H6')
        
        print("\n✅ Updated BESS sheet with instructions!")
        print(f"\n🔗 Open sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={bess_ws.id}")
        
    except Exception as e:
        print(f"\n⚠️ Could not update BESS sheet: {e}")
        print("   (You can still manually install the Apps Script)")

if __name__ == "__main__":
    install_apps_script()
