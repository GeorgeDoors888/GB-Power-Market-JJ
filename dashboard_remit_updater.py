#!/usr/bin/env python3
"""
REMIT Dashboard Updater - Add unavailability data to Google Sheets

Creates a new sheet "REMIT Unavailability" with current outage information
"""

import pickle
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import gspread
from typing import List, Dict

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "bmrs_remit_unavailability"

SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
REMIT_SHEET_NAME = "REMIT Unavailability"

# Google Sheets authentication
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_active_remit_events() -> pd.DataFrame:
    """Query BigQuery for active REMIT unavailability events"""
    
    print("📥 Fetching active REMIT events from BigQuery...")
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    query = f"""
    SELECT
        assetName,
        affectedUnit,
        fuelType,
        normalCapacity,
        availableCapacity,
        unavailableCapacity,
        CAST(eventStartTime AS STRING) as eventStartTime,
        CAST(eventEndTime AS STRING) as eventEndTime,
        cause,
        eventStatus,
        participantName,
        relatedInfo
    FROM `{table_id}`
    WHERE eventStatus = 'Active'
      AND DATETIME(eventStartTime) <= CURRENT_DATETIME()
      AND DATETIME(eventEndTime) >= CURRENT_DATETIME()
    ORDER BY unavailableCapacity DESC, eventStartTime ASC
    LIMIT 100
    """
    
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        
        if not results:
            print("ℹ️  No active unavailability events found")
            return pd.DataFrame()
        
        # Convert to DataFrame manually
        data = []
        for row in results:
            data.append({
                'assetName': row.assetName,
                'affectedUnit': row.affectedUnit,
                'fuelType': row.fuelType,
                'normalCapacity': float(row.normalCapacity) if row.normalCapacity else 0.0,
                'availableCapacity': float(row.availableCapacity) if row.availableCapacity else 0.0,
                'unavailableCapacity': float(row.unavailableCapacity) if row.unavailableCapacity else 0.0,
                'eventStartTime': pd.to_datetime(row.eventStartTime),
                'eventEndTime': pd.to_datetime(row.eventEndTime),
                'cause': row.cause,
                'eventStatus': row.eventStatus,
                'participantName': row.participantName,
                'relatedInfo': row.relatedInfo
            })
        
        df = pd.DataFrame(data)
        print(f"✅ Retrieved {len(df)} active unavailability events")
        return df
    except Exception as e:
        print(f"❌ Error querying BigQuery: {e}")
        return pd.DataFrame()


def format_remit_sheet_data(df: pd.DataFrame) -> List[List]:
    """Format REMIT data for Google Sheets"""
    
    if df.empty:
        return [
            ["🔴 UK POWER MARKET - REMIT UNAVAILABILITY TRACKER"],
            [f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            [""],
            ["ℹ️  No active unavailability events at this time"],
        ]
    
    # Calculate summary metrics
    total_unavailable = df['unavailableCapacity'].sum()
    affected_units = len(df)
    
    # Group by fuel type
    fuel_summary = df.groupby('fuelType')['unavailableCapacity'].sum().sort_values(ascending=False)
    
    # Build sheet data
    sheet_data = []
    
    # Header
    sheet_data.append(["🔴 UK POWER MARKET - REMIT UNAVAILABILITY TRACKER"])
    sheet_data.append([f"⏰ Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    sheet_data.append([""])
    
    # Summary
    sheet_data.append(["📊 SUMMARY"])
    sheet_data.append([f"Active Outages: {affected_units}"])
    sheet_data.append([f"Total Unavailable Capacity: {total_unavailable:.1f} MW"])
    sheet_data.append([""])
    
    # By Fuel Type
    sheet_data.append(["🔥 UNAVAILABLE CAPACITY BY FUEL TYPE"])
    for fuel, capacity in fuel_summary.items():
        pct = (capacity / total_unavailable * 100) if total_unavailable > 0 else 0
        sheet_data.append([f"{fuel}: {capacity:.1f} MW ({pct:.1f}%)"])
    sheet_data.append([""])
    
    # Detailed Events Table Header
    sheet_data.append(["🔴 ACTIVE UNAVAILABILITY EVENTS (Unplanned Outages)"])
    sheet_data.append([""])
    sheet_data.append([
        "Asset Name",
        "BM Unit",
        "Fuel Type",
        "Normal (MW)",
        "Available (MW)",
        "Unavailable (MW)",
        "Start Time",
        "End Time (Est.)",
        "Duration (hrs)",
        "Cause",
        "Operator"
    ])
    
    # Event rows
    for idx, row in df.iterrows():
        duration_hours = (row['eventEndTime'] - row['eventStartTime']).total_seconds() / 3600
        
        sheet_data.append([
            row['assetName'],
            row['affectedUnit'],
            row['fuelType'],
            f"{row['normalCapacity']:.0f}",
            f"{row['availableCapacity']:.0f}",
            f"{row['unavailableCapacity']:.0f}",
            row['eventStartTime'].strftime('%Y-%m-%d %H:%M'),
            row['eventEndTime'].strftime('%Y-%m-%d %H:%M'),
            f"{duration_hours:.1f}",
            row['cause'][:50] if pd.notna(row['cause']) else "",  # Truncate long causes
            row['participantName'][:30] if pd.notna(row['participantName']) else ""
        ])
    
    sheet_data.append([""])
    sheet_data.append(["ℹ️  Data Source: Elexon REMIT Messages (Regulation on wholesale Energy Market Integrity and Transparency)"])
    sheet_data.append(["💡 REMIT requires market participants to publish inside information about facility unavailability before trading"])
    
    return sheet_data


def create_or_update_remit_sheet():
    """Create or update REMIT sheet in Google Sheets"""
    
    print("="*70)
    print("🔴 REMIT DASHBOARD UPDATER")
    print("="*70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load Google Sheets credentials
    print("🔐 Authenticating with Google Sheets...")
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    
    gc = gspread.authorize(creds)
    
    # Open spreadsheet
    print(f"📊 Opening spreadsheet...")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Check if REMIT sheet exists, create if not
    try:
        sheet = spreadsheet.worksheet(REMIT_SHEET_NAME)
        print(f"✅ Found existing '{REMIT_SHEET_NAME}' sheet")
    except gspread.WorksheetNotFound:
        print(f"➕ Creating new '{REMIT_SHEET_NAME}' sheet...")
        sheet = spreadsheet.add_worksheet(title=REMIT_SHEET_NAME, rows=100, cols=12)
    
    # Get REMIT data
    df = get_active_remit_events()
    
    # Format for sheets
    sheet_data = format_remit_sheet_data(df)
    
    # Clear existing content
    print("🧹 Clearing existing data...")
    sheet.clear()
    
    # Update sheet
    print(f"📝 Updating sheet with {len(sheet_data)} rows...")
    sheet.update(sheet_data, 'A1')
    
    # Apply formatting
    print("🎨 Applying formatting...")
    
    # Header formatting (row 1)
    sheet.format('A1:K1', {
        'backgroundColor': {'red': 0.8, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 14}
    })
    
    # Summary section headers
    sheet.format('A4', {'textFormat': {'bold': True, 'fontSize': 12}})
    sheet.format('A8', {'textFormat': {'bold': True, 'fontSize': 12}})
    
    # Table header row (find it dynamically)
    header_row = None
    for idx, row in enumerate(sheet_data):
        if row and row[0] == "Asset Name":
            header_row = idx + 1
            break
    
    if header_row:
        sheet.format(f'A{header_row}:K{header_row}', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })
    
    # Auto-resize columns
    sheet.columns_auto_resize(0, 11)
    
    # Freeze header rows
    sheet.freeze(rows=2)
    
    print("\n" + "="*70)
    print("✅ REMIT DASHBOARD UPDATE COMPLETE!")
    print("="*70)
    print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"📄 Sheet: {REMIT_SHEET_NAME}")
    
    if not df.empty:
        print(f"\n📊 Active Events: {len(df)}")
        print(f"⚡ Total Unavailable: {df['unavailableCapacity'].sum():.1f} MW")


if __name__ == '__main__':
    create_or_update_remit_sheet()
