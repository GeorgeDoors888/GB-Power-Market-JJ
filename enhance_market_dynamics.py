#!/usr/bin/env python3
"""
enhance_market_dynamics.py

One-time script to create a new, enhanced "Market Dynamics" section
on the Live Dashboard v2. This script redesigns the layout by merging
cells for larger sparklines and populates them with 24-hour data.
"""

import logging
import pandas as pd
from datetime import datetime
import gspread
from google.cloud import bigquery
from cache_manager import CacheManager
import os

# --- Configuration ---
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
TARGET_SHEET = 'Live Dashboard v2'

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Verified Sparkline Generation Function ---
def generate_gs_sparkline_formula(data, options):
    """
    Generates a native Google Sheets =SPARKLINE() formula with a robust
    options array.
    """
    clean_data = [item if isinstance(item, (int, float)) else 0 for item in data]
    option_pairs = [f'"{key}", "{value}"' if isinstance(value, str) else f'"{key}", {value}' for key, value in options.items()]
    options_string = ";".join(option_pairs)
    return f'=SPARKLINE({{{",".join(map(str, clean_data))}}};{{{options_string}}})'

# --- Main Logic ---
def get_market_data(bq_client):
    """Fetches 24h of system prices and market index prices."""
    logging.info("Querying BigQuery for 24-hour market data...")
    query = f"""
    WITH system_prices AS (
      SELECT
        settlementPeriod,
        AVG(systemSellPrice) as imbalance_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    ),
    market_index AS (
      SELECT
        settlementPeriod,
        AVG(price) as mid_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
      GROUP BY settlementPeriod
    )
    SELECT
      period.p as settlementPeriod,
      COALESCE(s.imbalance_price, 0) as imbalance_price,
      COALESCE(m.mid_price, 0) as mid_price
    FROM UNNEST(GENERATE_ARRAY(1, 48)) AS period
    LEFT JOIN system_prices s ON period = s.settlementPeriod
    LEFT JOIN market_index m ON period = m.settlementPeriod
    ORDER BY period
    """
    df = bq_client.query(query).to_dataframe()
    df['bm_mid_spread'] = df['imbalance_price'] - df['mid_price']
    logging.info(f"✅ Retrieved {len(df)} periods of data.")
    return df

def main():
    """Main function to execute the dashboard enhancement."""
    logging.info("--- Starting Dashboard Enhancement: Market Dynamics ---")

    # --- Initialize Clients ---
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cred_files = [os.path.join(script_dir, f'inner-cinema-credentials-{i}.json') for i in range(1, 6)]
    cred_files.insert(0, os.path.join(script_dir, 'inner-cinema-credentials.json'))

    # Correctly initialize gspread client
    gspread_client = gspread.service_account(filename=cred_files[0])

    spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(TARGET_SHEET)

    # --- Fetch and Process Data ---
    market_df = get_market_data(bq_client)

    imbalance_data = market_df['imbalance_price'].tolist()
    spread_data = market_df['bm_mid_spread'].tolist()

    # Get latest non-zero values for display
    latest_imbalance = market_df[market_df['imbalance_price'] != 0].iloc[-1]['imbalance_price']
    latest_spread = market_df[market_df['bm_mid_spread'] != 0].iloc[-1]['bm_mid_spread']

    # --- Generate Sparkline Formulas ---
    logging.info("Generating sparkline formulas...")
    imbalance_sparkline = generate_gs_sparkline_formula(
        imbalance_data,
        {"charttype": "column", "color": "#FF6347"} # Tomato Red
    )

    spread_sparkline = generate_gs_sparkline_formula(
        spread_data,
        {"charttype": "winloss", "negcolor": "#DC143C", "color": "#228B22"} # Crimson Red / Forest Green
    )

    # --- Define Layout and Formatting Requests for Google Sheets API ---
    requests = []

    # 1. Merge cells for the new section
    requests.extend([
        {'mergeCells': {'range': {'sheetId': worksheet.id, 'startRowIndex': 26, 'endRowIndex': 27, 'startColumnIndex': 11, 'endColumnIndex': 19}, 'mergeType': 'MERGE_ALL'}}, # Title
        {'mergeCells': {'range': {'sheetId': worksheet.id, 'startRowIndex': 27, 'endRowIndex': 30, 'startColumnIndex': 13, 'endColumnIndex': 19}, 'mergeType': 'MERGE_ALL'}}, # Imbalance Sparkline
        {'mergeCells': {'range': {'sheetId': worksheet.id, 'startRowIndex': 30, 'endRowIndex': 33, 'startColumnIndex': 13, 'endColumnIndex': 19}, 'mergeType': 'MERGE_ALL'}}, # Spread Sparkline
    ])

    # --- Prepare Data for Batch Update ---
    batch_update_data = [
        {'range': 'L27', 'values': [['Market Dynamics (24-Hour View)']]},
        {'range': 'L28', 'values': [['Imbalance Price (System Price)']]},
        {'range': 'M28', 'values': [[f"£{latest_imbalance:.2f}"]] },
        {'range': 'N28', 'values': [[imbalance_sparkline]]},
        {'range': 'L31', 'values': [['BM–MID Spread']]},
        {'range': 'M31', 'values': [[f"£{latest_spread:.2f}"]] },
        {'range': 'N31', 'values': [[spread_sparkline]]},
    ]

    # --- Apply Formatting and Updates ---
    logging.info("Applying formatting and updating sheet...")
    spreadsheet.batch_update({'requests': requests})
    worksheet.batch_update(batch_update_data, value_input_option='USER_ENTERED')

    logging.info("✅ --- Dashboard Enhancement Complete ---")

if __name__ == "__main__":
    main()
