#!/usr/bin/env python3
"""
populate_dashboard_tables.py
----------------------------
Populates the live data tables in the V3 Dashboard:
- Fuel Mix & Interconnectors
- Active Outages
"""

import gspread
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread_formatting as gsf

# --- CONFIGURATION ---
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
DASHBOARD_SHEET_NAME = 'Dashboard'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# --- Cell Formatting ---
# Define a basic format for clearing cells
CLEAR_FORMAT = gsf.CellFormat(
    backgroundColor=gsf.Color(1, 1, 1),  # White
    textFormat=gsf.TextFormat(foregroundColor=gsf.Color(0, 0, 0)), # Black
)

def get_gspread_client():
    """Authorize and return gspread client."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def get_bigquery_client():
    """Authorize and return BigQuery client."""
    return bigquery.Client(project=PROJECT_ID)

def populate_fuel_mix_and_ics(sheet, bq_client):
    """Populates the Fuel Mix & Interconnectors tables using efficient batch updates."""
    print("   1. Fetching and populating Fuel Mix & Interconnectors data...")

    query = f"""
        WITH latest_data AS (
            SELECT
                fuelType,
                generation,
                ROW_NUMBER() OVER(PARTITION BY fuelType ORDER BY publishTime DESC) as rn
            FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
            WHERE publishTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 MINUTE)
        )
        SELECT fuelType, generation FROM latest_data WHERE rn = 1;
    """
    
    try:
        df = bq_client.query(query).to_dataframe()

        if df.empty:
            print("   ⚠️ No recent fuel or interconnector data found.")
            sheet.batch_clear(['A11:B21', 'C11:E21'])
            sheet.update('A11', [['No recent fuel data.']])
            return

        fuel_df = df[~df['fuelType'].str.startswith('INT')].sort_values(by='generation', ascending=False).head(8)
        ic_df = df[df['fuelType'].str.startswith('INT')].sort_values(by='fuelType').head(8)
        
        # Prepare data for sheet update
        fuel_update_data = fuel_df[['fuelType', 'generation']].values.tolist()

        ic_df['generation'] = pd.to_numeric(ic_df['generation'])
        ic_df['direction'] = ic_df['generation'].apply(lambda x: '→ Export' if x > 0 else '← Import')
        ic_df['generation'] = ic_df['generation'].abs()
        ic_update_data = ic_df[['fuelType', 'generation', 'direction']].values.tolist()

        # Batch clear previous data and then batch update
        sheet.batch_clear(['A11:B21', 'C11:E21'])
        
        if fuel_update_data:
            sheet.update(range_name='A11', values=fuel_update_data)
        
        if ic_update_data:
            sheet.update(range_name='C11', values=ic_update_data)

        print(f"   ✅ Populated Fuel Mix ({len(fuel_df)} rows) and Interconnectors ({len(ic_df)} rows).")

    except Exception as e:
        print(f"   ❌ Error fetching data for Fuel Mix/ICs: {e}")


def populate_outages(sheet, bq_client):
    """Populates the Active Outages table, now including End Time."""
    print("   2. Fetching and populating Active Outages data...")
    
    outage_query = f"""
        WITH latest_revisions AS (
            SELECT
                affectedUnit,
                MAX(revisionNumber) AS max_rev
            FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
            WHERE eventStatus = 'Active'
            GROUP BY affectedUnit
        )
        SELECT
            u.affectedUnit,
            u.fuelType,
            TIMESTAMP_TRUNC(u.eventStartTime, SECOND) as eventStartTime,
            TIMESTAMP_TRUNC(u.eventEndTime, SECOND) as eventEndTime,
            u.unavailableCapacity
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr ON u.affectedUnit = lr.affectedUnit AND u.revisionNumber = lr.max_rev
        WHERE u.eventStatus = 'Active'
        ORDER BY u.unavailableCapacity DESC
        LIMIT 10;
    """
    
    try:
        outage_df = bq_client.query(outage_query).to_dataframe()
        
        # Format both time columns
        outage_df['eventStartTime'] = pd.to_datetime(outage_df['eventStartTime']).dt.strftime('%Y-%m-%d %H:%M')
        outage_df['eventEndTime'] = pd.to_datetime(outage_df['eventEndTime']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Ensure the columns are in the correct order for the sheet
        update_data = outage_df[['affectedUnit', 'fuelType', 'eventStartTime', 'eventEndTime', 'unavailableCapacity']].values.tolist()

        # Batch clear (now 5 columns) and update
        sheet.batch_clear(['A26:E35'])
        if update_data:
            sheet.update('A26', update_data)
        else:
            sheet.update('A26', [['No active outages found.']])
        
        print(f"   ✅ Populated Active Outages ({len(outage_df)} rows).")

    except Exception as e:
        print(f"   ❌ Error fetching data for Outages: {e}")


def main():
    print("--- Populating Dashboard Live Data Tables ---")
    try:
        gspread_client = get_gspread_client()
        bq_client = get_bigquery_client()
        
        spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)
        dashboard_sheet = spreadsheet.worksheet(DASHBOARD_SHEET_NAME)
        
        populate_fuel_mix_and_ics(dashboard_sheet, bq_client)
        populate_outages(dashboard_sheet, bq_client)
        
        print("--- ✅ All tables updated successfully! ---")
        print(f"\n🔗 View your updated dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard_sheet.id}")

    except Exception as e:
        print(f"\n❌ A critical error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
