#!/usr/bin/env python3
"""
create_constraint_geojson_simple.py

Simplified version: Check constraint_costs_by_dno schema first,
then create GeoJSON with DNO boundaries.
"""

import json
from google.cloud import bigquery
import geopandas as gpd
from shapely.geometry import shape

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
OUTPUT_FILE = "dno_constraints.geojson"

def check_table_schema():
    """Check actual schema of constraint table"""
    print("\n🔍 Checking constraint_costs_by_dno schema...")
    client = bigquery.Client(project=PROJECT_ID, location="US")

    table = client.get_table(f"{PROJECT_ID}.{DATASET}.constraint_costs_by_dno")
    print(f"   Schema ({table.num_rows:,} rows):")
    for field in table.schema:
        print(f"      {field.name:30} {field.field_type}")

    # Sample 1 row
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno` LIMIT 1"
    result = list(client.query(query).result())
    if result:
        print(f"\n   Sample row:")
        for k, v in result[0].items():
            print(f"      {k}: {v}")

    return [f.name for f in table.schema]


def fetch_dno_boundaries():
    """Fetch DNO boundaries from BigQuery"""
    print("\n📍 Fetching DNO boundaries...")
    client = bigquery.Client(project=PROJECT_ID, location="US")

    # First check what fields exist
    table = client.get_table(f"{PROJECT_ID}.{DATASET}.neso_dno_boundaries")
    field_names = [f.name for f in table.schema]
    print(f"   Available fields: {', '.join(field_names)}")

    # Build query - get ALL fields to see what we have
    query = f"""
    SELECT
        *,
        ST_ASGEOJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    LIMIT 1
    """

    sample = list(client.query(query).result())[0]
    print(f"   Sample boundary row:")
    for k, v in sample.items():
        if k != 'geojson' and k != 'boundary':
            print(f"      {k}: {v}")

    # Now fetch all boundaries
    query = f"""
    SELECT
        *,
        ST_ASGEOJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    """

    df = client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} DNO boundaries")

    # Convert to GeoDataFrame
    geometries = []
    for geojson_str in df['geojson']:
        geom_dict = json.loads(geojson_str)
        geometries.append(shape(geom_dict))

    # Keep all columns except geojson and boundary
    data_cols = [c for c in df.columns if c not in ['geojson', 'boundary']]
    gdf = gpd.GeoDataFrame(
        df[data_cols],
        geometry=geometries,
        crs="EPSG:4326"
    )

    return gdf


def fetch_constraint_summary(field_names):
    """Fetch constraint summary using actual field names"""
    print("\n💰 Fetching constraint summary...")
    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Build query based on actual fields
    if 'dno_id' in field_names:
        dno_field = 'dno_id'
    elif 'dno_code' in field_names:
        dno_field = 'dno_code'
    else:
        print("   ❌ No DNO identifier field found!")
        return None

    # Check for cost/volume fields
    cost_field = None
    volume_field = None

    for name in field_names:
        if 'cost' in name.lower():
            cost_field = name
        if 'volume' in name.lower() or 'mw' in name.lower():
            volume_field = name

    print(f"   Using fields: {dno_field}, {cost_field}, {volume_field}")

    # Build query
    select_parts = [f"{dno_field} as dno_code", "COUNT(*) as constraint_events"]

    if cost_field:
        select_parts.append(f"SUM({cost_field}) as total_cost")
        select_parts.append(f"AVG({cost_field}) as avg_cost")

    if volume_field:
        select_parts.append(f"SUM({volume_field}) as total_volume")
        select_parts.append(f"AVG({volume_field}) as avg_volume")

    query = f"""
    SELECT
        {', '.join(select_parts)}
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`
    GROUP BY {dno_field}
    ORDER BY total_cost DESC
    """

    df = client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} DNO constraint summaries")

    return df


def main():
    print("🗺️  CREATE DNO CONSTRAINT GEOJSON (Simple)")
    print("=" * 60)

    # Step 1: Check schema
    field_names = check_table_schema()

    # Step 2: Get boundaries
    boundaries_gdf = fetch_dno_boundaries()

    # Step 3: Get constraints
    constraints_df = fetch_constraint_summary(field_names)

    if constraints_df is None:
        print("\n❌ Cannot proceed without constraint data")
        return

    # Step 4: Merge
    print("\n🔗 Merging boundaries with constraint costs...")

    # Find common join key
    boundary_cols = set(boundaries_gdf.columns)
    constraint_cols = set(constraints_df.columns)

    print(f"   Boundary columns: {boundary_cols}")
    print(f"   Constraint columns: {constraint_cols}")

    # Look for dno_id in boundaries
    if 'dno_id' in boundaries_gdf.columns and 'dno_code' in constraints_df.columns:
        print(f"   Joining on dno_id (boundaries) = dno_code (constraints)")
        # Rename constraint dno_code to match merge
        constraints_df = constraints_df.rename(columns={'dno_code': 'dno_id'})
        merged_gdf = boundaries_gdf.merge(
            constraints_df,
            on='dno_id',
            how='left'
        )
    else:
        print(f"   ⚠️ No clear join key, using left join without matching")
        merged_gdf = boundaries_gdf

    # Fill nulls
    merged_gdf = merged_gdf.fillna(0)

    print(f"   ✅ Merged {len(merged_gdf)} DNO regions")

    # Step 5: Save
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    merged_gdf.to_file(OUTPUT_FILE, driver='GeoJSON')

    print("\n" + "=" * 60)
    print(f"✅ Complete! Output: {OUTPUT_FILE}")
    print(f"   Next: python3 create_btm_constraint_map.py")


if __name__ == "__main__":
    main()
