#!/usr/bin/env python3
"""
Complete Dashboard V3 Data Refresh

Updates ALL sections of Dashboard V3:
1. KPIs (F10:L10) - VLP Revenue, Wholesale Avg, etc.
2. Fuel Mix & Interconnectors (A10:E21) - Live generation data
3. Active Outages (A25:H35) - Current plant outages  
4. VLP Actions (G25:N35) - Recent balancing actions
5. Chart Data sheet - Time series for charts
6. DNO_Map - 14 DNO regions with metrics

This replaces the partial update scripts with a single comprehensive refresh.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ===== CONFIGURATION =====
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_SHEET = "Dashboard V3"
DNO_MAP_SHEET = "DNO_Map"
CHART_DATA_SHEET = "Chart Data"

CREDENTIALS_PATH = os.path.expanduser("~/GB-Power-Market-JJ/inner-cinema-credentials.json")

DNO_REGIONS = [
    {"code": "10", "name": "UKPN-EPN", "lat": 52.2053, "lng": 0.1218},
    {"code": "11", "name": "UKPN-LPN", "lat": 51.5074, "lng": -0.1278},
    {"code": "12", "name": "UKPN-SPN", "lat": 51.3811, "lng": -0.0986},
    {"code": "13", "name": "NGED-WMID", "lat": 52.4862, "lng": -1.8904},
    {"code": "14", "name": "NGED-EMID", "lat": 52.9548, "lng": -1.1581},
    {"code": "15", "name": "NGED-SWALES", "lat": 51.6211, "lng": -3.9436},
    {"code": "16", "name": "NGED-SWEST", "lat": 50.7184, "lng": -3.5339},
    {"code": "17", "name": "SSEN-SHYDRO", "lat": 57.1497, "lng": -2.0943},
    {"code": "18", "name": "SSEN-SEPD", "lat": 51.9225, "lng": -0.8964},
    {"code": "19", "name": "SPEN-SPD", "lat": 55.8642, "lng": -4.2518},
    {"code": "20", "name": "SPEN-MANWEB", "lat": 53.4084, "lng": -2.9916},
    {"code": "21", "name": "ENWL", "lat": 53.4808, "lng": -2.2426},
    {"code": "22", "name": "NGED-YORKSHIRE", "lat": 53.8008, "lng": -1.5491},
    {"code": "23", "name": "NGED-NORTHEAST", "lat": 54.9783, "lng": -1.6178}
]


def get_credentials():
    """Load service account credentials."""
    return service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/bigquery"
        ]
    )


def update_fuel_mix_and_interconnectors(service, bq_client):
    """Update Fuel Mix & Interconnectors section (A10:E21)."""
    print("\n1️⃣  Updating Fuel Mix & Interconnectors...")
    
    query = f"""
    WITH latest_data AS (
        SELECT
            fuelType,
            generation,
            ROW_NUMBER() OVER(PARTITION BY fuelType ORDER BY publishTime DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE publishTime > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 MINUTE)
    )
    SELECT fuelType, generation 
    FROM latest_data 
    WHERE rn = 1
    ORDER BY generation DESC
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No recent fuel data")
            return False
        
        # Calculate total and percentages
        total_gen = df['generation'].sum()
        df['pct'] = (df['generation'] / total_gen * 100).round(1)
        
        # Split fuel types and interconnectors
        fuel_df = df[~df['fuelType'].str.startswith('INT')].head(12)
        ic_df = df[df['fuelType'].str.startswith('INT')].head(9)
        
        # Prepare fuel data (Fuel Type, GW, %)
        fuel_values = []
        for _, row in fuel_df.iterrows():
            fuel_values.append([
                row['fuelType'],
                round(row['generation'] / 1000, 2),  # Convert to GW
                row['pct']
            ])
        
        # Prepare interconnector data (Interconnector, Flow MW)
        ic_values = []
        for _, row in ic_df.iterrows():
            ic_name = row['fuelType'].replace('INT', '').replace('_', ' ').title()
            ic_values.append([ic_name, round(row['generation'], 0)])
        
        # Update both sections
        batch_data = [
            {
                'range': f'{DASHBOARD_SHEET}!A10:C21',
                'values': fuel_values + [[''] * 3] * (12 - len(fuel_values))
            },
            {
                'range': f'{DASHBOARD_SHEET}!D10:E18',
                'values': ic_values + [[''] * 2] * (9 - len(ic_values))
            }
        ]
        
        body = {'data': batch_data, 'valueInputOption': 'RAW'}
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        print(f"   ✅ Updated {len(fuel_values)} fuel types, {len(ic_values)} interconnectors")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def update_active_outages(service, bq_client):
    """Update Active Outages section (A25:H35)."""
    print("\n2️⃣  Updating Active Outages...")
    
    query = f"""
    WITH latest_revisions AS (
        SELECT
            affectedUnit,
            MAX(revisionNumber) AS max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
        GROUP BY affectedUnit
    )
    SELECT
        u.affectedUnit as bmUnitId,
        u.assetName as affectedPlant,
        u.fuelType,
        u.unavailableCapacity as mw_lost,
        'GB' as region,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', u.eventStartTime) as start_time
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr 
        ON u.affectedUnit = lr.affectedUnit 
        AND u.revisionNumber = lr.max_rev
    WHERE u.eventStatus = 'Active'
    ORDER BY u.unavailableCapacity DESC
    LIMIT 11
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            values = [['No active outages'] + [''] * 5]
        else:
            values = df.values.tolist()
            # Pad to 11 rows
            while len(values) < 11:
                values.append([''] * 6)
        
        body = {
            'range': f'{DASHBOARD_SHEET}!A25:F35',
            'values': values
        }
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=body['range'],
            valueInputOption='RAW',
            body={'values': body['values']}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} active outages")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def update_vlp_actions(service, bq_client):
    """Update VLP Actions section (G25:N35)."""
    print("\n3️⃣  Updating VLP Actions...")
    
    query = f"""
    SELECT
        bmUnit as bmUnitId,
        CASE 
            WHEN soFlag THEN 'System'
            WHEN storFlag THEN 'STOR'
            WHEN rrFlag THEN 'Reserve'
            ELSE 'Balancing'
        END as mode,
        (settlementPeriodTo - settlementPeriodFrom) * 30 as duration_min,
        FORMAT_TIMESTAMP('%H:%M', acceptanceTime) as time
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    ORDER BY acceptanceTime DESC
    LIMIT 11
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            values = [['No recent actions'] + [''] * 3]
        else:
            values = df.values.tolist()
            # Pad to 11 rows
            while len(values) < 11:
                values.append([''] * 4)
        
        body = {
            'range': f'{DASHBOARD_SHEET}!G25:J35',
            'values': values
        }
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=body['range'],
            valueInputOption='RAW',
            body={'values': body['values']}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} VLP actions")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def update_chart_data(service, bq_client):
    """Update Chart Data sheet with last 48 settlement periods."""
    print("\n4️⃣  Updating Chart Data (last 48 periods)...")
    
    # Try IRIS first, fallback to historical
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        price as systemPrice
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE TIMESTAMP(settlementDate) > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 48
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        # If IRIS empty, use historical data
        if df.empty:
            print("   ⚠️  No IRIS data, using historical...")
            query = f"""
            SELECT 
                settlementDate,
                settlementPeriod,
                price as systemPrice
            FROM `{PROJECT_ID}.{DATASET}.bmrs_mid`
            WHERE settlementDate >= DATE_SUB(DATE('2025-10-30'), INTERVAL 1 DAY)
            ORDER BY settlementDate DESC, settlementPeriod DESC
            LIMIT 48
            """
            df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            print("   ⚠️  No chart data available")
            return False
        
        # Add timestamp column - handle both DATETIME and DATE types
        df['timestamp'] = df.apply(
            lambda row: f"{str(row['settlementDate'])[:10]} {(row['settlementPeriod']-1) * 30 // 60:02d}:{(row['settlementPeriod']-1) * 30 % 60:02d}",
            axis=1
        )
        
        # Prepare data: Timestamp, Price
        header = [['Timestamp', 'Price (£/MWh)']]
        chart_values = df[['timestamp', 'systemPrice']].values.tolist()
        # Reverse to get chronological order
        chart_values.reverse()
        values = header + chart_values
        
        # Clear and update Chart Data sheet
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{CHART_DATA_SHEET}!A:Z'
        ).execute()
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{CHART_DATA_SHEET}!A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print(f"   ✅ Updated {len(df)} time periods")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def update_dno_kpis(service, bq_client):
    """Update Dashboard KPIs (F10:L10) based on selected DNO."""
    print("\n5️⃣  Updating Dashboard KPIs...")
    
    try:
        # Read F3 selected DNO
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DASHBOARD_SHEET}!F3"
        ).execute()
        selected_dno = result.get('values', [['']])[0][0]
        
        # Read DNO_Map to get metrics
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DNO_MAP_SHEET}!A:M"
        ).execute()
        
        values = result.get('values', [])
        dno_data = None
        
        for row in values[1:]:  # Skip header
            if len(row) >= 2 and (str(row[0]) == selected_dno or str(row[1]) == selected_dno):
                dno_data = row
                break
        
        if not dno_data:
            print(f"   ⚠️  DNO '{selected_dno}' not found")
            kpi_values = [0, 0, 0, 0, 0, 0, 0]
        else:
            # Extract KPIs: VLP Revenue, Wholesale, Volume, PPA, Cost, Margin, DUoS
            vlp_rev = float(dno_data[8]) if len(dno_data) > 8 else 0
            wholesale = float(dno_data[9]) if len(dno_data) > 9 else 0
            volume = float(dno_data[5]) if len(dno_data) > 5 else 0
            ppa = float(dno_data[6]) if len(dno_data) > 6 else 0
            cost = float(dno_data[7]) if len(dno_data) > 7 else 0
            margin = float(dno_data[4]) if len(dno_data) > 4 else 0
            
            # DUoS weighted
            red = float(dno_data[10]) if len(dno_data) > 10 else 0
            amber = float(dno_data[11]) if len(dno_data) > 11 else 0
            green = float(dno_data[12]) if len(dno_data) > 12 else 0
            duos_weighted = (red * 3.5/24 + amber * 8/24 + green * 12.5/24)
            
            kpi_values = [
                round(vlp_rev / 1000, 1),  # Convert to thousands (k)
                round(wholesale, 2),
                round(volume / 100000, 1),  # Convert to percentage of ~10M MWh market
                round(margin, 2),
                round(margin, 2),  # Repeat for "Selected DNO Net Margin"
                round(volume, 0),
                round(ppa / 1000, 1)  # Revenue in thousands
            ]
        
        # Update F10:L10
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DASHBOARD_SHEET}!F10:L10",
            valueInputOption='RAW',
            body={'values': [kpi_values]}
        ).execute()
        
        print(f"   ✅ Updated KPIs for {selected_dno}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main execution."""
    print("=" * 60)
    print("🔄 DASHBOARD V3 - COMPLETE REFRESH")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    credentials = get_credentials()
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location="US")
    service = build('sheets', 'v4', credentials=credentials)
    
    # Run all updates
    results = {
        'Fuel Mix & ICs': update_fuel_mix_and_interconnectors(service, bq_client),
        'Active Outages': update_active_outages(service, bq_client),
        'VLP Actions': update_vlp_actions(service, bq_client),
        'Chart Data': update_chart_data(service, bq_client),
        'Dashboard KPIs': update_dno_kpis(service, bq_client)
    }
    
    print()
    print("=" * 60)
    print("📊 REFRESH SUMMARY")
    print("=" * 60)
    for section, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {section}")
    
    all_success = all(results.values())
    print()
    if all_success:
        print("✅ COMPLETE: All sections updated successfully")
    else:
        print("⚠️  PARTIAL: Some sections failed (see above)")
    print("=" * 60)
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
