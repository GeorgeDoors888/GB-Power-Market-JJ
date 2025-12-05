"""
populate_dashboard_tables_hybrid.py

📊 DASHBOARD V3 - HYBRID IMPLEMENTATION (OPTION C)
--------------------------------------------------
Python side: Loads ALL backing sheets from BigQuery
Apps Script side: Formats Dashboard V3 (Code_V3_Hybrid.gs)

BACKING SHEETS CREATED:
1. Chart_Data_V2 - Timeseries data (48 rows, columns A-J)
2. VLP_Data - VLP revenue data (7-day rolling)
3. Market_Prices - Market prices (7-day rolling)
4. BESS - Battery storage summary (single row)
5. DNO_Map - DNO centroids and KPIs
6. ESO_Actions - ESO balancing actions (last 50)
7. Outages - Active outages (top 15 by MW lost)

Author: Upowerenergy / Overarch Jibber Jabber System
Last Updated: 2025-12-04
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
import pandas as pd

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.cloud import bigquery

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "../inner-cinema-credentials.json")
GCP_PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Sheet names (match Apps Script expectations)
SHEET_NAMES = {
    'chart_data': 'Chart_Data_V2',
    'vlp_data': 'VLP_Data',
    'market_prices': 'Market_Prices',
    'bess': 'BESS',
    'dno_map': 'DNO_Map',
    'eso_actions': 'ESO_Actions',
    'outages': 'Outages'
}

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def get_bigquery_client():
    """Create BigQuery client using service account credentials."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(project=GCP_PROJECT_ID, credentials=creds)


def ensure_sheet_exists(service, spreadsheet_id: str, sheet_name: str) -> int:
    """Ensure sheet exists, return sheet ID."""
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    
    for sheet in ss.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    
    # Create sheet if not exists
    request = {
        'addSheet': {
            'properties': {
                'title': sheet_name,
                'gridProperties': {
                    'rowCount': 1000,
                    'columnCount': 20
                }
            }
        }
    }
    
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': [request]}
    ).execute()
    
    return response['replies'][0]['addSheet']['properties']['sheetId']


def write_to_sheet(service, spreadsheet_id: str, sheet_name: str, data: list):
    """Write data to sheet, clearing existing content first."""
    # Clear existing data
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1:Z1000"
    ).execute()
    
    # Write new data
    body = {
        'values': data
    }
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    print(f"   ✅ Written {len(data)} rows to {sheet_name}")


# ---------------------------------------------------------------------
# DATA LOADERS
# ---------------------------------------------------------------------

def load_chart_data_v2(bq_client: bigquery.Client) -> list:
    """
    Load 48 hours of timeseries data for main chart.
    Columns: Timestamp, Demand, Price, Volume, Gen, Wind, Solar, Nuclear, CCGT, Net_Margin
    """
    query = f"""
    WITH hourly_data AS (
        SELECT
            CAST(settlementDate AS DATETIME) as timestamp,
            AVG(price) as avg_price,
            SUM(volume) as total_volume
        FROM `{GCP_PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
        GROUP BY timestamp
        ORDER BY timestamp DESC
        LIMIT 48
    )
    SELECT
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', timestamp) as timestamp,
        0 as demand_gw,  -- Placeholder
        ROUND(avg_price, 2) as price_gbp_per_mwh,
        ROUND(total_volume, 0) as volume_mwh,
        0 as generation_gw,  -- Placeholder
        0 as wind_gw,  -- Placeholder
        0 as solar_gw,  -- Placeholder
        0 as nuclear_gw,  -- Placeholder
        0 as ccgt_gw,  -- Placeholder
        ROUND(avg_price - 50, 2) as net_margin  -- Simplified calculation
    FROM hourly_data
    ORDER BY timestamp ASC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    # Convert to list of lists with header
    header = ['Timestamp', 'Demand (GW)', 'Price (£/MWh)', 'Volume (MWh)', 
              'Gen (GW)', 'Wind (GW)', 'Solar (GW)', 'Nuclear (GW)', 'CCGT (GW)', 
              'Net Margin (£/MWh)']
    data = [header] + df.values.tolist()
    
    return data


def load_vlp_data(bq_client: bigquery.Client) -> list:
    """
    Load VLP revenue data (7-day rolling).
    Columns: Date, BMU, Volume, Revenue
    """
    query = f"""
    SELECT
        FORMAT_DATE('%Y-%m-%d', DATE(settlementDate)) as date,
        'FBPGM002' as bmu,
        0 as volume_mwh,
        50000 as revenue_gbp  -- Placeholder
    FROM `{GCP_PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    GROUP BY date
    ORDER BY date DESC
    LIMIT 7
    """
    
    df = bq_client.query(query).to_dataframe()
    
    header = ['Date', 'BMU', 'Volume (MWh)', 'Revenue (£)']
    data = [header] + df.values.tolist()
    
    return data


def load_market_prices(bq_client: bigquery.Client) -> list:
    """
    Load market prices (7-day rolling).
    Columns: Date, Avg Price, Max Price, Min Price
    """
    query = f"""
    SELECT
        FORMAT_DATE('%Y-%m-%d', DATE(settlementDate)) as date,
        ROUND(AVG(price), 2) as avg_price,
        ROUND(MAX(price), 2) as max_price,
        ROUND(MIN(price), 2) as min_price
    FROM `{GCP_PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    GROUP BY date
    ORDER BY date DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    header = ['Date', 'Avg Price (£/MWh)', 'Max Price (£/MWh)', 'Min Price (£/MWh)']
    data = [header] + df.values.tolist()
    
    return data


def load_bess_summary(bq_client: bigquery.Client) -> list:
    """
    Load BESS summary (single row).
    Columns: Active BMUs, Total Capacity, Avg Efficiency
    """
    # Placeholder data
    header = ['Active BMUs', 'Total Capacity (MW)', 'Avg Efficiency (%)']
    data = [header, [25, 1500, 85.5]]
    
    return data


def load_dno_map(bq_client: bigquery.Client) -> list:
    """
    Load DNO map with centroids and KPIs.
    Columns: DNO Code, DNO Name, Latitude, Longitude, Net Margin, Volume, Revenue
    """
    query = f"""
    SELECT
        dno_short_code as dno_code,
        dno_name,
        0.0 as latitude,  -- Placeholder (needs geospatial data)
        0.0 as longitude,  -- Placeholder
        45.50 as net_margin,  -- Placeholder
        12500 as volume_mwh,  -- Placeholder
        562500 as revenue_gbp  -- Placeholder
    FROM `{GCP_PROJECT_ID}.{DATASET}.neso_dno_reference`
    WHERE dno_short_code IS NOT NULL
    ORDER BY mpan_distributor_id
    LIMIT 14
    """
    
    df = bq_client.query(query).to_dataframe()
    
    header = ['DNO Code', 'DNO Name', 'Latitude', 'Longitude', 
              'Net Margin (£/MWh)', 'Volume (MWh)', 'Revenue (£)']
    data = [header] + df.values.tolist()
    
    return data


def load_eso_actions(bq_client: bigquery.Client) -> list:
    """
    Load ESO balancing actions (last 50).
    Columns: BMU, Mode, MW, Price, Duration, Action Type
    """
    query = f"""
    SELECT
        bmUnit as bmu,
        IF(levelTo > levelFrom, 'Increase', 'Decrease') as mode,
        ABS(levelTo - levelFrom) as mw,
        0 as price_gbp_per_mwh,  -- Placeholder (needs BOD join)
        TIMESTAMP_DIFF(
            CAST(acceptanceTime AS TIMESTAMP),
            CAST(settlementDate AS TIMESTAMP),
            MINUTE
        ) as duration_min,
        'Balancing' as action_type
    FROM `{GCP_PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
    WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY acceptanceTime DESC
    LIMIT 50
    """
    
    df = bq_client.query(query).to_dataframe()
    
    header = ['BM Unit', 'Mode', 'MW', '£/MWh', 'Duration (min)', 'Action Type']
    data = [header] + df.values.tolist()
    
    return data


def load_outages(bq_client: bigquery.Client) -> list:
    """
    Load active outages (top 15 by MW lost).
    Columns: BMU, Plant, Fuel, MW Lost, % Lost, Region, Start Time, Status
    """
    query = f"""
    SELECT
        affectedUnit as bmu,
        assetName as plant,
        fuelType as fuel,
        unavailableCapacity as mw_lost,
        ROUND((unavailableCapacity / NULLIF(normalCapacity, 0)) * 100, 1) as pct_lost,
        affectedArea as region,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventStartTime) as start_time,
        eventStatus as status
    FROM `{GCP_PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
    WHERE eventStatus IN ('Active', 'Pending')
        AND eventStartTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    ORDER BY unavailableCapacity DESC
    LIMIT 15
    """
    
    df = bq_client.query(query).to_dataframe()
    
    header = ['BM Unit', 'Plant', 'Fuel', 'MW Lost', '% Lost', 'Region', 'Start Time', 'Status']
    data = [header] + df.values.tolist()
    
    return data


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    print("=" * 60)
    print("📊 DASHBOARD V3 - HYBRID DATA LOADER (OPTION C)")
    print("=" * 60)
    print(f"Spreadsheet: {SPREADSHEET_ID}")
    print(f"BigQuery Project: {GCP_PROJECT_ID}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize services
    print("\n🔧 Initializing services...")
    sheets_service = get_sheets_service()
    bq_client = get_bigquery_client()
    print("   ✅ Google Sheets API connected")
    print("   ✅ BigQuery client connected")
    
    # Ensure all sheets exist
    print("\n📋 Ensuring sheets exist...")
    for key, sheet_name in SHEET_NAMES.items():
        ensure_sheet_exists(sheets_service, SPREADSHEET_ID, sheet_name)
        print(f"   ✅ {sheet_name}")
    
    # Load and write data
    print("\n📊 Loading data from BigQuery...")
    
    print("\n1️⃣  Chart_Data_V2 (48-hour timeseries)")
    data = load_chart_data_v2(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['chart_data'], data)
    
    print("\n2️⃣  VLP_Data (7-day revenue)")
    data = load_vlp_data(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['vlp_data'], data)
    
    print("\n3️⃣  Market_Prices (7-day prices)")
    data = load_market_prices(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['market_prices'], data)
    
    print("\n4️⃣  BESS (battery summary)")
    data = load_bess_summary(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['bess'], data)
    
    print("\n5️⃣  DNO_Map (DNO centroids)")
    data = load_dno_map(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['dno_map'], data)
    
    print("\n6️⃣  ESO_Actions (balancing actions)")
    data = load_eso_actions(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['eso_actions'], data)
    
    print("\n7️⃣  Outages (active outages)")
    data = load_outages(bq_client)
    write_to_sheet(sheets_service, SPREADSHEET_ID, SHEET_NAMES['outages'], data)
    
    print("\n" + "=" * 60)
    print("✅ DATA LOAD COMPLETE")
    print("=" * 60)
    print("\n📋 NEXT STEPS:")
    print("   1. Open spreadsheet in browser")
    print("   2. Go to Extensions → Apps Script")
    print("   3. Paste Code_V3_Hybrid.gs content")
    print("   4. Save and refresh spreadsheet")
    print("   5. Run: ⚡ GB Energy V3 → Rebuild Dashboard Design")
    print("\n🔗 Spreadsheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
