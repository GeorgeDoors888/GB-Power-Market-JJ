#!/usr/bin/env python3
"""
Generate sparkline formulas for manual copy-paste into Google Sheets
Once entered manually, formulas will persist across all automated updates
"""

# Fuel type sparklines (Column C, rows 11-20)
FUEL_SPARKLINES = [
    (11, 1, '#4ECDC4', 20, '💨 Wind'),
    (12, 2, '#FF6B6B', 10, '🔥 CCGT'),
    (13, 3, '#FFA07A', 5, '⚛️ Nuclear'),
    (14, 4, '#98D8C8', 5, '🌱 Biomass'),
    (15, 5, '#F7DC6F', 2, '❓ Other'),
    (16, 6, '#85C1E9', 2, '💧 Pumped'),
    (17, 7, '#52B788', 1, '🌊 Hydro'),
    (18, 8, '#E76F51', 1, '🔥 OCGT'),
    (19, 9, '#666666', 1, '⚫ Coal'),
    (20, 10, '#8B4513', 1, '🛢️ Oil'),
]

# Interconnector sparklines (Column F, rows 11-20)
IC_SPARKLINES = [
    (11, 11, '#0055A4', 2, '🇫🇷 France'),
    (12, 12, '#169B62', 1, '🇮🇪 Ireland'),
    (13, 13, '#FF9B00', 1, '🇳🇱 Netherlands'),
    (14, 14, '#00843D', 1, '🏴 East-West'),
    (15, 15, '#FDDA24', 1, '🇧🇪 Belgium (Nemo)'),
    (16, 16, '#EF3340', 1, '🇧🇪 Belgium (Elec)'),
    (17, 17, '#0055A4', 2, '🇫🇷 IFA2'),
    (18, 18, '#BA0C2F', 2, '🇳🇴 Norway (NSL)'),
    (19, 19, '#C8102E', 2, '🇩🇰 Viking Link'),
    (20, 20, '#169B62', 1, '🇮🇪 Greenlink'),
]

print("=" * 80)
print("📋 SPARKLINE FORMULAS FOR MANUAL ENTRY")
print("=" * 80)
print("\n⚠️ IMPORTANT: You only need to do this ONCE. After manual entry, the formulas")
print("   will persist across all automated dashboard updates.\n")

print("\n" + "=" * 80)
print("COLUMN C - FUEL TYPE SPARKLINES (Rows 11-20)")
print("=" * 80)
print("\nInstructions:")
print("1. Open Google Sheets in browser")
print("2. Navigate to 'GB Live' sheet")
print("3. Click cell C11 and paste the first formula")
print("4. Press Enter, then move to C12 and paste the next formula")
print("5. Repeat for all 10 fuel types\n")

for row, data_row, color, max_val, label in FUEL_SPARKLINES:
    formula = f'=SPARKLINE(Data_Hidden!A{data_row}:X{data_row},{{"charttype","line";"linewidth",2;"color","{color}";"max",{max_val};"ymin",0}})'
    print(f"Cell C{row} ({label}):")
    print(f"{formula}\n")

print("\n" + "=" * 80)
print("COLUMN F - INTERCONNECTOR SPARKLINES (Rows 11-20)")
print("=" * 80)
print("\nInstructions:")
print("1. Click cell F11 and paste the first formula")
print("2. Press Enter, then move to F12 and paste the next formula")
print("3. Repeat for all 10 interconnectors\n")

for row, data_row, color, max_val, label in IC_SPARKLINES:
    formula = f'=SPARKLINE(Data_Hidden!A{data_row}:X{data_row},{{"charttype","line";"linewidth",2;"color","{color}";"max",{max_val};"ymin",0}})'
    print(f"Cell F{row} ({label}):")
    print(f"{formula}\n")

print("\n" + "=" * 80)
print("✅ AFTER MANUAL ENTRY")
print("=" * 80)
print("\n1. Verify sparklines display correctly in columns C and F")
print("2. Run: python3 update_bg_live_dashboard.py")
print("3. Confirm formulas are NOT overwritten (columns A-B and D-E update, C and F stay)")
print("4. Set up cron job for automated updates every 5 minutes")
print("\n⚠️ The update script will SKIP columns C and F from now on to preserve formulas")
print("\n" + "=" * 80)
