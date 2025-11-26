#!/usr/bin/env python3
"""
Add dropdowns and data validation to BESS sheet
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import os

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

# BigQuery setup
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

sheet_id = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(sheet_id)
bess_sheet = sh.worksheet('BESS')

print("🔧 Adding dropdowns and data validation to BESS sheet...")

# ==============================================
# 1. VOLTAGE LEVEL DROPDOWN (A10)
# ==============================================
print("\n1️⃣ Adding Voltage Level dropdown...")

voltage_options = [
    "LV (<1kV)",
    "LV sub (<1kV)",
    "HV (6.6-33kV)",
    "EHV (33-132kV)",
    "132kV Transmission"
]

bess_sheet.add_validation(
    'A10',
    gspread.DataValidationRule(
        gspread.BooleanCondition('ONE_OF_LIST', voltage_options),
        showCustomUi=True,
        strict=True
    )
)
print(f"   ✅ Voltage Level dropdown added to A10 ({len(voltage_options)} options)")

# ==============================================
# 2. PROFILE CLASS DROPDOWN (E10)
# ==============================================
print("\n2️⃣ Adding Profile Class dropdown...")

profile_classes = [
    "00 (Half-Hourly)",
    "01 (Domestic Unrestricted)",
    "02 (Domestic Economy 7)",
    "03 (Non-Domestic Unrestricted)",
    "04 (Non-Domestic Economy 7)",
    "05 (Non-Domestic Maximum Demand)",
    "06 (Non-Domestic Two-Rate)",
    "07 (Seasonal Time of Day)",
    "08 (Seasonal"
]

bess_sheet.data_validation(
    'E10',
    {
        'type': 'ONE_OF_LIST',
        'values': profile_classes,
        'strict': True,
        'showCustomUi': True
    }
)
print(f"   ✅ Profile Class dropdown added to E10 ({len(profile_classes)} options)")

# ==============================================
# 3. METER REGISTRATION DROPDOWN (F10)
# ==============================================
print("\n3️⃣ Adding Meter Registration dropdown...")

meter_types = [
    "800 (NHH Non-Settlement)",
    "801 (HH Metered)",
    "802 (NHH Metered - Unmetered Supplies)",
    "H (HH Metered - Demand)",
    "M (NHH - Manually Read)",
    "C (NHH - Check Metering)",
    "P (NHH - Prepayment)"
]

bess_sheet.data_validation(
    'F10',
    {
        'type': 'ONE_OF_LIST',
        'values': meter_types,
        'strict': True,
        'showCustomUi': True
    }
)
print(f"   ✅ Meter Registration dropdown added to F10 ({len(meter_types)} options)")

# ==============================================
# 4. DUOS CHARGING CLASS DROPDOWN (H10)
# ==============================================
print("\n4️⃣ Adding DUoS Charging Class dropdown...")

duos_classes = [
    "Domestic Unrestricted",
    "Domestic Two Rate",
    "Non-Domestic HH",
    "Non-Domestic NHH Unrestricted",
    "Non-Domestic NHH Two Rate",
    "LV Generation",
    "HV Generation",
    "EHV Generation",
    "Unmetered Supply"
]

bess_sheet.data_validation(
    'H10',
    {
        'type': 'ONE_OF_LIST',
        'values': duos_classes,
        'strict': True,
        'showCustomUi': True
    }
)
print(f"   ✅ DUoS Charging Class dropdown added to H10 ({len(duos_classes)} options)")

# ==============================================
# 5. DNO DISTRIBUTOR DROPDOWN (B6) - From BigQuery
# ==============================================
print("\n5️⃣ Adding DNO Distributor dropdown from BigQuery...")

dno_query = """
SELECT DISTINCT 
    CAST(distributor_id AS STRING) as id,
    name,
    short_code
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
WHERE distributor_id BETWEEN 10 AND 23
ORDER BY distributor_id
"""

dno_df = bq_client.query(dno_query).to_dataframe()
dno_options = [f"{row['id']} - {row['short_code']}" for _, row in dno_df.iterrows()]

bess_sheet.data_validation(
    'B6',
    {
        'type': 'ONE_OF_LIST',
        'values': dno_options,
        'strict': False,  # Allow manual MPAN input
        'showCustomUi': True
    }
)
print(f"   ✅ DNO Distributor dropdown added to B6 ({len(dno_options)} options)")
print("   📋 Options:", ', '.join(dno_options[:5]), "...")

# ==============================================
# 6. NUMBER VALIDATION FOR kW FIELDS (B17:B19)
# ==============================================
print("\n6️⃣ Adding number validation for kW fields...")

for cell in ['B17', 'B18', 'B19']:
    bess_sheet.data_validation(
        cell,
        {
            'type': 'NUMBER_GREATER',
            'values': [0],
            'strict': True,
            'showCustomUi': True
        }
    )

print("   ✅ Number validation added to B17 (Min kW), B18 (Avg kW), B19 (Max kW)")

# ==============================================
# 7. POSTCODE FORMAT HELP TEXT (A6)
# ==============================================
print("\n7️⃣ Adding help text to Postcode field...")

# Add note to A6
note_text = """UK Postcode Format:
Examples: SW1A 1AA, M1 1AE, B33 8TH

System will auto-lookup:
• DNO distributor
• GSP Group
• Regional network info"""

bess_sheet.update_note('A6', note_text)
print("   ✅ Help note added to A6 (Postcode)")

# ==============================================
# 8. MPAN FORMAT HELP TEXT (B6)
# ==============================================
print("\n8️⃣ Adding help text to MPAN field...")

mpan_note = """MPAN Format:
• 13-digit core MPAN
• Or 21-digit full MPAN
• First 2 digits = DNO ID (10-23)

Examples:
• 14055667788 (core)
• 00 800 999 932 14055667788 (full)

System extracts core and validates DNO"""

bess_sheet.update_note('B6', mpan_note)
print("   ✅ Help note added to B6 (MPAN)")

# ==============================================
# 9. CONDITIONAL FORMATTING FOR RATES
# ==============================================
print("\n9️⃣ Adding conditional formatting for DUoS rates...")

# Format rates with color scale (green = cheap, red = expensive)
rate_cells = ['B10', 'C10', 'D10']  # Red, Amber, Green rates

# Add currency formatting
for cell in rate_cells:
    bess_sheet.format(cell, {
        "numberFormat": {
            "type": "NUMBER",
            "pattern": "0.000\" p/kWh\""
        }
    })

print("   ✅ Currency formatting applied to rate cells")

# ==============================================
# 10. SUMMARY
# ==============================================
print("\n" + "="*60)
print("✅ DROPDOWNS & VALIDATION COMPLETE")
print("="*60)
print("\n📋 Added dropdowns:")
print("   • A10: Voltage Level (5 options)")
print("   • B6: DNO Distributor (from BigQuery)")
print("   • E10: Profile Class (8 options)")
print("   • F10: Meter Registration (7 options)")
print("   • H10: DUoS Charging Class (9 options)")
print("\n🔢 Added validation:")
print("   • B17-B19: Number validation (kW > 0)")
print("\n💬 Added help notes:")
print("   • A6: Postcode format guide")
print("   • B6: MPAN format guide")
print("\n🎨 Added formatting:")
print("   • B10-D10: Currency format (p/kWh)")
print("\n🔄 Test the dropdowns by clicking on the cells!")
print("="*60)
