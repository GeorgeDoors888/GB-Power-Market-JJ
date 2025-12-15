#!/usr/bin/env python3
"""
Complete graphics cleanup - read actual values and fix properly
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("\n🔧 COMPLETE GRAPHICS CLEANUP...")
print("=" * 70)

# Setup
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

ss = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = ss.worksheet('Dashboard')

# Read rows 7-17 (fuel types section)
print("📊 Reading GENERATION BY FUEL TYPE section...")
fuel_values = dashboard.get('A8:A17')  # Rows 8-17, column A

print("\nCurrent fuel type values:")
for i, row in enumerate(fuel_values, 8):
    if row:
        print(f"  Row {i}: '{row[0]}'")

# Define correct fuel type names (without country flags)
correct_fuels = {
    'Gas (CCGT)': '🔥 Gas (CCGT)',
    'CCGT': '🔥 Gas (CCGT)',
    'Nuclear': '⚛️ Nuclear',
    'Wind': '💨 Wind',
    'Biomass': '🌿 Biomass',
    'Hydro (Run-of-River)': '💧 Hydro (Run-of-River)',
    'Hydro': '💧 Hydro (Run-of-River)',
    'Pumped Storage': '💧 Pumped Storage 🔋',
    'Coal': '⚫ Coal',
    'Gas Peaking (OCGT)': '🔥 Gas Peaking (OCGT)',
    'OCGT': '🔥 Gas Peaking (OCGT)',
    'Oil': '🛢️ Oil',
    'Other': '⚙️ Other'
}

print("\n📝 Applying clean fuel type names...")

updates = []
for i, row in enumerate(fuel_values, 8):
    if row and row[0]:
        old_value = row[0]
        
        # Remove ALL emojis first, then extract base name
        import re
        # Remove all emoji and flag characters
        clean_name = re.sub(r'[^\w\s()-]', '', old_value).strip()
        
        # Match to correct fuel type
        new_value = None
        for base_name, formatted_name in correct_fuels.items():
            if base_name.lower() in clean_name.lower() or clean_name.lower() in base_name.lower():
                new_value = formatted_name
                break
        
        if new_value and new_value != old_value:
            updates.append((i, old_value, new_value))
            print(f"  Row {i}: '{old_value}' → '{new_value}'")

# Apply updates
if updates:
    print(f"\n✅ Updating {len(updates)} fuel types...")
    for row_num, old_val, new_val in updates:
        dashboard.update_acell(f'A{row_num}', new_val)
    print(f"✅ Updated {len(updates)} cells")
else:
    print("\n✅ No updates needed")

# Now fix interconnectors (rows 9-17 in column D or E)
print("\n📊 Checking interconnectors section...")
interconnector_values = dashboard.get('D9:D17')

print("\nCurrent interconnector values:")
for i, row in enumerate(interconnector_values, 9):
    if row and row[0]:
        print(f"  Row {i}: '{row[0]}'")

# Correct interconnector names
correct_interconnectors = {
    'NSL (Norway)': '🇳🇴 NSL (Norway)',
    'IFA (France)': '⚡ IFA (France) 🇫🇷',
    'IFA2 (France)': '⚡ IFA2 (France) 🇫🇷',
    'ElecLink (France)': '⚡ ElecLink (France) 🇫🇷',
    'Nemo (Belgium)': '⚡ Nemo (Belgium) 🇧🇪',
    'Viking Link (Denmark)': '⚡ Viking Link (Denmark) 🇩🇰',
    'BritNed (Netherlands)': '🇳🇱 BritNed (Netherlands)',
    'Moyle (N.Ireland)': '⚡ Moyle (N.Ireland) 🇮🇪',
    'East-West (Ireland)': '⚡ East-West (Ireland) 🇮🇪',
    'Greenlink (Ireland)': '⚡ Greenlink (Ireland) 🇮🇪'
}

interconnector_updates = []
for i, row in enumerate(interconnector_values, 9):
    if row and row[0]:
        old_value = row[0]
        
        # Match to correct interconnector
        new_value = None
        for base_name, formatted_name in correct_interconnectors.items():
            # Extract country/name without emojis for matching
            import re
            clean_old = re.sub(r'[^\w\s()-]', '', old_value).strip()
            clean_base = re.sub(r'[^\w\s()-]', '', base_name).strip()
            
            if clean_base.lower() in clean_old.lower() or clean_old.lower() in clean_base.lower():
                new_value = formatted_name
                break
        
        if new_value and new_value != old_value:
            interconnector_updates.append((i, old_value, new_value))
            print(f"  Row {i}: '{old_value}' → '{new_value}'")

# Apply interconnector updates
if interconnector_updates:
    print(f"\n✅ Updating {len(interconnector_updates)} interconnectors...")
    for row_num, old_val, new_val in interconnector_updates:
        dashboard.update_acell(f'D{row_num}', new_val)
    print(f"✅ Updated {len(interconnector_updates)} interconnector cells")
else:
    print("\n✅ Interconnectors already correct")

print("\n" + "=" * 70)
print("✅ COMPLETE CLEANUP FINISHED")
print("=" * 70)
print(f"\n📊 Summary:")
print(f"   • Fuel types cleaned: {len(updates)}")
print(f"   • Interconnectors fixed: {len(interconnector_updates)}")
print()
