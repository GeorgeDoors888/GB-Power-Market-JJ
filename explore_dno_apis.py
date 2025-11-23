#!/usr/bin/env python3
"""
Explore UK Power Networks and other DNO open data APIs
Document available datasets and data access patterns
"""

import requests
import json
import pandas as pd
from typing import Dict, List, Optional

# DNO Open Data APIs
DNO_APIS = {
    "UKPN": {
        "name": "UK Power Networks",
        "regions": ["London", "South East", "Eastern"],
        "api_base": "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1",
        "console": "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/console",
        "datasets_endpoint": "/catalog/datasets"
    },
    "NGED": {
        "name": "National Grid Electricity Distribution",
        "regions": ["South West", "South Wales", "West Midlands", "East Midlands"],
        "api_base": "https://connecteddata.nationalgrid.co.uk/api/explore/v2.1",
        "datasets_endpoint": "/catalog/datasets"
    },
    "SSEN": {
        "name": "Scottish and Southern Electricity Networks",
        "regions": ["Scottish Hydro", "Southern England"],
        "api_base": "https://data.ssen.co.uk/api/explore/v2.1",
        "datasets_endpoint": "/catalog/datasets"
    },
    "NPG": {
        "name": "Northern Powergrid",
        "regions": ["Yorkshire", "North East"],
        "api_base": "https://northernpowergrid.opendatasoft.com/api/explore/v2.1",
        "datasets_endpoint": "/catalog/datasets"
    },
    "ENWL": {
        "name": "Electricity North West",
        "regions": ["North West England"],
        "api_base": "https://www.enwl.co.uk/opendata/api/explore/v2.1",
        "datasets_endpoint": "/catalog/datasets"
    },
    "SPEN": {
        "name": "SP Energy Networks",
        "regions": ["Central Scotland", "Merseyside", "Cheshire", "North Wales"],
        "api_base": "https://www.spenergynetworks.co.uk/opendata/api/explore/v2.1",
        "datasets_endpoint": "/catalog/datasets"
    }
}


def explore_api(dno_code: str, api_config: Dict) -> Optional[Dict]:
    """Explore a DNO's open data API"""
    print(f"\n{'='*80}")
    print(f"🔍 EXPLORING: {api_config['name']} ({dno_code})")
    print(f"{'='*80}")
    print(f"Regions: {', '.join(api_config['regions'])}")
    print(f"API Base: {api_config['api_base']}")
    
    # Try to fetch datasets catalog
    catalog_url = api_config['api_base'] + api_config['datasets_endpoint']
    
    try:
        print(f"\n📡 Fetching: {catalog_url}")
        response = requests.get(catalog_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_datasets = data.get('total_count', 0)
            
            print(f"✅ API ACTIVE - {total_datasets} datasets available")
            
            # Parse datasets
            datasets = []
            for ds in data.get('results', [])[:50]:  # First 50
                dataset_info = {
                    'id': ds.get('dataset_id'),
                    'title': ds.get('metas', {}).get('default', {}).get('title', 'No title'),
                    'records': ds.get('has_records', False),
                    'features': ', '.join(ds.get('features', []))
                }
                datasets.append(dataset_info)
            
            # Show relevant datasets
            print(f"\n📊 Found {len(datasets)} datasets (showing first 50):")
            
            # Filter for interesting datasets
            keywords = ['generation', 'renewable', 'wind', 'solar', 'capacity', 
                       'constraint', 'network', 'substation', 'demand', 'load']
            
            relevant = []
            for ds in datasets:
                if any(kw in ds['id'].lower() or kw in ds['title'].lower() for kw in keywords):
                    relevant.append(ds)
            
            if relevant:
                print(f"\n⭐ {len(relevant)} RELEVANT datasets:")
                for ds in relevant[:20]:
                    print(f"   • {ds['id']}")
                    print(f"     {ds['title']}")
            
            # Return full results
            return {
                'dno': dno_code,
                'status': 'active',
                'total_datasets': total_datasets,
                'datasets': datasets,
                'relevant': relevant
            }
            
        elif response.status_code == 404:
            print(f"❌ API NOT FOUND (404) - May use different URL pattern")
            return {'dno': dno_code, 'status': 'not_found'}
            
        else:
            print(f"⚠️  HTTP {response.status_code} - API may require authentication")
            return {'dno': dno_code, 'status': f'error_{response.status_code}'}
            
    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT - API not responding")
        return {'dno': dno_code, 'status': 'timeout'}
        
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Invalid URL or API offline")
        return {'dno': dno_code, 'status': 'connection_error'}
        
    except Exception as e:
        print(f"⚠️  ERROR: {str(e)}")
        return {'dno': dno_code, 'status': 'error', 'error': str(e)}


def get_ukpn_generation_data():
    """Example: Fetch generation data from UKPN API"""
    print(f"\n{'='*80}")
    print("📥 EXAMPLE: Fetching UKPN Generation Data")
    print(f"{'='*80}")
    
    # Example dataset IDs that might exist
    test_datasets = [
        'ukpn-distributed-generation',
        'ukpn-generation-availability',
        'ukpn-renewable-generation',
        'generation-register',
        'embedded-generation'
    ]
    
    base_url = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets"
    
    for dataset_id in test_datasets:
        url = f"{base_url}/{dataset_id}/records?limit=5"
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Found dataset: {dataset_id}")
                print(f"   Total records: {data.get('total_count', 0)}")
                
                # Show sample record
                if data.get('results'):
                    print(f"   Sample fields: {list(data['results'][0].keys())}")
                    
        except Exception as e:
            continue
    
    print("\n💡 To explore all UKPN datasets, visit:")
    print("   https://ukpowernetworks.opendatasoft.com/explore/")


def search_generation_datasets(dno_code: str, api_config: Dict):
    """Search for generation/wind/renewable datasets in a DNO API"""
    catalog_url = api_config['api_base'] + api_config['datasets_endpoint']
    
    try:
        response = requests.get(catalog_url, timeout=10)
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        # Search for generation-related datasets
        generation_datasets = []
        for ds in data.get('results', []):
            ds_id = ds.get('dataset_id', '').lower()
            ds_title = ds.get('metas', {}).get('default', {}).get('title', '').lower()
            
            if any(kw in ds_id or kw in ds_title for kw in [
                'generation', 'wind', 'solar', 'renewable', 'embedded', 
                'distributed', 'capacity', 'constraint'
            ]):
                generation_datasets.append({
                    'id': ds.get('dataset_id'),
                    'title': ds.get('metas', {}).get('default', {}).get('title'),
                    'records': ds.get('has_records')
                })
        
        return generation_datasets
        
    except Exception as e:
        return []


def main():
    print("="*80)
    print("DNO OPEN DATA API EXPLORER")
    print("="*80)
    print("\nExploring all UK DNO open data APIs...")
    print("Looking for generation, wind, solar, and capacity data")
    
    results = {}
    
    # Explore each DNO API
    for dno_code, api_config in DNO_APIS.items():
        result = explore_api(dno_code, api_config)
        results[dno_code] = result
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print(f"{'='*80}")
    
    active_apis = [dno for dno, res in results.items() if res and res.get('status') == 'active']
    print(f"\n✅ Active APIs: {len(active_apis)} / {len(DNO_APIS)}")
    for dno in active_apis:
        res = results[dno]
        print(f"   • {dno}: {res.get('total_datasets', 0)} datasets, {len(res.get('relevant', []))} relevant")
    
    inactive_apis = [dno for dno, res in results.items() if not res or res.get('status') != 'active']
    if inactive_apis:
        print(f"\n❌ Inactive/Inaccessible APIs: {len(inactive_apis)}")
        for dno in inactive_apis:
            status = results[dno].get('status', 'unknown') if results[dno] else 'unknown'
            print(f"   • {dno}: {status}")
    
    # Next steps
    print(f"\n{'='*80}")
    print("📝 NEXT STEPS")
    print(f"{'='*80}")
    print("\n1. For each active API, browse the web interface:")
    for dno in active_apis:
        api_config = DNO_APIS[dno]
        web_url = api_config['api_base'].replace('/api/explore/v2.1', '/explore/')
        print(f"   {dno}: {web_url}")
    
    print("\n2. Search for specific datasets:")
    print("   - Distributed Generation Register")
    print("   - Embedded Generation")
    print("   - Renewable Capacity")
    print("   - Network Constraints")
    print("   - Load/Demand Data")
    
    print("\n3. Example API queries:")
    print("   # List all datasets")
    print("   GET https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets")
    print("\n   # Get records from a dataset")
    print("   GET https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/DATASET_ID/records?limit=100")
    
    # Example UKPN data fetch
    get_ukpn_generation_data()
    
    # Save results
    output_file = f"dno_api_exploration_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
