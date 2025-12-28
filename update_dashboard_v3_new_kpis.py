#!/usr/bin/env python3
"""
Dashboard V3 - Replace KPIs from Row 13 with New Metrics + Sparklines
Deletes old data and adds: Real-time imbalance, EWAP, Dispatch Intensity, etc.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import pytz

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # GB Live 2 - CORRECT!
SHEET_NAME = 'Live Dashboard v2'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = 'inner-cinema-credentials.json'

def get_clients():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/bigquery'
        ]
    )
    sheets = build('sheets', 'v4', credentials=creds)
    bq = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    return sheets, bq


def get_imbalance_data(bq_client):
    """Get imbalance price data for KPIs and sparklines"""
    query = f"""
    WITH recent_data AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            systemSellPrice as price,
            TIMESTAMP_ADD(
                TIMESTAMP(CAST(settlementDate AS STRING)), 
                INTERVAL (settlementPeriod - 1) * 30 MINUTE
            ) as timestamp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        ORDER BY settlementDate DESC, settlementPeriod DESC
        LIMIT 1500
    )
    SELECT * FROM recent_data ORDER BY timestamp ASC
    """
    
    df = bq_client.query(query).to_dataframe()
    return df


def get_boalf_dispatch_data(bq_client):
    """Get BOALF dispatch data for intensity metrics"""
    query = f"""
    WITH recent_boalf AS (
        SELECT 
            DATE(CAST(acceptanceTime AS DATETIME)) as date,
            EXTRACT(HOUR FROM CAST(acceptanceTime AS DATETIME)) as hour,
            COUNT(*) as acceptance_count,
            AVG(CASE WHEN soFlag THEN 1 ELSE 0 END) as so_rate,
            AVG(CASE WHEN storFlag THEN 1 ELSE 0 END) as stor_rate
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE CAST(acceptanceTime AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 7 DAY)
        GROUP BY date, hour
        ORDER BY date DESC, hour DESC
    )
    SELECT * FROM recent_boalf
    LIMIT 200
    """
    
    df = bq_client.query(query).to_dataframe()
    return df


def get_current_kpis(imbalance_df, dispatch_df):
    """Calculate current KPI values"""
    
    # Latest imbalance price (real-time)
    latest_price = imbalance_df['price'].iloc[-1] if len(imbalance_df) > 0 else 0
    
    # 7-day metrics
    seven_days_ago = imbalance_df['timestamp'].max() - timedelta(days=7)
    df_7d = imbalance_df[imbalance_df['timestamp'] >= seven_days_ago]
    
    avg_7d = df_7d['price'].mean() if len(df_7d) > 0 else 0
    high_7d = df_7d['price'].max() if len(df_7d) > 0 else 0
    low_7d = df_7d['price'].min() if len(df_7d) > 0 else 0
    
    # 30-day metrics
    thirty_days_ago = imbalance_df['timestamp'].max() - timedelta(days=30)
    df_30d = imbalance_df[imbalance_df['timestamp'] >= thirty_days_ago]
    
    avg_30d = df_30d['price'].mean() if len(df_30d) > 0 else 0
    high_30d = df_30d['price'].max() if len(df_30d) > 0 else 0
    low_30d = df_30d['price'].min() if len(df_30d) > 0 else 0
    
    # Deviation calculations
    dev_from_7d = ((latest_price - avg_7d) / avg_7d * 100) if avg_7d > 0 else 0
    dev_30d_from_7d = ((avg_30d - avg_7d) / avg_7d * 100) if avg_7d > 0 else 0
    
    # Dispatch intensity (acceptances per hour)
    dispatch_intensity = dispatch_df['acceptance_count'].mean() if len(dispatch_df) > 0 else 0
    active_pct = (dispatch_df['so_rate'].mean() * 100) if len(dispatch_df) > 0 else 0
    
    # EWAP (placeholder - would need BOD data)
    ewap_offer = 0.0  # TODO: Calculate from BOD if needed
    
    return {
        'realtime_price': latest_price,
        'avg_7d': avg_7d,
        'high_7d': high_7d,
        'low_7d': low_7d,
        'avg_30d': avg_30d,
        'high_30d': high_30d,
        'low_30d': low_30d,
        'dev_from_7d': dev_from_7d,
        'dev_30d_from_7d': dev_30d_from_7d,
        'dispatch_intensity': dispatch_intensity,
        'active_pct': active_pct,
        'ewap_offer': ewap_offer
    }


def clear_old_data(sheets_service):
    """Clear rows 13+ (old KPIs and data)"""
    print("🗑️  Clearing old data from row 13 onwards...")
    
    requests = [{
        'deleteDimension': {
            'range': {
                'sheetId': 1471864390,  # Dashboard V3 sheet ID
                'dimension': 'ROWS',
                'startIndex': 12,  # Row 13 (0-indexed)
                'endIndex': 100   # Clear up to row 100
            }
        }
    }]
    
    body = {'requests': requests}
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=body
    ).execute()
    
    print("✅ Old data cleared")


def write_new_kpis(sheets_service, kpis, imbalance_df):
    """Write new KPIs starting from row 13"""
    print("📝 Writing new KPIs with sparklines...")
    
    # Prepare 7-day price data for sparkline
    seven_days_ago = imbalance_df['timestamp'].max() - timedelta(days=7)
    sparkline_data = imbalance_df[imbalance_df['timestamp'] >= seven_days_ago]['price'].tolist()
    sparkline_range = f"'Sparkline_Data'!A2:A{len(sparkline_data)+1}"  # Will create this sheet
    
    # New KPI layout starting from row 13
    values = [
        # Header
        ['⚡ MARKET DYNAMICS - 7 DAY VIEW', '', '', '', '', ''],
        [],
        # KPIs with labels, values, sparklines
        ['Real-time imbalance price', f'£{kpis["realtime_price"]:.2f}/MWh', f'=SPARKLINE({sparkline_range},{{"linewidth",2;"color1","blue"}})'],
        ['', f'£{kpis["avg_7d"]:.2f}/MWh', 'Rolling mean'],
        [],
        ['7-Day Average', f'£{kpis["avg_7d"]:.2f}/MWh', 'Rolling mean'],
        ['Deviation from 7d', f'{kpis["dev_from_7d"]:.2f}%', 'vs 7-day avg'],
        [],
        ['30-Day Average', f'£{kpis["avg_30d"]:.2f}/MWh', 'Rolling mean'],
        ['30-Day Low', f'£{kpis["low_30d"]:.2f}/MWh', 'Min price'],
        ['Deviation from 7d', f'{kpis["dev_30d_from_7d"]:.2f}%', 'vs 7-day avg'],
        [],
        ['EWAP Offer', f'£{kpis["ewap_offer"]:.2f}/MWh', 'Energy-weighted avg'],
        ['30-Day High', f'£{kpis["high_30d"]:.2f}/MWh', 'Max price'],
        [],
        ['Dispatch Intensity', f'{kpis["dispatch_intensity"]:.1f}/hr', f'Acceptances/hour • {kpis["active_pct"]:.1f}% active'],
        [],
        # Summary stats
        ['7-Day Average Price', f'£{kpis["avg_7d"]:.2f}/MWh', 'Daily avg'],
        ['7-Day High', f'£{kpis["high_7d"]:.2f}/MWh', 'Peak daily'],
    ]
    
    body = {
        'values': values
    }
    
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A13:F{12+len(values)}',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    print(f"✅ Wrote {len(values)} rows of new KPIs")


def create_sparkline_data_sheet(sheets_service, imbalance_df):
    """Create hidden sheet with sparkline data"""
    print("📊 Creating Sparkline_Data sheet...")
    
    # Check if sheet exists, delete if it does
    try:
        metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        for sheet in metadata.get('sheets', []):
            if sheet['properties']['title'] == 'Sparkline_Data':
                delete_request = [{
                    'deleteSheet': {
                        'sheetId': sheet['properties']['sheetId']
                    }
                }]
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID,
                    body={'requests': delete_request}
                ).execute()
                print("  Deleted existing Sparkline_Data sheet")
                break
    except Exception as e:
        print(f"  Note: {e}")
    
    # Create new sheet
    create_request = [{
        'addSheet': {
            'properties': {
                'title': 'Sparkline_Data',
                'hidden': True,
                'gridProperties': {
                    'rowCount': 1000,
                    'columnCount': 10
                }
            }
        }
    }]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': create_request}
    ).execute()
    
    # Write 7-day price data
    seven_days_ago = imbalance_df['timestamp'].max() - timedelta(days=7)
    sparkline_df = imbalance_df[imbalance_df['timestamp'] >= seven_days_ago][['timestamp', 'price']].copy()
    
    values = [['Timestamp', 'Price']]
    for _, row in sparkline_df.iterrows():
        values.append([row['timestamp'].strftime('%Y-%m-%d %H:%M'), row['price']])
    
    body = {'values': values}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Sparkline_Data!A1',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    print(f"✅ Created Sparkline_Data with {len(values)-1} data points")


def main():
    print("🔄 DASHBOARD V3 - NEW KPI UPDATE")
    print("="*80)
    
    sheets, bq = get_clients()
    
    # Get data
    print("\n1️⃣  Fetching imbalance price data...")
    imbalance_df = get_imbalance_data(bq)
    print(f"   ✅ Got {len(imbalance_df)} price records")
    
    print("\n2️⃣  Fetching dispatch/BOALF data...")
    dispatch_df = get_boalf_dispatch_data(bq)
    print(f"   ✅ Got {len(dispatch_df)} dispatch records")
    
    print("\n3️⃣  Calculating KPI values...")
    kpis = get_current_kpis(imbalance_df, dispatch_df)
    print("   ✅ KPIs calculated:")
    print(f"      Real-time price: £{kpis['realtime_price']:.2f}/MWh")
    print(f"      7-day avg: £{kpis['avg_7d']:.2f}/MWh")
    print(f"      30-day avg: £{kpis['avg_30d']:.2f}/MWh")
    print(f"      Dispatch intensity: {kpis['dispatch_intensity']:.1f}/hr")
    
    print("\n4️⃣  Creating sparkline data sheet...")
    create_sparkline_data_sheet(sheets, imbalance_df)
    
    print("\n5️⃣  Clearing old data...")
    clear_old_data(sheets)
    
    print("\n6️⃣  Writing new KPIs...")
    write_new_kpis(sheets, kpis, imbalance_df)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=1471864390")


if __name__ == '__main__':
    main()
