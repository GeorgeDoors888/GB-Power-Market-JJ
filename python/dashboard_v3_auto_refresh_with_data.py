#!/usr/bin/env python3
"""
Dashboard V3 - Auto Refresh with Data Sheet Updates

Refreshes:
1. VLP_Data sheet - from bmrs_boalf (balancing actions)
2. Market_Prices sheet - from bmrs_mid_iris (wholesale prices)
3. Fuel Mix & Interconnectors - from bmrs_fuelinst_iris
4. Active Outages - from bmrs_remit_unavailability
5. VLP Actions table - from bmrs_boalf recent

Run every 15 minutes via cron to keep dashboard live.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import sys

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json'


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


def refresh_vlp_data(sheets_service, bq_client):
    """Refresh VLP_Data sheet with latest balancing actions"""
    print("1️⃣  Refreshing VLP_Data...")
    
    query = f"""
    SELECT
        DATE(settlementDate) as date,
        COUNT(*) as action_count,
        SUM(CASE WHEN soFlag OR storFlag OR rrFlag THEN 1 ELSE 0 END) as vlp_actions,
        AVG((settlementPeriodTo - settlementPeriodFrom) * 30) as avg_duration_min
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    GROUP BY DATE(settlementDate)
    ORDER BY date DESC
    LIMIT 30
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No recent VLP data, keeping existing")
            return True
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        header = [['Date', 'Total Actions', 'VLP Actions', 'Avg Duration (min)']]
        values = header + df.values.tolist()
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='VLP_Data!A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def refresh_market_prices(sheets_service, bq_client):
    """Refresh Market_Prices sheet with latest IRIS data"""
    print("2️⃣  Refreshing Market_Prices...")
    
    query = f"""
    WITH daily_prices AS (
        SELECT
            DATE(settlementDate) as date,
            AVG(price) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price,
            STDDEV(price) as volatility
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY DATE(settlementDate)
        
        UNION ALL
        
        SELECT
            DATE(settlementDate) as date,
            AVG(price) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price,
            STDDEV(price) as volatility
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
        WHERE settlementDate >= DATE('2025-10-01')
          AND settlementDate < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY DATE(settlementDate)
    )
    SELECT * FROM daily_prices
    ORDER BY date DESC
    LIMIT 30
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No price data, keeping existing")
            return True
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df.fillna(0)
        
        header = [['Date', 'Avg Price (£/MWh)', 'Min Price', 'Max Price', 'Volatility']]
        values = header + df.values.tolist()
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Market_Prices!A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def refresh_fuel_mix(sheets_service, bq_client):
    """Refresh fuel mix and interconnectors"""
    print("3️⃣  Refreshing Fuel Mix & ICs...")
    
    query = f"""
    WITH latest_data AS (
        SELECT fuelType, generation,
            ROW_NUMBER() OVER(PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE publishTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
    )
    SELECT fuelType, generation FROM latest_data WHERE rn = 1 ORDER BY generation DESC
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No fuel data")
            return False
        
        total_gen = df['generation'].sum()
        df['pct'] = (df['generation'] / total_gen * 100).round(1)
        
        # Split fuel vs interconnectors
        fuel_df = df[~df['fuelType'].str.startswith('INT')].head(12)
        ic_df = df[df['fuelType'].str.startswith('INT')].copy()
        ic_df['fuelType'] = ic_df['fuelType'].str.replace('INT_', '')
        
        # Write fuel mix (A10:C21)
        fuel_values = [[row['fuelType'], f"{row['generation']/1000:.2f}", f"{row['pct']}%"] 
                      for _, row in fuel_df.iterrows()]
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!A10:C21',
            valueInputOption='USER_ENTERED',
            body={'values': fuel_values}
        ).execute()
        
        # Write ICs (D10:E18) - pad to 9 rows max
        ic_values = [[row['fuelType'], int(row['generation'])] 
                    for _, row in ic_df.head(9).iterrows()]
        
        # Pad with empty rows to fill D10:E18 (9 rows)
        while len(ic_values) < 9:
            ic_values.append(['', ''])
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!D10:E18',
            valueInputOption='RAW',
            body={'values': ic_values}
        ).execute()
        
        print(f"   ✅ Updated {len(fuel_df)} fuels, {len(ic_df)} ICs")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def refresh_outages(sheets_service, bq_client):
    """Refresh active outages"""
    print("4️⃣  Refreshing Outages...")
    
    query = f"""
    WITH latest_revisions AS (
        SELECT
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE unavailabilityType IN ('Planned', 'Unplanned Outage', 'Forced')
          AND availableCapacity < normalCapacity
          AND publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY affectedUnit
    )
    SELECT
        u.affectedUnit,
        u.assetName,
        u.fuelType,
        CAST(u.normalCapacity - u.availableCapacity AS INT64) as mw_lost,
        'GB' as region,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', u.eventStartTime) as start_time
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    WHERE u.normalCapacity > u.availableCapacity
    ORDER BY mw_lost DESC
    LIMIT 11
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            values = [['No active outages', '', '', '', '', '']]
        else:
            values = df.values.tolist()
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Dashboard V3!A25:F35',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} outages")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print(f"\n{'='*70}")
    print(f"🔄 Dashboard V3 Auto Refresh - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    sheets_service, bq_client = get_clients()
    
    results = {
        'VLP_Data': refresh_vlp_data(sheets_service, bq_client),
        'Market_Prices': refresh_market_prices(sheets_service, bq_client),
        'Fuel Mix': refresh_fuel_mix(sheets_service, bq_client),
        'Outages': refresh_outages(sheets_service, bq_client)
    }
    
    print(f"\n{'='*70}")
    print("📊 REFRESH SUMMARY")
    print(f"{'='*70}")
    for name, success in results.items():
        status = '✅' if success else '❌'
        print(f"  {status} {name}")
    
    all_success = all(results.values())
    print(f"\n{'✅ COMPLETE' if all_success else '⚠️  PARTIAL'}: Dashboard refreshed")
    print(f"{'='*70}\n")
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
