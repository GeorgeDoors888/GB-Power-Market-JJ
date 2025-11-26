#!/usr/bin/env python3
"""
Implement comprehensive GB Transmission Constraint System in Dashboard
Based on next_steps.txt requirements for NESO/ESO constraint data
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import os
from datetime import datetime

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
dashboard = sh.worksheet('Dashboard')

print("🔌 Implementing GB Transmission Constraint System")
print("="*70)

# Find where to start adding constraint sections
START_ROW = 110  # After existing outages section

print(f"\n📍 Adding constraint sections starting at row {START_ROW}")

# ============================================================================
# SECTION 1: MAIN HEADER
# ============================================================================
print("\n1️⃣ Adding Main Constraint Header...")

header_section = [
    [""],
    ["🔌 GB TRANSMISSION CONSTRAINTS & NETWORK ANALYSIS"],
    [f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: NESO Connected Data Portal"],
    [""],
]

dashboard.update(f'A{START_ROW}', header_section)

dashboard.format(f'A{START_ROW+1}:H{START_ROW+1}', {
    "backgroundColor": {"red": 0.13, "green": 0.2, "blue": 0.42},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 14,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{START_ROW+2}:H{START_ROW+2}', {
    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
    "textFormat": {"fontSize": 9, "italic": True},
    "horizontalAlignment": "LEFT"
})

# ============================================================================
# SECTION 2: KEY TRANSMISSION BOUNDARIES
# ============================================================================
print("2️⃣ Adding Key Transmission Boundaries table...")

BOUNDARY_ROW = START_ROW + 4

boundary_data = [
    ["📊 KEY TRANSMISSION BOUNDARIES (Day-Ahead Flows & Limits)"],
    [""],
    ["Boundary", "Name", "Flow (MW)", "Limit (MW)", "Util %", "Margin", "Status", "Direction"],
    ["B6", "Anglo-Scottish", "—", "—", "—", "—", "⏳ Setup Required", "N→S"],
    ["B7", "Cheviot", "—", "—", "—", "—", "⏳ Setup Required", "N→S"],
    ["B8", "Western HVDC", "—", "—", "—", "—", "⏳ Setup Required", "S→N"],
    ["SC1", "Scotland-England", "—", "—", "—", "—", "⏳ Setup Required", "N→S"],
    ["EC5", "East Coast", "—", "—", "—", "—", "⏳ Setup Required", "N→S"],
    ["NW1", "North Wales/Mersey", "—", "—", "—", "—", "⏳ Setup Required", "N→S"],
    ["SW1", "South West Peninsula", "—", "—", "—", "—", "⏳ Setup Required", "S→N"],
    [""],
    ["💡 Status Legend: 🟢 <50% | 🟡 50-75% | 🟠 75-90% | 🔴 >90% | ⚠️ Breach"],
]

dashboard.update(f'A{BOUNDARY_ROW}', boundary_data)

# Format boundary section
dashboard.format(f'A{BOUNDARY_ROW}:H{BOUNDARY_ROW}', {
    "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{BOUNDARY_ROW+2}:H{BOUNDARY_ROW+2}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SECTION 3: CMIS (CONSTRAINT MANAGEMENT INTERTRIP SERVICE)
# ============================================================================
print("3️⃣ Adding CMIS Arming Events section...")

CMIS_ROW = BOUNDARY_ROW + 14

cmis_data = [
    [""],
    ["⚡ CMIS - CONSTRAINT MANAGEMENT INTERTRIP SERVICE (Recent Arming Events)"],
    [""],
    ["BMU ID", "Boundary", "Arm Time", "Disarm Time", "Duration", "MW Armed", "Status", "£/MWh"],
    ["—", "—", "—", "—", "—", "—", "⏳ Setup Required", "—"],
    [""],
    ["💡 CMIS is used during transmission stress - units are armed for rapid dispatch to manage constraints"],
]

dashboard.update(f'A{CMIS_ROW}', cmis_data)

dashboard.format(f'A{CMIS_ROW+1}:H{CMIS_ROW+1}', {
    "backgroundColor": {"red": 1, "green": 0.65, "blue": 0},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{CMIS_ROW+3}:H{CMIS_ROW+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SECTION 4: CMZ (CONSTRAINT MANAGEMENT ZONES - DISTRIBUTION)
# ============================================================================
print("4️⃣ Adding CMZ section...")

CMZ_ROW = CMIS_ROW + 8

cmz_data = [
    [""],
    ["🏘️ CMZ - CONSTRAINT MANAGEMENT ZONES (HV/LV Distribution Constraints)"],
    [""],
    ["CMZ ID", "Zone Type", "GSP", "Forecast MW", "Limit MW", "Util %", "Status", "Flexibility Req"],
    ["—", "—", "—", "—", "—", "—", "⏳ Setup Required", "—"],
    [""],
    ["💡 CMZ tracks local distribution constraints at HV (11-33kV) and LV (<1kV) levels"],
]

dashboard.update(f'A{CMZ_ROW}', cmz_data)

dashboard.format(f'A{CMZ_ROW+1}:H{CMZ_ROW+1}', {
    "backgroundColor": {"red": 0.6, "green": 0.4, "blue": 0.8},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{CMZ_ROW+3}:H{CMZ_ROW+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SECTION 5: CONSTRAINT COST ANALYSIS
# ============================================================================
print("5️⃣ Adding Constraint Cost Analysis...")

COST_ROW = CMZ_ROW + 8

cost_data = [
    [""],
    ["💰 CONSTRAINT COST ANALYSIS (Balancing Actions)"],
    [""],
    ["Metric", "Last Hour", "Last 24h", "Last 7d", "MTD", "Unit"],
    ["Total Constraint Cost", "—", "—", "—", "—", "£"],
    ["Avg £/MWh", "—", "—", "—", "—", "£/MWh"],
    ["Constrained-ON Actions", "—", "—", "—", "—", "count"],
    ["Constrained-OFF Actions", "—", "—", "—", "—", "count"],
    ["Most Congested Boundary", "—", "—", "—", "—", "ID"],
    ["Peak Utilisation %", "—", "—", "—", "—", "%"],
    [""],
    ["💡 Links BOAs (Balancing Offers/Bids) to constraint boundaries - costs MW-weighted by boundary utilisation"],
]

dashboard.update(f'A{COST_ROW}', cost_data)

dashboard.format(f'A{COST_ROW+1}:H{COST_ROW+1}', {
    "backgroundColor": {"red": 0.13, "green": 0.55, "blue": 0.13},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{COST_ROW+3}:F{COST_ROW+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SECTION 6: DATA SOURCES & INGESTION STATUS
# ============================================================================
print("6️⃣ Adding Data Sources status...")

SOURCES_ROW = COST_ROW + 13

sources_data = [
    [""],
    ["📡 CONSTRAINT DATA SOURCES & INGESTION STATUS"],
    [""],
    ["Dataset", "Status", "Last Update", "Records", "Source", "Update Freq"],
    ["Day-Ahead Constraint Flows", "❌ Not Configured", "—", "0", "NESO Data Portal", "Daily 14:00"],
    ["24-Month Constraint Limits", "❌ Not Configured", "—", "0", "NESO Data Portal", "Monthly"],
    ["CMIS Arming Events", "❌ Not Configured", "—", "0", "Connected Data Portal", "Daily"],
    ["CMZ HV/LV Forecasts", "❌ Not Configured", "—", "0", "DNO Flexibility Portal", "Weekly"],
    ["CMZ Flexibility Trades", "❌ Not Configured", "—", "0", "Connected Data Portal", "Per Event"],
    ["Boundary Capability (NOA)", "❌ Not Configured", "—", "0", "NESO Planning Docs", "Yearly Nov"],
    [""],
    ["💡 All datasets require Python ingestion pipeline - see setup instructions below"],
]

dashboard.update(f'A{SOURCES_ROW}', sources_data)

dashboard.format(f'A{SOURCES_ROW+1}:F{SOURCES_ROW+1}', {
    "backgroundColor": {"red": 0.4, "green": 0.4, "blue": 0.6},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{SOURCES_ROW+3}:F{SOURCES_ROW+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SECTION 7: SETUP INSTRUCTIONS
# ============================================================================
print("7️⃣ Adding Setup Instructions...")

SETUP_ROW = SOURCES_ROW + 13

setup_data = [
    [""],
    ["🚀 SETUP INSTRUCTIONS - ENABLE CONSTRAINT DATA INGESTION"],
    [""],
    ["Step", "Action", "Command / Script", "Status"],
    ["1", "Create uk_constraints dataset in BigQuery", "bq mk --location=US uk_constraints", "⏳ Not Done"],
    ["2", "Install ingestion pipeline", "python3 ingest_neso_constraints.py --setup", "⏳ Not Done"],
    ["3", "Run initial backfill", "python3 ingest_neso_constraints.py --backfill", "⏳ Not Done"],
    ["4", "Configure 6-hourly cron job", "*/6 * * * * python3 ingest_neso_constraints.py", "⏳ Not Done"],
    ["5", "Create dashboard updater", "python3 update_constraints_dashboard.py", "⏳ Not Done"],
    ["6", "Enable auto-refresh (5 min)", "*/5 * * * * python3 update_constraints_dashboard.py", "⏳ Not Done"],
    [""],
    ["📖 Full documentation: See next_steps.txt and NESO Data Portal"],
    ["🔗 NESO Portal: https://www.neso.energy/data-portal"],
    ["🔗 Connected Data: https://connecteddata.nationalgrid.co.uk"],
]

dashboard.update(f'A{SETUP_ROW}', setup_data)

dashboard.format(f'A{SETUP_ROW+1}:D{SETUP_ROW+1}', {
    "backgroundColor": {"red": 0.85, "green": 0.35, "blue": 0.13},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{SETUP_ROW+3}:D{SETUP_ROW+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SECTION 8: EMERGENCY CONSTRAINT DETECTION
# ============================================================================
print("8️⃣ Adding Emergency Detection section...")

EMERGENCY_ROW = SETUP_ROW + 16

emergency_data = [
    [""],
    ["🚨 EMERGENCY CONSTRAINT ALERTS & RAPID CHANGES"],
    [""],
    ["Time", "Boundary", "Event Type", "Previous Limit", "New Limit", "Change", "Severity"],
    ["—", "—", "—", "—", "—", "—", "⏳ Monitoring Not Active"],
    [""],
    ["💡 Emergency events: >20% limit drop, >90% utilisation, CMIS mass-arming, CMZ thermal breach"],
    ["🔔 When configured, alerts will update here within 6 hours of NESO publishing emergency data"],
]

dashboard.update(f'A{EMERGENCY_ROW}', emergency_data)

dashboard.format(f'A{EMERGENCY_ROW+1}:G{EMERGENCY_ROW+1}', {
    "backgroundColor": {"red": 0.8, "green": 0.1, "blue": 0.1},
    "textFormat": {
        "foregroundColor": {"red": 1, "green": 1, "blue": 1},
        "fontSize": 12,
        "bold": True
    },
    "horizontalAlignment": "LEFT"
})

dashboard.format(f'A{EMERGENCY_ROW+3}:G{EMERGENCY_ROW+3}', {
    "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85},
    "textFormat": {"bold": True, "fontSize": 10},
    "horizontalAlignment": "CENTER"
})

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*70)
print("✅ GB TRANSMISSION CONSTRAINT SYSTEM LAYOUT COMPLETE")
print("="*70)
print(f"\n📊 Sections Added:")
print(f"   Row {START_ROW}: Main Header")
print(f"   Row {BOUNDARY_ROW}: Key Transmission Boundaries (7 boundaries)")
print(f"   Row {CMIS_ROW}: CMIS Arming Events")
print(f"   Row {CMZ_ROW}: CMZ Distribution Constraints")
print(f"   Row {COST_ROW}: Constraint Cost Analysis")
print(f"   Row {SOURCES_ROW}: Data Sources & Status")
print(f"   Row {SETUP_ROW}: Setup Instructions")
print(f"   Row {EMERGENCY_ROW}: Emergency Alert Section")
print(f"\n📝 Total Rows Added: {EMERGENCY_ROW - START_ROW + 8}")
print("\n🔗 View Dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={dashboard.id}&range=A{START_ROW}")
print("\n⚡ NEXT STEPS:")
print("   1. Review next_steps.txt for detailed explanation of each dataset")
print("   2. Create ingest_neso_constraints.py from the template in next_steps.txt")
print("   3. Set up BigQuery dataset: bq mk --location=US uk_constraints")
print("   4. Run initial backfill to populate historic data")
print("   5. Create update_constraints_dashboard.py to refresh live data")
print("   6. Configure 6-hourly cron for continuous updates")
print("="*70)
