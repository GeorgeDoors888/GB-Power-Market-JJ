#!/usr/bin/env python3
"""
create_dno_geojson.py - Creates a GeoJSON file with UK DNO boundaries

This script generates a simplified GeoJSON file with boundaries for UK Distribution
Network Operators (DNOs) based on the DNO reference data. This file can be used with
the Google Apps Script map visualization code.
"""
import json
import pandas as pd
import os
import random
import math

# Load the DNO reference data
print("Loading DNO reference data...")
if os.path.exists("DNO_Reference_Complete.csv"):
    dno_ref = pd.read_csv("DNO_Reference_Complete.csv")
    print(f"Loaded {len(dno_ref)} DNO records from DNO_Reference_Complete.csv")
else:
    print("DNO_Reference_Complete.csv not found, creating simplified reference data")
    # Create simplified reference data if file not found
    dno_data = {
        "MPAN_Code": list(range(10, 24)),
        "DNO_Key": [
            "UKPN-E", "NGED-EM", "UKPN-L", "SP-MW", "NGED-M", 
            "NPg-NE", "ENWL", "UKPN-SE", "SSE-S", "NGED-SW", 
            "NGED-SW", "NPg-Y", "SSE-H", "SP-S"
        ],
        "DNO_Name": [
            "UKPN – Eastern Power Networks", "NGED – East Midlands", 
            "UKPN – London Power Networks", "SPEN – Manweb (Merseyside/N Wales)", 
            "NGED – Midlands", "NPg – North East", "Electricity North West",
            "UKPN – South Eastern", "SSEN – Southern (SEPD)", 
            "NGED – South Wales", "NGED – South West", 
            "NPg – Yorkshire", "SSEN – Hydro (SHEPD)", 
            "SPEN – Scottish Power (SPD)"
        ],
        "GSP_Group_ID": ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P"],
        "Region": [
            "East Anglia", "Nottingham, Leicester", "Greater London", 
            "Liverpool, North Wales", "Birmingham, Coventry", 
            "Newcastle, Durham", "Manchester, Cumbria", 
            "Kent, Sussex", "Hampshire, Surrey, Berks", 
            "Cardiff, Swansea", "Cornwall, Devon, Somerset", 
            "Leeds, Sheffield", "North Scotland (Highlands)", 
            "Central & Southern Scotland"
        ]
    }
    dno_ref = pd.DataFrame(dno_data)

# Create simplified UK DNO boundaries as GeoJSON
# These are approximated and simplified polygons for visualization
# Real DNO boundaries would require actual geographic data

# Reference points (approximate centers of regions)
uk_reference_points = {
    "UKPN-E": (52.2, 0.7),      # East Anglia
    "NGED-EM": (52.9, -1.1),    # East Midlands
    "UKPN-L": (51.5, -0.1),     # London
    "SP-MW": (53.3, -3.0),      # Merseyside/North Wales
    "NGED-M": (52.5, -1.9),     # Midlands
    "NPg-NE": (54.9, -1.6),     # North East
    "ENWL": (54.0, -2.5),       # North West
    "UKPN-SE": (51.0, 0.5),     # South East
    "SSE-S": (51.2, -1.0),      # Southern
    "NGED-SW": (51.5, -3.2),    # South Wales
    "NGED-SW2": (50.5, -4.2),   # South West (duplicate key with different coordinates)
    "NPg-Y": (53.8, -1.5),      # Yorkshire
    "SSE-H": (57.5, -4.5),      # Highlands
    "SP-S": (55.9, -3.2)        # Central & Southern Scotland
}

def generate_polygon(center, radius_km, points=8, jitter=0.15):
    """Generate a simplified polygon around a center point with some randomness"""
    lat, lon = center
    polygon = []
    
    # Convert radius from km to degrees (approximate)
    radius_lat = radius_km / 111  # 1 degree latitude is about 111 km
    radius_lon = radius_km / (111 * math.cos(math.radians(lat)))  # Adjust for longitude
    
    for i in range(points):
        angle = (2 * math.pi * i) / points
        # Add some randomness to make irregular shapes
        jitter_amount = 1.0 + (random.random() * jitter * 2 - jitter)
        r_lat = radius_lat * jitter_amount
        r_lon = radius_lon * jitter_amount
        
        point_lat = lat + r_lat * math.cos(angle)
        point_lon = lon + r_lon * math.sin(angle)
        polygon.append([point_lon, point_lat])  # GeoJSON uses [lon, lat] order
    
    # Close the polygon
    polygon.append(polygon[0])
    return polygon

print("Generating GeoJSON file with DNO boundaries...")
features = []

# Special case for South West vs South Wales (both have NGED-SW code)
for index, row in dno_ref.iterrows():
    dno_key = row['DNO_Key']
    dno_id = row['MPAN_Code']
    dno_name = row['DNO_Name']
    
    # Handle the duplicate NGED-SW key
    if dno_key == "NGED-SW":
        if "Wales" in dno_name:
            ref_key = "NGED-SW"  # South Wales
            radius = 30  # Smaller area
        else:
            ref_key = "NGED-SW2"  # South West
            radius = 60  # Larger area
    else:
        ref_key = dno_key
        # Adjust radius based on region size (approximate)
        if dno_key in ["SSE-H", "SP-S"]:  # Scottish regions
            radius = 80
        elif dno_key in ["UKPN-L"]:  # London - small dense area
            radius = 15
        else:
            radius = 40  # Default
    
    # Get center coordinates or default to a UK point if not found
    if ref_key in uk_reference_points:
        center = uk_reference_points[ref_key]
    else:
        print(f"Warning: No coordinates for {dno_key}, using default")
        center = (52.5, -1.5)  # Default to middle of UK
    
    # Generate polygon with some randomness
    polygon = generate_polygon(center, radius, points=10, jitter=0.2)
    
    # Create GeoJSON feature
    feature = {
        "type": "Feature",
        "properties": {
            "DNO_ID": int(dno_id),
            "DNO_KEY": dno_key,
            "DNO_NAME": dno_name,
            "GSP_GROUP": row['GSP_Group_ID'],
            "REGION": row['Region']
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [polygon]
        }
    }
    
    features.append(feature)

# Create GeoJSON structure
geojson = {
    "type": "FeatureCollection",
    "features": features
}

# Write to file
output_file = "uk_dno_boundaries.geojson"
with open(output_file, 'w') as f:
    json.dump(geojson, f, indent=2)

print(f"✅ GeoJSON file created: {output_file}")
print(f"Total features: {len(features)}")

# Also create a simplified CSV file for Google Sheets
print("\nCreating DNO data CSV for Google Sheets...")
sheet_data = []

# Load our organized data to get mean rate values
if os.path.exists("Organised_DNO_By_Date_Fixed.csv"):
    print("Loading rate data from Organised_DNO_By_Date_Fixed.csv")
    rates_df = pd.read_csv("Organised_DNO_By_Date_Fixed.csv")
    
    # Get latest year
    latest_year = rates_df['Year'].max()
    print(f"Using data for latest year: {latest_year}")
    
    # Group by DNO and calculate mean rates for latest year
    latest_data = rates_df[rates_df['Year'] == latest_year]
    dno_means = latest_data.groupby('MPAN_Code')['Mean_Rate_p_kWh'].mean().reset_index()
    
    # Scale up the values for better visualization (p/kWh to £/MWh)
    dno_means['Value'] = dno_means['Mean_Rate_p_kWh'] * 1000 / 100  # Convert to £/MWh
    
    for index, row in dno_ref.iterrows():
        mpan_code = row['MPAN_Code']
        # Find the corresponding rate
        rate_row = dno_means[dno_means['MPAN_Code'] == mpan_code]
        if not rate_row.empty:
            value = rate_row.iloc[0]['Value']
        else:
            # Assign random value if no rate data
            value = random.uniform(30, 120)
        
        sheet_data.append({
            'ID': int(mpan_code),
            'Name': row['DNO_Name'],
            'Value': round(value, 2)
        })
else:
    print("Rate data not found, using random values")
    # If no rate data, use random values
    for index, row in dno_ref.iterrows():
        sheet_data.append({
            'ID': int(row['MPAN_Code']),
            'Name': row['DNO_Name'],
            'Value': round(random.uniform(30, 120), 2)  # Random value in £/MWh
        })

# Create DataFrame and save to CSV
sheet_df = pd.DataFrame(sheet_data)
sheet_file = "dno_data_for_sheets.csv"
sheet_df.to_csv(sheet_file, index=False)
print(f"✅ Sheets data file created: {sheet_file}")

print("\nInstructions for Google Apps Script:")
print("1. Upload uk_dno_boundaries.geojson to your Google Drive")
print("2. Get the file ID from the URL (the long string after /d/ in the URL)")
print("3. Replace 'YOUR_GEOJSON_FILE_ID' in the Apps Script with this ID")
print("4. Import dno_data_for_sheets.csv into a sheet named 'DNO_Data'")
print("5. Run the Apps Script to visualize the DNO map")
