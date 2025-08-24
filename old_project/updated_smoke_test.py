#!/usr/bin/env python3
"""
Updated smoke test using confirmed working endpoints and parameters
Based on comprehensive testing results that identified working parameter combinations
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import pandas as pd

# Load environment variables
load_dotenv('api.env')

class UpdatedSmokeTest:
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.results = []
        
    def test_endpoint(self, endpoint_url, params=None, description="", expected_min_records=0):
        """Test a single endpoint with given parameters"""
        print(f"\n{'='*50}")
        print(f"🧪 Testing: {description}")
        print(f"🔗 URL: {endpoint_url}")
        print(f"📊 Parameters: {params}")
        
        try:
            full_url = f"{self.base_url}/{endpoint_url}"
            if params is None:
                params = {}
            params['apikey'] = self.api_key
            
            start_time = time.time()
            response = requests.get(full_url, headers=self.headers, params=params, timeout=30)
            response_time = time.time() - start_time
            
            result = {
                'endpoint': endpoint_url,
                'description': description,
                'params': params.copy(),
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_time': round(response_time, 2),
                'response_size': len(response.content) if response.content else 0,
                'data_count': 0,
                'sample_data': None,
                'error': None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and isinstance(data['data'], list):
                        result['data_count'] = len(data['data'])
                        result['sample_data'] = data['data'][0] if data['data'] else None
                        
                        status = "✅ SUCCESS"
                        if result['data_count'] >= expected_min_records:
                            status += f" (Expected ≥{expected_min_records}, got {result['data_count']})"
                        elif expected_min_records > 0:
                            status += f" ⚠️ (Expected ≥{expected_min_records}, got {result['data_count']})"
                            
                        print(f"{status}")
                        print(f"📊 Records: {result['data_count']:,}")
                        print(f"⏱️ Response time: {response_time:.2f}s")
                        print(f"💾 Response size: {len(response.content):,} bytes")
                        
                        # Show key fields from sample record
                        if result['sample_data']:
                            sample = result['sample_data']
                            key_fields = ['settlementDate', 'settlementPeriod', 'bmUnit', 'acceptanceNumber', 
                                        'levelFrom', 'levelTo', 'price', 'volume', 'dataset']
                            sample_info = []
                            for field in key_fields:
                                if field in sample:
                                    sample_info.append(f"{field}: {sample[field]}")
                            if sample_info:
                                print(f"🔍 Sample data: {', '.join(sample_info[:3])}")
                    else:
                        print(f"✅ SUCCESS: Non-standard response format")
                        print(f"⏱️ Response time: {response_time:.2f}s")
                        
                except json.JSONDecodeError:
                    print(f"✅ SUCCESS: Non-JSON response ({len(response.content):,} bytes)")
                    print(f"⏱️ Response time: {response_time:.2f}s")
                    
            else:
                result['error'] = response.text[:200]
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"⚠️ Error: {result['error']}")
                
        except Exception as e:
            result = {
                'endpoint': endpoint_url,
                'description': description,
                'params': params,
                'status_code': None,
                'success': False,
                'response_time': 0,
                'response_size': 0,
                'data_count': 0,
                'sample_data': None,
                'error': str(e)
            }
            print(f"❌ EXCEPTION: {str(e)}")
            
        self.results.append(result)
        time.sleep(0.5)  # Rate limiting
        return result
        
    def get_test_dates(self):
        """Get test dates for different scenarios"""
        # Use recent dates that are likely to have data
        today = datetime.now()
        return {
            'recent': today - timedelta(days=2),      # 2 days ago
            'week_ago': today - timedelta(days=7),    # 1 week ago
            'month_ago': today - timedelta(days=30),  # 1 month ago
            'known_good': datetime(2024, 6, 25),      # Date from our successful tests
        }
        
    def run_confirmed_endpoints_test(self):
        """Test all confirmed working endpoints with verified parameters"""
        
        print("🎯 TESTING CONFIRMED WORKING ENDPOINTS")
        print("=" * 60)
        
        test_dates = self.get_test_dates()
        
        # Test 1: Bid-offer acceptances - Settlement period approach
        print(f"\n📋 SECTION 1: BID-OFFER ACCEPTANCES (Settlement Period)")
        for date_name, test_date in test_dates.items():
            for period in [15, 29, 35]:  # Test different settlement periods
                params = {
                    'settlementDate': test_date.strftime('%Y-%m-%d'),
                    'settlementPeriod': period
                }
                description = f"Bid-offer acceptances - {date_name} ({test_date.strftime('%Y-%m-%d')}) - Period {period}"
                self.test_endpoint('balancing/acceptances/all', params, description, expected_min_records=50)
                
        # Test 2: Bid-offer acceptances - Bulk data approach  
        print(f"\n📋 SECTION 2: BID-OFFER ACCEPTANCES (Bulk Historical)")
        for date_name, test_date in list(test_dates.items())[:2]:  # Test first 2 dates
            params = {
                'from': test_date.strftime('%Y-%m-%d'),
                'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')
            }
            description = f"BOALF dataset - {date_name} ({test_date.strftime('%Y-%m-%d')}) - 1 day range"
            self.test_endpoint('datasets/BOALF', params, description, expected_min_records=1000)
            
        # Test 3: Market Index Data
        print(f"\n📋 SECTION 3: MARKET INDEX DATA")
        for date_name, test_date in list(test_dates.items())[:2]:
            params = {
                'from': test_date.strftime('%Y-%m-%d'),
                'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')
            }
            description = f"Market Index Data - {date_name} ({test_date.strftime('%Y-%m-%d')})"
            self.test_endpoint('datasets/MID', params, description, expected_min_records=10)
            
        # Test 4: Additional confirmed working endpoints from previous tests
        print(f"\n📋 SECTION 4: ADDITIONAL CONFIRMED ENDPOINTS")
        test_date = test_dates['known_good']
        
        additional_endpoints = [
            {
                'endpoint': 'datasets/BOD',
                'params': {'from': test_date.strftime('%Y-%m-%d'), 'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')},
                'description': 'Bid-Offer Data (BOD)',
                'min_records': 100
            },
            {
                'endpoint': 'datasets/FREQ',
                'params': {'from': test_date.strftime('%Y-%m-%d'), 'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')},
                'description': 'System Frequency Data',
                'min_records': 100
            },
            {
                'endpoint': 'datasets/TEMP',
                'params': {'from': test_date.strftime('%Y-%m-%d'), 'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')},
                'description': 'Temperature Data',
                'min_records': 10
            },
            {
                'endpoint': 'datasets/INDO',
                'params': {'from': test_date.strftime('%Y-%m-%d'), 'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')},
                'description': 'Initial National Demand Outturn',
                'min_records': 10
            }
        ]
        
        for endpoint_config in additional_endpoints:
            self.test_endpoint(
                endpoint_config['endpoint'],
                endpoint_config['params'],
                endpoint_config['description'],
                endpoint_config['min_records']
            )
            
    def print_summary(self):
        """Print detailed test results summary"""
        print(f"\n{'='*60}")
        print("📊 UPDATED SMOKE TEST RESULTS")
        print(f"{'='*60}")
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"✅ Successful endpoints: {len(successful)}")
        print(f"❌ Failed endpoints: {len(failed)}")
        print(f"📈 Success rate: {len(successful)/(len(self.results))*100:.1f}%")
        
        if successful:
            total_records = sum(r['data_count'] for r in successful)
            avg_response_time = sum(r['response_time'] for r in successful) / len(successful)
            print(f"📊 Total records retrieved: {total_records:,}")
            print(f"⏱️ Average response time: {avg_response_time:.2f}s")
            
            print(f"\n🎯 WORKING ENDPOINTS SUMMARY:")
            endpoint_groups = {}
            for result in successful:
                if result['data_count'] > 0:
                    base_endpoint = result['endpoint'].split('/')[0] + '/' + result['endpoint'].split('/')[1]
                    if base_endpoint not in endpoint_groups:
                        endpoint_groups[base_endpoint] = []
                    endpoint_groups[base_endpoint].append(result)
                    
            for group, results in endpoint_groups.items():
                total_group_records = sum(r['data_count'] for r in results)
                avg_group_time = sum(r['response_time'] for r in results) / len(results)
                print(f"\n  📂 {group}")
                print(f"     📊 {len(results)} successful tests, {total_group_records:,} total records")
                print(f"     ⏱️ Average response time: {avg_group_time:.2f}s")
                
                # Show best performing test
                best = max(results, key=lambda x: x['data_count'])
                print(f"     🏆 Best: {best['data_count']:,} records in {best['response_time']:.2f}s")
        
        if failed:
            print(f"\n❌ FAILED ENDPOINTS:")
            error_types = {}
            for result in failed:
                error_key = f"Status {result['status_code']}" if result['status_code'] else "Exception"
                if error_key not in error_types:
                    error_types[error_key] = []
                error_types[error_key].append(result)
                
            for error_type, results in error_types.items():
                print(f"  ⚠️ {error_type}: {len(results)} endpoints")
                
    def save_results(self):
        """Save detailed results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f'updated_smoke_test_results_{timestamp}.json'
        
        # Prepare results for JSON serialization
        json_results = []
        for result in self.results:
            json_result = result.copy()
            # Remove API key from saved params
            if 'params' in json_result and 'apikey' in json_result['params']:
                json_result['params'] = {k: v for k, v in json_result['params'].items() if k != 'apikey'}
            json_results.append(json_result)
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_timestamp': datetime.now().isoformat(),
                'test_summary': {
                    'total_tests': len(self.results),
                    'successful_tests': len([r for r in self.results if r['success']]),
                    'failed_tests': len([r for r in self.results if not r['success']]),
                    'success_rate': len([r for r in self.results if r['success']]) / len(self.results) * 100
                },
                'detailed_results': json_results
            }, f, indent=2, default=str)
            
        print(f"\n💾 Detailed results saved to: {results_file}")
        return results_file

def main():
    """Main execution function"""
    print("🚀 UPDATED SMOKE TEST - CONFIRMED WORKING ENDPOINTS")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Testing only endpoints and parameters confirmed to work")
    
    tester = UpdatedSmokeTest()
    
    if not tester.api_key:
        print("❌ ERROR: BMRS_API_KEY not found in environment variables")
        print("Make sure your api.env file contains: BMRS_API_KEY=your_key_here")
        return
        
    tester.run_confirmed_endpoints_test()
    tester.print_summary()
    results_file = tester.save_results()
    
    print(f"\n🏁 Updated smoke test completed!")
    print(f"📋 This test validates our confirmed working endpoints")
    print(f"💡 Use this as a baseline for API health monitoring")

if __name__ == "__main__":
    main()
