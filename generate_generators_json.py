#!/usr/bin/env python3
"""
Generate JSON file with generator data for map markers
"""

import pandas as pd
import json
import numpy as np

def generate_generators_json():
    """Convert generators Excel to JSON for web map"""
    
    print("📊 Loading generator data...")
    
    # Load the Excel file
    df = pd.read_excel('All_Generators.xlsx')
    
    print(f"✅ Loaded {len(df):,} generators")
    print(f"   Columns: {len(df.columns)}")
    
    # Show column names to understand the data
    print(f"\n📋 Available columns:")
    for i, col in enumerate(df.columns[:20], 1):  # Show first 20
        print(f"   {i}. {col}")
    
    # Look for coordinate columns
    coord_cols = [col for col in df.columns if any(x in col.lower() for x in ['lat', 'lon', 'lng', 'coord', 'location'])]
    print(f"\n🗺️  Coordinate columns found: {coord_cols}")
    
    # Look for key columns
    print(f"\n🔍 Looking for key columns...")
    name_cols = [col for col in df.columns if any(x in col.lower() for x in ['name', 'site', 'project'])]
    type_cols = [col for col in df.columns if any(x in col.lower() for x in ['type', 'technology', 'fuel', 'energy'])]
    capacity_cols = [col for col in df.columns if any(x in col.lower() for x in ['capacity', 'mw', 'power', 'size'])]
    status_cols = [col for col in df.columns if any(x in col.lower() for x in ['status', 'operational', 'commissioned'])]
    
    print(f"   Name columns: {name_cols[:3]}")
    print(f"   Type columns: {type_cols[:3]}")
    print(f"   Capacity columns: {capacity_cols[:3]}")
    print(f"   Status columns: {status_cols[:3]}")
    
    # Sample the data
    print(f"\n📊 Sample data (first generator):")
    for col in df.columns[:15]:
        print(f"   {col}: {df[col].iloc[0]}")
    
    # Try to identify the right columns
    # Based on typical UK generator data structure
    generators = []
    
    # Map column names (adjust based on actual column names)
    for idx, row in df.iterrows():
        try:
            # Try to extract data - adjust column names based on actual structure
            generator = {}
            
            # Get all column values for inspection
            for col in df.columns:
                val = row[col]
                if pd.notna(val):
                    # Check if this might be coordinates
                    if isinstance(val, (int, float)):
                        if 49 <= val <= 61 and 'lat' not in generator:
                            generator['lat'] = float(val)
                        elif -8 <= val <= 2 and 'lng' not in generator:
                            generator['lng'] = float(val)
            
            # Only add if we have coordinates
            if 'lat' in generator and 'lng' in generator:
                # Try to get other fields
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val):
                        if any(x in col.lower() for x in ['name', 'site']) and 'name' not in generator:
                            generator['name'] = str(val)[:100]  # Limit length
                        elif any(x in col.lower() for x in ['type', 'technology', 'fuel']) and 'type' not in generator:
                            generator['type'] = str(val)
                        elif any(x in col.lower() for x in ['capacity', 'mw']) and 'capacity' not in generator:
                            try:
                                generator['capacity'] = float(val)
                            except:
                                pass
                        elif any(x in col.lower() for x in ['status']) and 'status' not in generator:
                            generator['status'] = str(val)
                
                # Set defaults if missing
                if 'name' not in generator:
                    generator['name'] = f"Generator {idx + 1}"
                if 'type' not in generator:
                    generator['type'] = "Unknown"
                if 'capacity' not in generator:
                    generator['capacity'] = 0
                if 'status' not in generator:
                    generator['status'] = "Unknown"
                
                generators.append(generator)
        except Exception as e:
            continue
    
    print(f"\n✅ Extracted {len(generators):,} generators with coordinates")
    
    # Show breakdown by type
    if generators:
        types = {}
        for gen in generators:
            gen_type = gen['type']
            types[gen_type] = types.get(gen_type, 0) + 1
        
        print(f"\n📊 Breakdown by type:")
        for gen_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {gen_type:30s}: {count:>5,} ({count/len(generators)*100:.1f}%)")
    
    # Save to JSON
    output_file = 'generators.json'
    with open(output_file, 'w') as f:
        json.dump(generators, f, indent=2)
    
    print(f"\n✅ Generated {output_file}")
    print(f"   File size: {len(json.dumps(generators)) / 1024 / 1024:.2f} MB")
    
    # Also create a smaller sample for testing (first 100 of each type)
    sample_generators = []
    type_counts = {}
    for gen in generators:
        gen_type = gen['type']
        if type_counts.get(gen_type, 0) < 100:
            sample_generators.append(gen)
            type_counts[gen_type] = type_counts.get(gen_type, 0) + 1
    
    sample_file = 'generators_sample.json'
    with open(sample_file, 'w') as f:
        json.dump(sample_generators, f, indent=2)
    
    print(f"\n✅ Generated {sample_file} (sample for testing)")
    print(f"   Contains {len(sample_generators):,} generators")

if __name__ == '__main__':
    generate_generators_json()
