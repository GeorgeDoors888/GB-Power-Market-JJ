#!/usr/bin/env python3
"""
BigQuery to Google Sheets Auto-Updater
Automatically updates Google Sheets when BigQuery data changes
"""

import os
import time
import json
import base64
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import requests

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Railway API endpoint
RAILWAY_API = "https://jibber-jabber-production.up.railway.app"
BEARER_TOKEN = "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Load credentials
def get_bigquery_credentials():
    """Load Google credentials for BigQuery access"""
    creds_file = "inner-cinema-credentials.json"
    
    if not os.path.exists(creds_file):
        raise ValueError(f"BigQuery credentials not found: {creds_file}")
    
    with open(creds_file, 'r') as f:
        return json.load(f)


def get_workspace_credentials():
    """Load Google credentials for Sheets access via domain-wide delegation"""
    creds_file = "workspace-credentials.json"
    
    if not os.path.exists(creds_file):
        # Try loading from environment (Railway)
        creds_b64 = os.environ.get('GOOGLE_WORKSPACE_CREDENTIALS')
        if creds_b64:
            creds_json = base64.b64decode(creds_b64).decode('utf-8')
            creds_dict = json.loads(creds_json)
            return creds_dict
        else:
            raise ValueError(f"Workspace credentials not found: {creds_file}")
    
    with open(creds_file, 'r') as f:
        return json.load(f)


def get_bigquery_client():
    """Create BigQuery client"""
    creds_dict = get_bigquery_credentials()
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    return bigquery.Client(project=PROJECT_ID, credentials=credentials, location="US")


def get_sheets_client():
    """Create gspread client with domain-wide delegation"""
    creds_dict = get_workspace_credentials()
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    ).with_subject('george@upowerenergy.uk')
    
    return gspread.authorize(credentials)


def query_bigquery(sql_query):
    """Query BigQuery and return results as list of dicts"""
    client = get_bigquery_client()
    
    print(f"🔍 Executing query: {sql_query[:100]}...")
    query_job = client.query(sql_query)
    results = query_job.result()
    
    # Convert to list of dicts
    data = []
    for row in results:
        data.append(dict(row.items()))
    
    print(f"✅ Retrieved {len(data)} rows from BigQuery")
    return data


def update_sheet_via_api(worksheet_name, data, range_start="A1"):
    """Update Google Sheet via Railway API"""
    
    if not data:
        print("⚠️  No data to update")
        return
    
    # Convert data (list of dicts) to 2D array
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [[str(row.get(col, '')) for col in headers] for row in data]
        values = [headers] + rows
    else:
        values = data
    
    # Calculate range
    num_rows = len(values)
    num_cols = len(values[0]) if values else 0
    
    # Build range notation (A1:D10 format)
    def col_letter(n):
        """Convert column number to letter (1=A, 27=AA, etc.)"""
        result = ""
        while n > 0:
            n -= 1
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result
    
    end_col = col_letter(num_cols)
    end_row = num_rows
    range_notation = f"{range_start}:{end_col}{end_row}"  # Just A1:D3 (worksheet added in payload)
    
    # Call Railway API
    url = f"{RAILWAY_API}/workspace/write_sheet"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "spreadsheet_id": SPREADSHEET_ID,
        "worksheet_name": worksheet_name,  # Worksheet name separate
        "cell_range": range_notation,      # Range without worksheet name
        "values": values
    }
    
    print(f"📤 Updating '{worksheet_name}' range {range_notation}...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Updated {result.get('updated_cells', 0)} cells in '{worksheet_name}'")
        return result
    else:
        print(f"❌ Error updating sheet: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def update_sheet_direct(worksheet_name, data):
    """Update Google Sheet directly via gspread (alternative method)"""
    
    if not data:
        print("⚠️  No data to update")
        return
    
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Find or create worksheet
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        print(f"📋 Found worksheet: {worksheet_name}")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
        print(f"➕ Created new worksheet: {worksheet_name}")
    
    # Convert data to 2D array
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [[str(row.get(col, '')) for col in headers] for row in data]
        values = [headers] + rows
    else:
        values = data
    
    # Clear and update
    worksheet.clear()
    worksheet.update('A1', values)
    
    print(f"✅ Updated {len(values)} rows in '{worksheet_name}'")


# ============================================================================
# PRE-CONFIGURED UPDATE FUNCTIONS
# ============================================================================

def update_live_bigquery_sheet():
    """Update Live BigQuery worksheet with latest market prices"""
    # bmrs_mid_iris schema: settlementDate, settlementPeriod, price, volume
    query = f"""
    SELECT 
        CAST(settlementDate AS STRING) as settlementDate,
        settlementPeriod,
        ROUND(price, 2) as price_gbp_mwh,
        ROUND(volume, 2) as volume_mwh,
        CAST(startTime AS STRING) as startTime
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE settlementDate >= CURRENT_DATE()
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 100
    """
    
    data = query_bigquery(query)
    update_sheet_via_api("Live BigQuery", data)


def update_live_raw_gen():
    """Update Live_Raw_Gen worksheet with latest generation data"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        fuelType,
        generation
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE settlementDate >= CURRENT_DATE()
    ORDER BY settlementDate DESC, settlementPeriod DESC, fuelType
    LIMIT 500
    """
    
    data = query_bigquery(query)
    update_sheet_via_api("Live_Raw_Gen", data)


def update_live_raw_ic():
    """Update Live_Raw_IC worksheet with interconnector flows"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        interconnectorId,
        flow
    FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
    WHERE settlementDate >= CURRENT_DATE()
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 500
    """
    
    data = query_bigquery(query)
    update_sheet_via_api("Live_Raw_IC", data)


def update_live_raw_prices():
    """Update Live_Raw_Prices with market prices"""
    # bmrs_mid_iris schema: price, volume (not systemSellPrice/systemBuyPrice)
    query = f"""
    SELECT 
        CAST(settlementDate AS STRING) as settlementDate,
        settlementPeriod,
        ROUND(price, 2) as price_gbp_mwh,
        ROUND(volume, 2) as volume_mwh,
        CAST(startTime AS STRING) as startTime,
        dataProvider
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE settlementDate >= CURRENT_DATE()
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 200
    """
    
    data = query_bigquery(query)
    update_sheet_via_api("Live_Raw_Prices", data)


def update_bess_vlp():
    """Update BESS_VLP worksheet with battery arbitrage data"""
    # Use bmrs_mid_iris for market prices
    query = f"""
    WITH latest_prices AS (
        SELECT 
            CAST(settlementDate AS DATE) as settlementDate,
            settlementPeriod,
            price,
            volume
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    )
    SELECT 
        settlementDate,
        COUNT(*) as periods,
        ROUND(AVG(price), 2) as avg_price,
        ROUND(MAX(price), 2) as max_price,
        ROUND(MIN(price), 2) as min_price,
        ROUND(MAX(price) - MIN(price), 2) as daily_spread,
        ROUND(SUM(volume), 2) as total_volume
    FROM latest_prices
    GROUP BY settlementDate
    ORDER BY settlementDate DESC
    """
    
    data = query_bigquery(query)
    update_sheet_via_api("BESS_VLP", data)


def update_dashboard_summary():
    """Update Dashboard worksheet with summary statistics"""
    # bmrs_mid_iris: price (not systemSellPrice/systemBuyPrice)
    # bmrs_fuelinst_iris: generation by fuelType
    query = f"""
    WITH price_stats AS (
        SELECT 
            'Market Price' as metric,
            ROUND(AVG(price), 2) as avg_value,
            ROUND(MAX(price), 2) as max_value,
            ROUND(MIN(price), 2) as min_value
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate = CURRENT_DATE()
    ),
    gen_stats AS (
        SELECT 
            'Generation (GW)' as metric,
            ROUND(SUM(generation)/1000, 2) as avg_value,
            ROUND(MAX(generation)/1000, 2) as max_value,
            ROUND(MIN(generation)/1000, 2) as min_value
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE settlementDate = CURRENT_DATE()
        GROUP BY settlementDate, settlementPeriod
        LIMIT 1
    )
    SELECT * FROM price_stats
    UNION ALL
    SELECT * FROM gen_stats
    """
    
    data = query_bigquery(query)
    # Add timestamp
    timestamp_row = {"metric": "Last Updated", "avg_value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "max_value": "", "min_value": ""}
    data.insert(0, timestamp_row)
    
    update_sheet_via_api("Dashboard", data, range_start="A1")


# ============================================================================
# MAIN UPDATE ORCHESTRATOR
# ============================================================================

def update_all_sheets():
    """Run all sheet updates"""
    print("=" * 80)
    print("🚀 Starting BigQuery → Sheets Auto-Update")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    updates = [
        ("Dashboard Summary", update_dashboard_summary),
        ("Live BigQuery", update_live_bigquery_sheet),
        ("Live Generation", update_live_raw_gen),
        ("Live Interconnectors", update_live_raw_ic),
        ("Live Prices", update_live_raw_prices),
        ("BESS VLP", update_bess_vlp),
    ]
    
    for name, func in updates:
        try:
            print(f"\n📊 Updating: {name}")
            func()
        except Exception as e:
            print(f"❌ Error updating {name}: {str(e)}")
            continue
    
    print("\n" + "=" * 80)
    print("✅ Update cycle complete!")
    print("=" * 80)


def continuous_update(interval_seconds=300):
    """Continuously update sheets at specified interval"""
    print(f"🔄 Starting continuous update (every {interval_seconds} seconds)")
    
    while True:
        try:
            update_all_sheets()
            print(f"\n⏳ Waiting {interval_seconds} seconds until next update...")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Fatal error: {str(e)}")
            print(f"⏳ Retrying in {interval_seconds} seconds...")
            time.sleep(interval_seconds)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "continuous":
            # Continuous mode: update every 5 minutes
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            continuous_update(interval)
        
        elif command == "once":
            # Run once and exit
            update_all_sheets()
        
        elif command == "dashboard":
            update_dashboard_summary()
        
        elif command == "live":
            update_live_bigquery_sheet()
        
        elif command == "gen":
            update_live_raw_gen()
        
        elif command == "ic":
            update_live_raw_ic()
        
        elif command == "prices":
            update_live_raw_prices()
        
        elif command == "bess":
            update_bess_vlp()
        
        else:
            print("❌ Unknown command")
            print("\nUsage:")
            print("  python bigquery_to_sheets_updater.py once          # Run once")
            print("  python bigquery_to_sheets_updater.py continuous    # Run every 5 min")
            print("  python bigquery_to_sheets_updater.py continuous 60 # Run every 60 sec")
            print("  python bigquery_to_sheets_updater.py dashboard     # Update dashboard only")
            print("  python bigquery_to_sheets_updater.py live          # Update live data only")
            sys.exit(1)
    else:
        # Default: run once
        update_all_sheets()
