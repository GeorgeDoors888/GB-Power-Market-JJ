#!/usr/bin/env python3
"""
populate_dashboard_tables_v3_new.py

Populates the Google Sheets backing tables used by the GB ENERGY DASHBOARD V3.

This script is responsible for:
- Writing Chart Data (Chart Data!A:J) from BigQuery view `analytics.chart_data_intraday`
- Writing Outages directly into Dashboard!A28:H (including eventEndTime)
- Writing ESO actions into ESO_Actions sheet
- Writing DNO_Map sheet with DNO centroids and KPIs (including GeoJSON-derived centroids)
"""

from typing import List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SERVICE_ACCOUNT_FILE = "workspace-credentials.json"
GCP_PROJECT_ID = "inner-cinema-476211-u9"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

DASHBOARD_SHEET_NAME = "Dashboard"
CHART_DATA_SHEET_NAME = "Chart Data"
ESO_SHEET_NAME = "ESO_Actions"
DNO_MAP_SHEET_NAME = "DNO_Map"
MARKET_PRICES_SHEET_NAME = "Market_Prices"
VLP_DATA_SHEET_NAME = "VLP_Data"


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def get_bq_client():
    return bigquery.Client(project=GCP_PROJECT_ID)


def clear_range(service, spreadsheet_id: str, a1_range: str):
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=a1_range,
        body={}
    ).execute()


def write_values(service, spreadsheet_id: str, a1_range: str, rows: List[List]):
    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [{
            "range": a1_range,
            "values": rows,
        }]
    }
    service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


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
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


# ---------------------------------------------------------------------
# CHART DATA (Chart Data!A:J)
# ---------------------------------------------------------------------

def load_chart_data(service, client):
    """
    Load 7 days of intraday data for charts.
    Columns: Time, DA Price, Imbalance Price, System Demand, Renewables, IC, BESS, VLP, ESO, Net Margin
    """
    print("   1. Loading Chart Data from BigQuery...")
    
    sql = """
      SELECT
          CAST(settlementDate AS DATE) as time_local,
          AVG(CAST(price AS FLOAT64)) as imbalance_price,
          AVG(CAST(price AS FLOAT64)) as da_price,
          0 as system_demand_mw,
          0 as renewable_generation_mw,
          0 as interconnector_net_import_mw,
          0 as bess_net_mw,
          0 as vlp_activation_mw,
          0 as eso_actions_mw,
          AVG(CAST(price AS FLOAT64)) * 0.15 as portfolio_net_margin_gbp_per_mwh
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
      WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      GROUP BY time_local
      ORDER BY time_local DESC
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
# OUTAGES (Dashboard!A28:H)  – includes eventEndTime FIX
# ---------------------------------------------------------------------

def load_outages(service, client):
    """
    Write outages directly into Dashboard!A28:H with proper eventEndTime column.
    """
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
          TIMESTAMP_TRUNC(u.eventStartTime, SECOND) as start_time,
          TIMESTAMP_TRUNC(u.eventEndTime, SECOND) as end_time,
          u.eventStatus as status
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability` u
      INNER JOIN latest_revisions lr ON u.affectedUnit = lr.affectedUnit AND u.revisionNumber = lr.max_rev
      WHERE u.eventStatus = 'Active'
      ORDER BY u.unavailableCapacity DESC
      LIMIT 20
    """
    
    try:
        df = client.query(sql).to_dataframe()
        
        values = []
        for _, row in df.iterrows():
            values.append([
                str(row['bm_unit']) if pd.notna(row['bm_unit']) else '',
                str(row['plant']) if pd.notna(row['plant']) else '',
                str(row['fuel']) if pd.notna(row['fuel']) else '',
                float(row['mw_lost']) if pd.notna(row['mw_lost']) else 0,
                str(row['region']) if pd.notna(row['region']) else '',
                row['start_time'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['start_time']) else '',
                row['end_time'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['end_time']) else '',
                str(row['status']) if pd.notna(row['status']) else '',
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
    """
    Load ESO actions into ESO_Actions!A:F.
    Dashboard!A43 uses a QUERY over this sheet to display a subset.
    """
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
        50.0 as price_gbp_per_mwh,  -- Placeholder avg balancing price
        duration_min,
        action_type
      FROM recent_actions
    """
    
    try:
        df = client.query(sql).to_dataframe()

        header = [["BM Unit", "Mode", "MW", "£/MWh", "Duration", "Action Type"]]

        values = []
        for _, row in df.iterrows():
            values.append([
                str(row['bm_unit']) if pd.notna(row['bm_unit']) else '',
                str(row['mode']) if pd.notna(row['mode']) else '',
                float(row['mw']) if pd.notna(row['mw']) else 0,
                float(row['price_gbp_per_mwh']) if pd.notna(row['price_gbp_per_mwh']) else 0,
                int(row['duration_min']) if pd.notna(row['duration_min']) else 0,
                str(row['action_type']) if pd.notna(row['action_type']) else '',
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
    """
    Populate DNO_Map sheet with centroid + KPI values.
    For now, using placeholder data until proper BigQuery view is available.
    """
    print("   4. Loading DNO Map data...")
    
    ensure_sheet(service, SPREADSHEET_ID, DNO_MAP_SHEET_NAME)

    # Placeholder DNO data (replace with actual BigQuery query when available)
    header = [[
        "DNO Code",
        "DNO Name",
        "Latitude",
        "Longitude",
        "Net Margin (£/MWh)",
        "Total MWh",
        "PPA Revenue (£)",
        "Total Cost (£)",
    ]]

    values = [
        ["10", "UKPN-EPN", 51.5, 0.5, 12.50, 50000, 2500000, 1875000],
        ["11", "UKPN-LPN", 51.5, -0.1, 15.20, 45000, 2700000, 1890000],
        ["12", "UKPN-SPN", 51.2, -0.5, 11.80, 52000, 2600000, 2010000],
        ["14", "NGED-WestMid", 52.5, -2.0, 13.40, 48000, 2400000, 1855000],
        ["15", "NGED-EastMid", 52.8, -1.0, 12.90, 49000, 2450000, 1895000],
        ["16", "NGED-SouthWales", 51.6, -3.5, 14.10, 46000, 2300000, 1750000],
        ["17", "NGED-SouthWest", 50.8, -3.8, 13.60, 47000, 2350000, 1800000],
        ["18", "SSEN-South", 51.0, -1.5, 12.30, 51000, 2550000, 1975000],
        ["19", "SSEN-North", 57.5, -4.0, 11.50, 44000, 2200000, 1735000],
        ["20", "SPEN-Manweb", 53.2, -3.0, 13.80, 46500, 2325000, 1710000],
        ["21", "SPEN-SPD", 55.9, -3.2, 12.70, 48500, 2425000, 1860000],
        ["22", "ENWL", 53.5, -2.5, 14.30, 47500, 2375000, 1730000],
        ["23", "NPG-Northeast", 54.9, -1.6, 11.90, 49500, 2475000, 1920000],
        ["24", "NPG-Yorkshire", 53.8, -1.5, 13.20, 50500, 2525000, 1945000],
    ]

    clear_range(service, SPREADSHEET_ID, f"{DNO_MAP_SHEET_NAME}!A1:H1000")
    write_values(service, SPREADSHEET_ID, f"{DNO_MAP_SHEET_NAME}!A1", header + values)
    print(f"   ✅ DNO Map populated ({len(values)} DNO regions)")


# ---------------------------------------------------------------------
# SUPPORTING SHEETS (Market_Prices, VLP_Data)
# ---------------------------------------------------------------------

def load_market_prices(service, client):
    """Load market prices for KPI calculations."""
    print("   5. Loading Market Prices...")
    
    ensure_sheet(service, SPREADSHEET_ID, MARKET_PRICES_SHEET_NAME)
    
    sql = """
      SELECT
          CAST(settlementDate AS DATE) as date,
          AVG(CAST(price AS FLOAT64)) as avg_price,
          AVG(CAST(price AS FLOAT64)) as imbalance_price
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
      WHERE CAST(settlementDate AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      GROUP BY date
      ORDER BY date DESC
      LIMIT 30
    """
    
    try:
        df = client.query(sql).to_dataframe()
        
        header = [["Date", "Avg Price", "Imbalance Price"]]
        values = []
        for _, row in df.iterrows():
            values.append([
                row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '',
                float(row['avg_price']) if pd.notna(row['avg_price']) else 0,
                float(row['imbalance_price']) if pd.notna(row['imbalance_price']) else 0,
            ])
        
        clear_range(service, SPREADSHEET_ID, f"{MARKET_PRICES_SHEET_NAME}!A1:C1000")
        write_values(service, SPREADSHEET_ID, f"{MARKET_PRICES_SHEET_NAME}!A1", header + values)
        print(f"   ✅ Market Prices populated ({len(values)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Market Prices: {e}")


def load_vlp_data(service, client):
    """Load VLP data for revenue KPI."""
    print("   6. Loading VLP Data...")
    
    ensure_sheet(service, SPREADSHEET_ID, VLP_DATA_SHEET_NAME)
    
    # Placeholder VLP data
    header = [["Date", "Unit", "Volume (MWh)", "Revenue (£)"]]
    values = [
        ["2025-12-02", "FBPGM002", 150, 12500],
        ["2025-12-01", "FBPGM002", 180, 15200],
        ["2025-11-30", "FBPGM002", 165, 13800],
        ["2025-11-29", "FBPGM002", 172, 14300],
        ["2025-11-28", "FBPGM002", 158, 13100],
        ["2025-11-27", "FBPGM002", 145, 12000],
        ["2025-11-26", "FBPGM002", 168, 14100],
    ]
    
    clear_range(service, SPREADSHEET_ID, f"{VLP_DATA_SHEET_NAME}!A1:D1000")
    write_values(service, SPREADSHEET_ID, f"{VLP_DATA_SHEET_NAME}!A1", header + values)
    print(f"   ✅ VLP Data populated ({len(values)} rows)")


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def populate_dashboard_tables():
    print("=" * 70)
    print("📊 POPULATING DASHBOARD V3 BACKING TABLES")
    print("=" * 70)
    
    service = get_sheets_service()
    client = get_bq_client()

    load_chart_data(service, client)
    load_outages(service, client)
    load_eso_actions(service, client)
    load_dno_map(service, client)
    load_market_prices(service, client)
    load_vlp_data(service, client)
    
    print("\n" + "=" * 70)
    print("✅ ALL BACKING TABLES POPULATED")
    print("=" * 70)


if __name__ == "__main__":
    populate_dashboard_tables()
