#!/usr/bin/env python3
"""
Fix Dashboard Graphics - Remove incorrectly placed emojis from fuel types
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("\n🔧 FIXING DASHBOARD GRAPHICS...")
print("=" * 70)

# Setup
scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')

# Get all values
all_values = dashboard.get_all_values()

print("📋 Analyzing current state...")

# Find and fix misplaced graphics
fixes = []

for row_idx, row in enumerate(all_values, 1):
    if len(row) > 0:
        cell_value = row[0]
        
        # Fix fuel types that have wrong flags
        if 'Nuclear 🇫🇷' in cell_value:
            new_value = cell_value.replace(' 🇫🇷', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Wind 🇫🇷' in cell_value:
            new_value = cell_value.replace(' 🇫🇷', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Biomass 🇫🇷' in cell_value:
            new_value = cell_value.replace(' 🇫🇷', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Hydro (Run-of-River) 🇧🇪' in cell_value or 'Hydro 🇧🇪' in cell_value:
            new_value = cell_value.replace(' 🇧🇪', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Pumped Storage 🇩🇰' in cell_value:
            # This should just be: 💧 Pumped Storage 🔋
            new_value = '💧 Pumped Storage 🔋'
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Gas Peaking (OCGT) 🇮🇪' in cell_value or 'OCGT 🇮🇪' in cell_value:
            new_value = cell_value.replace(' 🇮🇪', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Oil 🇮🇪' in cell_value:
            new_value = cell_value.replace(' 🇮🇪', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))
            
        elif 'Other 🇮🇪' in cell_value:
            new_value = cell_value.replace(' 🇮🇪', '')
            fixes.append((f'A{row_idx}', cell_value, new_value))

print(f"\n✅ Found {len(fixes)} cells to fix")

# Apply fixes
if fixes:
    print("\n📝 Applying fixes:")
    for cell, old_val, new_val in fixes:
        print(f"   {cell}: '{old_val}' → '{new_val}'")
        dashboard.update_acell(cell, new_val)
    
    print(f"\n✅ Fixed {len(fixes)} cells")
else:
    print("✅ No fixes needed")

print("\n" + "=" * 70)
print("✅ GRAPHICS FIX COMPLETE")
print("=" * 70)
print("\n📊 Fuel types should now show correct emojis only")
print("📊 Interconnectors should keep their flags")
print("📊 Pumped Storage: 💧 🔋")
print()
