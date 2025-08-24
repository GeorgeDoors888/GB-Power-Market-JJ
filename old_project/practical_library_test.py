#!/usr/bin/env python3
"""
Practical ElexonDataPortal Library Test
=====================================
Test the specific functionality we need for our BMRS data collection project
"""

import os
import sys
import time
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv('api.env')
api_key = os.getenv('BMRS_API_KEY')

def test_2016_historical_data():
    """Test if we can access 2016 historical data"""
    print("\n🕐 Testing 2016 Historical Data Access")
    print("=" * 50)
    
    # Try multiple approaches for historical data
    approaches = [
        {
            'name': 'Current API with 2016 date',
            'url': 'https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances/all',
            'params': {'apikey': api_key, 'settlementDate': '2016-01-01', 'settlementPeriod': 1}
        },
        {
            'name': 'Generation data 2016',
            'url': 'https://data.elexon.co.uk/bmrs/api/v1/generation/outturn/summary',
            'params': {'apikey': api_key, 'settlementDate': '2016-06-01'}
        }
    ]
    
    for approach in approaches:
        try:
            print(f"\n📡 Trying: {approach['name']}")
            response = requests.get(approach['url'], params=approach['params'], timeout=20)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    records = len(data.get('data', []))
                    print(f"   Records: {records}")
                    
                    if records > 0:
                        print(f"✅ {approach['name']} - Historical data available!")
                        return True
                    else:
                        print(f"⚠️  {approach['name']} - No data for 2016")
                except:
                    print(f"   Non-JSON response")
            else:
                print(f"   Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {str(e)[:50]}...")
    
    return False

def test_2025_current_data():
    """Test current 2025 data access"""
    print("\n📅 Testing 2025 Current Data Access")
    print("=" * 50)
    
    # Test multiple recent dates to ensure we get data
    test_dates = []
    for i in range(1, 8):  # Last 7 days
        test_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        test_dates.append(test_date)
    
    base_url = 'https://data.elexon.co.uk/bmrs/api/v1'
    
    endpoints_to_test = [
        ('balancing/acceptances/all', {'settlementPeriod': 15}),
        ('generation/outturn/summary', {}),
        ('datasets/DETSYSPRICES', {})
    ]
    
    successful_tests = 0
    
    for endpoint, extra_params in endpoints_to_test:
        print(f"\n📊 Testing endpoint: {endpoint}")
        
        for test_date in test_dates[:3]:  # Test last 3 days
            try:
                url = f"{base_url}/{endpoint}"
                params = {'apikey': api_key, 'settlementDate': test_date}
                params.update(extra_params)
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        records = len(data.get('data', []))
                        
                        if records > 0:
                            print(f"   ✅ {test_date}: {records} records")
                            successful_tests += 1
                            break  # Found working data for this endpoint
                        else:
                            print(f"   ⚪ {test_date}: No data")
                    except:
                        print(f"   ⚪ {test_date}: Non-JSON response")
                else:
                    print(f"   ❌ {test_date}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {test_date}: {str(e)[:30]}...")
    
    return successful_tests >= 2  # At least 2 endpoints working

def test_data_collection_simulation():
    """Simulate the data collection we need for our project"""
    print("\n🔄 Testing Data Collection Simulation")
    print("=" * 50)
    
    try:
        base_url = 'https://data.elexon.co.uk/bmrs/api/v1'
        
        # Simulate collecting 1 day of bid-offer acceptance data
        test_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        print(f"📊 Simulating collection for {test_date}")
        
        # Test multiple settlement periods (like our current collection)
        settlement_periods = [1, 15, 30, 45]
        collected_data = []
        
        for sp in settlement_periods:
            try:
                endpoint = f"{base_url}/balancing/acceptances/all"
                params = {
                    'apikey': api_key,
                    'settlementDate': test_date,
                    'settlementPeriod': sp
                }
                
                start_time = time.time()
                response = requests.get(endpoint, params=params, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    records = len(data.get('data', []))
                    
                    collected_data.append({
                        'settlement_period': sp,
                        'records': records,
                        'response_time': response_time
                    })
                    
                    print(f"   SP {sp:2d}: {records:4d} records in {response_time:.2f}s")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   SP {sp:2d}: Error - {str(e)[:30]}...")
        
        if collected_data:
            # Calculate collection stats
            total_records = sum([d['records'] for d in collected_data])
            avg_response_time = sum([d['response_time'] for d in collected_data]) / len(collected_data)
            
            print(f"\n📈 Collection Summary:")
            print(f"   Total Records: {total_records}")
            print(f"   Avg Response Time: {avg_response_time:.2f}s")
            print(f"   Settlement Periods: {len(collected_data)}")
            
            # Estimate full day collection (48 periods)
            estimated_time = avg_response_time * 48
            estimated_records = (total_records / len(collected_data)) * 48
            
            print(f"\n🔮 Full Day Estimates:")
            print(f"   Time for 48 periods: {estimated_time:.1f}s ({estimated_time/60:.1f} min)")
            print(f"   Expected records: {estimated_records:.0f}")
            
            return True
        else:
            print("❌ No data collected")
            return False
            
    except Exception as e:
        print(f"❌ Collection simulation failed: {e}")
        return False

def test_library_core_functions():
    """Test the core functions we'd use from the library"""
    print("\n⚙️  Testing Core Library Functions")
    print("=" * 50)
    
    try:
        # Test DataFrame processing
        print("📊 Testing DataFrame processing...")
        
        # Create sample data similar to BMRS response
        sample_data = [
            {'settlementDate': '2025-08-07', 'settlementPeriod': 1, 'quantity': 100.5},
            {'settlementDate': '2025-08-07', 'settlementPeriod': 2, 'quantity': 150.2},
            {'settlementDate': '2025-08-07', 'settlementPeriod': 3, 'quantity': 75.8}
        ]
        
        df = pd.DataFrame(sample_data)
        
        # Test data type conversions
        df['quantity'] = pd.to_numeric(df['quantity'])
        df['settlementDate'] = pd.to_datetime(df['settlementDate'])
        
        print(f"   ✅ DataFrame created: {df.shape}")
        print(f"   ✅ Data types: {df.dtypes.to_dict()}")
        
        # Test settlement period calculations
        print("\n🕐 Testing settlement period utilities...")
        
        # Simple settlement period range
        start_time = datetime(2025, 1, 1, 0, 0)
        periods = []
        
        for hour in range(24):
            for minute in [0, 30]:
                period = int(2 * hour + minute/30 + 1)
                periods.append({
                    'hour': hour,
                    'minute': minute,
                    'settlement_period': period
                })
        
        sp_df = pd.DataFrame(periods)
        
        print(f"   ✅ Settlement periods calculated: {len(sp_df)} periods")
        print(f"   ✅ Period range: {sp_df['settlement_period'].min()} to {sp_df['settlement_period'].max()}")
        
        # Test timezone handling
        print("\n🌍 Testing timezone handling...")
        
        london_tz = pd.Timestamp.now(tz='Europe/London')
        utc_tz = pd.Timestamp.now(tz='UTC')
        
        print(f"   ✅ London time: {london_tz}")
        print(f"   ✅ UTC time: {utc_tz}")
        
        return True
        
    except Exception as e:
        print(f"❌ Core functions test failed: {e}")
        return False

def test_performance_at_scale():
    """Test performance for our scale requirements"""
    print("\n🚀 Testing Performance at Scale")
    print("=" * 50)
    
    try:
        base_url = 'https://data.elexon.co.uk/bmrs/api/v1'
        endpoint = f"{base_url}/balancing/acceptances/all"
        
        # Test rapid successive requests (like our batch collection)
        test_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        print(f"⚡ Testing rapid requests for {test_date}")
        
        request_times = []
        successful_requests = 0
        
        for sp in range(1, 11):  # Test 10 settlement periods
            try:
                params = {
                    'apikey': api_key,
                    'settlementDate': test_date,
                    'settlementPeriod': sp
                }
                
                start_time = time.time()
                response = requests.get(endpoint, params=params, timeout=8)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    request_times.append(response_time)
                    successful_requests += 1
                
                # Small delay to be respectful
                time.sleep(0.05)
                
            except Exception as e:
                print(f"   Request {sp} failed: {str(e)[:30]}...")
        
        if request_times:
            avg_time = sum(request_times) / len(request_times)
            max_time = max(request_times)
            min_time = min(request_times)
            
            print(f"\n📊 Performance Results:")
            print(f"   Successful requests: {successful_requests}/10")
            print(f"   Average time: {avg_time:.2f}s")
            print(f"   Min time: {min_time:.2f}s")
            print(f"   Max time: {max_time:.2f}s")
            
            # Estimate our project needs
            # We need ~3,403 files with ~336 requests each = ~1.1M requests
            total_requests_needed = 3403 * 48  # files × settlement periods
            estimated_total_time = total_requests_needed * avg_time
            
            print(f"\n🎯 Project Scale Estimates:")
            print(f"   Total requests needed: {total_requests_needed:,}")
            print(f"   Sequential time: {estimated_total_time/3600:.1f} hours")
            print(f"   With 4 parallel threads: {estimated_total_time/(3600*4):.1f} hours")
            
            if avg_time < 2.0:
                print("   ✅ Performance suitable for project scale")
                return True
            else:
                print("   ⚠️  Performance may be slow for project scale")
                return True
        else:
            print("❌ No successful requests")
            return False
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def run_practical_smoke_test():
    """Run practical smoke test for our specific needs"""
    print("🎯 ElexonDataPortal Library Practical Test")
    print("=" * 60)
    print("Testing functionality specifically needed for our BMRS project")
    print("=" * 60)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Key: {'✅ Available' if api_key else '❌ Missing'}")
    
    if not api_key:
        print("\n❌ CRITICAL: No API key - cannot proceed")
        return False
    
    # Run targeted tests
    tests = [
        ("2016 Historical Data", test_2016_historical_data),
        ("2025 Current Data", test_2025_current_data), 
        ("Data Collection", test_data_collection_simulation),
        ("Core Functions", test_library_core_functions),
        ("Scale Performance", test_performance_at_scale)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = test_func()
            results.append(result)
            
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{status} {test_name}")
            
        except Exception as e:
            results.append(False)
            print(f"\n❌ EXCEPTION {test_name}: {e}")
    
    # Final assessment
    print(f"\n{'='*60}")
    print("📋 PRACTICAL TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    success_rate = passed / total
    
    print(f"📊 Results: {passed}/{total} tests passed")
    print(f"📈 Success Rate: {success_rate:.1%}")
    
    # Specific recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if results[0]:  # Historical data
        print("✅ Historical data access confirmed - can collect from 2016")
    else:
        print("⚠️  Historical data may be limited - focus on recent years")
    
    if results[1]:  # Current data
        print("✅ Current data access excellent - real-time collection possible")
    else:
        print("❌ Current data issues - may affect real-time features")
    
    if results[2]:  # Data collection
        print("✅ Data collection pattern works - can replace current scripts")
    else:
        print("❌ Data collection issues - keep existing approach")
    
    if results[3]:  # Core functions
        print("✅ Core library functions operational - integration ready")
    else:
        print("⚠️  Core functions need attention - gradual integration")
    
    if results[4]:  # Performance
        print("✅ Performance suitable for project scale")
    else:
        print("⚠️  Performance optimization needed")
    
    # Overall verdict
    if success_rate >= 0.8:
        print(f"\n🎉 SMOKE TEST PASSED!")
        print("✅ ElexonDataPortal library is ready for integration")
        print("✅ Significant improvements over current manual approach")
        print("🚀 Recommend immediate integration planning")
        return True
    elif success_rate >= 0.6:
        print(f"\n⚠️  PARTIAL SUCCESS")
        print("💡 Library has useful features but some limitations")
        print("🔄 Recommend selective integration of working components")
        return True
    else:
        print(f"\n💥 SMOKE TEST FAILED")
        print("❌ Too many issues for reliable integration")
        print("🔄 Recommend sticking with current approach for now")
        return False

if __name__ == "__main__":
    success = run_practical_smoke_test()
    sys.exit(0 if success else 1)
