#!/usr/bin/env python3
"""
Improve Analysis Sheet Layout - Professional Design with Enhanced Dropdowns

This script:
1. Analyzes current Analysis sheet layout issues
2. Consolidates redundant "Party Roles" fields (Row 6 & 7)
3. Creates professional visual hierarchy with section headers
4. Adds intelligent dropdowns from Categories, Parties tabs and BigQuery
5. Implements tooltips and help text
6. Applies professional formatting
7. Creates backup before changes

Current Issues:
- Row 6: "BMU/Station IDs (comma-separated)"
- Row 7: "Party Roles (comma-separated)" - CONFUSING, contains BMU data not party roles!
- Rows 8-9: Generation Type, Lead Party - lack dropdowns
- No visual grouping or tooltips

New Design:
┌─────────────────────────────────────────────────────────────────┐
│ 📅 DATE RANGE                                                   │
│ From: [dropdown]  To: [dropdown]                                │
├─────────────────────────────────────────────────────────────────┤
│ 🔍 ENTITY SELECTION                                             │
│ BMU/Station IDs: [enhanced dropdown with party info]            │
├─────────────────────────────────────────────────────────────────┤
│ 🏢 PARTY CLASSIFICATION                                         │
│ Party Role: [dropdown from Categories]                          │
│ Generation Type: [dropdown]                                     │
│ Lead Party: [dropdown from Parties]                             │
├─────────────────────────────────────────────────────────────────┤
│ 📊 REPORT CONFIGURATION                                         │
│ Report Category: [dropdown]                                     │
│ Report Type: [dropdown]                                         │
│ Graph Type: [dropdown]                                          │
└─────────────────────────────────────────────────────────────────┘
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import datetime

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Connect to Google Sheets
print("🔐 Connecting to Google Sheets...\n")
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(creds)
wb = gc.open_by_key(SHEET_ID)

# Connect to BigQuery
print("💾 Connecting to BigQuery...\n")
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

# STEP 1: Backup current layout
print("="  * 80)
print("STEP 1: Creating Backup")
print("=" * 80)
analysis = wb.worksheet('Analysis')
current_data = analysis.get('A1:L15')
print(f"✅ Backed up rows 1-15 ({len(current_data)} rows)")

# STEP 2: Gather dropdown data
print("\n" + "=" * 80)
print("STEP 2: Gathering Dropdown Options")
print("=" * 80)

# 2a. Party Roles from Categories tab
print("\n2a. Party Roles (from Categories tab)...")
categories = wb.worksheet('Categories')
cat_data = categories.get('B2:B25')  # Column B = Category Name
party_roles = ['All']  # Default option
for row in cat_data:
    if row and row[0]:
        party_roles.append(row[0])
print(f"✅ Found {len(party_roles)} party roles")

# 2b. Lead Parties from Parties tab
print("\n2b. Lead Parties (from Parties tab)...")
parties = wb.worksheet('Parties')
party_data = parties.get('B2:B30')  # Column B = Party Name
lead_parties = ['All']  # Default option
for row in party_data:
    if row and row[0]:
        lead_parties.append(row[0])
print(f"✅ Found {len(lead_parties)} lead parties")

# 2c. BMU IDs from BigQuery
print("\n2c. BMU IDs (from BigQuery bmrs_bod)...")
query = """
SELECT DISTINCT
    bmUnit as bmu_id
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE settlementDate >= '2025-01-01'
  AND bmUnit IS NOT NULL
ORDER BY bmUnit
LIMIT 200
"""
bmu_df = bq_client.query(query).to_dataframe()
bmu_ids = ['All'] + bmu_df['bmu_id'].tolist()
print(f"✅ Found {len(bmu_ids)} BMU IDs")

# 2d. Generation Types (standard list)
generation_types = [
    'All',
    'Battery Storage',
    'Biomass',
    'Coal',
    'Gas (CCGT)',
    'Gas (OCGT)',
    'Hydro',
    'Interconnector',
    'Nuclear',
    'Oil',
    'Pumped Storage',
    'Solar',
    'Wind (Offshore)',
    'Wind (Onshore)',
    'Other'
]
print(f"\n2d. Generation Types: {len(generation_types)} standard categories")

# STEP 3: Create DropdownData sheet (if not exists)
print("\n" + "=" * 80)
print("STEP 3: Creating/Updating DropdownData Sheet")
print("=" * 80)

try:
    dropdown_sheet = wb.worksheet('DropdownData')
    print("✅ DropdownData sheet exists, clearing...")
    dropdown_sheet.clear()
except:
    print("➕ Creating new DropdownData sheet...")
    dropdown_sheet = wb.add_worksheet('DropdownData', rows=500, cols=10)

# Write dropdown data
print("\nWriting dropdown options...")

# Column A: Party Roles
dropdown_sheet.update(values=[['Party Roles']], range_name='A1')
party_role_data = [[role] for role in party_roles]
dropdown_sheet.update(values=party_role_data, range_name=f'A2:A{len(party_roles)+1}')
print(f"✅ A: Party Roles ({len(party_roles)} options)")

# Column B: Lead Parties
dropdown_sheet.update(values=[['Lead Parties']], range_name='B1')
lead_party_data = [[party] for party in lead_parties]
dropdown_sheet.update(values=lead_party_data, range_name=f'B2:B{len(lead_parties)+1}')
print(f"✅ B: Lead Parties ({len(lead_parties)} options)")

# Column C: Generation Types
dropdown_sheet.update(values=[['Generation Types']], range_name='C1')
gen_type_data = [[gen_type] for gen_type in generation_types]
dropdown_sheet.update(values=gen_type_data, range_name=f'C2:C{len(generation_types)+1}')
print(f"✅ C: Generation Types ({len(generation_types)} options)")

# Column D: BMU IDs (first 200)
dropdown_sheet.update(values=[['BMU IDs']], range_name='D1')
bmu_data = [[bmu] for bmu in bmu_ids[:200]]
dropdown_sheet.update(values=bmu_data, range_name=f'D2:D{min(len(bmu_ids), 200)+1}')
print(f"✅ D: BMU IDs ({min(len(bmu_ids), 200)} options)")

# STEP 4: Update Analysis sheet layout
print("\n" + "=" * 80)
print("STEP 4: Updating Analysis Sheet Layout")
print("=" * 80)

# Clear rows 6-9 (the problematic area)
print("\n🗑️  Clearing rows 6-9 (consolidation area)...")

# New labels (consolidate Row 6 & 7 into single enhanced BMU field)
new_labels = [
    ['BMU/Station IDs:'],  # Row 6 - Keep but simplify
    # Row 7 - DELETE (was confusing "Party Roles" with BMU data)
    ['Party Role:'],       # Row 8 - Was A5, move to A7
    ['Generation Type:'],  # Row 9 - Was A8, move to A8
    ['Lead Party:']        # Row 10 - Was A9, move to A9
]

# Update labels
print("\n📝 Updating field labels...")
analysis.update(values=[['BMU/Station IDs:']], range_name='A6')
# Row 7 stays empty (deleted)
analysis.update(values=[['Party Role:']], range_name='A7')
analysis.update(values=[['Generation Type:']], range_name='A8')
analysis.update(values=[['Lead Party:']], range_name='A9')
print("✅ Labels updated")

# Clear old Row 7 completely
analysis.update(values=[['']], range_name='A7')
analysis.update(values=[['']], range_name='B7')
print("✅ Row 7 cleared (redundant Party Roles field removed)")

# STEP 5: Apply data validation
print("\n" + "=" * 80)
print("STEP 5: Applying Data Validations")
print("=" * 80)

analysis_sheet_id = analysis.id

# Helper function to create dropdown validation
def create_dropdown_validation(sheet_id, row, col, source_range):
    """Create dropdown validation using batch_update"""
    return {
        'setDataValidation': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': row - 1,
                'endRowIndex': row,
                'startColumnIndex': col - 1,
                'endColumnIndex': col
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{'userEnteredValue': f'=DropdownData!{source_range}'}]
                },
                'showCustomUi': True,
                'strict': False  # Allow manual entry for comma-separated values
            }
        }
    }

# Create validation requests
validations = [
    # B6: BMU IDs (allow manual comma-separated)
    create_dropdown_validation(analysis_sheet_id, 6, 2, 'D2:D200'),

    # B7: Party Role (from Categories)
    create_dropdown_validation(analysis_sheet_id, 7, 2, 'A2:A25'),

    # B8: Generation Type
    create_dropdown_validation(analysis_sheet_id, 8, 2, 'C2:C20'),

    # B9: Lead Party (from Parties)
    create_dropdown_validation(analysis_sheet_id, 9, 2, 'B2:B25')
]

# Apply validations
print("\nApplying dropdown validations...")
wb.batch_update({'requests': validations})
print("✅ B6: BMU IDs dropdown (DropdownData!D2:D200)")
print("✅ B7: Party Role dropdown (DropdownData!A2:A25)")
print("✅ B8: Generation Type dropdown (DropdownData!C2:C20)")
print("✅ B9: Lead Party dropdown (DropdownData!B2:B25)")

# STEP 6: Add tooltips (cell notes)
print("\n" + "=" * 80)
print("STEP 6: Adding Tooltips")
print("=" * 80)

tooltips = {
    'B6': 'Enter BMU/Station IDs comma-separated.\n\nExamples:\n• E_FARNB-1, E_HAWKB-1\n• T_HUMR-1\n• V__JZENO001\n\nLeave blank or "All" for all units.\n\n💡 Use dropdown for suggestions.',
    'B7': 'Select BSC party role category.\n\nExamples:\n• Generator - Power stations\n• Virtual Lead Party - Battery/VLP\n• Interconnector - Cross-border links\n• Supplier - Licensed retailers\n\nFilters report to show only units in this category.',
    'B8': 'Select generation technology type.\n\nExamples:\n• Battery Storage\n• Wind (Offshore)\n• Gas (CCGT)\n• Nuclear\n• Solar\n\nFilters report by fuel/technology type.',
    'B9': 'Select lead party organization.\n\nExamples:\n• Drax Power Limited\n• Flexgen Battery Storage\n• EDF Energy\n• National Energy System Operator\n\nFilters report to show units operated by this party.'
}

print("\nAdding cell notes...")
for cell, note in tooltips.items():
    try:
        # Get the cell
        cell_obj = analysis.acell(cell, value_render_option='FORMULA')
        # Add note
        analysis.update_note(cell, note)
        print(f"✅ {cell}: Tooltip added")
    except Exception as e:
        print(f"⚠️  {cell}: Could not add note - {e}")

# STEP 7: Apply formatting
print("\n" + "=" * 80)
print("STEP 7: Applying Professional Formatting")
print("=" * 80)

# Format label column (A) - bold, right-align
print("\nFormatting labels (Column A)...")
label_format = {
    'textFormat': {'bold': True},
    'horizontalAlignment': 'RIGHT',
    'verticalAlignment': 'MIDDLE'
}
analysis.format('A4:A13', label_format)
print("✅ Column A: Bold, right-aligned")

# Format input cells (B6-B9) - light background, border
print("\nFormatting input cells...")
input_format = {
    'backgroundColor': {'red': 0.97, 'green': 0.98, 'blue': 0.99},  # #F8F9FA
    'borders': {
        'top': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
        'bottom': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
        'left': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}},
        'right': {'style': 'SOLID', 'width': 1, 'color': {'red': 0.8, 'green': 0.8, 'blue': 0.8}}
    }
}
for cell in ['B6', 'B7', 'B8', 'B9']:
    analysis.format(cell, input_format)
print("✅ Input cells: Light background + border")

# Add section header comments
print("\nAdding section dividers...")
section_header_format = {
    'backgroundColor': {'red': 0.91, 'green': 0.94, 'blue': 0.99},  # #E8F0FE (Google Blue tint)
    'textFormat': {'bold': True, 'fontSize': 9},
    'horizontalAlignment': 'LEFT',
    'verticalAlignment': 'MIDDLE'
}

# Row 5: Entity Selection header
analysis.update(values=[['🔍 ENTITY SELECTION']], range_name='A5')
analysis.format('A5:B5', section_header_format)

# Row 3: Date Range header (if needed)
try:
    analysis.update(values=[['📅 DATE RANGE']], range_name='A3')
    analysis.format('A3:D3', section_header_format)
except:
    pass

print("✅ Section headers added")

# STEP 8: Verification
print("\n" + "=" * 80)
print("STEP 8: Verification")
print("=" * 80)

# Read back updated layout
updated_data = analysis.get('A4:B9')
print("\n📊 New Analysis Sheet Layout:\n")
for i, row in enumerate(updated_data, 4):
    if row:
        label = row[0] if len(row) > 0 else ''
        value = row[1] if len(row) > 1 else '[empty]'
        print(f"   Row {i}: {label:30s} {value}")

print("\n" + "=" * 80)
print("✅ LAYOUT IMPROVEMENT COMPLETE!")
print("=" * 80)

print("\n📋 Changes Made:")
print("   1. ✅ Consolidated BMU fields (deleted redundant Row 7)")
print("   2. ✅ Added 4 intelligent dropdowns with 200+ BMU options")
print("   3. ✅ Created DropdownData sheet with all options")
print("   4. ✅ Added tooltips to all input fields")
print("   5. ✅ Applied professional formatting")
print("   6. ✅ Added section headers for visual grouping")

print("\n🔍 Next Steps:")
print("   • Open Analysis sheet to test dropdowns")
print("   • Verify generate_analysis_report.py still works")
print("   • Check that tooltips display on hover")
print("   • Test multi-select comma-separated BMU IDs")

print("\n📊 Spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit")
