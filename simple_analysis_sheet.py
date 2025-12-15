#!/usr/bin/env python3
"""
Simplified Analysis Sheet - Works with existing schemas
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis'
PROJECT_ID = 'inner-cinema-476211-u9'

print("=" * 70)
print("📊 SIMPLE ANALYSIS SHEET SETUP")
print("=" * 70)
print()

# Step 1: Check what views we have
print("Step 1: Checking existing views...")
client = bigquery.Client(project=PROJECT_ID)

# Only use bmrs_fuelinst_unified (the one that works)
print("✅ Using bmrs_fuelinst_unified (generation data)")
print()

# Step 2: Create minimal Analysis sheet
print("Step 2: Creating Analysis sheet...")

with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

try:
    sheet = spreadsheet.worksheet(SHEET_NAME)
    print(f"Sheet '{SHEET_NAME}' exists, clearing it...")
    sheet.clear()
except gspread.exceptions.WorksheetNotFound:
    print(f"Creating new sheet: {SHEET_NAME}")
    sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=100, cols=10)

print("✅ Sheet ready")
print()

# Step 3: Add basic structure
print("Step 3: Adding basic structure...")

# Header
updates = [
    ('A1', 'ANALYSIS DASHBOARD - Historical + Real-Time Data'),
    ('A3', '📊 GENERATION ANALYSIS'),
    ('A4', 'Data Source: bmrs_fuelinst + bmrs_fuelinst_iris'),
    ('A6', 'Date Range:'),
    ('B6', '1 Month'),
    ('A7', 'From:'),
    ('B7', (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y')),
    ('A8', 'To:'),
    ('B8', datetime.now().strftime('%d/%m/%Y')),
    ('A10', 'KEY METRICS:'),
    ('A12', '📋 RAW DATA'),
]

for cell, value in updates:
    sheet.update_acell(cell, value)

print("✅ Basic structure added")
print()

# Step 4: Query and populate data
print("Step 4: Querying generation data...")

query = f"""
SELECT 
    timestamp,
    fuelType,
    generation,
    source,
    settlementDate,
    settlementPeriod
FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_unified`
WHERE timestamp >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
ORDER BY timestamp DESC
LIMIT 100
"""

results = list(client.query(query).result())
print(f"✅ Retrieved {len(results)} records")
print()

# Step 5: Write data table
print("Step 5: Writing data to sheet...")

# Headers and data combined
table_data = [['Timestamp', 'Fuel Type', 'Generation (MW)', 'Source', 'Date', 'Period']]

for row in results[:50]:  # Limit to 50 to avoid quota
    table_data.append([
        row.timestamp.strftime('%d/%m/%y %H:%M') if row.timestamp else '',
        row.fuelType or '',
        f"{row.generation:.0f}" if row.generation else '',
        row.source or '',
        row.settlementDate.strftime('%d/%m/%y') if row.settlementDate else '',
        f"SP{row.settlementPeriod}" if row.settlementPeriod else ''
    ])

# Write in one batch
sheet.update(values=table_data, range_name='A14:F64')
print(f"✅ Wrote {len(table_data)-1} rows")
print()

# Calculate summary stats
print("Step 6: Adding summary statistics...")
total_gen = sum(row.generation for row in results if row.generation)
fuel_types = set(row.fuelType for row in results if row.fuelType)

sheet.update_acell('A11', f"Total Generation (7 days): {total_gen/1000:.0f} GWh")
sheet.update_acell('A13', f"Fuel Types: {', '.join(sorted(fuel_types))}")
print("✅ Summary added")
print()

print("=" * 70)
print("✅ ANALYSIS SHEET CREATED!")
print("=" * 70)
print()
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("📊 What's included:")
print("  • Last 7 days of generation data")
print("  • 50 rows displayed")
print("  • Combines historical + IRIS real-time data")
print()
print("💡 To update with latest data, run this script again")
print()
