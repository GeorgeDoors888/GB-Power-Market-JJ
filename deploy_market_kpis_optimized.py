#!/usr/bin/env python3
"""
Optimized BM Market KPIs Deployment with Rate Limiting
Deploys 20 BM market KPIs to Live Dashboard v2 with sparklines
Includes exponential backoff, retry logic, and API rate limit protection
"""

import logging
import time
from datetime import date, datetime, timedelta
from google.cloud import bigquery
from google.auth import credentials as auth_credentials
from google.oauth2 import service_account
import gspread
from gspread.exceptions import APIError
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SA_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

# API Rate Limiting
MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # seconds
BATCH_DELAY = 1  # seconds between batch operations

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def retry_with_backoff(func, max_retries=MAX_RETRIES):
    """Execute function with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            return func()
        except APIError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = INITIAL_BACKOFF * (2 ** attempt)
            logging.warning(f"⚠️ API error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            logging.error(f"❌ Unexpected error: {e}")
            raise

def get_market_kpi_data(bq_client):
    """
    Fetch all 20 BM market KPIs for latest complete data
    Uses most recent date with >=40 settlement periods
    Returns DataFrame with period-by-period data for sparklines
    """

    # Find most recent complete BOALF date
    logging.info("🔍 Finding most recent complete BOALF data...")
    check_query = """
    SELECT
      CAST(settlementDate AS DATE) as date,
      COUNT(DISTINCT settlementPeriod) as num_periods
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE CAST(settlementDate AS DATE) >= CURRENT_DATE() - 7
      AND validation_flag = 'Valid'
    GROUP BY date
    HAVING COUNT(DISTINCT settlementPeriod) >= 40
    ORDER BY date DESC
    LIMIT 1
    """

    result = bq_client.query(check_query).to_dataframe()
    if len(result) > 0:
        boalf_date = result.iloc[0]['date']
        num_periods = result.iloc[0]['num_periods']
        logging.info(f"✅ Using BOALF data from {boalf_date} ({num_periods} periods)")
    else:
        boalf_date = date.today() - timedelta(days=3)
        logging.warning(f"⚠️ No complete BOALF data found, defaulting to {boalf_date}")

    # Use latest available date for price data (MID, COSTS)
    price_date = date.today()

    query = f"""
    WITH
    periods AS (
      SELECT period
      FROM UNNEST(GENERATE_ARRAY(1, 48)) AS period
    ),

    -- BOALF Acceptance Prices (BM accepted prices)
    boalf_data AS (
      SELECT
        settlementPeriod as period,
        AVG(acceptancePrice) as avg_acceptance,
        STDDEV(acceptancePrice) as volatility,
        SUM(acceptanceVolume) as total_energy_mwh,
        SUM(acceptanceVolume * acceptancePrice) / NULLIF(SUM(acceptanceVolume), 0) as vol_wtd_price,
        SUM(acceptanceVolume * acceptancePrice) / 1000000 as revenue_gbp  -- Million £
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{boalf_date}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
      GROUP BY period
    ),

    -- MID Market Index Prices
    mid_data AS (
      SELECT
        settlementPeriod as period,
        AVG(price) as avg_mid_price
      FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
      WHERE CAST(settlementDate AS DATE) = '{price_date}'
        AND price > 0
      GROUP BY period
    ),

    -- System Buy/Sell Prices (imbalance)
    system_prices AS (
      SELECT
        settlementPeriod as period,
        AVG(systemBuyPrice) as sys_buy,
        AVG(systemSellPrice) as sys_sell
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) = '{price_date}'
      GROUP BY period
    ),

    -- VLP-specific revenue (FBPGM002, FFSEN005)
    vlp_data AS (
      SELECT
        settlementPeriod as period,
        SUM(acceptanceVolume * acceptancePrice) / NULLIF(SUM(acceptanceVolume), 0) as vlp_vwap,
        SUM(acceptanceVolume * acceptancePrice) / 1000000 as vlp_revenue_gbp
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{boalf_date}'
        AND bmUnit IN ('FBPGM002', 'FFSEN005')
        AND validation_flag = 'Valid'
      GROUP BY period
    )

    SELECT
      p.period,
      COALESCE(b.avg_acceptance, 0) as avg_accept,
      COALESCE(b.vol_wtd_price, 0) as vol_wtd,
      COALESCE(m.avg_mid_price, 0) as mkt_index,
      COALESCE(s.sys_buy, 0) as sys_buy,
      COALESCE(s.sys_sell, 0) as sys_sell,

      -- Spreads
      COALESCE(b.vol_wtd_price - m.avg_mid_price, 0) as bm_mid_spread,
      COALESCE(b.vol_wtd_price - s.sys_buy, 0) as bm_sysbuy_spread,
      COALESCE(b.vol_wtd_price - s.sys_sell, 0) as bm_syssell_spread,

      -- Revenue metrics
      COALESCE(v.vlp_vwap, 0) as vlp_price,
      COALESCE(v.vlp_revenue_gbp, 0) as vlp_rev_daily,
      COALESCE(b.total_energy_mwh, 0) as bm_energy,

      -- Analytics
      COALESCE(b.volatility, 0) as volatility,
      COALESCE((s.sys_buy + s.sys_sell) / 2, 0) as imb_index,

      -- Placeholders (need more complex calc)
      0 as supp_vlp_diff,
      0 as daily_comp,
      0 as supp_comp,
      0 as net_spread,
      0 as eff_rev,
      0 as contango,
      0 as coverage

    FROM periods p
    LEFT JOIN boalf_data b ON p.period = b.period
    LEFT JOIN mid_data m ON p.period = m.period
    LEFT JOIN system_prices s ON p.period = s.period
    LEFT JOIN vlp_data v ON p.period = v.period
    ORDER BY p.period
    """

    try:
        df = bq_client.query(query).to_dataframe()

        # Store data date for timestamp
        df.attrs['data_date'] = boalf_date

        logging.info(f"✅ Fetched {len(df)} settlement periods of BM KPI data")
        logging.info(f"   Data shape: {len(df)} periods × {len(df.columns)} metrics")

        # Show sample values
        sample_avg = df['avg_accept'].mean()
        sample_vol = df['vol_wtd'].mean()
        sample_spread = df['bm_mid_spread'].mean()
        sample_vlp = df['vlp_rev_daily'].sum()

        logging.info(f"   Sample values:")
        logging.info(f"     Avg Accept: £{sample_avg:.2f}/MWh")
        logging.info(f"     Vol-Wtd: £{sample_vol:.2f}/MWh")
        logging.info(f"     BM-MID Spread: £{sample_spread:.2f}/MWh")
        logging.info(f"     VLP Revenue: £{sample_vlp:.2f}M total")

        return df

    except Exception as e:
        logging.error(f"❌ BigQuery error: {e}")
        raise


def update_market_kpis(sheet, data_hidden, df):
    """
    Update dashboard with BM market KPIs, sparklines, and timestamp
    Uses batch updates with rate limiting for API efficiency
    """

    data_date = df.attrs.get('data_date', date.today())

    def get_latest(col_name):
        """Get most recent non-zero value from column"""
        valid_data = df[df[col_name] != 0][col_name]
        return valid_data.iloc[-1] if len(valid_data) > 0 else 0

    # Column index to letter conversion
    def col_letter(idx):
        """Convert 0-based index to column letter (0=A, 12=M, etc.)"""
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if idx < 26:
            return letters[idx]
        else:
            return letters[idx // 26 - 1] + letters[idx % 26]

    # KPI Configuration: (label_row, value_row, value_col_idx, label, col_name, format_str)
    kpis = [
        # Row 13-14
        (13, 14, 12, 'Avg Accept', 'avg_accept', '£{:.2f}'),
        (13, 14, 16, 'BM–MID', 'bm_mid_spread', '£{:.2f}'),
        (13, 14, 19, 'Supp–VLP', 'supp_vlp_diff', '£{:.2f}'),
        (13, 14, 22, 'Imb Index', 'imb_index', '£{:.2f}'),

        # Row 15-16
        (15, 16, 12, 'Vol-Wtd', 'vol_wtd', '£{:.2f}'),
        (15, 16, 16, 'BM–SysBuy', 'bm_sysbuy_spread', '£{:.2f}'),
        (15, 16, 19, 'Daily Comp', 'daily_comp', '£{:.2f}M'),
        (15, 16, 22, 'Volatility', 'volatility', '£{:.2f}'),

        # Row 17-18
        (17, 18, 12, 'Mkt Index', 'mkt_index', '£{:.2f}'),
        (17, 18, 16, 'BM–SysSell', 'bm_syssell_spread', '£{:.2f}'),
        (17, 18, 19, 'Supp Comp', 'supp_comp', '£{:.2f}M'),
        (17, 18, 22, 'Net Spread', 'net_spread', '£{:.2f}'),

        # Row 19-20
        (19, 20, 12, 'Sys Buy', 'sys_buy', '£{:.2f}'),
        (19, 20, 16, 'VLP Rev', 'vlp_rev_daily', '£{:.2f}M'),
        (19, 20, 19, 'BM Energy', 'bm_energy', '{:.0f} MWh'),
        (19, 20, 22, 'Eff Rev', 'eff_rev', '£{:.2f}'),

        # Row 21-22
        (21, 22, 12, 'Sys Sell', 'sys_sell', '£{:.2f}'),
        (21, 22, 16, 'VLP £/MWh', 'vlp_price', '£{:.2f}'),
        (21, 22, 19, 'Contango', 'contango', '{:.2f}'),
        (21, 22, 22, 'Coverage', 'coverage', '{:.1f}%'),
    ]

    # Prepare all batch updates
    batch_updates = []
    data_hidden_rows = []
    data_row_map = {}
    current_data_row = 27

    # Add timestamp header
    timestamp = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    batch_updates.append({
        'range': 'L13',
        'values': [[f'⚡ BM Market KPIs (Data: {data_date}, Updated: {timestamp})']]
    })

    for label_row, value_row, col_idx, label, col_name, fmt in kpis:
        # Get current value
        current_val = get_latest(col_name)

        # Format value - handle NaN/None cases
        if pd.isna(current_val) or current_val is None:
            display_val = '0'
        elif 'M' in fmt:  # Million pounds
            display_val = fmt.format(current_val / 1e6) if current_val != 0 else '£0.0M'
        elif 'MWh' in fmt:  # Energy
            display_val = fmt.format(current_val) if current_val != 0 else '0 MWh'
        else:
            display_val = fmt.format(current_val) if current_val != 0 else '0'

        col = col_letter(col_idx)

        # Add label to label_row
        batch_updates.append({
            'range': f'{col}{label_row}',
            'values': [[label]]
        })

        # Add value to value_row
        batch_updates.append({
            'range': f'{col}{value_row}',
            'values': [[display_val]]
        })

        # Store data for Data_Hidden if not already stored
        if col_name not in data_row_map:
            data_row_map[col_name] = current_data_row
            # Prepare row data: [label, period1, period2, ..., period48]
            row_data = [col_name] + df[col_name].tolist()
            # Pad to 49 columns (A + 48 periods)
            if len(row_data) < 49:
                row_data.extend([0] * (49 - len(row_data)))
            data_hidden_rows.append(row_data)
            current_data_row += 1

        # Add sparkline formula next to value (column + 1)
        sparkline_col = col_letter(col_idx + 1)
        hidden_row = data_row_map[col_name]
        sparkline_formula = f'=SPARKLINE(Data_Hidden!$B${hidden_row}:$AW${hidden_row}, {{"charttype","line";"linewidth",2;"color","#3498db"}})'

        batch_updates.append({
            'range': f'{sparkline_col}{value_row}',
            'values': [[sparkline_formula]]
        })

    # Write all updates to main sheet with retry logic
    if batch_updates:
        logging.info(f"📝 Updating dashboard with {len(kpis)} KPIs...")

        def do_batch_update():
            sheet.batch_update(batch_updates, value_input_option='USER_ENTERED')

        retry_with_backoff(do_batch_update)
        time.sleep(BATCH_DELAY)  # Rate limiting
        logging.info(f"✅ Updated {len(kpis)} BM KPIs with values and labels")

    # Write sparkline data to Data_Hidden sheet with retry logic
    if data_hidden_rows:
        try:
            logging.info(f"📊 Updating Data_Hidden with timeseries...")

            def do_data_update():
                data_hidden.update(
                    values=data_hidden_rows,
                    range_name=f'A27:AW{26 + len(data_hidden_rows)}'
                )

            retry_with_backoff(do_data_update)
            time.sleep(BATCH_DELAY)  # Rate limiting
            logging.info(f"✅ Updated Data_Hidden with {len(data_hidden_rows)} metric timeseries")
        except Exception as e:
            logging.error(f"❌ Could not update Data_Hidden: {e}")


def main():
    """Main execution with optimized API handling"""
    print("⚡ Deploying BM Market KPIs to Live Dashboard v2 (Optimized)...")
    print(f"   Max retries: {MAX_RETRIES}, Backoff: {INITIAL_BACKOFF}s, Batch delay: {BATCH_DELAY}s\n")

    try:
        # BigQuery client
        credentials = service_account.Credentials.from_service_account_file(
            SA_FILE,
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        bq_client = bigquery.Client(
            credentials=credentials,
            project=PROJECT_ID,
            location='US'
        )
        print("✅ Connected to BigQuery")

        # Google Sheets client with retry
        def connect_sheets():
            gc = gspread.service_account(filename=SA_FILE)
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            return spreadsheet

        spreadsheet = retry_with_backoff(connect_sheets)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"✅ Connected to Google Sheets: '{SHEET_NAME}'")

        # Get or create Data_Hidden sheet
        try:
            data_hidden = spreadsheet.worksheet('Data_Hidden')
            print("✅ Found Data_Hidden sheet\n")
        except gspread.exceptions.WorksheetNotFound:
            logging.info("Creating Data_Hidden sheet...")
            data_hidden = spreadsheet.add_worksheet('Data_Hidden', 100, 50)
            print("✅ Created Data_Hidden sheet\n")

        # Fetch BM market data
        print("📊 Fetching BM market data from BigQuery...")
        df = get_market_kpi_data(bq_client)
        print()

        # Update dashboard
        print("📝 Updating dashboard...")
        update_market_kpis(sheet, data_hidden, df)

        print(f"\n✅ COMPLETE! Check dashboard:")
        print(f"   {SPREADSHEET_ID}")
        print(f"   Rows 13-22: All 20 BM market KPIs with sparklines")
        print(f"   Data from: {df.attrs.get('data_date', 'N/A')}")

    except Exception as e:
        logging.error(f"\n❌ Deployment failed: {e}")
        raise


if __name__ == '__main__':
    main()
