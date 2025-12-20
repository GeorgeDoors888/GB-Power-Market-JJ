#!/usr/bin/env python3
"""
BM KPI Deployment with Explicit HTTP Timeouts
Fixes: HTTPSConnectionPool read timeout by setting connection/read timeouts
"""
import time
from datetime import date, datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread.http_client import HTTPClient
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SA_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Custom HTTP client with explicit timeouts
class TimeoutHTTPClient(HTTPClient):
    """Custom HTTP client with timeout configuration"""
    def __init__(self, auth, timeout=(10, 30)):
        """
        Args:
            auth: Credentials
            timeout: (connect_timeout, read_timeout) in seconds
        """
        super().__init__(auth)
        self.timeout = timeout

        # Configure retries and timeouts on the session
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Monkey-patch the session's request method to add timeout
        original_request = self.session.request
        def request_with_timeout(*args, **kwargs):
            kwargs.setdefault('timeout', self.timeout)
            return original_request(*args, **kwargs)
        self.session.request = request_with_timeout

def get_complete_boalf_data():
    """Query BigQuery for most recent complete BOALF dataset"""
    print("📊 Connecting to BigQuery...")
    credentials = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=['https://www.googleapis.com/auth/bigquery']
    )
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID, location='US')

    print("🔍 Finding most recent complete BOALF data...")
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

    result = client.query(check_query).to_dataframe()
    if len(result) == 0:
        raise ValueError("No complete BOALF data found in last 7 days")

    data_date = result.iloc[0]['date']
    num_periods = result.iloc[0]['num_periods']
    print(f"✅ Using data from {data_date} ({num_periods} periods)")

    # Get full KPI data
    print("📈 Querying KPI data...")
    query = f"""
    WITH boalf AS (
      SELECT
        settlementPeriod as period,
        AVG(acceptancePrice) as avg_accept,
        SUM(acceptanceVolume * acceptancePrice) / NULLIF(SUM(acceptanceVolume), 0) as vol_wtd,
        STDDEV(acceptancePrice) as volatility,
        SUM(acceptanceVolume) as energy_mwh
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) = '{data_date}'
        AND validation_flag = 'Valid'
        AND acceptancePrice IS NOT NULL
      GROUP BY period
    )
    SELECT
      p as period,
      COALESCE(b.avg_accept, 0) as avg_accept,
      COALESCE(b.vol_wtd, 0) as vol_wtd,
      COALESCE(b.volatility, 0) as volatility,
      COALESCE(b.energy_mwh, 0) as energy_mwh
    FROM UNNEST(GENERATE_ARRAY(1, 48)) as p
    LEFT JOIN boalf b ON p = b.period
    ORDER BY p
    """

    df = client.query(query).to_dataframe()
    df.attrs['data_date'] = data_date

    avg = df['avg_accept'].mean()
    vol = df['vol_wtd'].mean()
    print(f"✅ Retrieved {len(df)} periods")
    print(f"   Avg Accept: £{avg:.2f}/MWh, Vol-Wtd: £{vol:.2f}/MWh")

    return df

def deploy_to_dashboard(df):
    """Deploy KPIs to Google Sheets with timeout protection"""
    data_date = df.attrs['data_date']
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print("\n📝 Connecting to Google Sheets (with 10s/30s timeouts)...")

    # Create custom HTTP client with timeouts
    scopes = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=scopes
    )

    # Initialize gspread with custom timeout client
    gc = gspread.Client(auth=credentials, http_client=TimeoutHTTPClient)

    print("📂 Opening spreadsheet...")
    ss = gc.open_by_key(SPREADSHEET_ID)
    print(f"✅ Opened: {ss.title}")

    sheet = ss.worksheet('Live Dashboard v2')
    print(f"✅ Got worksheet: {sheet.title}")

    # Prepare KPI values
    avg_accept = df['avg_accept'].mean()
    vol_wtd = df['vol_wtd'].mean()
    volatility = df['volatility'].mean()
    energy = df['energy_mwh'].sum()

    print("\n💾 Deploying KPIs...")

    # Batch 1: Headers and first row values (delay after)
    batch1 = [
        {'range': 'L13', 'values': [[f'⚡ BM KPIs (Data: {data_date}, Updated: {timestamp})']]},
        {'range': 'M13', 'values': [['Avg Accept']]},
        {'range': 'M14', 'values': [[f'£{avg_accept:.2f}']]},
        {'range': 'Q13', 'values': [['Vol-Wtd']]},
        {'range': 'Q14', 'values': [[f'£{vol_wtd:.2f}']]},
    ]
    sheet.batch_update(batch1, value_input_option='USER_ENTERED')
    print("   ✅ Batch 1: Headers + Row 1 values")
    time.sleep(2)  # Rate limit protection

    # Batch 2: Second row
    batch2 = [
        {'range': 'M15', 'values': [['Volatility']]},
        {'range': 'M16', 'values': [[f'£{volatility:.2f}']]},
        {'range': 'Q15', 'values': [['BM Energy']]},
        {'range': 'Q16', 'values': [[f'{energy:.0f} MWh']]},
    ]
    sheet.batch_update(batch2, value_input_option='USER_ENTERED')
    print("   ✅ Batch 2: Row 2 values")
    time.sleep(2)

    # Get or create Data_Hidden sheet
    print("\n📊 Setting up Data_Hidden sheet...")
    try:
        data_hidden = ss.worksheet('Data_Hidden')
        print("   ✅ Found existing Data_Hidden")
    except gspread.exceptions.WorksheetNotFound:
        print("   ℹ️ Creating Data_Hidden...")
        data_hidden = ss.add_worksheet('Data_Hidden', 100, 50)
        print("   ✅ Created Data_Hidden")
    time.sleep(1)

    # Write timeseries data
    print("📈 Writing timeseries data...")
    row_avg = ['avg_accept'] + df['avg_accept'].tolist()
    row_vol = ['vol_wtd'] + df['vol_wtd'].tolist()
    row_volatility = ['volatility'] + df['volatility'].tolist()
    row_energy = ['energy_mwh'] + df['energy_mwh'].tolist()

    data_hidden.update(
        values=[row_avg, row_vol, row_volatility, row_energy],
        range_name='A27:AW30'
    )
    print("   ✅ Written 4 timeseries to rows 27-30")
    time.sleep(2)

    # Add sparklines
    print("✨ Adding sparklines...")
    sparklines = [
        {'range': 'N14', 'values': [['=SPARKLINE(Data_Hidden!$B$27:$AW$27,{"charttype","line";"linewidth",2;"color","#3498db"})']]},
        {'range': 'R14', 'values': [['=SPARKLINE(Data_Hidden!$B$28:$AW$28,{"charttype","line";"linewidth",2;"color","#3498db"})']]},
        {'range': 'N16', 'values': [['=SPARKLINE(Data_Hidden!$B$29:$AW$29,{"charttype","line";"linewidth",2;"color","#e74c3c"})']]},
        {'range': 'R16', 'values': [['=SPARKLINE(Data_Hidden!$B$30:$AW$30,{"charttype","line";"linewidth",2;"color","#2ecc71"})']]},
    ]
    sheet.batch_update(sparklines, value_input_option='USER_ENTERED')
    print("   ✅ Added 4 sparklines")

    print(f"\n✅ DEPLOYMENT COMPLETE!")
    print(f"   Spreadsheet: {SPREADSHEET_ID}")
    print(f"   Data date: {data_date}")
    print(f"   Avg Accept: £{avg_accept:.2f}/MWh")
    print(f"   Vol-Wtd: £{vol_wtd:.2f}/MWh")

def main():
    """Main execution with timeout handling"""
    print("=" * 60)
    print("🚀 BM Market KPIs Deployment (Timeout-Protected)")
    print("=" * 60)
    print()

    try:
        # Get data from BigQuery
        df = get_complete_boalf_data()

        # Deploy to Google Sheets
        deploy_to_dashboard(df)

        print("\n" + "=" * 60)
        print("✅ SUCCESS - Check your dashboard!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
