#!/usr/bin/env python3
"""
VLP Dashboard - Simple Version
Reads REAL Elexon data (bmrs_boalf + bmrs_costs) directly
Calculates revenues, writes to Google Sheets
NO BigQuery views needed!
"""

from google.cloud import bigquery
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
from datetime import datetime
import json

# Load config
with open('vlp_prerequisites.json', 'r') as f:
    config = json.load(f)

PROJECT_ID = config['PROJECT_ID']
DATASET = config['DATASET']
SPREADSHEET_ID = config['SPREADSHEET_ID']
BMU_ID = config['BMU_BATTERY']

# Battery parameters
BATTERY_POWER_MW = config['BATTERY_POWER_MW']
BATTERY_ENERGY_MWH = config['BATTERY_ENERGY_MWH']
EFFICIENCY = config['EFFICIENCY']

# Revenue parameters
CM_GBP_PER_MWH = 9.04  # \u00a39.04/MWh (£36,192/year / 4,000 MWh)
PPA_PRICE = 150.0      # £150/MWh export price
LEVIES = 98.15         # £/MWh blended levies
SITE_SHARE = config['SITE_SHARE']
FIXED_OPEX = config['FIXED_OPEX_GBP']

def get_bq_client():
    """BigQuery client"""
    return bigquery.Client(project=PROJECT_ID)

def get_sheets_client():
    """Google Sheets client with oauth2client (known working)"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        '/home/george/inner-cinema-credentials.json',
        scope
    )
    return gspread.authorize(creds)

def fetch_vlp_data(start_date='2025-10-17', end_date='2025-10-23'):
    """Fetch VLP revenue data from BigQuery"""
    
    print(f'\U0001F4CA Fetching data from {start_date} to {end_date}...')
    
    client = get_bq_client()
    
    # Query combines bmrs_boalf (volumes) + bmrs_costs (prices)
    query = f"""
    WITH bm_volumes AS (
      -- BM acceptance volumes per settlement period
      SELECT
        CAST(settlementDate AS DATE) AS settlementDate,
        settlementPeriodFrom AS settlementPeriod,
        SUM(ABS(levelTo - levelFrom)) AS accepted_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE bmUnit = '{BMU_ID}'
        AND CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
      GROUP BY settlementDate, settlementPeriod
    )
    
    SELECT
      c.settlementDate,
      c.settlementPeriod,
      c.systemBuyPrice AS wholesale_price,
      c.systemSellPrice AS ssp_price,
      
      -- DUoS band
      CASE
        WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 'GREEN'
        WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
        WHEN c.settlementPeriod BETWEEN 17 AND 44 THEN 'AMBER'
        ELSE 'GREEN'
      END AS duos_band,
      
      -- DUoS rate (£/MWh)
      CASE
        WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 0.11
        WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 17.64
        WHEN c.settlementPeriod BETWEEN 17 AND 44 THEN 2.05
        ELSE 0.11
      END AS duos_rate,
      
      -- BM acceptance volume (MW)
      COALESCE(bm.accepted_mw, 0) AS bm_accepted_mw,
      
      -- Convert to MWh (30-min period)
      COALESCE(bm.accepted_mw, 0) * 0.5 AS bm_accepted_mwh
      
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs` c
    LEFT JOIN bm_volumes bm USING (settlementDate, settlementPeriod)
    WHERE c.settlementDate BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY c.settlementDate, c.settlementPeriod
    """
    
    df = client.query(query).to_dataframe()
    print(f'   \u2705 Loaded {len(df)} settlement periods')
    
    return df

def calculate_revenues(df):
    """Calculate all revenue streams"""
    
    print('\U0001F4B0 Calculating revenues...')
    
    # Import cost = wholesale + DUoS + levies
    df['import_cost'] = df['wholesale_price'] + df['duos_rate'] + LEVIES
    
    # Revenue streams (based on BM accepted volumes)
    # Note: Using SSP as proxy for BM acceptance price (actual prices in bmrs_bod)
    df['r_bm_gbp'] = df['bm_accepted_mwh'] * df['ssp_price']
    df['r_cm_gbp'] = df['bm_accepted_mwh'] * CM_GBP_PER_MWH
    df['r_ppa_gbp'] = df['bm_accepted_mwh'] * PPA_PRICE
    df['r_avoided_import_gbp'] = df['bm_accepted_mwh'] * df['import_cost']
    
    # Placeholder for ESO/DSO
    df['r_eso_gbp'] = 0.0
    df['r_dso_gbp'] = 0.0
    
    # Gross margin per SP
    df['gross_margin_sp'] = (
        df['r_bm_gbp'] + 
        df['r_cm_gbp'] + 
        df['r_ppa_gbp'] + 
        df['r_avoided_import_gbp']
    )
    
    # Simple SoC tracking (start at 50%, charge/discharge based on volume)
    soc = BATTERY_ENERGY_MWH / 2  # Start at 50%
    soc_list = []
    
    for idx, row in df.iterrows():
        soc_start = soc
        # Discharge if positive BM volume, charge if negative
        soc += row['bm_accepted_mwh']  # Simplified: not applying efficiency
        soc = max(0.25, min(BATTERY_ENERGY_MWH, soc))  # Clamp to bounds
        soc_list.append({'soc_start': soc_start, 'soc_end': soc})
    
    df = pd.concat([df, pd.DataFrame(soc_list)], axis=1)
    
    print(f'   ✅ Calculated {len(df)} periods')
    total_bm = df['r_bm_gbp'].sum()
    total_cm = df['r_cm_gbp'].sum()
    total_ppa = df['r_ppa_gbp'].sum()
    total_gross = df['gross_margin_sp'].sum()
    print(f'   Total BM revenue: £{total_bm:,.0f}')
    print(f'   Total CM revenue: £{total_cm:,.0f}')
    print(f'   Total PPA revenue: £{total_ppa:,.0f}')
    print(f'   Total gross margin: £{total_gross:,.0f}')
    
    return df

def write_to_sheets(df):
    """Write results to Google Sheets"""
    
    print('\U0001F4DD Writing to Google Sheets...')
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)
    
    # 1. BESS worksheet - full time series
    try:
        bess_sheet = ss.worksheet('BESS_VLP')
    except gspread.WorksheetNotFound:
        bess_sheet = ss.add_worksheet('BESS_VLP', rows=1000, cols=30)
    
    bess_sheet.clear()
    
    # Convert DataFrame copy with datetime columns as strings (avoid JSON serialization error)
    df_write = df.copy()
    if 'settlementDate' in df_write.columns:
        df_write['settlementDate'] = df_write['settlementDate'].astype(str)
    
    # Write headers + data
    headers = df_write.columns.tolist()
    bess_sheet.append_row(headers)
    
    if not df_write.empty:
        # Convert to list of lists
        data = df_write.values.tolist()
        bess_sheet.append_rows(data)
    
    print(f'   \u2705 BESS_VLP sheet updated ({len(df)} rows)')
    
    # 2. Dashboard worksheet - summary KPIs
    try:
        dash = ss.worksheet('Dashboard')
    except gspread.WorksheetNotFound:
        dash = ss.add_worksheet('Dashboard', rows=100, cols=20)
    
    # Calculate totals
    total_bm = df['r_bm_gbp'].sum()
    total_cm = df['r_cm_gbp'].sum()
    total_ppa = df['r_ppa_gbp'].sum()
    total_avoided = df['r_avoided_import_gbp'].sum()
    total_eso = 0.0
    total_dso = 0.0
    
    total_gross = total_bm + total_cm + total_ppa + total_avoided + total_eso + total_dso
    site_margin = total_gross * SITE_SHARE - (FIXED_OPEX / 12)  # Monthly
    vlp_margin = total_gross * (1 - SITE_SHARE)
    
    # Write to Dashboard (using new gspread API format)
    dash.update(values=[['VLP Site – BESS Revenue Dashboard']], range_name='A1')
    dash.update(values=[['Revenue Breakdown']], range_name='A3')
    dash.update(values=[['Revenue Line', 'Value (£)']], range_name='A4')
    dash.update(values=[
        ['BM revenue', total_bm],
        ['ESO services', total_eso],
        ['CM revenue', total_cm],
        ['DSO flex', total_dso],
        ['PPA export', total_ppa],
        ['Avoided import', total_avoided]
    ], range_name='A5')
    
    dash.update(values=[
        ['Total Gross Margin', total_gross],
        ['Site Margin (70%)', site_margin],
        ['VLP Margin (30%)', vlp_margin]
    ], range_name='D4')
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dash.update(values=[[f'Last Updated: {timestamp}']], range_name='A20')
    
    print(f'   \u2705 Dashboard updated')
    print(f'\n\U0001F4CA SUMMARY:')
    print(f'   Total Gross: £{total_gross:,.0f}')
    print(f'   Site (70%): £{site_margin:,.0f}')
    print(f'   VLP (30%): £{vlp_margin:,.0f}')

def main():
    print('\U0001F680 VLP DASHBOARD - SIMPLE VERSION')
    print('='*60)
    print(f'BMU: {BMU_ID}')
    print(f'Battery: {BATTERY_POWER_MW} MW / {BATTERY_ENERGY_MWH} MWh')
    print(f'Spreadsheet: {SPREADSHEET_ID}')
    print('='*60)
    
    # Fetch data
    df = fetch_vlp_data(start_date='2025-10-17', end_date='2025-10-23')
    
    # Calculate revenues
    df = calculate_revenues(df)
    
    # Write to sheets
    write_to_sheets(df)
    
    print('\n\u2705 COMPLETE! Check Google Sheets Dashboard')
    print(f'   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/')

if __name__ == '__main__':
    main()
