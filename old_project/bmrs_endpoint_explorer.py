#!/usr/bin/env python3
"""
Extended BMRS API endpoint explorer
Tests additional endpoints from the BMRS API documentation using patterns discovered from working endpoints
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('api.env')

class BMRSEndpointExplorer:
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.results = []
        self.working_endpoints = []
        
    def test_endpoint_strategies(self, endpoint_url, description="", test_strategies=None):
        """Test an endpoint with multiple parameter strategies"""
        print(f"\n{'='*60}")
        print(f"🔍 Exploring: {description}")
        print(f"🔗 Endpoint: {endpoint_url}")
        
        if test_strategies is None:
            test_strategies = self.get_default_strategies()
            
        test_date = datetime(2024, 6, 25)  # Known good date
        
        for i, strategy in enumerate(test_strategies, 1):
            try:
                params = strategy(test_date)
                print(f"\n  📋 Strategy {i}: {params}")
                
                result = self.test_single_endpoint(endpoint_url, params, f"{description} - Strategy {i}")
                
                if result['success'] and result['data_count'] > 0:
                    print(f"  ✅ SUCCESS: Found working strategy!")
                    self.working_endpoints.append({
                        'endpoint': endpoint_url,
                        'description': description,
                        'working_params': params,
                        'data_count': result['data_count']
                    })
                    return result  # Stop at first working strategy
                elif result['success']:
                    print(f"  ⚠️ SUCCESS but no data returned")
                else:
                    print(f"  ❌ Strategy {i} failed: {result.get('error', 'Unknown error')[:100]}")
                    
            except Exception as e:
                print(f"  ❌ Strategy {i} exception: {str(e)}")
                
        return None
        
    def test_single_endpoint(self, endpoint_url, params, description):
        """Test a single endpoint with specific parameters"""
        try:
            full_url = f"{self.base_url}/{endpoint_url}"
            test_params = params.copy()
            test_params['apikey'] = self.api_key
            
            response = requests.get(full_url, headers=self.headers, params=test_params, timeout=30)
            
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
                except json.JSONDecodeError:
                    pass
            else:
                result['error'] = response.text[:200]
                
            self.results.append(result)
            time.sleep(0.3)  # Rate limiting
            return result
            
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
            self.results.append(result)
            return result
            
    def get_default_strategies(self):
        """Get default parameter strategies based on working patterns"""
        return [
            # Strategy 1: Settlement date + period (works for balancing endpoints)
            lambda date: {
                'settlementDate': date.strftime('%Y-%m-%d'),
                'settlementPeriod': 29
            },
            # Strategy 2: Date range (works for datasets)
            lambda date: {
                'from': date.strftime('%Y-%m-%d'),
                'to': (date + timedelta(days=1)).strftime('%Y-%m-%d')
            },
            # Strategy 3: Single date parameter
            lambda date: {
                'date': date.strftime('%Y-%m-%d')
            },
            # Strategy 4: Settlement date only
            lambda date: {
                'settlementDate': date.strftime('%Y-%m-%d')
            },
            # Strategy 5: Different settlement period
            lambda date: {
                'settlementDate': date.strftime('%Y-%m-%d'),
                'settlementPeriod': 15
            },
            # Strategy 6: With format specification
            lambda date: {
                'from': date.strftime('%Y-%m-%d'),
                'to': (date + timedelta(days=1)).strftime('%Y-%m-%d'),
                'format': 'json'
            }
        ]
        
    def explore_balancing_endpoints(self):
        """Explore balancing mechanism related endpoints"""
        print("🔍 EXPLORING BALANCING MECHANISM ENDPOINTS")
        print("=" * 60)
        
        balancing_endpoints = [
            # Core balancing endpoints
            ('balancing/physical', 'Physical balancing data'),
            ('balancing/settlement', 'Settlement balancing data'),
            ('balancing/services', 'Balancing services data'),
            ('balancing/constraints', 'Constraint balancing data'),
            ('balancing/marginal', 'Marginal balancing data'),
            ('balancing/response', 'Response balancing data'),
            
            # Price related endpoints
            ('balancing/pricing/energy', 'Energy pricing data'),
            ('balancing/pricing/system', 'System pricing data'),
            ('balancing/pricing/marginal', 'Marginal pricing data'),
            
            # Volume related endpoints
            ('balancing/volumes/total', 'Total balancing volumes'),
            ('balancing/volumes/by-fuel', 'Balancing volumes by fuel type'),
            ('balancing/volumes/by-region', 'Balancing volumes by region'),
            
            # Additional discovered patterns
            ('balancing/imbalance', 'System imbalance data'),
            ('balancing/reserves', 'Reserve balancing data'),
            ('balancing/regulation', 'Regulation balancing data')
        ]
        
        for endpoint, description in balancing_endpoints:
            self.test_endpoint_strategies(endpoint, description)
            
    def explore_generation_endpoints(self):
        """Explore generation related endpoints"""
        print("\n🔍 EXPLORING GENERATION ENDPOINTS")
        print("=" * 60)
        
        generation_endpoints = [
            # Generation by fuel type
            ('generation/outturn/total', 'Total generation outturn'),
            ('generation/outturn/by-fuel-type', 'Generation by fuel type'),
            ('generation/forecast/total', 'Total generation forecast'),
            ('generation/forecast/by-fuel-type', 'Forecast by fuel type'),
            
            # Wind generation
            ('generation/wind/total', 'Total wind generation'),
            ('generation/wind/onshore', 'Onshore wind generation'),
            ('generation/wind/offshore', 'Offshore wind generation'),
            ('generation/wind/forecast', 'Wind generation forecast'),
            
            # Solar generation
            ('generation/solar/total', 'Total solar generation'),
            ('generation/solar/forecast', 'Solar generation forecast'),
            
            # Nuclear and thermal
            ('generation/nuclear', 'Nuclear generation'),
            ('generation/thermal', 'Thermal generation'),
            ('generation/hydro', 'Hydro generation'),
            
            # Interconnector flows
            ('generation/interconnector/total', 'Total interconnector flows'),
            ('generation/interconnector/by-link', 'Flows by interconnector link')
        ]
        
        for endpoint, description in generation_endpoints:
            self.test_endpoint_strategies(endpoint, description)
            
    def explore_demand_endpoints(self):
        """Explore demand related endpoints"""
        print("\n🔍 EXPLORING DEMAND ENDPOINTS")
        print("=" * 60)
        
        demand_endpoints = [
            # National demand
            ('demand/total', 'Total national demand'),
            ('demand/forecast', 'Demand forecast'),
            ('demand/outturn', 'Demand outturn'),
            
            # Regional demand
            ('demand/regional/total', 'Total regional demand'),
            ('demand/regional/by-gsp', 'Demand by GSP region'),
            
            # Transmission demand
            ('demand/transmission', 'Transmission system demand'),
            ('demand/embedded', 'Embedded generation adjusted demand'),
            
            # Peak demand
            ('demand/peak/daily', 'Daily peak demand'),
            ('demand/peak/weekly', 'Weekly peak demand'),
            ('demand/peak/annual', 'Annual peak demand')
        ]
        
        for endpoint, description in demand_endpoints:
            self.test_endpoint_strategies(endpoint, description)
            
    def explore_dataset_endpoints(self):
        """Explore additional dataset endpoints"""
        print("\n🔍 EXPLORING ADDITIONAL DATASET ENDPOINTS")
        print("=" * 60)
        
        # These are based on common BMRS dataset codes
        dataset_endpoints = [
            # System data
            ('datasets/SYSWARN', 'System warnings'),
            ('datasets/SYSDEM', 'System demand'),
            ('datasets/SYSPRICE', 'System prices'),
            
            # Balancing mechanism data
            ('datasets/BMUNIT', 'BM unit data'),
            ('datasets/BMRS', 'BMRS data'),
            ('datasets/BODC', 'Bid-offer data by consumption'),
            
            # Demand data
            ('datasets/DEMAND', 'Demand data'),
            ('datasets/DEMFOR', 'Demand forecast'),
            
            # Generation data  
            ('datasets/GENERATION', 'Generation data'),
            ('datasets/GENFOR', 'Generation forecast'),
            ('datasets/WIND', 'Wind generation data'),
            ('datasets/SOLAR', 'Solar generation data'),
            
            # Market data
            ('datasets/MARKET', 'Market data'),
            ('datasets/PRICES', 'Price data'),
            ('datasets/TRADING', 'Trading data'),
            
            # System information
            ('datasets/SYSCON', 'System configuration'),
            ('datasets/MARGIN', 'System margin'),
            ('datasets/RESERVE', 'Reserve data')
        ]
        
        for endpoint, description in dataset_endpoints:
            self.test_endpoint_strategies(endpoint, description)
            
    def run_comprehensive_exploration(self):
        """Run comprehensive endpoint exploration"""
        print("🚀 COMPREHENSIVE BMRS API ENDPOINT EXPLORATION")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Discovering new working endpoints using proven parameter strategies")
        
        self.explore_balancing_endpoints()
        self.explore_generation_endpoints() 
        self.explore_demand_endpoints()
        self.explore_dataset_endpoints()
        
    def print_discovery_summary(self):
        """Print summary of discovered working endpoints"""
        print(f"\n{'='*60}")
        print("🎯 ENDPOINT DISCOVERY RESULTS")
        print(f"{'='*60}")
        
        total_tested = len(self.results)
        successful = len([r for r in self.results if r['success']])
        with_data = len([r for r in self.results if r['success'] and r['data_count'] > 0])
        
        print(f"📊 Total endpoints tested: {total_tested}")
        print(f"✅ Responded successfully: {successful}")
        print(f"📈 Success rate: {successful/total_tested*100:.1f}%")
        print(f"💾 Endpoints with data: {with_data}")
        
        if self.working_endpoints:
            print(f"\n🎉 NEW WORKING ENDPOINTS DISCOVERED:")
            print(f"{'='*60}")
            
            total_new_records = 0
            for endpoint in self.working_endpoints:
                total_new_records += endpoint['data_count']
                print(f"\n✅ {endpoint['endpoint']}")
                print(f"   📋 {endpoint['description']}")
                print(f"   📊 {endpoint['data_count']:,} records")
                print(f"   🔧 Working params: {endpoint['working_params']}")
                
            print(f"\n📊 Total new data discovered: {total_new_records:,} records")
            
        else:
            print(f"\n💡 No new working endpoints discovered")
            print(f"   The confirmed endpoints from previous testing remain the most reliable")
            
        # Show most promising failed endpoints (those that responded but had no data)
        promising = [r for r in self.results if r['success'] and r['data_count'] == 0]
        if promising:
            print(f"\n🔍 PROMISING ENDPOINTS (responded but no data):")
            for result in promising[:5]:  # Show top 5
                print(f"   ⚠️ {result['endpoint']} - {result['description']}")
                
    def save_discovery_results(self):
        """Save discovery results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f'bmrs_endpoint_discovery_{timestamp}.json'
        
        discovery_data = {
            'discovery_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_endpoints_tested': len(self.results),
                'successful_responses': len([r for r in self.results if r['success']]),
                'endpoints_with_data': len([r for r in self.results if r['success'] and r['data_count'] > 0]),
                'new_working_endpoints': len(self.working_endpoints)
            },
            'working_endpoints': self.working_endpoints,
            'all_test_results': [
                {k: v for k, v in result.items() if k != 'apikey'}  # Remove API key
                for result in self.results
            ]
        }
        
        with open(results_file, 'w') as f:
            json.dump(discovery_data, f, indent=2, default=str)
            
        print(f"\n💾 Discovery results saved to: {results_file}")
        return results_file

def main():
    """Main execution function"""
    explorer = BMRSEndpointExplorer()
    
    if not explorer.api_key:
        print("❌ ERROR: BMRS_API_KEY not found in environment variables")
        return
        
    explorer.run_comprehensive_exploration()
    explorer.print_discovery_summary()
    explorer.save_discovery_results()
    
    print(f"\n🏁 Endpoint discovery completed!")
    print(f"💡 Use discovered endpoints to expand your data collection capabilities")

if __name__ == "__main__":
    main()
