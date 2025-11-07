#!/usr/bin/env python3
"""Create comprehensive JSON file with VLP battery unit data"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# Find the most recent CSV files
csv_files = list(Path('.').glob('battery_bmus_complete_*.csv'))
if not csv_files:
    print("❌ No battery BMU CSV files found")
    exit(1)

latest_csv = sorted(csv_files)[-1]
print(f"📂 Reading: {latest_csv}")

# Read the battery BMUs data
df = pd.read_csv(latest_csv)

# Create comprehensive JSON structure
data = {
    "metadata": {
        "title": "GB Battery Storage BMU Units - VLP Analysis",
        "description": "Complete list of battery storage BMU units in GB balancing mechanism with Virtual Lead Party (VLP) identification",
        "generated_date": datetime.now().isoformat(),
        "data_source": "NESO BMRS API + BMU Registration Data",
        "analysis_date": latest_csv.stem.split('_')[-2] if '_' in str(latest_csv) else "2025-11-06",
        "total_battery_bmus": int(len(df)),
        "total_vlp_operated": int(len(df[df['is_vlp'] == True])),
        "total_direct_operated": int(len(df[df['is_vlp'] == False])),
        "vlp_percentage": round(len(df[df['is_vlp'] == True]) / len(df) * 100, 1) if len(df) > 0 else 0,
        "analysis_period": "2023-2024",
        "data_fields": {
            "nationalGridBmUnit": "National Grid BMU identifier",
            "elexonBmUnit": "Elexon BMU identifier (used in BOD data)",
            "leadPartyName": "Company operating the BMU",
            "leadPartyId": "Lead party identifier code",
            "fuelType": "Fuel/technology type",
            "generationCapacity": "Export capacity in MW",
            "demandCapacity": "Import capacity in MW",
            "bmUnitType": "Type of BMU unit (E=embedded, T=transmission, V=virtual)",
            "bmUnitName": "Site/project name",
            "gspGroupName": "Grid Supply Point region",
            "is_vlp": "True if operated by Virtual Lead Party (any VLP criteria met)",
            "is_vlp_by_name": "True if VLP identified by company name keywords",
            "is_aggregator_code": "True if BMU code indicates aggregation (2__, C__, M__)",
            "multiple_assets": "True if lead party manages multiple BMUs (portfolio)"
        }
    },
    "summary_statistics": {
        "total_capacity_mw": float(df['generationCapacity'].sum()),
        "average_capacity_mw": float(df['generationCapacity'].mean()),
        "median_capacity_mw": float(df['generationCapacity'].median()),
        "by_vlp_status": {
            "vlp_operated": {
                "count": int(len(df[df['is_vlp'] == True])),
                "total_capacity_mw": float(df[df['is_vlp'] == True]['generationCapacity'].sum()),
                "avg_capacity_mw": float(df[df['is_vlp'] == True]['generationCapacity'].mean()),
                "percentage": round(len(df[df['is_vlp'] == True]) / len(df) * 100, 1) if len(df) > 0 else 0
            },
            "direct_operated": {
                "count": int(len(df[df['is_vlp'] == False])),
                "total_capacity_mw": float(df[df['is_vlp'] == False]['generationCapacity'].sum()),
                "avg_capacity_mw": float(df[df['is_vlp'] == False]['generationCapacity'].mean()),
                "percentage": round(len(df[df['is_vlp'] == False]) / len(df) * 100, 1) if len(df) > 0 else 0
            }
        },
        "top_vlp_operators": []
    },
    "battery_units": []
}

# Calculate top VLP operators
vlp_df = df[df['is_vlp'] == True]
top_vlps = vlp_df.groupby('leadPartyName').agg({
    'nationalGridBmUnit': 'count',
    'generationCapacity': 'sum'
}).sort_values('generationCapacity', ascending=False).head(10)

for lead_party, row in top_vlps.iterrows():
    data['summary_statistics']['top_vlp_operators'].append({
        "name": str(lead_party),
        "bmu_count": int(row['nationalGridBmUnit']),
        "total_capacity_mw": float(row['generationCapacity'])
    })

# Add all battery units
for _, row in df.iterrows():
    unit = {
        "nationalGridBmUnit": str(row['nationalGridBmUnit']) if pd.notna(row['nationalGridBmUnit']) else None,
        "elexonBmUnit": str(row['elexonBmUnit']) if pd.notna(row['elexonBmUnit']) else None,
        "leadPartyName": str(row['leadPartyName']) if pd.notna(row['leadPartyName']) else None,
        "leadPartyId": str(row['leadPartyId']) if pd.notna(row['leadPartyId']) else None,
        "fuelType": str(row['fuelType']) if pd.notna(row['fuelType']) else None,
        "generationCapacity": float(row['generationCapacity']) if pd.notna(row['generationCapacity']) else None,
        "demandCapacity": float(row['demandCapacity']) if pd.notna(row['demandCapacity']) else None,
        "bmUnitType": str(row['bmUnitType']) if pd.notna(row['bmUnitType']) else None,
        "bmUnitName": str(row['bmUnitName']) if pd.notna(row['bmUnitName']) else None,
        "gspGroupName": str(row['gspGroupName']) if pd.notna(row['gspGroupName']) else None,
        "is_vlp": bool(row['is_vlp']) if pd.notna(row['is_vlp']) else False,
        "is_vlp_by_name": bool(row['is_vlp_by_name']) if pd.notna(row['is_vlp_by_name']) else False,
        "is_aggregator_code": bool(row['is_aggregator_code']) if pd.notna(row['is_aggregator_code']) else False,
        "multiple_assets": bool(row['multiple_assets']) if pd.notna(row['multiple_assets']) else False
    }
    data['battery_units'].append(unit)

# Write to JSON file
output_file = 'vlp_battery_units_data.json'
with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f'\n✅ Created {output_file}')
print(f'📊 Total battery BMUs: {len(df)}')
print(f'🔋 VLP-operated: {len(df[df["is_vlp"] == True])} ({round(len(df[df["is_vlp"] == True]) / len(df) * 100, 1)}%)')
print(f'⚡ Direct-operated: {len(df[df["is_vlp"] == False])} ({round(len(df[df["is_vlp"] == False]) / len(df) * 100, 1)}%)')
print(f'💪 Total capacity: {df["generationCapacity"].sum():.0f} MW')
print(f'📏 File size: {Path(output_file).stat().st_size / 1024:.1f} KB')
print(f'\n🎯 Top 3 VLP operators:')
for i, op in enumerate(data['summary_statistics']['top_vlp_operators'][:3], 1):
    print(f"   {i}. {op['name']}: {op['bmu_count']} BMUs, {op['total_capacity_mw']:.0f} MW")
