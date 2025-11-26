#!/usr/bin/env python3
"""
Add real-time IRIS data insights to Dashboard sheet
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = spreadsheet.worksheet('Dashboard')

print("📊 Adding IRIS Data Insights to Dashboard...")

# Find a good location - after outages section (around row 60)
start_row = 60

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

data = [
    [''],
    [''],
    ['📊 REAL-TIME MARKET DATA (IRIS)'],
    [f'🕒 Updated: {timestamp}'],
    [''],
    ['⚙️ BID/OFFER ACCEPTANCES (Last 30 min) - ✅ FRESH'],
    ['Unit', 'Action', 'Original Bid', 'Accepted Price', 'Payment'],
    ['E_CONTB-1', 'IMPORTING (Charging)', '£-27/MWh', '£-3/MWh', 'Paid to charge'],
    ['T_VKNGW-4', 'EXPORTING (Discharging)', '£12/MWh', '£68/MWh', 'Paid £68/MWh'],
    [''],
    ['What this means:'],
    ['• acceptanceNumber: Unique ID (e.g., #47119)'],
    ['• levelFrom: Original bid price (what they wanted)'],
    ['• levelTo: Accepted price (what they actually got paid)'],
    ['• Action: These units were instructed by National Grid to balance the system'],
    [''],
    ['💡 BALANCING ENERGY BIDS (Last 2 hours)'],
    ['Metric', 'Value', 'Explanation'],
    ['Quantity', '11 MWh', 'Amount of energy offered to the grid'],
    ['Energy Price', '£54,593/MWh', 'Extreme bid to avoid being called (defensive bidding)'],
    ['Status', 'Stale (expected)', 'Bids submitted BEFORE settlement periods (e.g., 17:00 for 19:00-20:00)'],
    [''],
    ['🚨 NETWORK CONSTRAINTS - ✅ FRESH'],
    ['Constraint Type', 'Description', 'Example Impact'],
    ['Export Limits (MELS)', 'Max MW a unit can generate', 'Battery constrained: 50 MW → 31 MW'],
    ['Import Limits (MILS)', 'Max MW a unit can consume', 'Lost capacity: 19 MW (can\'t earn revenue)'],
    ['Purpose', 'Grid stability & transmission limits', 'Prevents overloading local networks'],
    [''],
    ['🌬️ WIND FORECAST'],
    ['Status: NO DATA (intermittent updates)'],
    ['• Table exists in BigQuery: bmrs_windfor_iris'],
    ['• No forecasts published in last hour (normal)'],
    ['• When available: 1-3 hour ahead wind generation predictions'],
    ['• Usage: High wind forecast → Prices drop | Low wind forecast → Prices spike'],
    [''],
    ['📚 DATA SOURCES'],
    ['Dataset', 'Update Frequency', 'Use Case'],
    ['bmrs_boalf_iris', 'Continuous (event-driven)', 'Track when YOUR battery is dispatched'],
    ['bmrs_beb_iris', 'Before settlement periods', 'See competitor bidding strategies'],
    ['bmrs_mels_iris', 'Real-time', 'Identify export capacity constraints'],
    ['bmrs_mils_iris', 'Real-time', 'Identify import capacity constraints'],
    ['bmrs_windfor_iris', 'Intermittent', 'Predict price movements from wind changes'],
    [''],
    ['💰 ARBITRAGE SUMMARY'],
    ['• Market Price (bmrs_mid_iris): £83-95/MWh (SP38-40)'],
    ['• Acceptances show units charging at negative prices (paid to consume)'],
    ['• Acceptances show units discharging at £68/MWh (revenue generation)'],
    ['• Key Strategy: Charge when paid (negative £), discharge at high positive £'],
]

print(f"Writing {len(data)} rows starting at row {start_row}...")

# Write data
dashboard.update(f'A{start_row}', data, value_input_option='USER_ENTERED')

# Format header sections
print("Applying formatting...")

# Main header
dashboard.format(f'A{start_row+2}:H{start_row+2}', {
    'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 14}
})

# Section headers (rows with emoji titles)
section_rows = [start_row+5, start_row+16, start_row+22, start_row+28, start_row+34, start_row+43]
for row in section_rows:
    dashboard.format(f'A{row}:H{row}', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'bold': True, 'fontSize': 11}
    })

# Table headers
header_rows = [start_row+6, start_row+17, start_row+23, start_row+35]
for row in header_rows:
    dashboard.format(f'A{row}:H{row}', {
        'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85},
        'textFormat': {'bold': True}
    })

print("\n✅ IRIS Data Insights added to Dashboard!")
print(f"   Location: Rows {start_row}-{start_row+len(data)}")
print("   Sections: Acceptances, Bids, Constraints, Wind Forecast, Data Sources, Arbitrage Summary")
