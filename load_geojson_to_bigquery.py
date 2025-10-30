#!/usr/bin/env python3
"""
Load GeoJSON files into BigQuery with GEOGRAPHY columns.
Handles DNO network boundaries, substations, or any geospatial data.
"""

import json
from google.cloud import bigquery
from datetime import datetime


def flatten_geojson_features(geojson_file):
    """
    Convert GeoJSON FeatureCollection to newline-delimited JSON
    with proper structure for BigQuery.
    """
    with open(geojson_file, 'r') as f:
        geojson = json.load(f)
    
    features = []
    
    if geojson.get('type') == 'FeatureCollection':
        for feature in geojson.get('features', []):
            # Extract geometry and properties
            row = {
                'geometry': json.dumps(feature.get('geometry')),  # Keep as JSON string
                'properties': feature.get('properties', {}),
                'feature_type': feature.get('type'),
            }
            
            # Flatten properties into top-level fields (optional)
            for key, value in feature.get('properties', {}).items():
                row[key] = value
            
            features.append(row)
    
    return features


def create_geography_table(client, dataset_id, table_id, schema):
    """
    Create a BigQuery table with GEOGRAPHY column.
    """
    table_ref = f"{client.project}.{dataset_id}.{table_id}"
    
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table, exists_ok=True)
    
    print(f"✓ Table created: {table_ref}")
    return table


def load_geojson_to_bigquery(
    geojson_file,
    project_id,
    dataset_id,
    table_id,
    description=None
):
    """
    Load GeoJSON file into BigQuery table with GEOGRAPHY column.
    
    Args:
        geojson_file: Path to .geojson file
        project_id: GCP project ID
        dataset_id: BigQuery dataset name
        table_id: BigQuery table name
        description: Optional table description
    """
    client = bigquery.Client(project=project_id)
    
    print(f"📁 Loading GeoJSON: {geojson_file}")
    
    # Read and flatten GeoJSON
    features = flatten_geojson_features(geojson_file)
    print(f"   Found {len(features)} features")
    
    # Define schema
    # Note: We'll store geometry as JSON string, then convert to GEOGRAPHY in query
    schema = [
        bigquery.SchemaField("geometry", "JSON", mode="REQUIRED", 
                            description="GeoJSON geometry object"),
        bigquery.SchemaField("properties", "JSON", mode="NULLABLE",
                            description="Feature properties"),
        bigquery.SchemaField("feature_type", "STRING", mode="NULLABLE"),
    ]
    
    # Add fields from properties (auto-detect from first feature)
    if features and features[0].get('properties'):
        for key, value in features[0]['properties'].items():
            # Determine type
            if isinstance(value, bool):
                field_type = "BOOLEAN"
            elif isinstance(value, int):
                field_type = "INTEGER"
            elif isinstance(value, float):
                field_type = "FLOAT"
            else:
                field_type = "STRING"
            
            schema.append(
                bigquery.SchemaField(key, field_type, mode="NULLABLE")
            )
    
    # Create table
    table = create_geography_table(client, dataset_id, table_id, schema)
    
    # Load data
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    job = client.load_table_from_json(
        features,
        table,
        job_config=job_config
    )
    
    job.result()  # Wait for completion
    
    print(f"✅ Loaded {len(features)} features to {table.table_id}")
    
    # Create view with proper GEOGRAPHY column
    view_id = f"{table_id}_geography"
    view_query = f"""
    SELECT
        * EXCEPT(geometry),
        ST_GEOGFROMGEOJSON(JSON_EXTRACT_SCALAR(geometry, '$')) AS geography
    FROM `{project_id}.{dataset_id}.{table_id}`
    """
    
    view = bigquery.Table(f"{project_id}.{dataset_id}.{view_id}")
    view.view_query = view_query
    view = client.create_table(view, exists_ok=True)
    
    print(f"✅ Created geography view: {view_id}")
    print(f"   Use this for geospatial queries!")
    
    return table, view


def example_dno_boundaries():
    """
    Example: Load DNO service area boundaries into BigQuery.
    """
    # Assuming you have DNO boundary GeoJSON files
    dno_files = {
        'UKPN': 'dno_boundaries/ukpn_service_area.geojson',
        'SSEN': 'dno_boundaries/ssen_service_area.geojson',
        'ENWL': 'dno_boundaries/enwl_service_area.geojson',
        'NPg': 'dno_boundaries/npg_service_area.geojson',
        'SPEN': 'dno_boundaries/spen_service_area.geojson',
        'NGED': 'dno_boundaries/nged_service_area.geojson',
    }
    
    client = bigquery.Client()
    project_id = client.project
    dataset_id = 'uk_energy_data'
    
    for dno, filepath in dno_files.items():
        try:
            table_id = f"dno_boundaries_{dno.lower()}"
            load_geojson_to_bigquery(
                filepath,
                project_id,
                dataset_id,
                table_id,
                description=f"{dno} distribution network service area boundaries"
            )
        except FileNotFoundError:
            print(f"⚠️  File not found: {filepath}")
        except Exception as e:
            print(f"❌ Error loading {dno}: {e}")


def example_query_geography():
    """
    Example queries using GEOGRAPHY data in BigQuery.
    """
    queries = {
        "Find DNO for a location": """
        SELECT dno_name
        FROM `project.dataset.dno_boundaries_geography`
        WHERE ST_CONTAINS(
            geography,
            ST_GEOGPOINT(-0.1278, 51.5074)  -- London coordinates
        )
        """,
        
        "Calculate service area size": """
        SELECT 
            dno_name,
            ST_AREA(geography) / 1000000 AS area_km2
        FROM `project.dataset.dno_boundaries_geography`
        ORDER BY area_km2 DESC
        """,
        
        "Find substations in DNO area": """
        SELECT s.*, d.dno_name
        FROM `project.dataset.substations` s
        JOIN `project.dataset.dno_boundaries_geography` d
        ON ST_CONTAINS(d.geography, s.location)
        """,
        
        "Distance to nearest substation": """
        SELECT 
            customer_location,
            MIN(ST_DISTANCE(customer_location, substation_location)) AS nearest_distance_m
        FROM `project.dataset.customers`
        CROSS JOIN `project.dataset.substations`
        GROUP BY customer_location
        """,
    }
    
    for description, query in queries.items():
        print(f"\n{description}:")
        print(query)


if __name__ == "__main__":
    print("="*60)
    print("BigQuery GeoJSON Loader")
    print("="*60)
    
    # Example usage
    print("\n📝 Usage Examples:\n")
    
    print("1. Load single GeoJSON file:")
    print("""
    load_geojson_to_bigquery(
        'data/dno_boundaries.geojson',
        'your-project-id',
        'uk_energy_data',
        'dno_boundaries'
    )
    """)
    
    print("\n2. Load multiple DNO boundaries:")
    print("   See example_dno_boundaries() function")
    
    print("\n3. Query geography data:")
    example_query_geography()
    
    print("\n" + "="*60)
    print("For DNO network data, consider loading:")
    print("  • Service area boundaries (polygons)")
    print("  • Substation locations (points)")
    print("  • Transmission line routes (linestrings)")
    print("  • Grid supply point areas (polygons)")
    print("="*60)
