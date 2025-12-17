#!/usr/bin/env python3
"""
Add Market KPIs to Live Dashboard v2
Adds advanced market metrics with current values and 48-period sparklines

Metrics to add:
Row 1: Avg Acceptance Price | BM-MID Spread | Supplier-VLP Diff | Imbalance Premium Index
Row 2: Volume-Weighted Avg Price | BM-System Buy Spread | Daily Comp | Price Volatility
Row 3: Avg Market Index Price | BM-System Sell Spread | Daily VLP Revenue | Total BM Energy
Row 4: Avg System Buy Price | Supplier Comp | Net Spread | Effective Revenue
Row 5: Avg System Sell Price | VLP Revenue | Contango Index | Coverage Reliability

Each metric shows:
- Current value (large number)
- Sparkline showing trend from 00:00 (48 settlement periods)
"""

import sys
import logging
from datetime import datetime, date
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd
import numpy as np

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = 'inner-cinema-credentials.json'

# Layout configuration
KPI_START_ROW = 65  # Start after existing content
KPI_START_COL_LETTER = 'A'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_market_kpis(bq_client):
    """
    Fetch all market KPIs for today's 48 settlement periods
    Returns DataFrame with 48 periods and all metrics
    """
    
    today = date.today()
    
    query = f"""
    WITH
    -- Get today's settlement periods (48 periods)
    periods AS (
      SELECT period
      FROM UNNEST(GENERATE_ARRAY(1, 48)) AS period
    ),
    
    -- BOALF Acceptance Prices (BM accepted prices)
    boalf_prices AS (
      SELECT
        settlementPeriod as period,
        AVG(acceptancePrice) as avg_acceptance_price,
        STDDEV(acceptancePrice) as price_volatility,
        SUM(acceptanceVolume) as total_bm_energy_mwh,
        SUM(acceptanceVolume * acceptancePrice) / NULLIF(SUM(acceptanceVolume), 0) as volume_weighted_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{today}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
      GROUP BY period
    ),
    
    -- MID Market Index Prices (wholesale day-ahead)
    mid_prices AS (
      SELECT
        settlementPeriod as period,
        AVG(price) as avg_mid_price,
        SUM(volume * price) / NULLIF(SUM(volume), 0) as mid_vwap
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
      WHERE CAST(settlementDate AS DATE) = '{today}'
        AND price > 0
      GROUP BY period
    ),
    
    -- System Buy/Sell Prices (imbalance prices)
    -- Use bmrs_costs (covers all data including today via IRIS backfill)
    system_prices AS (
      SELECT
        settlementPeriod as period,
        AVG(systemBuyPrice) as avg_system_buy,
        AVG(systemSellPrice) as avg_system_sell,
        AVG((systemBuyPrice + systemSellPrice) / 2) as avg_imbalance
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) = '{today}'
      GROUP BY period
    ),
    
    -- VLP Specific Revenue (VLP units only)
    vlp_revenue AS (
      SELECT
        settlementPeriod as period,
        SUM(acceptanceVolume * acceptancePrice) as vlp_revenue_gbp,
        AVG(acceptancePrice) as vlp_avg_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{today}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
        AND (bmUnit LIKE '2__%' OR bmUnit LIKE 'V__%')  -- VLP units
      GROUP BY period
    ),
    
    -- Supplier vs VLP comparison (non-VLP units)
    supplier_comp AS (
      SELECT
        settlementPeriod as period,
        AVG(acceptancePrice) as supplier_avg_price,
        SUM(acceptanceVolume * acceptancePrice) / NULLIF(SUM(acceptanceVolume), 0) as supplier_vwap
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{today}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
        AND bmUnit NOT LIKE '2__%' 
        AND bmUnit NOT LIKE 'V__%'  -- Non-VLP units
      GROUP BY period
    )
    
    SELECT
      p.period,
      
      -- Row 1 KPIs
      ROUND(COALESCE(b.avg_acceptance_price, 0), 2) as avg_acceptance_price,
      ROUND(COALESCE(b.avg_acceptance_price - m.avg_mid_price, 0), 2) as bm_mid_spread,
      ROUND(COALESCE(s.supplier_avg_price - v.vlp_avg_price, 0), 2) as supplier_vlp_diff,
      ROUND(COALESCE((b.avg_acceptance_price - sys.avg_imbalance) / NULLIF(sys.avg_imbalance, 0) * 100, 0), 2) as imbalance_premium_index,
      
      -- Row 2 KPIs
      ROUND(COALESCE(b.volume_weighted_price, 0), 2) as volume_weighted_price,
      ROUND(COALESCE(b.avg_acceptance_price - sys.avg_system_buy, 0), 2) as bm_system_buy_spread,
      ROUND(COALESCE(s.supplier_vwap, 0), 2) as daily_comp_gbp_mwh,
      ROUND(COALESCE(b.price_volatility, 0), 2) as price_volatility_sigma,
      
      -- Row 3 KPIs
      ROUND(COALESCE(m.avg_mid_price, 0), 2) as avg_market_index_price,
      ROUND(COALESCE(b.avg_acceptance_price - sys.avg_system_sell, 0), 2) as bm_system_sell_spread,
      ROUND(COALESCE(v.vlp_revenue_gbp, 0), 0) as daily_vlp_revenue_gbp,
      ROUND(COALESCE(b.total_bm_energy_mwh, 0), 0) as total_bm_energy_mwh,
      
      -- Row 4 KPIs
      ROUND(COALESCE(sys.avg_system_buy, 0), 2) as avg_system_buy_price,
      ROUND(COALESCE(s.supplier_vwap, 0), 2) as supplier_comp_gbp_mwh,
      ROUND(COALESCE(b.avg_acceptance_price - sys.avg_imbalance, 0), 2) as net_spread,
      ROUND(COALESCE(v.vlp_revenue_gbp / NULLIF(b.total_bm_energy_mwh, 0) * 1000 * 365, 0), 0) as effective_revenue_gbp_kw_yr,
      
      -- Row 5 KPIs
      ROUND(COALESCE(sys.avg_system_sell, 0), 2) as avg_system_sell_price,
      ROUND(COALESCE(v.vlp_avg_price, 0), 2) as vlp_revenue_gbp_mwh,
      ROUND(COALESCE((m.avg_mid_price - sys.avg_imbalance) / NULLIF(sys.avg_imbalance, 0) * 100, 0), 2) as contango_index,
      ROUND(COALESCE(COUNT(*) OVER (ORDER BY p.period) * 100.0 / 48, 0), 1) as coverage_reliability_score
      
    FROM periods p
    LEFT JOIN boalf_prices b ON p.period = b.period
    LEFT JOIN mid_prices m ON p.period = m.period
    LEFT JOIN system_prices sys ON p.period = sys.period
    LEFT JOIN vlp_revenue v ON p.period = v.period
    LEFT JOIN supplier_comp s ON p.period = s.period
    ORDER BY p.period
    """
    
    logging.info("📊 Fetching market KPIs from BigQuery...")
    df = bq_client.query(query).to_dataframe()
    logging.info(f"   ✅ Retrieved {len(df)} periods of data")
    
    return df

def update_market_kpis_section(sheet, spreadsheet, df):
    """
    Update Google Sheets with market KPIs
    Layout: 5 rows × 4 columns of KPIs, each with current value + sparkline
    """
    
    logging.info("\n✍️  Writing market KPIs to Google Sheet...")
    
    # Define KPI configuration
    # Format: (row_offset, col_offset, label, column_name, format_suffix)
    kpi_config = [
        # Row 1
        (0, 0, "Avg Acceptance Price £/MWh", "avg_acceptance_price", ""),
        (0, 3, "BM–MID Spread", "bm_mid_spread", ""),
        (0, 6, "Supplier–VLP Diff £/MWh", "supplier_vlp_diff", ""),
        (0, 9, "Imbalance Premium Index", "imbalance_premium_index", "%"),
        
        # Row 2
        (3, 0, "Volume-Weighted Avg Price", "volume_weighted_price", ""),
        (3, 3, "BM–System Buy Spread", "bm_system_buy_spread", ""),
        (3, 6, "Daily Comp £", "daily_comp_gbp_mwh", ""),
        (3, 9, "Price Volatility σ £/MWh", "price_volatility_sigma", ""),
        
        # Row 3
        (6, 0, "Avg Market Index Price", "avg_market_index_price", ""),
        (6, 3, "BM–System Sell Spread", "bm_system_sell_spread", ""),
        (6, 6, "Daily VLP Revenue £", "daily_vlp_revenue_gbp", ""),
        (6, 9, "Total BM Energy MWh", "total_bm_energy_mwh", ""),
        
        # Row 4
        (9, 0, "Avg System Buy Price", "avg_system_buy_price", ""),
        (9, 3, "Supplier Comp £/MWh", "supplier_comp_gbp_mwh", ""),
        (9, 6, "Net Spread £", "net_spread", ""),
        (9, 9, "Effective Revenue £/kW-yr", "effective_revenue_gbp_kw_yr", ""),
        
        # Row 5
        (12, 0, "Avg System Sell Price", "avg_system_sell_price", ""),
        (12, 3, "VLP Revenue £/MWh", "vlp_revenue_gbp_mwh", ""),
        (12, 6, "Contango Index", "contango_index", ""),
        (12, 9, "Coverage Reliability Score", "coverage_reliability_score", "%"),
    ]
    
    updates = []
    
    # Add section header
    header_row = KPI_START_ROW
    updates.append({
        'range': f'A{header_row}',
        'values': [['📊 MARKET METRICS & ANALYSIS']]
    })
    
    # Add timestamp
    updates.append({
        'range': f'K{header_row}',
        'values': [[f"Updated: {datetime.now().strftime('%H:%M:%S')}"]]
    })
    
    # Map column names to Data_Hidden rows (rows 27-50 available)
    # We'll assign each unique column a row starting at 27
    unique_cols = list(set([col_name for _, _, _, col_name, _ in kpi_config]))
    col_to_row = {col_name: 27 + idx for idx, col_name in enumerate(unique_cols)}
    
    # Create each KPI cell
    for row_offset, col_offset, label, col_name, suffix in kpi_config:
        kpi_row = KPI_START_ROW + 2 + row_offset
        
        # Calculate column letters
        label_col = chr(ord('A') + col_offset)
        value_col = chr(ord('A') + col_offset)
        sparkline_col = chr(ord('A') + col_offset + 1)
        
        # Get current value (latest non-zero period)
        current_value = df[df[col_name] != 0][col_name].iloc[-1] if len(df[df[col_name] != 0]) > 0 else 0
        
        # Label
        updates.append({
            'range': f'{label_col}{kpi_row}',
            'values': [[label]]
        })
        
        # Current value
        value_display = f"{current_value}{suffix}"
        updates.append({
            'range': f'{value_col}{kpi_row + 1}',
            'values': [[value_display]]
        })
        
        # Get Data_Hidden row for this metric
        data_hidden_row = col_to_row.get(col_name, 27)
        
        # Sparkline formula
        sparkline_formula = (
            f'=SPARKLINE(Data_Hidden!$B${data_hidden_row}:$AW${data_hidden_row}, '
            f'{{"charttype","column";"color","#4285F4"}})'
        )
        
        updates.append({
            'range': f'{sparkline_col}{kpi_row + 1}',
            'values': [[sparkline_formula]]
        })
    
    # Batch update
    if updates:
        sheet.batch_update(updates)
        logging.info(f"   ✅ Updated {len(kpi_config)} market KPIs")
    
    # Write timeseries data to Data_Hidden sheet
    write_timeseries_data(spreadsheet, df, kpi_config)

def write_timeseries_data(spreadsheet, df, kpi_config):
    """Write 48-period timeseries to Data_Hidden sheet for sparklines"""
    
    logging.info("\n📈 Writing timeseries data to Data_Hidden sheet...")
    
    # Get Data_Hidden worksheet
    try:
        data_hidden = spreadsheet.worksheet('Data_Hidden')
    except Exception as e:
        logging.error(f"   ❌ Data_Hidden sheet not found: {e}")
        return
    
    updates = []
    
    # Extract unique column names from config
    unique_cols = list(set([col_name for _, _, _, col_name, _ in kpi_config]))
    
    # Starting row in Data_Hidden (rows 27-50 available, current usage: 2-26)
    START_ROW = 27
    
    # Write each metric's timeseries
    for idx, col_name in enumerate(unique_cols):
        data_row = START_ROW + idx
        
        # Safety check - don't exceed sheet limits
        if data_row > 50:
            logging.warning(f"   ⚠️  Skipping {col_name} - would exceed sheet limit (row {data_row})")
            continue
        
        # Get 48 periods of data
        values = df[col_name].fillna(0).tolist()
        
        # Ensure we have 48 values (pad if necessary)
        while len(values) < 48:
            values.append(0)
        values = values[:48]
        
        # Write to Data_Hidden (columns B-AW = 48 columns)
        updates.append({
            'range': f'B{data_row}:AW{data_row}',
            'values': [values]
        })
    
    if updates:
        data_hidden.batch_update(updates)
        logging.info(f"   ✅ Wrote {len(updates)} metric timeseries to Data_Hidden (rows {START_ROW}-{START_ROW + len(updates) - 1})")

def main():
    """Main execution"""
    
    print("\n" + "=" * 80)
    print("⚡ ADDING MARKET KPIs TO LIVE DASHBOARD V2")
    print("=" * 80)
    
    # Initialize clients
    logging.info("\n🔧 Connecting to BigQuery and Google Sheets...")
    
    creds = service_account.Credentials.from_service_account_file(
        SA_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive']
    )
    
    bq_client = bigquery.Client(credentials=creds, project=PROJECT_ID, location='US')
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    logging.info("   ✅ Connected")
    
    # Fetch data
    df = get_market_kpis(bq_client)
    
    if df.empty:
        logging.error("❌ No data retrieved from BigQuery!")
        return 1
    
    # Update sheet
    update_market_kpis_section(sheet, spreadsheet, df)
    
    print("\n" + "=" * 80)
    print("✅ MARKET KPIs UPDATE COMPLETE")
    print("=" * 80)
    print(f"\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
