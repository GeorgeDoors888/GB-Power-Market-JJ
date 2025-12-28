#!/usr/bin/env python3
"""
Create DATA DICTIONARY sheet in Google Sheets
Comprehensive glossary of all columns/KPIs across all sheets
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Initialize gspread
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Try to get existing sheet or create new one
try:
    worksheet = spreadsheet.worksheet('DATA DICTIONARY')
    print("📝 Found existing DATA DICTIONARY sheet, clearing...")
    worksheet.clear()
except gspread.WorksheetNotFound:
    print("📝 Creating new DATA DICTIONARY sheet...")
    worksheet = spreadsheet.add_worksheet(title='DATA DICTIONARY', rows=500, cols=10)

# Header row
header_data = [
    ['GB POWER MARKET JJ - DATA DICTIONARY', '', '', '', '', '', ''],
    ['Complete reference for all KPIs, columns, and metrics across all sheets', '', '', '', '', '', ''],
    ['Last Updated: December 23, 2025', '', '', '', '', '', ''],
    [''],
    ['Sheet', 'Column/KPI', 'Description', 'Units', 'Source Table(s)', 'Update Frequency', 'Calculation Method', 'Example Values']
]

# Live Dashboard v2 - Market Metrics (A5-B9)
live_dashboard_market = [
    ['LIVE DASHBOARD V2 - MARKET METRICS', '', '', '', '', '', '', ''],
    ['Live Dashboard v2', 'BM-MID Spread (A5)', 'Balancing Mechanism vs Market Index price difference', '£/MWh', 'bmrs_costs, bmrs_mid', '5 min', 'System Price - MID Price', '£15-40/MWh'],
    ['Live Dashboard v2', 'Market Index (C5)', 'Wholesale day-ahead/within-day price', '£/MWh', 'bmrs_mid', '5 min', 'Latest MID price from Elexon', '£30-60/MWh'],
    ['Live Dashboard v2', 'Spread Sparkline (A7-B9)', '48-period sparkline showing BM-MID spread trend', 'Visual', 'bmrs_costs, bmrs_mid', '5 min', 'LET formula with SPARKLINE', 'Purple/crimson bars'],
    ['']
]

# Live Dashboard v2 - Combined KPIs (K12-S22)
live_dashboard_kpis = [
    ['LIVE DASHBOARD V2 - COMBINED KPIs (K12:S22)', '', '', '', '', '', '', ''],
    ['Live Dashboard v2', 'Real-time imbalance price (K13)', 'Current system imbalance settlement price', '£/MWh', 'bmrs_costs', '5 min', 'Latest SSP (=SBP since Nov 2015)', '£40-100/MWh'],
    ['Live Dashboard v2', '7-Day Average (K14)', 'Rolling 7-day mean system price', '£/MWh', 'bmrs_costs', '5 min', 'AVG(price) over 7 days', '£50-80/MWh'],
    ['Live Dashboard v2', '30-Day Average (K15)', 'Rolling 30-day mean system price', '£/MWh', 'bmrs_costs', '5 min', 'AVG(price) over 30 days', '£50-80/MWh'],
    ['Live Dashboard v2', 'Deviation from 7d (K16)', 'Percentage deviation from 7-day average', '%', 'bmrs_costs', '5 min', '(Current - 7d avg) / 7d avg × 100', '-20% to +50%'],
    ['Live Dashboard v2', '30-Day High (K17)', 'Maximum price in last 30 days', '£/MWh', 'bmrs_costs', '5 min', 'MAX(price) over 30 days', '£100-400/MWh'],
    ['Live Dashboard v2', '30-Day Low (K18)', 'Minimum price in last 30 days (can be negative)', '£/MWh', 'bmrs_costs', '5 min', 'MIN(price) over 30 days', '£-20 to £20/MWh'],
    ['Live Dashboard v2', 'Total BM Cashflow (K19)', 'Sum of all BM acceptance cashflows', '£k', 'bmrs_ebocf, bmrs_boav', '5 min', 'Σ(Volume × Price) for all acceptances', '£50k-500k/day'],
    ['Live Dashboard v2', 'EWAP Offer (K20)', 'Energy-Weighted Average Price for offers', '£/MWh', 'bmrs_ebocf, bmrs_boav', '5 min', 'Σ(Offer £) / Σ(Offer MWh)', '£50-150/MWh'],
    ['Live Dashboard v2', 'EWAP Bid (K21)', 'Energy-Weighted Average Price for bids', '£/MWh', 'bmrs_ebocf, bmrs_boav', '5 min', 'Σ(Bid £) / Σ(Bid MWh)', '£30-80/MWh'],
    ['Live Dashboard v2', 'Dispatch Intensity (K22)', 'Balancing actions per hour', 'actions/hr', 'bmrs_boalf', '5 min', 'Total Acceptances / Hours', '5-30/hr (stress: 60+)'],
    ['Live Dashboard v2', 'Workhorse Index (S22)', 'Percentage of settlement periods with activity', '%', 'bmrs_boalf', '5 min', '(Periods with activity / 48) × 100', '5-15% (stress: 50%+)'],
    ['Live Dashboard v2', 'Sparklines (N13-S22)', '6-column wide sparklines for 24h trends', 'Visual', 'Various', '5 min', 'Google Sheets SPARKLINE formula', 'Bar/line charts'],
    ['']
]

# VLP Revenue Analysis (L54-R67)
vlp_revenue = [
    ['LIVE DASHBOARD V2 - VLP REVENUE ANALYSIS (L54:R67)', '', '', '', '', '', '', ''],
    ['Live Dashboard v2', 'Operator Name (M)', 'VLP unit identifier', 'Text', 'bmrs_boalf', '5 min', 'bmUnitId from acceptances', 'FFSEN005, FBPGM002'],
    ['Live Dashboard v2', 'Total MWh (N)', 'Total energy dispatched', 'MWh', 'bmrs_boalf', '5 min', 'Σ(acceptanceVolume) 28-day rolling', '5,000-20,000 MWh'],
    ['Live Dashboard v2', 'Revenue (£k) (O)', 'Gross revenue from BM actions', '£k', 'bmrs_boalf_complete', '5 min', 'Σ(Volume × acceptancePrice)', '£500k-5,000k/month'],
    ['Live Dashboard v2', 'Margin (£/MWh) (P)', 'Average revenue per MWh', '£/MWh', 'Calculated', '5 min', 'Revenue / Total MWh', '£20-150/MWh'],
    ['Live Dashboard v2', 'BM Price (Q)', 'Average imbalance price received', '£/MWh', 'bmrs_costs', '5 min', 'Weighted avg system price', '£50-90/MWh'],
    ['Live Dashboard v2', 'Wholesale (R)', 'Average wholesale price', '£/MWh', 'bmrs_mid', '5 min', 'Avg MID price', '£40-70/MWh'],
    ['']
]

# Active Outages (G25-K41)
outages = [
    ['LIVE DASHBOARD V2 - ACTIVE OUTAGES (G25:K41)', '', '', '', '', '', '', ''],
    ['Live Dashboard v2', 'Asset Name (G)', 'Generator/unit identifier', 'Text', 'bmrs_remit_unavailability', '5 min', 'bmUnitId from REMIT messages', 'DIDCB6, DRAXX8'],
    ['Live Dashboard v2', 'Fuel Type (H)', 'Generation technology with emoji', 'Text', 'bmrs_remit_unavailability', '5 min', 'fuelType from REMIT', '🏭 CCGT, ⚛️ Nuclear'],
    ['Live Dashboard v2', 'Unavail (MW) (I)', 'Offline capacity', 'MW', 'bmrs_remit_unavailability', '5 min', 'unavailableCapacity', '100-1,200 MW'],
    ['Live Dashboard v2', 'Normal (MW) (J)', 'Installed capacity', 'MW', 'bmrs_remit_unavailability', '5 min', 'normalCapacity', '100-1,200 MW'],
    ['Live Dashboard v2', 'Cause (K)', 'Outage reason (truncated)', 'Text', 'bmrs_remit_unavailability', '5 min', 'cause field (30 chars)', 'Planned outage, etc'],
    ['']
]

# Interconnectors (G13-H22)
interconnectors = [
    ['LIVE DASHBOARD V2 - INTERCONNECTORS (G13:H22)', '', '', '', '', '', '', ''],
    ['Live Dashboard v2', 'Interconnector Name (G)', 'Cross-border link identifier', 'Text', 'bmrs_indgen_iris', '5 min', 'bmUnitId for interconnector', 'IFA, IFA2, Moyle'],
    ['Live Dashboard v2', 'Flow (MW) (H)', 'Current power flow (+ = import)', 'MW', 'bmrs_indgen_iris', '5 min', 'generation from IRIS', '-2,000 to +2,000 MW'],
    ['Live Dashboard v2', 'Sparklines', '48-period flow trend', 'Visual', 'bmrs_indgen_iris', '5 min', 'SPARKLINE formula', 'Purple bars'],
    ['']
]

# Data_Hidden sheet
data_hidden = [
    ['DATA_HIDDEN SHEET - RAW DATA STORAGE', '', '', '', '', '', '', ''],
    ['Data_Hidden', 'Fuel Generation (Rows 2-25)', '48 settlement periods × 10 fuel types', 'GW', 'bmrs_fuelinst, bmrs_fuelinst_iris', '5 min', 'UNION historical + IRIS', '0-20 GW per fuel'],
    ['Data_Hidden', 'Interconnector Flows', '48 settlement periods × 10 links', 'MW', 'bmrs_indgen_iris', '5 min', 'Latest IRIS generation data', '-2,000 to +2,000 MW'],
    ['Data_Hidden', 'Market Metrics', '48 settlement periods for prices/spreads', '£/MWh', 'bmrs_costs, bmrs_mid', '5 min', 'System price, MID, spread calc', '£20-120/MWh'],
    ['']
]

# BtM Calculator
btm_calculator = [
    ['BTM CALCULATOR SHEET', '', '', '', '', '', '', ''],
    ['BtM Calculator', 'Site Consumption (kWh)', 'Total electricity consumed', 'kWh', 'User input', 'Manual', 'User-entered value', '10,000-500,000 kWh'],
    ['BtM Calculator', 'Generation (kWh)', 'Behind-the-meter generation', 'kWh', 'User input', 'Manual', 'Solar/wind generation', '0-100,000 kWh'],
    ['BtM Calculator', 'Grid Import (kWh)', 'Electricity drawn from grid', 'kWh', 'Calculated', 'Auto', 'Consumption - Generation', '5,000-400,000 kWh'],
    ['BtM Calculator', 'Export (kWh)', 'Surplus sent to grid', 'kWh', 'User input', 'Manual', 'Excess generation', '0-50,000 kWh'],
    ['BtM Calculator', 'Import Rate (p/kWh)', 'Grid electricity cost', 'p/kWh', 'User input', 'Manual', 'Supplier tariff', '15-40 p/kWh'],
    ['BtM Calculator', 'Export Rate (p/kWh)', 'Payment for exports', 'p/kWh', 'User input', 'Manual', 'SEG rate', '3-15 p/kWh'],
    ['BtM Calculator', 'Savings (£)', 'Total cost savings from BtM', '£', 'Calculated', 'Auto', 'Generation × Import Rate', '£500-£20,000'],
    ['']
]

# BESS sheet
bess = [
    ['BESS SHEET - BATTERY SYSTEM CALCULATOR', '', '', '', '', '', '', ''],
    ['BESS', 'Postcode (A6)', 'Site location postcode', 'Text', 'User input', 'Manual', 'UK postcode', 'SW1A 1AA'],
    ['BESS', 'MPAN (B6)', 'Meter Point Administration Number', 'Text', 'User input', 'Manual', '13-digit MPAN', '1405566778899'],
    ['BESS', 'DNO Region (C6-H6)', 'Distribution Network Operator details', 'Text', 'gb_power.duos_unit_rates, postcodes.io', 'On-demand', 'MPAN core lookup + API', 'NGED West Midlands'],
    ['BESS', 'Voltage (A9)', 'Connection voltage level', 'Text', 'User input (dropdown)', 'Manual', 'LV/HV/EHV selection', 'HV, LV, EHV'],
    ['BESS', 'DUoS Rates (B9-D9)', 'Distribution charges by time band', 'p/kWh', 'gb_power.duos_unit_rates', 'On-demand', 'DNO + voltage lookup', 'Red: 1.764, Amber: 0.118'],
    ['BESS', 'Time Bands (A11-C13)', 'Red/Amber/Green time periods', 'Text', 'gb_power.duos_time_bands', 'On-demand', 'DNO time band rules', '16:00-19:30 weekdays'],
    ['']
]

# BigQuery source tables
bigquery_tables = [
    ['BIGQUERY SOURCE TABLES - INNER-CINEMA-476211-U9.UK_ENERGY_PROD', '', '', '', '', '', '', ''],
    ['BigQuery', 'bmrs_costs', 'System imbalance prices (SSP/SBP)', '£/MWh', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '50M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_costs_iris', 'Real-time imbalance prices', '£/MWh', 'Azure IRIS streaming', '5 min', 'Real-time stream', '~20k rows, 24-48h'],
    ['BigQuery', 'bmrs_mid', 'Market Index Data (wholesale)', '£/MWh', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '40M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_fuelinst', 'Fuel generation by type', 'MW', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '80M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_fuelinst_iris', 'Real-time fuel generation', 'MW', 'Azure IRIS streaming', '5 min', 'Real-time stream', '~30k rows, 24-48h'],
    ['BigQuery', 'bmrs_bod', 'Bid-Offer Data (prices)', '£/MWh', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '391M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_boalf', 'Balancing acceptance volumes', 'MW', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '40M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_boalf_complete', 'Acceptances WITH prices', '£/MWh', 'BOD matching logic', 'Daily', 'Derived from BOD+BOALF', '11M rows, 42.8% valid'],
    ['BigQuery', 'bmrs_ebocf', 'BM cashflow data', '£', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '30M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_boav', 'BM acceptance volumes', 'MWh', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '35M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_freq', 'Grid frequency measurements', 'Hz', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '15M+ rows, 2020-present'],
    ['BigQuery', 'bmrs_indgen_iris', 'Real-time unit generation', 'MW', 'Azure IRIS streaming', '5 min', 'Real-time stream', '~50k rows, 24-48h'],
    ['BigQuery', 'bmrs_remit_unavailability', 'Generation outages', 'MW', 'Elexon BMRS REST API', '5 min', 'Historical batch ingest', '5M+ rows, 2020-present'],
    ['BigQuery', 'neso_dno_reference', 'DNO operator details', 'Text', 'Manual dataset', 'Static', 'Reference table', '14 DNO regions'],
    ['BigQuery', 'duos_unit_rates', 'DUoS charges by DNO/voltage', 'p/kWh', 'Manual dataset', 'Annual', 'Ofgem published rates', '~200 rate combinations'],
    ['BigQuery', 'duos_time_bands', 'Time band definitions', 'Text', 'Manual dataset', 'Annual', 'DNO time rules', 'Red/Amber/Green times'],
    ['']
]

# Special calculations
calculations = [
    ['KEY CALCULATIONS & FORMULAS', '', '', '', '', '', '', ''],
    ['Calculation', 'BM Cashflow', 'Total revenue from balancing actions', '£', 'bmrs_ebocf, bmrs_boav', 'Real-time', 'Σ(Volume × Price) for offers + bids', '£50k-500k/day'],
    ['Calculation', 'EWAP', 'Energy-Weighted Average Price', '£/MWh', 'bmrs_ebocf, bmrs_boav', 'Real-time', 'Σ(Cashflow) / Σ(MWh)', '£30-150/MWh'],
    ['Calculation', 'BM-MID Spread', 'Balancing premium over wholesale', '£/MWh', 'bmrs_costs, bmrs_mid', 'Real-time', 'System Price - MID Price', '£5-50/MWh'],
    ['Calculation', 'Workhorse Index', 'Market activity intensity', '%', 'bmrs_boalf', 'Real-time', '(Active periods / 48) × 100', '5-50%'],
    ['Calculation', 'VLP Margin', 'Battery arbitrage profitability', '£/MWh', 'bmrs_boalf_complete, bmrs_mid', 'Real-time', 'Revenue / Total MWh', '£20-500/MWh'],
    ['Calculation', 'DUoS Charges', 'Distribution network costs', 'p/kWh', 'duos_unit_rates, duos_time_bands', 'On-demand', 'Rate × Time Band', '0.038-4.837 p/kWh'],
    ['']
]

# System metadata
metadata = [
    ['SYSTEM METADATA & SCALE', '', '', '', '', '', '', ''],
    ['System', 'Total BMRS Tables', '174+ tables in uk_energy_prod dataset', 'Count', 'BigQuery', 'Static', 'Schema inspection', '174+ tables'],
    ['System', 'bmrs_bod Rows', 'Largest single table', 'Rows', 'BigQuery', 'Growing', 'SELECT COUNT(*)', '391M+ rows'],
    ['System', 'Total Dataset Size', 'Complete uk_energy_prod dataset', 'GB', 'BigQuery', 'Growing', 'Storage quota', '~50-100 GB'],
    ['System', 'Historical Coverage', 'Batch data date range', 'Years', 'Elexon API', 'Static', 'Archive depth', '2020-present (5+ years)'],
    ['System', 'IRIS Coverage', 'Real-time data retention', 'Hours', 'Azure IRIS', 'Rolling', 'Stream buffer', '24-48 hours'],
    ['System', 'Update Frequency', 'Dashboard refresh rate', 'Minutes', 'Cron', 'Configured', 'update_live_metrics.py', 'Every 5 minutes'],
    ['System', 'Data Latency', 'Time from generation to dashboard', 'Minutes', 'Various', 'Variable', 'Pipeline delay', '5-120 min (varies by source)'],
    ['System', 'API Integrations', 'External data sources', 'Count', 'Various', 'Static', 'Integration count', '4 APIs (Elexon, IRIS, postcodes.io, Google)'],
    ['']
]

# Combine all data
all_data = header_data + live_dashboard_market + live_dashboard_kpis + vlp_revenue + outages + interconnectors + data_hidden + btm_calculator + bess + bigquery_tables + calculations + metadata

print(f"📝 Writing {len(all_data)} rows to DATA DICTIONARY sheet...")

# Write data in batches (Google Sheets API limit: 10M cells per request, ~1000 rows safe)
batch_size = 100
for i in range(0, len(all_data), batch_size):
    batch = all_data[i:i+batch_size]
    start_row = i + 1
    end_row = start_row + len(batch) - 1
    range_name = f'A{start_row}:H{end_row}'
    worksheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
    print(f"  ✅ Wrote rows {start_row}-{end_row}")

# Format header
print("🎨 Applying formatting...")

# Header rows (1-3) - bold, large, centered
worksheet.format('A1:H3', {
    'textFormat': {'bold': True, 'fontSize': 14},
    'horizontalAlignment': 'CENTER',
    'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8}
})

# Column headers (row 5) - bold, background color
worksheet.format('A5:H5', {
    'textFormat': {'bold': True, 'fontSize': 11},
    'horizontalAlignment': 'CENTER',
    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
})

# Section headers (rows with "SHEET" or "BIGQUERY" in col A) - bold, colored
for i, row in enumerate(all_data, start=1):
    if row and len(row[0]) > 0 and any(keyword in row[0].upper() for keyword in ['SHEET', 'BIGQUERY', 'CALCULATION', 'SYSTEM']):
        worksheet.format(f'A{i}:H{i}', {
            'textFormat': {'bold': True, 'fontSize': 12},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.7}
        })

# Set column widths using batch_update
column_widths = [
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1, 'pixelSize': 200},   # A
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2, 'pixelSize': 250},   # B
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3, 'pixelSize': 350},   # C
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 4, 'pixelSize': 100},   # D
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 5, 'pixelSize': 200},   # E
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 5, 'endIndex': 6, 'pixelSize': 150},   # F
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 7, 'pixelSize': 250},   # G
    {'sheetId': worksheet.id, 'dimension': 'COLUMNS', 'startIndex': 7, 'endIndex': 8, 'pixelSize': 200},   # H
]

requests = []
for col_width in column_widths:
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': col_width['sheetId'],
                'dimension': col_width['dimension'],
                'startIndex': col_width['startIndex'],
                'endIndex': col_width['endIndex']
            },
            'properties': {'pixelSize': col_width['pixelSize']},
            'fields': 'pixelSize'
        }
    })

worksheet.spreadsheet.batch_update({'requests': requests})

# Freeze header rows
worksheet.freeze(rows=5, cols=1)

print("✅ DATA DICTIONARY sheet created successfully!")
print(f"📊 Total entries: {len(all_data)}")
print(f"🔗 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
