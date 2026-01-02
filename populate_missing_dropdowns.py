#!/usr/bin/env python3
"""
Populate Missing Dropdown Data (Capacity Range, Connection Site, Project Status)
"""

from googleapiclient.discovery import build
from google.cloud import bigquery
from google.oauth2 import service_account

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = "inner-cinema-credentials.json"

# Initialize clients
bq_client = bigquery.Client(project=PROJECT_ID, location="US")
sheets_creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets_service = build('sheets', 'v4', credentials=sheets_creds)

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 POPULATING MISSING DROPDOWN DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# ============================================================================
# 1. CAPACITY RANGES
# ============================================================================
print("\n⚡ Creating Capacity Ranges...")
capacity_ranges = [
    'None',
    'All',
    'Micro (<1 MW)',
    'Small (1-10 MW)',
    'Medium (10-50 MW)',
    'Large (50-100 MW)',
    'Very Large (100-500 MW)',
    'Mega (>500 MW)'
]
print(f"   ✅ Defined {len(capacity_ranges)-2} capacity ranges")

# ============================================================================
# 2. CONNECTION SITES (use power station names as proxy)
# ============================================================================
print("\n🔌 Fetching Connection Sites from BigQuery...")
query = """
SELECT DISTINCT bmu_name
FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators`
WHERE is_active = TRUE
AND bmu_name IS NOT NULL
AND generation_capacity_mw > 10  -- Only larger units
ORDER BY bmu_name
LIMIT 100
"""
df = bq_client.query(query).to_dataframe()
connection_sites = ['None', 'All'] + df['bmu_name'].tolist()
print(f"   ✅ Retrieved {len(connection_sites)-2} connection sites (BMU names)")

# ============================================================================
# 3. PROJECT STATUS
# ============================================================================
print("\n📋 Creating Project Status options...")
project_status = [
    'None',
    'All',
    'Active/Operational',
    'Under Construction',
    'Planned/Consented',
    'Testing/Commissioning',
    'Decommissioned',
    'On Hold',
    'Cancelled'
]
print(f"   ✅ Defined {len(project_status)-2} status options")

# ============================================================================
# 4. WRITE TO DROPDOWNS SHEET
# ============================================================================
print("\n📝 Writing to Dropdowns sheet (columns K, L, M)...")

batch_data = [
    {
        'range': 'Dropdowns!K1',
        'values': [['Capacity Ranges']]
    },
    {
        'range': f'Dropdowns!K2:K{len(capacity_ranges)+1}',
        'values': [[cr] for cr in capacity_ranges]
    },
    {
        'range': 'Dropdowns!L1',
        'values': [['Connection Sites']]
    },
    {
        'range': f'Dropdowns!L2:L{len(connection_sites)+1}',
        'values': [[cs] for cs in connection_sites]
    },
    {
        'range': 'Dropdowns!M1',
        'values': [['Project Status']]
    },
    {
        'range': f'Dropdowns!M2:M{len(project_status)+1}',
        'values': [[ps] for ps in project_status]
    }
]

body = {
    'valueInputOption': 'USER_ENTERED',
    'data': batch_data
}

result = sheets_service.spreadsheets().values().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=body
).execute()

print(f"   ✅ Wrote {result.get('totalUpdatedCells', 0)} cells")

print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ MISSING DROPDOWN DATA POPULATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Added to Dropdowns sheet:
   • Column K: Capacity Ranges ({len(capacity_ranges)-2} ranges)
   • Column L: Connection Sites ({len(connection_sites)-2} sites)
   • Column M: Project Status ({len(project_status)-2} statuses)

✅ All search dropdown data is now complete!
   B8-B16 should now work properly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
