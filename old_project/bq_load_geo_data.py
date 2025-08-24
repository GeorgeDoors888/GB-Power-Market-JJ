#!/usr/bin/env python3
"""
BigQuery GeoJSON Data Loader

This script loads GeoJSON data into BigQuery for geographic visualizations
in the energy dashboard.
"""

import os
import json
import argparse
import logging
from google.cloud import bigquery, storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bq_geo_loader')

# Default settings
DEFAULT_PROJECT = 'jibber-jabber-knowledge'
DEFAULT_DATASET = 'uk_energy_prod'
DEFAULT_GCS_BUCKET = 'jibber-jabber-knowledge-data'
GCS_GEO_PREFIX = 'geo/'

# Mapping of GeoJSON files to BigQuery tables
GEO_MAPPING = {
    # DNO License Areas
    'dno_license_areas_20200506_simplified.geojson': {
        'table': 'neso_dno_licence_areas',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'owner', 'dno']
    },
    'gb-dno-license-areas-20240503-as-geojson_simplified.geojson': {
        'table': 'neso_dno_licence_areas_2024',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'owner', 'dno']
    },
    
    # Generation Charging Zones
    'tnuosgenzones_geojs_simplified.geojson': {
        'table': 'neso_generation_charging_zones',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'zone_number', 'zone']
    },
    
    # Grid Supply Points
    'gsp_regions_20181031_simplified.geojson': {
        'table': 'neso_grid_supply_points_2018',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'gsp_group', '_gsp_group_id']
    },
    'gsp_regions_20220314_simplified.geojson': {
        'table': 'neso_grid_supply_points_2022',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'gsp_group', '_gsp_group_id']
    },
    'GSP_regions_27700_20250102_simplified.geojson': {
        'table': 'neso_grid_supply_points_2025_jan',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'gsp_group', 'gsp_id']
    },
    'GSP_regions_4326_20250102_simplified.geojson': {
        'table': 'neso_grid_supply_points_2025_jan_wgs84',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'gsp_group', 'gsp_id']
    },
    'GSP_regions_27700_20250109_simplified.geojson': {
        'table': 'neso_grid_supply_points_2025_latest',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'gsp_group', 'gsp_id']
    },
    'GSP_regions_4326_20250109_simplified.geojson': {
        'table': 'neso_grid_supply_points_2025_latest_wgs84',
        'geometry_column': 'geometry',
        'properties_columns': ['name', 'id', 'gsp_group', 'gsp_id']
    }
}

def load_geojson_to_bigquery(geojson_file, project_id, dataset_id, file_mapping=None):
    """Load a GeoJSON file into BigQuery."""
    file_basename = os.path.basename(geojson_file)
    
    if not file_mapping:
        # Use predefined mapping
        if file_basename not in GEO_MAPPING:
            logger.error(f"No mapping defined for {file_basename}")
            return False
        
        mapping = GEO_MAPPING[file_basename]
    else:
        mapping = file_mapping
        
    table_id = f"{project_id}.{dataset_id}.{mapping['table']}"
    
    # Load GeoJSON file
    try:
        with open(geojson_file, 'r') as f:
            geojson_data = json.load(f)
    except Exception as e:
        logger.error(f"Error reading GeoJSON file {geojson_file}: {str(e)}")
        return False
    
    # Check if it's a valid GeoJSON
    if 'type' not in geojson_data or 'features' not in geojson_data:
        logger.error(f"Invalid GeoJSON format in {geojson_file}")
        return False
    
    # Transform to BigQuery rows
    rows = []
    for feature in geojson_data.get('features', []):
        properties = feature.get('properties', {})
        geometry = feature.get('geometry')
        
        if not geometry:
            logger.warning(f"Feature without geometry in {geojson_file}")
            continue
        
        row = {
            mapping['geometry_column']: json.dumps(geometry)
        }
        
        # Add properties
        for prop in mapping['properties_columns']:
            if prop in properties:
                row[prop] = properties.get(prop)
            else:
                row[prop] = None
        
        rows.append(row)
    
    if not rows:
        logger.warning(f"No valid features found in {geojson_file}")
        return False
    
    # Load data to BigQuery
    client = bigquery.Client(project=project_id)
    
    # Check if table exists, create if not with proper schema
    try:
        client.get_table(table_id)
        logger.info(f"Table {table_id} already exists")
    except Exception:
        logger.info(f"Creating table {table_id}")
        
        # Generate schema from the first row
        schema = [
            bigquery.SchemaField(mapping['geometry_column'], "STRING", mode="REQUIRED"),
        ]
        
        for prop in mapping['properties_columns']:
            schema.append(bigquery.SchemaField(prop, "STRING"))
        
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
    
    # Load data
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.autodetect = False
    
    # First delete existing data
    delete_query = f"DELETE FROM `{table_id}` WHERE 1=1"
    client.query(delete_query).result()
    logger.info(f"Deleted existing data from {table_id}")
    
    # Convert rows to newline-delimited JSON
    json_data = "\n".join([json.dumps(row) for row in rows])
    
    # Load data using load_table_from_json
    load_job = client.load_table_from_json(
        rows, 
        table_id,
        job_config=job_config
    )
    
    try:
        load_job.result()
        logger.info(f"Loaded {len(rows)} features to {table_id}")
        return True
    except Exception as e:
        logger.error(f"Error loading data to {table_id}: {str(e)}")
        return False

def process_directory(directory, project_id, dataset_id):
    """Process all GeoJSON files in a directory."""
    success_count = 0
    fail_count = 0
    
    for filename in os.listdir(directory):
        if filename.endswith('.geojson') and filename in GEO_MAPPING:
            filepath = os.path.join(directory, filename)
            logger.info(f"Processing {filepath}")
            
            if load_geojson_to_bigquery(filepath, project_id, dataset_id):
                success_count += 1
            else:
                fail_count += 1
    
    logger.info(f"Processed {success_count + fail_count} files. Success: {success_count}, Failed: {fail_count}")
    return success_count, fail_count

def main():
    """Main entry point for script."""
    parser = argparse.ArgumentParser(description='Load GeoJSON data to BigQuery')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT,
                        help=f'BigQuery project ID (default: {DEFAULT_PROJECT})')
    parser.add_argument('--dataset', type=str, default=DEFAULT_DATASET,
                        help=f'BigQuery dataset ID (default: {DEFAULT_DATASET})')
    parser.add_argument('--local-dir', type=str, default='GIS_data',
                        help='Local directory with GeoJSON files')
    parser.add_argument('--file', type=str, 
                        help='Process only a specific GeoJSON file')
    parser.add_argument('--download-from-gcs', action='store_true',
                        help='Download GeoJSON files from GCS before loading')
    parser.add_argument('--gcs-bucket', type=str, default=DEFAULT_GCS_BUCKET,
                        help=f'GCS bucket with GeoJSON files (default: {DEFAULT_GCS_BUCKET})')
    
    args = parser.parse_args()
    
    # Ensure local directory exists
    if not os.path.exists(args.local_dir):
        os.makedirs(args.local_dir)
    
    # Download from GCS if requested
    if args.download_from_gcs:
        logger.info(f"Downloading GeoJSON files from gs://{args.gcs_bucket}/{GCS_GEO_PREFIX}")
        storage_client = storage.Client(project=args.project)
        bucket = storage_client.bucket(args.gcs_bucket)
        
        blobs = bucket.list_blobs(prefix=GCS_GEO_PREFIX)
        for blob in blobs:
            if blob.name.endswith('.geojson'):
                filename = os.path.basename(blob.name)
                local_path = os.path.join(args.local_dir, filename)
                
                logger.info(f"Downloading {blob.name} to {local_path}")
                blob.download_to_filename(local_path)
    
    # Process specific file or all files in directory
    if args.file:
        filepath = os.path.join(args.local_dir, args.file)
        if os.path.exists(filepath):
            logger.info(f"Processing single file: {filepath}")
            success = load_geojson_to_bigquery(filepath, args.project, args.dataset)
            logger.info(f"Processing {'succeeded' if success else 'failed'}")
        else:
            logger.error(f"File not found: {filepath}")
    else:
        logger.info(f"Processing all GeoJSON files in {args.local_dir}")
        success_count, fail_count = process_directory(args.local_dir, args.project, args.dataset)
        
        if fail_count == 0:
            logger.info("All files processed successfully")
        else:
            logger.warning(f"{fail_count} files failed to process")

if __name__ == "__main__":
    main()
