#!/usr/bin/env python3
"""
create_btm_constraint_map.py

Creates an interactive Folium map showing:
- BtM site locations (from CSV with geocoded postcodes)
- DNO boundary polygons
- DNO constraint cost heatmap
- NESO constraint boundaries

Outputs: btm_constraint_map.html (interactive HTML map)

Usage:
    python3 create_btm_constraint_map.py
    python3 create_btm_constraint_map.py --sites btm_sites.csv --constraints dno_constraints.geojson
    python3 create_btm_constraint_map.py --output custom_map.html

Requirements:
    pip3 install --user pandas geopandas folium shapely
"""

import argparse
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import json

# ===== CONFIGURATION =====
DEFAULT_CENTER = [54.5, -3.5]  # UK center
DEFAULT_ZOOM = 6


def load_btm_sites(csv_path):
    """
    Load BtM sites from CSV.

    Returns DataFrame with columns: asset_id, asset_name, location, dno, latitude, longitude
    """

    print(f"\n📍 Loading BtM sites from {csv_path}...")

    df = pd.read_csv(csv_path)

    # Filter to valid coordinates
    valid = df.dropna(subset=['latitude', 'longitude'])

    print(f"   ✅ Loaded {len(valid)} valid sites (out of {len(df)} total)")

    if len(valid) < len(df):
        invalid_count = len(df) - len(valid)
        print(f"   ⚠️ Skipped {invalid_count} sites with missing coordinates")

    return valid


def load_constraint_geojson(geojson_path):
    """
    Load DNO constraint GeoJSON.

    Returns GeoDataFrame.
    """

    print(f"\n🗺️  Loading DNO constraints from {geojson_path}...")

    gdf = gpd.read_file(geojson_path)

    print(f"   ✅ Loaded {len(gdf)} DNO regions")
    if 'total_cost' in gdf.columns:
        print(f"   📊 Total constraint cost: £{gdf['total_cost'].sum():,.0f}")

    return gdf


def create_base_map(center=DEFAULT_CENTER, zoom=DEFAULT_ZOOM):
    """
    Create base Folium map.

    Returns folium.Map object.
    """

    print(f"\n🗺️  Creating base map (center: {center}, zoom: {zoom})...")

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='OpenStreetMap',
        control_scale=True
    )

    # Add alternative tile layers
    folium.TileLayer('CartoDB positron', name='Light Theme').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Theme').add_to(m)

    return m


def add_dno_boundaries(m, gdf):
    """
    Add DNO boundary polygons to map with constraint cost choropleth.

    Args:
        m: folium.Map object
        gdf: GeoDataFrame with DNO boundaries and constraint data
    """

    print("\n🎨 Adding DNO constraint choropleth...")

    # Prepare data for choropleth (needs DataFrame, not GeoDataFrame)
    choropleth_data = gdf[['dno_code', 'total_cost']].copy()
    choropleth_data = choropleth_data.drop_duplicates('dno_code')

    # Create choropleth layer
    folium.Choropleth(
        geo_data=gdf.to_json(),
        name='DNO Constraint Costs',
        data=choropleth_data,
        columns=['dno_code', 'total_cost'],
        key_on='feature.properties.dno_code',
        fill_color='YlOrRd',
        fill_opacity=0.6,
        line_opacity=0.8,
        legend_name='Total Constraint Cost (£)',
        highlight=True
    ).add_to(m)

    # Add tooltips with detailed info
    style_function = lambda x: {
        'fillColor': '#ffffff00',  # Transparent fill (choropleth handles color)
        'color': '#000000',
        'weight': 2,
        'fillOpacity': 0
    }

    highlight_function = lambda x: {
        'fillColor': '#00000000',
        'color': '#0000ff',
        'weight': 3,
        'fillOpacity': 0
    }

    # Add GeoJson layer with tooltips
    tooltip_layer = folium.GeoJson(
        gdf,
        name='DNO Details',
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['dno_code', 'dno_full_name', 'constraint_events', 'total_cost', 'avg_cost'],
            aliases=['DNO:', 'Code:', 'Events:', 'Total Cost (£):', 'Avg Cost (£):'],
            localize=True,
            sticky=True,
            labels=True,
            style="""
                background-color: white;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px 3px 3px rgba(0,0,0,0.5);
                padding: 10px;
            """
        )
    )

    tooltip_layer.add_to(m)

    print(f"   ✅ Added {len(gdf)} DNO regions with constraint data")


def add_btm_sites(m, df):
    """
    Add BtM site markers to map.

    Args:
        m: folium.Map object
        df: DataFrame with site locations
    """

    print("\n📍 Adding BtM site markers...")

    # Create marker cluster for better performance with many sites
    marker_cluster = plugins.MarkerCluster(name='BtM Sites').add_to(m)

    for _, row in df.iterrows():
        # Create popup content with BESS-specific fields
        popup_html = f"""
        <div style="font-family: Arial; width: 220px;">
            <h4 style="margin: 0 0 10px 0; color: #d32f2f;">⚡ {row['asset_name']}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><b>Asset ID:</b></td><td>{row['asset_id']}</td></tr>
        """

        if 'p_max_mw' in row and pd.notna(row['p_max_mw']):
            popup_html += f"<tr><td><b>Power:</b></td><td>{row['p_max_mw']} MW</td></tr>"

        if 'e_max_mwh' in row and pd.notna(row['e_max_mwh']):
            popup_html += f"<tr><td><b>Energy:</b></td><td>{row['e_max_mwh']} MWh</td></tr>"

        if 'dno' in row and pd.notna(row['dno']):
            popup_html += f"<tr><td><b>DNO:</b></td><td>{row['dno']}</td></tr>"

        if 'location' in row and pd.notna(row['location']):
            popup_html += f"<tr><td><b>Location:</b></td><td>{row['location']}</td></tr>"

        popup_html += f"""
                <tr><td><b>Coordinates:</b></td><td>{row['latitude']:.4f}, {row['longitude']:.4f}</td></tr>
        """

        if 'geocode_method' in row and pd.notna(row['geocode_method']):
            method_label = "📍 Exact" if row['geocode_method'] == 'postcode' else "📌 Approx"
            popup_html += f"<tr><td><b>Geocode:</b></td><td>{method_label}</td></tr>"

        popup_html += """
            </table>
        </div>
        """

        # Add marker
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=row['asset_name'],
            icon=folium.Icon(color='red', icon='bolt', prefix='fa')
        ).add_to(marker_cluster)

    print(f"   ✅ Added {len(df)} BtM site markers")


def add_legend(m):
    """Add custom legend to map."""

    legend_html = """
    <div style="position: fixed;
                bottom: 50px; right: 50px; width: 250px; height: auto;
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
    <h4 style="margin-top: 0;">GB Power Market - Constraint Map</h4>
    <p style="margin: 5px 0;"><i class="fa fa-bolt" style="color:red"></i> BtM Sites</p>
    <p style="margin: 5px 0;">
        <span style="background-color: #ffffcc; padding: 2px 10px; border: 1px solid #ccc;">Low</span>
        <span style="background-color: #ffeda0; padding: 2px 10px; border: 1px solid #ccc;">Medium</span>
        <span style="background-color: #fd8d3c; padding: 2px 10px; border: 1px solid #ccc;">High</span>
        <span style="background-color: #bd0026; color: white; padding: 2px 10px; border: 1px solid #ccc;">Very High</span>
    </p>
    <p style="margin: 5px 0; font-size: 12px;">DNO Constraint Costs (2017-2025)</p>
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))


def create_constraint_map(sites_csv, constraints_geojson, output_html):
    """
    Main function to create constraint map.

    Args:
        sites_csv: Path to BtM sites CSV
        constraints_geojson: Path to DNO constraints GeoJSON
        output_html: Output HTML file path
    """

    print("=" * 70)
    print("🗺️  CREATING BTM CONSTRAINT MAP")
    print("=" * 70)

    # Load data
    sites_df = load_btm_sites(sites_csv)
    constraints_gdf = load_constraint_geojson(constraints_geojson)

    # Calculate map center from sites
    if not sites_df.empty:
        center_lat = sites_df['latitude'].mean()
        center_lon = sites_df['longitude'].mean()
        center = [center_lat, center_lon]
        print(f"\n📍 Map center calculated from sites: {center}")
    else:
        center = DEFAULT_CENTER
        print(f"\n📍 Using default UK center: {center}")

    # Create map
    m = create_base_map(center=center, zoom=DEFAULT_ZOOM)

    # Add layers
    add_dno_boundaries(m, constraints_gdf)

    if not sites_df.empty:
        add_btm_sites(m, sites_df)
    else:
        print("\n⚠️ No valid BtM sites to display")

    # Add legend
    add_legend(m)

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # Add fullscreen button
    plugins.Fullscreen(
        position='topright',
        title='Enter fullscreen',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(m)

    # Save map
    print(f"\n💾 Saving map to {output_html}...")
    m.save(output_html)

    # Show file size
    import os
    file_size = os.path.getsize(output_html)
    print(f"   ✅ Saved interactive map ({file_size / 1024:.1f} KB)")

    print("\n✅ Map creation complete!")
    print(f"   Open in browser: file://{os.path.abspath(output_html)}")
    print(f"   Or run: xdg-open {output_html}")


def main():
    parser = argparse.ArgumentParser(description='Create BtM constraint map')
    parser.add_argument('--sites', default='btm_sites.csv',
                       help='BtM sites CSV file (default: btm_sites.csv)')
    parser.add_argument('--constraints', default='dno_constraints.geojson',
                       help='DNO constraints GeoJSON file (default: dno_constraints.geojson)')
    parser.add_argument('--output', default='btm_constraint_map.html',
                       help='Output HTML file (default: btm_constraint_map.html)')
    args = parser.parse_args()

    create_constraint_map(
        sites_csv=args.sites,
        constraints_geojson=args.constraints,
        output_html=args.output
    )


if __name__ == "__main__":
    main()
