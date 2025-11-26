#!/usr/bin/env python3
"""
Create Data Availability sheet in Dashboard spreadsheet
Shows all IRIS data from last 30 minutes in organized tables
"""
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

# BigQuery credentials
bq_credentials = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
bq_client = bigquery.Client(project=PROJECT_ID, location="US", credentials=bq_credentials)

# Google Sheets credentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
gs_creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(gs_creds)
spreadsheet = gc.open_by_key(SHEET_ID)

print("=" * 100)
print("📊 CREATING DATA AVAILABILITY SHEET")
print("=" * 100)

# Get current time
now_utc = datetime.now(pytz.UTC)
thirty_min_ago = now_utc - timedelta(minutes=30)

print(f"\n🕒 Current Time: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"🕒 Window: Last 30 minutes")

# Create or get the sheet
try:
    sheet = spreadsheet.worksheet('Data Availability')
    print("\n📄 Found existing 'Data Availability' sheet - clearing...")
    sheet.clear()
except:
    print("\n📄 Creating new 'Data Availability' sheet...")
    sheet = spreadsheet.add_worksheet(title='Data Availability', rows=1000, cols=20)

# Header
header_data = [
    [f'📊 IRIS DATA AVAILABILITY - Last 30 Minutes'],
    [f'🕒 Updated: {now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")}'],
    [''],
]

all_data = header_data

# Define all IRIS tables
iris_tables = {
    'bmrs_freq_iris': {
        'name': '⚡ System Frequency',
        'cols': ['measurementTime', 'frequency']
    },
    'bmrs_fuelinst_iris': {
        'name': '🔥 Fuel Generation Mix',
        'cols': ['settlementDate', 'settlementPeriod', 'fuelType', 'generation']
    },
    'bmrs_mid_iris': {
        'name': '💰 Market Index Prices',
        'cols': ['settlementDate', 'settlementPeriod', 'dataProvider', 'price', 'volume']
    },
    'bmrs_boalf_iris': {
        'name': '⚙️ Bid/Offer Acceptances',
        'cols': ['settlementDate', 'bmUnit', 'acceptanceNumber', 'levelFrom', 'levelTo']
    },
    'bmrs_mels_iris': {
        'name': '🚨 Maximum Export Limits',
        'cols': ['settlementDate', 'settlementPeriod', 'bmUnit', 'levelFrom', 'levelTo']
    },
    'bmrs_mils_iris': {
        'name': '🚨 Maximum Import Limits',
        'cols': ['settlementDate', 'settlementPeriod', 'bmUnit', 'levelFrom', 'levelTo']
    },
    'bmrs_indgen_iris': {
        'name': '🔌 Indicative Generation',
        'cols': ['settlementDate', 'settlementPeriod', 'boundary', 'generation']
    },
    'bmrs_inddem_iris': {
        'name': '🔌 Indicative Demand',
        'cols': ['settlementDate', 'settlementPeriod', 'boundary', 'demand']
    },
    'bmrs_indo_iris': {
        'name': '📊 National Demand Outturn',
        'cols': ['settlementDate', 'settlementPeriod', 'demand']
    },
    'bmrs_beb_iris': {
        'name': '💡 Balancing Energy Bids',
        'cols': ['settlementDate', 'settlementPeriod', 'bidId', 'quantity', 'energyPrice']
    },
}

# Query each table
for table_name, info in iris_tables.items():
    print(f"\n📋 Querying {table_name}...")
    
    # Add section header
    all_data.append([''])
    all_data.append([info['name']])
    all_data.append(['Status', 'Rows', 'Latest Ingest', 'Age (min)'])
    
    try:
        # Check data availability
        check_query = f"""
        SELECT MAX(ingested_utc) as latest_ingest, COUNT(*) as row_count
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
        """
        
        check_df = bq_client.query(check_query).to_dataframe()
        
        if check_df.empty or check_df['latest_ingest'].iloc[0] is None:
            all_data.append(['❌ NO DATA', 0, 'N/A', 'N/A'])
            all_data.append([''])
            continue
        
        latest_ingest = check_df['latest_ingest'].iloc[0]
        row_count = check_df['row_count'].iloc[0]
        age_minutes = (now_utc - latest_ingest.replace(tzinfo=pytz.UTC)).total_seconds() / 60
        
        status = "✅ FRESH" if age_minutes < 5 else "⚠️ RECENT" if age_minutes < 15 else "🔴 STALE"
        
        all_data.append([
            status,
            int(row_count),
            latest_ingest.strftime('%H:%M:%S UTC'),
            f'{age_minutes:.1f}'
        ])
        
        # Get sample data (last 10 rows)
        cols_str = ', '.join(info['cols'])
        sample_query = f"""
        SELECT {cols_str}
        FROM `{PROJECT_ID}.{DATASET}.{table_name}`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
        ORDER BY ingested_utc DESC
        LIMIT 10
        """
        
        sample_df = bq_client.query(sample_query).to_dataframe()
        
        if not sample_df.empty:
            all_data.append([''])
            # Add column headers
            all_data.append(info['cols'])
            
            # Add data rows
            for _, row in sample_df.iterrows():
                row_data = []
                for col in info['cols']:
                    val = row[col]
                    if pd.isna(val):
                        row_data.append('')
                    elif isinstance(val, (int, float)):
                        row_data.append(str(val))
                    else:
                        row_data.append(str(val))
                all_data.append(row_data)
        
        all_data.append([''])
        
    except Exception as e:
        all_data.append([f'❌ ERROR: {str(e)[:100]}', '', '', ''])
        all_data.append([''])

# Add summary at top
summary_row = 4  # After header
all_data.insert(3, ['=== SUMMARY ==='])
all_data.insert(4, ['Category', 'Table', 'Status', 'Rows'])

# Write to sheet
print(f"\n💾 Writing {len(all_data)} rows to sheet...")
sheet.update('A1', all_data, value_input_option='USER_ENTERED')

# Format header
sheet.format('A1:T3', {
    'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 12}
})

print("\n✅ Data Availability sheet created!")
print("=" * 100)
