#!/usr/bin/env python3
"""
map_mpan_to_dno.py - Maps MPAN distributor IDs to DNO information

This script creates and saves a comprehensive DNO reference file based on the
mapping between MPAN distributor IDs (first two digits) and DNO information.
"""
import pandas as pd
import os

print("Creating comprehensive DNO reference mapping...")

# === Define the MPAN code to DNO mapping ===
mpan_dno_mapping = {
    10: {'DNO_Key': 'UKPN-E', 'DNO_Name': 'UKPN – Eastern Power Networks', 'Short_Code': 'Eastern', 'GSP_Group_ID': 'A', 'Region': 'East Anglia'},
    11: {'DNO_Key': 'NGED-EM', 'DNO_Name': 'NGED – East Midlands', 'Short_Code': 'EastMidlands', 'GSP_Group_ID': 'B', 'Region': 'Nottingham, Leicester'},
    12: {'DNO_Key': 'UKPN-L', 'DNO_Name': 'UKPN – London Power Networks', 'Short_Code': 'London', 'GSP_Group_ID': 'C', 'Region': 'Greater London'},
    13: {'DNO_Key': 'SP-MW', 'DNO_Name': 'SPEN – Manweb (Merseyside/N Wales)', 'Short_Code': 'Manweb', 'GSP_Group_ID': 'D', 'Region': 'Liverpool, North Wales'},
    14: {'DNO_Key': 'NGED-M', 'DNO_Name': 'NGED – Midlands', 'Short_Code': 'Midlands', 'GSP_Group_ID': 'E', 'Region': 'Birmingham, Coventry'},
    15: {'DNO_Key': 'NPg-NE', 'DNO_Name': 'NPg – North East', 'Short_Code': 'NorthEast', 'GSP_Group_ID': 'F', 'Region': 'Newcastle, Durham'},
    16: {'DNO_Key': 'ENWL', 'DNO_Name': 'Electricity North West', 'Short_Code': 'NorthWest', 'GSP_Group_ID': 'G', 'Region': 'Manchester, Cumbria'},
    17: {'DNO_Key': 'UKPN-SE', 'DNO_Name': 'UKPN – South Eastern', 'Short_Code': 'SouthEastern', 'GSP_Group_ID': 'H', 'Region': 'Kent, Sussex'},
    18: {'DNO_Key': 'SSE-S', 'DNO_Name': 'SSEN – Southern (SEPD)', 'Short_Code': 'Southern', 'GSP_Group_ID': 'J', 'Region': 'Hampshire, Surrey, Berks'},
    19: {'DNO_Key': 'NGED-SW', 'DNO_Name': 'NGED – South Wales', 'Short_Code': 'SouthWales', 'GSP_Group_ID': 'K', 'Region': 'Cardiff, Swansea'},
    20: {'DNO_Key': 'NGED-SW', 'DNO_Name': 'NGED – South West', 'Short_Code': 'SouthWest', 'GSP_Group_ID': 'L', 'Region': 'Cornwall, Devon, Somerset'},
    21: {'DNO_Key': 'NPg-Y', 'DNO_Name': 'NPg – Yorkshire', 'Short_Code': 'Yorkshire', 'GSP_Group_ID': 'M', 'Region': 'Leeds, Sheffield'},
    22: {'DNO_Key': 'SSE-H', 'DNO_Name': 'SSEN – Hydro (SHEPD)', 'Short_Code': 'Hydro', 'GSP_Group_ID': 'N', 'Region': 'North Scotland (Highlands)'},
    23: {'DNO_Key': 'SP-S', 'DNO_Name': 'SPEN – Scottish Power (SPD)', 'Short_Code': 'SPDistribution', 'GSP_Group_ID': 'P', 'Region': 'Central & Southern Scotland'}
}

# Create a reference DataFrame from the mapping
dno_reference_data = []
for mpan_code, data in mpan_dno_mapping.items():
    row = {'MPAN_Code': mpan_code, **data}
    dno_reference_data.append(row)

dno_ref = pd.DataFrame(dno_reference_data)
print(f"Created reference mapping for {len(dno_reference_data)} DNOs")

# === Save the comprehensive DNO reference file ===
output_file = "DNO_Reference_Complete.csv"
dno_ref.to_csv(output_file, index=False)
print(f"\n✅ Comprehensive DNO reference saved to {output_file}")
print(dno_ref)

# === Now update the Organised_DNO_By_Date.csv file with correct mapping ===
if os.path.exists("duos_outputs2/DNO_DUoS_All_Data.csv"):
    duos_file = "duos_outputs2/DNO_DUoS_All_Data.csv"
elif os.path.exists("DNO_DUoS_All_Data.csv"):
    duos_file = "DNO_DUoS_All_Data.csv"
else:
    print("\n❌ Could not find DNO_DUoS_All_Data.csv file")
    exit(1)

print(f"\nLoading DUoS data from {duos_file}...")
df = pd.read_csv(duos_file)
print(f"Loaded {len(df)} rows with {len(df.columns)} columns")

# Check if MPAN_Code exists, if not derive from DNO_Key
if 'MPAN_Code' not in df.columns:
    print("\nMPAN_Code column not found, creating from mapping...")
    # Create reverse mapping from DNO_Key to MPAN_Code
    dno_key_to_mpan = {}
    for mpan_code, data in mpan_dno_mapping.items():
        dno_key_to_mpan[data['DNO_Key']] = mpan_code
    
    # Apply mapping
    if 'DNO_Key' in df.columns:
        df['MPAN_Code'] = df['DNO_Key'].map(dno_key_to_mpan)
        print(f"Mapped {df['MPAN_Code'].notna().sum()} MPAN codes from DNO_Key")
    else:
        print("❌ Could not create MPAN_Code: DNO_Key column not found")
        df['MPAN_Code'] = 0  # Default to avoid errors

# Standardize year and create date column
df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
print(f"Year values: {df['Year'].unique()}")
# Create the Date column
df['Date'] = pd.to_datetime(df['Year'], format='%Y', errors='coerce')

# Group by MPAN_Code and Year
print("\nGrouping data by MPAN_Code and Year...")
agg_columns = {
    'Min_Rate_p_kWh': 'min',
    'Max_Rate_p_kWh': 'max',
    'Mean_Rate_p_kWh': 'mean',
    'Median_Rate_p_kWh': 'median',
    'Count': 'sum'
}
# Filter columns that exist
agg_columns = {k: v for k, v in agg_columns.items() if k in df.columns}
if not agg_columns:
    print("❌ No rate columns found to aggregate")
    exit(1)

grouped = df.groupby(['MPAN_Code', 'Year']).agg(agg_columns).reset_index()

# Merge with reference data
print("\nMerging with DNO reference data...")
merged = pd.merge(grouped, dno_ref, on='MPAN_Code', how='left')

# Select and order final columns
final_columns = [col for col in [
    'MPAN_Code', 'DNO_Key', 'DNO_Name', 'Short_Code', 'GSP_Group_ID', 'Region',
    'Year', 'Date', 'Min_Rate_p_kWh', 'Max_Rate_p_kWh', 
    'Mean_Rate_p_kWh', 'Median_Rate_p_kWh', 'Count'
] if col in merged.columns]

# Save organized data
output_file = "Organised_DNO_By_Date_Fixed.csv"
final_df = merged[final_columns].sort_values(['DNO_Key', 'Year'])
final_df.to_csv(output_file, index=False)

print(f"\n✅ Fixed organized data saved to {output_file}")
print(f"Total rows: {len(merged)}")
print("\nSample of the fixed organized data:")
print(merged.head(10))

# Print summary by DNO
print("\nSummary by DNO:")
dno_summary = merged.groupby('DNO_Name').agg({
    'Year': 'nunique',
    'Min_Rate_p_kWh': lambda x: x.mean() if 'Min_Rate_p_kWh' in merged.columns else None,
    'Max_Rate_p_kWh': lambda x: x.mean() if 'Max_Rate_p_kWh' in merged.columns else None,
    'Mean_Rate_p_kWh': lambda x: x.mean() if 'Mean_Rate_p_kWh' in merged.columns else None
}).reset_index()
dno_summary.columns = ['DNO_Name', 'Years_Covered', 'Avg_Min_Rate', 'Avg_Max_Rate', 'Avg_Mean_Rate']
print(dno_summary)
