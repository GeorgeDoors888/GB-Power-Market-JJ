#!/usr/bin/env python3
"""
Export DNO boundaries with constraint costs to interactive HTML map
Uses Folium (Leaflet.js) to render GEOGRAPHY polygons with color-coded costs
Replaces Google Sheets geo chart which doesn't support DNO boundaries
"""

import folium
from google.cloud import bigquery
import json
from shapely.geometry import shape
from shapely import wkt

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def fetch_dno_data_with_boundaries():
    """Fetch DNO constraint costs with GEOGRAPHY boundaries"""
    print('📊 Fetching DNO data with boundaries from BigQuery...')
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    query = f"""
    SELECT 
        d.dno_id,
        d.dno_full_name,
        d.area_name,
        d.dno_code,
        c.total_cost_gbp,
        c.voltage_cost_gbp,
        c.thermal_cost_gbp,
        c.inertia_cost_gbp,
        c.cost_per_sq_km,
        ST_ASGEOJSON(d.boundary) as boundary_geojson,
        ST_Y(ST_CENTROID(d.boundary)) as center_lat,
        ST_X(ST_CENTROID(d.boundary)) as center_lng
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries` d
    JOIN `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno_latest` c
        ON d.dno_id = c.dno_id
    ORDER BY c.total_cost_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    print(f'✅ Retrieved {len(df)} DNO regions with boundaries')
    return df

def create_interactive_map(df, output_file='dno_constraint_map.html'):
    """Create interactive Folium map with DNO boundaries"""
    print('\n🗺️  Creating interactive map...')
    
    # UK center coordinates
    uk_center = [54.5, -3.5]
    
    # Create map
    m = folium.Map(
        location=uk_center,
        zoom_start=6,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Calculate color scale (red gradient based on cost)
    max_cost = df['total_cost_gbp'].max()
    min_cost = df['total_cost_gbp'].min()
    
    def get_color(cost):
        """Get color based on cost (light to dark blue)"""
        if max_cost == min_cost:
            return '#4575b4'
        
        # Normalize cost to 0-1 range
        normalized = (cost - min_cost) / (max_cost - min_cost)
        
        # Blue color gradient (light to dark)
        if normalized < 0.2:
            return '#e0f3f8'  # Very light blue
        elif normalized < 0.4:
            return '#abd9e9'  # Light blue
        elif normalized < 0.6:
            return '#74add1'  # Medium blue
        elif normalized < 0.8:
            return '#4575b4'  # Dark blue
        else:
            return '#313695'  # Very dark blue
    
    # Add DNO polygons to map
    for idx, row in df.iterrows():
        # Parse GeoJSON boundary
        boundary_geojson = json.loads(row['boundary_geojson'])
        
        # Get color based on cost
        color = get_color(row['total_cost_gbp'])
        
        # Create popup with cost details
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 250px;">
            <h4 style="margin: 5px 0; color: #333;">{row['dno_full_name']}</h4>
            <hr style="margin: 5px 0;">
            <b>Region:</b> {row['area_name']}<br>
            <b>DNO Code:</b> {row['dno_code']}<br>
            <hr style="margin: 5px 0;">
            <b style="color: #d73027;">Total Cost:</b> £{row['total_cost_gbp']:,.0f}<br>
            <b style="color: #fc8d59;">Voltage:</b> £{row['voltage_cost_gbp']:,.0f}<br>
            <b style="color: #e34a33;">Thermal:</b> £{row['thermal_cost_gbp']:,.0f}<br>
            <b style="color: #31a354;">Inertia:</b> £{row['inertia_cost_gbp']:,.0f}<br>
            <hr style="margin: 5px 0;">
            <b>Cost Density:</b> £{row['cost_per_sq_km']:.2f}/km²
        </div>
        """
        
        # Add polygon to map
        folium.GeoJson(
            boundary_geojson,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': '#2c3e50',  # Border color
                'weight': 2,
                'fillOpacity': 0.6
            },
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['area_name']}: £{row['total_cost_gbp']:,.0f}"
        ).add_to(m)
        
        # Add label at centroid
        folium.Marker(
            location=[row['center_lat'], row['center_lng']],
            icon=folium.DivIcon(html=f"""
                <div style="
                    font-size: 10px; 
                    font-weight: bold; 
                    color: #2c3e50; 
                    text-align: center;
                    text-shadow: 1px 1px 2px white, -1px -1px 2px white;
                    white-space: nowrap;
                ">
                    {row['dno_code']}
                </div>
            """)
        ).add_to(m)
    
    # Add legend
    legend_html = f"""
    <div style="
        position: fixed; 
        top: 10px; right: 10px; 
        width: 220px; 
        background-color: white; 
        border: 2px solid grey; 
        z-index: 9999; 
        font-size: 12px;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0,0,0,0.3);
    ">
        <h4 style="margin: 0 0 10px 0;">DNO Constraint Costs</h4>
        <p style="margin: 5px 0;"><b>Latest Month (Dec 2025)</b></p>
        <hr style="margin: 5px 0;">
        <div style="margin: 5px 0;">
            <span style="background: #e0f3f8; padding: 3px 10px; border: 1px solid #999;">Low</span>
            <span style="background: #abd9e9; padding: 3px 10px; border: 1px solid #999;"></span>
            <span style="background: #74add1; padding: 3px 10px; border: 1px solid #999;"></span>
            <span style="background: #4575b4; padding: 3px 10px; border: 1px solid #999;"></span>
            <span style="background: #313695; padding: 3px 10px; border: 1px solid #999;">High</span>
        </div>
        <p style="margin: 5px 0; font-size: 10px;">
            Min: £{min_cost:,.0f}<br>
            Max: £{max_cost:,.0f}
        </p>
        <hr style="margin: 5px 0;">
        <p style="margin: 5px 0; font-size: 10px;">
            <b>Total (14 DNOs):</b> £{df['total_cost_gbp'].sum():,.0f}<br>
            <b>Average:</b> £{df['total_cost_gbp'].mean():,.0f}
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    m.save(output_file)
    print(f'✅ Map saved to: {output_file}')
    
    return output_file

def main():
    print('🚀 Creating DNO Constraint Cost Map with Boundaries')
    print('='*80)
    
    # Fetch data
    df = fetch_dno_data_with_boundaries()
    
    # Create map
    output_file = 'dno_constraint_map.html'
    create_interactive_map(df, output_file)
    
    print('\n' + '='*80)
    print('✅ SUCCESS: Interactive DNO map created')
    print('='*80)
    print(f'\nOpen: {output_file}')
    print('Or run: firefox dno_constraint_map.html')
    print('\nFeatures:')
    print('  • DNO boundaries with accurate GEOGRAPHY polygons')
    print('  • Color-coded by constraint costs (blue gradient)')
    print('  • Interactive tooltips with cost breakdown')
    print('  • DNO codes labeled on map')
    print('  • Legend with cost ranges')
    print('  • Focused on UK only (no Europe)')

if __name__ == '__main__':
    main()
