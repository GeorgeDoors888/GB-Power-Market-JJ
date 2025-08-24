import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

load_dotenv()

BMRS_API_KEY = os.getenv("BMRS_API_KEY")

def test_acceptances_endpoints():
    """Test different approaches to access bid/offer acceptances data"""
    
    print("🔍 TESTING BID/OFFER ACCEPTANCES ENDPOINTS")
    print("=" * 60)
    
    # Different date formats and approaches to try
    test_dates = [
        ("2025-08-01", "2025-08-08"),  # Recent data
        ("2022-06-25", "2022-06-25"),  # Date from the schema example
        ("2024-01-01", "2024-01-07"),  # Different recent period
    ]
    
    # Different endpoint variations to try
    endpoint_variations = [
        "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances",
        "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances/all", 
        "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOALF",  # BOALF is the BMRS dataset for acceptances
        "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOD",    # BOD is bid-offer data
        "https://data.elexon.co.uk/bmrs/api/v1/datasets/DISPTAV", # Dispatch acceptances
        "https://data.elexon.co.uk/bmrs/api/v1/balancing/dynamic/all", # Dynamic balancing data
    ]
    
    # Different parameter combinations
    def get_param_combinations(start_date, end_date):
        return [
            # Standard parameters
            {"from": start_date, "to": end_date, "apiKey": BMRS_API_KEY, "format": "json"},
            # Settlement date format
            {"settlementDate": end_date, "apiKey": BMRS_API_KEY, "format": "json"},
            # Date only (no time range)
            {"date": end_date, "apiKey": BMRS_API_KEY, "format": "json"},
            # Settlement period specific
            {"settlementDate": end_date, "settlementPeriod": "1", "apiKey": BMRS_API_KEY, "format": "json"},
            # BM Unit specific (try a common unit)
            {"settlementDate": end_date, "bmUnit": "T_ABRBO-1", "apiKey": BMRS_API_KEY, "format": "json"},
            # Minimal parameters
            {"apiKey": BMRS_API_KEY, "format": "json"},
        ]
    
    results = []
    
    for endpoint in endpoint_variations:
        print(f"\n📡 Testing endpoint: {endpoint}")
        print("-" * 60)
        
        for start_date, end_date in test_dates:
            print(f"\n📅 Date range: {start_date} to {end_date}")
            
            param_combinations = get_param_combinations(start_date, end_date)
            
            for i, params in enumerate(param_combinations, 1):
                try:
                    print(f"  Attempt {i}: {list(params.keys())}")
                    r = requests.get(endpoint, params=params, timeout=30)
                    print(f"    Status: {r.status_code}")
                    
                    if r.status_code == 200:
                        try:
                            response_data = r.json()
                            
                            # Check for data
                            if isinstance(response_data, dict) and "data" in response_data:
                                data = response_data["data"]
                                if isinstance(data, list) and len(data) > 0:
                                    print(f"    ✅ SUCCESS! Found {len(data)} records")
                                    
                                    # Analyze the structure
                                    sample = data[0]
                                    print(f"    📋 Sample keys: {list(sample.keys())[:8]}{'...' if len(sample.keys()) > 8 else ''}")
                                    
                                    # Look for key acceptance fields
                                    acceptance_fields = ['acceptanceNumber', 'acceptanceTime', 'levelFrom', 'levelTo', 'bmUnit']
                                    found_fields = {k: v for k, v in sample.items() if k in acceptance_fields}
                                    if found_fields:
                                        print(f"    🎯 Acceptance fields found: {found_fields}")
                                    
                                    # Save successful result
                                    results.append({
                                        'endpoint': endpoint,
                                        'date_range': f"{start_date} to {end_date}",
                                        'params': params,
                                        'records': len(data),
                                        'sample_data': sample,
                                        'success': True
                                    })
                                    
                                    print(f"    📊 Full sample record:")
                                    for k, v in list(sample.items())[:10]:
                                        print(f"      {k}: {v}")
                                    
                                    # Don't test more params if we found data
                                    break
                                else:
                                    print(f"    ⚠️  Empty data array")
                            else:
                                print(f"    ⚠️  Unexpected response structure: {type(response_data)}")
                                
                        except Exception as e:
                            print(f"    ❌ Parse error: {e}")
                            # Show raw response for debugging
                            print(f"    Raw response: {r.text[:200]}...")
                            
                    elif r.status_code == 404:
                        print(f"    ❌ Not found")
                    else:
                        print(f"    ❌ HTTP {r.status_code}: {r.text[:100]}...")
                        
                except Exception as e:
                    print(f"    ❌ Request error: {e}")
                
                # Small delay between requests
                time.sleep(0.5)
            
            # If we found data for this date range, move to next endpoint
            if results and results[-1]['endpoint'] == endpoint:
                break
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY OF SUCCESSFUL ENDPOINTS")
    print("=" * 60)
    
    if results:
        for result in results:
            print(f"\n✅ {result['endpoint']}")
            print(f"   📅 Date: {result['date_range']}")
            print(f"   📊 Records: {result['records']}")
            print(f"   🔧 Working params: {list(result['params'].keys())}")
    else:
        print("❌ No successful endpoints found for bid/offer acceptances data")
        print("\nPossible reasons:")
        print("• Endpoints require different authentication level")
        print("• Data might be available through BMRS datasets with different names")
        print("• Specific BM Unit or settlement period required")
        print("• Data only available for certain time periods")
    
    return results

def test_bmrs_datasets_for_acceptances():
    """Test BMRS datasets that might contain bid/offer/acceptances data"""
    
    print("\n" + "=" * 60)
    print("🗂️  TESTING BMRS DATASETS FOR BID/OFFER DATA")
    print("=" * 60)
    
    # BMRS datasets that might contain bid/offer/acceptances data
    datasets_to_test = {
        "BOALF": "Bid Offer Acceptance Level Flagged",
        "BOD": "Bid Offer Data", 
        "DISPTAV": "Dispatch Acceptances Volume",
        "EBOCF": "Energy Bid Offer Component Flagged",
        "MELNGC": "Maximum Export Limit NGC",
        "MILNGC": "Maximum Import Limit NGC",
        "DYNBMDATA": "Dynamic BM Data",
        "PHYBMDATA": "Physical BM Data",
    }
    
    params = {
        "from": "2025-08-01",
        "to": "2025-08-08", 
        "apiKey": BMRS_API_KEY,
        "format": "json"
    }
    
    successful_datasets = []
    
    for dataset_code, description in datasets_to_test.items():
        url = f"https://data.elexon.co.uk/bmrs/api/v1/datasets/{dataset_code}"
        print(f"\n📋 Testing {dataset_code}: {description}")
        
        try:
            r = requests.get(url, params=params, timeout=30)
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                try:
                    response_data = r.json()
                    data = response_data.get("data", [])
                    
                    if isinstance(data, list) and len(data) > 0:
                        print(f"   ✅ SUCCESS! {len(data)} records")
                        
                        sample = data[0]
                        print(f"   📋 Fields: {list(sample.keys())}")
                        
                        # Look for bid/offer related fields
                        bid_offer_keywords = ['bid', 'offer', 'acceptance', 'level', 'price', 'volume']
                        relevant_fields = {k: v for k, v in sample.items() 
                                         if any(keyword in k.lower() for keyword in bid_offer_keywords)}
                        
                        if relevant_fields:
                            print(f"   🎯 Bid/Offer fields: {relevant_fields}")
                            successful_datasets.append({
                                'code': dataset_code,
                                'description': description,
                                'records': len(data),
                                'relevant_fields': relevant_fields,
                                'sample': sample
                            })
                    else:
                        print(f"   ⚠️  No data returned")
                        
                except Exception as e:
                    print(f"   ❌ Parse error: {e}")
            else:
                print(f"   ❌ HTTP {r.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request error: {e}")
        
        time.sleep(0.5)
    
    return successful_datasets

if __name__ == "__main__":
    # Test acceptances endpoints
    acceptance_results = test_acceptances_endpoints()
    
    # Test BMRS datasets
    dataset_results = test_bmrs_datasets_for_acceptances()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RECOMMENDATIONS")
    print("=" * 60)
    
    if acceptance_results or dataset_results:
        print("✅ Found potential sources for bid/offer/acceptances data:")
        
        for result in acceptance_results:
            print(f"• {result['endpoint']} - {result['records']} records")
            
        for result in dataset_results:
            print(f"• Dataset {result['code']}: {result['description']} - {result['records']} records")
    else:
        print("❌ No bid/offer/acceptances data found with current API access level")
        print("💡 Consider contacting Elexon for higher-level API access")
