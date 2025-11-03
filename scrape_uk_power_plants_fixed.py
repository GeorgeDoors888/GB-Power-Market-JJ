#!/usr/bin/env python3
"""
Scrape ALL UK power plant data from electricityproduction.uk
Fixed version that correctly extracts:
- Plant names from titles
- Coordinates from meta tags
- All 14 pages (2751 plants)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import re

def get_all_plant_urls():
    """Get ALL plant URLs from all 14 pages"""
    
    print("🔍 Scraping UK Power Plants from electricityproduction.uk\n")
    print("="*90)
    
    base_url = "https://electricityproduction.uk"
    plant_urls = set()
    
    # Loop through all 14 pages
    for page in range(1, 15):
        if page == 1:
            page_url = f"{base_url}/plant/"
        else:
            page_url = f"{base_url}/plant/?page={page}"
        
        print(f"📥 Fetching page {page}/14...", end=' ')
        
        try:
            response = requests.get(page_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all plant links in the table
            # They're in format: <a href="/plant/GBR1000372/">Pembroke</a>
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/plant/') and href != '/plant/' and '/owner/' not in href:
                    # Extract plant ID (e.g., /plant/GBR1000372/)
                    parts = href.strip('/').split('/')
                    if len(parts) == 2 and parts[0] == 'plant':
                        plant_id = parts[1]
                        # Exclude category pages
                        if plant_id not in ['gas', 'coal', 'wind', 'solar', 'nuclear', 'hydro', 
                                           'biomass', 'oil', 'waste', 'map']:
                            full_url = f"{base_url}{href}"
                            plant_urls.add(full_url)
            
            print(f"{len(plant_urls)} plants total")
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            continue
    
    print(f"\n✅ Found {len(plant_urls)} unique plant URLs\n")
    return list(plant_urls)


def scrape_plant_details(plant_url):
    """Scrape details from individual plant page"""
    
    try:
        response = requests.get(plant_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract plant name from page title (format: "Pembroke - UK Electricity Production")
        title = soup.find('title')
        plant_name = None
        if title:
            title_text = title.get_text()
            plant_name = title_text.split(' - ')[0].strip()
        
        plant_data = {
            'name': plant_name,
            'url': plant_url,
            'plant_id': plant_url.split('/')[-2] if plant_url.endswith('/') else plant_url.split('/')[-1],
            'capacity_mw': None,
            'fuel': None,
            'owner': None,
            'latitude': None,
            'longitude': None,
            'utilisation_pct': None
        }
        
        # Extract coordinates from meta tags
        # <meta name="geo.position" content="51.6850;-4.9900">
        geo_position = soup.find('meta', attrs={'name': 'geo.position'})
        if geo_position and geo_position.get('content'):
            coords = geo_position['content'].split(';')
            if len(coords) == 2:
                try:
                    plant_data['latitude'] = float(coords[0])
                    plant_data['longitude'] = float(coords[1])
                except:
                    pass
        
        # Extract data from definition lists (dt/dd pairs)
        for dt in soup.find_all('dt'):
            dd = dt.find_next_sibling('dd')
            if dd:
                key = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)
                
                if 'capacity' in key:
                    # Extract number from capacity (format: "2180.0 MW")
                    match = re.search(r'([\d,]+\.?\d*)', value)
                    if match:
                        plant_data['capacity_mw'] = float(match.group(1).replace(',', ''))
                
                elif 'fuel' in key:
                    plant_data['fuel'] = value
                
                elif 'owner' in key:
                    # Get text content, not link
                    plant_data['owner'] = value
                
                elif 'utilisation' in key or 'utilization' in key:
                    # Extract percentage (format: "10.7% (233.9 MW)")
                    match = re.search(r'([\d.]+)%', value)
                    if match:
                        plant_data['utilisation_pct'] = float(match.group(1))
        
        return plant_data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500:
            return 'server_error'
        raise
    except Exception as e:
        print(f"\n  ⚠️ Error scraping {plant_url}: {e}")
        return None


def main():
    """Main scraping function"""
    
    # Get all plant URLs
    plant_urls = get_all_plant_urls()
    
    if not plant_urls:
        print("❌ No plants found!")
        return
    
    print(f"📊 Scraping details for {len(plant_urls)} plants...")
    print("="*90)
    
    all_plant_data = []
    server_errors = []
    
    for i, url in enumerate(plant_urls, 1):
        # Show progress
        plant_id = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        print(f"\r{i}/{len(plant_urls)}: {plant_id:<30}", end='', flush=True)
        
        result = scrape_plant_details(url)
        
        if result == 'server_error':
            server_errors.append(url)
            print(f"\r{i}/{len(plant_urls)}: {plant_id:<30} ⚠️ Server Error (500)", flush=True)
        elif result:
            all_plant_data.append(result)
        
        # Be polite - rate limiting
        time.sleep(0.3)
    
    print(f"\n\n✅ Scraped {len(all_plant_data)} plants successfully")
    
    if server_errors:
        print(f"⚠️  {len(server_errors)} server errors (500)")
    
    if all_plant_data:
        # Convert to DataFrame
        df = pd.DataFrame(all_plant_data)
        
        # Save as CSV
        df.to_csv('uk_power_plants_cva_complete.csv', index=False)
        print(f"\n✅ Saved to uk_power_plants_cva_complete.csv")
        
        # Save as JSON
        with open('uk_power_plants_cva_complete.json', 'w') as f:
            json.dump(all_plant_data, f, indent=2)
        print(f"✅ Saved to uk_power_plants_cva_complete.json")
        
        # Show summary statistics
        print(f"\n📊 Summary:")
        print(f"   Total plants: {len(df)}")
        print(f"   With coordinates: {df['latitude'].notna().sum()}")
        print(f"   With capacity: {df['capacity_mw'].notna().sum()}")
        print(f"   With fuel type: {df['fuel'].notna().sum()}")
        
        # Capacity stats
        if df['capacity_mw'].notna().sum() > 0:
            print(f"\n   Total capacity: {df['capacity_mw'].sum():.1f} MW ({df['capacity_mw'].sum()/1000:.1f} GW)")
            print(f"   Largest plant: {df.loc[df['capacity_mw'].idxmax(), 'name']} ({df['capacity_mw'].max():.1f} MW)")
            print(f"   Smallest plant: {df.loc[df['capacity_mw'].idxmin(), 'name']} ({df['capacity_mw'].min():.1f} MW)")
        
        # Fuel type breakdown
        if df['fuel'].notna().sum() > 0:
            print(f"\n   Plants by fuel type:")
            fuel_counts = df['fuel'].value_counts()
            for fuel, count in fuel_counts.head(10).items():
                print(f"     {fuel}: {count}")
        
        # Sample plants with coordinates
        print(f"\n   Sample plants with coordinates:")
        sample = df[df['latitude'].notna()].head(10)
        print(sample[['name', 'fuel', 'capacity_mw', 'latitude', 'longitude']].to_string())
    
    else:
        print("\n❌ No data scraped.")


if __name__ == '__main__':
    main()
