"""
Add GSP Dual-Table Display to Main Dashboard Tab
Adds below existing content (starting at row 55)
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd
from datetime import datetime
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BQ_CREDS_FILE = "inner-cinema-credentials.json"
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

# GSP row positions on Dashboard tab
GSP_START_ROW = 55  # Start AFTER outages section (which ends around row 50)
GENERATION_COL = 1  # Column A
DEMAND_COL = 8      # Column H

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# GSP Name Mapping
GSP_NAMES = {
    'B1': 'Northern Scotland', 'B2': 'Southern Scotland', 'B3': 'North West',
    'B4': 'North East', 'B5': 'Yorkshire', 'B6': 'N Wales & Mersey',
    'B7': 'East Midlands', 'B8': 'West Midlands', 'B9': 'East Anglia',
    'B10': 'South Wales', 'B11': 'South West', 'B12': 'Southern',
    'B13': 'South East', 'B14': 'London', 'B15': 'South Coast',
    'B16': 'Birmingham', 'B17': 'Manchester', 'N': 'London Core'
}

def fetch_gsp_data():
    """Fetch latest GSP data from BigQuery"""
    logger.info("🔍 Fetching latest GSP data...")
    
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
    df['gsp_name'] = df['gsp_id'].map(GSP_NAMES).fillna(df['gsp_id'])
    
    logger.info(f"✅ Retrieved {len(df)} GSPs at {df['publishTime'].iloc[0]}")
    return df

def format_tables(df):
    """Create formatted generation and demand tables"""
    
    # Split into exporters and importers
    exporters = df[df['import_export_mw'] > 0].copy()
    importers = df[df['import_export_mw'] < 0].copy()
    
    # Sort
    exporters = exporters.sort_values('import_export_mw', ascending=False)
    importers = importers.sort_values('import_export_mw')
    
    # Format for display
    def format_row(row, is_export):
        flow = f"{abs(row['import_export_mw']):,.1f} MW"
        wind = f"{row['wind_generation_mw']:,.0f} MW"
        
        # Status emoji
        abs_mw = abs(row['import_export_mw'])
        if abs_mw > 1000:
            status = '🟢 Major Export' if is_export else '🔴 Major Import'
        elif abs_mw > 100:
            status = '🟢 Export' if is_export else '🟠 Import'
        else:
            status = '⚪ Balanced'
        
        return [row['gsp_id'], row['gsp_name'], flow, wind, status]
    
    generation_data = [format_row(row, True) for _, row in exporters.iterrows()]
    demand_data = [format_row(row, False) for _, row in importers.iterrows()]
    
    return generation_data, demand_data, df['wind_generation_mw'].iloc[0]

def update_dashboard(generation_data, demand_data, wind_mw):
    """Add GSP tables to main Dashboard tab"""
    logger.info("📝 Adding GSP tables to Dashboard...")
    
    gc_credentials = service_account.Credentials.from_service_account_file(
        BQ_CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(gc_credentials)
    
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    dashboard = spreadsheet.worksheet('Dashboard')
    
    current_row = GSP_START_ROW
    
    # Main header
    header_text = f"📊 GSP ANALYSIS | Wind: {wind_mw:,.0f} MW | Updated: {datetime.now().strftime('%H:%M:%S')}"
    dashboard.update(f'A{current_row}', [[header_text]], value_input_option='RAW')
    current_row += 2
    
    # GENERATION TABLE (Left - Columns A-E)
    gen_row = current_row
    dashboard.update(f'A{gen_row}', [['⚡ GENERATION (Exporting GSPs)']], value_input_option='RAW')
    gen_row += 1
    
    # Headers
    gen_headers = [['GSP', 'Name', 'Export', 'Wind', 'Status']]
    dashboard.update(f'A{gen_row}', gen_headers, value_input_option='RAW')
    gen_row += 1
    
    if generation_data:
        dashboard.update(f'A{gen_row}', generation_data, value_input_option='RAW')
        logger.info(f"✅ Generation: {len(generation_data)} exporting GSPs")
    else:
        dashboard.update(f'A{gen_row}', [['No exporting GSPs currently']], value_input_option='RAW')
        logger.info("ℹ️ Generation: No exporters")
    
    # DEMAND TABLE (Right - Columns H-L)
    dem_row = current_row
    dashboard.update(f'H{dem_row}', [['🔌 DEMAND (Importing GSPs)']], value_input_option='RAW')
    dem_row += 1
    
    # Headers
    dem_headers = [['GSP', 'Name', 'Import', 'Wind', 'Status']]
    dashboard.update(f'H{dem_row}', dem_headers, value_input_option='RAW')
    dem_row += 1
    
    if demand_data:
        dashboard.update(f'H{dem_row}', demand_data, value_input_option='RAW')
        logger.info(f"✅ Demand: {len(demand_data)} importing GSPs")
    
    logger.info(f"✅ GSP tables added to Dashboard at row {GSP_START_ROW}")
    logger.info(f"🔗 View: {spreadsheet.url}")
    
    return spreadsheet.url

def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("📊 ADDING GSP TABLES TO MAIN DASHBOARD")
    logger.info("=" * 80)
    
    try:
        df = fetch_gsp_data()
        generation_data, demand_data, wind_mw = format_tables(df)
        
        logger.info(f"\n⚡ Generation: {len(generation_data)} exporting GSPs")
        logger.info(f"🔌 Demand: {len(demand_data)} importing GSPs")
        logger.info(f"🌬️ Wind: {wind_mw:,.0f} MW\n")
        
        url = update_dashboard(generation_data, demand_data, wind_mw)
        
        logger.info("=" * 80)
        logger.info("✅ GSP TABLES ADDED TO DASHBOARD")
        logger.info(f"📍 Location: Row {GSP_START_ROW} on Dashboard tab")
        logger.info(f"🔗 View: {url}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
