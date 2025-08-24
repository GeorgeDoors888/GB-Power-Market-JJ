import os
import requests
import pandas as pd
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import json

load_dotenv()

BMRS_API_KEY = os.getenv("BMRS_API_KEY")

def create_focused_test_config():
    """Create a focused test configuration with key endpoints from each category"""
    
    # Define key endpoints to test from each category based on the comprehensive list
    focused_config = {
        "demand": {
            "DEMAND": "https://data.elexon.co.uk/bmrs/api/v1/demand",
            "ROLLINGSYSTEMDEMAND": "https://data.elexon.co.uk/bmrs/api/v1/demand/rollingSystemDemand"
        },
        "generation_forecast": {
            "DAILY": "https://data.elexon.co.uk/bmrs/api/v1/forecast/availability/daily",
            "WEEKLY": "https://data.elexon.co.uk/bmrs/api/v1/forecast/availability/weekly"
        },
        "generation_actual": {
            "OUTTURN": "https://data.elexon.co.uk/bmrs/api/v1/generation/outturn",
            "ACTUAL_STREAMS": "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/streams"
        },
        "system": {
            "FREQUENCY": "https://data.elexon.co.uk/bmrs/api/v1/system/frequency",
            "WARNINGS": "https://data.elexon.co.uk/bmrs/api/v1/system/warnings"
        },
        "balancing_mechanism": {
            "BID_OFFER": "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer",
            "ACCEPTANCES": "https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances"
        },
        "bmrs_key_datasets": {
            "FUELHH": "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH",
            "INDO": "https://data.elexon.co.uk/bmrs/api/v1/datasets/INDO",
            "B1610": "https://data.elexon.co.uk/bmrs/api/v1/datasets/B1610"
        },
        "market_pricing": {
            "MARKET_INDEX": "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index"
        }
    }
    
    # Save focused config
    with open('config:focused_test.yml', 'w') as f:
        yaml.dump(focused_config, f, default_flow_style=False, sort_keys=True)
    
    return focused_config

def test_endpoint_advanced(category, name, url, start_date, end_date):
    """Advanced endpoint testing with better error handling and parameter detection"""
    print(f"=== Testing {category}.{name} ===")
    print(f"URL: {url}")
    
    # Try different parameter combinations
    param_combinations = [
        # Standard parameters
        {"from": start_date, "to": end_date, "apiKey": BMRS_API_KEY, "format": "json"},
        # Without date range (some endpoints don't need it)
        {"apiKey": BMRS_API_KEY, "format": "json"},
        # With settlement date instead of from/to
        {"settlementDate": end_date, "apiKey": BMRS_API_KEY, "format": "json"},
        # Minimal parameters
        {"apiKey": BMRS_API_KEY}
    ]
    
    for i, params in enumerate(param_combinations):
        try:
            print(f"  Attempt {i+1} with params: {list(params.keys())}")
            r = requests.get(url, params=params, timeout=30)
            print(f"  Status: {r.status_code}")
            
            if r.ok:
                try:
                    response_data = r.json()
                    data = None
                    
                    # Handle different response structures
                    if isinstance(response_data, dict):
                        if "data" in response_data:
                            data = response_data["data"]
                        elif "records" in response_data:
                            data = response_data["records"]
                        else:
                            # Sometimes the whole response is the data
                            data = response_data
                    elif isinstance(response_data, list):
                        data = response_data
                    
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data)
                        print(f"  ✅ Success! Rows: {len(df)}")
                        if not df.empty:
                            print(f"  📊 Columns: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")
                            print(f"  📈 Sample data shape: {df.shape}")
                        return {
                            'success': True,
                            'rows': len(df),
                            'columns': list(df.columns),
                            'attempt': i+1,
                            'params_used': params
                        }
                    else:
                        print(f"  ✅ Success! Non-tabular data: {type(data)}")
                        return {
                            'success': True,
                            'rows': 1,
                            'columns': [],
                            'attempt': i+1,
                            'params_used': params,
                            'data_type': str(type(data))
                        }
                        
                except json.JSONDecodeError:
                    print(f"  📄 Non-JSON response (might be CSV/XML)")
                    return {
                        'success': True,
                        'rows': 1,
                        'columns': [],
                        'attempt': i+1,
                        'params_used': params,
                        'content_type': r.headers.get('content-type', 'unknown')
                    }
                except Exception as e:
                    print(f"  ⚠️ Parse error: {e}")
                    continue
            else:
                print(f"  ❌ HTTP {r.status_code}: {r.text[:100] if r.text else 'No response'}")
                if i == len(param_combinations) - 1:  # Last attempt
                    return {
                        'success': False,
                        'error': f"HTTP {r.status_code}",
                        'attempts': len(param_combinations)
                    }
                    
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout on attempt {i+1}")
            continue
        except Exception as e:
            print(f"  ❌ Error on attempt {i+1}: {e}")
            continue
    
    return {
        'success': False,
        'error': "All parameter combinations failed",
        'attempts': len(param_combinations)
    }

def run_comprehensive_smoke_test():
    """Run comprehensive smoke test with advanced endpoint testing"""
    
    print("=" * 80)
    print("🚀 ELEXON INSIGHTS API - COMPREHENSIVE SMOKE TEST")
    print("=" * 80)
    
    # Create focused test configuration
    print("Creating focused test configuration...")
    config = create_focused_test_config()
    
    print(f"API Key: {'***' + BMRS_API_KEY[-4:] if BMRS_API_KEY else '❌ NOT SET'}")
    
    # Calculate date range - Using 2017 data for historical testing
    start_date = "2017-08-01"  # August 1, 2017
    end_date = "2017-08-08"    # August 8, 2017 (1 week in 2017)
    print(f"📅 Date range: {start_date} to {end_date} (Historical data from 2017)")
    print()
    
    all_results = []
    category_summary = {}
    
    for category, endpoints in config.items():
        print(f"🔍 TESTING CATEGORY: {category.upper()}")
        print("-" * 60)
        
        category_results = []
        
        for name, url in endpoints.items():
            result = test_endpoint_advanced(category, name, url, start_date, end_date)
            result['category'] = category
            result['name'] = name
            result['url'] = url
            
            category_results.append(result)
            all_results.append(result)
            
            # Respectful delay between requests
            time.sleep(2)
            print()
        
        # Category summary
        successful = sum(1 for r in category_results if r.get('success', False))
        total = len(category_results)
        total_rows = sum(r.get('rows', 0) for r in category_results if r.get('success', False))
        
        category_summary[category] = {
            'successful': successful,
            'total': total,
            'total_rows': total_rows,
            'success_rate': successful / total if total > 0 else 0
        }
        
        status_emoji = "✅" if successful == total else "⚠️" if successful > 0 else "❌"
        print(f"{status_emoji} {category.upper()} SUMMARY: {successful}/{total} successful ({successful/total:.1%})")
        print(f"📊 Total rows: {total_rows}")
        print("=" * 60)
        print()
    
    # Final summary
    print("🏁 FINAL RESULTS")
    print("=" * 80)
    
    total_successful = sum(1 for r in all_results if r.get('success', False))
    total_tests = len(all_results)
    total_data_rows = sum(r.get('rows', 0) for r in all_results if r.get('success', False))
    
    print(f"📊 OVERALL STATISTICS:")
    print(f"   • Total endpoints tested: {total_tests}")
    print(f"   • Successful: {total_successful}")
    print(f"   • Failed: {total_tests - total_successful}")
    print(f"   • Success rate: {total_successful/total_tests:.1%}")
    print(f"   • Total data rows retrieved: {total_data_rows:,}")
    print()
    
    print(f"📈 CATEGORY PERFORMANCE:")
    for category, summary in category_summary.items():
        status = "🟢" if summary['success_rate'] == 1.0 else "🟡" if summary['success_rate'] >= 0.5 else "🔴"
        print(f"   {status} {category}: {summary['successful']}/{summary['total']} ({summary['success_rate']:.1%}) - {summary['total_rows']:,} rows")
    
    # Failed endpoints details
    failed_results = [r for r in all_results if not r.get('success', False)]
    if failed_results:
        print(f"\n❌ FAILED ENDPOINTS ({len(failed_results)}):")
        for result in failed_results:
            error_msg = result.get('error', 'Unknown error')
            print(f"   • {result['category']}.{result['name']}: {error_msg}")
    
    print("\n" + "=" * 80)
    print("🎉 SMOKE TEST COMPLETED!")
    print("=" * 80)
    
    return all_results, category_summary

if __name__ == "__main__":
    results, summary = run_comprehensive_smoke_test()
