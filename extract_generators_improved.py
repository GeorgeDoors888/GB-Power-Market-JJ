#!/usr/bin/env python3
"""
Better extraction of generator data with proper column identification
"""

import pandas as pd
import json
import numpy as np

def extract_generators():
    """Extract generator data with proper column mapping"""
    
    print("📊 Loading generator data...")
    
    # Load Excel - it seems to have headers in row 1 or 2
    df = pd.read_excel('All_Generators.xlsx', header=1)  # Try header in row 2
    
    print(f"✅ Loaded {len(df):,} generators")
    
    # Show actual column names
    print(f"\n📋 Column names:")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2d}. {col}")
        if i == 30:  # Show first 30
            print(f"   ... and {len(df.columns) - 30} more columns")
            break
    
    # Show first row of data
    print(f"\n📊 First generator data:")
    first_gen = df.iloc[0]
    for col in df.columns[:30]:
        val = first_gen[col]
        if pd.notna(val):
            print(f"   {col}: {val}")
    
    # Extract generators
    generators = []
    
    for idx, row in df.iterrows():
        try:
            # Get coordinates
            lat = row.get('Latitude')
            lng = row.get('Longitude')
            
            # Skip if no valid coordinates
            if pd.isna(lat) or pd.isna(lng):
                continue
            
            lat = float(lat)
            lng = float(lng)
            
            # Validate UK coordinates
            if not (49 <= lat <= 61 and -8 <= lng <= 2):
                continue
            
            # Extract other fields
            generator = {
                'lat': lat,
                'lng': lng,
                'name': '',
                'type': 'Unknown',
                'capacity': 0,
                'status': 'Unknown'
            }
            
            # Try to get name from various columns
            for col in ['Customer Site ', 'Customer Name ', 'Site Name', 'Project Name']:
                if col in df.columns and pd.notna(row.get(col)):
                    generator['name'] = str(row[col])[:100]
                    break
            
            if not generator['name']:
                generator['name'] = f"Generator {idx + 1}"
            
            # Get type
            for col in ['Primary Resource Type_Group', 'Technology Type', 'Fuel Type', 'Energy Source']:
                if col in df.columns and pd.notna(row.get(col)):
                    generator['type'] = str(row[col]).strip()
                    break
            
            # Get capacity
            for col in ['Installed Capacity', 'Capacity (MW)', 'Export Capacity (kVA)', 'Import Capacity (kVA)']:
                if col in df.columns and pd.notna(row.get(col)):
                    try:
                        cap = float(row[col])
                        # Convert kVA to MW if needed
                        if 'kVA' in col and cap > 100:
                            cap = cap / 1000  # kVA to MVA, roughly same as MW
                        generator['capacity'] = round(cap, 2)
                        break
                    except:
                        pass
            
            # Get status
            for col in ['Status', 'Connection Status', 'Operational Status']:
                if col in df.columns and pd.notna(row.get(col)):
                    generator['status'] = str(row[col]).strip()
                    break
            
            # Get postcode for additional info
            if 'Postcode ' in df.columns and pd.notna(row.get('Postcode ')):
                generator['postcode'] = str(row['Postcode ']).strip()
            
            generators.append(generator)
            
        except Exception as e:
            continue
    
    print(f"\n✅ Extracted {len(generators):,} generators with valid UK coordinates")
    
    # Show statistics
    if generators:
        # By type
        types = {}
        for gen in generators:
            gen_type = gen['type']
            types[gen_type] = types.get(gen_type, 0) + 1
        
        print(f"\n📊 Breakdown by type:")
        for gen_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(generators) * 100
            print(f"   {gen_type:30s}: {count:>5,} ({pct:>5.1f}%)")
        
        # By capacity
        total_capacity = sum(g['capacity'] for g in generators)
        print(f"\n⚡ Total capacity: {total_capacity:,.1f} MW")
        
        # Show sample
        print(f"\n📋 Sample generators:")
        for gen in generators[:5]:
            print(f"   {gen['name'][:40]:40s} | {gen['type']:20s} | {gen['capacity']:>6.1f} MW | ({gen['lat']:.4f}, {gen['lng']:.4f})")
    
    # Save full dataset
    output_file = 'generators.json'
    with open(output_file, 'w') as f:
        json.dump(generators, f, indent=2)
    
    print(f"\n✅ Generated {output_file}")
    print(f"   Size: {len(json.dumps(generators)) / 1024:.1f} KB")
    
    return generators

if __name__ == '__main__':
    extract_generators()
