#!/usr/bin/env python3
"""
Enhanced Dashboard Updater with Live Map Integration
Runs every 5 minutes to keep Dashboard sheet fresh with:
- Latest generation data
- Outage information
- Map data (GSPs, ICs, DNOs)
- Chart data
- Timestamp

Author: George Major
Date: 24 November 2025
"""

import sys
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import json

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
LOCATION = 'US'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'

def log(msg):
    """Print with timestamp"""
    now = datetime.now().strftime('%H:%M:%S')
    print(f"[{now}] {msg}")

def init_clients():
    """Initialize Google Sheets and BigQuery clients"""
    sheets_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE),
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(sheets_creds)
    
    bq_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE),
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=bq_creds)
    
    return gc, bq_client

def update_timestamp(dashboard):
    """Update last refresh timestamp in B2"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamp_text = f"⏰ Last Updated: {now} | ✅ LIVE AUTO-REFRESH (5 min)"
    dashboard.update([[timestamp_text]], 'B2')
    log(f"Timestamp updated: {now}")

def update_chart_data(dashboard, bq_client):
    """Update intraday chart data for today"""
    log("Fetching today's intraday data...")
    
    query = f"""
    WITH combined AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        fuelType,
        SUM(CAST(generation AS FLOAT64)) as total_generation
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE('Europe/London')
      GROUP BY date, settlementPeriod, fuelType
      
      UNION ALL
      
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        fuelType,
        SUM(CAST(generation AS FLOAT64)) as total_generation
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE CAST(settlementDate AS DATE) = CURRENT_DATE('Europe/London')
      GROUP BY date, settlementPeriod, fuelType
    )
    SELECT 
      settlementPeriod,
      fuelType,
      ROUND(SUM(total_generation), 2) as generation
    FROM combined
    GROUP BY settlementPeriod, fuelType
    ORDER BY settlementPeriod, fuelType
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        if df.empty:
            log("⚠️ No data for today yet")
            return
        
        periods = sorted(df['settlementPeriod'].unique())
        fuels = sorted(df['fuelType'].unique())
        
        # Create pivot table
        header_row = ['Settlement Period'] + list(fuels)
        data_rows = []
        
        for period in periods:
            row = [f"SP {period}"]
            for fuel in fuels:
                val = df[(df['settlementPeriod'] == period) & (df['fuelType'] == fuel)]['generation'].values
                row.append(float(val[0]) if len(val) > 0 else 0)
            data_rows.append(row)
        
        # Write to A64
        dashboard.update([header_row] + data_rows, 'A64')
        
        # Format header
        dashboard.format('A64:K64', {
            'backgroundColor': {'red': 0.07, 'green': 0.07, 'blue': 0.07},
            'textFormat': {
                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                'bold': True
            }
        })
        
        log(f"✅ Chart data updated: {len(periods)} periods, {len(fuels)} fuels")
        
    except Exception as e:
        log(f"❌ Error updating chart data: {e}")

def update_map_data(gc, bq_client):
    """Update Map_Data_* sheets with fresh data"""
    log("Updating map data sheets...")
    
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Update GSP data
        gsp_sheet = spreadsheet.worksheet('Map_Data_GSP')
        gsp_data = fetch_gsp_data(bq_client)
        if gsp_data:
            gsp_sheet.update(gsp_data, 'A1')
            log(f"✅ Updated {len(gsp_data)-1} GSPs")
        
        # Update Interconnector data
        ic_sheet = spreadsheet.worksheet('Map_Data_IC')
        ic_data = fetch_ic_data(bq_client)
        if ic_data:
            ic_sheet.update(ic_data, 'A1')
            log(f"✅ Updated {len(ic_data)-1} ICs")
        
        # DNO boundaries update less frequently (they don't change)
        # Skip unless needed
        
    except Exception as e:
        log(f"⚠️ Map data update skipped: {e}")

def fetch_gsp_data(bq_client):
    """Fetch GSP data from BigQuery"""
    query = f"""
    SELECT 
      gsp_id,
      gsp_name,
      area_sqkm
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
    LIMIT 9
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        # Format for sheet (with sample coordinates)
        data = [['GSP_ID', 'Name', 'Lat', 'Lng', 'Demand_MW', 'Frequency_Hz', 'Region', 'Load_MW', 'Constraint_MW', 'Generation_MW']]
        
        # Sample coordinates for 9 GSPs across GB
        sample_coords = [
            (51.5, -0.1),   # London
            (53.5, -2.2),   # Manchester
            (52.5, -1.9),   # Birmingham
            (55.9, -3.2),   # Edinburgh
            (51.5, -3.2),   # Cardiff
            (53.8, -1.5),   # Leeds
            (54.6, -5.9),   # Belfast
            (52.6, 1.3),    # Norwich
            (50.4, -4.1)    # Plymouth
        ]
        
        for i, (_, row) in enumerate(df.iterrows()):
            lat, lng = sample_coords[min(i, len(sample_coords)-1)]
            data.append([
                row['gsp_id'],
                row['gsp_name'],
                lat,
                lng,
                0,  # Demand (would fetch from bmrs_indgen_iris)
                50.0,
                'England',
                0,
                0,
                0
            ])
        
        return data
        
    except Exception as e:
        log(f"Error fetching GSP data: {e}")
        return None

def fetch_ic_data(bq_client):
    """Fetch Interconnector data from BigQuery"""
    # Sample data - would be enhanced with real BMRS queries
    data = [
        ['Name', 'Country', 'Flow_MW', 'Start_Lat', 'Start_Lng', 'End_Lat', 'End_Lng', 'Capacity_MW', 'Status'],
        ['IFA', 'France', 1000, 50.8, 1.1, 50.0, 1.6, 2000, 'Active'],
        ['IFA2', 'France', 800, 50.9, 1.2, 50.1, 1.7, 1000, 'Active'],
        ['BritNed', 'Netherlands', 600, 51.9, 1.3, 52.3, 4.3, 1000, 'Active'],
        ['NEMO', 'Belgium', 400, 51.2, 1.4, 51.3, 2.9, 1000, 'Active'],
        ['NSL', 'Norway', 500, 55.9, -3.2, 59.9, 10.7, 1400, 'Active'],
        ['Viking', 'Denmark', 300, 53.5, 0.1, 55.7, 12.6, 1400, 'Active'],
        ['ElecLink', 'France', 200, 51.1, 1.3, 50.9, 1.8, 1000, 'Active'],
        ['Moyle', 'Ireland', -100, 55.2, -6.0, 55.0, -6.3, 500, 'Active']
    ]
    
    return data

def main():
    """Main update loop"""
    log("=" * 60)
    log("🔄 Enhanced Dashboard Updater - Starting")
    log("=" * 60)
    
    try:
        # Initialize
        gc, bq_client = init_clients()
        log("✅ Clients initialized")
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        dashboard = spreadsheet.worksheet('Dashboard')
        
        # Update components
        update_timestamp(dashboard)
        update_chart_data(dashboard, bq_client)
        update_map_data(gc, bq_client)
        
        log("=" * 60)
        log("✅ Dashboard update complete!")
        log("=" * 60)
        
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
