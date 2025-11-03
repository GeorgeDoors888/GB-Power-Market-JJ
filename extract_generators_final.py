#!/usr/bin/env python3
"""
Extract generator data and convert British National Grid to WGS84
"""

import pandas as pd
import json
from pyproj import Transformer

def extract_generators():
    """Extract generator data with coordinate conversion"""
    
    print("📊 Loading generator data...")
    
    # Load Excel with proper header row
    df = pd.read_excel('All_Generators.xlsx', header=1)
    
    print(f"✅ Loaded {len(df):,} generators")
    print(f"   Columns: {len(df.columns)}")
    
    # Setup coordinate transformer: British National Grid (EPSG:27700) to WGS84 (EPSG:4326)
    transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    
    print(f"\n🔄 Converting British National Grid to WGS84...")
    
    generators = []
    conversion_errors = 0
    no_coords = 0
    
    # Column name mapping
    eastings_col = 'Location (X-coordinate):\nEastings (where data is held)'
    northings_col = 'Location (y-coordinate):\nNorthings (where data is held)'
    
    for idx, row in df.iterrows():
        try:
            # Get British National Grid coordinates
            easting = row.get(eastings_col)
            northing = row.get(northings_col)
            
            if pd.isna(easting) or pd.isna(northing):
                no_coords += 1
                continue
            
            # Convert to float
            easting = float(easting)
            northing = float(northing)
            
            # Skip invalid coordinates (outside GB)
            if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
                conversion_errors += 1
                continue
            
            # Transform to WGS84
            lng, lat = transformer.transform(easting, northing)
            
            # Validate result (should be in UK)
            if not (49 <= lat <= 61 and -8 <= lng <= 2):
                conversion_errors += 1
                continue
            
            # Build generator object
            generator = {
                'lat': round(lat, 6),
                'lng': round(lng, 6),
                'name': '',
                'type': 'Unknown',
                'capacity': 0,
                'status': 'Operational',
                'source': 'Unknown'
            }
            
            # Get site name
            site = row.get('Customer Site ')
            if pd.notna(site):
                generator['name'] = str(site)[:80].strip()
            else:
                customer = row.get('Customer Name ')
                if pd.notna(customer):
                    generator['name'] = str(customer)[:80].strip()
                else:
                    generator['name'] = f"Site {idx + 1}"
            
            # Get energy source
            source1 = row.get('Energy Source 1')
            if pd.notna(source1):
                generator['source'] = str(source1).strip()
                # Map to simpler types
                source_lower = generator['source'].lower()
                if 'solar' in source_lower:
                    generator['type'] = 'Solar'
                elif 'wind' in source_lower:
                    generator['type'] = 'Wind'
                elif 'storage' in source_lower or 'battery' in source_lower:
                    generator['type'] = 'Storage'
                elif 'gas' in source_lower:
                    generator['type'] = 'Gas'
                elif 'biomass' in source_lower or 'biogas' in source_lower:
                    generator['type'] = 'Biomass'
                elif 'hydro' in source_lower:
                    generator['type'] = 'Hydro'
                elif 'coal' in source_lower:
                    generator['type'] = 'Coal'
                elif 'nuclear' in source_lower:
                    generator['type'] = 'Nuclear'
                else:
                    generator['type'] = generator['source']
            
            # Get capacity
            capacity_col = 'Energy Source & Energy Conversion Technology 1 - Registered Capacity (MW)'
            capacity = row.get(capacity_col)
            if pd.notna(capacity):
                try:
                    generator['capacity'] = round(float(capacity), 3)
                except:
                    pass
            
            # Get postcode
            postcode = row.get('Postcode ')
            if pd.notna(postcode):
                generator['postcode'] = str(postcode).strip()
            
            # Get GSP
            gsp = row.get('Grid Supply Point')
            if pd.notna(gsp):
                generator['gsp'] = str(gsp).strip()
            
            # Get license area (DNO)
            license_area = row.get('Licence Area ')
            if pd.notna(license_area):
                generator['dno'] = str(license_area).strip()
            
            generators.append(generator)
            
        except Exception as e:
            conversion_errors += 1
            continue
    
    print(f"\n✅ Extracted {len(generators):,} generators with valid coordinates")
    print(f"   ⚠️  Skipped {no_coords:,} without coordinates")
    print(f"   ⚠️  Skipped {conversion_errors:,} with invalid/out-of-range coordinates")
    
    # Statistics
    if generators:
        # By type
        types = {}
        for gen in generators:
            gen_type = gen['type']
            types[gen_type] = types.get(gen_type, 0) + 1
        
        print(f"\n📊 Breakdown by type:")
        for gen_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:15]:
            pct = count / len(generators) * 100
            print(f"   {gen_type:25s}: {count:>5,} ({pct:>5.1f}%)")
        
        # Total capacity
        total_capacity = sum(g['capacity'] for g in generators)
        print(f"\n⚡ Total registered capacity: {total_capacity:,.1f} MW")
        
        # By DNO
        dnos = {}
        for gen in generators:
            dno = gen.get('dno', 'Unknown')
            dnos[dno] = dnos.get(dno, 0) + 1
        
        print(f"\n🏢 Breakdown by DNO:")
        for dno, count in sorted(dnos.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = count / len(generators) * 100
            print(f"   {dno:40s}: {count:>5,} ({pct:>5.1f}%)")
        
        # Sample
        print(f"\n📋 Sample generators:")
        for gen in generators[:10]:
            print(f"   {gen['name'][:35]:35s} | {gen['type']:12s} | {gen['capacity']:>7.2f} MW | {gen.get('postcode', 'N/A'):8s}")
    
    # Save
    output_file = 'generators.json'
    with open(output_file, 'w') as f:
        json.dump(generators, f, indent=2)
    
    print(f"\n✅ Saved to {output_file}")
    print(f"   File size: {len(json.dumps(generators)) / 1024:.1f} KB")
    
    return generators

if __name__ == '__main__':
    extract_generators()
