#!/usr/bin/env python3
"""
Sync BigQuery view v_btm_bess_inputs into Google Sheets:
- Populates 'BtM Daily' tab with inputs (Prices, Volumes)
- 'GB Live' tab then updates automatically via formulas

Run locally on your Dell machine (Windows/WSL/Linux).
"""

import datetime as dt
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

# --------------------------------------------------------------------
# CONFIG – EDIT THESE VALUES TO MATCH YOUR ENVIRONMENT
# --------------------------------------------------------------------
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW = "v_btm_bess_inputs"

# Path to your service account file on the Dell
SERVICE_ACCOUNT_FILE = r"/home/george/.config/google-cloud/bigquery-credentials.json" 

# BtM Revenue Comparison spreadsheet
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
BESS_SHEET_NAME = "BtM Daily"  # Updated target

# Date range to pull – example: last 1 day (today only)
TODAY = dt.date.today()
DAYS_BACK = 5
START_DATE = TODAY - dt.timedelta(days=DAYS_BACK - 1)
END_DATE = TODAY  # inclusive

# --------------------------------------------------------------------
# AUTH – GOOGLE CLOUD & SHEETS
# --------------------------------------------------------------------
def get_credentials():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/bigquery",
    ]
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"⚠️ Warning: Service account file not found at {SERVICE_ACCOUNT_FILE}")
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
             return Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=scopes)
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    return creds


# --------------------------------------------------------------------
# BIGQUERY FETCH
# --------------------------------------------------------------------
def fetch_btm_bess_inputs(client, start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    """
    Fetch rows from v_btm_bess_inputs for the given date range.
    """
    query = f"""
    SELECT
      settlementDate as settlement_date,
      settlementPeriod as settlement_period,
      COALESCE(ppa_price, 0) as actual_bess_mwh,
      COALESCE(ppa_price, 0) as wholesale_price_da,
      COALESCE(ppa_price, 150.0) as ppa_price_gbp_mwh,
      COALESCE(bm_max_offer, 0) as bm_offer_price_bess,
      COALESCE(total_cost_per_mwh, 140.0) as full_import_cost_gbp_mwh,
      COALESCE(total_cost_per_mwh, 120.0) as bess_discharge_cost_gbp_mwh
    FROM `{PROJECT_ID}.{DATASET}.{VIEW}`
    WHERE CAST(settlementDate AS DATE) BETWEEN @start_date AND @end_date
    ORDER BY settlementDate DESC, settlementPeriod ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    df = client.query(query, job_config=job_config).result().to_dataframe()
    
    # Add missing columns expected by the sheet
    # We need columns for: Energy Route, ESO Util, CM Equiv, Avail Equiv
    if 'energy_route_code' not in df.columns:
        df['energy_route_code'] = 'BM' # Default
    if 'eso_util_price_gbp_mwh' not in df.columns:
        df['eso_util_price_gbp_mwh'] = 0.0
    if 'cm_equiv_gbp_mwh' not in df.columns:
        df['cm_equiv_gbp_mwh'] = 0.0
    if 'availability_equiv_gbp_mwh' not in df.columns:
        df['availability_equiv_gbp_mwh'] = 0.0
        
    return df


# --------------------------------------------------------------------
# WRITE INPUTS TO BTM DAILY SHEET
# --------------------------------------------------------------------
def write_btm_daily_inputs(ws, df: pd.DataFrame) -> None:
    """
    Write input columns to 'BtM Daily' sheet (B4:K51).
    """
    if df.empty:
        print("No data found to write.")
        return

    # Filter for the most recent single date
    latest_date = df['settlement_date'].max()
    day_df = df[df['settlement_date'] == latest_date].copy()
    day_df = day_df.sort_values('settlement_period')
    
    print(f"Writing data for date: {latest_date} ({len(day_df)} SPs)")
    
    # Update Date cell (B1)
    ws.update(range_name="B1", values=[[str(latest_date)]])

    # Prepare data for columns B to K (10 columns)
    # B: Net BESS MWh (actual_bess_mwh)
    # C: Energy Route (energy_route_code)
    # D: BM Price (bm_offer_price_bess)
    # E: PPA Price (ppa_price_gbp_mwh)
    # F: Wholesale Price (wholesale_price_da)
    # G: ESO Util Price (eso_util_price_gbp_mwh)
    # H: Full Import Cost (full_import_cost_gbp_mwh)
    # I: CM Equiv (cm_equiv_gbp_mwh)
    # J: Avail £/MW/h (availability_equiv_gbp_mwh)
    # K: Charge Cost £/MWh (bess_discharge_cost_gbp_mwh)
    
    columns_map = [
        'actual_bess_mwh',
        'energy_route_code',
        'bm_offer_price_bess',
        'ppa_price_gbp_mwh',
        'wholesale_price_da',
        'eso_util_price_gbp_mwh',
        'full_import_cost_gbp_mwh',
        'cm_equiv_gbp_mwh',
        'availability_equiv_gbp_mwh',
        'bess_discharge_cost_gbp_mwh'
    ]
    
    # Handle NaNs
    day_df = day_df.fillna(0)
    
    # Extract values
    values = day_df[columns_map].values.tolist()
    
    # Write to B4:K{4+len}
    end_row = 3 + len(values)
    range_name = f"B4:K{end_row}"
    
    ws.update(range_name=range_name, values=values)
    print(f"Updated range {range_name}")


# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def main():
    try:
        creds = get_credentials()
        
        # BigQuery client
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)
        
        # Google Sheets client
        gc = gspread.authorize(creds)
        ss = gc.open_by_key(SPREADSHEET_ID)
        
        try:
            btm_ws = ss.worksheet(BESS_SHEET_NAME)
        except gspread.WorksheetNotFound:
            print(f"❌ Worksheet '{BESS_SHEET_NAME}' not found. Please run 'Setup BtM Daily View' in Apps Script first.")
            return

        print(f"Fetching data for {START_DATE} to {END_DATE}...")
        df = fetch_btm_bess_inputs(bq_client, START_DATE, END_DATE)
        print(f"Fetched {len(df)} rows.")
        
        write_btm_daily_inputs(btm_ws, df)
        
        print("✅ Sync complete: BtM Daily inputs updated. GB Live should update automatically.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
