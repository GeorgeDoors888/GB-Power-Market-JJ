#!/usr/bin/env python
"""
convert_geojson_for_google_maps.py

This script optimizes GeoJSON files containing UK DNO license areas for use with
Google Maps and Leaflet in Google Apps Script.

It:
1. Loads DNO reference data to get proper mappings
2. Processes GeoJSON files of DNO license areas
3. Converts coordinates from OSGB (EPSG:27700) to WGS84 (EPSG:4326)
4. Simplifies geometry to reduce file size
5. Adds proper DNO ID properties
6. Creates an optimized GeoJSON file for use with Google Apps Script

Requirements:
- pyproj
- shapely
- pandas

Example usage:
    python convert_geojson_for_google_maps.py --input-dir ./geojson --output-file dno_areas_for_maps.json
"""

import argparse
import csv
import glob
import json
import os
import sys
from pathlib import Path

try:
    import pandas as pd
    import pyproj
    from shapely.geometry import shape, mapping
    from shapely.ops import transform
except ImportError:
    print("Required libraries not found. Please install:")
    print("pip install pandas pyproj shapely")
    sys.exit(1)

# Constants
DEFAULT_INPUT_DIR = "./geojson"
DEFAULT_OUTPUT_FILE = "dno_areas_for_maps.json"
DEFAULT_DNO_REFERENCE = "DNO_Reference_Complete.csv"
DEFAULT_SIMPLIFY_TOLERANCE = 0.001  # Degrees for WGS84 (roughly 100m)

def load_dno_reference(reference_file):
    """Load DNO reference data from CSV file"""
    try:
        df = pd.read_csv(reference_file)
        # Create a mapping from license area names to DNO IDs
        dno_mapping = {}
        
        for _, row in df.iterrows():
            # Extract the MPAN code (DNO ID)
            dno_id = row["MPAN_Code"]
            
            # Get the DNO name and key
            dno_name = row["DNO_Name"]
            dno_key = row["DNO_Key"]
            
            # Add mappings with variations of the name
            dno_mapping[dno_name.lower()] = {"id": dno_id, "name": dno_name, "key": dno_key}
            
            # Add short name variations
            if "–" in dno_name:
                company, area = dno_name.split("–", 1)
                company = company.strip()
                area = area.strip()
                
                dno_mapping[company.lower()] = {"id": dno_id, "name": dno_name, "key": dno_key}
                dno_mapping[area.lower()] = {"id": dno_id, "name": dno_name, "key": dno_key}
                
                # Add without special characters
                clean_name = dno_name.replace("–", "-")
                dno_mapping[clean_name.lower()] = {"id": dno_id, "name": dno_name, "key": dno_key}
        
        return dno_mapping
    
    except Exception as e:
        print(f"Error loading DNO reference data: {e}")
        return {}

def create_coordinate_transformer():
    """Create a transformer from OSGB36 (EPSG:27700) to WGS84 (EPSG:4326)"""
    try:
        # Define the source and target CRS
        source_crs = pyproj.CRS.from_epsg(27700)  # OSGB36 / British National Grid
        target_crs = pyproj.CRS.from_epsg(4326)   # WGS84
        
        # Create a transformer
        transformer = pyproj.Transformer.from_crs(source_crs, target_crs, always_xy=True)
        
        # Create a function that transforms coordinates
        def transform_coords(x, y):
            return transformer.transform(x, y)
        
        return transform_coords
    
    except Exception as e:
        print(f"Error creating coordinate transformer: {e}")
        return None

def simplify_geometry(geojson, tolerance=0.001):
    """Simplify GeoJSON geometry to reduce file size"""
    try:
        # Create a copy of the GeoJSON
        simplified = {"type": "FeatureCollection", "features": []}
        
        # Process each feature
        for feature in geojson["features"]:
            # Convert to shapely geometry
            geom = shape(feature["geometry"])
            
            # Simplify the geometry
            simplified_geom = geom.simplify(tolerance, preserve_topology=True)
            
            # Convert back to GeoJSON
            feature["geometry"] = mapping(simplified_geom)
            
            # Add to the simplified GeoJSON
            simplified["features"].append(feature)
        
        return simplified
    
    except Exception as e:
        print(f"Error simplifying geometry: {e}")
        return geojson

def transform_coordinates(geojson, transform_func):
    """Transform coordinates from OSGB36 to WGS84"""
    if not transform_func:
        print("Warning: No transform function provided. Returning original GeoJSON.")
        return geojson
    
    try:
        # Create a copy of the GeoJSON
        transformed = {"type": "FeatureCollection", "features": []}
        
        # Process each feature
        for feature in geojson["features"]:
            # Convert to shapely geometry
            geom = shape(feature["geometry"])
            
            # Transform the geometry
            transformed_geom = transform(transform_func, geom)
            
            # Convert back to GeoJSON
            feature["geometry"] = mapping(transformed_geom)
            
            # Add to the transformed GeoJSON
            transformed["features"].append(feature)
        
        return transformed
    
    except Exception as e:
        print(f"Error transforming coordinates: {e}")
        return geojson

def add_dno_properties(geojson, dno_mapping):
    """Add DNO ID properties to GeoJSON features"""
    if not dno_mapping:
        print("Warning: No DNO mapping provided. Returning original GeoJSON.")
        return geojson
    
    try:
        # Create a copy of the GeoJSON
        with_properties = {"type": "FeatureCollection", "features": []}
        
        # Process each feature
        for feature in geojson["features"]:
            properties = feature.get("properties", {})
            
            # Try to find the DNO in the mapping
            dno_found = False
            
            # Get name from properties
            name = properties.get("name", "").lower()
            if name in dno_mapping:
                dno = dno_mapping[name]
                properties["dno_id"] = dno["id"]
                properties["dno_name"] = dno["name"]
                properties["dno_key"] = dno["key"]
                dno_found = True
            else:
                # Try other common property names
                for prop in ["DNO", "dno", "operator", "company", "description"]:
                    if prop in properties and properties[prop].lower() in dno_mapping:
                        dno = dno_mapping[properties[prop].lower()]
                        properties["dno_id"] = dno["id"]
                        properties["dno_name"] = dno["name"]
                        properties["dno_key"] = dno["key"]
                        dno_found = True
                        break
            
            # If DNO not found, use a default ID
            if not dno_found:
                # Check if any DNO name is contained within the property values
                for prop, value in properties.items():
                    if isinstance(value, str):
                        for dno_name, dno in dno_mapping.items():
                            if dno_name in value.lower():
                                properties["dno_id"] = dno["id"]
                                properties["dno_name"] = dno["name"]
                                properties["dno_key"] = dno["key"]
                                dno_found = True
                                break
                    if dno_found:
                        break
            
            # If still not found, set to unknown
            if not dno_found:
                print(f"Warning: No DNO found for feature with properties: {properties}")
                properties["dno_id"] = "0"
                properties["dno_name"] = "Unknown DNO"
                properties["dno_key"] = "UNKNOWN"
            
            # Update the feature properties
            feature["properties"] = properties
            
            # Add to the updated GeoJSON
            with_properties["features"].append(feature)
        
        return with_properties
    
    except Exception as e:
        print(f"Error adding DNO properties: {e}")
        return geojson

def process_geojson_files(input_dir, output_file, dno_reference, simplify_tolerance):
    """Process all GeoJSON files in the input directory"""
    try:
        # Load DNO reference data
        dno_mapping = load_dno_reference(dno_reference)
        if not dno_mapping:
            print("Error: Failed to load DNO reference data.")
            return False
        
        # Create coordinate transformer
        transform_func = create_coordinate_transformer()
        if not transform_func:
            print("Error: Failed to create coordinate transformer.")
            return False
        
        # Find all GeoJSON files in the input directory
        geojson_files = glob.glob(os.path.join(input_dir, "*.geojson"))
        geojson_files.extend(glob.glob(os.path.join(input_dir, "*.json")))
        
        if not geojson_files:
            print(f"Error: No GeoJSON files found in {input_dir}")
            return False
        
        print(f"Found {len(geojson_files)} GeoJSON files to process.")
        
        # Create a combined GeoJSON
        combined = {"type": "FeatureCollection", "features": []}
        
        # Process each file
        for file_path in geojson_files:
            print(f"Processing {file_path}...")
            
            try:
                # Load the GeoJSON file
                with open(file_path, 'r') as f:
                    geojson = json.load(f)
                
                # If it's not a FeatureCollection, skip it
                if geojson.get("type") != "FeatureCollection":
                    print(f"Warning: {file_path} is not a FeatureCollection. Skipping.")
                    continue
                
                # Process the GeoJSON
                processed = geojson
                processed = transform_coordinates(processed, transform_func)
                processed = add_dno_properties(processed, dno_mapping)
                
                # Add features to the combined GeoJSON
                combined["features"].extend(processed["features"])
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        # Simplify the combined GeoJSON
        if combined["features"]:
            combined = simplify_geometry(combined, simplify_tolerance)
            
            # Write the output file
            with open(output_file, 'w') as f:
                json.dump(combined, f)
            
            print(f"Successfully processed {len(combined['features'])} features.")
            print(f"Output written to {output_file}")
            
            # Calculate file size
            size_bytes = os.path.getsize(output_file)
            size_kb = size_bytes / 1024
            size_mb = size_kb / 1024
            
            print(f"File size: {size_bytes:,} bytes ({size_mb:.2f} MB)")
            
            # Warning if file is too large
            if size_mb > 5:
                print("Warning: File size exceeds 5 MB, which may cause performance issues.")
                print("Consider increasing the simplify_tolerance parameter.")
            
            return True
        else:
            print("Error: No features found in GeoJSON files.")
            return False
    
    except Exception as e:
        print(f"Error processing GeoJSON files: {e}")
        return False

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Convert GeoJSON files for Google Maps")
    parser.add_argument("--input-dir", type=str, default=DEFAULT_INPUT_DIR,
                        help=f"Directory containing GeoJSON files (default: {DEFAULT_INPUT_DIR})")
    parser.add_argument("--output-file", type=str, default=DEFAULT_OUTPUT_FILE,
                        help=f"Output GeoJSON file (default: {DEFAULT_OUTPUT_FILE})")
    parser.add_argument("--dno-reference", type=str, default=DEFAULT_DNO_REFERENCE,
                        help=f"DNO reference CSV file (default: {DEFAULT_DNO_REFERENCE})")
    parser.add_argument("--simplify-tolerance", type=float, default=DEFAULT_SIMPLIFY_TOLERANCE,
                        help=f"Simplify tolerance in degrees (default: {DEFAULT_SIMPLIFY_TOLERANCE})")
    
    args = parser.parse_args()
    
    # Process GeoJSON files
    success = process_geojson_files(
        args.input_dir,
        args.output_file,
        args.dno_reference,
        args.simplify_tolerance
    )
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
