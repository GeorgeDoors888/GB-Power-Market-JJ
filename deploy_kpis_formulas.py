#!/usr/bin/env python3
"""
BM Market KPIs Deployment - FORMULA VERSION

ROOT CAUSE DISCOVERED:
- Manual test proved: Formulas persist (=1+1 → 2) but raw values disappear
- Spreadsheet has Apps Script or validation rejecting non-formula cells
- 900 duplicate protections were removed but issue persists

SOLUTION:
- Deploy values as formulas referencing Data_Hidden cells
- Data_Hidden contains the raw values written by Python
- Formulas bypass whatever is clearing raw values
"""

from google.cloud import bigquery
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# === Configuration ===
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
WORKSHEET_NAME = "Live Dashboard v2"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# === Custom HTTP Client with Timeout ===
class TimeoutHTTPClient(gspread.http_client.HTTPClient):
    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout', (10, 30))  # 10s connect, 30s read
        return super().request(*args, **kwargs)

def get_complete_boalf_data():
    """Find most recent date with complete BOALF data (>=40 periods)"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = """
    SELECT
        CAST(settlementDate AS DATE) as date,
        COUNT(DISTINCT settlementPeriod) as period_count
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE settlementDate >= '2025-12-01'
      AND validation_flag = 'Valid'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 10
    """

    dates_df = client.query(query).to_dataframe()

    # Find first date with >= 40 periods (allows for some missing data)
    for _, row in dates_df.iterrows():
        if row['period_count'] >= 40:
            print(f"✅ Using data from {row['date']} ({row['period_count']} periods)")
            return str(row['date'])

    # Fallback to most recent
    if not dates_df.empty:
        date = str(dates_df.iloc[0]['date'])
        count = dates_df.iloc[0]['period_count']
        print(f"⚠️ Using incomplete data from {date} ({count} periods)")
        return date

    raise Exception("No BOALF data found in last 10 days!")

def query_boalf_kpis():
    """Query BOALF acceptance prices for BM KPIs"""
    client = bigquery.Client(project=PROJECT_ID, location="US")

    target_date = get_complete_boalf_data()

    query = f"""
    SELECT
        settlementPeriod,
        acceptancePrice as price_gbp_mwh,
        acceptanceVolume as volume_mw
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE CAST(settlementDate AS DATE) = '{target_date}'
      AND validation_flag = 'Valid'
      AND acceptancePrice IS NOT NULL
      AND acceptanceVolume IS NOT NULL
    ORDER BY settlementPeriod
    """

    df = client.query(query).to_dataframe()

    # Calculate KPIs
    avg_price = df['price_gbp_mwh'].mean()
    vol_weighted_price = (df['price_gbp_mwh'] * df['volume_mw'].abs()).sum() / df['volume_mw'].abs().sum()
    volatility = df['price_gbp_mwh'].std()

    print(f"✅ Retrieved {len(df)} periods")
    print(f"   Avg Accept: £{avg_price:.2f}/MWh, Vol-Wtd: £{vol_weighted_price:.2f}/MWh")

    return df, target_date, {
        'avg_price': avg_price,
        'vol_weighted': vol_weighted_price,
        'volatility': volatility
    }

def deploy_to_dashboard(df, date, kpis):
    """Deploy BM KPIs using FORMULAS that reference Data_Hidden"""

    # Setup Sheets client (simple version without custom timeout)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    ss = client.open_by_key(SPREADSHEET_ID)

    print(f"✅ Opened: {ss.title}")

    sheet = ss.worksheet(WORKSHEET_NAME)
    print(f"✅ Got worksheet: {sheet.title}")

    # === 1. WRITE RAW DATA TO Data_Hidden ===
    data_hidden = ss.worksheet('Data_Hidden')

    # Write BM KPI timeseries to Data_Hidden rows 27-30
    # Format: Row 27=Avg Price per period, Row 28=Vol-Wtd, Row 29=Volume, Row 30=Count

    # Aggregate by period (in case of duplicates)
    period_stats = df.groupby('settlementPeriod').agg({
        'price_gbp_mwh': 'mean',
        'volume_mw': 'sum'
    }).reset_index()

    # Ensure 48 periods
    all_periods = pd.DataFrame({'settlementPeriod': range(1, 49)})
    period_stats = all_periods.merge(period_stats, on='settlementPeriod', how='left')
    period_stats = period_stats.fillna(0)

    # Write timeseries (columns B-AW = 48 periods)
    data_rows = [
        ['BM_Avg_Price'] + period_stats['price_gbp_mwh'].tolist(),  # Row 27
        ['BM_Vol_Wtd'] + [(p * v) for p, v in zip(period_stats['price_gbp_mwh'], period_stats['volume_mw'])],  # Row 28
        ['BM_Volume'] + period_stats['volume_mw'].tolist(),  # Row 29
        ['BM_Count'] + [1 if v > 0 else 0 for v in period_stats['volume_mw']]  # Row 30
    ]

    data_hidden.update('A27:AW30', data_rows, value_input_option='USER_ENTERED')
    print(f"✅ Written 4 timeseries to Data_Hidden rows 27-30")
    time.sleep(1)

    # === 2. DEPLOY FORMULAS TO DASHBOARD ===
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # Batch 1: Header and formulas for row 1 (Avg Accept, Vol-Wtd)
    batch1 = [
        {
            'range': 'L13',
            'values': [[f"⚡ BM KPIs (Data: {date}, Updated: {timestamp})"]]
        },
        {
            'range': 'M13',
            'values': [['Avg Accept']]
        },
        {
            'range': 'M14',
            'values': [['=ROUND(AVERAGE(Data_Hidden!B27:AW27), 2)&" £/MWh"']]  # FORMULA!
        },
        {
            'range': 'Q13',
            'values': [['Vol-Wtd']]
        },
        {
            'range': 'Q14',
            'values': [['=ROUND(SUM(Data_Hidden!B28:AW28)/SUM(Data_Hidden!B29:AW29), 2)&" £/MWh"']]  # FORMULA!
        }
    ]

    sheet.batch_update(batch1, value_input_option='USER_ENTERED')
    print(f"   ✅ Batch 1: Headers + Formulas")
    time.sleep(2)

    # Batch 2: Row 2 formulas (Volatility, etc.)
    batch2 = [
        {
            'range': 'M15',
            'values': [['Volatility']]
        },
        {
            'range': 'M16',
            'values': [['=ROUND(STDEV(Data_Hidden!B27:AW27), 2)&" £/MWh"']]  # FORMULA!
        }
    ]

    sheet.batch_update(batch2, value_input_option='USER_ENTERED')
    print(f"   ✅ Batch 2: Volatility formula")
    time.sleep(2)

    # === 3. SPARKLINES ===
    sparklines = [
        {
            'range': 'N14',
            'values': [['=SPARKLINE(Data_Hidden!B27:AW27, {"charttype","column";"color","#3498db"})']]
        },
        {
            'range': 'R14',
            'values': [['=SPARKLINE(Data_Hidden!B28:AW28, {"charttype","line";"color","#e74c3c"})']]
        }
    ]

    try:
        sheet.batch_update(sparklines, value_input_option='USER_ENTERED')
        print(f"   ✅ Sparklines added")
    except Exception as e:
        print(f"   ⚠️ Sparklines failed (non-critical): {e}")

    print("\n✅ DEPLOYMENT COMPLETE!")
    print("=" * 60)

def main():
    print("=" * 60)
    print("🚀 BM Market KPIs Deployment (FORMULA VERSION)")
    print("=" * 60)

    print("\n📊 Connecting to BigQuery...")
    print("🔍 Finding most recent complete BOALF data...")

    df, date, kpis = query_boalf_kpis()

    print("\n📝 Connecting to Google Sheets...")
    deploy_to_dashboard(df, date, kpis)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
