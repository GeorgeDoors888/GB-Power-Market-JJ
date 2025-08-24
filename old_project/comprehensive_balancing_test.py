#!/usr/bin/env python3
"""
Comprehensive test for balancing and bid-offer acceptance endpoints
Based on successful discovery of working parameter combinations
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('api.env')

class BalancingAPITester:
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.results = []
        
    def test_endpoint(self, endpoint_url, params=None, description=""):
        """Test a single endpoint with given parameters"""
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"URL: {endpoint_url}")
        print(f"Parameters: {params}")
        
        try:
            full_url = f"{self.base_url}/{endpoint_url}"
            if params is None:
                params = {}
            params['apikey'] = self.api_key
            
            response = requests.get(full_url, headers=self.headers, params=params, timeout=30)
            
            result = {
                'endpoint': endpoint_url,
                'description': description,
                'params': params,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_size': len(response.content) if response.content else 0,
                'data_count': 0,
                'error': None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and isinstance(data['data'], list):
                        result['data_count'] = len(data['data'])
                        print(f"✅ SUCCESS: {result['data_count']} records returned")
                        
                        # Show sample data structure
                        if data['data'] and len(data['data']) > 0:
                            sample_record = data['data'][0]
                            print(f"Sample record keys: {list(sample_record.keys())}")
                            # Show a few key fields if they exist
                            for key in ['settlementDate', 'settlementPeriod', 'bmUnit', 'acceptanceNumber', 'levelFrom', 'levelTo']:
                                if key in sample_record:
                                    print(f"  {key}: {sample_record[key]}")
                    else:
                        print(f"✅ SUCCESS: Response received (non-standard format)")
                        print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                except json.JSONDecodeError:
                    print(f"✅ SUCCESS: Non-JSON response ({len(response.content)} bytes)")
                    
            else:
                result['error'] = response.text[:200]
                print(f"❌ FAILED: Status {response.status_code}")
                print(f"Error: {result['error']}")
                
        except Exception as e:
            result = {
                'endpoint': endpoint_url,
                'description': description,
                'params': params,
                'status_code': None,
                'success': False,
                'response_size': 0,
                'data_count': 0,
                'error': str(e)
            }
            print(f"❌ EXCEPTION: {str(e)}")
            
        self.results.append(result)
        time.sleep(0.5)  # Rate limiting
        return result
        
    def get_test_dates(self):
        """Get a range of test dates"""
        # Use dates from 2024 (known to have data)
        base_date = datetime(2024, 6, 25)  # Date from the schema example
        return [
            base_date,
            base_date - timedelta(days=1),
            base_date + timedelta(days=1),
            datetime(2024, 1, 15),  # Different date
            datetime(2023, 6, 15),  # Earlier date
        ]
        
    def test_balancing_endpoints(self):
        """Test all balancing-related endpoints with proper parameters"""
        
        print("🔍 TESTING BALANCING AND BID-OFFER ACCEPTANCE ENDPOINTS")
        print("=" * 60)
        
        test_dates = self.get_test_dates()
        
        # Core balancing endpoints we've found that work
        balancing_endpoints = [
            {
                'url': 'balancing/acceptances/all',
                'description': 'Market-wide bid-offer acceptances (BOALF)',
                'param_strategies': [
                    # Strategy 1: Settlement date + period (WORKING)
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': 29
                    },
                    # Strategy 2: Different settlement periods
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'), 
                        'settlementPeriod': 15
                    },
                    # Strategy 3: With format parameter
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': 29,
                        'format': 'json'
                    }
                ]
            },
            {
                'url': 'balancing/acceptances/bmu',
                'description': 'BMU-specific bid-offer acceptances',
                'param_strategies': [
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': 29,
                        'bmUnit': 'T_ABRBO-1'  # From schema example
                    },
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': 29,
                        'bmUnit': 'ABRBO-1'  # Alternative format
                    }
                ]
            },
            {
                'url': 'datasets/BOD',
                'description': 'Bid-offer data (BOD)',
                'param_strategies': [
                    # This was working with date range
                    lambda date: {
                        'from': date.strftime('%Y-%m-%d'),
                        'to': (date + timedelta(days=1)).strftime('%Y-%m-%d')
                    },
                    # Try with settlement parameters
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': 29
                    }
                ]
            },
            {
                'url': 'balancing/dynamic/all',
                'description': 'Dynamic balancing data',
                'param_strategies': [
                    lambda date: {
                        'from': date.strftime('%Y-%m-%d'),
                        'to': (date + timedelta(days=1)).strftime('%Y-%m-%d')
                    }
                ]
            },
            {
                'url': 'balancing/acceptances/volumes',
                'description': 'Acceptance volumes',
                'param_strategies': [
                    lambda date: {
                        'settlementDate': date.strftime('%Y-%m-%d'),
                        'settlementPeriod': 29
                    }
                ]
            }
        ]
        
        # Additional endpoints to explore based on BMRS API patterns
        exploratory_endpoints = [
            'balancing/balancing-services-use-of-system',
            'balancing/response-energy-prices',
            'balancing/system-prices',
            'balancing/system-sell-buy-price',
            'datasets/BOALF',  # Direct dataset access
            'datasets/DERSYS',  # Dynamic regulation
            'datasets/MID',     # Market Index Data
            'datasets/SYSMEM',  # System members
        ]
        
        # Test main balancing endpoints
        for endpoint_config in balancing_endpoints:
            for i, test_date in enumerate(test_dates[:2]):  # Test first 2 dates
                for j, param_strategy in enumerate(endpoint_config['param_strategies']):
                    params = param_strategy(test_date)
                    description = f"{endpoint_config['description']} - Date: {test_date.strftime('%Y-%m-%d')} - Strategy {j+1}"
                    self.test_endpoint(endpoint_config['url'], params, description)
                    
        # Test exploratory endpoints with basic parameters
        print(f"\n{'='*60}")
        print("🔍 TESTING EXPLORATORY BALANCING ENDPOINTS")
        
        test_date = test_dates[0]  # Use first test date
        for endpoint in exploratory_endpoints:
            # Try multiple parameter strategies
            strategies = [
                {
                    'settlementDate': test_date.strftime('%Y-%m-%d'),
                    'settlementPeriod': 29
                },
                {
                    'from': test_date.strftime('%Y-%m-%d'),
                    'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d')
                },
                {
                    'date': test_date.strftime('%Y-%m-%d')
                }
            ]
            
            for i, params in enumerate(strategies):
                description = f"{endpoint} - Strategy {i+1}"
                result = self.test_endpoint(endpoint, params, description)
                if result['success']:
                    break  # Stop if we find a working strategy
                    
    def print_summary(self):
        """Print test results summary"""
        print(f"\n{'='*60}")
        print("📊 TEST RESULTS SUMMARY")
        print(f"{'='*60}")
        
        successful = [r for r in self.results if r['success']]
        failed = [r for r in self.results if not r['success']]
        
        print(f"✅ Successful endpoints: {len(successful)}")
        print(f"❌ Failed endpoints: {len(failed)}")
        print(f"📈 Success rate: {len(successful)/(len(self.results))*100:.1f}%")
        
        if successful:
            total_records = sum(r['data_count'] for r in successful)
            print(f"📊 Total records retrieved: {total_records:,}")
            
            print(f"\n🎯 WORKING ENDPOINTS:")
            for result in successful:
                if result['data_count'] > 0:
                    print(f"  ✅ {result['endpoint']}")
                    print(f"     📊 {result['data_count']:,} records")
                    print(f"     📋 {result['description']}")
                    print(f"     🔧 Params: {result['params']}")
                    print()
        
        if failed:
            print(f"\n❌ FAILED ENDPOINTS (showing first 5):")
            for result in failed[:5]:
                print(f"  ❌ {result['endpoint']}")
                print(f"     📋 {result['description']}")
                if result['error']:
                    print(f"     ⚠️ Error: {result['error'][:100]}...")
                print()

def main():
    """Main execution function"""
    print("🚀 Starting Comprehensive Balancing API Test")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = BalancingAPITester()
    
    if not tester.api_key:
        print("❌ ERROR: BMRS_API_KEY not found in environment variables")
        print("Make sure your api.env file contains: BMRS_API_KEY=your_key_here")
        return
        
    tester.test_balancing_endpoints()
    tester.print_summary()
    
    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'balancing_test_results_{timestamp}.json'
    
    with open(results_file, 'w') as f:
        json.dump(tester.results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()
