"""
Format GSP Data into Two Side-by-Side Tables
- Generation Table (Exporting GSPs)
- Demand Table (Importing GSPs)
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd
from datetime import datetime
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BQ_CREDS_FILE = "inner-cinema-credentials.json"
DASHBOARD_SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# GSP Name Mapping
GSP_NAMES = {
    '_A': 'Northern Scotland', '_B': 'Southern Scotland', '_C': 'North West England',
    '_D': 'North East England', '_E': 'Yorkshire', '_F': 'North Wales & Mersey',
    '_G': 'East Midlands', '_H': 'West Midlands', '_J': 'Eastern England',
    '_K': 'South Wales', '_L': 'South West England', '_M': 'Southern England',
    '_N': 'London', '_P': 'South East England',
    'B1': 'Northern Scotland', 'B2': 'Southern Scotland', 'B3': 'North West',
    'B4': 'North East', 'B5': 'Yorkshire', 'B6': 'N Wales & Mersey',
    'B7': 'East Midlands', 'B8': 'West Midlands', 'B9': 'East Anglia',
    'B10': 'South Wales', 'B11': 'South West', 'B12': 'Southern',
    'B13': 'South East', 'B14': 'London', 'B15': 'South Coast',
    'B16': 'Birmingham', 'B17': 'Manchester', 'N': 'London Core'
}

def fetch_gsp_data():
    """Fetch latest GSP data from BigQuery"""
    logger.info("🔍 Fetching latest GSP data from BigQuery...")
    
    bq_credentials = service_account.Credentials.from_service_account_file(BQ_CREDS_FILE)
    client = bigquery.Client(credentials=bq_credentials, project=PROJECT_ID)
    
    query = f"""
    WITH latest_wind AS (
      SELECT generation AS wind_generation_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE fuelType = 'WIND'
      ORDER BY publishTime DESC
      LIMIT 1
    ),
    latest_gsp_time AS (
      SELECT MAX(publishTime) as max_time
      FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris`
    ),
    latest_gsp AS (
      SELECT 
        g.publishTime,
        g.boundary AS gsp_id, 
        AVG(g.demand) AS import_export_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris` g
      CROSS JOIN latest_gsp_time t
      WHERE g.publishTime = t.max_time
      GROUP BY g.publishTime, g.boundary
    )
    SELECT
      g.publishTime,
      g.gsp_id,
      ROUND(g.import_export_mw, 1) as import_export_mw,
      ROUND(w.wind_generation_mw, 1) as wind_generation_mw
    FROM latest_gsp g
    CROSS JOIN latest_wind w
    ORDER BY g.import_export_mw;
    """
    
    df = client.query(query).to_dataframe()
    
    # Add friendly names
    df['gsp_name'] = df['gsp_id'].map(GSP_NAMES).fillna(df['gsp_id'])
    
    # Add formatted columns
    df['import_export_formatted'] = df['import_export_mw'].apply(lambda x: f"{x:,.1f} MW")
    df['wind_formatted'] = df['wind_generation_mw'].apply(lambda x: f"{x:,.0f} MW")
    
    # Add status emoji
    def get_status(mw):
        if mw < -1000:
            return '🔴 Major Import'
        elif mw < -100:
            return '🟠 Import'
        elif mw < 100:
            return '⚪ Balanced'
        elif mw < 1000:
            return '🟢 Export'
        else:
            return '🟢 Major Export'
    
    df['status'] = df['import_export_mw'].apply(get_status)
    
    logger.info(f"✅ Retrieved {len(df)} GSPs at {df['publishTime'].iloc[0]}")
    
    return df

def create_dual_tables(df):
    """Create two separate tables: Generation (Export) and Demand (Import)"""
    
    # Split into exporters and importers
    exporters = df[df['import_export_mw'] > 0].copy()
    importers = df[df['import_export_mw'] < 0].copy()
    
    # Sort: exporters by highest export, importers by highest import
    exporters = exporters.sort_values('import_export_mw', ascending=False)
    importers = importers.sort_values('import_export_mw')
    
    # Create formatted tables
    generation_table = exporters[['gsp_id', 'gsp_name', 'import_export_formatted', 'wind_formatted', 'status']].copy()
    generation_table.columns = ['GSP', 'Name', 'Export', 'Wind', 'Status']
    
    demand_table = importers[['gsp_id', 'gsp_name', 'import_export_formatted', 'wind_formatted', 'status']].copy()
    demand_table.columns = ['GSP', 'Name', 'Import', 'Wind', 'Status']
    
    return generation_table, demand_table

def update_google_sheets(generation_table, demand_table, timestamp):
    """Update Google Sheets with dual-table format"""
    logger.info("📝 Updating Google Sheets with dual-table format...")
    
    gc_credentials = service_account.Credentials.from_service_account_file(
        BQ_CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets', 
                'https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(gc_credentials)
    
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    
    # Create or get GSP Display worksheet
    try:
        ws = spreadsheet.worksheet("GSP Display")
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="GSP Display", rows=100, cols=20)
    
    # Write headers
    ws.update('A1', [[f'🌬️ GSP ANALYSIS - Last Updated: {timestamp}']], value_input_option='RAW')
    
    # GENERATION TABLE (Left side)
    ws.update('A3', [['⚡ GENERATION (Exporting GSPs)']], value_input_option='RAW')
    if not generation_table.empty:
        set_with_dataframe(ws, generation_table, row=4, col=1, include_index=False, include_column_header=True)
        logger.info(f"✅ Generation table: {len(generation_table)} exporting GSPs")
    else:
        ws.update('A5', [['No exporting GSPs at this time']], value_input_option='RAW')
        logger.info("⚠️ No exporting GSPs found")
    
    # DEMAND TABLE (Right side)
    col_offset = 8  # Column H
    ws.update('H3', [['🔌 DEMAND (Importing GSPs)']], value_input_option='RAW')
    if not demand_table.empty:
        set_with_dataframe(ws, demand_table, row=4, col=col_offset, include_index=False, include_column_header=True)
        logger.info(f"✅ Demand table: {len(demand_table)} importing GSPs")
    
    # Format headers
    ws.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
    })
    ws.format('A3:E3', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.4, 'green': 0.8, 'blue': 0.4}
    })
    ws.format('H3:L3', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.4, 'blue': 0.4}
    })
    
    # Bold table headers
    ws.format('A4:E4', {'textFormat': {'bold': True}})
    ws.format('H4:L4', {'textFormat': {'bold': True}})
    
    logger.info(f"🔗 View at: {spreadsheet.url}")
    
    return spreadsheet.url

def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("🌬️ GSP DUAL-TABLE DISPLAY - Starting")
    logger.info("=" * 80)
    
    try:
        # Fetch data
        df = fetch_gsp_data()
        
        # Create dual tables
        generation_table, demand_table = create_dual_tables(df)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Print to console
        logger.info("\n" + "=" * 80)
        logger.info("⚡ GENERATION (EXPORTING GSPs)")
        logger.info("=" * 80)
        if not generation_table.empty:
            logger.info(generation_table.to_string(index=False))
        else:
            logger.info("No exporting GSPs at this time")
        
        logger.info("\n" + "=" * 80)
        logger.info("🔌 DEMAND (IMPORTING GSPs)")
        logger.info("=" * 80)
        logger.info(demand_table.to_string(index=False))
        
        # Update Google Sheets
        url = update_google_sheets(generation_table, demand_table, timestamp)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ DUAL-TABLE DISPLAY - Complete")
        logger.info(f"🟢 Exporting: {len(generation_table)} GSPs")
        logger.info(f"🔴 Importing: {len(demand_table)} GSPs")
        logger.info(f"🔗 View: {url}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
