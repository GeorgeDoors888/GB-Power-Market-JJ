#!/usr/bin/env python3
"""Add unavailability section to Dashboard sheet with visual indicators"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import date
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Credentials
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]

SHEETS_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=SHEETS_CREDS).spreadsheets()

BQ_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=BQ_SCOPES)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=BQ_CREDS, location="US")

def get_active_outages():
    """Get active power plant outages from BigQuery"""
    
    today = date.today()
    
    # Get latest revision for each unit
    query = f"""
    WITH latest_revisions AS (
        SELECT 
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE DATE(eventStartTime) <= '{today}'
          AND (DATE(eventEndTime) >= '{today}' OR eventEndTime IS NULL)
        GROUP BY affectedUnit
    )
    SELECT 
        u.affectedUnit as bmu_id,
        u.assetName,
        u.fuelType,
        u.normalCapacity as normal_mw,
        u.unavailableCapacity as unavail_mw,
        u.eventType,
        u.cause
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    WHERE DATE(u.eventStartTime) <= '{today}'
      AND (DATE(u.eventEndTime) >= '{today}' OR u.eventEndTime IS NULL)
      AND u.unavailableCapacity > 0
    ORDER BY u.unavailableCapacity DESC
    LIMIT 10
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if len(df) == 0:
            return []
        
        outages = []
        for _, row in df.iterrows():
            asset_name = row['assetName'] or row['bmu_id']
            normal = row['normal_mw'] or 0
            unavail = row['unavail_mw'] or 0
            
            # Calculate percentage
            if normal > 0:
                pct = (unavail / normal) * 100
            else:
                pct = 0
            
            # Create visual bar (10 blocks)
            blocks = int(pct / 10)
            visual = '🟥' * blocks + '⬜' * (10 - blocks)
            
            # Get cause
            cause = row['cause'] or row['eventType'] or 'Unknown'
            if len(cause) > 40:
                cause = cause[:37] + '...'
            
            # Fuel type for display
            fuel = row['fuelType'] or 'Unknown'
            
            outages.append({
                'asset': asset_name,
                'fuel': fuel,
                'normal': normal,
                'unavail': unavail,
                'pct': pct,
                'visual': visual,
                'cause': cause
            })
        
        return outages
    
    except Exception as e:
        print(f"❌ Error querying outages: {e}")
        return []

def add_unavailability_to_dashboard():
    """Add unavailability section to Dashboard sheet after settlement periods"""
    
    print("=" * 80)
    print("⚠️  ADDING UNAVAILABILITY TO DASHBOARD")
    print("=" * 80)
    
    # Get current outages
    outages = get_active_outages()
    
    if not outages:
        print("\n✅ No active outages - writing 'All systems operational' message")
        
        # Write header + no outages message
        data = [
            [''],  # Blank row
            ['⚠️ POWER STATION OUTAGES'],
            ['Asset Name', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', '% Unavailable', 'Cause'],
            ['', '', '', '', '✅ All systems operational - no active outages', '']
        ]
    else:
        print(f"\n📊 Found {len(outages)} active outages")
        
        # Build data with header
        data = [
            [''],  # Blank row
            ['⚠️ POWER STATION OUTAGES'],
            ['Asset Name', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', '% Unavailable', 'Cause']
        ]
        
        # Add each outage
        for outage in outages:
            data.append([
                outage['asset'],
                outage['fuel'],
                f"{outage['normal']:.0f}",
                f"{outage['unavail']:.0f}",
                f"{outage['visual']} {outage['pct']:.1f}%",
                outage['cause']
            ])
            print(f"   • {outage['asset']}: {outage['unavail']:.0f} MW unavailable ({outage['pct']:.1f}%)")
    
    # Determine where to write (after settlement periods)
    # Dashboard structure: Header (6) + Fuel/IC (11) + SP Header (2) + SPs (48) = 67 rows
    # Start unavailability at row 68
    start_row = 68
    
    # Write to Dashboard
    try:
        sheets.values().update(
            spreadsheetId=SHEET_ID,
            range=f'Dashboard!A{start_row}',
            valueInputOption="USER_ENTERED",
            body={"values": data}
        ).execute()
        
        print(f"\n✅ Wrote unavailability section to Dashboard starting at row {start_row}")
        print(f"   Total rows: {len(data)}")
        
    except Exception as e:
        print(f"\n❌ Error writing to Dashboard: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_unavailability_to_dashboard()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ DASHBOARD UPDATED WITH UNAVAILABILITY DATA")
        print("=" * 80)
        print("\nView at: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
    else:
        print("\n❌ Update failed")
