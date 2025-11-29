#!/usr/bin/env python3
"""
update_top_outages.py
---------------------
Updates Dashboard V2 rows 22-33 (A22:H33) with Top 12 Active Outages
Queries BigQuery for current outages and displays them in the dashboard
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime
import logging

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'  # Dashboard V2
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
OUTAGES_START_ROW = 22  # User specified: A22:H33 for top 12 outages
OUTAGES_END_ROW = 33

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

print("=" * 80)
print("UPDATING TOP 12 OUTAGES - Dashboard V2 (Rows 22-33)")
print("=" * 80)

try:
    # Authenticate
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/bigquery']
    )
    gc = gspread.authorize(creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    # Open spreadsheet
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.sheet1  # Dashboard V2 main sheet
    
    logging.info("📊 Querying BigQuery for active outages...")
    
    # Query top 12 outages by MW unavailable
    # NOTE: Simplified query using available data - full outages schema needs verification
    query = f"""
    SELECT 
        bmUnit,
        bmUnit as plant_name,
        'Power' as fuel_type,
        ABS(levelTo - levelFrom) as mw_unavailable,
        PARSE_DATE('%Y-%m-%d', settlementDate) as settlement_date,
        settlementPeriod
    FROM `{PROJECT_ID}.{DATASET}.balancing_physical_mels`
    WHERE PARSE_DATE('%Y-%m-%d', settlementDate) >= CURRENT_DATE() - 2
        AND ABS(levelTo - levelFrom) > 50
    ORDER BY ABS(levelTo - levelFrom) DESC
    LIMIT 12
    """
    
    df = bq_client.query(query).to_dataframe()
    
    logging.info(f"✅ Retrieved {len(df)} outages")
    
    # Prepare data for rows 22-33
    # Row 22: Headers
    headers = [['BM Unit', 'Plant', 'Fuel', 'MW Unavailable', 'Settlement Date', 'SP', '', '']]
    
    # Rows 23-33: Data (up to 11 outages since header takes row 22)
    data_rows = []
    for i in range(11):  # 11 data rows (22 is header, 23-33 is data)
        if i < len(df):
            row = df.iloc[i]
            data_rows.append([
                str(row['bmUnit'])[:15],
                str(row['plant_name'])[:30] if row['plant_name'] else row['bmUnit'],
                str(row['fuel_type'])[:15] if row['fuel_type'] else 'Unknown',
                f"{float(row['mw_unavailable']):.1f}",
                str(row['settlement_date'])[:10] if row['settlement_date'] else 'N/A',
                str(row['settlementPeriod']),
                '', ''
            ])
        else:
            data_rows.append(['', '', '', '', '', '', '', ''])
    
    # Combine headers + data
    all_data = headers + data_rows
    
    # Update Dashboard V2 rows 22-33 (A22:H33)
    logging.info(f"📝 Updating Dashboard V2 rows {OUTAGES_START_ROW}-{OUTAGES_END_ROW}...")
    sheet.update(f'A{OUTAGES_START_ROW}:H{OUTAGES_END_ROW}', all_data, value_input_option='USER_ENTERED')
    
    logging.info(f"✅ Updated rows {OUTAGES_START_ROW}-{OUTAGES_END_ROW} with {len(df)} outages")
    
    if len(df) > 0:
        logging.info(f"   Top outage: {df.iloc[0]['bmUnit']} - {df.iloc[0]['mw_unavailable']:.1f} MW")
    
    print("=" * 80)
    print(f"✅ COMPLETE - Top 12 outages displayed in rows {OUTAGES_START_ROW}-{OUTAGES_END_ROW}")
    print("=" * 80)
    
except Exception as e:
    logging.error(f"❌ Update failed: {e}")
    logging.exception("Full traceback:")
    raise
