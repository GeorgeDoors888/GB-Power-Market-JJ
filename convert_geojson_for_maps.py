#!/usr/bin/env python3
"""
convert_geojson_for_maps.py - Prepares DNO GeoJSON files for use in Google Apps Script map viewer

This script processes the DNO license areas GeoJSON file and prepares it for use in the
Google Apps Script map viewer by:
1. Converting to EPSG:4326 (WGS84) coordinates required by Leaflet
2. Simplifying geometries to reduce file size
3. Adding DNO ID properties that match our reference data
4. Creating a new optimized GeoJSON file
"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

print("Converting DNO GeoJSON for Google Maps integration...")

# Load DNO reference data to match IDs
dno_ref_file = "DNO_Reference_Complete.csv"
if not os.path.exists(dno_ref_file):
    print(f"Error: Could not find {dno_ref_file}. Please run map_mpan_to_dno.py first.")
    sys.exit(1)

dno_ref = pd.read_csv(dno_ref_file)
print(f"Loaded DNO reference data with {len(dno_ref)} entries")

# Create a mapping dictionary for DNO names to MPAN codes
dno_name_to_mpan = {}
for _, row in dno_ref.iterrows():
    # Create variations of the DNO name to handle different formats in the GeoJSON
    base_name = row["DNO_Name"].lower().replace("–", "-")

    # Create multiple variations of the name to improve matching
    variations = [
        base_name,
        base_name.replace(" - ", " "),
        base_name.replace("ukpn", "uk power networks"),
        base_name.replace("nged", "national grid electricity distribution"),
        base_name.replace("npg", "northern powergrid"),
        base_name.replace("ssen", "scottish and southern electricity networks"),
        base_name.replace("spen", "sp energy networks"),
    ]

    # Add short names too
    variations.append(row["Short_Code"].lower())
    variations.append(row["DNO_Key"].lower())

    # Add all variations to the mapping
    for variation in variations:
        dno_name_to_mpan[variation] = int(row["MPAN_Code"])

print(f"Created {len(dno_name_to_mpan)} DNO name variations for matching")

# Include additional GeoJSON files for processing
geojson_files = [
    "system_regulatory/gis/dno_license_areas_20200506.geojson",
    "system_regulatory/gis/gsp_regions_20181031.geojson",
    "system_regulatory/gis/gb-dno-license-areas-20240503-as-geojson.geojson",
]

# Create transformer for OSGB (EPSG:27700) to WGS84 (EPSG:4326)
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


def transform_coordinates(geom):
    """Transform geometry from OSGB to WGS84"""
    return transform(lambda x, y, z=None: transformer.transform(x, y), geom)


# Enhance name normalization for matching
def normalize_name(name):
    """Normalize names by removing special characters and converting to lowercase."""
    return re.sub(r"[^a-zA-Z0-9 ]", "", name).lower()


# Process each GeoJSON file
processed_features = []
for geojson_file in geojson_files:
    if not os.path.exists(geojson_file):
        print(f"Error: Could not find {geojson_file}.")
        continue

    try:
        with open(geojson_file, "r") as f:
            geojson_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not parse {geojson_file} as valid JSON.")
        continue

    print(
        f"Loaded GeoJSON file: {geojson_file} with {len(geojson_data['features'])} features"
    )

    # Process features from the current GeoJSON file
    for feature in geojson_data["features"]:
        try:
            # Extract properties
            properties = feature["properties"]

            # Add debugging to inspect feature properties
            print(f"Debug: Feature properties: {properties}")

            # Extract and convert name to lowercase for matching
            name = None
            # Include additional keys ('Name', 'LongName') for feature name extraction
            for key in ["DNO_Name", "RegionName", "name", "NAME", "Name", "LongName"]:
                if key in properties and properties[key]:
                    name = normalize_name(properties[key])
                    break

            if not name:
                print(f"Warning: No name found for feature, skipping")
                continue

            # Try to match to a DNO using normalized names
            dno_id = None
            for key, value in dno_name_to_mpan.items():
                if normalize_name(key) in name or name in normalize_name(key):
                    dno_id = value
                    matching_key = key
                    break

            if not dno_id:
                print(f"Warning: Could not match '{name}' to a known DNO, skipping")
                continue

            # Get corresponding DNO information from reference data
            dno_info = dno_ref[dno_ref["MPAN_Code"] == dno_id].iloc[0]

            # Convert geometry to Shapely object
            geom = shape(feature["geometry"])

            # Transform coordinates to WGS84
            geom_wgs84 = transform_coordinates(geom)

            # Simplify geometry to reduce file size (adjust tolerance as needed)
            geom_simplified = geom_wgs84.simplify(0.001)

            # Create new feature with transformed geometry and updated properties
            new_feature = {
                "type": "Feature",
                "properties": {
                    "DNO_ID": int(dno_id),
                    "DNO_NAME": dno_info["DNO_Name"],
                    "DNO_KEY": dno_info["DNO_Key"],
                    "SHORT_CODE": dno_info["Short_Code"],
                    "GSP_GROUP": dno_info["GSP_Group_ID"],
                    "REGION": dno_info["Region"],
                },
                "geometry": mapping(geom_simplified),
            }

            processed_features.append(new_feature)
            print(
                f"Processed: {dno_info['DNO_Name']} (ID: {dno_id}), matched with '{matching_key}'"
            )

        except Exception as e:
            print(f"Error processing feature: {e}")

# Create new GeoJSON with processed features
new_geojson = {
    "type": "FeatureCollection",
    "name": "UK_DNO_Areas",
    "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
    "features": processed_features,
}

# Save to file
output_file = "uk_dno_areas_wgs84.geojson"
with open(output_file, "w") as f:
    json.dump(new_geojson, f)

print(f"\n✅ Converted GeoJSON saved to {output_file}")
print(f"Successfully processed {len(processed_features)} DNO areas")

# Create a simple CSV for testing in Google Sheets
dno_data_for_sheets = []
for _, row in dno_ref.iterrows():
    # Add random test value for demonstration
    value = np.random.randint(1000, 15000)
    dno_data_for_sheets.append(
        {"id": int(row["MPAN_Code"]), "name": row["DNO_Name"], "value": value}
    )

# Save to CSV
sheets_file = "dno_data_for_sheets.csv"
pd.DataFrame(dno_data_for_sheets).to_csv(sheets_file, index=False)
print(f"Created sample data CSV for Google Sheets: {sheets_file}")
