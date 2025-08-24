#!/usr/bin/env python3
"""
Test historical data availability from 2017
Checks if bid-offer acceptance data is available for dates in 2017
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('api.env')

class HistoricalDataTester:
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.results = []
        
    def test_historical_date(self, test_date, settlement_periods=[15, 29, 35]):
        """Test a specific historical date with multiple settlement periods"""
        print(f"\n{'='*60}")
        print(f"🗓️ Testing historical date: {test_date.strftime('%Y-%m-%d (%A)')}")
        print(f"{'='*60}")
        
        date_results = []
        
        # Test settlement period approach
        print(f"\n📊 TESTING SETTLEMENT PERIOD APPROACH")
        for period in settlement_periods:
            params = {
                'settlementDate': test_date.strftime('%Y-%m-%d'),
                'settlementPeriod': period,
                'apikey': self.api_key
            }
            
            try:
                url = f"{self.base_url}/balancing/acceptances/all"
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                result = {
                    'method': 'settlement_period',
                    'date': test_date.strftime('%Y-%m-%d'),
                    'settlement_period': period,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'record_count': 0,
                    'error': None
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'data' in data and isinstance(data['data'], list):
                            result['record_count'] = len(data['data'])
                            print(f"✅ Period {period:02d}: {result['record_count']} records")
                            
                            # Show sample data from first record
                            if data['data']:
                                sample = data['data'][0]
                                print(f"   Sample: BMU={sample.get('bmUnit', 'N/A')}, AcceptanceNo={sample.get('acceptanceNumber', 'N/A')}")
                        else:
                            print(f"⚠️ Period {period:02d}: No data array in response")
                    except json.JSONDecodeError:
                        print(f"⚠️ Period {period:02d}: JSON decode error")
                        result['error'] = "JSON decode error"
                else:
                    result['error'] = f"HTTP {response.status_code}"
                    print(f"❌ Period {period:02d}: HTTP {response.status_code}")
                    
                date_results.append(result)
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                result = {
                    'method': 'settlement_period',
                    'date': test_date.strftime('%Y-%m-%d'),
                    'settlement_period': period,
                    'status_code': None,
                    'success': False,
                    'record_count': 0,
                    'error': str(e)
                }
                date_results.append(result)
                print(f"❌ Period {period:02d}: Exception - {str(e)}")
                
        # Test bulk dataset approach
        print(f"\n📦 TESTING BULK DATASET APPROACH")
        params = {
            'from': test_date.strftime('%Y-%m-%d'),
            'to': (test_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            'apikey': self.api_key
        }
        
        try:
            url = f"{self.base_url}/datasets/BOALF"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            result = {
                'method': 'bulk_dataset',
                'date': test_date.strftime('%Y-%m-%d'),
                'settlement_period': None,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'record_count': 0,
                'error': None
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and isinstance(data['data'], list):
                        result['record_count'] = len(data['data'])
                        print(f"✅ Bulk dataset: {result['record_count']} records")
                        
                        # Show sample data
                        if data['data']:
                            sample = data['data'][0]
                            print(f"   Sample: BMU={sample.get('bmUnit', 'N/A')}, Date={sample.get('settlementDate', 'N/A')}")
                    else:
                        print(f"⚠️ Bulk dataset: No data array in response")
                except json.JSONDecodeError:
                    print(f"⚠️ Bulk dataset: JSON decode error")
                    result['error'] = "JSON decode error"
            else:
                result['error'] = f"HTTP {response.status_code}"
                print(f"❌ Bulk dataset: HTTP {response.status_code}")
                
            date_results.append(result)
            
        except Exception as e:
            result = {
                'method': 'bulk_dataset',
                'date': test_date.strftime('%Y-%m-%d'),
                'settlement_period': None,
                'status_code': None,
                'success': False,
                'record_count': 0,
                'error': str(e)
            }
            date_results.append(result)
            print(f"❌ Bulk dataset: Exception - {str(e)}")
            
        self.results.extend(date_results)
        return date_results
        
    def test_2017_data_availability(self):
        """Test data availability for various dates in 2017"""
        print("🗓️ TESTING 2017 HISTORICAL DATA AVAILABILITY")
        print("=" * 60)
        
        # Test dates throughout 2017
        test_dates_2017 = [
            datetime(2017, 1, 15),   # January 2017
            datetime(2017, 3, 15),   # March 2017  
            datetime(2017, 6, 15),   # June 2017 (mid-year)
            datetime(2017, 9, 15),   # September 2017
            datetime(2017, 12, 15),  # December 2017 (end of year)
        ]
        
        # Also test some comparison dates
        comparison_dates = [
            datetime(2018, 6, 15),   # 2018 for comparison
            datetime(2019, 6, 15),   # 2019 for comparison
            datetime(2024, 6, 25),   # 2024 (known working date)
        ]
        
        all_test_dates = test_dates_2017 + comparison_dates
        
        for test_date in all_test_dates:
            self.test_historical_date(test_date)
            
    def print_summary(self):
        """Print summary of historical data availability"""
        print(f"\n{'='*60}")
        print("📊 HISTORICAL DATA AVAILABILITY SUMMARY")
        print(f"{'='*60}")
        
        # Group results by year
        results_by_year = {}
        for result in self.results:
            year = result['date'][:4]
            if year not in results_by_year:
                results_by_year[year] = []
            results_by_year[year].append(result)
            
        # Summary by year
        for year in sorted(results_by_year.keys()):
            year_results = results_by_year[year]
            successful = [r for r in year_results if r['success']]
            total_records = sum(r['record_count'] for r in successful)
            
            print(f"\n📅 {year}:")
            print(f"  ✅ Successful requests: {len(successful)}/{len(year_results)}")
            print(f"  📊 Total records: {total_records:,}")
            
            if successful:
                # Show best performing dates
                best_by_records = max(successful, key=lambda x: x['record_count'])
                print(f"  🏆 Best date: {best_by_records['date']} ({best_by_records['record_count']:,} records)")
                
        # Method comparison
        print(f"\n🔍 METHOD COMPARISON:")
        settlement_results = [r for r in self.results if r['method'] == 'settlement_period' and r['success']]
        bulk_results = [r for r in self.results if r['method'] == 'bulk_dataset' and r['success']]
        
        print(f"  📊 Settlement period approach: {len(settlement_results)} successful")
        print(f"  📦 Bulk dataset approach: {len(bulk_results)} successful")
        
        if settlement_results:
            settlement_total = sum(r['record_count'] for r in settlement_results)
            print(f"     Total records: {settlement_total:,}")
            
        if bulk_results:
            bulk_total = sum(r['record_count'] for r in bulk_results)
            print(f"     Total records: {bulk_total:,}")
            
        # 2017 specific analysis
        results_2017 = [r for r in self.results if r['date'].startswith('2017')]
        successful_2017 = [r for r in results_2017 if r['success']]
        
        print(f"\n🎯 2017 DATA AVAILABILITY:")
        if successful_2017:
            total_2017_records = sum(r['record_count'] for r in successful_2017)
            print(f"  ✅ Data available: YES")
            print(f"  📊 Total 2017 records found: {total_2017_records:,}")
            print(f"  📈 Success rate: {len(successful_2017)}/{len(results_2017)} requests")
            
            # Show all successful 2017 dates
            print(f"  📅 Available 2017 dates:")
            for result in successful_2017:
                if result['record_count'] > 0:
                    method_label = "Settlement" if result['method'] == 'settlement_period' else "Bulk"
                    period_info = f" P{result['settlement_period']:02d}" if result['settlement_period'] else ""
                    print(f"     {result['date']}{period_info} ({method_label}): {result['record_count']:,} records")
        else:
            print(f"  ❌ Data available: NO")
            print(f"  ⚠️ No successful requests for 2017 dates")
            
    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'historical_data_test_2017_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump({
                'test_info': {
                    'test_timestamp': datetime.now().isoformat(),
                    'test_purpose': 'Check 2017 historical data availability',
                    'total_tests': len(self.results)
                },
                'results': self.results
            }, f, indent=2, default=str)
            
        print(f"\n💾 Test results saved to: {filename}")
        return filename

def main():
    """Main execution function"""
    tester = HistoricalDataTester()
    
    if not tester.api_key:
        print("❌ ERROR: BMRS_API_KEY not found in environment variables")
        return
        
    print("🕰️ TESTING 2017 HISTORICAL DATA AVAILABILITY")
    print("Testing bid-offer acceptance data from various dates in 2017")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester.test_2017_data_availability()
    tester.print_summary()
    tester.save_results()
    
    print(f"\n🏁 Historical data test completed!")

if __name__ == "__main__":
    main()
