import os
import requests
import pandas as pd
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()

BMRS_API_KEY = os.getenv("BMRS_API_KEY")

def analyze_endpoint_data(url, params, endpoint_name):
    """Analyze the actual data content from an endpoint"""
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.ok:
            response_data = r.json()
            data = response_data.get("data", [])
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                
                # Get sample data and column info
                sample_record = data[0] if data else {}
                
                return {
                    'success': True,
                    'rows': len(df),
                    'columns': list(df.columns),
                    'sample_data': sample_record,
                    'data_types': df.dtypes.to_dict() if not df.empty else {},
                    'date_range': {
                        'start': df.iloc[0].get('startTime') if 'startTime' in df.columns and not df.empty else None,
                        'end': df.iloc[-1].get('startTime') if 'startTime' in df.columns and not df.empty else None
                    }
                }
        return {'success': False, 'error': f"HTTP {r.status_code}"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def test_specific_data_types(start_date, end_date, period_name):
    """Test for specific data types: bids/offers, acceptances, frequency, temperature"""
    
    print(f"🔍 ANALYZING DATA TYPES FOR {period_name} ({start_date} to {end_date})")
    print("=" * 80)
    
    params = {"from": start_date, "to": end_date, "apiKey": BMRS_API_KEY, "format": "json"}
    
    # Test specific endpoints for the data types requested
    endpoints_to_test = {
        "📊 BIDS & OFFERS": {
            "BID_OFFER": "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer",
            "BID_OFFER_ALL": "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer/all",
        },
        "✅ ACCEPTANCES": {
            "ACCEPTANCES": "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances",
            "ACCEPTANCES_ALL": "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances/all",
        },
        "📈 FREQUENCY": {
            "FREQUENCY": "https://data.elexon.co.uk/bmrs/api/v1/system/frequency",
        },
        "🌡️ TEMPERATURE": {
            "TEMPERATURE": "https://data.elexon.co.uk/bmrs/api/v1/datasets/TEMP",  # Common temperature dataset
        },
        "⚡ DEMAND": {
            "DEMAND": "https://data.elexon.co.uk/bmrs/api/v1/demand",
            "ROLLING_DEMAND": "https://data.elexon.co.uk/bmrs/api/v1/demand/rollingSystemDemand",
        },
        "🔥 FUEL/GENERATION": {
            "FUELHH": "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH",
            "GENERATION_OUTTURN": "https://data.elexon.co.uk/bmrs/api/v1/generation/outturn",
        },
        "💰 PRICING": {
            "MARKET_INDEX": "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index",
        }
    }
    
    results = {}
    
    for category, endpoints in endpoints_to_test.items():
        print(f"\n{category}")
        print("-" * 60)
        
        category_results = {}
        
        for name, url in endpoints.items():
            print(f"Testing {name}...")
            result = analyze_endpoint_data(url, params, name)
            category_results[name] = result
            
            if result['success']:
                print(f"  ✅ SUCCESS: {result['rows']} rows")
                print(f"  📋 Columns: {result['columns'][:5]}{'...' if len(result['columns']) > 5 else ''}")
                
                # Show sample data for key fields
                sample = result['sample_data']
                if sample:
                    # Look for key fields
                    key_fields = ['price', 'bidPrice', 'offerPrice', 'acceptanceNumber', 'frequency', 'temperature', 'demand', 'generation']
                    found_fields = {k: v for k, v in sample.items() if any(field.lower() in k.lower() for field in key_fields)}
                    if found_fields:
                        print(f"  🔑 Key data fields: {found_fields}")
                
                # Show date range if available
                if result['date_range']['start']:
                    print(f"  📅 Data range: {result['date_range']['start']} to {result['date_range']['end']}")
            else:
                print(f"  ❌ FAILED: {result['error']}")
            
            print()
        
        results[category] = category_results
    
    return results

def compare_periods():
    """Compare data availability between 2017 and 2025"""
    
    print("🕰️  ELEXON API DATA TYPE ANALYSIS")
    print("=" * 80)
    print("Comparing data availability between 2017 and 2025...")
    print()
    
    # Test 2017 data
    results_2017 = test_specific_data_types("2017-08-01", "2017-08-08", "2017 HISTORICAL")
    
    print("\n" + "=" * 80)
    print()
    
    # Test 2025 data  
    results_2025 = test_specific_data_types("2025-08-01", "2025-08-08", "2025 CURRENT")
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("📊 SUMMARY COMPARISON")
    print("=" * 80)
    
    for category in results_2017.keys():
        print(f"\n{category}")
        print("-" * 40)
        
        for endpoint in results_2017[category].keys():
            result_2017 = results_2017[category][endpoint]
            result_2025 = results_2025[category][endpoint]
            
            status_2017 = "✅" if result_2017['success'] else "❌"
            status_2025 = "✅" if result_2025['success'] else "❌"
            
            rows_2017 = result_2017.get('rows', 0) if result_2017['success'] else 0
            rows_2025 = result_2025.get('rows', 0) if result_2025['success'] else 0
            
            print(f"{endpoint}:")
            print(f"  2017: {status_2017} {rows_2017:,} rows")
            print(f"  2025: {status_2025} {rows_2025:,} rows")
            
            if result_2017['success'] and result_2025['success']:
                change = ((rows_2025 - rows_2017) / rows_2017 * 100) if rows_2017 > 0 else 0
                if change > 0:
                    print(f"  📈 Data volume increased by {change:.1f}%")
                elif change < 0:
                    print(f"  📉 Data volume decreased by {abs(change):.1f}%")
                else:
                    print(f"  ➡️  Data volume unchanged")
    
    return results_2017, results_2025

if __name__ == "__main__":
    results_2017, results_2025 = compare_periods()
