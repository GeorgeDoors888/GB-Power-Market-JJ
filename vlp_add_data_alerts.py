#!/usr/bin/env python3
"""
VLP Data Validation & Alerts
Checks for anomalies and adds alert indicators
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials as BQCredentials
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
VIEW_NAME = 'v_btm_bess_inputs'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

def get_bigquery_client():
    """Initialize BigQuery client"""
    creds = BQCredentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    return bigquery.Client(project=PROJECT_ID, location='US', credentials=creds)

def get_sheets_client():
    """Initialize Google Sheets client"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def check_data_quality():
    """Check for data quality issues"""
    client = get_bigquery_client()
    
    alerts = []
    
    # 1. Check for zero prices
    query = f"""
    SELECT COUNT(*) as zero_price_count
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 7
    AND ssp_charge = 0
    """
    result = client.query(query).to_dataframe()
    zero_count = result.iloc[0]['zero_price_count']
    
    if zero_count > 0:
        alerts.append({
            'type': 'ZERO_PRICE',
            'severity': 'WARNING',
            'icon': '⚠️',
            'message': f'{zero_count} periods with £0.00 market price in last 7 days'
        })
    
    # 2. Check for negative pricing opportunities
    query = f"""
    SELECT COUNT(*) as neg_count, SUM(paid_to_charge_amount) as total_paid
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 7
    AND negative_pricing = TRUE
    AND paid_to_charge_amount > 0
    """
    result = client.query(query).to_dataframe()
    neg_count = result.iloc[0]['neg_count']
    total_paid = result.iloc[0]['total_paid']
    if total_paid is None or str(total_paid) == '<NA>':
        total_paid = 0
    else:
        total_paid = float(total_paid)
    
    if neg_count > 0:
        alerts.append({
            'type': 'NEGATIVE_PRICING',
            'severity': 'OPPORTUNITY',
            'icon': '🔥',
            'message': f'{neg_count} negative pricing events! £{total_paid:.2f}/MWh paid to charge'
        })
    
    # 3. Check for high profit opportunities
    query = f"""
    SELECT COUNT(*) as high_profit_count, MAX(net_margin_per_mwh) as max_profit
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 7
    AND net_margin_per_mwh > 200
    """
    result = client.query(query).to_dataframe()
    high_count = result.iloc[0]['high_profit_count']
    max_profit = result.iloc[0]['max_profit']
    if max_profit is None or str(max_profit) == '<NA>':
        max_profit = 0
    else:
        max_profit = float(max_profit)
    
    if high_count > 0:
        alerts.append({
            'type': 'HIGH_PROFIT',
            'severity': 'OPPORTUNITY',
            'icon': '💰',
            'message': f'{high_count} periods with >£200/MWh profit! Max: £{max_profit:.2f}'
        })
    
    # 4. Check data freshness (IRIS)
    query = f"""
    SELECT MAX(settlementDate) as latest_date,
           MAX(settlementPeriod) as latest_period
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    """
    result = client.query(query).to_dataframe()
    latest_date = result.iloc[0]['latest_date']
    latest_period = result.iloc[0]['latest_period']
    
    # Calculate expected latest period
    now = datetime.now()
    current_period = ((now.hour * 2) + (1 if now.minute >= 30 else 0)) + 1
    
    if latest_date.date() < now.date() or (latest_date.date() == now.date() and latest_period < current_period - 2):
        alerts.append({
            'type': 'STALE_DATA',
            'severity': 'ERROR',
            'icon': '🕐',
            'message': f'Data may be stale. Latest: {latest_date.date()} P{latest_period}'
        })
    else:
        alerts.append({
            'type': 'DATA_FRESH',
            'severity': 'OK',
            'icon': '✅',
            'message': f'Data is current: {latest_date.date()} P{latest_period}'
        })
    
    # 5. Check for missing services
    query = f"""
    SELECT 
        SUM(CASE WHEN dc_revenue_per_mwh = 0 THEN 1 ELSE 0 END) as dc_zero,
        SUM(CASE WHEN bm_acceptance_count = 0 THEN 1 ELSE 0 END) as bm_zero
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= CURRENT_DATE() - 1
    """
    result = client.query(query).to_dataframe()
    
    if result.iloc[0]['dc_zero'] > 40:  # More than 40 out of 48 periods
        alerts.append({
            'type': 'SERVICE_MISSING',
            'severity': 'WARNING',
            'icon': '⚠️',
            'message': 'DC (Dynamic Containment) may not be active'
        })
    
    return alerts

def write_alerts_to_sheet(alerts):
    """Write alerts to Google Sheets"""
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet('VLP Revenue')
    
    # Write alerts starting at row 36 (below charts area)
    alert_data = [['🚨 SYSTEM ALERTS & NOTIFICATIONS']]
    alert_data.append([''])  # Blank row
    
    for alert in alerts:
        severity_color = {
            'OK': '✅',
            'OPPORTUNITY': '🌟',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }.get(alert['severity'], '•')
        
        alert_data.append([f"{alert['icon']} {alert['message']}"])
    
    # Write to sheet
    worksheet.update(values=alert_data, range_name='A36')
    
    # Format alerts section
    sheet_id = worksheet.id
    requests = [
        # Header
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 35,
                    'endRowIndex': 36,
                    'startColumnIndex': 0,
                    'endColumnIndex': 6
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.8, 'green': 0.0, 'blue': 0.0},
                        'textFormat': {
                            'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                            'fontSize': 14,
                            'bold': True
                        }
                    }
                },
                'fields': 'userEnteredFormat'
            }
        },
        # Alert rows background
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 37,
                    'endRowIndex': 37 + len(alerts),
                    'startColumnIndex': 0,
                    'endColumnIndex': 6
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 1.0, 'green': 0.95, 'blue': 0.85}
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        }
    ]
    
    worksheet.spreadsheet.batch_update({'requests': requests})
    
    print(f"✅ Added {len(alerts)} alerts to dashboard")

def main():
    """Main execution"""
    print("=" * 80)
    print("VLP DATA VALIDATION & ALERTS")
    print("=" * 80)
    print()
    
    print("🔍 Checking data quality...")
    alerts = check_data_quality()
    
    print()
    print("📊 Alert Summary:")
    for alert in alerts:
        print(f"   {alert['icon']} [{alert['severity']}] {alert['message']}")
    
    print()
    print("📝 Writing alerts to dashboard...")
    write_alerts_to_sheet(alerts)
    
    print()
    print("=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)
    print()
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

if __name__ == '__main__':
    main()
