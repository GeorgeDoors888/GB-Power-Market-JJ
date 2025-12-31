#!/usr/bin/env python3
"""
Export DNO Constraint Costs for Google Geo Chart
Creates CORRECT 2-column format: Region Name | Total Cost (£M)

Google Geo Chart Requirements:
- Column 1: Region name (e.g., "England" or UK region names)
- Column 2: Numeric value (total cost)
- NO additional columns in the data range
"""

from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Setup
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

creds = service_account.Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets_service = build('sheets', 'v4', credentials=creds)

print("🗺️ Fetching DNO constraint costs from BigQuery...")

# Query: Aggregate costs by DNO region (sum all months)
query = f"""
SELECT
    area_name,
    ROUND(SUM(allocated_total_cost) / 1000000, 2) as total_cost_millions
FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`
GROUP BY area_name
ORDER BY total_cost_millions DESC
"""

df = bq_client.query(query).to_dataframe()
print(f"✅ Retrieved {len(df)} DNO regions")

# Prepare data for Google Sheets (2-column format)
data = [['DNO Region', 'Cost (£M)']]  # Header
for _, row in df.iterrows():
    data.append([row['area_name'], row['total_cost_millions']])

print(f"\n📊 Data Preview:")
for row in data[:5]:
    print(f"  {row}")

# Export to Google Sheets - Use existing 'Constraint Map Data' tab
print(f"\n📤 Exporting to Google Sheets tab 'Constraint Map Data'...")

# Clear and update (use existing sheet)
try:
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range='Constraint Map Data!A1:Z1000'
    ).execute()
except Exception as e:
    print(f"⚠️ Note: {e}")
    print("Continuing with update...")

sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range='Constraint Map Data!A1',
    valueInputOption='USER_ENTERED',
    body={'values': data}
).execute()

print(f"\n✅ DONE! Data exported to 'Constraint Map Data' tab")
print(f"\n📍 CREATE GEO CHART:")
print(f"1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print(f"2. Go to 'Constraint Map Data' tab")
print(f"3. Select cells A1:B{len(data)} (ONLY 2 columns!)")
print(f"4. Insert → Chart")
print(f"5. Chart type → Geo chart")
print(f"6. Customize → Region: United Kingdom")
print(f"7. Customize → Display mode: Regions (NOT Markers!)")
print(f"\n⚠️ IMPORTANT: Select ONLY A1:B{len(data)} - Do NOT include column C or beyond!")
print(f"\n💡 The 'uja '2' error means you selected too many columns.")
print(f"   Google Geo Chart requires EXACTLY 2 columns: Region Name | Value")

print(f"\n📊 Total Constraint Costs:")
print(f"   UK Total: £{df['total_cost_millions'].sum():,.2f}M")
print(f"   Most Expensive: {df.iloc[0]['area_name']} (£{df.iloc[0]['total_cost_millions']:,.2f}M)")
print(f"   Least Expensive: {df.iloc[-1]['area_name']} (£{df.iloc[-1]['total_cost_millions']:,.2f}M)")
