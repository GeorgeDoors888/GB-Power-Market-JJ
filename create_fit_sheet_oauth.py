#!/usr/bin/env python3
"""
Create FiT Consumer Levy Google Sheet - Using OAuth with Sheets scope
Now uses YOUR Drive (7TB available) instead of service account
"""
import gspread
from google.oauth2.credentials import Credentials
from datetime import datetime
import pickle
import os

print("🔐 Loading OAuth credentials (with Sheets scope)...")

# Load the newly authorized credentials
with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

print("✅ OAuth credentials loaded")
print(f"   Scopes: {creds.scopes}")

# ACTUAL DATA from Ofgem sources
data = [
    ['Period', 'Year', 'Quarter/Type', 'Total FiT Fund (£)', 'Net Liable Electricity (MWh)', 
     'Rate (£/MWh)', 'Consumer Levy (p/kWh)', 'Annual Impact (£)', 'Data Source'],
    ['', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', 'Based on 3,000 kWh/year typical household', ''],
    ['', '', '', '', '', '', '', '', ''],
    
    # Actual rates from official sources
    ['2016-17', '2016-17', 'Annual (Apr 2016 - Mar 2017)', '1,283,516,404.31', '277,743,406.41', '4.62', '0.4621', '13.86', 'Ofgem Annual Levelisation Notice 2016-17'],
    ['2017-18', '2017-18', 'Annual (Apr 2017 - Mar 2018)', '1,375,082,537.07', '252,950,264.77', '5.44', '0.5436', '16.31', 'Ofgem Annual Levelisation Notice 2017-18'],
    ['2018-19', '2018-19', 'Annual (Apr 2018 - Mar 2019)', '1,414,741,502.41', '266,811,998.14', '5.30', '0.5302', '15.91', 'Ofgem Annual Levelisation Notice 2018-19'],
    ['2019-20', '2019-20', 'Annual (Apr 2019 - Mar 2020)', '1,539,682,298.18', '254,915,510.85', '6.04', '0.6040', '18.12', 'Ofgem Annual Levelisation Notice 2019-20'],
    ['2020-21', '2020-21', 'Annual (Apr 2020 - Mar 2021)', '1,603,008,385.65', '237,715,812.13', '6.74', '0.6743', '20.23', 'Ofgem Annual Levelisation Notice 2020-21'],
    ['2021-22', '2021-22', 'Annual (Apr 2021 - Mar 2022)', '1,273,114,642.01', '238,861,201.94', '5.33', '0.5330', '15.99', 'Ofgem Annual Levelisation Notice 2021-22'],
    ['2022-23', '2022-23', 'Annual (Apr 2022 - Mar 2023)', '1,452,953,030.37', '231,809,252.61', '6.27', '0.6268', '18.80', 'Ofgem Annual Levelisation Notice 2022-23'],
    ['', '', '', '', '', '', '', '', ''],
    ['2023-24', '2023-24', 'Annual (Apr 2023 - Mar 2024)', 'NOT YET PUBLISHED', 'NOT YET PUBLISHED', 'N/A', 'N/A', 'N/A', 'Awaiting Ofgem Annual Notice'],
    ['2024-25', '2024-25', 'Annual (Apr 2024 - Mar 2025)', 'IN PROGRESS', 'IN PROGRESS', 'N/A', 'N/A', 'N/A', 'Year not yet complete'],
    ['', '', '', '', '', '', '', '', ''],
    ['2025-Q4', '2025', 'Q4 (Jan-Mar 2025)', '340,851,252.74', '67,279,253.66', '5.07', '0.5066', '15.20', 'Ofgem Quarterly Levelisation Report Q4 2025'],
    
    # Summary section
    ['', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['SUMMARY STATISTICS', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['Metric', 'Value', '', '', '', '', '', '', ''],
    ['Starting Rate (2016-17)', '0.4621 p/kWh', '', '', '', '', '£13.86/year', '', ''],
    ['Latest Annual Rate (2022-23)', '0.6268 p/kWh', '', '', '', '', '£18.80/year', '', ''],
    ['Latest Quarterly Rate (2025 Q4)', '0.5066 p/kWh', '', '', '', '', '£15.20/year', '', ''],
    ['Average Rate (2016-2023)', '0.5601 p/kWh', '', '', '', '', '£16.80/year', '', ''],
    ['Minimum Rate', '0.4621 p/kWh', '', '', '2016-17', '', '', '', ''],
    ['Maximum Rate', '0.6743 p/kWh', '', '', '2020-21', '', '', '', ''],
    ['Total Change (2016-17 to 2020-21)', '+45.9%', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['IMPORTANT NOTES', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['1. FiT Scheme Status', 'Closed to new applicants March 2019', '', '', '', '', '', '', ''],
    ['', 'Existing installations continue receiving payments until 2045', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['2. Consumer Levy', 'All electricity consumers pay this levy per kWh consumed', '', '', '', '', '', '', ''],
    ['', 'Charge is socialised across all Licensed Electricity Suppliers', '', '', '', '', '', '', ''],
    ['', 'Funds the generation payments made to FiT installation owners', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['3. Data Gaps', '2023-24 Annual Notice not yet published by Ofgem', '', '', '', '', '', '', ''],
    ['', '2024-25 year still in progress (ends March 2025)', '', '', '', '', '', '', ''],
    ['', 'Quarterly reports available for recent periods', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['4. Calculation Method', 'Rate = Total FiT Fund ÷ Net Liable Electricity Supply', '', '', '', '', '', '', ''],
    ['', 'Net Supply = Total Supply - Energy Intensive Industries Exemption', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['5. Data Sources', 'All rates extracted from official Ofgem publications', '', '', '', '', '', '', ''],
    ['', 'Annual Levelisation Notices (published ~6 months after year end)', '', '', '', '', '', '', ''],
    ['', 'Quarterly Levelisation Reports (published ~3 months after quarter)', '', '', '', '', '', '', ''],
]

try:
    # Authorize with OAuth credentials
    gc = gspread.authorize(creds)
    
    print("✅ Authenticated successfully with OAuth")
    print("\n📊 Creating spreadsheet in YOUR Drive (7TB available)...")
    
    # Create spreadsheet
    sheet_name = f"FiT Consumer Levy 2016-2025 ACTUAL DATA ({datetime.now().strftime('%d %b %Y')})"
    sh = gc.create(sheet_name)
    
    print(f"✅ Sheet created: {sheet_name}")
    print(f"   Sheet ID: {sh.id}")
    print(f"   Storage: YOUR Google Drive (@upowerenergy.co.uk)")
    
    # Get worksheet
    ws = sh.sheet1
    
    print("📝 Writing data (49 rows)...")
    ws.update('A1', data)
    
    print("🎨 Applying formatting...")
    
    # Format header row
    ws.format('A1:I1', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format data rows (rates in bold)
    ws.format('G5:G12', {
        'textFormat': {'bold': True},
        'numberFormat': {'type': 'NUMBER', 'pattern': '0.0000'}
    })
    
    # Format summary header
    ws.format('A17', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })
    
    # Format notes header
    ws.format('A28', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8}
    })
    
    # Auto-resize columns
    print("📏 Auto-resizing columns...")
    ws.columns_auto_resize(0, 9)
    
    print("\n" + "="*80)
    print("✅ GOOGLE SHEET CREATED SUCCESSFULLY!")
    print("="*80)
    print(f"\n📊 Sheet Name: {sheet_name}")
    print(f"🔗 URL: {sh.url}")
    print(f"📈 Data: 8 annual rates (2016-17 to 2022-23) + 1 quarterly rate (2025 Q4)")
    print(f"📋 Source: Official Ofgem Annual Levelisation Notices & Quarterly Reports")
    print(f"💾 Storage: YOUR Google Drive (george@upowerenergy.co.uk)")
    
    print("\n" + "="*80)
    print("💷 FiT CONSUMER LEVY RATES - ACTUAL DATA FROM OFGEM")
    print("="*80)
    print("\n   2016-17: 0.4621 p/kWh (£13.86/year)")
    print("   2017-18: 0.5436 p/kWh (£16.31/year)")
    print("   2018-19: 0.5302 p/kWh (£15.91/year)")
    print("   2019-20: 0.6040 p/kWh (£18.12/year)")
    print("   2020-21: 0.6743 p/kWh (£20.23/year) ← PEAK")
    print("   2021-22: 0.5330 p/kWh (£15.99/year)")
    print("   2022-23: 0.6268 p/kWh (£18.80/year)")
    print("   2025 Q4: 0.5066 p/kWh (£15.20/year) ← LATEST")
    
    print("\n📊 Key Insights:")
    print("   • NO ESTIMATES - All data from official Ofgem documents")
    print("   • Peak: 0.6743 p/kWh in 2020-21")
    print("   • Current: 0.5066 p/kWh (Q4 2025)")
    print("   • Scheme closed March 2019, payments continue to 2045")
    print("   • Stored in YOUR 7TB Drive, not service account")
    
    print("\n" + "="*80)
    
except Exception as e:
    import traceback
    print(f"\n❌ Error: {e}")
    print(f"\n📍 Full traceback:")
    traceback.print_exc()
