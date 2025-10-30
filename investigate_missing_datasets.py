#!/usr/bin/env python3
"""
Investigate the 12 missing datasets from Elexon API
Analyze why they failed and find alternative endpoints
"""

import httpx
import json
from datetime import datetime, timedelta

# Failed datasets from the log
FAILED_DATASETS = [
    {
        "name": "GENERATION_ACTUAL_PER_TYPE",
        "route": "/generation/actual/per-type",
        "error": "Error converting Pandas column 'data' - nested structure",
        "category": "generation"
    },
    {
        "name": "GENERATION_OUTTURN",
        "route": "/generation/outturn/summary",
        "error": "Error converting Pandas column 'data' - nested structure",
        "category": "generation"
    },
    {
        "name": "DEMAND_PEAK_INDICATIVE",
        "route": "/demand/peak/indicative/settlement",
        "error": "HTTP 404 - endpoint not found",
        "category": "demand"
    },
    {
        "name": "DEMAND_PEAK_TRIAD",
        "route": "/demand/peak/triad",
        "error": "HTTP 404 - endpoint not found",
        "category": "demand"
    },
    {
        "name": "BALANCING_PHYSICAL",
        "route": "/balancing/physical",
        "error": "HTTP 404 - endpoint not found",
        "category": "balancing"
    },
    {
        "name": "BALANCING_DYNAMIC",
        "route": "/balancing/dynamic",
        "error": "HTTP 404 - endpoint not found",
        "category": "balancing"
    },
    {
        "name": "BALANCING_DYNAMIC_RATES",
        "route": "/balancing/dynamic/rates",
        "error": "HTTP 404 - endpoint not found",
        "category": "balancing"
    },
    {
        "name": "BALANCING_BID_OFFER",
        "route": "/balancing/bid-offer",
        "error": "HTTP 404 - endpoint not found",
        "category": "balancing"
    },
    {
        "name": "BALANCING_ACCEPTANCES",
        "route": "/balancing/acceptances",
        "error": "HTTP 404 - endpoint not found",
        "category": "balancing"
    },
    {
        "name": "BALANCING_NONBM_VOLUMES",
        "route": "/balancing/nonbm/volumes",
        "error": "HTTP 400 - bad request (wrong parameters?)",
        "category": "balancing"
    },
    {
        "name": "DISBSAD",
        "route": "/datasets/DISBSAD/stream",
        "error": "Error converting Pandas column 'isTendered' - nested structure",
        "category": "balancing"
    },
    {
        "name": "SYSTEM_PRICES",
        "route": "/balancing/settlement/system-prices",
        "error": "HTTP 404 - endpoint not found",
        "category": "settlement"
    }
]

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def test_endpoint_variations(dataset):
    """Try different URL variations and parameters for a dataset"""
    print(f"\n{'='*80}")
    print(f"🔍 Testing: {dataset['name']}")
    print(f"   Category: {dataset['category']}")
    print(f"   Original error: {dataset['error']}")
    print(f"{'='*80}")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    variations = []
    
    # Original route
    variations.append({
        "name": "Original",
        "url": f"{BASE_URL}{dataset['route']}",
        "params": {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "format": "json"
        }
    })
    
    # Try without date range (for reference data)
    variations.append({
        "name": "No date range",
        "url": f"{BASE_URL}{dataset['route']}",
        "params": {"format": "json"}
    })
    
    # Try settlementDate parameter
    variations.append({
        "name": "settlementDate param",
        "url": f"{BASE_URL}{dataset['route']}",
        "params": {
            "settlementDate": end_date.strftime("%Y-%m-%d"),
            "format": "json"
        }
    })
    
    # Try dataset stream format (for BMRS datasets)
    if not dataset['route'].startswith('/datasets/'):
        dataset_code = dataset['name'].split('_')[0]
        variations.append({
            "name": "Stream format",
            "url": f"{BASE_URL}/datasets/{dataset_code}/stream",
            "params": {
                "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "to": end_date.strftime("%Y-%m-%dT23:59:59Z")
            }
        })
    
    # Test each variation
    client = httpx.Client(timeout=30.0)
    working_urls = []
    
    for i, var in enumerate(variations, 1):
        print(f"\n  {i}. Testing: {var['name']}")
        print(f"     URL: {var['url']}")
        print(f"     Params: {var['params']}")
        
        try:
            response = client.get(var['url'], params=var['params'])
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Check data structure
                    if isinstance(data, dict):
                        if 'data' in data:
                            rows = data['data']
                            print(f"     ✅ SUCCESS! Found {len(rows)} rows")
                            print(f"     📊 Sample structure:")
                            if rows and len(rows) > 0:
                                sample = rows[0]
                                print(f"        Keys: {list(sample.keys())[:10]}")
                                if 'data' in sample and isinstance(sample['data'], (list, dict)):
                                    print(f"        ⚠️  WARNING: Contains nested 'data' field")
                                    print(f"           Type: {type(sample['data'])}")
                                    if isinstance(sample['data'], list) and len(sample['data']) > 0:
                                        print(f"           Nested keys: {list(sample['data'][0].keys()) if isinstance(sample['data'][0], dict) else 'list items'}")
                            working_urls.append((var, data, None))
                        else:
                            print(f"     ⚠️  Response has no 'data' field. Keys: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"     ✅ SUCCESS! Found {len(data)} rows (direct list)")
                        if data:
                            print(f"     📊 Sample keys: {list(data[0].keys())[:10]}")
                        working_urls.append((var, data, None))
                    else:
                        print(f"     ⚠️  Unexpected response type: {type(data)}")
                        
                except json.JSONDecodeError as e:
                    print(f"     ⚠️  Response is not JSON: {str(e)[:100]}")
            elif response.status_code == 404:
                print(f"     ❌ 404 Not Found")
            elif response.status_code == 400:
                print(f"     ❌ 400 Bad Request")
                try:
                    error_data = response.json()
                    print(f"     Error details: {error_data}")
                except:
                    print(f"     Error text: {response.text[:200]}")
            else:
                print(f"     ❌ HTTP {response.status_code}")
                
        except httpx.TimeoutException:
            print(f"     ⏱️  Timeout")
        except Exception as e:
            print(f"     ❌ Error: {str(e)[:100]}")
    
    client.close()
    
    # Summary
    if working_urls:
        print(f"\n  ✅ Found {len(working_urls)} working variation(s)!")
        return working_urls
    else:
        print(f"\n  ❌ No working variations found")
        return []

def main():
    print("="*80)
    print("🔎 INVESTIGATING 12 MISSING DATASETS")
    print("="*80)
    print(f"\nTesting {len(FAILED_DATASETS)} failed datasets...")
    print(f"Date range: Last 7 days")
    
    results = {}
    
    for dataset in FAILED_DATASETS:
        working = test_endpoint_variations(dataset)
        results[dataset['name']] = {
            'dataset': dataset,
            'working_urls': working
        }
    
    # Final summary
    print("\n" + "="*80)
    print("📊 SUMMARY OF FINDINGS")
    print("="*80)
    
    still_missing = []
    found_alternatives = []
    needs_fixing = []
    
    for name, result in results.items():
        if not result['working_urls']:
            still_missing.append(name)
        else:
            has_nested = any('nested' in str(result['dataset']['error']).lower() for url in result['working_urls'])
            if has_nested or 'data' in result['dataset']['error'].lower():
                needs_fixing.append(name)
            else:
                found_alternatives.append(name)
    
    print(f"\n✅ Found working alternatives: {len(found_alternatives)}")
    for name in found_alternatives:
        print(f"   • {name}")
    
    print(f"\n⚠️  Found but need nested data handling: {len(needs_fixing)}")
    for name in needs_fixing:
        print(f"   • {name}")
    
    print(f"\n❌ Still missing (truly unavailable): {len(still_missing)}")
    for name in still_missing:
        print(f"   • {name}")
    
    # Save detailed results
    with open('missing_datasets_investigation.json', 'w') as f:
        json.dump({
            'summary': {
                'found_alternatives': found_alternatives,
                'needs_fixing': needs_fixing,
                'still_missing': still_missing
            },
            'details': {k: {'dataset': v['dataset'], 'working_count': len(v['working_urls'])} for k, v in results.items()}
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: missing_datasets_investigation.json")

if __name__ == "__main__":
    main()
