#!/usr/bin/env python3
"""
create_constraint_geojson.py

Creates constraint GeoJSON by joining constraint_costs_by_dno with neso_dno_boundaries.
Outputs GeoJSON file with DNO polygons colored by constraint cost/volume.

Outputs: dno_constraints.geojson

Usage:
    python3 create_constraint_geojson.py
    python3 create_constraint_geojson.py --output dno_constraints_custom.geojson
    python3 create_constraint_geojson.py --start-date 2024-01-01 --end-date 2025-12-31

Requirements:
    pip3 install --user google-cloud-bigquery pandas geopandas shapely
"""

import argparse
import json
from google.cloud import bigquery
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape

# ===== CONFIGURATION =====
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"


def fetch_dno_boundaries():
    """
    Fetch DNO boundary GeoJSON from BigQuery.

    Returns GeoDataFrame with DNO polygons.
    """

    print("\n📍 Fetching DNO boundaries from BigQuery...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT
        dno_code,
        ST_ASGEOJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    """

    df = client.query(query).to_dataframe()

    print(f"   ✅ Retrieved {len(df)} DNO boundaries")

    # Convert GeoJSON strings to shapely geometries
    geometries = []
    for geojson_str in df['geojson']:
        geom_dict = json.loads(geojson_str)
        geometries.append(shape(geom_dict))

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df[['dno_code']],
        geometry=geometries,
        crs="EPSG:4326"
    )

    return gdf


def fetch_constraint_costs(start_date=None, end_date=None):
    """
    Fetch DNO constraint costs from BigQuery.

    Returns DataFrame with aggregated costs/volumes by DNO.
    """

    print("\n💰 Fetching constraint costs from BigQuery...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Build date filter
    date_filter = ""
    if start_date and end_date:
        date_filter = f"WHERE constraint_date BETWEEN '{start_date}' AND '{end_date}'"
        print(f"   📅 Date range: {start_date} to {end_date}")

    query = f"""
    SELECT
        dno_id as dno_code,
        COUNT(*) as constraint_events,
        SUM(constraint_cost_gbp) as total_cost_gbp,
        AVG(constraint_cost_gbp) as avg_cost_gbp,
        SUM(constraint_volume_mw) as total_volume_mw,
        AVG(constraint_volume_mw) as avg_volume_mw,
        MIN(constraint_date) as earliest_date,
        MAX(constraint_date) as latest_date
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`
    {date_filter}
    GROUP BY dno_id
    ORDER BY total_cost_gbp DESC
    """

    df = client.query(query).to_dataframe()

    print(f"   ✅ Retrieved {len(df)} DNO constraint records")
    print(f"\n   📊 Top 5 constrained DNOs by cost:")
    for i, row in df.head(5).iterrows():
        print(f"      {i+1}. {row['dno_code']}: £{row['total_cost_gbp']:,.0f} ({row['constraint_events']} events)")

    return df


def merge_constraints_with_boundaries(boundaries_gdf, constraints_df):
    """
    Merge constraint costs with DNO boundaries.

    Returns GeoDataFrame with constraints data.
    """

    print("\n🔗 Merging constraints with boundaries...")

    # Merge on dno_code
    merged_gdf = boundaries_gdf.merge(
        constraints_df,
        on='dno_code',
        how='left',
        suffixes=('_boundary', '_constraint')
    )

    # Fill NaN values for DNOs with no constraint data
    merged_gdf['constraint_events'] = merged_gdf['constraint_events'].fillna(0).astype(int)
    merged_gdf['total_cost_gbp'] = merged_gdf['total_cost_gbp'].fillna(0)
    merged_gdf['avg_cost_gbp'] = merged_gdf['avg_cost_gbp'].fillna(0)
    merged_gdf['total_volume_mw'] = merged_gdf['total_volume_mw'].fillna(0)
    merged_gdf['avg_volume_mw'] = merged_gdf['avg_volume_mw'].fillna(0)

    # Use dno_name from boundaries (more reliable)
    if 'dno_name_boundary' in merged_gdf.columns:
        merged_gdf['dno_name'] = merged_gdf['dno_name_boundary']
        merged_gdf = merged_gdf.drop(columns=['dno_name_boundary', 'dno_name_constraint'])

    print(f"   ✅ Merged {len(merged_gdf)} DNO regions")

    # Show DNOs with no constraint data
    no_data = merged_gdf[merged_gdf['constraint_events'] == 0]
    if len(no_data) > 0:
        print(f"\n   ⚠️ {len(no_data)} DNOs with no constraint data:")
        for _, row in no_data.iterrows():
            print(f"      - {row['dno_name']} ({row['dno_code']})")

    return merged_gdf


def save_geojson(gdf, output_path):
    """Save GeoDataFrame to GeoJSON file."""

    print(f"\n💾 Saving to {output_path}...")

    # Convert datetime columns to strings (GeoJSON doesn't support datetime)
    for col in gdf.columns:
        if pd.api.types.is_datetime64_any_dtype(gdf[col]):
            gdf[col] = gdf[col].astype(str)

    gdf.to_file(output_path, driver='GeoJSON')

    print(f"   ✅ Saved {len(gdf)} features")

    # Show file size
    import os
    file_size = os.path.getsize(output_path)
    print(f"   📦 File size: {file_size / 1024:.1f} KB")


def main():
    parser = argparse.ArgumentParser(description='Create constraint GeoJSON from BigQuery')
    parser.add_argument('--output', default='dno_constraints.geojson',
                       help='Output GeoJSON file path (default: dno_constraints.geojson)')
    parser.add_argument('--start-date', default=None,
                       help='Start date for constraint data (YYYY-MM-DD)')
    parser.add_argument('--end-date', default=None,
                       help='End date for constraint data (YYYY-MM-DD)')
    args = parser.parse_args()

    print("=" * 70)
    print("🗺️  CREATE DNO CONSTRAINT GEOJSON")
    print("=" * 70)

    # Step 1: Fetch DNO boundaries
    boundaries_gdf = fetch_dno_boundaries()

    # Step 2: Fetch constraint costs
    constraints_df = fetch_constraint_costs(
        start_date=args.start_date,
        end_date=args.end_date
    )

    # Step 3: Merge
    merged_gdf = merge_constraints_with_boundaries(boundaries_gdf, constraints_df)

    # Step 4: Save to GeoJSON
    save_geojson(merged_gdf, args.output)

    print("\n✅ Constraint GeoJSON created successfully!")
    print(f"   Next step: python3 create_btm_constraint_map.py")


if __name__ == "__main__":
    main()
