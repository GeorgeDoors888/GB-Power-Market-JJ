#!/usr/bin/env python3
"""
GB Power Market - GSP Regional Map Generator
==============================================
Creates interactive maps showing:
- Generators by fuel type and capacity
- GSP (Grid Supply Point) zones
- Transmission boundaries (B1-B17)
- Real-time generation by region
"""

import folium
from folium import plugins
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import pandas as pd
import json
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

# UK center coordinates
UK_CENTER = [54.5, -3.5]

# Fuel type colors
FUEL_COLORS = {
    'WIND': '#00a86b',      # Green
    'NUCLEAR': '#ff6b6b',   # Red
    'CCGT': '#ffa500',      # Orange
    'COAL': '#8b4513',      # Brown
    'BIOMASS': '#9acd32',   # Yellow-green
    'HYDRO': '#4169e1',     # Blue
    'BATTERY': '#9400d3',   # Purple
    'OIL': '#2f4f4f',       # Dark grey
    'OCGT': '#ff8c00',      # Dark orange
    'OTHER': '#808080'      # Grey
}

# GSP Group colors (14 DNO regions _A through _P)
GSP_COLORS = [
    '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
    '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
    '#008080', '#e6beff', '#9a6324', '#fffac8'
]


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_generators():
    """Load BMU generators (no coordinates in this table)"""
    print("📍 Loading BMU generator data...")
    
    query = f"""
    SELECT 
        nationalgridbmunit as bmu_code,
        bmunitname as name,
        fueltype as fuel_type,
        generationcapacity as capacity_mw,
        gspgroupid as gsp_group,
        gspgroupname as gsp_name
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE generationcapacity > 0
    ORDER BY generationcapacity DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df)} BMU generators (no coordinates)")
    return df


def load_sva_generators():
    """Load small SVA generators with coordinates"""
    print("📍 Loading SVA (small) generators with coordinates...")
    
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
      AND capacity_mw > 0
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df)} SVA generators with coordinates")
    return df


def load_transmission_boundaries():
    """Load latest generation by transmission boundary (B1-B17)"""
    print("⚡ Loading transmission boundary generation...")
    
    query = f"""
    WITH latest AS (
        SELECT MAX(settlementDate) as max_date
        FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
    )
    SELECT 
        boundary,
        ROUND(AVG(generation), 2) as avg_generation_mw,
        ROUND(MAX(generation), 2) as max_generation_mw,
        COUNT(*) as data_points
    FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
    CROSS JOIN latest
    WHERE DATE(settlementDate) = DATE(latest.max_date)
      AND boundary != 'N'  -- Exclude national total
    GROUP BY boundary
    ORDER BY boundary
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df)} transmission boundaries")
    return df


def aggregate_by_gsp_group():
    """Aggregate generation by GSP group (_A through _P)"""
    print("🗺️ Aggregating generation by GSP group...")
    
    query = f"""
    SELECT 
        gspgroupid as gsp_group,
        gspgroupname as gsp_name,
        COUNT(DISTINCT nationalgridbmunit) as num_generators,
        ROUND(SUM(generationcapacity), 2) as total_capacity_mw,
        STRING_AGG(DISTINCT fueltype ORDER BY fueltype) as fuel_types
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE gspgroupid IS NOT NULL
      AND generationcapacity > 0
    GROUP BY gspgroupid, gspgroupname
    ORDER BY gspgroupid
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Aggregated {len(df)} GSP groups")
    return df


# ============================================================================
# Map Creation Functions
# ============================================================================

def create_generator_map(sva_generators_df, output_file='gb_generators_map.html'):
    """Create interactive map showing SVA generators (with coordinates) colored by fuel type"""
    print(f"\n🗺️ Creating generator map: {output_file}")
    
    # Create base map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add alternative tile layers
    folium.TileLayer('CartoDB positron', name='Light').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark').add_to(m)
    
    # Group generators by technology/fuel type
    fuel_groups = {}
    for fuel_type in sva_generators_df['fuel_type'].unique():
        if pd.notna(fuel_type):
            fuel_groups[fuel_type] = folium.FeatureGroup(name=f'{fuel_type} Generators')
    
    # Add generators as markers
    for idx, gen in sva_generators_df.iterrows():
        if pd.notna(gen['latitude']) and pd.notna(gen['longitude']):
            fuel = gen['fuel_type'] if pd.notna(gen['fuel_type']) else 'OTHER'
            color = FUEL_COLORS.get(fuel, FUEL_COLORS['OTHER'])
            
            # Size based on capacity
            radius = min(max(gen['capacity_mw'] / 5, 2), 10)
            
            # Popup text
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <h4 style="margin: 0 0 10px 0;">{gen['generator_name']}</h4>
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><b>Technology:</b></td><td>{gen['technology']}</td></tr>
                    <tr><td><b>Fuel:</b></td><td>{fuel}</td></tr>
                    <tr><td><b>Capacity:</b></td><td>{gen['capacity_mw']:.1f} MW</td></tr>
                    <tr><td><b>GSP:</b></td><td>{gen['gsp_group']}</td></tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[gen['latitude'], gen['longitude']],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{gen['generator_name']} ({gen['capacity_mw']:.1f} MW)",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(fuel_groups.get(fuel, m))
    
    # Add all fuel type groups to map
    for group in fuel_groups.values():
        group.add_to(m)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 16px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">🔌 GB Power Generators Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            {count} generators | Updated: {date}
        </p>
    </div>
    '''.format(count=len(sva_generators_df), date=datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    print(f"✅ Map saved: {output_file}")
    return output_file


def create_gsp_regional_map(gsp_df, output_file='gb_gsp_regions_map.html'):
    """Create map showing GSP groups with aggregated capacity"""
    print(f"\n🗺️ Creating GSP regional map: {output_file}")
    
    # GSP group approximate centers (DNO regions)
    gsp_centers = {
        '_A': (51.5, -0.1, 'Eastern'),           # London/Eastern
        '_B': (52.5, 1.0, 'East Anglia'),        # East Anglia
        '_C': (51.3, -0.8, 'South East'),        # South East
        '_D': (51.0, -1.3, 'Southern'),          # Southern
        '_E': (50.8, -1.8, 'South Western'),     # South Western
        '_F': (52.3, -1.5, 'West Midlands'),     # West Midlands
        '_G': (52.8, -2.0, 'North West'),        # North West (Shropshire)
        '_H': (54.0, -2.0, 'North West'),        # North West (Cumbria)
        '_J': (53.8, -1.5, 'Yorkshire'),         # Yorkshire
        '_K': (54.5, -1.5, 'North East'),        # North East
        '_L': (55.8, -4.2, 'South Scotland'),    # South Scotland
        '_M': (56.5, -3.5, 'Mid Scotland'),      # Mid Scotland
        '_N': (57.5, -4.0, 'North Scotland'),    # North Scotland
        '_P': (51.5, -3.0, 'South Wales'),       # South Wales
    }
    
    # Create base map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add GSP groups as markers
    for idx, gsp in gsp_df.iterrows():
        gsp_id = gsp['gsp_group']
        if gsp_id in gsp_centers:
            lat, lon, region_name = gsp_centers[gsp_id]
            
            # Color based on capacity
            color_idx = list(gsp_centers.keys()).index(gsp_id) % len(GSP_COLORS)
            color = GSP_COLORS[color_idx]
            
            # Radius based on capacity
            radius = min(max(gsp['total_capacity_mw'] / 500, 10), 40)
            
            popup_html = f"""
            <div style="font-family: Arial; width: 250px;">
                <h4 style="margin: 0 0 10px 0;">GSP Group {gsp_id}</h4>
                <h5 style="margin: 0 0 10px 0;">{gsp['gsp_name']}</h5>
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><b>Generators:</b></td><td>{gsp['num_generators']}</td></tr>
                    <tr><td><b>Total Capacity:</b></td><td>{gsp['total_capacity_mw']:,.0f} MW</td></tr>
                    <tr><td><b>Fuel Types:</b></td><td>{gsp['fuel_types']}</td></tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"GSP {gsp_id} - {gsp['gsp_name']} ({gsp['total_capacity_mw']:,.0f} MW)",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                weight=3
            ).add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 16px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">🗺️ GSP Regional Capacity Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            14 GSP Groups | Total: {total:,.0f} MW
        </p>
    </div>
    '''.format(total=gsp_df['total_capacity_mw'].sum())
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    print(f"✅ Map saved: {output_file}")
    return output_file


def create_transmission_boundary_map(boundary_df, output_file='gb_transmission_boundaries_map.html'):
    """Create heatmap showing transmission boundary generation"""
    print(f"\n🗺️ Creating transmission boundary map: {output_file}")
    
    # Approximate boundary zone centers (B1-B17)
    boundary_centers = {
        'B1': (51.5, 0.5, 'South East Coast'),
        'B2': (51.3, -0.5, 'London'),
        'B3': (50.8, -1.1, 'South Coast'),
        'B4': (51.0, -2.5, 'South West'),
        'B5': (52.5, -1.5, 'Midlands East'),
        'B6': (52.0, -2.5, 'Midlands West'),
        'B7': (53.5, -1.5, 'Yorkshire'),
        'B8': (53.0, -3.0, 'North West'),
        'B9': (56.0, -4.0, 'Scotland'),
        'B10': (51.5, -3.5, 'South Wales'),
        'B11': (54.5, -2.0, 'North East'),
        'B12': (52.5, 1.0, 'East Anglia'),
        'B13': (50.5, -4.0, 'Cornwall'),
        'B14': (54.0, -3.0, 'Cumbria'),
        'B15': (52.0, -0.5, 'East Midlands'),
        'B16': (55.0, -1.5, 'Northumbria'),
        'B17': (53.0, -1.0, 'South Yorkshire'),
    }
    
    # Create base map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB dark_matter'
    )
    
    # Normalize generation for color intensity
    max_gen = boundary_df['avg_generation_mw'].max()
    
    # Add boundary zones
    for idx, boundary in boundary_df.iterrows():
        b_id = boundary['boundary']
        if b_id in boundary_centers:
            lat, lon, name = boundary_centers[b_id]
            
            # Color intensity based on generation
            intensity = boundary['avg_generation_mw'] / max_gen
            # Red = high generation, Yellow = medium, Green = low
            if intensity > 0.7:
                color = '#ff0000'
            elif intensity > 0.4:
                color = '#ff6600'
            elif intensity > 0.2:
                color = '#ffcc00'
            else:
                color = '#00ff00'
            
            # Radius based on generation
            radius = min(max(boundary['avg_generation_mw'] / 500, 10), 50)
            
            popup_html = f"""
            <div style="font-family: Arial; width: 250px;">
                <h4 style="margin: 0 0 10px 0;">Boundary {b_id} - {name}</h4>
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><b>Avg Generation:</b></td><td>{boundary['avg_generation_mw']:,.0f} MW</td></tr>
                    <tr><td><b>Peak Generation:</b></td><td>{boundary['max_generation_mw']:,.0f} MW</td></tr>
                    <tr><td><b>Data Points:</b></td><td>{boundary['data_points']}</td></tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{b_id} - {name} ({boundary['avg_generation_mw']:,.0f} MW)",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=3
            ).add_to(m)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 450px; height: 80px; 
                background-color: white; border: 2px solid grey;
                z-index: 9999; font-size: 16px; padding: 10px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h3 style="margin: 0;">⚡ Transmission Boundary Generation</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            17 Boundaries (B1-B17) | Real-time IRIS data<br/>
            🔴 High (>70%) 🟠 Medium (40-70%) 🟡 Low (20-40%) 🟢 Very Low (<20%)
        </p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    print(f"✅ Map saved: {output_file}")
    return output_file


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Generate all maps"""
    print("=" * 80)
    print("🗺️ GB POWER MARKET - MAP GENERATOR")
    print("=" * 80)
    
    # Load data
    bmu_df = load_generators()  # No coordinates
    sva_generators_df = load_sva_generators()  # Has coordinates
    gsp_df = aggregate_by_gsp_group()
    boundary_df = load_transmission_boundaries()
    
    print(f"\n📊 Data Summary:")
    print(f"   • BMU Generators: {len(bmu_df)} (no coordinates)")
    print(f"   • SVA Generators: {len(sva_generators_df)} (with coordinates)")
    print(f"   • GSP Groups: {len(gsp_df)}")
    print(f"   • Transmission Boundaries: {len(boundary_df)}")
    
    # Generate maps
    print("\n" + "=" * 80)
    print("🎨 Generating Maps...")
    print("=" * 80)
    
    map1 = create_generator_map(sva_generators_df)  # Use SVA data with coordinates
    map2 = create_gsp_regional_map(gsp_df)
    map3 = create_transmission_boundary_map(boundary_df)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ MAP GENERATION COMPLETE")
    print("=" * 80)
    print(f"\n📁 Generated files:")
    print(f"   1. {map1} - SVA generators by fuel type (with coordinates)")
    print(f"   2. {map2} - GSP groups with capacity")
    print(f"   3. {map3} - Transmission boundary heatmap")
    print(f"\n💡 Open these HTML files in your browser to view interactive maps!")
    print(f"\n📝 Note: BMU generators ({len(bmu_df)}) don't have coordinates in BigQuery")
    print(f"         Only SVA generators ({len(sva_generators_df)}) are shown on map 1")


if __name__ == '__main__':
    main()
