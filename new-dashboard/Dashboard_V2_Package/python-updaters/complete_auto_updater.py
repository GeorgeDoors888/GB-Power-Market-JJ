#!/usr/bin/env python3
"""
Dashboard V2 - Complete Auto-Updater
Updates all sheets with live data from BigQuery
"""

import sys
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = 'inner-cinema-credentials.json'

def main():
    print("🔄 Dashboard V2 Auto-Update")
    
    # Connect
    sheets_creds = service_account.Credentials.from_service_account_file(
        SA_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    
    gc = gspread.authorize(sheets_creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    today = datetime.now().date()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Update Dashboard
    dashboard = spreadsheet.worksheet('Dashboard')
    dashboard.update([[f'⏰ Last Updated: {timestamp}']], 'A2')
    
    # Query and update generation data
    gen_query = f"""
    SELECT 
        fuelType,
        ROUND(SUM(generation)/1000, 2) as total_gw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{today}'
    GROUP BY fuelType
    ORDER BY total_gw DESC
    LIMIT 20
    """
    
    gen_df = bq_client.query(gen_query).to_dataframe()
    
    if not gen_df.empty:
        gen_data = []
        for _, row in gen_df.iterrows():
            gen_data.append([row['fuelType'], f"{row['total_gw']:.1f} GW"])
        
        dashboard.update(gen_data, 'A10')
        print(f"✅ Updated {len(gen_data)} fuel types")
    
    print("✅ Update complete!")
    return True

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
