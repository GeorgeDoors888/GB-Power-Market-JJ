"""
Generate static GeoJSON file from BigQuery for the DNO map
This avoids needing a running Flask server
"""

from google.cloud import bigquery
import json

def generate_dno_geojson():
    """Query BigQuery and generate static GeoJSON file from REAL NESO data"""
    
    print("🗄️  Fetching REAL NESO DNO boundaries from BigQuery...")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    # Query the real NESO data
    query = """
    SELECT 
        b.dno_id,
        b.gsp_group,
        b.dno_code,
        b.area_name,
        b.dno_full_name,
        r.mpan_distributor_id,
        r.gsp_group_name,
        r.website_url,
        r.primary_coverage_area,
        ST_ASGEOJSON(b.boundary) as geojson,
        ST_AREA(b.boundary) / 1000000 as area_sqkm
    FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` b
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` r
        ON REPLACE(b.gsp_group, '_', '') = r.gsp_group_id
    ORDER BY b.gsp_group
    """
    
    try:
        results = client.query(query).result()
        
        features = []
        for row in results:
            feature = {
                "type": "Feature",
                "geometry": json.loads(row.geojson),
                "properties": {
                    "dno_id": row.dno_id,
                    "gsp_group": row.gsp_group,
                    "dno_code": row.dno_code,
                    "dno_name": row.dno_full_name,
                    "area": row.area_name,
                    "mpan_id": row.mpan_distributor_id,
                    "gsp_name": row.gsp_group_name,
                    "coverage": row.primary_coverage_area,
                    "website": row.website_url,
                    "area_sqkm": round(row.area_sqkm, 1)
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Save to file
        filename = "dno_regions.geojson"
        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        print(f"✅ Generated {filename}")
        print(f"   Contains {len(features)} DNO license areas")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    generate_dno_geojson()
