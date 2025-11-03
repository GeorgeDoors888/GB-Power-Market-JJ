#!/usr/bin/env python3
"""
Generate JSON file with CVA plants for map display
"""

import json
import os

def generate_cva_map_json():
    """Convert CVA plants data to map-ready JSON format"""
    
    input_file = "cva_plants_data.json"
    output_file = "cva_plants_map.json"
    
    print("🗺️  Generating CVA Plants Map Data")
    print("="*90)
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print(f"   Waiting for scraping to complete...")
        return
    
    # Load scraped data
    print(f"📂 Loading {input_file}...")
    with open(input_file, 'r') as f:
        plants = json.load(f)
    
    print(f"✅ Loaded {len(plants)} plants")
    
    # Filter and format for map
    map_plants = []
    
    for plant in plants:
        # Only include plants with coordinates
        if 'lat' not in plant or 'lng' not in plant:
            continue
        
        # Format for map display
        map_plant = {
            'lat': plant['lat'],
            'lng': plant['lng'],
            'name': plant.get('name', 'Unknown Plant'),
            'type': 'CVA',  # Mark as CVA site
            'capacity': plant.get('capacity_mw', 0),
            'fuel_type': plant.get('fuel_type', 'Unknown'),
            'status': plant.get('status', 'Unknown'),
            'operator': plant.get('operator', ''),
            'plant_id': plant.get('plant_id', ''),
            'source': 'electricityproduction.uk'
        }
        
        # Standardize fuel type for color coding
        fuel = map_plant['fuel_type'].upper()
        if 'WIND' in fuel:
            map_plant['type_category'] = 'Wind'
        elif 'SOLAR' in fuel or 'PHOTOVOLTAIC' in fuel:
            map_plant['type_category'] = 'Solar'
        elif 'GAS' in fuel or 'CCGT' in fuel or 'OCGT' in fuel:
            map_plant['type_category'] = 'Gas'
        elif 'COAL' in fuel:
            map_plant['type_category'] = 'Coal'
        elif 'NUCLEAR' in fuel:
            map_plant['type_category'] = 'Nuclear'
        elif 'HYDRO' in fuel or 'PUMPED' in fuel:
            map_plant['type_category'] = 'Hydro'
        elif 'BIOMASS' in fuel or 'BIOGAS' in fuel:
            map_plant['type_category'] = 'Biomass'
        elif 'STORAGE' in fuel or 'BATTERY' in fuel:
            map_plant['type_category'] = 'Storage'
        else:
            map_plant['type_category'] = 'Other'
        
        map_plants.append(map_plant)
    
    print(f"✅ Prepared {len(map_plants)} plants for map")
    
    # Statistics
    print(f"\n📊 CVA Plants Statistics:")
    print("-"*90)
    
    # By fuel type
    fuel_types = {}
    for plant in map_plants:
        cat = plant['type_category']
        fuel_types[cat] = fuel_types.get(cat, 0) + 1
    
    print(f"\n📈 By Type:")
    for fuel_type, count in sorted(fuel_types.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(map_plants) * 100
        print(f"   {fuel_type:<20}: {count:>5,} ({pct:>5.1f}%)")
    
    # By capacity
    with_capacity = [p for p in map_plants if p['capacity'] > 0]
    total_capacity = sum(p['capacity'] for p in with_capacity)
    
    print(f"\n⚡ Capacity:")
    print(f"   Plants with capacity data: {len(with_capacity):,}")
    print(f"   Total capacity: {total_capacity:,.0f} MW")
    if len(with_capacity) > 0:
        print(f"   Average capacity: {total_capacity / len(with_capacity):,.1f} MW")
    
    # By status
    statuses = {}
    for plant in map_plants:
        status = plant['status']
        statuses[status] = statuses.get(status, 0) + 1
    
    print(f"\n📋 By Status:")
    for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {status:<30}: {count:>5,}")
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(map_plants, f, indent=2)
    
    print(f"\n✅ Saved {len(map_plants)} plants to {output_file}")
    print(f"   File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    return map_plants

if __name__ == '__main__':
    plants = generate_cva_map_json()
