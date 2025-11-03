#!/usr/bin/env python3
"""
Optimized scraper for electricityproduction.uk with progress tracking
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os

def scrape_all_plants_optimized():
    """Scrape all plants with progress tracking and checkpointing"""
    
    base_url = "https://electricityproduction.uk"
    output_file = "cva_plants_data.json"
    checkpoint_file = "scraping_progress.txt"
    
    print("🔋 Scraping CVA Plants from electricityproduction.uk")
    print("="*80)
    
    # Load checkpoint if exists
    scraped_ids = set()
    plants_data = []
    
    if os.path.exists(output_file):
        print(f"📂 Found existing data file, loading...")
        with open(output_file, 'r') as f:
            plants_data = json.load(f)
            scraped_ids = {p['plant_id'] for p in plants_data}
        print(f"   ✅ Loaded {len(plants_data)} existing plants")
    
    # Step 1: Get all plant IDs from table pages (fast)
    print(f"\n📋 Step 1: Collecting plant IDs from all pages...")
    all_plant_ids = []
    
    for page in range(1, 15):  # 14 pages
        try:
            url = f"{base_url}/plant/?page={page}"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all plant links in table
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/plant/GBR' in href and href not in ['/plant/']:
                    plant_id = href.strip('/').split('/')[-1]
                    if plant_id not in scraped_ids:
                        all_plant_ids.append(plant_id)
            
            print(f"   Page {page}/14: Found {len([x for x in all_plant_ids if x not in scraped_ids])} new plants")
            time.sleep(0.5)  # Be nice to the server
            
        except Exception as e:
            print(f"   ❌ Error on page {page}: {e}")
    
    total_new = len(all_plant_ids)
    print(f"\n✅ Found {total_new} new plants to scrape (plus {len(scraped_ids)} already done)")
    print(f"   Total will be: {total_new + len(scraped_ids)} plants")
    
    # Step 2: Scrape individual plant pages
    print(f"\n⚡ Step 2: Scraping individual plant details...")
    print(f"   This will take approximately {(total_new * 0.7) / 60:.1f} minutes")
    print(f"   Progress will be saved every 50 plants")
    print()
    
    start_time = time.time()
    error_count = 0
    
    for i, plant_id in enumerate(all_plant_ids, 1):
        try:
            url = f"{base_url}/plant/{plant_id}/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data
            plant = {'plant_id': plant_id, 'url': url}
            
            # Get coordinates from meta tag
            geo_meta = soup.find('meta', {'name': 'geo.position'})
            if geo_meta:
                coords = geo_meta['content'].split(';')
                plant['lat'] = float(coords[0])
                plant['lng'] = float(coords[1])
            
            # Get plant name from title
            title = soup.find('title')
            if title:
                plant['name'] = title.text.replace(' | Electricity Production', '').strip()
            
            # Get capacity and fuel type from table
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if 'Installed Capacity' in label:
                        # Extract MW value
                        if 'MW' in value:
                            plant['capacity_mw'] = float(value.replace('MW', '').replace(',', '').strip())
                    elif 'Technology' in label or 'Fuel' in label:
                        plant['fuel_type'] = value
                    elif 'Status' in label:
                        plant['status'] = value
                    elif 'Company' in label or 'Operator' in label:
                        plant['operator'] = value
            
            plants_data.append(plant)
            
            # Progress update
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (total_new - i) / rate if rate > 0 else 0
            
            if i % 10 == 0:
                print(f"   Progress: {i}/{total_new} ({i/total_new*100:.1f}%) | "
                      f"Rate: {rate:.1f} plants/sec | "
                      f"ETA: {remaining/60:.1f} min | "
                      f"Errors: {error_count}")
            
            # Save checkpoint every 50 plants
            if i % 50 == 0:
                with open(output_file, 'w') as f:
                    json.dump(plants_data, f, indent=2)
                print(f"   💾 Checkpoint saved ({len(plants_data)} plants)")
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            error_count += 1
            print(f"   ⚠️  Error on {plant_id}: {e}")
            if error_count > 50:
                print(f"\n❌ Too many errors, stopping")
                break
    
    # Final save
    with open(output_file, 'w') as f:
        json.dump(plants_data, f, indent=2)
    
    print(f"\n✅ Scraping complete!")
    print(f"   Total plants: {len(plants_data)}")
    print(f"   Errors: {error_count}")
    print(f"   Time taken: {(time.time() - start_time) / 60:.1f} minutes")
    print(f"   Saved to: {output_file}")
    
    # Show summary
    with_coords = sum(1 for p in plants_data if 'lat' in p and 'lng' in p)
    with_capacity = sum(1 for p in plants_data if 'capacity_mw' in p)
    
    print(f"\n📊 Data Quality:")
    print(f"   Plants with coordinates: {with_coords} ({with_coords/len(plants_data)*100:.1f}%)")
    print(f"   Plants with capacity: {with_capacity} ({with_capacity/len(plants_data)*100:.1f}%)")
    
    return plants_data

if __name__ == '__main__':
    plants = scrape_all_plants_optimized()
