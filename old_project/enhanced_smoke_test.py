import os
import requests
import pandas as pd
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

load_dotenv()

BMRS_API_KEY = os.getenv("BMRS_API_KEY")
INSIGHTS_BASE_URL = os.getenv("INSIGHTS_BASE_URL")

def load_config(config_file):
    """Load configuration from YAML file"""
    try:
        with open(config_file) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file {config_file} not found!")
        return {}

def test_endpoint(category, name, url, start_date, end_date):
    """Test a single endpoint and return results"""
    print(f"=== Testing {category}.{name} ===")
    print(f"URL: {url}")
    
    # Common parameters that most endpoints accept
    params = {
        "from": start_date, 
        "to": end_date, 
        "apiKey": BMRS_API_KEY,
        "format": "json"  # Ensure JSON format
    }
    
    try:
        r = requests.get(url, params=params, timeout=30)
        print(f"Status: {r.status_code}")
        
        result = {
            'category': category,
            'name': name,
            'url': url,
            'status_code': r.status_code,
            'success': False,
            'rows': 0,
            'error': None,
            'response_time': None
        }
        
        if r.ok:
            try:
                response_data = r.json()
                
                # Handle different response structures
                if isinstance(response_data, dict):
                    data = response_data.get("data", [])
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                        result['rows'] = len(df)
                        result['success'] = True
                        
                        print(f"Rows: {len(df)}")
                        if not df.empty:
                            print("Sample data:")
                            print(df.head(3))
                            print(f"Columns: {list(df.columns)}")
                    else:
                        print("Data is not a list - might be a single record or different structure")
                        result['success'] = True
                        result['rows'] = 1
                        print(f"Response type: {type(data)}")
                else:
                    print("Response is not a dictionary")
                    result['success'] = True
                    result['rows'] = 1
                    
            except Exception as e:
                print(f"Parse error: {e}")
                result['error'] = str(e)
                # Try to show raw response for debugging
                try:
                    print(f"Raw response (first 200 chars): {r.text[:200]}")
                except:
                    pass
        else:
            print(f"HTTP Error: {r.text[:200] if r.text else 'No response body'}")
            result['error'] = f"HTTP {r.status_code}: {r.text[:100] if r.text else 'No response body'}"
            
    except requests.exceptions.Timeout:
        print("Request timed out")
        result['error'] = "Request timeout"
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        result['error'] = str(e)
    except Exception as e:
        print(f"Unexpected error: {e}")
        result['error'] = str(e)
    
    print()
    return result

def run_smoke_test(config_file="config:sample_endpoints.yml", max_endpoints_per_category=None):
    """Run smoke test on all configured endpoints"""
    
    print("=" * 60)
    print("ELEXON INSIGHTS API SMOKE TEST")
    print("=" * 60)
    print(f"Config file: {config_file}")
    print(f"API Key: {'***' + BMRS_API_KEY[-4:] if BMRS_API_KEY else 'NOT SET'}")
    
    # Calculate date range (1 week of data)
    start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    # Load configuration
    cfg = load_config(config_file)
    if not cfg:
        print("No configuration loaded. Exiting.")
        return
    
    # Track results
    all_results = []
    category_summary = {}
    
    # Test each category
    for category, endpoints in cfg.items():
        print(f"🔍 TESTING CATEGORY: {category.upper()}")
        print("-" * 40)
        
        category_results = []
        
        # Limit endpoints per category if specified
        if max_endpoints_per_category:
            endpoints = dict(list(endpoints.items())[:max_endpoints_per_category])
        
        for name, url in endpoints.items():
            result = test_endpoint(category, name, url, start_date, end_date)
            category_results.append(result)
            all_results.append(result)
            
            # Small delay between requests to be respectful to the API
            time.sleep(1)
        
        # Category summary
        successful = sum(1 for r in category_results if r['success'])
        total = len(category_results)
        total_rows = sum(r['rows'] for r in category_results if r['success'])
        
        category_summary[category] = {
            'successful': successful,
            'total': total,
            'total_rows': total_rows,
            'success_rate': successful / total if total > 0 else 0
        }
        
        print(f"📊 {category.upper()} SUMMARY: {successful}/{total} successful, {total_rows} total rows")
        print()
    
    # Overall summary
    print("=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    
    total_successful = sum(1 for r in all_results if r['success'])
    total_tests = len(all_results)
    total_data_rows = sum(r['rows'] for r in all_results if r['success'])
    overall_success_rate = total_successful / total_tests if total_tests > 0 else 0
    
    print(f"✅ Total endpoints tested: {total_tests}")
    print(f"✅ Successful: {total_successful}")
    print(f"❌ Failed: {total_tests - total_successful}")
    print(f"📈 Success rate: {overall_success_rate:.1%}")
    print(f"📊 Total data rows retrieved: {total_data_rows}")
    print()
    
    # Category breakdown
    print("CATEGORY BREAKDOWN:")
    for category, summary in category_summary.items():
        status = "✅" if summary['success_rate'] == 1.0 else "⚠️" if summary['success_rate'] > 0.5 else "❌"
        print(f"{status} {category}: {summary['successful']}/{summary['total']} ({summary['success_rate']:.1%}) - {summary['total_rows']} rows")
    
    print()
    
    # Failed endpoints
    failed_results = [r for r in all_results if not r['success']]
    if failed_results:
        print("FAILED ENDPOINTS:")
        for result in failed_results:
            print(f"❌ {result['category']}.{result['name']}: {result['error']}")
    
    return all_results, category_summary

if __name__ == "__main__":
    print("Starting enhanced smoke test...")
    
    # Run test with sample configuration (limited endpoints for quicker testing)
    results, summary = run_smoke_test("config:sample_endpoints.yml", max_endpoints_per_category=3)
    
    print("\n" + "=" * 60)
    print("SMOKE TEST COMPLETED")
    print("=" * 60)
