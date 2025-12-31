#!/usr/bin/env python3
"""
Interactive Constraint Map with Date Ranges and Full Details
Shows DNO boundaries with constraint costs, date ranges, and site overlay
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from google.cloud import bigquery
import os
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Setup BigQuery
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

print("📊 Fetching constraint data with date ranges from BigQuery...")

# Query: Get constraint costs by DNO with date range info
query = f"""
WITH monthly_costs AS (
    SELECT
        dno_full_name,
        area_name,
        year,
        month,
        SUM(allocated_total_cost) as monthly_cost,
        SUM(allocated_voltage_cost) as voltage_cost,
        SUM(allocated_thermal_cost) as thermal_cost,
        SUM(allocated_inertia_cost) as inertia_cost
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`
    GROUP BY dno_full_name, area_name, year, month
),
dno_summary AS (
    SELECT
        dno_full_name,
        area_name,
        MIN(CONCAT(year, '-', LPAD(CAST(month AS STRING), 2, '0'))) as start_date,
        MAX(CONCAT(year, '-', LPAD(CAST(month AS STRING), 2, '0'))) as end_date,
        COUNT(DISTINCT CONCAT(year, month)) as num_months,
        ROUND(SUM(monthly_cost) / 1000000, 2) as total_cost_millions,
        ROUND(AVG(monthly_cost) / 1000000, 2) as avg_monthly_cost_millions,
        ROUND(SUM(voltage_cost) / 1000000, 2) as voltage_cost_millions,
        ROUND(SUM(thermal_cost) / 1000000, 2) as thermal_cost_millions,
        ROUND(SUM(inertia_cost) / 1000000, 2) as inertia_cost_millions
    FROM monthly_costs
    GROUP BY dno_full_name, area_name
)
SELECT * FROM dno_summary
ORDER BY total_cost_millions DESC
"""

df_costs = bq_client.query(query).to_dataframe()
print(f"✅ Retrieved {len(df_costs)} DNO regions with constraint data\n")

# Display summary
print("📊 Constraint Cost Summary:")
print(f"{'DNO Region':<40} {'Date Range':<20} {'Total (£M)':<12} {'Avg/Month (£M)':<15}")
print("=" * 90)
for _, row in df_costs.iterrows():
    print(f"{row['area_name']:<40} {row['start_date']} to {row['end_date']:<8} £{row['total_cost_millions']:>10,.2f} £{row['avg_monthly_cost_millions']:>13,.2f}")

# Fetch DNO boundaries geometry
print(f"\n🗺️ Fetching DNO boundary geometries...")
query_geo = f"""
SELECT
    dno_id,
    dno_full_name,
    area_name,
    area_sq_km,
    ST_ASGEOJSON(boundary_geometry) as geometry_json
FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
"""
df_geo = bq_client.query(query_geo).to_dataframe()

# Parse geometry and create GeoDataFrame
from shapely import wkt
import json

geometries = []
for geom_json in df_geo['geometry_json']:
    geom_dict = json.loads(geom_json)
    geometries.append(gpd.GeoDataFrame.from_features([{"type": "Feature", "geometry": geom_dict}]).geometry[0])

gdf_boundaries = gpd.GeoDataFrame(df_geo.drop(columns=['geometry_json']), geometry=geometries, crs="EPSG:4326")

# Merge constraint costs with boundaries
gdf_full = gdf_boundaries.merge(df_costs, on=['dno_full_name', 'area_name'], how='left')

print(f"✅ Loaded {len(gdf_full)} DNO boundaries with constraint data")

# Create interactive Folium map
print(f"\n🗺️ Building interactive map...")

# Calculate center of UK (approximately)
center_lat = 54.5
center_lon = -3.5

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=6,  # Zoomed in to UK
    tiles="CartoDB positron"
)

# Color scale based on total constraint costs
max_cost = df_costs['total_cost_millions'].max()
min_cost = df_costs['total_cost_millions'].min()

def get_color(cost):
    """Return color based on constraint cost (red = high, yellow = medium, green = low)"""
    if pd.isna(cost):
        return '#cccccc'
    normalized = (cost - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
    if normalized > 0.66:
        return '#d73027'  # Red
    elif normalized > 0.33:
        return '#fee08b'  # Yellow
    else:
        return '#1a9850'  # Green

# Add DNO polygons with constraint data
for _, row in gdf_full.iterrows():
    # Build detailed popup
    popup_html = f"""
    <div style="font-family: Arial; width: 350px;">
        <h4 style="margin: 0 0 10px 0;">{row['area_name']}</h4>
        <table style="width: 100%; font-size: 12px;">
            <tr><td><b>DNO:</b></td><td>{row['dno_full_name']}</td></tr>
            <tr><td><b>Area:</b></td><td>{row['area_sq_km']:.0f} km²</td></tr>
            <tr><td colspan="2"><hr style="margin: 5px 0;"></td></tr>
            <tr><td><b>Date Range:</b></td><td>{row['start_date']} to {row['end_date']}</td></tr>
            <tr><td><b>Months:</b></td><td>{row['num_months']:.0f} months</td></tr>
            <tr><td colspan="2"><hr style="margin: 5px 0;"></td></tr>
            <tr><td><b>Total Cost:</b></td><td><b>£{row['total_cost_millions']:,.2f}M</b></td></tr>
            <tr><td><b>Avg/Month:</b></td><td>£{row['avg_monthly_cost_millions']:,.2f}M</td></tr>
            <tr><td colspan="2"><hr style="margin: 5px 0;"></td></tr>
            <tr><td><b>Voltage:</b></td><td>£{row['voltage_cost_millions']:,.2f}M</td></tr>
            <tr><td><b>Thermal:</b></td><td>£{row['thermal_cost_millions']:,.2f}M</td></tr>
            <tr><td><b>Inertia:</b></td><td>£{row['inertia_cost_millions']:,.2f}M</td></tr>
        </table>
    </div>
    """

    folium.GeoJson(
        row['geometry'].__geo_interface__,
        style_function=lambda feature, cost=row['total_cost_millions']: {
            'fillColor': get_color(cost),
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.6
        },
        tooltip=f"{row['area_name']}: £{row['total_cost_millions']:,.2f}M",
        popup=folium.Popup(popup_html, max_width=400)
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed;
            bottom: 50px; right: 50px; width: 200px; height: 150px;
            background-color: white; border:2px solid grey; z-index:9999;
            font-size:14px; padding: 10px">
<p style="margin: 0 0 10px 0;"><b>Constraint Costs (£M)</b></p>
<p style="margin: 5px 0;"><i style="background:#d73027; width: 20px; height: 10px; display: inline-block;"></i> High (£{max_cost:.0f}M)</p>
<p style="margin: 5px 0;"><i style="background:#fee08b; width: 20px; height: 10px; display: inline-block;"></i> Medium</p>
<p style="margin: 5px 0;"><i style="background:#1a9850; width: 20px; height: 10px; display: inline-block;"></i> Low (£{min_cost:.0f}M)</p>
<p style="margin: 10px 0 0 0; font-size: 11px;">Click regions for details</p>
</div>
'''.format(max_cost=max_cost, min_cost=min_cost)

m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_file = "constraint_costs_detailed_map.html"
m.save(output_file)

print(f"\n✅ Map saved: {output_file}")
print(f"\n📍 Features:")
print(f"   - Color-coded by constraint cost (red=high, green=low)")
print(f"   - Click any region to see:")
print(f"     • Date range ({df_costs['start_date'].min()} to {df_costs['end_date'].max()})")
print(f"     • Total costs and monthly averages")
print(f"     • Breakdown by type (voltage/thermal/inertia)")
print(f"   - Hover for quick cost preview")
print(f"   - Zoomed to UK (latitude: {center_lat}, longitude: {center_lon})")

print(f"\n🌐 Open in browser:")
print(f"   file://{os.path.abspath(output_file)}")
print(f"   OR")
print(f"   http://localhost:8080/{output_file}")
