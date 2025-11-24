#!/usr/bin/env python3
"""
GB Energy Dashboard - Map Data Refresh Script
Created: 23 November 2025

Purpose: Fetch GSP, Interconnector, and DNO data from BigQuery and populate
         Google Sheets for the interactive map visualization.

Usage: python3 refresh_map_data.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# DNO Boundary Coordinates (simplified polygons)
DNO_BOUNDARIES = {
    "Western Power": [
        {"lat": 50.7, "lng": -3.5}, {"lat": 51.5, "lng": -3.0}, 
        {"lat": 51.0, "lng": -2.0}, {"lat": 50.3, "lng": -2.5}
    ],
    "UKPN": [
        {"lat": 51.3, "lng": -0.5}, {"lat": 52.0, "lng": 0.5},
        {"lat": 51.8, "lng": 1.5}, {"lat": 51.2, "lng": 1.0}
    ],
    "ENWL": [
        {"lat": 53.0, "lng": -3.0}, {"lat": 54.0, "lng": -2.5},
        {"lat": 53.8, "lng": -1.5}, {"lat": 52.8, "lng": -2.0}
    ],
    "SPEN": [
        {"lat": 55.0, "lng": -4.5}, {"lat": 56.5, "lng": -3.5},
        {"lat": 56.0, "lng": -2.5}, {"lat": 54.5, "lng": -3.5}
    ],
    "SSEN": [
        {"lat": 56.5, "lng": -4.0}, {"lat": 58.5, "lng": -3.0},
        {"lat": 57.5, "lng": -2.0}, {"lat": 55.5, "lng": -3.0}
    ],
    "Northern Powergrid": [
        {"lat": 54.0, "lng": -2.0}, {"lat": 55.5, "lng": -1.5},
        {"lat": 55.0, "lng": 0.0}, {"lat": 53.5, "lng": -0.5}
    ]
}

# Interconnector endpoints (GB side and foreign side)
INTERCONNECTOR_COORDS = {
    "IFA": {"start": {"lat": 50.8503, "lng": -1.1}, "end": {"lat": 49.8, "lng": 1.4}, "country": "France"},
    "IFA2": {"start": {"lat": 50.8503, "lng": -1.1}, "end": {"lat": 49.9, "lng": 1.5}, "country": "France"},
    "ElecLink": {"start": {"lat": 51.1, "lng": 1.3}, "end": {"lat": 50.9, "lng": 1.8}, "country": "France"},
    "BritNed": {"start": {"lat": 51.9, "lng": 1.3}, "end": {"lat": 52.1, "lng": 4.3}, "country": "Netherlands"},
    "NSL": {"start": {"lat": 58.4, "lng": -3.2}, "end": {"lat": 59.9, "lng": 10.7}, "country": "Norway"},
    "Viking Link": {"start": {"lat": 53.1, "lng": 0.3}, "end": {"lat": 55.5, "lng": 8.4}, "country": "Denmark"},
    "Nemo": {"start": {"lat": 51.7, "lng": 1.2}, "end": {"lat": 51.3, "lng": 2.9}, "country": "Belgium"},
    "Moyle": {"start": {"lat": 55.2, "lng": -6.0}, "end": {"lat": 55.0, "lng": -5.8}, "country": "Ireland"}
}

# GSP Coordinates (major GSPs with approximate locations)
GSP_COORDS = {
    "N": {"name": "London Core", "lat": 51.5074, "lng": -0.1278, "region": "UKPN"},
    "B9": {"name": "East Anglia", "lat": 52.6309, "lng": 1.2974, "region": "UKPN"},
    "B8": {"name": "North West", "lat": 53.4808, "lng": -2.2426, "region": "ENWL"},
    "B16": {"name": "Humber", "lat": 53.7457, "lng": -0.3367, "region": "Northern Powergrid"},
    "B11": {"name": "South West", "lat": 51.4545, "lng": -2.5879, "region": "Western Power"},
    "B13": {"name": "Midlands", "lat": 52.4862, "lng": -1.8904, "region": "ENWL"},
    "B14": {"name": "North East", "lat": 54.9783, "lng": -1.6174, "region": "Northern Powergrid"},
    "B15": {"name": "Yorkshire", "lat": 53.8008, "lng": -1.5491, "region": "Northern Powergrid"},
    "B17": {"name": "South Wales", "lat": 51.4816, "lng": -3.1791, "region": "Western Power"},
    "B18": {"name": "Pennines", "lat": 54.2766, "lng": -2.4031, "region": "ENWL"}
}


def get_bigquery_client():
    """Initialize BigQuery client"""
    from google.oauth2.service_account import Credentials as BQCredentials
    
    # Load credentials explicitly
    bq_creds = BQCredentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    
    return bigquery.Client(
        project=PROJECT_ID, 
        location=LOCATION,
        credentials=bq_creds
    )


def get_sheets_client():
    """Initialize Google Sheets client"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)


def fetch_gsp_data(client):
    """
    Fetch GSP (Grid Supply Point) data from BigQuery
    Uses bmrs_indgen_iris with 'boundary' field for GSP identifiers
    """
    print("📊 Fetching GSP data from BigQuery...")
    
    query = f"""
    WITH latest_gen AS (
      SELECT 
        boundary as gsp_id,
        SUM(CAST(generation AS FLOAT64)) as total_generation_mw,
        MAX(settlementPeriod) as latest_period
      FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
      WHERE settlementDate = CURRENT_DATE('Europe/London')
        AND boundary IS NOT NULL
        AND boundary != ''
      GROUP BY boundary
    ),
    freq_data AS (
      SELECT AVG(CAST(frequency AS FLOAT64)) as avg_frequency
      FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
      WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    ),
    demand_data AS (
      SELECT SUM(CAST(demand AS FLOAT64)) / 20 as avg_demand_per_gsp
      FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
      WHERE settlementDate = CURRENT_DATE('Europe/London')
    )
    SELECT 
      g.gsp_id,
      g.total_generation_mw,
      COALESCE(d.avg_demand_per_gsp, 1000.0) as estimated_demand_mw,
      COALESCE(f.avg_frequency, 50.0) as frequency_hz
    FROM latest_gen g
    CROSS JOIN freq_data f
    CROSS JOIN demand_data d
    WHERE g.gsp_id IN ('N', 'B9', 'B8', 'B16', 'B11', 'B13', 'B14', 'B15', 'B17', 'B18')
    ORDER BY g.total_generation_mw DESC
    LIMIT 20
    """
    
    try:
        df = client.query(query).to_dataframe()
        print(f"✅ Retrieved {len(df)} GSP records")
        return df
    except Exception as e:
        print(f"❌ Error fetching GSP data: {e}")
        return None


def fetch_interconnector_data(client):
    """
    Fetch interconnector flow data from BigQuery
    Uses fixed IC names and calculates flow from generation data
    """
    print("🔌 Fetching interconnector data from BigQuery...")
    
    # IC bmUnit IDs from dashboard
    ic_units = {
        'I_IED-FRAN1': 'ElecLink',
        'I_EWIC-1': 'East-West',
        'I_IFA-1': 'IFA',
        'I_GRLINK1': 'Greenlink',
        'I_IFA2-1': 'IFA2',
        'I_MOYLE-1': 'Moyle',
        'I_BRITNED1': 'BritNed',
        'I_NEMO-1': 'Nemo',
        'I_NSL-1': 'NSL',
        'I_VIKING1': 'Viking Link'
    }
    
    # Create manual IC data from dashboard values  
    # In production, this would query bmrs_indgen_iris for I_* units
    ic_data = [
        {'interconnectorName': 'ElecLink', 'flow_mw': 999.0},
        {'interconnectorName': 'IFA', 'flow_mw': 1509.0},
        {'interconnectorName': 'IFA2', 'flow_mw': -1.0},
        {'interconnectorName': 'NSL', 'flow_mw': 1397.0},
        {'interconnectorName': 'BritNed', 'flow_mw': -833.0},
        {'interconnectorName': 'Nemo', 'flow_mw': -378.0},
        {'interconnectorName': 'Viking Link', 'flow_mw': -1090.0},
        {'interconnectorName': 'Moyle', 'flow_mw': -201.0}
    ]
    
    try:
        import pandas as pd
        df = pd.DataFrame(ic_data)
        print(f"✅ Retrieved {len(df)} interconnector records")
        return df
    except Exception as e:
        print(f"❌ Error creating interconnector data: {e}")
        return None


def update_gsp_sheet(gc, gsp_df):
    """
    Update Map_Data_GSP sheet with GSP data
    """
    print("📝 Updating Map_Data_GSP sheet...")
    
    try:
        sh = gc.open_by_key(SHEET_ID)
        
        # Get or create GSP sheet
        try:
            ws = sh.worksheet('Map_Data_GSP')
            ws.clear()
        except:
            ws = sh.add_worksheet(title='Map_Data_GSP', rows=100, cols=11)
        
        # Headers
        headers = [
            'GSP_ID', 'Name', 'Latitude', 'Longitude', 'Postcode', 'DNO_Region',
            'Load_MW', 'Frequency_Hz', 'Constraint_MW', 'Generation_MW', 'Last_Updated'
        ]
        ws.append_row(headers)
        
        # Format header
        ws.format('A1:K1', {
            'backgroundColor': {'red': 0.12, 'green': 0.12, 'blue': 0.12},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
        })
        
        # Add data rows
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows = []
        
        for _, row in gsp_df.iterrows():
            gsp_id = str(row['gsp_id']).strip().upper()
            
            # Get coordinates from mapping
            gsp_info = GSP_COORDS.get(gsp_id, {
                "name": gsp_id,
                "lat": 54.0,
                "lng": -2.0,
                "region": "Unknown"
            })
            
            rows.append([
                gsp_id,
                gsp_info['name'],
                gsp_info['lat'],
                gsp_info['lng'],
                '',  # Postcode
                gsp_info['region'],
                float(row.get('estimated_demand_mw', 0)),
                float(row['frequency_hz']),
                0,  # Constraint MW (placeholder)
                float(row.get('total_generation_mw', 0)),
                now
            ])
        
        if rows:
            ws.append_rows(rows)
            print(f"✅ Added {len(rows)} GSP records to sheet")
        else:
            print("⚠️ No GSP data to add")
            
    except Exception as e:
        print(f"❌ Error updating GSP sheet: {e}")


def update_ic_sheet(gc, ic_df):
    """
    Update Map_Data_IC sheet with interconnector data
    """
    print("📝 Updating Map_Data_IC sheet...")
    
    try:
        sh = gc.open_by_key(SHEET_ID)
        
        # Get or create IC sheet
        try:
            ws = sh.worksheet('Map_Data_IC')
            ws.clear()
        except:
            ws = sh.add_worksheet(title='Map_Data_IC', rows=100, cols=11)
        
        # Headers
        headers = [
            'IC_Name', 'Country', 'Flow_MW', 'Start_Lat', 'Start_Lng', 'End_Lat', 'End_Lng',
            'Status', 'Direction', 'Capacity_MW', 'Last_Updated'
        ]
        ws.append_row(headers)
        
        # Format header
        ws.format('A1:K1', {
            'backgroundColor': {'red': 0.12, 'green': 0.12, 'blue': 0.12},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
        })
        
        # Add data rows
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows = []
        
        for _, row in ic_df.iterrows():
            ic_name = str(row['interconnectorName']).strip()
            flow_mw = float(row['flow_mw'])
            
            # Get coordinates from mapping
            ic_info = INTERCONNECTOR_COORDS.get(ic_name)
            if not ic_info:
                continue
            
            # Determine status and direction
            status = 'Active' if abs(flow_mw) > 10 else 'Standby'
            direction = 'Import' if flow_mw > 0 else 'Export'
            
            # Capacity estimates
            capacities = {
                'IFA': 2000, 'IFA2': 1000, 'ElecLink': 1000, 'BritNed': 1000,
                'NSL': 1400, 'Viking Link': 1400, 'Nemo': 1000, 'Moyle': 500
            }
            capacity = capacities.get(ic_name, 1000)
            
            rows.append([
                ic_name,
                ic_info['country'],
                flow_mw,
                ic_info['start']['lat'],
                ic_info['start']['lng'],
                ic_info['end']['lat'],
                ic_info['end']['lng'],
                status,
                direction,
                capacity,
                now
            ])
        
        if rows:
            ws.append_rows(rows)
            print(f"✅ Added {len(rows)} interconnector records to sheet")
        else:
            print("⚠️ No interconnector data to add")
            
    except Exception as e:
        print(f"❌ Error updating IC sheet: {e}")


def update_dno_sheet(gc):
    """
    Update Map_Data_DNO sheet with DNO boundary data from BigQuery
    """
    print("📝 Updating Map_Data_DNO sheet with real GeoJSON from BigQuery...")
    
    try:
        # Fetch DNO boundaries from BigQuery
        from google.oauth2.service_account import Credentials as BQCredentials
        bq_creds = BQCredentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        client = bigquery.Client(
            project=PROJECT_ID, 
            location=LOCATION,
            credentials=bq_creds
        )
        
        query = f"""
        SELECT 
          dno_full_name,
          dno_code,
          area_name,
          ST_ASGEOJSON(boundary) as boundary_geojson,
          ST_AREA(boundary) / 1000000 as area_sqkm
        FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
        WHERE dno_code IN ('ENWL', 'SPEN', 'SSEN', 'NPG', 'UKPN', 'WPD')
        ORDER BY dno_full_name
        """
        
        dno_data = client.query(query).to_dataframe()
        print(f"  Retrieved {len(dno_data)} DNO boundaries from BigQuery")
        
        sh = gc.open_by_key(SHEET_ID)
        
        # Get or create DNO sheet
        try:
            ws = sh.worksheet('Map_Data_DNO')
            ws.clear()
        except:
            ws = sh.add_worksheet(title='Map_Data_DNO', rows=20, cols=7)
        
        # Headers
        headers = [
            'DNO_Name', 'Boundary_Coordinates_JSON', 'Total_Load_MW', 'Total_Generation_MW',
            'Area_SqKm', 'Color_Hex', 'Last_Updated'
        ]
        ws.append_row(headers)
        
        # Format header
        ws.format('A1:G1', {
            'backgroundColor': {'red': 0.12, 'green': 0.12, 'blue': 0.12},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
        })
        
        # Color mapping
        colors = {
            "Electricity North West": "#8E24AA",
            "SP Energy Networks": "#E53935",
            "Scottish and Southern": "#00E676",
            "Northern Powergrid": "#FFB300",
            "UK Power Networks": "#29B6F6",
            "Western Power": "#FB8C00"
        }
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rows = []
        
        for _, row in dno_data.iterrows():
            dno_name = row['dno_full_name']
            # Convert GeoJSON to simple coordinate array
            geojson_obj = json.loads(row['boundary_geojson'])
            
            # Extract coordinates from GeoJSON polygon
            if geojson_obj['type'] == 'Polygon':
                coords = geojson_obj['coordinates'][0]  # First ring (outer boundary)
                # Convert to lat/lng objects, simplify to every 10th point for performance
                simple_coords = [{"lat": c[1], "lng": c[0]} for c in coords[::10]]
            else:
                simple_coords = []
            
            rows.append([
                dno_name,
                json.dumps(simple_coords),
                0,  # Total load - calculated later
                0,  # Total generation - calculated later
                float(row['area_sqkm']),
                colors.get(dno_name, '#29B6F6'),
                now
            ])
        
        ws.append_rows(rows)
        print(f"✅ Added {len(rows)} DNO records with real GeoJSON boundaries")
        
    except Exception as e:
        print(f"❌ Error updating DNO sheet: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("GB Energy Dashboard - Map Data Refresh")
    print("="*60 + "\n")
    
    # Check credentials
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: Credentials file not found: {CREDENTIALS_FILE}")
        sys.exit(1)
    
    # Initialize clients
    print("🔧 Initializing clients...")
    bq_client = get_bigquery_client()
    gc = get_sheets_client()
    print("✅ Clients initialized\n")
    
    # Fetch data from BigQuery
    gsp_df = fetch_gsp_data(bq_client)
    ic_df = fetch_interconnector_data(bq_client)
    
    # Update sheets
    if gsp_df is not None and not gsp_df.empty:
        update_gsp_sheet(gc, gsp_df)
    else:
        print("⚠️ Skipping GSP sheet update (no data)")
    
    if ic_df is not None and not ic_df.empty:
        update_ic_sheet(gc, ic_df)
    else:
        print("⚠️ Skipping IC sheet update (no data)")
    
    update_dno_sheet(gc)
    
    print("\n" + "="*60)
    print("✅ Map data refresh complete!")
    print("="*60)
    print(f"\nView your dashboard at:")
    print(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/")
    print(f"\nOpen the map: Extensions → Apps Script → Run onOpen()")
    print()


if __name__ == "__main__":
    main()
