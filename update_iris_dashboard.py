#!/usr/bin/env python3
"""
Auto-update IRIS Market Data section in Dashboard
Runs every 5 minutes via cron to keep data fresh
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime
import logging
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'iris_dashboard_updater.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
gs_creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(gs_creds)

# BigQuery
bq_credentials = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
bq_client = bigquery.Client(project=PROJECT_ID, location="US", credentials=bq_credentials)

logging.info("=" * 80)
logging.info("🔄 AUTO-UPDATING IRIS MARKET DATA")
logging.info("=" * 80)

try:
    spreadsheet = gc.open_by_key(SHEET_ID)
    dashboard = spreadsheet.worksheet('Dashboard')
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Query recent acceptances
    acceptance_query = f"""
    SELECT bmUnit, levelFrom, levelTo, acceptanceNumber,
           TIMESTAMP_DIFF(timeTo, timeFrom, MINUTE) as duration_min
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_iris`
    WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
    ORDER BY ingested_utc DESC
    LIMIT 5
    """
    
    acceptances = bq_client.query(acceptance_query).to_dataframe()
    
    # Query market prices
    price_query = f"""
    SELECT settlementPeriod, dataProvider, price, volume
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE settlementDate = CURRENT_DATE()
      AND dataProvider = 'APXMIDP'
    ORDER BY settlementPeriod DESC
    LIMIT 3
    """
    
    prices = bq_client.query(price_query).to_dataframe()
    
    # Build data rows
    start_row = 60
    
    data = [
        [''],
        [''],
        ['📊 REAL-TIME MARKET DATA (IRIS) - AUTO-UPDATED'],
        [f'🕒 Last Update: {timestamp}'],
        [''],
        ['⚙️ BID/OFFER ACCEPTANCES (Last 30 min) - ✅ LIVE'],
        ['Unit', 'Action', 'Original Bid', 'Accepted Price', 'Duration'],
    ]
    
    # Add acceptance rows
    if not acceptances.empty:
        for _, row in acceptances.head(3).iterrows():
            action = "IMPORTING" if row['levelFrom'] < 0 else "EXPORTING"
            data.append([
                row['bmUnit'],
                action,
                f"£{row['levelFrom']:.2f}/MWh",
                f"£{row['levelTo']:.2f}/MWh",
                f"{row['duration_min']:.0f} min"
            ])
        logging.info(f"✅ Added {len(acceptances)} acceptances")
    else:
        data.append(['No acceptances in last 30 minutes', '', '', '', ''])
    
    data.extend([
        [''],
        ['💰 CURRENT MARKET PRICES (Today)'],
        ['Settlement Period', 'Time', 'Price', 'Volume', 'Source'],
    ])
    
    # Add price rows
    if not prices.empty:
        for _, row in prices.iterrows():
            sp = int(row['settlementPeriod'])
            time_label = f"{(sp-1)//2:02d}:{30 if sp%2==0 else '00'}"
            data.append([
                f"SP{sp}",
                time_label,
                f"£{row['price']:.2f}/MWh",
                f"{row['volume']:.0f} MWh",
                row['dataProvider']
            ])
        logging.info(f"✅ Added {len(prices)} price periods")
    else:
        data.append(['No price data available', '', '', '', ''])
    
    data.extend([
        [''],
        ['📚 DATA FRESHNESS STATUS'],
        ['Stream', 'Status', 'Update Frequency'],
        ['Acceptances (boalf)', '✅ Real-time', 'Event-driven (continuous)'],
        ['Market Prices (mid)', '🔴 30-min lag', 'After settlement period ends'],
        ['Export Limits (mels)', '✅ Real-time', 'Event-driven'],
        ['Import Limits (mils)', '✅ Real-time', 'Event-driven'],
        ['Frequency (freq)', '✅ Real-time', 'Every 2 minutes'],
        [''],
        ['💡 ARBITRAGE OPPORTUNITY'],
    ])
    
    # Calculate simple arbitrage signal
    if not prices.empty and len(prices) >= 2:
        latest_price = prices.iloc[0]['price']
        prev_price = prices.iloc[1]['price']
        price_change = latest_price - prev_price
        
        if price_change > 10:
            signal = f"📈 RISING: +£{price_change:.2f}/MWh - Consider DISCHARGING"
        elif price_change < -10:
            signal = f"📉 FALLING: £{price_change:.2f}/MWh - Consider CHARGING"
        else:
            signal = f"➡️ STABLE: {price_change:+.2f}/MWh - Monitor"
        
        data.append([signal, '', '', '', ''])
        logging.info(f"💰 Price signal: {signal}")
    else:
        data.append(['Insufficient data for signal', '', '', '', ''])
    
    # Write to Dashboard
    dashboard.update(f'A{start_row}', data, value_input_option='USER_ENTERED')
    
    # Format headers
    dashboard.format(f'A{start_row+2}:H{start_row+2}', {
        'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 14}
    })
    
    logging.info(f"✅ Dashboard IRIS section updated ({len(data)} rows)")
    logging.info("=" * 80)
    
except Exception as e:
    logging.error(f"❌ Update failed: {e}")
    logging.exception("Full traceback:")
