#!/usr/bin/env python
"""
create_dno_map_data.py

This script creates a sample CSV file with DNO data for visualization in Google Sheets
with the DNO map application.

It uses the DNO reference information and generates random values for demonstration purposes.
"""

import csv
import json
import os
import random
from pathlib import Path

# Constants
DNO_REFERENCE_FILE = "DNO_Reference_Complete.csv"
OUTPUT_CSV = "DNO_Map_Data.csv"
OUTPUT_GEOJSON = "DNO_Map_GeoJSON.json"

def load_dno_reference():
    """Load DNO reference data from CSV file"""
    dno_data = []
    
    try:
        with open(DNO_REFERENCE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                dno_data.append(row)
        return dno_data
    except FileNotFoundError:
        print(f"Error: {DNO_REFERENCE_FILE} not found. Creating sample data instead.")
        return create_sample_dno_data()

def create_sample_dno_data():
    """Create sample DNO data if reference file is not available"""
    return [
        {"MPAN_Code": "10", "DNO_Key": "UKPN_EPN", "DNO_Name": "UKPN – Eastern Power Networks", "Short_Code": "EPN", "GSP_Group_ID": "_A", "Region": "East England"},
        {"MPAN_Code": "11", "DNO_Key": "NGED_EME", "DNO_Name": "NGED – East Midlands", "Short_Code": "EME", "GSP_Group_ID": "_B", "Region": "East Midlands"},
        {"MPAN_Code": "12", "DNO_Key": "UKPN_LPN", "DNO_Name": "UKPN – London Power Networks", "Short_Code": "LPN", "GSP_Group_ID": "_C", "Region": "London"},
        {"MPAN_Code": "13", "DNO_Key": "SPEN_SPM", "DNO_Name": "SPEN – Manweb", "Short_Code": "SPM", "GSP_Group_ID": "_D", "Region": "Merseyside and North Wales"},
        {"MPAN_Code": "14", "DNO_Key": "NGED_WMI", "DNO_Name": "NGED – Midlands", "Short_Code": "WMI", "GSP_Group_ID": "_E", "Region": "West Midlands"},
        {"MPAN_Code": "15", "DNO_Key": "NPG_NEE", "DNO_Name": "NPg – North East", "Short_Code": "NEE", "GSP_Group_ID": "_F", "Region": "North East England"},
        {"MPAN_Code": "16", "DNO_Key": "ENWL", "DNO_Name": "Electricity North West", "Short_Code": "ENWL", "GSP_Group_ID": "_G", "Region": "North West England"},
        {"MPAN_Code": "17", "DNO_Key": "UKPN_SPN", "DNO_Name": "UKPN – South Eastern", "Short_Code": "SPN", "GSP_Group_ID": "_H", "Region": "South East England"},
        {"MPAN_Code": "18", "DNO_Key": "SSEN_SEPD", "DNO_Name": "SSEN – Southern (SEPD)", "Short_Code": "SEPD", "GSP_Group_ID": "_J", "Region": "Southern England"},
        {"MPAN_Code": "19", "DNO_Key": "NGED_SWA", "DNO_Name": "NGED – South Wales", "Short_Code": "SWA", "GSP_Group_ID": "_K", "Region": "South Wales"},
        {"MPAN_Code": "20", "DNO_Key": "NGED_SWE", "DNO_Name": "NGED – South West", "Short_Code": "SWE", "GSP_Group_ID": "_L", "Region": "South West England"},
        {"MPAN_Code": "21", "DNO_Key": "NPG_YOR", "DNO_Name": "NPg – Yorkshire", "Short_Code": "YOR", "GSP_Group_ID": "_M", "Region": "Yorkshire"},
        {"MPAN_Code": "22", "DNO_Key": "SSEN_SHEPD", "DNO_Name": "SSEN – Hydro (SHEPD)", "Short_Code": "SHEPD", "GSP_Group_ID": "_N", "Region": "North Scotland"},
        {"MPAN_Code": "23", "DNO_Key": "SPEN_SPD", "DNO_Name": "SPEN – Scottish Power (SPD)", "Short_Code": "SPD", "GSP_Group_ID": "_P", "Region": "South Scotland"},
    ]

def generate_random_values(dno_data, min_value=5000, max_value=15000):
    """Generate random values for each DNO for demonstration"""
    return {row["MPAN_Code"]: random.randint(min_value, max_value) for row in dno_data}

def create_map_data_csv(dno_data, values):
    """Create a CSV file with DNO data for the map"""
    headers = ["ID", "Name", "Value"]
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for dno in dno_data:
            writer.writerow([
                dno["MPAN_Code"],
                dno["DNO_Name"],
                values[dno["MPAN_Code"]]
            ])
    
    print(f"Created {OUTPUT_CSV} with data for {len(dno_data)} DNOs")

def create_sample_geojson():
    """Create a minimal sample GeoJSON file with just one DNO area"""
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "dno_id": "10",
                    "dno_name": "UKPN – Eastern Power Networks",
                    "dno_key": "UKPN_EPN"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [0.1, 52.0], [0.2, 52.0], [0.2, 52.1], [0.1, 52.1], [0.1, 52.0]
                    ]]
                }
            }
        ]
    }
    
    with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump(sample_geojson, f, indent=2)
    
    print(f"Created sample {OUTPUT_GEOJSON} file")
    print("Note: This is just a placeholder. Use convert_geojson_for_maps.py to create actual DNO area GeoJSON.")

def main():
    # Load DNO reference data
    dno_data = load_dno_reference()
    
    # Generate random values for demonstration
    values = generate_random_values(dno_data)
    
    # Create CSV file for Google Sheets
    create_map_data_csv(dno_data, values)
    
    # Create a minimal sample GeoJSON file
    create_sample_geojson()
    
    print("\nNext steps:")
    print("1. Upload DNO_Map_Data.csv to Google Drive")
    print("2. Run convert_geojson_for_maps.py to create proper GeoJSON file")
    print("3. Upload the resulting GeoJSON file to Google Drive")
    print("4. Create a new Google Sheet and import the CSV data")
    print("5. Set up the Google Apps Script as described in the documentation")

if __name__ == "__main__":
    main()
