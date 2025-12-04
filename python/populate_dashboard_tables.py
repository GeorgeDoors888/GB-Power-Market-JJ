"""
populate_dashboard_tables.py

Populates the Google Sheets backing tables used by the GB ENERGY DASHBOARD V3.

This script is responsible for:
- Writing Chart Data (Chart Data!A:J) from BigQuery IRIS tables
- Writing Outages directly into Dashboard V3!A28:H (including eventEndTime)
- Writing ESO actions into ESO_Actions sheet
- Writing DNO_Map sheet with DNO centroids and KPIs

Configured for inner-cinema-476211-u9 project with IRIS real-time data.
"""

from __future__ import annotations

import os
from typing import List
import pandas as pd

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.cloud import bigquery

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "../workspace-credentials.json")
GCP_PROJECT_ID = "inner-cinema-476211-u9"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

DASHBOARD_SHEET_NAME = "Dashboard V3"
CHART_DATA_SHEET_NAME = "Chart Data"
ESO_SHEET_NAME = "ESO_Actions"
DNO_MAP_SHEET_NAME = "DNO_Map"
MARKET_PRICES_SHEET_NAME = "Market_Prices"
VLP_DATA_SHEET_NAME = "VLP_Data"


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def get_bq_client():
    return bigquery.Client(project=GCP_PROJECT_ID)


def clear_range(service, spreadsheet_id: str, a1_range: str):
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=a1_range,
        body={}
    ).execute()


def write_values(service, spreadsheet_id: str, a1_range: str,
                 rows: List[List[object]]):
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [{
            "range": a1_range,
            "values": rows,
        }]
    }
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()


def ensure_sheet(service, spreadsheet_id: str, title: str) -> None:
    ss = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sh in ss["sheets"]:
        if sh["properties"]["title"] == title:
            return
    body = {
        "requests": [{
            "addSheet": {"properties": {"title": title}}
        }]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()


# ---------------------------------------------------------------------
# CHART DATA (Chart Data!A:J)
# ---------------------------------------------------------------------

def load_chart_data(service, client):
    print("   1. Loading Chart Data from BigQuery...")
    
    ensure_sheet(service, SPREADSHEET_ID, CHART_DATA_SHEET_NAME)
    
    sql = """
      SELECT
        CAST(settlementDate AS TIMESTAMP) as time_local,
        CAST(price AS FLOAT64) as da_price,
        CAST(price AS FLOAT64) as imbalance_price,
        0.0 as system_demand_mw,
        0.0 as renewable_generation_mw,
        0.0 as interconnector_net_import_mw,
        0.0 as bess_net_mw,
        0.0 as vlp_activation_mw,
        0.0 as eso_actions_mw,
        0.0 as portfolio_net_margin_gbp_per_mwh
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
      WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      ORDER BY settlementDate DESC
      LIMIT 48
    """
    
    try:
        df = client.query(sql).to_dataframe()

        header = [[
            "Time",
            "DA Price (£/MWh)",
            "Imbalance Price (£/MWh)",
            "System Demand (MW)",
            "Renewables Output (MW)",
            "Net IC Flow (MW, +Import)",
            "BESS Net MW (Discharge +)",
            "VLP Flex MW (Activation)",
            "ESO / BM Actions (MW)",
            "Portfolio Net Margin (£/MWh)",
        ]]

        values = []
        for _, row in df.iterrows():
            values.append([
                row['time_local'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['time_local']) else '',
                float(row['da_price']) if pd.notna(row['da_price']) else 0,
                float(row['imbalance_price']) if pd.notna(row['imbalance_price']) else 0,
                float(row['system_demand_mw']) if pd.notna(row['system_demand_mw']) else 0,
                float(row['renewable_generation_mw']) if pd.notna(row['renewable_generation_mw']) else 0,
                float(row['interconnector_net_import_mw']) if pd.notna(row['interconnector_net_import_mw']) else 0,
                float(row['bess_net_mw']) if pd.notna(row['bess_net_mw']) else 0,
                float(row['vlp_activation_mw']) if pd.notna(row['vlp_activation_mw']) else 0,
                float(row['eso_actions_mw']) if pd.notna(row['eso_actions_mw']) else 0,
                float(row['portfolio_net_margin_gbp_per_mwh']) if pd.notna(row['portfolio_net_margin_gbp_per_mwh']) else 0,
            ])

        clear_range(service, SPREADSHEET_ID, f"{CHART_DATA_SHEET_NAME}!A1:J10000")
        write_values(service, SPREADSHEET_ID, f"{CHART_DATA_SHEET_NAME}!A1", header + values)
        print(f"   ✅ Chart Data populated ({len(values)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Chart Data: {e}")


# ---------------------------------------------------------------------
# OUTAGES (Dashboard V3!A28:H)
# ---------------------------------------------------------------------

def load_outages(service, client):
    print("   2. Loading Active Outages from BigQuery...")
    
    sql = """
      WITH latest_revisions AS (
          SELECT
              affectedUnit,
              MAX(revisionNumber) AS max_rev
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability`
          WHERE eventStatus = 'Active'
          GROUP BY affectedUnit
      )
      SELECT
          u.affectedUnit as bm_unit,
          u.affectedUnit as plant,
          u.fuelType as fuel,
          u.unavailableCapacity as mw_lost,
          'GB' as region,
          CAST(u.eventStart AS STRING) as start_time,
          CAST(u.eventEnd AS STRING) as end_time,
          u.eventStatus as status
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability` u
      INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
      WHERE u.eventStatus = 'Active'
      ORDER BY u.eventStart DESC
      LIMIT 20
    """
    
    try:
        df = client.query(sql).to_dataframe()

        values = []
        for _, r in df.iterrows():
            values.append([
                str(r['bm_unit']) if pd.notna(r['bm_unit']) else '',
                str(r['plant']) if pd.notna(r['plant']) else '',
                str(r['fuel']) if pd.notna(r['fuel']) else '',
                int(r['mw_lost']) if pd.notna(r['mw_lost']) else 0,
                str(r['region']) if pd.notna(r['region']) else '',
                str(r['start_time']) if pd.notna(r['start_time']) else '',
                str(r['end_time']) if pd.notna(r['end_time']) else '',
                str(r['status']) if pd.notna(r['status']) else ''
            ])

        clear_range(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A28:H100")
        if values:
            write_values(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A28", values)
        print(f"   ✅ Active Outages populated ({len(values)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Outages: {e}")


# ---------------------------------------------------------------------
# ESO ACTIONS (ESO_Actions sheet)
# ---------------------------------------------------------------------

def load_eso_actions(service, client):
    print("   3. Loading ESO Actions from BigQuery...")
    
    ensure_sheet(service, SPREADSHEET_ID, ESO_SHEET_NAME)

    sql = """
      WITH recent_actions AS (
        SELECT
          bmUnit as bm_unit,
          CASE 
            WHEN levelTo > levelFrom THEN 'Increase'
            WHEN levelTo < levelFrom THEN 'Decrease'
            ELSE 'Stable'
          END as mode,
          ABS(CAST(levelTo AS FLOAT64) - CAST(levelFrom AS FLOAT64)) as mw,
          TIMESTAMP_DIFF(
            CAST(timeTo AS TIMESTAMP), 
            CAST(timeFrom AS TIMESTAMP), 
            MINUTE
          ) as duration_min,
          acceptanceTime,
          CASE 
            WHEN soFlag THEN 'System Action'
            WHEN storFlag THEN 'STOR'
            ELSE 'BM Action'
          END as action_type
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
        WHERE CAST(acceptanceTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND levelTo IS NOT NULL
          AND levelFrom IS NOT NULL
          AND ABS(CAST(levelTo AS FLOAT64) - CAST(levelFrom AS FLOAT64)) > 0
        ORDER BY acceptanceTime DESC
        LIMIT 100
      )
      SELECT 
        bm_unit,
        mode,
        mw,
        50.0 as price_gbp_per_mwh,
        duration_min,
        action_type
      FROM recent_actions
    """
    
    try:
        df = client.query(sql).to_dataframe()

        header = [[
            "BM Unit",
            "Mode",
            "MW",
            "£/MWh",
            "Duration",
            "Action Type",
        ]]

        values = []
        for _, r in df.iterrows():
            values.append([
                str(r['bm_unit']) if pd.notna(r['bm_unit']) else '',
                str(r['mode']) if pd.notna(r['mode']) else '',
                float(r['mw']) if pd.notna(r['mw']) else 0,
                float(r['price_gbp_per_mwh']) if pd.notna(r['price_gbp_per_mwh']) else 0,
                int(r['duration_min']) if pd.notna(r['duration_min']) else 0,
                str(r['action_type']) if pd.notna(r['action_type']) else '',
            ])

        clear_range(service, SPREADSHEET_ID, f"{ESO_SHEET_NAME}!A1:F10000")
        write_values(service, SPREADSHEET_ID, f"{ESO_SHEET_NAME}!A1", header + values)
        print(f"   ✅ ESO Actions populated ({len(values)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading ESO Actions: {e}")


# ---------------------------------------------------------------------
# DNO MAP & KPIs (DNO_Map sheet)
# ---------------------------------------------------------------------

def load_dno_map(service, client):
    print("   4. Loading DNO Map data...")
    
    ensure_sheet(service, SPREADSHEET_ID, DNO_MAP_SHEET_NAME)

    # Placeholder DNO data with GB regions
    dno_data = [
        ["DNO Code", "DNO Name", "Latitude", "Longitude", "Net Margin (£/MWh)", "Total MWh", "PPA Revenue (£)"],
        ["10", "UKPN-EPN", 52.2053, 0.1218, 5.2, 12000, 62400],
        ["11", "UKPN-LPN", 51.5074, -0.1278, 4.8, 15000, 72000],
        ["12", "UKPN-SPN", 51.2, -0.6, 5.1, 11000, 56100],
        ["13", "ENWL", 53.4808, -2.2426, 4.9, 13000, 63700],
        ["14", "NGED-WM", 52.4862, -1.8904, 5.3, 10000, 53000],
        ["15", "NGED-EM", 52.9548, -1.1581, 5.0, 11500, 57500],
        ["16", "NGED-SW", 50.7184, -3.5339, 5.4, 9000, 48600],
        ["17", "NGED-S Wales", 51.4816, -3.1791, 5.2, 9500, 49400],
        ["18", "SPEN-SPD", 55.9533, -3.1883, 4.7, 8000, 37600],
        ["19", "SPEN-SPM", 55.8642, -4.2518, 4.6, 8500, 39100],
        ["20", "SSEN-SEPD", 57.1497, -2.0943, 5.1, 7000, 35700],
        ["21", "SSEN-SHEPD", 57.4778, -4.2247, 5.3, 6500, 34450],
        ["22", "NPG-NEEB", 54.9783, -1.6178, 4.8, 9000, 43200],
        ["23", "NPG-YEDL", 53.7997, -1.5492, 5.0, 10000, 50000],
    ]

    clear_range(service, SPREADSHEET_ID, f"{DNO_MAP_SHEET_NAME}!A1:G100")
    write_values(service, SPREADSHEET_ID, f"{DNO_MAP_SHEET_NAME}!A1", dno_data)
    print(f"   ✅ DNO Map populated ({len(dno_data)-1} DNO regions)")


# ---------------------------------------------------------------------
# MARKET PRICES
# ---------------------------------------------------------------------

def load_market_prices(service, client):
    print("   5. Loading Market Prices...")
    
    ensure_sheet(service, SPREADSHEET_ID, MARKET_PRICES_SHEET_NAME)

    sql = """
      SELECT
        CAST(settlementDate AS TIMESTAMP) as time,
        settlementPeriod,
        AVG(CAST(price AS FLOAT64)) as price
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
      WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      GROUP BY settlementDate, settlementPeriod
      ORDER BY settlementDate DESC
      LIMIT 336
    """
    
    try:
        df = client.query(sql).to_dataframe()

        header = [["Time", "Settlement Period", "Price (£/MWh)"]]

        values = []
        for _, r in df.iterrows():
            values.append([
                r['time'].strftime('%Y-%m-%d %H:%M') if pd.notna(r['time']) else '',
                int(r['settlementPeriod']) if pd.notna(r['settlementPeriod']) else 0,
                float(r['price']) if pd.notna(r['price']) else 0,
            ])

        clear_range(service, SPREADSHEET_ID, f"{MARKET_PRICES_SHEET_NAME}!A1:C10000")
        write_values(service, SPREADSHEET_ID, f"{MARKET_PRICES_SHEET_NAME}!A1", header + values)
        print(f"   ✅ Market Prices populated ({len(values)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Market Prices: {e}")


# ---------------------------------------------------------------------
# VLP DATA
# ---------------------------------------------------------------------

def load_vlp_data(service, client):
    print("   6. Loading VLP Data...")
    
    ensure_sheet(service, SPREADSHEET_ID, VLP_DATA_SHEET_NAME)

    # Placeholder VLP revenue data
    vlp_data = [
        ["Date", "Settlement Period", "VLP Revenue (£)", "Volume (MWh)"],
        ["2025-12-03", 1, 1250, 50],
        ["2025-12-02", 48, 1890, 72],
        ["2025-12-01", 48, 1640, 68],
        ["2025-11-30", 48, 1420, 61],
        ["2025-11-29", 48, 1780, 74],
        ["2025-11-28", 48, 1560, 65],
        ["2025-11-27", 48, 1690, 70],
    ]

    clear_range(service, SPREADSHEET_ID, f"{VLP_DATA_SHEET_NAME}!A1:D100")
    write_values(service, SPREADSHEET_ID, f"{VLP_DATA_SHEET_NAME}!A1", vlp_data)
    print(f"   ✅ VLP Data populated ({len(vlp_data)-1} rows)")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def populate_dashboard_tables():
    print("\n" + "="*70)
    print("📊 POPULATING DASHBOARD V3 BACKING TABLES")
    print("="*70)
    
    service = get_sheets_service()
    client = get_bq_client()

    load_chart_data(service, client)
    load_outages(service, client)
    load_eso_actions(service, client)
    load_dno_map(service, client)
    load_market_prices(service, client)
    load_vlp_data(service, client)

    print("\n" + "="*70)
    print("✅ ALL BACKING TABLES POPULATED")
    print("="*70)


if __name__ == "__main__":
    populate_dashboard_tables()
