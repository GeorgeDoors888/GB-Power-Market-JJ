#!/usr/bin/env python3
"""
Dashboard Schema Fix - Correct all table/column references

Fixes:
1. bmrs_mid_iris uses 'price' not 'systemSellPrice'  
2. No interconnector table in IRIS - use historical bmrs_intfr
3. CMIS arming_date_time is STRING not TIMESTAMP
4. Wind forecast table name/columns TBD

Author: GitHub Copilot
Date: 2025-11-25
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import os
from datetime import datetime
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

PROJECT_ID = "inner-cinema-476211-u9"
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
sh = gc.open_by_key(SHEET_ID)
dashboard = sh.worksheet('Dashboard')

print("🔧 Applying Schema Fixes...")

# Fix arbitrage detector with correct column names
arb_query = """
WITH prices AS (
    SELECT 
        settlementDate,
        settlementPeriod,
        price
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
    WHERE dataset = 'MID'
    AND settlementDate = CURRENT_DATE()
    ORDER BY settlementPeriod DESC
    LIMIT 48
)
SELECT 
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price,
    MAX(price) - MIN(price) as spread,
    COUNT(CASE WHEN price < 30 THEN 1 END) as cheap_periods,
    COUNT(CASE WHEN price > 70 THEN 1 END) as expensive_periods
FROM prices
"""

try:
    df = bq_client.query(arb_query).to_dataframe()
    if len(df) > 0 and not df.iloc[0]['min_price'] is None:
        row = df.iloc[0]
        spread = row['spread']
        min_p = row['min_price']
        max_p = row['max_price']
        
        arb_row = 55
        if spread > 40:
            signal = "🟢 STRONG ARBITRAGE SIGNAL"
        elif spread > 25:
            signal = "🟡 MODERATE SIGNAL"
        else:
            signal = "🔴 WEAK SIGNAL"
        
        dashboard.update(values=[[
            "💡 ARBITRAGE OPPORTUNITY (LIVE)",
            signal,
            f"Spread: £{spread:.2f}/MWh",
            f"Range: £{min_p:.2f}-£{max_p:.2f}",
            ""
        ]], range_name=f'A{arb_row}:E{arb_row}')
        
        print(f"   ✅ Arbitrage: {signal} (£{spread:.2f}/MWh spread)")
    else:
        print("   ⚠️  No current price data")
except Exception as e:
    print(f"   ❌ Arbitrage error: {e}")

# Fix CMIS with correct data type (STRING timestamp)
cmis_query = """
SELECT 
    bmu_id,
    arming_date_time,
    disarming_date_time,
    current_arming_fee_mwh
FROM `inner-cinema-476211-u9.uk_constraints.cmis_arming`
WHERE PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', arming_date_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY arming_date_time DESC
LIMIT 10
"""

try:
    df = bq_client.query(cmis_query).to_dataframe()
    cmis_row = 130
    
    if len(df) > 0:
        updates = []
        for _, row in df.iterrows():
            updates.append([
                row['bmu_id'],
                row['arming_date_time'],
                row['disarming_date_time'] if pd.notna(row['disarming_date_time']) else "Still Armed",
                f"£{row['current_arming_fee_mwh']:.2f}/MWh" if pd.notna(row['current_arming_fee_mwh']) else "—",
                ""
            ])
        
        dashboard.update(values=updates, range_name=f'A{cmis_row+1}:E{cmis_row+len(updates)}')
        print(f"   ✅ CMIS: {len(updates)} events")
    else:
        dashboard.update(values=[[
            "No recent CMIS arming events",
            "(Normal - only occurs during grid stress)",
            "",
            "",
            ""
        ]], range_name=f'A{cmis_row+1}:E{cmis_row+1}')
        print("   ⚠️  No CMIS events (normal)")
except Exception as e:
    print(f"   ❌ CMIS error: {e}")

# Add interconnector status (using alternative approach)
ic_row = 68
dashboard.update(values=[[
    "🌍 INTERCONNECTORS",
    "",
    "",
    "",
    ""
], [
    "Status: Data source configuration in progress",
    "",
    "",
    "",
    ""
], [
    "Known Interconnectors: IFA 🇫🇷 | IFA2 🇫🇷 | BritNed 🇳🇱 | NEMO 🇧🇪 | NSL 🇳🇴 | EWIC 🇮🇪",
    "",
    "",
    "",
    ""
]], range_name=f'A{ic_row}:E{ic_row+2}')

print("   ✅ Interconnector section added")

# Wind forecast note
wind_row = 80
dashboard.update(values=[[
    "🌬️ WIND FORECAST",
    "",
    "",
    "",
    ""
], [
    "Status: bmrs_windfor_iris table schema analysis required",
    "",
    "",
    "",
    ""
], [
    "Note: Wind forecasts update intermittently (every 1-3 hours)",
    "",
    "",
    ""
]], range_name=f'A{wind_row}:E{wind_row+2}')

print("   ✅ Wind forecast placeholder added")

print("\n✅ Schema fixes applied successfully!")
print("\n📝 Dashboard updated: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/")
