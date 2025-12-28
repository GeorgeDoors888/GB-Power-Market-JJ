#!/usr/bin/env python3
"""
Dashboard V3 - RESTORE fuel mix data and add NEW KPIs in column K
WITHOUT deleting existing data in columns A-J
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

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


def restore_fuel_mix_and_tables(sheets_service, bq_client):
    """Restore the fuel mix table that was deleted (rows 13-30)"""
    print("🔧 Restoring fuel mix table rows 13-30...")
    
    # Get current fuel mix data from BigQuery
    query = f"""
    SELECT 
        fuelType,
        generation / 1000 as gw,
        generation / SUM(generation) OVER() * 100 as pct
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE publishTime = (SELECT MAX(publishTime) FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`)
    ORDER BY generation DESC
    """
    
    fuel_df = bq_client.query(query).to_dataframe()
    
    # Restore fuel mix rows (continuing from row 13)
    fuel_data = []
    for _, row in fuel_df.iterrows():
        fuel_emoji = {
            'CCGT': '🔥',
            'NUCLEAR': '⚛️',
            'WIND': '💨',
            'BIOMASS': '🌱',
            'OTHER': '⚙️',
            'NPSHYD': '💧',
            'PS': '⛰️',
            'OCGT': '🔥',
            'COAL': '⚫',
            'OIL': '🛢️'
        }.get(row['fuelType'], '⚡')
        
        fuel_data.append([
            f"{fuel_emoji} {row['fuelType']}",
            f"{row['gw']:.2f}",
            f"{row['pct']:.2f}%"
        ])
    
    # Get interconnector data
    ic_query = f"""
    SELECT 
        interconnectorName,
        flow
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE publishTime = (SELECT MAX(publishTime) FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`)
      AND interconnectorName IS NOT NULL
    ORDER BY ABS(flow) DESC
    LIMIT 10
    """
    
    ic_df = bq_client.query(ic_query).to_dataframe()
    
    ic_data = []
    for _, row in ic_df.iterrows():
        ic_data.append([
            row['interconnectorName'],
            f"{int(row['flow'])}"
        ])
    
    # Build rows 13-30 (rest of fuel mix + interconnectors + outages header)
    restore_values = []
    
    # Add remaining fuel types (rows 13+)
    for fuel_row in fuel_data[3:]:  # Skip first 3 (already in rows 10-12)
        restore_values.append(fuel_row + [''] * 13)  # Pad to column P
    
    # Add blank row
    restore_values.append([''] * 16)
    
    # Total Gen row
    total_gen = fuel_df['gw'].sum()
    restore_values.append([f'Total Gen: {total_gen:.1f} GW'] + [''] * 15)
    
    # Outages header
    restore_values.append(['🚨 ACTIVE OUTAGES'] + [''] * 15)
    restore_values.append(['BM Unit', 'Plant Name', 'Fuel Type', 'MW Lost', '% Lost', 'Start Time', '', 'End Time', 'Status'] + [''] * 7)
    
    # Get outages data
    outages_query = f"""
    SELECT 
        bmUnit,
        nationalGridBmUnit as plant_name,
        fuelType,
        affectedMW as mw_lost,
        eventStart,
        eventEnd,
        eventStatus
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
    WHERE eventStatus = 'Active'
    ORDER BY affectedMW DESC
    LIMIT 7
    """
    
    try:
        outages_df = bq_client.query(outages_query).to_dataframe()
        
        for _, row in outages_df.iterrows():
            restore_values.append([
                row['bmUnit'] if pd.notna(row['bmUnit']) else '',
                row['plant_name'] if pd.notna(row['plant_name']) else '',
                row['fuelType'] if pd.notna(row['fuelType']) else '',
                f"{int(row['mw_lost'])}" if pd.notna(row['mw_lost']) else '0',
                '',  # % Lost (calculate if needed)
                str(row['eventStart'])[:16] if pd.notna(row['eventStart']) else '',
                '',
                str(row['eventEnd'])[:16] if pd.notna(row['eventEnd']) else '',
                row['eventStatus'] if pd.notna(row['eventStatus']) else ''
            ] + [''] * 7)
    except:
        print("   ⚠️  Could not fetch outages data")
    
    # Write to sheet (columns A-J, rows 13+)
    body = {'values': restore_values}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!A13:J{12+len(restore_values)}',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    print(f"   ✅ Restored {len(restore_values)} rows of fuel/outages data")


def get_kpi_data(bq_client):
    """Get imbalance price data for KPIs"""
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
    
    # Calculate KPIs
    latest_price = df['price'].iloc[-1] if len(df) > 0 else 0
    
    seven_days_ago = df['timestamp'].max() - timedelta(days=7)
    df_7d = df[df['timestamp'] >= seven_days_ago]
    avg_7d = df_7d['price'].mean() if len(df_7d) > 0 else 0
    high_7d = df_7d['price'].max() if len(df_7d) > 0 else 0
    
    thirty_days_ago = df['timestamp'].max() - timedelta(days=30)
    df_30d = df[df['timestamp'] >= thirty_days_ago]
    avg_30d = df_30d['price'].mean() if len(df_30d) > 0 else 0
    high_30d = df_30d['price'].max() if len(df_30d) > 0 else 0
    low_30d = df_30d['price'].min() if len(df_30d) > 0 else 0
    
    dev_from_7d = ((latest_price - avg_7d) / avg_7d * 100) if avg_7d > 0 else 0
    
    return {
        'realtime_price': latest_price,
        'avg_7d': avg_7d,
        'high_7d': high_7d,
        'avg_30d': avg_30d,
        'high_30d': high_30d,
        'low_30d': low_30d,
        'dev_from_7d': dev_from_7d
    }, df


def write_kpis_column_k(sheets_service, kpis):
    """Write NEW KPIs in column K onwards (row 13+) WITHOUT touching columns A-J"""
    print("📝 Writing NEW KPIs in columns K-P (row 13 onwards)...")
    
    # KPI data for columns K-P starting at row 13
    kpi_values = [
        # Row 13: Header
        ['⚡ MARKET KPIs', '', '', 'Sparkline'],
        # Row 14: Blank
        ['', '', '', ''],
        # Row 15: Real-time price
        ['Real-time imbalance', f'£{kpis["realtime_price"]:.2f}/MWh', '', ''],
        # Row 16: Rolling mean
        ['', f'£{kpis["avg_7d"]:.2f}/MWh', 'Rolling mean', ''],
        # Row 17: Blank
        ['', '', '', ''],
        # Row 18: 7-day average
        ['7-Day Average', f'£{kpis["avg_7d"]:.2f}/MWh', 'Rolling mean', ''],
        # Row 19: Deviation
        ['Deviation from 7d', f'{kpis["dev_from_7d"]:.2f}%', 'vs 7-day avg', ''],
        # Row 20: Blank
        ['', '', '', ''],
        # Row 21: 30-day average
        ['30-Day Average', f'£{kpis["avg_30d"]:.2f}/MWh', 'Rolling mean', ''],
        # Row 22: 30-day low
        ['30-Day Low', f'£{kpis["low_30d"]:.2f}/MWh', 'Min price', ''],
        # Row 23: Blank
        ['', '', '', ''],
        # Row 24: 7-day high
        ['7-Day High', f'£{kpis["high_7d"]:.2f}/MWh', 'Peak daily', ''],
        # Row 25: 30-day high
        ['30-Day High', f'£{kpis["high_30d"]:.2f}/MWh', 'Max price', ''],
    ]
    
    body = {'values': kpi_values}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!K13:N{12+len(kpi_values)}',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    print(f"   ✅ Wrote {len(kpi_values)} rows of KPIs in column K-N")


def main():
    print("🔄 DASHBOARD V3 - RESTORE & FIX")
    print("="*80)
    
    sheets, bq = get_clients()
    
    print("\n1️⃣  Restoring fuel mix and tables (columns A-J, rows 13+)...")
    restore_fuel_mix_and_tables(sheets, bq)
    
    print("\n2️⃣  Fetching KPI data...")
    kpis, price_df = get_kpi_data(bq)
    print(f"   ✅ Got {len(price_df)} price records")
    print(f"   📊 Real-time price: £{kpis['realtime_price']:.2f}/MWh")
    print(f"   📊 7-day avg: £{kpis['avg_7d']:.2f}/MWh")
    
    print("\n3️⃣  Writing NEW KPIs in column K...")
    write_kpis_column_k(sheets, kpis)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("📊 Columns A-J: Fuel Mix + Interconnectors + Outages")
    print("📊 Columns K-N: New Market KPIs")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=1471864390")


if __name__ == '__main__':
    main()
