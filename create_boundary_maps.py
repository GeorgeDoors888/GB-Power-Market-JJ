#!/usr/bin/env python3
"""
GB Power Market - Enhanced Map Generator with GeoJSON Boundaries
=================================================================
Creates interactive maps with actual boundary polygons from GeoJSON files:
- DNO regional boundaries (14 zones)
- GSP catchment areas (333 zones)
- Generator locations overlaid on boundaries
- Real-time generation data by region
"""

import folium
from folium import plugins
import json
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

UK_CENTER = [54.5, -3.5]

# Color schemes
DNO_COLORS = {
    'UKPN': '#e74c3c',      # Red
    'SPEN': '#3498db',      # Blue
    'NGED': '#2ecc71',      # Green
    'SSEN': '#f39c12',      # Orange
    'NPG': '#9b59b6',       # Purple
    'ENWL': '#1abc9c',      # Turquoise
    'Default': '#95a5a6'    # Gray
}

GSP_GRADIENT = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', 
                '#fc4e2a', '#e31a1c', '#bd0026', '#800026']

# ============================================================================
# GeoJSON Loading
# ============================================================================

def load_geojson(filename):
    """Load GeoJSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading {filename}: {e}")
        return None


def load_dno_boundaries():
    """Load DNO boundary GeoJSON"""
    return load_geojson('official_dno_boundaries.geojson')


def load_gsp_boundaries():
    """Load GSP boundary GeoJSON"""
    return load_geojson('official_gsp_boundaries.geojson')


def load_gsp_zones():
    """Load GSP zones (detailed)"""
    return load_geojson('gsp_zones.geojson')


# ============================================================================
# BigQuery Data Loading
# ============================================================================

def get_generators_by_region():
    """Get generator counts and capacity by GSP group"""
    query = f"""
    SELECT 
        gspgroupid as gsp_group,
        gspgroupname as gsp_name,
        COUNT(DISTINCT nationalgridbmunit) as num_generators,
        ROUND(SUM(generationcapacity), 0) as total_capacity_mw,
        ROUND(SUM(CASE WHEN fueltype = 'WIND' THEN generationcapacity ELSE 0 END), 0) as wind_mw,
        ROUND(SUM(CASE WHEN fueltype = 'SOLAR' THEN generationcapacity ELSE 0 END), 0) as solar_mw,
        ROUND(SUM(CASE WHEN fueltype = 'GAS' THEN generationcapacity ELSE 0 END), 0) as gas_mw,
        ROUND(SUM(CASE WHEN fueltype = 'NUCLEAR' THEN generationcapacity ELSE 0 END), 0) as nuclear_mw
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE gspgroupid IS NOT NULL
      AND generationcapacity > 0
    GROUP BY gspgroupid, gspgroupname
    ORDER BY total_capacity_mw DESC
    """
    
    return bq_client.query(query).to_dataframe()


def get_sva_generators():
    """Get small generators with coordinates"""
    query = f"""
    SELECT 
        name as generator_name,
        technology,
        capacity_mw,
        gsp as gsp_group,
        lat as latitude,
        lng as longitude,
        fuel_type
    FROM `{PROJECT_ID}.{DATASET}.sva_generators_with_coords`
    WHERE lat IS NOT NULL 
      AND lng IS NOT NULL
      AND capacity_mw > 1
    LIMIT 1000
    """
    
    return bq_client.query(query).to_dataframe()


def get_transmission_data():
    """Get latest transmission boundary generation"""
    query = f"""
    WITH latest AS (
        SELECT MAX(settlementDate) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
    )
    SELECT 
        boundary,
        ROUND(AVG(generation), 0) as avg_generation_mw,
        ROUND(MAX(generation), 0) as max_generation_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
    CROSS JOIN latest
    WHERE DATE(settlementDate) = DATE(latest.max_date)
      AND boundary != 'N'
    GROUP BY boundary
    ORDER BY avg_generation_mw DESC
    """
    
    return bq_client.query(query).to_dataframe()


# ============================================================================
# Map Creation Functions
# ============================================================================

def create_dno_boundary_map(output_file='map_dno_boundaries.html'):
    """Create map with DNO boundaries and capacity data"""
    print(f"🗺️ Creating DNO boundary map: {output_file}")
    
    # Load data
    dno_geojson = load_dno_boundaries()
    capacity_data = get_generators_by_region()
    
    if not dno_geojson:
        print("❌ DNO GeoJSON not found")
        return None
    
    # Create capacity lookup by region
    capacity_lookup = {}
    for _, row in capacity_data.iterrows():
        gsp_group = row['gsp_group']
        capacity_lookup[gsp_group] = {
            'capacity': row['total_capacity_mw'],
            'generators': row['num_generators'],
            'name': row['gsp_name'],
            'wind': row['wind_mw'],
            'solar': row['solar_mw'],
            'gas': row['gas_mw'],
            'nuclear': row['nuclear_mw']
        }
    
    # Create map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    # Add DNO boundaries with capacity data
    for feature in dno_geojson['features']:
        props = feature['properties']
        dno_name = props.get('Name', props.get('dno_name', 'Unknown'))
        dno_full = props.get('DNO_Full', props.get('DNO', dno_name))
        area = props.get('Area', props.get('area', 'N/A'))
        
        # Get GSP group from properties or map DNO to GSP
        gsp_group = props.get('gsp_group', None)
        
        # Try to match capacity data
        capacity_info = None
        if gsp_group and gsp_group in capacity_lookup:
            capacity_info = capacity_lookup[gsp_group]
        
        # Determine color based on DNO
        color = DNO_COLORS.get('Default')
        for dno_key in DNO_COLORS:
            if dno_key in dno_full.upper():
                color = DNO_COLORS[dno_key]
                break
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial; width: 280px;">
            <h4 style="margin: 0 0 10px 0; color: {color};">{dno_name}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>DNO:</b></td><td>{dno_full}</td></tr>
                <tr><td><b>Area:</b></td><td>{area} km²</td></tr>
        """
        
        if capacity_info:
            popup_html += f"""
                <tr><td colspan="2"><hr style="margin: 5px 0;"></td></tr>
                <tr><td><b>Generators:</b></td><td>{capacity_info['generators']}</td></tr>
                <tr><td><b>Total Capacity:</b></td><td>{capacity_info['capacity']:,.0f} MW</td></tr>
                <tr><td><b>Wind:</b></td><td>{capacity_info['wind']:,.0f} MW</td></tr>
                <tr><td><b>Solar:</b></td><td>{capacity_info['solar']:,.0f} MW</td></tr>
                <tr><td><b>Gas:</b></td><td>{capacity_info['gas']:,.0f} MW</td></tr>
                <tr><td><b>Nuclear:</b></td><td>{capacity_info['nuclear']:,.0f} MW</td></tr>
            """
        
        popup_html += """
            </table>
        </div>
        """
        
        # Add to map
        folium.GeoJson(
            feature,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.5
            },
            highlight_function=lambda x: {
                'fillColor': '#ffff00',
                'fillOpacity': 0.7
            },
            tooltip=dno_name,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 450px; height: 80px; 
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 16px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">⚡ GB DNO Regional Boundaries</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            14 Distribution Network Operator zones<br/>
            Total capacity: {capacity_data['total_capacity_mw'].sum():,.0f} MW<br/>
            Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px;
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 12px; padding: 10px;">
        <h4 style="margin: 0 0 10px 0;">DNO Companies</h4>
        <div style="line-height: 20px;">
            <span style="color: #e74c3c;">⬤</span> UK Power Networks<br/>
            <span style="color: #3498db;">⬤</span> Scottish Power<br/>
            <span style="color: #2ecc71;">⬤</span> National Grid (NGED)<br/>
            <span style="color: #f39c12;">⬤</span> SSE Networks<br/>
            <span style="color: #9b59b6;">⬤</span> Northern Powergrid<br/>
            <span style="color: #1abc9c;">⬤</span> Electricity NW
        </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    plugins.Fullscreen().add_to(m)
    
    m.save(output_file)
    print(f"✅ Saved: {output_file}")
    return output_file


def create_gsp_capacity_map(output_file='map_gsp_capacity.html'):
    """Create choropleth map of GSP zones colored by capacity"""
    print(f"🗺️ Creating GSP capacity map: {output_file}")
    
    # Load data
    gsp_geojson = load_gsp_zones()
    capacity_data = get_generators_by_region()
    
    if not gsp_geojson:
        print("❌ GSP GeoJSON not found")
        return None
    
    # Create capacity lookup
    capacity_lookup = {}
    for _, row in capacity_data.iterrows():
        capacity_lookup[row['gsp_group']] = row['total_capacity_mw']
    
    max_capacity = capacity_data['total_capacity_mw'].max()
    
    # Create map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    # Add GSP zones with capacity-based coloring
    for feature in gsp_geojson['features']:
        props = feature['properties']
        gsp_group = props.get('gsp_group', props.get('GSPGroup'))
        gsp_name = props.get('gsp_name', props.get('GSPs', 'Unknown'))
        area = props.get('area_sqkm', 'N/A')
        
        # Get capacity
        capacity = capacity_lookup.get(gsp_group, 0)
        
        # Calculate color based on capacity
        if capacity > 0:
            intensity = min(capacity / max_capacity, 1.0)
            color_idx = int(intensity * (len(GSP_GRADIENT) - 1))
            color = GSP_GRADIENT[color_idx]
        else:
            color = '#e0e0e0'
        
        # Create popup
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="margin: 0 0 10px 0;">{gsp_name}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>GSP Group:</b></td><td>{gsp_group}</td></tr>
                <tr><td><b>Capacity:</b></td><td>{capacity:,.0f} MW</td></tr>
                <tr><td><b>Area:</b></td><td>{area} km²</td></tr>
            </table>
        </div>
        """
        
        folium.GeoJson(
            feature,
            style_function=lambda x, color=color: {
                'fillColor': color,
                'color': 'gray',
                'weight': 1,
                'fillOpacity': 0.7
            },
            highlight_function=lambda x: {
                'fillOpacity': 0.9,
                'weight': 2
            },
            tooltip=f"{gsp_name}: {capacity:,.0f} MW",
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 450px; height: 80px; 
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 16px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">🔌 GSP Generation Capacity</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            333 Grid Supply Point zones<br/>
            Color intensity = generation capacity<br/>
            Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add gradient legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px;
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 12px; padding: 10px;">
        <h4 style="margin: 0 0 10px 0;">Capacity (MW)</h4>
        <div style="background: linear-gradient(to right, #ffffcc, #800026); 
                    height: 20px; border: 1px solid black;"></div>
        <div style="display: flex; justify-content: space-between; font-size: 10px; margin-top: 5px;">
            <span>Low</span>
            <span>High</span>
        </div>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    plugins.Fullscreen().add_to(m)
    
    m.save(output_file)
    print(f"✅ Saved: {output_file}")
    return output_file


def create_combined_map(output_file='map_combined_boundaries.html'):
    """Create map with generators overlaid on DNO boundaries"""
    print(f"🗺️ Creating combined boundary + generator map: {output_file}")
    
    # Load data
    dno_geojson = load_dno_boundaries()
    generators = get_sva_generators()
    
    if not dno_geojson:
        print("❌ DNO GeoJSON not found")
        return None
    
    # Create map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    # Add DNO boundaries (background layer)
    boundary_layer = folium.FeatureGroup(name='DNO Boundaries')
    
    for feature in dno_geojson['features']:
        props = feature['properties']
        dno_name = props.get('Name', props.get('dno_name', 'Unknown'))
        
        folium.GeoJson(
            feature,
            style_function=lambda x: {
                'fillColor': '#e0e0e0',
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.3
            },
            tooltip=dno_name
        ).add_to(boundary_layer)
    
    boundary_layer.add_to(m)
    
    # Add generators by fuel type
    fuel_colors = {
        'Wind': '#00a86b',
        'Solar': '#ffd700',
        'Hydro': '#4169e1',
        'Gas': '#ffa500',
        'Nuclear': '#ff6b6b',
        'Battery': '#9400d3',
        'Biomass': '#9acd32',
        'Other': '#808080'
    }
    
    fuel_layers = {}
    for fuel_type in generators['fuel_type'].unique():
        if pd.notna(fuel_type):
            fuel_layers[fuel_type] = folium.FeatureGroup(name=f'{fuel_type} Generators')
    
    for _, gen in generators.iterrows():
        if pd.notna(gen['latitude']) and pd.notna(gen['longitude']):
            fuel = gen['fuel_type'] if pd.notna(gen['fuel_type']) else 'Other'
            color = fuel_colors.get(fuel, fuel_colors['Other'])
            
            radius = min(max(gen['capacity_mw'] / 5, 2), 8)
            
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <h4 style="margin: 0 0 10px 0;">{gen['generator_name']}</h4>
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><b>Technology:</b></td><td>{gen['technology']}</td></tr>
                    <tr><td><b>Capacity:</b></td><td>{gen['capacity_mw']:.1f} MW</td></tr>
                    <tr><td><b>GSP:</b></td><td>{gen['gsp_group']}</td></tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[gen['latitude'], gen['longitude']],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{gen['generator_name']} ({gen['capacity_mw']:.1f} MW)",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=1
            ).add_to(fuel_layers.get(fuel, m))
    
    # Add fuel layers to map
    for layer in fuel_layers.values():
        layer.add_to(m)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add title
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 80px; 
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 16px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">🗺️ GB Power Infrastructure Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            {len(generators)} generators shown on DNO boundaries<br/>
            Toggle layers to filter by fuel type<br/>
            Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    plugins.Fullscreen().add_to(m)
    
    m.save(output_file)
    print(f"✅ Saved: {output_file}")
    return output_file


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 80)
    print("🗺️ GB POWER MARKET - GEOJSON BOUNDARY MAPS")
    print("=" * 80)
    
    print("\n📂 Loading GeoJSON files...")
    dno_geo = load_dno_boundaries()
    gsp_geo = load_gsp_zones()
    
    print(f"   {'✅' if dno_geo else '❌'} DNO boundaries: {len(dno_geo['features']) if dno_geo else 0} features")
    print(f"   {'✅' if gsp_geo else '❌'} GSP zones: {len(gsp_geo['features']) if gsp_geo else 0} features")
    
    print("\n📊 Loading data from BigQuery...")
    capacity_data = get_generators_by_region()
    generators = get_sva_generators()
    transmission = get_transmission_data()
    
    print(f"   • Capacity data: {len(capacity_data)} GSP groups")
    print(f"   • SVA generators: {len(generators)} with coordinates")
    print(f"   • Transmission boundaries: {len(transmission)} zones")
    
    print("\n🎨 Generating maps...")
    
    maps_created = []
    
    # Map 1: DNO boundaries with capacity
    map1 = create_dno_boundary_map()
    if map1:
        maps_created.append(('DNO Boundaries', map1))
    
    # Map 2: GSP capacity choropleth
    map2 = create_gsp_capacity_map()
    if map2:
        maps_created.append(('GSP Capacity', map2))
    
    # Map 3: Combined boundaries + generators
    map3 = create_combined_map()
    if map3:
        maps_created.append(('Combined Infrastructure', map3))
    
    print("\n" + "=" * 80)
    print("✅ MAP GENERATION COMPLETE")
    print("=" * 80)
    
    if maps_created:
        print(f"\n📁 Created {len(maps_created)} maps:")
        for name, filename in maps_created:
            print(f"   • {filename} - {name}")
        
        print("\n💡 Open in browser to view interactive maps with:")
        print("   • Click regions for detailed capacity data")
        print("   • Toggle generator layers by fuel type")
        print("   • Zoom and pan for detailed exploration")
    else:
        print("\n⚠️ No maps created - check GeoJSON files exist")


if __name__ == '__main__':
    main()
