#!/usr/bin/env python3
"""
Extract CVA sites (BMUs) from Elexon data in BigQuery
"""

from google.cloud import bigquery
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"

def extract_bmu_list():
    """Extract unique BMUs from Elexon data"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    print("🔍 Extracting CVA Sites (BMUs) from Elexon BigQuery Data\n")
    print("="*90)
    
    # Query to get unique BMUs from the output_usable table (has fuel type!)
    query = f"""
    SELECT DISTINCT
        nationalGridBmUnit,
        bmUnit,
        fuelType
    FROM `{PROJECT_ID}.{DATASET_ID}.uou2t14d_2025`
    WHERE nationalGridBmUnit IS NOT NULL
    ORDER BY nationalGridBmUnit
    """
    
    print("📊 Querying BMU data...")
    results = client.query(query).result()
    
    bmus = []
    for row in results:
        bmus.append({
            'ngc_bmu_id': row.nationalGridBmUnit,
            'bmu_id': row.bmUnit,
            'fuel_type': row.fuelType
        })
    
    print(f"✅ Found {len(bmus)} unique BMUs\n")
    
    # Group by fuel type
    fuel_types = {}
    for bmu in bmus:
        fuel = bmu['fuel_type']
        if fuel not in fuel_types:
            fuel_types[fuel] = []
        fuel_types[fuel].append(bmu)
    
    print("📈 BMUs by Fuel Type:")
    print("-"*90)
    print(f"{'Fuel Type':<30} {'Count':<10} {'% of Total':<12}")
    print("-"*90)
    
    total = len(bmus)
    for fuel, units in sorted(fuel_types.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(units)
        pct = (count / total * 100) if total > 0 else 0
        print(f"{fuel:<30} {count:>8}  {pct:>10.1f}%")
    
    print("-"*90)
    print(f"{'TOTAL':<30} {total:>8}  {100.0:>10.1f}%\n")
    
    # Show sample BMUs from each fuel type
    print("📋 Sample BMUs by Fuel Type:\n")
    for fuel, units in sorted(fuel_types.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{fuel} ({len(units)} units):")
        print("-"*90)
        for bmu in units[:5]:  # Show first 5
            ngc_id = bmu['ngc_bmu_id'] or 'N/A'
            bmu_id = bmu['bmu_id'] or 'N/A'
            print(f"   NGC ID: {ngc_id:<15} | BMU ID: {bmu_id:<15}")
        if len(units) > 5:
            print(f"   ... and {len(units) - 5} more")
    
    # Save to JSON
    output_file = 'cva_bmu_list.json'
    with open(output_file, 'w') as f:
        json.dump(bmus, f, indent=2)
    
    print(f"\n✅ Saved {len(bmus)} BMUs to {output_file}")
    
    return bmus

if __name__ == '__main__':
    bmus = extract_bmu_list()
