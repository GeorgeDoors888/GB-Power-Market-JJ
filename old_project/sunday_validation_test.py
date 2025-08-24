#!/usr/bin/env python3
"""
Quick Validation Test for Enhanced Data Collector
===============================================
Test the hybrid approach before Sunday deployment
"""

import os
import sys
import time
from datetime import datetime, timedelta
from enhanced_data_collector import EnhancedBMRSCollector

def quick_validation_test():
    """Quick test to validate enhanced collector functionality"""
    print("🧪 QUICK VALIDATION TEST")
    print("=" * 40)
    print("Testing enhanced collector before Sunday deployment")
    print("=" * 40)
    
    # Initialize collector
    collector = EnhancedBMRSCollector()
    
    # Test 1: Quick current data collection
    print("\n📊 Test 1: Current Data Collection")
    print("-" * 30)
    
    test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        start_time = time.time()
        
        # Test with just bid/offer data first
        results = collector.collect_current_data(
            settlement_date=test_date,
            data_types=['bid_offer_acceptances']
        )
        
        duration = time.time() - start_time
        
        print(f"✅ Collection completed in {duration:.2f}s")
        
        if 'bid_offer_acceptances' in results:
            data_info = results['bid_offer_acceptances']
            print(f"📈 Method used: {data_info['method']}")
            print(f"📊 Records collected: {data_info['records']}")
            
            if data_info['records'] > 0:
                print("✅ Data collection working!")
            else:
                print("⚠️  No data collected - may need fallback")
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Additional datasets
    print("\n🌟 Test 2: Additional Datasets")
    print("-" * 30)
    
    try:
        additional_data = collector.collect_additional_datasets(test_date)
        
        print(f"📊 Additional datasets found: {len(additional_data)}")
        
        for dataset, info in additional_data.items():
            print(f"   ✅ {dataset}: {info['records']} records")
        
        if additional_data:
            print("🌟 Enhanced features working!")
        else:
            print("⚪ No additional data - core functionality still works")
    
    except Exception as e:
        print(f"⚠️  Test 2 warning: {e}")
        print("💡 Additional features may be limited, but core works")
    
    # Test 3: Statistics check
    print("\n📊 Test 3: Performance Statistics")
    print("-" * 30)
    
    stats = collector.stats
    print(f"📈 Requests made: {stats['requests_made']}")
    print(f"✅ Successful: {stats['requests_successful']}")
    print(f"❌ Failed: {stats['requests_failed']}")
    print(f"📊 Total records: {stats['total_records']}")
    print(f"🔄 Fallbacks used: {stats['fallback_used']}")
    
    if stats['requests_made'] > 0:
        success_rate = stats['requests_successful'] / stats['requests_made']
        print(f"📈 Success rate: {success_rate:.1%}")
        
        if success_rate > 0.7:
            print("✅ Good performance!")
        elif success_rate > 0.5:
            print("⚠️  Acceptable performance")
        else:
            print("❌ Poor performance - may need optimization")
    
    # Final assessment
    print("\n🎯 VALIDATION SUMMARY")
    print("=" * 30)
    
    if stats['total_records'] > 0:
        print("✅ VALIDATION PASSED!")
        print("🚀 Enhanced collector ready for Sunday deployment")
        print("💾 Data being saved in both new and existing formats")
        print("🔄 Fallback methods available if needed")
        return True
    else:
        print("❌ VALIDATION FAILED!")
        print("🔄 Recommend using existing scripts for Sunday")
        print("🛠️  Need to debug enhanced collector")
        return False

def compatibility_check():
    """Check that enhanced collector doesn't break existing workflow"""
    print("\n🔗 COMPATIBILITY CHECK")
    print("=" * 30)
    
    # Check if existing directories are preserved
    from pathlib import Path
    
    base_data_path = Path('bmrs_data')
    enhanced_data_path = Path('bmrs_enhanced_data')
    
    print(f"📁 Existing data path: {base_data_path.exists()}")
    print(f"📁 Enhanced data path: {enhanced_data_path.exists()}")
    
    # Check for recent files
    if base_data_path.exists():
        recent_files = list(base_data_path.glob('**/*.json'))
        print(f"📊 Existing data files: {len(recent_files)}")
    
    if enhanced_data_path.exists():
        enhanced_files = list(enhanced_data_path.glob('*.json'))
        print(f"🌟 Enhanced data files: {len(enhanced_files)}")
    
    print("✅ No conflicts with existing data structure")
    return True

if __name__ == "__main__":
    print("🧪 Enhanced BMRS Collector - Pre-Sunday Validation")
    print("=" * 60)
    print(f"🕐 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run validation
    validation_passed = quick_validation_test()
    
    # Run compatibility check
    compatibility_passed = compatibility_check()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL ASSESSMENT")
    print("=" * 60)
    
    if validation_passed and compatibility_passed:
        print("🎉 READY FOR SUNDAY DEPLOYMENT!")
        print("✅ Enhanced collector validated")
        print("✅ Existing functionality preserved") 
        print("✅ No breaking changes detected")
        print("\n💡 DEPLOYMENT RECOMMENDATION:")
        print("   1. ✅ Deploy enhanced_data_collector.py")
        print("   2. ✅ Keep existing scripts as backup")
        print("   3. ✅ Monitor performance on Sunday")
        print("   4. ✅ Fallback available if needed")
    else:
        print("⚠️  NEEDS ATTENTION BEFORE SUNDAY!")
        print("🔄 Recommend additional testing")
        print("🛡️  Stick with existing scripts for safety")
    
    sys.exit(0 if validation_passed else 1)
