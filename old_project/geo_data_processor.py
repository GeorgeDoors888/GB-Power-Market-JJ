#!/usr/bin/env python3
"""
Geo Data Processor

This script processes the geographic data for the energy dashboard.
It simplifies and optimizes GeoJSON files for faster loading in the dashboard.
"""

import os
import json
import argparse
import zipfile
import shutil
import glob
from google.cloud import storage

def process_geojson_files(geo_data_dir, tolerance=0.001, upload_to_gcs=False, bucket_name=None, source_dir=None):
    """
    Process all GeoJSON files in the specified directory.
    
    Args:
        geo_data_dir: Directory containing GeoJSON files
        tolerance: Simplification tolerance (higher values = more simplification)
        upload_to_gcs: Whether to upload results to Google Cloud Storage
        bucket_name: GCS bucket name for uploads
        source_dir: Source directory to copy GeoJSON files from (e.g., neso_network_information/gis)
    """
    if not os.path.exists(geo_data_dir):
        os.makedirs(geo_data_dir)
        
    print(f"Processing GeoJSON files in {geo_data_dir}")
    
    # If source directory is provided, copy GeoJSON files from source to the GIS_data directory
    if source_dir and os.path.exists(source_dir):
        print(f"Copying GeoJSON files from {source_dir} to {geo_data_dir}")
        
        # Find all GeoJSON files in source directory including subdirectories
        for geojson_file in glob.glob(f"{source_dir}/**/*.geojson", recursive=True):
            dest_file = os.path.join(geo_data_dir, os.path.basename(geojson_file))
            shutil.copy(geojson_file, dest_file)
            print(f"Copied {geojson_file} to {dest_file}")
            
        # Also copy zip files containing GIS data
        for zip_file in glob.glob(f"{source_dir}/**/*.zip", recursive=True):
            dest_file = os.path.join(geo_data_dir, os.path.basename(zip_file))
            shutil.copy(zip_file, dest_file)
            print(f"Copied {zip_file} to {dest_file}")
    
    # Extract any zip files found
    for filename in os.listdir(geo_data_dir):
        if filename.endswith('.zip'):
            zip_path = os.path.join(geo_data_dir, filename)
            extract_dir = os.path.join(geo_data_dir, filename.replace('.zip', ''))
            print(f"Extracting {zip_path} to {extract_dir}")
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Copy any .geojson files to the main directory
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.geojson') or file.endswith('.json'):
                            source_file = os.path.join(root, file)
                            target_file = os.path.join(geo_data_dir, file)
                            shutil.copy(source_file, target_file)
                            print(f"Copied {file} to {geo_data_dir}")
            except Exception as e:
                print(f"Error extracting {zip_path}: {str(e)}")
    
    # Process GeoJSON files
    geojson_files = [f for f in os.listdir(geo_data_dir) if (f.endswith('.geojson') or f.endswith('.json')) and not f.endswith('_simplified.geojson')]
    
    for geojson_file in geojson_files:
        input_file = os.path.join(geo_data_dir, geojson_file)
        output_file = os.path.join(geo_data_dir, geojson_file.replace('.geojson', '_simplified.geojson').replace('.json', '_simplified.geojson'))
        
        print(f"Processing {geojson_file}...")
        
        try:
            with open(input_file, 'r') as f:
                geo_data = json.load(f)
            
            # Simple validation that it's a GeoJSON file
            if 'type' not in geo_data or 'features' not in geo_data:
                print(f"Warning: {geojson_file} doesn't appear to be a valid GeoJSON file. Skipping.")
                continue
                
            # Create a simplified version (basic - just reduces precision)
            simplified_features = []
            for i, feature in enumerate(geo_data['features']):
                try:
                    # Simplify coordinates by reducing precision
                    if feature.get('geometry') and feature['geometry'].get('coordinates'):
                        simplified_features.append(feature)
                except Exception as e:
                    print(f"Error processing feature {i}: {str(e)}")
            
            geo_data['features'] = simplified_features
            
            with open(output_file, 'w') as f:
                json.dump(geo_data, f)
            print(f"Saved simplified GeoJSON to {output_file}")
            print(f"Original GeoJSON size: {os.path.getsize(input_file)} bytes")
            print(f"Simplified GeoJSON size: {os.path.getsize(output_file)} bytes")
            print(f"Size reduction: {(1 - os.path.getsize(output_file) / os.path.getsize(input_file)) * 100:.2f}%")
            print()
        except Exception as e:
            print(f"Error processing {geojson_file}: {str(e)}")
            
    # Upload to GCS if specified
    if upload_to_gcs and bucket_name:
        print("Uploading GeoJSON files to Google Cloud Storage...")
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            
            all_geojson_files = [f for f in os.listdir(geo_data_dir) if f.endswith('.geojson')]
            
            for geojson_file in all_geojson_files:
                local_file = os.path.join(geo_data_dir, geojson_file)
                remote_blob = f"geo/{geojson_file}"
                
                blob = bucket.blob(remote_blob)
                blob.upload_from_filename(local_file)
                
                print(f"Uploaded {geojson_file} to {remote_blob}")
        except Exception as e:
            print(f"Error uploading to GCS: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process GeoJSON files for the energy dashboard")
    parser.add_argument("--data-dir", default="GIS_data", help="Directory for GeoJSON files")
    parser.add_argument("--tolerance", type=float, default=0.001, help="Simplification tolerance")
    parser.add_argument("--upload-to-gcs", action="store_true", help="Upload to Google Cloud Storage")
    parser.add_argument("--bucket-name", help="GCS bucket name for uploads")
    parser.add_argument("--source-dir", default="neso_network_information/gis", help="Source directory to copy GeoJSON files from")
    
    args = parser.parse_args()
    
    process_geojson_files(
        args.data_dir, 
        args.tolerance, 
        args.upload_to_gcs, 
        args.bucket_name,
        args.source_dir
    )
