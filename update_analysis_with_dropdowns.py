#!/usr/bin/env python3
"""
Update Analysis Sheet based on dropdown selections
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Analysis'
PROJECT_ID = 'inner-cinema-476211-u9'

print("=" * 70)
print("🔄 UPDATING ANALYSIS SHEET")
print("=" * 70)
print()

# Connect
print("Connecting...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)
client = bigquery.Client(project=PROJECT_ID)

print("✅ Connected")
print()

# Read dropdown selection
print("Reading user selections...")
quick_select = sheet.acell('C6').value
print(f"  Date Range: {quick_select}")

# Convert to days
range_map = {
    '24 Hours': 1,
    '1 Week': 7,
    '1 Month': 30,
    '3 Months': 90,
    '6 Months': 180,
    '1 Year': 365,
    '2 Years': 730,
    'Custom': None  # Will use from/to dates
}

if quick_select == 'Custom':
    # Read custom dates
    from_date = sheet.acell('H7').value
    to_date = sheet.acell('H8').value
    print(f"  Custom Range: {from_date} to {to_date}")
    
    # Parse dates
    try:
        start_date = datetime.strptime(from_date, '%d/%m/%Y')
        end_date = datetime.strptime(to_date, '%d/%m/%Y')
        days = (end_date - start_date).days
        print(f"  Calculated: {days} days")
    except:
        print("  ⚠️ Invalid custom dates, using 7 days")
        days = 7
else:
    days = range_map.get(quick_select, 7)
    print(f"  Days to query: {days}")

print()

# Query data
print(f"Querying generation data ({days} days)...")
query = f"""
SELECT 
    timestamp,
    fuelType,
    generation,
    source,
    settlementDate,
    settlementPeriod
FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_unified`
WHERE timestamp >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {days} DAY)
ORDER BY timestamp DESC
LIMIT 200
"""

results = list(client.query(query).result())
print(f"✅ Retrieved {len(results)} records")
print()

# Calculate statistics
print("Calculating statistics...")
total_gen = sum(row.generation for row in results if row.generation)
fuel_types = sorted(set(row.fuelType for row in results if row.fuelType))

# Count by fuel type
fuel_totals = {}
for row in results:
    if row.fuelType and row.generation:
        if row.fuelType not in fuel_totals:
            fuel_totals[row.fuelType] = 0
        fuel_totals[row.fuelType] += row.generation

# Sort by total generation
top_fuels = sorted(fuel_totals.items(), key=lambda x: x[1], reverse=True)

print(f"  Total Generation: {total_gen/1000:.1f} GWh")
print(f"  Fuel Types: {len(fuel_types)}")
print(f"  Top 3 Fuels: {', '.join([f[0] for f in top_fuels[:3]])}")
print()

# Update sheet
print("Updating sheet...")

# Update summary stats
sheet.update_acell('C19', f"{total_gen/1000:.1f} GWh")
sheet.update_acell('C20', ', '.join([f"{ft[0]} ({ft[1]/1000:.0f} GWh)" for ft in top_fuels[:3]]))
sheet.update_acell('C21', f"{len(results):,} records")

if quick_select == 'Custom':
    sheet.update_acell('C22', f"{from_date} - {to_date}")
else:
    end = datetime.now()
    start = end - timedelta(days=days)
    sheet.update_acell('C22', f"{start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}")

# Update data table
table_data = []
for row in results[:50]:  # Display 50 rows
    table_data.append([
        row.timestamp.strftime('%d/%m/%y %H:%M') if row.timestamp else '',
        row.fuelType or '',
        f"{row.generation:.0f}" if row.generation else '',
        row.source or '',
        row.settlementDate.strftime('%d/%m/%y') if row.settlementDate else '',
        f"SP{row.settlementPeriod}" if row.settlementPeriod else ''
    ])

if table_data:
    # Clear old data first (rows 27-126)
    sheet.update(values=[[''] * 6 for _ in range(100)], range_name='A27:F126')
    # Write new data
    sheet.update(values=table_data, range_name='A27:F76')
    print(f"✅ Updated table with {len(table_data)} rows")

# Update timestamp
sheet.update_acell('A101', f"Last Updated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

print()
print("=" * 70)
print("✅ ANALYSIS SHEET UPDATED!")
print("=" * 70)
print()
print(f"📊 Summary:")
print(f"  • Date Range: {quick_select} ({days} days)")
print(f"  • Total Generation: {total_gen/1000:.1f} GWh")
print(f"  • Records: {len(results):,}")
print(f"  • Displayed: {len(table_data)} rows")
print()
print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
