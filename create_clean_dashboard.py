#!/usr/bin/env python3
"""
Create Clean Traffic Light Dashboard matching the specified format:
Region | DNO ID | Red Band (p/kWh) | Amber Band (p/kWh) | Green Band (p/kWh) | 
Red Band Time | Amber Band Time | Green Band Time | Standing Charge (p/day) | Capacity Charge (p/kVA/day)
"""

import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load the cleaned rates
df = pd.read_csv('traffic_light_rates_clean.csv')

# Reformat to match the specified output
dashboard_df = pd.DataFrame({
    'Region': df['DNO_Name'],
    'DNO_ID': df['DNO_Code'],
    'Year': df['Year'],
    'Red_Band_p_per_kWh': df['Red_Rate_p_per_kWh'].round(2),
    'Amber_Band_p_per_kWh': df['Amber_Rate_p_per_kWh'].round(2),
    'Green_Band_p_per_kWh': df['Green_Rate_p_per_kWh'].round(2),
    'Red_Band_Time': df['Red_Time'],
    'Amber_Band_Time': df['Amber_Time'],
    'Green_Band_Time': df['Green_Time'],
    'Standing_Charge_p_per_day': 'See tariff sheet',  # Varies by tariff
    'Capacity_Charge_p_per_kVA_per_day': 'See tariff sheet'  # Varies by tariff
})

print("=" * 100)
print("🚦 TRAFFIC LIGHT DASHBOARD - CLEAN FORMAT")
print("=" * 100)
print()

# Display sample
for idx, row in dashboard_df.head(3).iterrows():
    print(f"Region: {row['Region']}")
    print(f"DNO ID: {row['DNO_ID']}")
    print(f"Year: {row['Year']}")
    print(f"Red Band:   {row['Red_Band_p_per_kWh']:.2f} p/kWh  | Time: {row['Red_Band_Time']}")
    print(f"Amber Band: {row['Amber_Band_p_per_kWh']:.2f} p/kWh  | Time: {row['Amber_Band_Time']}")
    print(f"Green Band: {row['Green_Band_p_per_kWh']:.2f} p/kWh  | Time: {row['Green_Band_Time']}")
    print()

print(f"Total records: {len(dashboard_df)}")
print()

# Save to CSV
csv_file = 'traffic_light_dashboard_formatted.csv'
dashboard_df.to_csv(csv_file, index=False)
print(f"💾 Saved to: {csv_file}")

# Upload to Google Sheets
print("\n📤 Uploading to Google Sheets...")

try:
    creds = Credentials.from_authorized_user_file('token.json', [
        'https://www.googleapis.com/auth/spreadsheets'
    ])
    
    service = build('sheets', 'v4', credentials=creds)
    
    # Create new spreadsheet
    spreadsheet = {
        'properties': {
            'title': 'Traffic Light Tariff Rates - Clean Format'
        }
    }
    
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    print(f"✅ Created spreadsheet: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    
    # Prepare data
    headers = list(dashboard_df.columns)
    values = [headers] + dashboard_df.fillna('').astype(str).values.tolist()
    
    # Upload data
    body = {
        'values': values
    }
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"✅ Uploaded {len(dashboard_df)} rows")
    
    # Format the header row
    requests = [
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86},
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        },
        {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': len(headers)
                }
            }
        }
    ]
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()
    
    print("✅ Applied formatting")
    print(f"\n🔗 Dashboard URL:")
    print(f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    
except FileNotFoundError:
    print("❌ token.json not found - Google Sheets upload skipped")
except HttpError as e:
    print(f"❌ Google Sheets API error: {e}")

print("\n✅ DASHBOARD CREATION COMPLETE!")
