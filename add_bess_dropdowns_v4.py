#!/usr/bin/env python3
"""
Add dropdowns and data validation to BESS sheet using Sheets API v4
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

sheet_id = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
sh = gc.open_by_key(sheet_id)
bess_sheet = sh.worksheet('BESS')
sheet_gid = bess_sheet.id

print("🔧 Adding dropdowns and data validation to BESS sheet...")

# Helper function to convert A1 notation to grid coordinates
def a1_to_grid(cell):
    """Convert A1 notation to row/col indices (0-based)"""
    import re
    match = re.match(r'([A-Z]+)(\d+)', cell)
    col_str, row_str = match.groups()
    
    col = 0
    for char in col_str:
        col = col * 26 + (ord(char) - ord('A') + 1)
    col -= 1  # 0-based
    
    row = int(row_str) - 1  # 0-based
    
    return row, col

# ==============================================
# Get DNO options from BigQuery first
# ==============================================
print("\n📊 Fetching DNO options from BigQuery...")

dno_query = """
SELECT DISTINCT 
    CAST(mpan_distributor_id AS STRING) as id,
    dno_short_code as short_code
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
WHERE mpan_distributor_id BETWEEN 10 AND 23
ORDER BY id
"""

dno_df = bq_client.query(dno_query).to_dataframe()
dno_options = [f"{row['id']} - {row['short_code']}" for _, row in dno_df.iterrows()]
print(f"   ✅ Fetched {len(dno_options)} DNO options")

# ==============================================
# Build batch update request
# ==============================================
requests = []

# 1. Voltage Level dropdown (A10)
row, col = a1_to_grid('A10')
voltage_options = [
    "LV (<1kV)",
    "LV sub (<1kV)",
    "HV (6.6-33kV)",
    "EHV (33-132kV)",
    "132kV Transmission"
]

requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_gid,
            "startRowIndex": row,
            "endRowIndex": row + 1,
            "startColumnIndex": col,
            "endColumnIndex": col + 1
        },
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in voltage_options]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
})

# 2. Profile Class dropdown (E10)
row, col = a1_to_grid('E10')
profile_classes = [
    "00 (Half-Hourly)",
    "01 (Domestic Unrestricted)",
    "02 (Domestic Economy 7)",
    "03 (Non-Domestic Unrestricted)",
    "04 (Non-Domestic Economy 7)",
    "05 (Non-Domestic Maximum Demand)",
    "06 (Non-Domestic Two-Rate)",
    "07 (Seasonal Time of Day)",
    "08 (Seasonal)"
]

requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_gid,
            "startRowIndex": row,
            "endRowIndex": row + 1,
            "startColumnIndex": col,
            "endColumnIndex": col + 1
        },
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in profile_classes]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
})

# 3. Meter Registration dropdown (F10)
row, col = a1_to_grid('F10')
meter_types = [
    "800 (NHH Non-Settlement)",
    "801 (HH Metered)",
    "802 (NHH Metered - Unmetered Supplies)",
    "H (HH Metered - Demand)",
    "M (NHH - Manually Read)",
    "C (NHH - Check Metering)",
    "P (NHH - Prepayment)"
]

requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_gid,
            "startRowIndex": row,
            "endRowIndex": row + 1,
            "startColumnIndex": col,
            "endColumnIndex": col + 1
        },
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in meter_types]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
})

# 4. DUoS Charging Class dropdown (H10)
row, col = a1_to_grid('H10')
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

requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_gid,
            "startRowIndex": row,
            "endRowIndex": row + 1,
            "startColumnIndex": col,
            "endColumnIndex": col + 1
        },
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in duos_classes]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
})

# 5. DNO Distributor dropdown (B6)
row, col = a1_to_grid('B6')
requests.append({
    "setDataValidation": {
        "range": {
            "sheetId": sheet_gid,
            "startRowIndex": row,
            "endRowIndex": row + 1,
            "startColumnIndex": col,
            "endColumnIndex": col + 1
        },
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in dno_options]
            },
            "showCustomUi": True,
            "strict": False  # Allow manual MPAN input
        }
    }
})

# 6. Number validation for kW fields (B17:B19)
for cell_ref in ['B17', 'B18', 'B19']:
    row, col = a1_to_grid(cell_ref)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_gid,
                "startRowIndex": row,
                "endRowIndex": row + 1,
                "startColumnIndex": col,
                "endColumnIndex": col + 1
            },
            "rule": {
                "condition": {
                    "type": "NUMBER_GREATER",
                    "values": [{"userEnteredValue": "0"}]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    })

# 7. Currency formatting for rate cells (B10:D10)
for cell_ref in ['B10', 'C10', 'D10']:
    row, col = a1_to_grid(cell_ref)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_gid,
                "startRowIndex": row,
                "endRowIndex": row + 1,
                "startColumnIndex": col,
                "endColumnIndex": col + 1
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "0.000\" p/kWh\""
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    })

# ==============================================
# Execute batch update
# ==============================================
print(f"\n🚀 Applying {len(requests)} validation rules...")

body = {"requests": requests}
sh.batch_update(body)

print("   ✅ All validation rules applied")

# ==============================================
# Add help notes
# ==============================================
print("\n💬 Adding help notes...")

postcode_note = """UK Postcode Format:
Examples: SW1A 1AA, M1 1AE, B33 8TH

System will auto-lookup:
• DNO distributor
• GSP Group
• Regional network info"""

mpan_note = """MPAN Format:
• 13-digit core MPAN
• Or 21-digit full MPAN
• First 2 digits = DNO ID (10-23)

Examples:
• 14055667788 (core)
• 00 800 999 932 14055667788 (full)

System extracts core and validates DNO"""

bess_sheet.update_note('A6', postcode_note)
bess_sheet.update_note('B6', mpan_note)

print("   ✅ Help notes added")

# ==============================================
# SUMMARY
# ==============================================
print("\n" + "="*60)
print("✅ DROPDOWNS & VALIDATION COMPLETE")
print("="*60)
print("\n📋 Added dropdowns:")
print("   • A10: Voltage Level (5 options)")
print(f"   • B6: DNO Distributor ({len(dno_options)} options from BigQuery)")
print(f"   • E10: Profile Class ({len(profile_classes)} options)")
print(f"   • F10: Meter Registration ({len(meter_types)} options)")
print(f"   • H10: DUoS Charging Class ({len(duos_classes)} options)")
print("\n🔢 Added validation:")
print("   • B17-B19: Number validation (kW > 0)")
print("\n💬 Added help notes:")
print("   • A6: Postcode format guide")
print("   • B6: MPAN format guide")
print("\n🎨 Added formatting:")
print("   • B10-D10: Currency format (p/kWh)")
print("\n🔄 Test the dropdowns by clicking on the cells in the BESS sheet!")
print("="*60)
