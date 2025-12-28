#!/usr/bin/env python3
"""
Implement comprehensive constraint system in Dashboard sheet
Based on next_steps.txt requirements
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import os
import pandas as pd
from datetime import datetime, timedelta

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
dashboard = sh.worksheet('Dashboard')

print("⚡ Implementing Constraint System in Dashboard")
print("="*60)

# Step 1: Check if constraint tables exist
print("\n1️⃣ Checking for existing constraint data in BigQuery...")

query_check_tables = """
SELECT table_name
FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE '%constraint%' 
   OR table_name LIKE '%boundary%'
   OR table_name LIKE '%cmz%'
ORDER BY table_name
"""

try:
    tables_df = bq_client.query(query_check_tables).to_dataframe()
    if len(tables_df) > 0:
        print(f"   ✅ Found {len(tables_df)} constraint-related tables:")
        for table in tables_df['table_name']:
            print(f"      • {table}")
    else:
        print("   ⚠️  No constraint tables found yet")
        print("   📝 Will create placeholder structure for future data")
except Exception as e:
    print(f"   ⚠️  Could not check tables: {e}")

# Step 2: Create constraint metadata section in Dashboard
print("\n2️⃣ Creating Constraint Metrics section in Dashboard...")

# Find where to add constraints section (after existing data)
current_data = dashboard.get('A1:A150')
last_row_with_data = 0
for i, row in enumerate(current_data, 1):
    if row and row[0]:
        last_row_with_data = i

constraints_start_row = last_row_with_data + 3

print(f"   📍 Adding constraint section starting at row {constraints_start_row}")

# Create header section
header_data = [
    ["", "", "", "", "", "", "", ""],  # Blank row
    ["🔌 TRANSMISSION CONSTRAINTS & NETWORK STATUS", "", "", "", "", "", "", ""],
    ["Last Updated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],  # Blank row
]

dashboard.update(f'A{constraints_start_row}', header_data)

# Format header
dashboard.format(f'A{constraints_start_row+1}:H{constraints_start_row+1}', {
    "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 14,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

# Step 3: Add Key Boundary Metrics table
print("\n3️⃣ Adding Key Boundary Metrics table...")

boundary_section_start = constraints_start_row + 4

boundary_headers = [[
    "Boundary ID",
    "Boundary Name",
    "Flow (MW)",
    "Limit (MW)",
    "Utilisation %",
    "Margin (MW)",
    "Status",
    "Last Update"
]]

# Sample boundaries (these will be populated with real data when constraint tables exist)
sample_boundaries = [
    ["B6", "B6 Anglo-Scottish", "Loading...", "Loading...", "Loading...", "Loading...", "⏳ Awaiting Data", ""],
    ["B7", "B7 Cheviot", "Loading...", "Loading...", "Loading...", "Loading...", "⏳ Awaiting Data", ""],
    ["B8", "B8 Western HVDC", "Loading...", "Loading...", "Loading...", "Loading...", "⏳ Awaiting Data", ""],
    ["EC5", "EC5 East Coast", "Loading...", "Loading...", "Loading...", "Loading...", "⏳ Awaiting Data", ""],
    ["SC1", "SC1 Scotland to England", "Loading...", "Loading...", "Loading...", "Loading...", "⏳ Awaiting Data", ""],
]

dashboard.update(f'A{boundary_section_start}', boundary_headers)
dashboard.update(f'A{boundary_section_start+1}', sample_boundaries)

# Format boundary headers
dashboard.format(f'A{boundary_section_start}:H{boundary_section_start}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True},
    "horizontalAlignment": "CENTER"
})

# Step 4: Add CMIS (Constraint Management Intertrip) section
print("\n4️⃣ Adding CMIS Arming Events section...")

cmis_section_start = boundary_section_start + 8

cmis_headers = [["", "", "", "", "", "", "", ""]]  # Blank
cmis_headers.append(["💡 CMIS - Constraint Management Intertrip Service", "", "", "", "", "", "", ""])
cmis_headers.append(["", "", "", "", "", "", "", ""])  # Blank
cmis_headers.append(["Unit ID", "Boundary", "Arm Time", "Disarm Time", "Duration (min)", "MW Available", "Status", "Notes"])

cmis_sample = [
    ["Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "⏳ Awaiting Data", ""]
]

dashboard.update(f'A{cmis_section_start}', cmis_headers)
dashboard.update(f'A{cmis_section_start+4}', cmis_sample)

# Format CMIS header
dashboard.format(f'A{cmis_section_start+1}:H{cmis_section_start+1}', {
    "backgroundColor": {"red": 1, "green": 0.85, "blue": 0.4},
    "textFormat": {"bold": True, "fontSize": 12},
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{cmis_section_start+3}:H{cmis_section_start+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True},
    "horizontalAlignment": "CENTER"
})

# Step 5: Add Constraint Cost Summary
print("\n5️⃣ Adding Constraint Cost Summary...")

cost_section_start = cmis_section_start + 8

cost_data = [
    ["", "", "", "", "", "", "", ""],  # Blank
    ["💰 CONSTRAINT COST ANALYSIS", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],  # Blank
    ["Metric", "Last Hour", "Last 24h", "Last 7d", "MTD", "YTD", "Unit", "Trend"],
    ["Total Constraint Cost", "Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "£", ""],
    ["Avg £/MWh Constraint", "Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "£/MWh", ""],
    ["Constrained-On Actions", "Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "count", ""],
    ["Constrained-Off Actions", "Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "count", ""],
    ["Most Constrained Boundary", "Loading...", "Loading...", "Loading...", "Loading...", "Loading...", "ID", ""],
]

dashboard.update(f'A{cost_section_start}', cost_data)

# Format cost header
dashboard.format(f'A{cost_section_start+1}:H{cost_section_start+1}', {
    "backgroundColor": {"red": 0.2, "green": 0.7, "blue": 0.4},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{cost_section_start+3}:H{cost_section_start+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True},
    "horizontalAlignment": "CENTER"
})

# Step 6: Add Data Sources & Status section
print("\n6️⃣ Adding Data Sources section...")

sources_section_start = cost_section_start + 12

sources_data = [
    ["", "", "", "", "", "", "", ""],  # Blank
    ["📊 CONSTRAINT DATA SOURCES & STATUS", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["Dataset", "Status", "Last Update", "Records", "Source", "Frequency", "Next Update", "Notes"],
    ["Day-Ahead Constraints", "⏳ Not Configured", "—", "—", "NESO Data Portal", "Daily", "—", "Requires ingestion setup"],
    ["24-Month Constraint Limits", "⏳ Not Configured", "—", "—", "NESO Data Portal", "Monthly", "—", "Planning data"],
    ["CMIS Events", "⏳ Not Configured", "—", "—", "NESO Connected Data", "Daily", "—", "Intertrip arming logs"],
    ["CMZ Forecasts", "⏳ Not Configured", "—", "—", "DNO Flexibility Portal", "Weekly", "—", "Distribution constraints"],
    ["Boundary Capability", "⏳ Not Configured", "—", "—", "NOA/SYS Reports", "Yearly", "—", "Historic MW limits"],
]

dashboard.update(f'A{sources_section_start}', sources_data)

# Format sources header
dashboard.format(f'A{sources_section_start+1}:H{sources_section_start+1}', {
    "backgroundColor": {"red": 0.4, "green": 0.4, "blue": 0.6},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{sources_section_start+3}:H{sources_section_start+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True},
    "horizontalAlignment": "CENTER"
})

# Step 7: Add Quick Actions section
print("\n7️⃣ Adding Quick Actions section...")

actions_section_start = sources_section_start + 12

actions_data = [
    ["", "", "", "", "", "", "", ""],
    ["⚡ QUICK ACTIONS & SETUP", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", ""],
    ["Action", "Description", "Status", "Command", "", "", "", ""],
    ["Setup Constraint Ingestion", "Install Python pipeline to fetch NESO data", "⏳ Ready", "See constraint_ingestion_setup.py", "", "", "", ""],
    ["Create uk_constraints Dataset", "BigQuery dataset for all constraint tables", "⏳ Ready", "See setup instructions", "", "", "", ""],
    ["Configure Auto-Refresh", "Schedule 6-hourly data updates", "⏳ Ready", "Add to cron", "", "", "", ""],
    ["Enable Map Visualization", "Interactive constraint map with GeoJSON", "⏳ Ready", "See constraint_map.html", "", "", "", ""],
]

dashboard.update(f'A{actions_section_start}', actions_data)

# Format actions header
dashboard.format(f'A{actions_section_start+1}:H{actions_section_start+1}', {
    "backgroundColor": {"red": 0.9, "green": 0.5, "blue": 0.2},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{actions_section_start+3}:H{actions_section_start+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True},
    "horizontalAlignment": "CENTER"
})

print("\n" + "="*60)
print("✅ CONSTRAINT SYSTEM LAYOUT COMPLETE")
print("="*60)
print(f"\n📍 Sections added starting at row {constraints_start_row}:")
print(f"   • Header: Row {constraints_start_row}")
print(f"   • Key Boundaries: Row {boundary_section_start}")
print(f"   • CMIS Events: Row {cmis_section_start}")
print(f"   • Cost Analysis: Row {cost_section_start}")
print(f"   • Data Sources: Row {sources_section_start}")
print(f"   • Quick Actions: Row {actions_section_start}")
print("\n📝 NEXT STEPS:")
print("   1. Run constraint_ingestion_setup.py to create BigQuery tables")
print("   2. Set up 6-hourly cron job for data refresh")
print("   3. Create update_constraints_dashboard.py for live data")
print("   4. Add GeoJSON map visualization (optional)")
print("\n🔗 Dashboard URL:")
print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
