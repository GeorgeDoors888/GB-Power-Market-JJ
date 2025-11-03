#!/usr/bin/env python3
"""
Simple Flask API to serve GeoJSON data from BigQuery to the map
"""

from flask import Flask, jsonify
from flask_cors import CORS
from google.cloud import bigquery
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Use application default credentials (gcloud auth)
try:
    client = bigquery.Client(project='inner-cinema-476211-u9')
    print("✅ BigQuery client initialized successfully")
except Exception as e:
    print(f"⚠️  BigQuery client error: {e}")
    print("Run: gcloud auth application-default login")
    client = None

@app.route('/api/geojson/dno-regions')
def get_dno_regions():
    """Serve DNO regions as GeoJSON from BigQuery"""
    
    query = """
    SELECT 
        dno_name,
        company,
        license,
        region,
        customers,
        area_sqkm,
        ST_ASGEOJSON(boundary) as geojson
    FROM `inner-cinema-476211-u9.uk_energy_prod.dno_license_areas`
    ORDER BY customers DESC
    """
    
    try:
        results = client.query(query).result()
        
        features = []
        for row in results:
            feature = {
                "type": "Feature",
                "geometry": json.loads(row.geojson),
                "properties": {
                    "dno_name": row.dno_name,
                    "company": row.company,
                    "license": row.license,
                    "region": row.region,
                    "customers": row.customers,
                    "area_sqkm": row.area_sqkm
                }
            }
            features.append(feature)
        
        return jsonify({
            "type": "FeatureCollection",
            "features": features
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/geojson/gsp-zones')
def get_gsp_zones():
    """Serve GSP zones as GeoJSON"""
    # Similar to DNO regions
    pass

@app.route('/api/live-stats')
def get_live_stats():
    """Get real-time energy statistics"""
    
    query = """
    SELECT 
        SUM(generation) as total_generation,
        MAX(timestamp) as last_updated
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_unified`
    WHERE timestamp >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
    """
    
    result = list(client.query(query).result())[0]
    
    return jsonify({
        "total_generation": float(result.total_generation),
        "last_updated": str(result.last_updated)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
