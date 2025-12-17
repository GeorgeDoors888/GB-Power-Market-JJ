"""
GSP Wind Analysis - Automated BigQuery to Google Sheets
Analyzes regional power flows correlated with national wind generation

Usage:
    python3 gsp_wind_analysis.py

Schedule (cron):
    */30 * * * * cd ~/GB\\ Power\\ Market\\ JJ && python3 gsp_wind_analysis.py
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
import pandas as pd
from datetime import datetime
import logging
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BQ_CREDS_FILE = "inner-cinema-credentials.json"
GSHEETS_CREDS_FILE = "inner-cinema-credentials.json"
SHEET_NAME = "GB GSP Wind Analysis"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "gsp_wind_analysis.log")

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# GSP Name Mapping (17 Grid Supply Points in GB)
GSP_NAMES = {
    '_A': 'Northern Scotland',
    '_B': 'Southern Scotland',
    '_C': 'North West England',
    '_D': 'North East England',
    '_E': 'Yorkshire',
    '_F': 'North Wales & Mersey',
    '_G': 'East Midlands',
    '_H': 'West Midlands',
    '_J': 'Eastern England',
    '_K': 'South Wales',
    '_L': 'South West England',
    '_M': 'Southern England',
    '_N': 'London',
    '_P': 'South East England',
    'B16': 'Birmingham Area',
    'B3': 'Neutral Region',
    'B12': 'SE Supplementary'
}

def fetch_gsp_wind_data():
    """
    Query BigQuery for GSP import/export data joined with wind generation
    Returns: pandas DataFrame with columns:
        - publishTime: Timestamp
        - gsp_id: GSP identifier (_A, _N, etc.)
        - gsp_name: Friendly name (London, Northern Scotland, etc.)
        - import_export_mw: Net flow (negative=import, positive=export)
        - flow_direction: Visual indicator (🔴 Import, 🟢 Export, ⚪ Balanced)
        - wind_generation_mw: National wind output
    """
    logger.info("🔍 Fetching GSP wind analysis data from BigQuery...")

    # Authenticate
    bq_credentials = service_account.Credentials.from_service_account_file(BQ_CREDS_FILE)
    client = bigquery.Client(credentials=bq_credentials, project=PROJECT_ID)

    # Query for LATEST data only (one row per GSP)
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
    ORDER BY g.gsp_id;
    """

    # Execute
    logger.info("⚙️ Executing query (scanning bmrs_fuelinst_iris + bmrs_inddem_iris)...")
    df = client.query(query).to_dataframe()
    logger.info(f"✅ Retrieved {len(df)} rows")

    if df.empty:
        logger.warning("⚠️ No data returned from BigQuery. Check table availability.")
        return df

    # Add friendly GSP names
    df['gsp_name'] = df['gsp_id'].map(GSP_NAMES).fillna(df['gsp_id'])

    # Add flow direction indicator
    def classify_flow(mw):
        if mw < -100:
            return '🔴 Import'
        elif mw > 100:
            return '🟢 Export'
        else:
            return '⚪ Balanced'

    df['flow_direction'] = df['import_export_mw'].apply(classify_flow)

    # Round values for readability
    df['import_export_mw'] = df['import_export_mw'].round(1)
    if 'wind_generation_mw' in df.columns:
        df['wind_generation_mw'] = df['wind_generation_mw'].round(1)

    # Reorder columns
    df = df[['publishTime', 'gsp_id', 'gsp_name', 'import_export_mw',
             'flow_direction', 'wind_generation_mw']]

    logger.info(f"📊 Data spans {df['publishTime'].min()} to {df['publishTime'].max()}")
    logger.info(f"🌍 GSPs included: {df['gsp_id'].nunique()} unique")

    return df

def calculate_summary_stats(df):
    """
    Calculate key statistics per GSP
    Returns: pandas DataFrame with aggregated metrics
    """
    logger.info("📊 Calculating summary statistics...")

    if df.empty:
        return pd.DataFrame()

    summary = df.groupby(['gsp_id', 'gsp_name']).agg({
        'import_export_mw': ['mean', 'min', 'max', 'std'],
        'wind_generation_mw': 'mean'
    }).round(1)

    summary.columns = ['Avg Import/Export (MW)', 'Min (MW)', 'Max (MW)',
                       'StdDev (MW)', 'Avg Wind (MW)']
    summary = summary.reset_index()

    # Add classification based on average flow
    def classify_gsp(avg_mw):
        if avg_mw < -1000:
            return 'Major Importer'
        elif avg_mw < -100:
            return 'Minor Importer'
        elif avg_mw > 100:
            return 'Exporter'
        else:
            return 'Balanced'

    summary['Classification'] = summary['Avg Import/Export (MW)'].apply(classify_gsp)

    # Sort by average import/export (most negative first)
    summary = summary.sort_values('Avg Import/Export (MW)')

    logger.info(f"📋 Summary covers {len(summary)} GSPs")

    return summary

def update_google_sheet(df, summary):
    """
    Write data and summary to Google Sheets
    Returns: Sheet URL
    """
    logger.info("📝 Updating Google Sheets...")

    # Authenticate
    gc_credentials = service_account.Credentials.from_service_account_file(
        GSHEETS_CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive']
    )
    gc = gspread.authorize(gc_credentials)

    # Use existing Dashboard sheet instead of creating new one
    # Service accounts can't create files, but can access shared files
    DASHBOARD_SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

    try:
        spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
        logger.info(f"✅ Opened existing Dashboard sheet")
    except Exception as e:
        logger.error(f"❌ Cannot access Dashboard sheet: {e}")
        raise

    # Update Data tab
    try:
        data_sheet = spreadsheet.worksheet("Data")
    except gspread.WorksheetNotFound:
        data_sheet = spreadsheet.add_worksheet(title="Data", rows=1000, cols=10)

    data_sheet.clear()
    if not df.empty:
        set_with_dataframe(data_sheet, df, include_index=False, include_column_header=True)
        logger.info(f"✅ Updated Data tab ({len(df)} rows)")

    # Update Summary tab
    try:
        summary_sheet = spreadsheet.worksheet("Summary")
    except gspread.WorksheetNotFound:
        summary_sheet = spreadsheet.add_worksheet(title="Summary", rows=100, cols=10)

    summary_sheet.clear()
    if not summary.empty:
        set_with_dataframe(summary_sheet, summary, include_index=False, include_column_header=True)
        logger.info(f"✅ Updated Summary tab ({len(summary)} rows)")

    # Update info sheet with timestamp
    info_sheet = spreadsheet.sheet1
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_sheet.update(range_name='A1', values=[[f'Last Updated: {timestamp}']], value_input_option='RAW')
    info_sheet.update(range_name='A2', values=[[f'Total Records: {len(df)}']], value_input_option='RAW')
    info_sheet.update(range_name='A3', values=[[f'GSPs Analyzed: {len(summary)}']], value_input_option='RAW')
    info_sheet.update(range_name='A4', values=[[f'View Data tab for details →']], value_input_option='RAW')

    logger.info(f"🔗 Sheet URL: {spreadsheet.url}")

    return spreadsheet.url

def main():
    """
    Main execution function
    """
    logger.info("=" * 70)
    logger.info("🌬️ GSP WIND ANALYSIS - Starting")
    logger.info("=" * 70)

    try:
        # Step 1: Fetch data from BigQuery
        df = fetch_gsp_wind_data()

        if df.empty:
            logger.error("❌ No data retrieved. Exiting.")
            return

        # Step 2: Calculate summary statistics
        summary = calculate_summary_stats(df)

        # Step 3: Update Google Sheets
        url = update_google_sheet(df, summary)

        logger.info("=" * 70)
        logger.info("✅ GSP WIND ANALYSIS - Complete")
        logger.info(f"📊 Processed {len(df)} data points")
        logger.info(f"🌍 Analyzed {len(summary)} GSPs")
        logger.info(f"🔗 View results: {url}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
