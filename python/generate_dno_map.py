#!/usr/bin/env python3
"""
Generate DNO Boundary Map from BigQuery GeoJSON data

Creates an interactive Folium map showing UK DNO boundaries loaded from
neso_dno_boundaries table.
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import folium
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def main():
    print("🗺️  Generating DNO Boundary Map...")
    print("="*80)
    
    # Initialize BigQuery
    creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json'
    )
    client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    # Query DNO boundaries
    print("\n📊 Querying neso_dno_boundaries table...")
    query = f"""
    SELECT 
        dno_code,
        area_name,
        ST_ASGEOJSON(boundary) as boundary_geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    """
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("❌ No DNO boundary data found")
        return
    
    print(f"✅ Retrieved {len(df)} DNO regions")
    for _, row in df.iterrows():
        print(f"   - {row['dno_code']:15s} {row['area_name']}")
    
    # Create base map centered on UK
    print("\n🗺️  Creating Folium map...")
    m = folium.Map(
        location=[54.5, -3.5],  # Center of UK
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add DNO boundaries as GeoJSON layers
    for idx, row in df.iterrows():
        dno_code = row['dno_code']
        area_name = row['area_name']
        boundary_json = json.loads(row['boundary_geojson'])
        
        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "properties": {
                "dno_code": dno_code,
                "area_name": area_name
            },
            "geometry": boundary_json
        }
        
        # Add to map with popup
        folium.GeoJson(
            feature,
            name=f"{dno_code} - {area_name}",
            style_function=lambda x, dno=dno_code: {
                'fillColor': get_color(dno),
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.3
            },
            tooltip=folium.Tooltip(f"<b>{area_name}</b><br>DNO: {dno_code}")
        ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
        <h4>UK DNO Boundary Map</h4>
        <p>Distribution Network Operator regions from NESO official boundaries</p>
        <p style="font-size:11px; color:grey;">Data: neso_dno_boundaries (BigQuery)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    output_file = 'dno_boundary_map.html'
    m.save(output_file)
    
    print(f"\n✅ Map saved to: {output_file}")
    print(f"✅ Open in browser: file://{output_file}")
    print("="*80)

def get_color(dno_code):
    """Assign colors to DNO regions"""
    color_map = {
        'UKPN-EPN': '#FF6B6B',  # Red
        'UKPN-LPN': '#4ECDC4',  # Teal
        'UKPN-SPN': '#45B7D1',  # Blue
        'NGED-WestMidlands': '#F7DC6F',  # Yellow
        'NGED-EastMidlands': '#BB8FCE',  # Purple
        'NGED-SouthWales': '#85C1E2',  # Light Blue
        'NGED-SouthWest': '#58D68D',  # Green
        'SSEN-Southern': '#F39C12',  # Orange
        'SSEN-Hydro': '#E74C3C',  # Dark Red
        'SPEN-Manweb': '#1ABC9C',  # Turquoise
        'SPEN-SPD': '#3498DB',  # Ocean Blue
        'SPEN-SPMW': '#9B59B6',  # Violet
        'NPG-Northeast': '#E67E22',  # Dark Orange
        'NPG-Yorkshire': '#16A085',  # Dark Teal
        'NPG-NorthernPowergrid': '#2980B9',  # Strong Blue
        'ENWL': '#27AE60',  # Forest Green
    }
    return color_map.get(dno_code, '#95A5A6')  # Default grey

if __name__ == "__main__":
    main()
