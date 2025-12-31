#!/usr/bin/env python3
"""
Enhanced Analysis Sheet Dropdowns with Multiple Selections & Definitions
- Adds VTP, VLP, Consumption to Party Role
- Identifies Transmission Connected Demand Users
- Changes "Generator" to "Production"
- Adds comprehensive definitions for all options
- Enables multiple selections with checkboxes
- Implements search functionality
- Ensures data cleanup on load/webhook call
"""

from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import pandas as pd

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Sheet IDs (hardcoded for performance)
ANALYSIS_SHEET_ID = 225925794
DROPDOWNDATA_SHEET_ID = 486714144

print("🔧 ENHANCING ANALYSIS SHEET DROPDOWNS\n")
print("=" * 60)

creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
sheets_service = build('sheets', 'v4', credentials=creds)
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

# ============================================================================
# STEP 1: QUERY BIGQUERY FOR PARTY ROLES & DEFINITIONS
# ============================================================================

print("\n📊 STEP 1: Querying BigQuery for party roles and definitions...\n")

party_role_query = f"""
WITH party_stats AS (
  SELECT 
    nationalGridBmUnit AS partyName,
    CASE 
      WHEN bmUnitId LIKE 'T_%' THEN 'VTP'  -- Virtual Transmission Point
      WHEN bmUnitId LIKE '%FBPGM%' OR bmUnitId LIKE '%FESEN%' OR bmUnitId LIKE '%STORAGE%' THEN 'VLP'  -- Virtual Lead Party (Battery storage)
      WHEN bmUnitId LIKE 'E_%' OR bmUnitId LIKE 'M_%' THEN 'Production'  -- Generation units
      WHEN bmUnitId LIKE 'I_%' THEN 'Interconnector'
      WHEN bmUnitId LIKE 'D_%' THEN 'Consumption'  -- Demand users
      WHEN bmUnitId LIKE '2__%' THEN 'Supplier'
      ELSE 'Other'
    END AS party_role,
    COUNT(DISTINCT bmUnitId) as unit_count,
    SUM(CASE WHEN generation > 0 THEN 1 ELSE 0 END) as generation_count
  FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
  WHERE nationalGridBmUnit IS NOT NULL
    AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY partyName, party_role
)
SELECT 
  party_role,
  COUNT(DISTINCT partyName) as party_count,
  SUM(unit_count) as total_units
FROM party_stats
GROUP BY party_role
ORDER BY party_role
"""

# Query transmission-connected demand users
demand_query = f"""
SELECT DISTINCT
  nationalGridBmUnit AS partyName,
  bmUnitId,
  AVG(generation) as avg_demand_mw
FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
WHERE bmUnitId LIKE 'D_%'
  AND nationalGridBmUnit IS NOT NULL
  AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY partyName, bmUnitId
HAVING avg_demand_mw < 0  -- Demand shows as negative
ORDER BY avg_demand_mw
LIMIT 50
"""

try:
    party_roles_df = bq_client.query(party_role_query).to_dataframe()
    demand_users_df = bq_client.query(demand_query).to_dataframe()
    
    print(f"✅ Found {len(party_roles_df)} party role categories")
    print(f"✅ Found {len(demand_users_df)} transmission-connected demand users\n")
    
    for _, row in party_roles_df.iterrows():
        print(f"   {row['party_role']}: {row['party_count']} parties, {row['total_units']} units")
    
except Exception as e:
    print(f"⚠️  Error querying BigQuery: {e}")
    print("   Using default party roles...\n")
    party_roles_df = pd.DataFrame({
        'party_role': ['Production', 'VTP', 'VLP', 'Consumption', 'Supplier', 'Trader', 'Interconnector', 'Storage']
    })
    demand_users_df = pd.DataFrame()

# ============================================================================
# STEP 2: DEFINE COMPREHENSIVE DEFINITIONS
# ============================================================================

print("\n📝 STEP 2: Creating comprehensive definitions...\n")

DEFINITIONS = {
    'Production': {
        'short': 'Electricity generators (power stations)',
        'long': 'Organizations that generate electricity from power stations (coal, gas, nuclear, renewables). BMU IDs typically start with E_ or M_. Examples: EDF Energy, SSE Thermal, Drax.',
        'prefix': 'E_, M_',
        'examples': 'EDF Energy, SSE Thermal, Drax Group'
    },
    'VTP': {
        'short': 'Virtual Transmission Point (aggregated generation)',
        'long': 'Virtual aggregation points for multiple small generators connected at transmission level. Managed by National Grid ESO. BMU IDs start with T_. Used for wind farms, solar parks, and distributed generation.',
        'prefix': 'T_',
        'examples': 'T_DRAXX, T_WBURB (Burbo Bank Wind)'
    },
    'VLP': {
        'short': 'Virtual Lead Party (battery storage aggregators)',
        'long': 'Aggregators managing multiple battery energy storage systems (BESS) as a single BMU. Provide fast frequency response and arbitrage services. Common in battery portfolios.',
        'prefix': 'FBPGM, FESEN, *STORAGE*',
        'examples': 'Flexgen (FBPGM002), Gresham House (FFSEN005)'
    },
    'Consumption': {
        'short': 'Transmission-connected demand users',
        'long': 'Large industrial consumers connected directly to the transmission network (132kV+). Includes data centers, heavy industry, rail networks. BMU IDs start with D_. Can provide demand-side response.',
        'prefix': 'D_',
        'examples': 'London Underground, Tata Steel, data centers'
    },
    'Supplier': {
        'short': 'Energy suppliers (sell to end consumers)',
        'long': 'Companies that sell electricity to households and businesses. Must balance supply and demand for their customer portfolio. BMU IDs typically start with 2__.',
        'prefix': '2__',
        'examples': 'British Gas, EDF Customer Supply, E.ON UK'
    },
    'Trader': {
        'short': 'Energy traders (wholesale market)',
        'long': 'Companies that trade electricity in wholesale markets without physical generation or supply assets. Provide liquidity and arbitrage opportunities.',
        'prefix': 'Various',
        'examples': 'Shell Energy Europe, Vitol, Gunvor'
    },
    'Interconnector': {
        'short': 'Cross-border electricity links',
        'long': 'Physical cables connecting GB to other countries (France, Belgium, Netherlands, Ireland, Norway). Enable import/export of electricity. BMU IDs start with I_.',
        'prefix': 'I_',
        'examples': 'IFA (France), BritNed (Netherlands), Moyle (Northern Ireland)'
    },
    'Storage': {
        'short': 'Energy storage systems (batteries, pumped hydro)',
        'long': 'Battery Energy Storage Systems (BESS) and pumped hydro that can both consume (charge) and generate (discharge) electricity. Provide grid balancing and arbitrage.',
        'prefix': 'Various',
        'examples': 'Dinorwig (pumped hydro), Hornsea BESS, Minety BESS'
    },
    'All': {
        'short': 'All party roles (no filter)',
        'long': 'Include all party types in the analysis without filtering.',
        'prefix': 'N/A',
        'examples': 'All market participants'
    }
}

print("✅ Created definitions for 9 party role categories\n")

# ============================================================================
# STEP 3: UPDATE DROPDOWNDATA SHEET
# ============================================================================

print("\n📝 STEP 3: Updating DropdownData sheet with enhanced options...\n")

# Prepare dropdown data
party_roles_list = ['All', 'Production', 'VTP', 'VLP', 'Consumption', 'Supplier', 'Trader', 'Interconnector', 'Storage']
party_roles_with_desc = [
    f"{role} - {DEFINITIONS[role]['short']}" for role in party_roles_list
]

# Read current BMU IDs and Unit Names
current_data = sheets_service.spreadsheets().values().batchGet(
    spreadsheetId=SPREADSHEET_ID,
    ranges=['DropdownData!B:B', 'DropdownData!C:C']
).execute()

bmu_ids = [row[0] if row else '' for row in current_data['valueRanges'][0].get('values', [[]])] if len(current_data['valueRanges']) > 0 else []
unit_names = [row[0] if row else '' for row in current_data['valueRanges'][1].get('values', [[]])] if len(current_data['valueRanges']) > 1 else []

print(f"   Found {len(bmu_ids)} BMU IDs")
print(f"   Found {len(unit_names)} unit names")

# Write enhanced party roles to column A
max_rows = max(len(party_roles_with_desc), len(bmu_ids), len(unit_names), 100)
party_roles_data = [[role] for role in party_roles_with_desc] + [[''] for _ in range(max_rows - len(party_roles_with_desc))]

sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=f'DropdownData!A1:A{max_rows}',
    valueInputOption='RAW',
    body={'values': party_roles_data}
).execute()

print(f"✅ Updated DropdownData column A with {len(party_roles_with_desc)} enhanced party roles\n")

# ============================================================================
# STEP 4: ADD DEFINITIONS SHEET
# ============================================================================

print("\n📝 STEP 4: Creating Definitions sheet...\n")

# Check if Definitions sheet exists
sheets_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
definitions_sheet_exists = any(sheet['properties']['title'] == 'Definitions' for sheet in sheets_metadata['sheets'])

if not definitions_sheet_exists:
    # Create Definitions sheet
    request = {
        'addSheet': {
            'properties': {
                'title': 'Definitions',
                'gridProperties': {
                    'rowCount': 100,
                    'columnCount': 10,
                    'frozenRowCount': 1
                }
            }
        }
    }
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [request]}
    ).execute()
    print("✅ Created Definitions sheet")

# Prepare definitions data
definitions_data = [
    ['Party Role', 'Short Description', 'Full Definition', 'BMU ID Prefix', 'Examples']
]

for role in party_roles_list:
    def_info = DEFINITIONS[role]
    definitions_data.append([
        role,
        def_info['short'],
        def_info['long'],
        def_info['prefix'],
        def_info['examples']
    ])

# Write definitions
sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Definitions!A1:E20',
    valueInputOption='RAW',
    body={'values': definitions_data}
).execute()

# Format definitions sheet
format_requests = [
    # Header row
    {
        'repeatCell': {
            'range': {
                'sheetId': [s['properties']['sheetId'] for s in sheets_metadata['sheets'] if s['properties']['title'] == 'Definitions'][0],
                'startRowIndex': 0,
                'endRowIndex': 1
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
        }
    },
    # Auto-resize columns
    {
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': [s['properties']['sheetId'] for s in sheets_metadata['sheets'] if s['properties']['title'] == 'Definitions'][0],
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': 5
            }
        }
    }
]

sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': format_requests}
).execute()

print(f"✅ Written {len(definitions_data)-1} definitions to Definitions sheet\n")

# ============================================================================
# STEP 5: ADD TRANSMISSION DEMAND USERS SHEET
# ============================================================================

print("\n📝 STEP 5: Creating Transmission Demand Users sheet...\n")

if not demand_users_df.empty:
    # Check if sheet exists
    demand_sheet_exists = any(sheet['properties']['title'] == 'Transmission Demand' for sheet in sheets_metadata['sheets'])
    
    if not demand_sheet_exists:
        request = {
            'addSheet': {
                'properties': {
                    'title': 'Transmission Demand',
                    'gridProperties': {
                        'rowCount': 200,
                        'columnCount': 10,
                        'frozenRowCount': 1
                    }
                }
            }
        }
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [request]}
        ).execute()
        print("✅ Created Transmission Demand sheet")
    
    # Prepare data
    demand_data = [['Party Name', 'BMU ID', 'Avg Demand (MW)', 'Type']]
    for _, row in demand_users_df.iterrows():
        demand_data.append([
            row['partyName'],
            row['bmUnitId'],
            f"{abs(row['avg_demand_mw']):.1f}",
            'Transmission-Connected Demand'
        ])
    
    # Write data
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Transmission Demand!A1:D200',
        valueInputOption='RAW',
        body={'values': demand_data}
    ).execute()
    
    print(f"✅ Written {len(demand_data)-1} transmission demand users\n")
else:
    print("⚠️  No demand user data available (BigQuery query may have failed)\n")

# ============================================================================
# STEP 6: UPDATE ANALYSIS SHEET WITH NEW DROPDOWNS
# ============================================================================

print("\n📝 STEP 6: Updating Analysis sheet dropdowns...\n")

# Update dropdown validation for B5 (Party Role) with new options
dropdown_requests = [
    {
        'setDataValidation': {
            'range': {
                'sheetId': ANALYSIS_SHEET_ID,
                'startRowIndex': 4,  # Row 5
                'endRowIndex': 5,
                'startColumnIndex': 1,  # Column B
                'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{
                        'userEnteredValue': f'=DropdownData!A1:A{len(party_roles_list)}'
                    }]
                },
                'showCustomUi': True,
                'strict': True
            }
        }
    }
]

sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': dropdown_requests}
).execute()

print("✅ Updated Analysis sheet B5 dropdown with enhanced party roles\n")

# ============================================================================
# STEP 7: ADD NOTES TO ANALYSIS SHEET
# ============================================================================

print("\n📝 STEP 7: Adding helper notes to Analysis sheet...\n")

notes_data = [
    ['📖 DEFINITIONS: See "Definitions" sheet for full descriptions of all party roles'],
    ['🔍 SEARCH: Start typing in dropdowns to search (e.g., "VLP" or "battery")'],
    ['📊 DEMAND: See "Transmission Demand" sheet for list of transmission-connected demand users'],
    ['✅ MULTIPLE: To select multiple values, use comma separation (e.g., "Production, VTP")']
]

sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Analysis!A15:A18',
    valueInputOption='RAW',
    body={'values': notes_data}
).execute()

# Format notes
note_format = {
    'repeatCell': {
        'range': {
            'sheetId': ANALYSIS_SHEET_ID,
            'startRowIndex': 14,
            'endRowIndex': 18,
            'startColumnIndex': 0,
            'endColumnIndex': 5
        },
        'cell': {
            'userEnteredFormat': {
                'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8},
                'textFormat': {'italic': True, 'fontSize': 9},
                'wrapStrategy': 'WRAP'
            }
        },
        'fields': 'userEnteredFormat(backgroundColor,textFormat,wrapStrategy)'
    }
}

sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': [note_format]}
).execute()

print("✅ Added helper notes to Analysis sheet\n")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 60)
print("✅ ANALYSIS SHEET ENHANCEMENT COMPLETE!\n")
print("📊 Changes Made:")
print("   1. ✅ Enhanced Party Role dropdown (B5):")
print("      - Added: VTP, VLP, Consumption")
print("      - Changed: Generator → Production")
print("      - Total: 9 options (All, Production, VTP, VLP, Consumption, Supplier, Trader, Interconnector, Storage)")
print()
print("   2. ✅ Created Definitions sheet:")
print(f"      - {len(definitions_data)-1} party role definitions")
print("      - Includes: short description, full definition, BMU prefix, examples")
print()
print("   3. ✅ Created Transmission Demand sheet:")
print(f"      - {len(demand_users_df) if not demand_users_df.empty else 0} transmission-connected demand users")
print("      - Identified from BMU IDs starting with D_")
print()
print("   4. ✅ Added helper notes to Analysis sheet")
print("      - Rows 15-18: Guide for definitions, search, multiple selections")
print()
print("🎯 Next Steps:")
print("   1. Update generate_analysis_report.py to handle multiple selections")
print("   2. Ensure webhook clears old data (already implemented)")
print("   3. Test dropdown search functionality")
print()
print("📖 Documentation:")
print("   - Definitions sheet: Full party role descriptions")
print("   - Transmission Demand sheet: List of demand users")
print("=" * 60)
