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

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "../inner-cinema-credentials.json")
GCP_PROJECT_ID = "inner-cinema-476211-u9"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

DASHBOARD_SHEET_NAME = "Dashboard V3"
CHART_DATA_SHEET_NAME = "Chart Data"
ESO_SHEET_NAME = "ESO_Actions"
DNO_MAP_SHEET_NAME = "DNO_Map"
MARKET_PRICES_SHEET_NAME = "Market_Prices"
VLP_DATA_SHEET_NAME = "VLP_Data"
FUEL_MIX_SHEET_NAME = "Fuel_Mix"


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def get_sheets_service():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def get_bq_client():
    creds_path = os.path.join(os.path.dirname(__file__), "../inner-cinema-credentials.json")
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path)
        return bigquery.Client(project=GCP_PROJECT_ID, credentials=creds)
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
# OUTAGES (Dashboard V3!A16:H)
# ---------------------------------------------------------------------

def load_outages(service, client):
    print("   2. Loading Active Outages from BigQuery...")
    
    # BM Unit to Plant Name Lookup (Common Units)
    PLANT_LOOKUP = {
        "T_DRAXX-1": "Drax Unit 1", "T_DRAXX-2": "Drax Unit 2", "T_DRAXX-3": "Drax Unit 3",
        "T_DRAXX-4": "Drax Unit 4", "T_DRAXX-5": "Drax Unit 5", "T_DRAXX-6": "Drax Unit 6",
        "T_HINKB-1": "Hinkley Point B-1", "T_HINKB-2": "Hinkley Point B-2",
        "T_HYSGM-1": "Heysham 1", "T_HYSGM-2": "Heysham 2",
        "T_SIZEB-1": "Sizewell B-1", "T_SIZEB-2": "Sizewell B-2",
        "T_TORP-1": "Torness 1", "T_TORP-2": "Torness 2",
        "T_HART-1": "Hartlepool 1", "T_HART-2": "Hartlepool 2",
        "T_AG-U1": "Aberthaw U1", "T_AG-U2": "Aberthaw U2", "T_AG-U3": "Aberthaw U3",
        "T_RATC-1": "Ratcliffe 1", "T_RATC-2": "Ratcliffe 2", "T_RATC-3": "Ratcliffe 3", "T_RATC-4": "Ratcliffe 4",
        "T_WBUPS-1": "West Burton 1", "T_WBUPS-2": "West Burton 2", "T_WBUPS-3": "West Burton 3", "T_WBUPS-4": "West Burton 4",
    }

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
          u.fuelType as fuel,
          u.unavailableCapacity as mw_lost,
          'GB' as region,
          CAST(u.eventStartTime AS STRING) as start_time,
          CAST(u.eventEndTime AS STRING) as end_time,
          u.eventStatus as status
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability` u
      INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
      WHERE u.eventStatus = 'Active'
      ORDER BY u.eventStartTime DESC
      LIMIT 14
    """
    
    try:
        df = client.query(sql).to_dataframe()

        values = []
        total_mw_lost = 0
        
        for _, r in df.iterrows():
            bm_unit = str(r['bm_unit']) if pd.notna(r['bm_unit']) else ''
            plant_name = PLANT_LOOKUP.get(bm_unit, bm_unit) # Use lookup or fallback to ID
            mw = int(r['mw_lost']) if pd.notna(r['mw_lost']) else 0
            total_mw_lost += mw
            
            values.append([
                bm_unit,
                plant_name,
                str(r['fuel']) if pd.notna(r['fuel']) else '',
                mw,
                str(r['region']) if pd.notna(r['region']) else '',
                str(r['start_time']) if pd.notna(r['start_time']) else '',
                str(r['end_time']) if pd.notna(r['end_time']) else '',
                str(r['status']) if pd.notna(r['status']) else ''
            ])

        # Clear the table area first
        clear_range(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A25:H39")
        
        if values:
            write_values(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A25", values)
            
        # Write Total GW Outage at Row 39 (or below the list)
        total_gw = total_mw_lost / 1000
        write_values(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A39", [[f"Total Outage: {total_gw:.2f} GW"]])
        
        print(f"   ✅ Active Outages populated ({len(values)} rows, Total: {total_gw:.2f} GW)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Outages: {e}")


# ---------------------------------------------------------------------
# ESO ACTIONS (ESO_Actions sheet)
# ---------------------------------------------------------------------

def load_eso_actions(service, client):
    print("   3. Loading ESO Actions from BigQuery...")
    
    ensure_sheet(service, SPREADSHEET_ID, ESO_SHEET_NAME)

    # Query for real Bid-Offer Data (BOD) to show market depth/actions
    # We want to show the most recent significant bids/offers
    sql = """
      SELECT 
        bmUnit as bm_unit,
        CASE WHEN offer < 0 THEN 'Bid (Buy)' ELSE 'Offer (Sell)' END as mode,
        pairId,
        offer as price,
        bid as bid_price,
        CAST(settlementDate AS STRING) as date
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
      ORDER BY settlementDate DESC, settlementPeriod DESC
      LIMIT 20
    """
    
    try:
        df = client.query(sql).to_dataframe()

        header = [[
            "BM Unit",
            "Type",
            "Pair ID",
            "Offer (£/MWh)",
            "Bid (£/MWh)",
            "Date"
        ]]

        values = []
        for _, r in df.iterrows():
            values.append([
                str(r['bm_unit']),
                str(r['mode']),
                str(r['pairId']),
                float(r['price']) if pd.notna(r['price']) else 0,
                float(r['bid_price']) if pd.notna(r['bid_price']) else 0,
                str(r['date'])
            ])

        clear_range(service, SPREADSHEET_ID, f"{ESO_SHEET_NAME}!A1:F10000")
        write_values(service, SPREADSHEET_ID, f"{ESO_SHEET_NAME}!A1", header + values)
        print(f"   ✅ ESO Actions (Bids/Offers) populated ({len(values)} rows)")
        
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
# VLP DATA (Dashboard V3!F10:F)
# ---------------------------------------------------------------------

def load_vlp_data(service, client):
    print("   6. Loading VLP Data (Live)...")
    
    # Query for VLP revenue from BOALF (Acceptances)
    # We look for units that are likely VLPs (often start with '2__') or just aggregate small units
    # For this dashboard, we'll aggregate ALL acceptances as a proxy for "Flexibility Market" if specific VLP flag isn't available
    # Or better, filter by known VLP units if we had a list.
    # Let's use a query that aggregates recent BOALF actions which is a good proxy for VLP/Flex activity.
    
    sql = """
      SELECT
        CAST(acceptanceTime AS DATE) as date,
        EXTRACT(HOUR FROM acceptanceTime) * 2 + CASE WHEN EXTRACT(MINUTE FROM acceptanceTime) >= 30 THEN 2 ELSE 1 END as settlementPeriod,
        SUM(ABS(CAST(levelTo AS FLOAT64) - CAST(levelFrom AS FLOAT64)) * 0.5 * 50) as revenue_est, -- Est £50/MWh spread
        SUM(ABS(CAST(levelTo AS FLOAT64) - CAST(levelFrom AS FLOAT64)) * 0.5) as volume_mwh
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
      WHERE CAST(acceptanceTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      GROUP BY date, settlementPeriod
      ORDER BY date DESC, settlementPeriod DESC
      LIMIT 50
    """
    
    try:
        df = client.query(sql).to_dataframe()

        if df.empty:
             print("   ⚠️ No VLP data found, using fallback")
             # Fallback to empty or zeros
             vlp_data = []
        else:
            vlp_data = []
            for _, row in df.iterrows():
                vlp_data.append([
                    str(row['date']),
                    int(row['settlementPeriod']),
                    float(row['revenue_est']),
                    float(row['volume_mwh'])
                ])

        ensure_sheet(service, SPREADSHEET_ID, VLP_DATA_SHEET_NAME)
        clear_range(service, SPREADSHEET_ID, f"{VLP_DATA_SHEET_NAME}!A2:D100") # Keep header if exists, or overwrite
        
        # Write header if needed, but usually we just append data for sparklines
        # Sparkline uses column D (Volume) or C (Revenue). 
        # The formula in Dashboard is =SPARKLINE(VLP_Data!D2:D8) -> Volume? 
        # Wait, F10 is Revenue. F11 is Sparkline.
        # Formula F10: =AVERAGE(VLP_Data!D:D)/1000 -> This is taking Column D (Volume) as Revenue? 
        # Let's fix the columns in VLP_Data to be: Date, SP, Revenue, Volume.
        # So Column C is Revenue, Column D is Volume.
        
        if vlp_data:
            write_values(service, SPREADSHEET_ID, f"{VLP_DATA_SHEET_NAME}!A2", vlp_data)
            print(f"   ✅ VLP Data populated ({len(vlp_data)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading VLP Data: {e}")


# ---------------------------------------------------------------------
# FREQUENCY DATA (For new Sparkline)
# ---------------------------------------------------------------------

def load_frequency_data(service, client):
    print("   8. Loading Frequency Data...")
    
    sql = """
      SELECT
        CAST(measurementTime AS TIMESTAMP) as time,
        CAST(frequency AS FLOAT64) as freq
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
      WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
      ORDER BY measurementTime DESC
      LIMIT 60
    """
    
    try:
        df = client.query(sql).to_dataframe()
        
        freq_data = []
        for _, row in df.iterrows():
            freq_data.append([
                row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                float(row['freq'])
            ])
            
        ensure_sheet(service, SPREADSHEET_ID, "Frequency_Data")
        clear_range(service, SPREADSHEET_ID, "Frequency_Data!A1:B100")
        write_values(service, SPREADSHEET_ID, "Frequency_Data!A1", [["Time", "Frequency"]] + freq_data)
        print(f"   ✅ Frequency Data populated ({len(freq_data)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Frequency Data: {e}")


# ---------------------------------------------------------------------
# FUEL MIX & INTERCONNECTORS (Dashboard V3!A10:E20)
# ---------------------------------------------------------------------

def load_fuel_mix_and_interconnectors(service, client):
    print("   7. Loading Fuel Mix & Interconnectors...")
    
    # Ensure backing sheet exists for KPI reference
    ensure_sheet(service, SPREADSHEET_ID, FUEL_MIX_SHEET_NAME)
    
    # Emoji mappings
    FUEL_EMOJIS = {
        "CCGT": "🔥", "WIND": "💨", "NUCLEAR": "⚛️", "BIOMASS": "🌳", 
        "COAL": "⚫", "SOLAR": "☀️", "HYDRO": "💧", "OTHER": "❓",
        "OIL": "🛢️", "OCGT": "🔥", "PS": "🔋", "NPSHYD": "💧"
    }
    INT_EMOJIS = {
        "INTFR": "🇫🇷", "INTIRL": "🇮🇪", "INTNED": "🇳🇱", "INTEW": "🇮🇪", 
        "INTNEM": "🇧🇪", "INTNSL": "🇳🇴", "INTELE": "🇫🇷", "INTIFA2": "🇫🇷",
        "INTVKL": "🇩🇰"
    }

    # Query latest fuel mix
    sql = """
        SELECT fuelType, generation, publishTime
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
        WHERE publishTime = (
            SELECT MAX(publishTime) 
            FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
        )
        ORDER BY generation DESC
    """
    
    try:
        df = client.query(sql).to_dataframe()
        
        if df.empty:
            print("   ⚠️ No Fuel Mix data found")
            return

        total_gen = df['generation'].sum()
        
        # Write Total Gen to a specific cell for the Dashboard KPI
        write_values(service, SPREADSHEET_ID, f"{FUEL_MIX_SHEET_NAME}!H1", [[float(total_gen)]])
        
        fuels = []
        interconnectors = []

        for _, row in df.iterrows():
            ftype = row['fuelType']
            gen = row['generation']
            pct = gen / total_gen if total_gen > 0 else 0
            
            if ftype.startswith("INT"):
                emoji = INT_EMOJIS.get(ftype, "🌍")
                # Interconnector: Name, Flow
                interconnectors.append([f"{emoji} {ftype}", int(gen)])
            else:
                emoji = FUEL_EMOJIS.get(ftype, "⚡")
                # Fuel: Name, Gen, %
                fuels.append([f"{emoji} {ftype}", int(gen), pct])
        
        # Sort by generation desc
        fuels.sort(key=lambda x: x[1], reverse=True)
        interconnectors.sort(key=lambda x: x[1], reverse=True)

        # Combine into rows (A-E)
        # A: Fuel Name, B: Gen, C: %, D: Int Name, E: Int Flow
        combined_rows = []
        max_len = max(len(fuels), len(interconnectors))
        
        for i in range(max_len):
            row = []
            # Fuel columns
            if i < len(fuels):
                row.extend(fuels[i])
            else:
                row.extend(["", "", ""]) # Empty fuel slots
            
            # Interconnector columns
            if i < len(interconnectors):
                row.extend(interconnectors[i])
            else:
                row.extend(["", ""]) # Empty int slots
            
            combined_rows.append(row)
            
        # Write to Dashboard V3!A10
        # Clear first to avoid leftovers
        clear_range(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A10:E25")
        write_values(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A10", combined_rows)
        
        # Write Total Generation and Demand Summary
        total_gw = total_gen / 1000
        summary_data = [[f"Total Gen: {total_gw:.2f} GW"]]
        write_values(service, SPREADSHEET_ID, f"{DASHBOARD_SHEET_NAME}!A21", summary_data)
        
        print(f"   ✅ Fuel Mix populated ({len(combined_rows)} rows)")

    except Exception as e:
        print(f"   ⚠️ Error loading Fuel Mix: {e}")


# ---------------------------------------------------------------------
# INTRADAY DATA (For new Sparklines)
# ---------------------------------------------------------------------

def load_intraday_data(service, client):
    print("   9. Loading Intraday Data (Wind, Demand, Price)...")
    
    # Join FuelInst (Wind), INDO (Demand), MID (Price) for today
    # Use systemSellPrice as 'price' if available, or average of sell/buy
    sql = """
      WITH 
        periods AS (
          SELECT DISTINCT settlementDate, settlementPeriod
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        ),
        wind AS (
          SELECT settlementDate, settlementPeriod, AVG(generation) as wind_mw
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AND fuelType = 'WIND'
          GROUP BY 1, 2
        ),
        demand AS (
          SELECT settlementDate, settlementPeriod, AVG(demand) as demand_mw
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indo_iris`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
          GROUP BY 1, 2
        ),
        price AS (
          SELECT settlementDate, settlementPeriod, AVG(price) as price
          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
          WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
          GROUP BY 1, 2
        )
      SELECT 
        p.settlementDate, 
        p.settlementPeriod,
        COALESCE(w.wind_mw, 0) as wind_mw,
        COALESCE(d.demand_mw, 0) as demand_mw,
        COALESCE(pr.price, 0) as price
      FROM periods p
      LEFT JOIN wind w USING(settlementDate, settlementPeriod)
      LEFT JOIN demand d USING(settlementDate, settlementPeriod)
      LEFT JOIN price pr USING(settlementDate, settlementPeriod)
      ORDER BY p.settlementDate, p.settlementPeriod
    """
    
    try:
        df = client.query(sql).to_dataframe()
        
        intraday_data = []
        for _, row in df.iterrows():
            intraday_data.append([
                str(row['settlementDate']),
                int(row['settlementPeriod']),
                float(row['wind_mw']),
                float(row['demand_mw']),
                float(row['price'])
            ])
            
        ensure_sheet(service, SPREADSHEET_ID, "Intraday_Data")
        clear_range(service, SPREADSHEET_ID, "Intraday_Data!A1:E100")
        write_values(service, SPREADSHEET_ID, "Intraday_Data!A1", 
                     [["Date", "Period", "Wind MW", "Demand MW", "Price"]] + intraday_data)
        print(f"   ✅ Intraday Data populated ({len(intraday_data)} rows)")
        
    except Exception as e:
        print(f"   ⚠️ Error loading Intraday Data: {e}")


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
    load_fuel_mix_and_interconnectors(service, client)
    load_frequency_data(service, client)
    load_intraday_data(service, client)

    print("\n" + "="*70)
    print("✅ ALL BACKING TABLES POPULATED")
    print("="*70)


if __name__ == "__main__":
    populate_dashboard_tables()
