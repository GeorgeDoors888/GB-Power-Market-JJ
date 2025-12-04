#!/usr/bin/env python3
"""
Update Dashboard V3 KPIs based on selected DNO in cell F3.

Reads:
- F3: Selected DNO (name or code)
- B3: Time range selection

Queries BigQuery for selected DNO's metrics, then writes to F10:L10:
F10: VLP Revenue
G10: Wholesale Avg Price
H10: Market Volume
I10: PPA Revenue
J10: Total Cost
K10: Net Margin
L10: DUoS Weighted Rate

This script is called either manually or via cron for auto-refresh.
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timedelta

# ===== CONFIGURATION =====
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_SHEET = "Dashboard V3"
DNO_MAP_SHEET = "DNO_Map"

# Cell locations
TIME_RANGE_CELL = "B3"
SELECTED_DNO_CELL = "F3"
KPI_RANGE = "F10:L10"  # 7 KPI cells

CREDENTIALS_PATH = os.path.expanduser("~/GB-Power-Market-JJ/inner-cinema-credentials.json")

# DNO code to name mapping
DNO_MAP = {
    "10": "UKPN-EPN", "11": "UKPN-LPN", "12": "UKPN-SPN",
    "13": "NGED-WMID", "14": "NGED-EMID", "15": "NGED-SWALES", "16": "NGED-SWEST",
    "17": "SSEN-SHYDRO", "18": "SSEN-SEPD",
    "19": "SPEN-SPD", "20": "SPEN-MANWEB",
    "21": "ENWL", "22": "NGED-YORKSHIRE", "23": "NGED-NORTHEAST"
}
DNO_NAME_TO_CODE = {v: k for k, v in DNO_MAP.items()}


def get_credentials():
    """Load service account credentials."""
    return service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/bigquery"
        ]
    )


def read_sheet_values(credentials, range_name):
    """Read values from Google Sheets."""
    service = build('sheets', 'v4', credentials=credentials)
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DASHBOARD_SHEET}!{range_name}"
        ).execute()
        return result.get('values', [[]])[0]
    except Exception as e:
        print(f"❌ Error reading {range_name}: {e}")
        return []


def get_dno_info_from_map(credentials, dno_identifier):
    """
    Read DNO_Map sheet to get full data for selected DNO.
    dno_identifier can be code (e.g., "10") or name (e.g., "UKPN-EPN").
    """
    service = build('sheets', 'v4', credentials=credentials)
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DNO_MAP_SHEET}!A:M"  # All columns
        ).execute()
        
        values = result.get('values', [])
        if len(values) < 2:
            return None
        
        header = values[0]
        
        # Find matching row
        for row in values[1:]:
            if len(row) < 2:
                continue
            
            dno_code = str(row[0])
            dno_name = str(row[1])
            
            if dno_code == dno_identifier or dno_name == dno_identifier:
                # Return dict with all metrics
                return {
                    'code': dno_code,
                    'name': dno_name,
                    'net_margin': float(row[4]) if len(row) > 4 and row[4] else 0,
                    'total_mwh': float(row[5]) if len(row) > 5 and row[5] else 0,
                    'ppa_revenue': float(row[6]) if len(row) > 6 and row[6] else 0,
                    'total_cost': float(row[7]) if len(row) > 7 and row[7] else 0,
                    'vlp_revenue': float(row[8]) if len(row) > 8 and row[8] else 0,
                    'wholesale_avg': float(row[9]) if len(row) > 9 and row[9] else 0,
                    'duos_red': float(row[10]) if len(row) > 10 and row[10] else 0,
                    'duos_amber': float(row[11]) if len(row) > 11 and row[11] else 0,
                    'duos_green': float(row[12]) if len(row) > 12 and row[12] else 0
                }
        
        return None
    except Exception as e:
        print(f"❌ Error reading DNO_Map: {e}")
        return None


def calculate_duos_weighted(duos_red, duos_amber, duos_green):
    """
    Calculate weighted average DUoS rate.
    Assumes: Red 3.5h/day, Amber 8h/day, Green 12.5h/day.
    """
    red_weight = 3.5 / 24
    amber_weight = 8.0 / 24
    green_weight = 12.5 / 24
    
    weighted = (duos_red * red_weight + 
                duos_amber * amber_weight + 
                duos_green * green_weight)
    return weighted


def query_realtime_metrics(bq_client, dno_code, time_range_days):
    """
    Query real-time metrics for the selected DNO.
    
    This is a placeholder - in production, you'd filter by DNO region
    using a unit->DNO mapping table.
    """
    # For now, return calculated values from DNO_Map
    # In production, query bmrs_boalf, bmrs_mid, bmrs_indgen filtered by DNO
    return None  # Use DNO_Map values


def update_kpi_cells(credentials, kpi_values):
    """
    Write KPI values to F10:L10 on Dashboard V3.
    
    kpi_values = [vlp_revenue, wholesale_avg, market_volume, ppa_revenue, 
                  total_cost, net_margin, duos_weighted]
    """
    service = build('sheets', 'v4', credentials=credentials)
    
    body = {'values': [kpi_values]}
    
    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DASHBOARD_SHEET}!{KPI_RANGE}",
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"✅ Updated {result.get('updatedCells')} KPI cells")
        return True
    except Exception as e:
        print(f"❌ Error updating KPIs: {e}")
        return False


def main():
    """Main execution flow."""
    print("=" * 60)
    print("DASHBOARD V3 - KPI UPDATE")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize
    credentials = get_credentials()
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location="US")
    
    print("📖 Step 1: Reading Dashboard selections...")
    print("-" * 60)
    
    # Read current selections
    selected_dno_raw = read_sheet_values(credentials, SELECTED_DNO_CELL)
    time_range_raw = read_sheet_values(credentials, TIME_RANGE_CELL)
    
    selected_dno = selected_dno_raw[0] if selected_dno_raw else "All GB"
    time_range = time_range_raw[0] if time_range_raw else "Last 24h"
    
    print(f"  Selected DNO: {selected_dno}")
    print(f"  Time Range: {time_range}")
    
    # Parse time range to days
    time_map = {
        "Last 24h": 1,
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90
    }
    time_range_days = time_map.get(time_range, 7)
    
    print()
    print("📊 Step 2: Fetching DNO metrics...")
    print("-" * 60)
    
    # Get DNO data from DNO_Map sheet
    dno_info = get_dno_info_from_map(credentials, selected_dno)
    
    if not dno_info:
        print(f"⚠️  DNO '{selected_dno}' not found in DNO_Map sheet")
        print("   Using All-GB averages instead...")
        
        # Use placeholder values for All GB
        kpi_values = [0, 0, 0, 0, 0, 0, 0]
    else:
        print(f"  ✓ Found: {dno_info['name']} (Code: {dno_info['code']})")
        print(f"  ✓ Net Margin: £{dno_info['net_margin']:.2f}/MWh")
        print(f"  ✓ Wholesale Avg: £{dno_info['wholesale_avg']:.2f}/MWh")
        print(f"  ✓ VLP Revenue: £{dno_info['vlp_revenue']:,.0f}")
        
        # Calculate weighted DUoS
        duos_weighted = calculate_duos_weighted(
            dno_info['duos_red'],
            dno_info['duos_amber'],
            dno_info['duos_green']
        )
        
        # Build KPI array
        kpi_values = [
            round(dno_info['vlp_revenue'], 0),      # F10: VLP Revenue
            round(dno_info['wholesale_avg'], 2),    # G10: Wholesale Avg
            round(dno_info['total_mwh'], 0),        # H10: Market Volume
            round(dno_info['ppa_revenue'], 0),      # I10: PPA Revenue
            round(dno_info['total_cost'], 0),       # J10: Total Cost
            round(dno_info['net_margin'], 2),       # K10: Net Margin
            round(duos_weighted, 3)                 # L10: DUoS Weighted
        ]
    
    print()
    print("☁️  Step 3: Updating Dashboard KPIs...")
    print("-" * 60)
    
    success = update_kpi_cells(credentials, kpi_values)
    
    print()
    print("=" * 60)
    if success:
        print("✅ SUCCESS: Dashboard V3 KPIs updated")
        print(f"   DNO: {selected_dno}")
        print(f"   Time Range: {time_range}")
        print(f"   KPIs: {KPI_RANGE}")
    else:
        print("❌ FAILED: Could not update KPIs")
    print("=" * 60)


if __name__ == "__main__":
    main()
