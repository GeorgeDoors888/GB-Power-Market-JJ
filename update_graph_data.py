"""
Update Graph Data Area (A18:H28) with Settlement Period Data
Provides data for: Demand, Generation+Import, System Sell Price, Frequency
"""
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Sheet1"
BQ_PROJECT = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"

def get_sheets_client():
    """Get authenticated Google Sheets client"""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        creds = Credentials.from_service_account_file(
            'service-account-key.json',
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    except:
        import pickle
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        return gspread.authorize(creds)

def get_todays_settlement_data():
    """Fetch today's settlement period data from BigQuery"""
    client = bigquery.Client(project=BQ_PROJECT)
    
    # Get today's date
    today = datetime.now().date()
    
    query = f"""
    WITH generation_data AS (
        SELECT
            settlementDate,
            settlementPeriod,
            SUM(generation) as total_generation
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_fuelinst`
        WHERE DATE(settlementDate) = '{today}'
        GROUP BY settlementDate, settlementPeriod
    ),
    price_data AS (
        SELECT
            settlementDate,
            settlementPeriod,
            AVG(price) as system_sell_price
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_mid`
        WHERE DATE(settlementDate) = '{today}'
        GROUP BY settlementDate, settlementPeriod
    ),
    freq_data AS (
        SELECT
            CAST(measurementTime AS DATE) as measurementDate,
            CAST(FLOOR((EXTRACT(HOUR FROM CAST(measurementTime AS TIMESTAMP)) * 60 + 
                   EXTRACT(MINUTE FROM CAST(measurementTime AS TIMESTAMP))) / 30) + 1 AS INT64) as settlementPeriod,
            AVG(frequency) as avg_frequency
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_freq`
        WHERE CAST(measurementTime AS DATE) = '{today}'
        GROUP BY measurementDate, settlementPeriod
    )
    SELECT
        g.settlementPeriod,
        COALESCE(g.total_generation, 0) / 1000 as generation_gw,
        COALESCE(f.avg_frequency, 50.0) as frequency,
        COALESCE(p.system_sell_price, 0) as price
    FROM generation_data g
    LEFT JOIN price_data p USING (settlementDate, settlementPeriod)
    LEFT JOIN freq_data f ON g.settlementDate = f.measurementDate AND g.settlementPeriod = f.settlementPeriod
    WHERE g.settlementPeriod BETWEEN 1 AND 48
    ORDER BY g.settlementPeriod
    """
    
    print(f"�� Fetching settlement data for {today}...")
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("⚠️  No data found for today, using yesterday's data...")
        yesterday = today - timedelta(days=1)
        query = query.replace(f"'{today}'", f"'{yesterday}'")
        df = client.query(query).to_dataframe()
    
    return df

def create_graph_data_table(df):
    """Create formatted table for graph area (A18:H28)"""
    
    # Header row
    table_data = [[
        '📈 Settlement Period Data',
        '',
        '',
        '',
        '',
        '',
        '',
        ''
    ]]
    
    # Column headers
    table_data.append([
        'SP',
        'Generation (GW)',
        'Frequency (Hz)',
        'Price (£/MWh)',
        '',
        'SP',
        'Generation (GW)',
        'Frequency (Hz)'
    ])
    
    # Data rows (show first 9 settlement periods in this view)
    # Full data will be written elsewhere for the graph
    for i in range(min(9, len(df))):
        row = df.iloc[i]
        if i < 4:
            # First 4 rows with data from SP 1-4
            table_data.append([
                f"SP{int(row['settlementPeriod']):02d}",
                f"{row['generation_gw']:.1f}",
                f"{row['frequency']:.2f}",
                f"£{row['price']:.2f}",
                '',
                '',
                '',
                ''
            ])
        elif i == 4:
            # Row 5: Current SP indicator
            current_sp = int(datetime.now().hour * 2 + datetime.now().minute / 30) + 1
            table_data.append([
                f"→ Current: SP{current_sp:02d}",
                '',
                '',
                '',
                '',
                '',
                '',
                ''
            ])
        else:
            # Rows 6-9: Latest SPs
            sp_offset = i - 5
            if len(df) > (len(df) - 4 + sp_offset):
                row = df.iloc[-(4-sp_offset)]
                table_data.append([
                    f"SP{int(row['settlementPeriod']):02d}",
                    f"{row['generation_gw']:.1f}",
                    f"{row['frequency']:.2f}",
                    f"£{row['price']:.2f}",
                    '',
                    '',
                    '',
                    ''
                ])
    
    # Pad to 11 rows total (A18:H28 = 11 rows)
    while len(table_data) < 11:
        table_data.append(['', '', '', '', '', '', '', ''])
    
    return table_data[:11]  # Ensure exactly 11 rows

def main():
    print("=" * 60)
    print("📈 GRAPH DATA UPDATER (A18:H28)")
    print("=" * 60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Fetch data
    df = get_todays_settlement_data()
    print(f"✅ Retrieved {len(df)} settlement periods\n")
    
    # Create table
    table_data = create_graph_data_table(df)
    
    # Update sheet
    print("📝 Updating graph data area (A18:H28)...")
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    sheet.update(values=table_data, range_name='A18:H28')
    
    print("✅ Graph data updated successfully!")
    print(f"\n📊 Summary:")
    print(f"   Settlement Periods: {len(df)}")
    print(f"   Avg Generation: {df['generation_gw'].mean():.1f} GW")
    print(f"   Avg Frequency: {df['frequency'].mean():.2f} Hz")
    print(f"   Avg Price: £{df['price'].mean():.2f}/MWh")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
