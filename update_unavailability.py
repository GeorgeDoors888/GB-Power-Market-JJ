#!/usr/bin/env python3
"""Fetch and display REMIT unavailability data in Dashboard"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import date, timedelta
import pandas as pd
from pathlib import Path

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
BMU_REGISTRATION_FILE = "bmu_registration_data.csv"

# Credentials
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]

SHEETS_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=SHEETS_CREDS).spreadsheets()

BQ_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=BQ_SCOPES)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=BQ_CREDS, location="US")

# Load BMU registration data for station names
def load_bmu_names():
    """Load BMU registration data to get station names"""
    try:
        bmu_file = Path(__file__).parent / BMU_REGISTRATION_FILE
        if bmu_file.exists():
            df = pd.read_csv(bmu_file)
            return df
        else:
            print(f"⚠️  BMU registration file not found: {bmu_file}")
            return None
    except Exception as e:
        print(f"⚠️  Error loading BMU data: {e}")
        return None

def get_station_name(bmu_id, bmu_df):
    """Get friendly station name from BMU ID"""
    if bmu_df is None:
        return None
    
    # Try exact match on nationalGridBmUnit
    match = bmu_df[bmu_df['nationalGridBmUnit'] == bmu_id]
    
    # Try elexonBmUnit if no match
    if len(match) == 0:
        match = bmu_df[bmu_df['elexonBmUnit'] == bmu_id]
    
    # Try partial match (remove prefix/suffix)
    if len(match) == 0:
        base_unit = bmu_id.replace('T_', '').replace('I_', '').replace('E_', '').split('-')[0]
        match = bmu_df[bmu_df['nationalGridBmUnit'].str.contains(base_unit, case=False, na=False)]
    
    if len(match) > 0:
        station_name = match.iloc[0]['bmUnitName']
        
        # Clean up station name
        if 'Generator' in str(station_name):
            station_name = station_name.split('Generator')[0].strip()
        elif 'Unit' in str(station_name):
            station_name = station_name.split('Unit')[0].strip()
        
        return station_name
    
    return None

def get_unavailability_data():
    """Get current REMIT unavailability/outage data from BigQuery"""
    
    # Get active outages (ongoing or recent)
    # Use LATEST revision per unit (highest revisionNumber)
    today = date.today()
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
        u.fuelType,
        u.assetName,
        u.normalCapacity as installed_capacity_mw,
        u.availableCapacity as available_capacity_mw,
        u.unavailableCapacity as unavailable_capacity_mw,
        u.eventStartTime as event_start,
        u.eventEndTime as event_end,
        u.eventType,
        u.cause
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    WHERE DATE(u.eventStartTime) <= '{today}'
      AND (DATE(u.eventEndTime) >= '{today}' OR u.eventEndTime IS NULL)
    ORDER BY u.unavailableCapacity DESC
    LIMIT 10
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if len(df) == 0:
            print("⚠️  No active outages found for today")
            return []
        
        print(f"✅ Found {len(df)} active outages")
        
        # Load BMU registration data for station names
        bmu_df = load_bmu_names()
        
        outages = []
        for _, row in df.iterrows():
            bmu = row['bmu_id']
            
            # Get station name from registration data
            station_name = get_station_name(bmu, bmu_df)
            
            # Use station name if available, otherwise use assetName or BMU ID
            if station_name:
                asset_name = station_name
            else:
                asset_name = row['assetName'] or bmu
            installed = row['installed_capacity_mw'] or 0
            unavail = row['unavailable_capacity_mw'] or 0
            
            if installed > 0:
                pct_unavail = (unavail / installed) * 100
            else:
                pct_unavail = 0
            
            # Create visual bar (10 blocks total)
            blocks = int(pct_unavail / 10)
            visual = '🟥' * blocks + '⬜' * (10 - blocks)
            
            event_type = row['eventType'] or 'Unknown'
            fuel_type = row['fuelType'] or 'Unknown'
            
            # Map fuel types to friendly names
            fuel_map = {
                'Nuclear': '⚛️ Nuclear',
                'Gas': '🔥 Gas',
                'Coal': '⚫ Coal',
                'Wind Onshore': '💨 Wind',
                'Wind Offshore': '🌊 Offshore Wind',
                'Hydro Run-of-River': '💧 Hydro',
                'Hydro Reservoir': '💧 Hydro',
                'Pumped Storage': '💧 Pumped Storage',
                'Biomass': '🌿 Biomass',
                'Other': '⚙️ Other'
            }
            fuel_desc = fuel_map.get(fuel_type, fuel_type)
            
            cause = row['cause'] or event_type
            # Shorten cause if too long
            if len(cause) > 30:
                cause = cause[:27] + '...'
            
            outages.append({
                'bmu': bmu,
                'asset': asset_name,
                'fuel': fuel_desc,
                'installed': installed,
                'unavail': unavail,
                'pct': pct_unavail,
                'visual': visual,
                'cause': cause
            })
        
        return outages
    
    except Exception as e:
        print(f"❌ Error querying unavailability: {e}")
        return []

def write_unavailability_to_sheet(outages):
    """Write unavailability data to REMIT Unavailability tab"""
    
    # Prepare data with header
    data = [
        ['Station Name', 'BMU Unit', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', '% Unavailable', 'Cause']
    ]
    
    for outage in outages:
        # Format display with station name and BMU ID
        display_name = f"{outage['asset']} ({outage['bmu']})"
        
        data.append([
            display_name,
            outage['bmu'],
            outage['fuel'],
            f"{outage['installed']:.0f}",
            f"{outage['unavail']:.0f}",
            f"{outage['visual']} {outage['pct']:.1f}%",
            outage['cause']
        ])
    
    # Write to REMIT Unavailability tab
    try:
        sheets.values().update(
            spreadsheetId=SHEET_ID,
            range='REMIT Unavailability!A1',
            valueInputOption="USER_ENTERED",
            body={"values": data}
        ).execute()
        print(f"✅ Wrote {len(outages)} outages to REMIT Unavailability tab")
    except Exception as e:
        print(f"❌ Error writing to sheet: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("⚠️  REMIT UNAVAILABILITY DATA UPDATE")
    print("=" * 80)
    
    outages = get_unavailability_data()
    
    if outages:
        print("\n📊 Active Outages (Unique Units Only):")
        print(f"{'Asset Name':<30} {'BMU':<15} {'Fuel':<20} {'Normal MW':>10} {'Unavail MW':>12} {'%':>8} {'Cause':<30}")
        print("-" * 135)
        for o in outages:
            print(f"{o['asset']:<30} {o['bmu']:<15} {o['fuel']:<20} {o['installed']:>10.0f} {o['unavail']:>12.0f} {o['pct']:>7.1f}% {o['cause']:<30}")
        
        write_unavailability_to_sheet(outages)
    else:
        print("\n⚠️  No outages to display")
    
    print("\n✅ Done")
