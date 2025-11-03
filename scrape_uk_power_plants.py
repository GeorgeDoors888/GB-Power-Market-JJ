#!/usr/bin/env python3
"""
Scrape all UK power plant data from electricityproduction.uk
This site has comprehensive CVA plant data with coordinates!
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from urllib.parse import urljoin

def get_plant_list():
    """Get list of all plants from the main page"""
    
    print("🔍 Scraping UK Power Plants from electricityproduction.uk\n")
    print("="*90)
    
    base_url = "https://electricityproduction.uk"
    plant_list_url = f"{base_url}/plant/"
    
    print(f"📥 Fetching plant list from {plant_list_url}")
    
    try:
        response = requests.get(plant_list_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all plant links
        plant_links = []
        
        # Look for plant links in the page
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Plant pages are typically /plant/plant-name/
            if '/plant/' in href and href != '/plant/':
                full_url = urljoin(base_url, href)
                plant_name = link.get_text(strip=True)
                if plant_name:
                    plant_links.append({
                        'url': full_url,
                        'name': plant_name
                    })
        
        # Remove duplicates
        unique_plants = {}
        for plant in plant_links:
            unique_plants[plant['url']] = plant['name']
        
        print(f"✅ Found {len(unique_plants)} unique plant URLs")
        
        return list(unique_plants.items())
        
    except Exception as e:
        print(f"❌ Error fetching plant list: {e}")
        return []

def scrape_plant_details(plant_url, plant_name):
    """Scrape details from individual plant page"""
    
    try:
        response = requests.get(plant_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        plant_data = {
            'name': plant_name,
            'url': plant_url,
            'type': None,
            'fuel': None,
            'capacity_mw': None,
            'operator': None,
            'location': None,
            'latitude': None,
            'longitude': None,
            'commissioned': None,
            'status': None
        }
        
        # Extract data from the page
        # This site typically has structured data
        
        # Try to find all dt/dd pairs (definition list)
        for dt in soup.find_all('dt'):
            dd = dt.find_next_sibling('dd')
            if dd:
                key = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)
                
                if 'type' in key or 'technology' in key:
                    plant_data['type'] = value
                elif 'fuel' in key:
                    plant_data['fuel'] = value
                elif 'capacity' in key or 'mw' in key:
                    # Extract number from capacity
                    import re
                    match = re.search(r'([\d,]+\.?\d*)', value)
                    if match:
                        plant_data['capacity_mw'] = float(match.group(1).replace(',', ''))
                elif 'operator' in key or 'owner' in key:
                    plant_data['operator'] = value
                elif 'location' in key or 'address' in key:
                    plant_data['location'] = value
                elif 'latitude' in key or 'lat' in key:
                    plant_data['latitude'] = float(value)
                elif 'longitude' in key or 'lon' in key:
                    plant_data['longitude'] = float(value)
                elif 'commissioned' in key or 'operational' in key:
                    plant_data['commissioned'] = value
                elif 'status' in key:
                    plant_data['status'] = value
        
        # Try to find coordinates in meta tags or JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                json_data = json.loads(script.string)
                if isinstance(json_data, dict):
                    if 'geo' in json_data:
                        plant_data['latitude'] = json_data['geo'].get('latitude')
                        plant_data['longitude'] = json_data['geo'].get('longitude')
            except:
                pass
        
        return plant_data
        
    except Exception as e:
        print(f"  ⚠️  Error scraping {plant_name}: {e}")
        return None

def scrape_all_plants():
    """Scrape all plants from the website"""
    
    # Get plant list
    plants = get_plant_list()
    
    if not plants:
        print("❌ No plants found. Trying alternative method...")
        # If direct scraping doesn't work, we'll need to find another way
        return []
    
    print(f"\n📊 Scraping details for {len(plants)} plants...")
    print("="*90)
    
    all_plant_data = []
    
    for i, (url, name) in enumerate(plants, 1):
        print(f"\r{i}/{len(plants)}: {name[:50]:<50}", end='', flush=True)
        
        plant_data = scrape_plant_details(url, name)
        if plant_data:
            all_plant_data.append(plant_data)
        
        # Be polite - add small delay between requests
        time.sleep(0.5)
    
    print(f"\n\n✅ Scraped {len(all_plant_data)} plants successfully")
    
    return all_plant_data

if __name__ == '__main__':
    plants_data = scrape_all_plants()
    
    if plants_data:
        # Save as CSV
        df = pd.DataFrame(plants_data)
        df.to_csv('uk_power_plants_cva.csv', index=False)
        print(f"\n✅ Saved to uk_power_plants_cva.csv")
        
        # Save as JSON
        with open('uk_power_plants_cva.json', 'w') as f:
            json.dump(plants_data, f, indent=2)
        print(f"✅ Saved to uk_power_plants_cva.json")
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"   Total plants: {len(df)}")
        print(f"   With coordinates: {df['latitude'].notna().sum()}")
        print(f"   With capacity: {df['capacity_mw'].notna().sum()}")
        
        if len(df) > 0:
            print(f"\n   Sample plants:")
            print(df[['name', 'type', 'capacity_mw', 'latitude', 'longitude']].head(10).to_string())
    else:
        print("\n❌ No data scraped. Website may have different structure.")
        print("💡 Trying alternative approach...")
