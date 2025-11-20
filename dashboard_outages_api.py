#!/usr/bin/env python3
"""
Flask API endpoint for Dashboard Outages with Station Names
Apps Script calls this endpoint every minute
"""

from flask import Flask, jsonify, request
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date
from pathlib import Path
import os

app = Flask(__name__)

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SA_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'inner-cinema-credentials.json')
BMU_REGISTRATION_FILE = "bmu_registration_data.csv"

# Initialize BigQuery client
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]
BQ_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=BQ_SCOPES)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=BQ_CREDS, location="US")

# Load BMU registration data (once at startup)
BMU_DF = None
try:
    bmu_file = Path(__file__).parent / BMU_REGISTRATION_FILE
    if bmu_file.exists():
        BMU_DF = pd.read_csv(bmu_file)
        print(f"✅ Loaded {len(BMU_DF)} BMU registrations")
    else:
        print(f"⚠️  BMU registration file not found: {bmu_file}")
except Exception as e:
    print(f"⚠️  Error loading BMU data: {e}")


def get_station_name(bmu_id):
    """Convert BMU code to friendly station name with emoji"""
    if BMU_DF is None:
        return f'⚡ {bmu_id}'
    
    # Try exact match on nationalGridBmUnit
    match = BMU_DF[BMU_DF['nationalGridBmUnit'] == bmu_id]
    
    # Try elexonBmUnit if no match
    if len(match) == 0:
        match = BMU_DF[BMU_DF['elexonBmUnit'] == bmu_id]
    
    # Try partial match (remove prefix/suffix)
    if len(match) == 0:
        base_unit = bmu_id.replace('T_', '').replace('I_', '').replace('E_', '').split('-')[0]
        match = BMU_DF[BMU_DF['nationalGridBmUnit'].str.contains(base_unit, case=False, na=False)]
    
    if len(match) > 0:
        station_name = match.iloc[0]['bmUnitName']
        fuel_type = match.iloc[0]['fuelType']
        
        # Clean up station name
        if 'Generator' in str(station_name):
            station_name = station_name.split('Generator')[0].strip()
        elif 'Unit' in str(station_name):
            station_name = station_name.split('Unit')[0].strip()
        
        # Add emoji based on fuel type
        emoji_map = {
            'NUCLEAR': '⚛️',
            'CCGT': '🔥',
            'PS': '🔋',
            'WIND': '💨',
            'OCGT': '🔥',
            'BIOMASS': '🌱',
            'COAL': '⚫',
            'OIL': '🛢️',
            'HYDRO': '💧'
        }
        emoji = emoji_map.get(str(fuel_type), '⚡')
        
        return f'{emoji} {station_name}'
    
    return f'⚡ {bmu_id}'


def get_latest_outages():
    """Query BigQuery for active outages"""
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
    LIMIT 15
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        outages = []
        for _, row in df.iterrows():
            bmu_id = row['bmu_id']
            station_name = get_station_name(bmu_id)
            
            outages.append({
                'bmu_id': bmu_id,
                'station_name': station_name,
                'fuel_type': row['fuelType'],
                'installed_mw': float(row['installed_capacity_mw']) if row['installed_capacity_mw'] else 0,
                'unavailable_mw': float(row['unavailable_capacity_mw']) if row['unavailable_capacity_mw'] else 0,
                'event_type': row['eventType'],
                'cause': row['cause']
            })
        
        return outages
    
    except Exception as e:
        print(f"❌ Error querying outages: {e}")
        return []


@app.route('/outages', methods=['GET'])
def get_outages():
    """
    GET /outages
    Returns current outages with station names
    
    Response format:
    {
      "status": "success",
      "count": 10,
      "outages": [
        {
          "bmu_id": "T_HEYM27",
          "station_name": "⚛️ Heysham 2",
          "fuel_type": "Nuclear",
          "installed_mw": 660,
          "unavailable_mw": 660,
          "event_type": "Planned",
          "cause": "OPR"
        },
        ...
      ]
    }
    """
    try:
        outages = get_latest_outages()
        
        return jsonify({
            'status': 'success',
            'count': len(outages),
            'outages': outages,
            'timestamp': date.today().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/outages/names', methods=['GET'])
def get_outage_names():
    """
    GET /outages/names
    Returns just the station names for Apps Script (minimal response)
    
    Response format:
    {
      "status": "success",
      "names": ["⚛️ Heysham 2", "⚛️ Torness", ...]
    }
    """
    try:
        outages = get_latest_outages()
        names = [outage['station_name'] for outage in outages]
        
        return jsonify({
            'status': 'success',
            'names': names,
            'count': len(names)
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'dashboard-outages-api',
        'bmu_data_loaded': BMU_DF is not None,
        'bmu_count': len(BMU_DF) if BMU_DF is not None else 0
    })


if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
