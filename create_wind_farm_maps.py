#!/usr/bin/env python3
"""
GB Power Market - Wind Farm Map Generator
==========================================
Creates interactive maps focused on wind generation:
- Offshore wind farms with capacity and turbine data
- Onshore wind farms (>= 1 MW) with GSP connections
- GSP zones colored by wind capacity
- Wind speed forecast data overlays
"""

import folium
from folium import plugins
import json
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import os

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Try both credential files
if os.path.exists('arbitrage-bq-key.json'):
    CREDS = Credentials.from_service_account_file('arbitrage-bq-key.json')
elif os.path.exists('inner-cinema-credentials.json'):
    CREDS = Credentials.from_service_account_file('inner-cinema-credentials.json')
else:
    CREDS = None

bq_client = bigquery.Client(project=PROJECT_ID, location='US', credentials=CREDS)

UK_CENTER = [54.5, -3.5]

# Wind-specific color scheme
WIND_COLORS = {
    'offshore': '#0077be',      # Ocean blue
    'onshore': '#2ecc71',       # Green
    'gsp': '#e74c3c',          # Red for GSP points
}

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


def load_gsp_boundaries():
    """Load GSP boundary GeoJSON"""
    return load_geojson('gsp_zones.geojson')


def load_dno_boundaries():
    """Load DNO boundary GeoJSON"""
    return load_geojson('official_dno_boundaries.geojson')


# ============================================================================
# BigQuery Data Loading
# ============================================================================

def get_offshore_wind_farms():
    """Get offshore wind farm data"""
    query = f"""
    SELECT 
        name,
        latitude,
        longitude,
        capacity_mw,
        turbine_count,
        commissioned_year,
        manufacturer,
        model,
        owner,
        gsp_zone,
        gsp_region
    FROM `{PROJECT_ID}.{DATASET}.offshore_wind_farms`
    WHERE status = 'Operational'
      AND latitude IS NOT NULL
    ORDER BY capacity_mw DESC
    """
    
    print("📥 Loading offshore wind farms...")
    df = bq_client.query(query).to_dataframe()
    print(f"   ✅ {len(df)} offshore wind farms")
    return df


def get_onshore_wind_farms():
    """Get onshore wind farms >= 1 MW from all_generators"""
    query = f"""
    SELECT 
        customer_site as name,
        location_x_coordinate_eastings_where_data_is_held as easting,
        location_y_coordinate_northings_where_data_is_held as northing,
        SAFE_CAST(energy_source_and_energy_conversion_technology_1_registered_capacity_mw AS FLOAT64) as capacity_mw,
        grid_supply_point as gsp,
        bulk_supply_point as bsp,
        energy_conversion_technology_1 as technology,
        date_connected,
        licence_area as dno_region
    FROM `{PROJECT_ID}.{DATASET}.all_generators`
    WHERE energy_source_1 IN ('Wind', 'Wind onshore', 'Wind offshore')
      AND SAFE_CAST(energy_source_and_energy_conversion_technology_1_registered_capacity_mw AS FLOAT64) >= 1.0
      AND connection_status = 'Connected'
      AND location_x_coordinate_eastings_where_data_is_held IS NOT NULL
    ORDER BY capacity_mw DESC
    """
    
    print("📥 Loading onshore wind farms...")
    df = bq_client.query(query).to_dataframe()
    
    # Convert British National Grid to Lat/Lon
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    
    lats = []
    lons = []
    for idx, row in df.iterrows():
        try:
            lon, lat = transformer.transform(float(row['easting']), float(row['northing']))
            lats.append(lat)
            lons.append(lon)
        except:
            lats.append(None)
            lons.append(None)
    
    df['latitude'] = lats
    df['longitude'] = lons
    
    # Filter out bad coordinates
    df = df[(df['latitude'].notna()) & (df['longitude'].notna())]
    
    print(f"   ✅ {len(df)} onshore wind farms >= 1 MW")
    return df


def get_gsp_wind_capacity():
    """Get wind capacity by GSP zone"""
    query = f"""
    WITH wind_by_gsp AS (
        SELECT 
            gspgroupid as gsp_id,
            gspgroupname as gsp_name,
            COUNT(DISTINCT nationalgridbmunit) as num_wind_units,
            ROUND(SUM(generationcapacity), 1) as wind_capacity_mw
        FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
        WHERE fueltype = 'WIND'
          AND gspgroupid IS NOT NULL
        GROUP BY gspgroupid, gspgroupname
    )
    SELECT * FROM wind_by_gsp
    WHERE wind_capacity_mw > 0
    ORDER BY wind_capacity_mw DESC
    """
    
    print("📥 Loading GSP wind capacity...")
    df = bq_client.query(query).to_dataframe()
    print(f"   ✅ {len(df)} GSP zones with wind generation")
    return df


def get_wind_forecast_latest():
    """Get latest wind generation forecast"""
    query = f"""
    SELECT 
        settlementDate as date,
        settlementPeriod as period,
        quantity as forecast_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 48
    """
    
    try:
        print("📥 Loading wind forecast...")
        df = bq_client.query(query).to_dataframe()
        print(f"   ✅ {len(df)} forecast periods")
        return df
    except:
        print("   ⚠️ Wind forecast not available")
        return pd.DataFrame()


def get_gsp_locations():
    """Get GSP substation locations"""
    query = f"""
    SELECT DISTINCT
        grid_supply_point as gsp_name,
        AVG(SAFE_CAST(location_x_coordinate_eastings_where_data_is_held AS FLOAT64)) as easting,
        AVG(SAFE_CAST(location_y_coordinate_northings_where_data_is_held AS FLOAT64)) as northing
    FROM `{PROJECT_ID}.{DATASET}.all_generators`
    WHERE grid_supply_point IS NOT NULL
      AND location_x_coordinate_eastings_where_data_is_held IS NOT NULL
    GROUP BY grid_supply_point
    """
    
    print("📥 Loading GSP locations...")
    df = bq_client.query(query).to_dataframe()
    
    # Convert to lat/lon
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    
    lats = []
    lons = []
    for idx, row in df.iterrows():
        try:
            lon, lat = transformer.transform(float(row['easting']), float(row['northing']))
            lats.append(lat)
            lons.append(lon)
        except:
            lats.append(None)
            lons.append(None)
    
    df['latitude'] = lats
    df['longitude'] = lons
    df = df[(df['latitude'].notna()) & (df['longitude'].notna())]
    
    print(f"   ✅ {len(df)} GSP locations")
    return df


# ============================================================================
# Map Creation Functions
# ============================================================================

def create_wind_capacity_map():
    """Main map: All wind farms (offshore + onshore) with GSP zones"""
    print("\n🗺️  Creating wind capacity map...")
    
    # Create base map
    m = folium.Map(
        location=UK_CENTER,
        zoom_start=6,
        tiles='CartoDB positron'
    )
    
    # Load data
    offshore = get_offshore_wind_farms()
    onshore = get_onshore_wind_farms()
    gsp_capacity = get_gsp_wind_capacity()
    gsp_boundaries = load_gsp_boundaries()
    
    # Add GSP zone boundaries (colored by wind capacity)
    if gsp_boundaries:
        print("   📊 Adding GSP zones colored by wind capacity...")
        
        # Create capacity lookup
        capacity_lookup = dict(zip(gsp_capacity['gsp_id'], gsp_capacity['wind_capacity_mw']))
        
        # Get max capacity for color scaling
        max_capacity = gsp_capacity['wind_capacity_mw'].max() if not gsp_capacity.empty else 1000
        
        for feature in gsp_boundaries.get('features', []):
            props = feature.get('properties', {})
            gsp_id = props.get('gsp_group', '')
            gsp_name = props.get('gsp_name', 'Unknown')
            
            # Get capacity for this GSP
            capacity = capacity_lookup.get(gsp_id, 0)
            
            # Color intensity based on capacity
            if capacity > 0:
                intensity = min(capacity / max_capacity, 1.0)
                color = f'rgba(46, 204, 113, {0.3 + intensity * 0.4})'  # Green gradient
            else:
                color = 'rgba(200, 200, 200, 0.1)'  # Gray for no wind
            
            # Create popup
            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <b>{gsp_name}</b><br>
                GSP Group: {gsp_id}<br>
                Wind Capacity: <b>{capacity:.1f} MW</b>
            </div>
            """
            
            folium.GeoJson(
                feature,
                style_function=lambda x, c=color: {
                    'fillColor': c,
                    'color': '#2ecc71',
                    'weight': 1,
                    'fillOpacity': 0.5
                },
                tooltip=gsp_name,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
    
    # Add offshore wind farms
    offshore_group = folium.FeatureGroup(name='Offshore Wind Farms', show=True)
    
    print(f"   🌊 Adding {len(offshore)} offshore wind farms...")
    for idx, farm in offshore.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="margin: 0; color: #0077be;">{farm['name']}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Capacity:</b></td><td>{farm['capacity_mw']:.1f} MW</td></tr>
                <tr><td><b>Turbines:</b></td><td>{farm['turbine_count']}</td></tr>
                <tr><td><b>Manufacturer:</b></td><td>{farm['manufacturer']}</td></tr>
                <tr><td><b>Model:</b></td><td>{farm['model']}</td></tr>
                <tr><td><b>Commissioned:</b></td><td>{farm['commissioned_year']}</td></tr>
                <tr><td><b>Owner:</b></td><td>{farm['owner']}</td></tr>
                <tr><td><b>GSP Region:</b></td><td>{farm['gsp_region']}</td></tr>
            </table>
        </div>
        """
        
        # Size marker by capacity
        radius = 5 + (farm['capacity_mw'] / 100)
        
        folium.CircleMarker(
            location=[farm['latitude'], farm['longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{farm['name']} ({farm['capacity_mw']:.0f} MW)",
            color='#0077be',
            fillColor='#0077be',
            fillOpacity=0.7,
            weight=2
        ).add_to(offshore_group)
    
    offshore_group.add_to(m)
    
    # Add onshore wind farms
    onshore_group = folium.FeatureGroup(name='Onshore Wind Farms (>= 1 MW)', show=True)
    
    print(f"   🌬️  Adding {len(onshore)} onshore wind farms...")
    for idx, farm in onshore.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; width: 220px;">
            <h4 style="margin: 0; color: #2ecc71;">{farm['name']}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Capacity:</b></td><td>{farm['capacity_mw']:.1f} MW</td></tr>
                <tr><td><b>Technology:</b></td><td>{farm['technology']}</td></tr>
                <tr><td><b>GSP:</b></td><td>{farm['gsp']}</td></tr>
                <tr><td><b>DNO:</b></td><td>{farm['dno_region']}</td></tr>
                <tr><td><b>Connected:</b></td><td>{farm['date_connected']}</td></tr>
            </table>
        </div>
        """
        
        # Size marker by capacity
        radius = 3 + (farm['capacity_mw'] / 50)
        
        folium.CircleMarker(
            location=[farm['latitude'], farm['longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{farm['name']} ({farm['capacity_mw']:.0f} MW)",
            color='#2ecc71',
            fillColor='#2ecc71',
            fillOpacity=0.6,
            weight=1
        ).add_to(onshore_group)
    
    onshore_group.add_to(m)
    
    # Add GSP points
    gsp_locations = get_gsp_locations()
    gsp_group = folium.FeatureGroup(name='GSP Substations', show=False)
    
    print(f"   ⚡ Adding {len(gsp_locations)} GSP locations...")
    for idx, gsp in gsp_locations.iterrows():
        folium.CircleMarker(
            location=[gsp['latitude'], gsp['longitude']],
            radius=4,
            popup=f"<b>GSP:</b> {gsp['gsp_name']}",
            tooltip=gsp['gsp_name'],
            color='#e74c3c',
            fillColor='#e74c3c',
            fillOpacity=0.8,
            weight=1
        ).add_to(gsp_group)
    
    gsp_group.add_to(m)
    
    # Add wind forecast info box
    forecast = get_wind_forecast_latest()
    if not forecast.empty:
        latest_forecast = forecast.iloc[0]['forecast_mw']
        
        forecast_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; 
                    background: white; 
                    padding: 10px; 
                    border: 2px solid #2ecc71;
                    border-radius: 5px;
                    z-index: 9999;
                    font-family: Arial;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
            <h4 style="margin: 0 0 5px 0; color: #2ecc71;">🌬️ Wind Forecast</h4>
            <p style="margin: 0; font-size: 18px;"><b>{latest_forecast:.0f} MW</b></p>
            <p style="margin: 0; font-size: 11px; color: #666;">Latest prediction</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(forecast_html))
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 60px; width: 400px; 
                background-color: white; 
                border: 2px solid #2ecc71; 
                border-radius: 5px;
                padding: 10px;
                z-index: 9999;
                font-family: Arial;">
        <h3 style="margin: 0; color: #2ecc71;">UK Wind Generation Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            Offshore + Onshore Wind Farms with GSP Connections
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save
    output_file = 'map_wind_capacity.html'
    m.save(output_file)
    print(f"   ✅ Saved: {output_file}")
    
    return output_file


def create_wind_summary_stats():
    """Create summary statistics for wind generation"""
    print("\n📊 Wind Generation Summary:")
    print("="*80)
    
    offshore = get_offshore_wind_farms()
    onshore = get_onshore_wind_farms()
    gsp_capacity = get_gsp_wind_capacity()
    forecast = get_wind_forecast_latest()
    
    print(f"\n🌊 OFFSHORE WIND:")
    print(f"   Farms: {len(offshore)}")
    print(f"   Capacity: {offshore['capacity_mw'].sum():,.0f} MW")
    print(f"   Turbines: {offshore['turbine_count'].sum():,.0f}")
    print(f"   Average farm size: {offshore['capacity_mw'].mean():,.0f} MW")
    print(f"   Largest: {offshore.iloc[0]['name']} ({offshore.iloc[0]['capacity_mw']:.0f} MW)")
    
    print(f"\n🌬️  ONSHORE WIND (>= 1 MW):")
    print(f"   Farms: {len(onshore)}")
    print(f"   Capacity: {onshore['capacity_mw'].sum():,.0f} MW")
    print(f"   Average farm size: {onshore['capacity_mw'].mean():,.0f} MW")
    print(f"   Largest: {onshore.iloc[0]['name']} ({onshore.iloc[0]['capacity_mw']:.0f} MW)")
    
    print(f"\n⚡ TOTAL WIND:")
    total_capacity = offshore['capacity_mw'].sum() + onshore['capacity_mw'].sum()
    print(f"   Combined capacity: {total_capacity:,.0f} MW")
    print(f"   Offshore share: {offshore['capacity_mw'].sum() / total_capacity * 100:.1f}%")
    print(f"   Onshore share: {onshore['capacity_mw'].sum() / total_capacity * 100:.1f}%")
    
    if not forecast.empty:
        print(f"\n🔮 WIND FORECAST:")
        print(f"   Latest prediction: {forecast.iloc[0]['forecast_mw']:,.0f} MW")
        print(f"   Capacity factor: {forecast.iloc[0]['forecast_mw'] / total_capacity * 100:.1f}%")
    
    print(f"\n📍 GSP ZONES WITH WIND:")
    print(f"   Number of GSP zones: {len(gsp_capacity)}")
    print(f"   Total BMU wind capacity: {gsp_capacity['wind_capacity_mw'].sum():,.0f} MW")
    
    print(f"\n🏆 TOP 5 GSP ZONES BY WIND CAPACITY:")
    for idx, row in gsp_capacity.head(5).iterrows():
        print(f"   {row['gsp_name']:30s} {row['wind_capacity_mw']:>8,.0f} MW ({row['num_wind_units']:>3.0f} units)")


# ============================================================================
# Main
# ============================================================================

def main():
    print("="*80)
    print("GB POWER MARKET - WIND FARM MAP GENERATOR")
    print("="*80)
    
    try:
        # Create summary stats
        create_wind_summary_stats()
        
        # Create main wind capacity map
        create_wind_capacity_map()
        
        print("\n✅ COMPLETE!")
        print("\nGenerated maps:")
        print("   • map_wind_capacity.html - Interactive map with all wind farms + GSP zones")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
