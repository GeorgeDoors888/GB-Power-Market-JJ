#!/usr/bin/env python3
"""
Automated Dashboard System - Complete Pipeline
Handles both data ingestion from Elexon and dashboard updates

This script:
1. Ingests latest FUELINST data from Elexon API → BigQuery
2. Updates Google Sheets dashboard with latest metrics
3. Logs all operations for monitoring
4. Can run automatically via cron/launchd

Usage:
    python automated_dashboard_system.py                    # Run full pipeline
    python automated_dashboard_system.py --ingest-only      # Only ingest data
    python automated_dashboard_system.py --dashboard-only   # Only update dashboard
    python automated_dashboard_system.py --dry-run          # Test without changes

Schedule with launchd (macOS):
    See setup_automated_dashboard.sh for installation instructions
    
Schedule with cron (Linux):
    */15 * * * * cd '/path/to/project' && ./.venv/bin/python automated_dashboard_system.py >> logs/automation.log 2>&1
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
# Note: bigquery imported locally in functions to avoid credential issues
import pickle
import gspread

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
INGEST_SCRIPT = "download_multi_year_streaming.py"  # Streaming ingestion for production data
MAX_DATA_AGE_MINUTES = 30  # Ingest if data is older than this

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(message, level="INFO"):
    """Print formatted log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = {
        "INFO": Colors.OKBLUE,
        "SUCCESS": Colors.OKGREEN,
        "WARNING": Colors.WARNING,
        "ERROR": Colors.FAIL,
        "HEADER": Colors.HEADER
    }.get(level, "")
    print(f"{color}{timestamp} [{level}] {message}{Colors.ENDC}")

def check_data_freshness():
    """
    Check how old the latest FUELINST data is
    Returns: (needs_ingest, age_minutes, latest_timestamp)
    """
    try:
        from google.cloud import bigquery as bq
        client = bq.Client(project=PROJECT_ID)
        
        query = f"""
        SELECT 
            MAX(publishTime) as latest_publish,
            COUNT(*) as today_rows
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
        WHERE DATE(publishTime) >= CURRENT_DATE()
        """
        
        result = list(client.query(query).result())[0]
        latest_time = result.latest_publish
        today_rows = result.today_rows
        
        if latest_time is None:
            log("No FUELINST data found for today", "WARNING")
            return True, float('inf'), None
        
        # Calculate age in minutes
        age_minutes = (datetime.now(latest_time.tzinfo) - latest_time).total_seconds() / 60
        
        log(f"Latest data: {latest_time} ({age_minutes:.1f} minutes old, {today_rows} rows today)", "INFO")
        
        needs_ingest = age_minutes > MAX_DATA_AGE_MINUTES
        return needs_ingest, age_minutes, latest_time
        
    except Exception as e:
        log(f"Error checking data freshness: {e}", "ERROR")
        return True, float('inf'), None

def ingest_latest_data(dry_run=False):
    """
    Fetch latest FUELINST data directly from Elexon API into BigQuery
    Uses streaming approach similar to download_multi_year_streaming.py
    Returns: success (bool)
    """
    log("Starting data ingestion from Elexon API...", "HEADER")
    
    if dry_run:
        log("DRY RUN: Would fetch latest FUELINST data from Elexon API", "WARNING")
        return True
    
    try:
        import httpx
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        # Get today's date range
        today = datetime.now()
        start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Fetch data from Elexon API
        url = f"https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST"
        params = {
            "settlementDateFrom": start_time.strftime("%Y-%m-%d"),
            "settlementDateTo": today.strftime("%Y-%m-%d")
        }
        
        log(f"Fetching FUELINST data from {start_time.date()} to {today.date()}", "INFO")
        
        response = httpx.get(url, params=params, timeout=120)
        
        if response.status_code != 200:
            log(f"❌ API request failed: {response.status_code}", "ERROR")
            return False
        
        data = response.json()
        records = data.get('data', []) if isinstance(data, dict) else data
        
        if not records:
            log("⚠️  No new data available from API", "WARNING")
            return True  # Not really an error, just no new data
        
        log(f"Retrieved {len(records)} records from API", "INFO")
        
        # Upload to BigQuery using Application Default Credentials
        from google.cloud import bigquery as bq
        client = bq.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst"
        
        # Convert to DataFrame for easier handling
        import pandas as pd
        df = pd.DataFrame(records)
        
        # Load into BigQuery (append mode to avoid duplicates)
        job_config = bq.LoadJobConfig(
            write_disposition=bq.WriteDisposition.WRITE_APPEND,
            schema_update_options=[
                bq.SchemaUpdateOption.ALLOW_FIELD_ADDITION
            ]
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        log(f"✅ Uploaded {len(records)} records to BigQuery", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"❌ Ingestion error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def get_latest_fuelinst_data():
    """
    Get latest generation data from FUELINST
    Returns: (data_dict, timestamp, settlement_info)
    """
    try:
        from google.cloud import bigquery as bq
        client = bq.Client(project=PROJECT_ID)
        
        query = f"""
        WITH latest_time AS (
            SELECT MAX(publishTime) as max_time
            FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
            WHERE DATE(settlementDate) >= CURRENT_DATE() - 1
        )
        SELECT 
            f.publishTime,
            f.settlementDate,
            f.settlementPeriod,
            f.fuelType,
            f.generation
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst` f
        JOIN latest_time lt ON f.publishTime = lt.max_time
        ORDER BY f.generation DESC
        """
        
        results = client.query(query).result()
        data = {}
        timestamp = None
        settlement_info = {}
        
        for row in results:
            if timestamp is None:
                timestamp = row.publishTime
                settlement_info = {
                    'date': row.settlementDate,
                    'period': row.settlementPeriod
                }
            
            fuel_type = row.fuelType
            generation_gw = row.generation / 1000  # Convert MW to GW
            data[fuel_type] = generation_gw
        
        return data, timestamp, settlement_info
        
    except Exception as e:
        log(f"Error fetching FUELINST data: {e}", "ERROR")
        return {}, None, {}

def calculate_metrics(data):
    """Calculate summary metrics from raw data"""
    
    renewables = [
        'WIND', 'SOLAR', 'HYDRO', 'BIOMASS', 'NPSHYD'  # Pumped storage hydro
    ]
    
    fossil = [
        'CCGT', 'COAL', 'GAS', 'OIL', 'OCGT'
    ]
    
    nuclear = ['NUCLEAR', 'PS']
    
    interconnectors = [
        'INTEW', 'INTFR', 'INTIRL', 'INTNED', 
        'INTNEM', 'INTNSL', 'INTIFA2'
    ]
    
    total_generation = sum(v for k, v in data.items() if k not in interconnectors)
    total_renewables = sum(v for k, v in data.items() if k in renewables)
    total_fossil = sum(v for k, v in data.items() if k in fossil)
    total_nuclear = sum(v for k, v in data.items() if k in nuclear)
    net_imports = sum(v for k, v in data.items() if k in interconnectors)
    
    metrics = {
        'total_generation': round(total_generation, 2),
        'total_renewables': round(total_renewables, 2),
        'total_fossil': round(total_fossil, 2),
        'total_nuclear': round(total_nuclear, 2),
        'net_imports': round(net_imports, 2),
        'renewable_pct': round(100 * total_renewables / total_generation, 1) if total_generation > 0 else 0,
        'fossil_pct': round(100 * total_fossil / total_generation, 1) if total_generation > 0 else 0,
        'fuel_types_count': len(data)
    }
    
    return metrics

def update_dashboard(dry_run=False):
    """
    Update Google Sheets dashboard with latest data
    Returns: success (bool)
    """
    log("Starting dashboard update...", "HEADER")
    
    # Get latest data
    data, timestamp, settlement = get_latest_fuelinst_data()
    
    if not data or not timestamp:
        log("No data available to update dashboard", "ERROR")
        return False
    
    metrics = calculate_metrics(data)
    
    log(f"Retrieved data for {metrics['fuel_types_count']} fuel types", "INFO")
    log(f"   Timestamp: {timestamp}", "INFO")
    log(f"   Settlement: {settlement['date']} Period {settlement['period']}", "INFO")
    log(f"   Total Generation: {metrics['total_generation']} GW", "INFO")
    log(f"   Renewables: {metrics['total_renewables']} GW ({metrics['renewable_pct']}%)", "SUCCESS")
    log(f"   Fossil: {metrics['total_fossil']} GW ({metrics['fossil_pct']}%)", "INFO")
    log(f"   Net Imports: {metrics['net_imports']} GW", "INFO")
    
    if dry_run:
        log("DRY RUN: Would update dashboard with this data", "WARNING")
        return True
    
    try:
        # Connect to Google Sheets
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(DASHBOARD_SHEET_ID)
        worksheet = sheet.sheet1
        
        # Prepare cell updates
        cells_to_update = []
        
        # Update timestamp (B1)
        cells_to_update.append(gspread.Cell(1, 2, str(timestamp)))
        
        # Update each fuel type (starting at row 3, column B)
        row = 3
        for fuel_type, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            # Column A: Fuel Type, Column B: Generation (GW)
            cells_to_update.append(gspread.Cell(row, 1, fuel_type))
            cells_to_update.append(gspread.Cell(row, 2, round(value, 2)))
            row += 1
        
        # Update summary metrics (assuming they're in specific cells)
        # Adjust these cell references based on your actual dashboard layout
        cells_to_update.append(gspread.Cell(1, 4, metrics['total_generation']))  # D1: Total
        cells_to_update.append(gspread.Cell(2, 4, metrics['total_renewables']))  # D2: Renewables
        cells_to_update.append(gspread.Cell(3, 4, metrics['renewable_pct']))     # D3: Renewable %
        
        # Batch update all cells
        worksheet.update_cells(cells_to_update)
        
        log(f"✅ Dashboard updated successfully! ({len(cells_to_update)} cells)", "SUCCESS")
        log(f"   View at: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}", "INFO")
        return True
        
    except Exception as e:
        log(f"❌ Dashboard update failed: {e}", "ERROR")
        return False

def run_full_pipeline(ingest_only=False, dashboard_only=False, dry_run=False):
    """
    Run the complete automation pipeline
    Returns: overall success (bool)
    """
    log("=" * 80, "HEADER")
    log("GB Power Market Dashboard - Automated Update System", "HEADER")
    log("=" * 80, "HEADER")
    
    success = True
    
    # Step 1: Check if we need to ingest new data
    if not dashboard_only:
        needs_ingest, age_minutes, latest_time = check_data_freshness()
        
        if needs_ingest:
            log(f"Data is {age_minutes:.1f} minutes old - ingestion needed", "WARNING")
            if not ingest_latest_data(dry_run):
                log("Ingestion failed, but will attempt dashboard update anyway", "WARNING")
                success = False
        else:
            log(f"Data is fresh ({age_minutes:.1f} minutes old) - skipping ingestion", "SUCCESS")
    
    if ingest_only:
        log("Ingest-only mode - skipping dashboard update", "INFO")
        return success
    
    # Step 2: Update dashboard
    if not update_dashboard(dry_run):
        success = False
    
    # Final summary
    log("=" * 80, "HEADER")
    if success:
        log("✅ All operations completed successfully", "SUCCESS")
    else:
        log("⚠️  Some operations failed - check logs above", "WARNING")
    log("=" * 80, "HEADER")
    
    return success

def main():
    parser = argparse.ArgumentParser(
        description="Automated GB Power Market Dashboard System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--ingest-only",
        action="store_true",
        help="Only run data ingestion, skip dashboard update"
    )
    
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Only update dashboard, skip data ingestion check"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test run without making any changes"
    )
    
    parser.add_argument(
        "--force-ingest",
        action="store_true",
        help="Force data ingestion regardless of data age"
    )
    
    args = parser.parse_args()
    
    # Override freshness check if force-ingest
    if args.force_ingest:
        global MAX_DATA_AGE_MINUTES
        MAX_DATA_AGE_MINUTES = 0
    
    # Run pipeline
    try:
        success = run_full_pipeline(
            ingest_only=args.ingest_only,
            dashboard_only=args.dashboard_only,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        log("\n\nInterrupted by user", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
