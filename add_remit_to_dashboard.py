#!/usr/bin/env python3
"""
Add REMIT Outages sheet to Google Sheets dashboard
Shows recent generation/transmission unavailability events
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'REMIT Outages'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Authenticate Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

# Authenticate BigQuery
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

def fetch_remit_data():
    """Fetch CURRENT ACTIVE outages from deduplicated BigQuery view"""
    query = f"""
    SELECT
      publishTime,
      affectedUnit,
      eventType,
      unavailabilityType,
      fuelType,
      normalCapacity,
      availableCapacity,
      unavailableCapacity,
      eventStartTime,
      eventEndTime,
      eventStatus,
      cause,
      participantId
    FROM `{PROJECT_ID}.{DATASET}.remit_latest_revisions`
    WHERE eventStatus = 'Active'
      AND eventStartTime <= CURRENT_DATETIME()
      AND (eventEndTime >= CURRENT_DATETIME() OR eventEndTime IS NULL)
      AND unavailableCapacity > 0
    ORDER BY CAST(unavailableCapacity AS FLOAT64) DESC
    LIMIT 100
    """

    df = bq_client.query(query).to_dataframe()

    # Format timestamps
    df['publishTime'] = pd.to_datetime(df['publishTime']).dt.strftime('%Y-%m-%d %H:%M')
    df['eventStartTime'] = pd.to_datetime(df['eventStartTime']).dt.strftime('%Y-%m-%d %H:%M')
    df['eventEndTime'] = pd.to_datetime(df['eventEndTime']).dt.strftime('%Y-%m-%d %H:%M')

    # Round capacity to 1 decimal
    for col in ['normalCapacity', 'availableCapacity', 'unavailableCapacity']:
        df[col] = df[col].round(1)

    return df

def update_remit_sheet(df):
    """Update Google Sheets with REMIT data"""
    print(f"\n📊 Opening spreadsheet...")
    ss = gc.open_by_key(SPREADSHEET_ID)

    # Create or get sheet
    try:
        sheet = ss.worksheet(SHEET_NAME)
        print(f"✅ Found existing sheet: {SHEET_NAME}")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"📝 Creating new sheet: {SHEET_NAME}")
        sheet = ss.add_worksheet(title=SHEET_NAME, rows=500, cols=16)

    # Add summary header
    total_mw = df['unavailableCapacity'].sum()
    total_units = df['affectedUnit'].nunique()
    active_count = len(df)

    summary = [
        ['CURRENT ACTIVE OUTAGES', '', '', '', '', '', '', '', '', '', '', '', ''],
        [f'Total: {active_count} outages', f'{total_units} units affected', f'{total_mw:,.0f} MW unavailable', '', '', '', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', '', '', '', '', '', ''],  # Blank row
    ]

    # Prepare data headers
    headers = [
        'Publish Time', 'Unit', 'Event Type', 'Type', 'Fuel Type',
        'Normal MW', 'Available MW', 'Unavailable MW',
        'Start Time', 'End Time', 'Status', 'Cause', 'Participant'
    ]

    data = summary + [headers]

    for _, row in df.iterrows():
        data.append([
            row['publishTime'],
            row['affectedUnit'],
            row['eventType'],
            row['unavailabilityType'],
            row.get('fuelType', ''),
            row['normalCapacity'],
            row['availableCapacity'],
            row['unavailableCapacity'],
            row['eventStartTime'],
            row['eventEndTime'],
            row['eventStatus'],
            row['cause'] if pd.notna(row['cause']) else '',
            row['participantId']
        ])

    # Upload data
    print(f"📤 Uploading {len(df)} active outage records...")
    sheet.update(values=data, range_name='A1', value_input_option='USER_ENTERED')

    # Format summary header (row 1)
    sheet.format('A1:M1', {
        'backgroundColor': {'red': 0.9, 'green': 0.3, 'blue': 0.2},
        'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })

    # Format summary stats (row 2)
    sheet.format('A2:M2', {
        'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.9},
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })

    # Format column headers (row 4)
    sheet.format('A4:M4', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })

    # Freeze header rows
    sheet.freeze(rows=4)

    print(f"✅ Sheet '{SHEET_NAME}' updated successfully!")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet.id}")


def main():
    print("="*60)
    print("🔥 REMIT OUTAGES DASHBOARD UPDATE")
    print("="*60)

    # Fetch data
    print("\n📊 Fetching REMIT data from BigQuery...")
    df = fetch_remit_data()
    print(f"✅ Retrieved {len(df)} outage records")

    # Show summary
    print("\n📈 SUMMARY:")
    summary = df.groupby('unavailabilityType').agg({
        'unavailableCapacity': ['count', 'sum']
    }).round(0)
    print(summary)

    # Update sheet
    update_remit_sheet(df)

    print("\n" + "="*60)
    print("✅ REMIT DASHBOARD COMPLETE!")
    print("="*60)

if __name__ == '__main__':
    main()
