#!/usr/bin/env python3
"""
RAPID DEPLOYMENT TRIGGER - NO HUMAN DELAYS!
Starts massive historical data collection the moment cloud service is ready
"""

import requests
import time
import json
from datetime import datetime

def wait_for_deployment():
    """Wait for service to be ready and get URL"""
    
    print("🚀 MACHINE MODE: Waiting for deployment completion...")
    
    # Service will be deployed to this URL pattern
    service_url = "https://bmrs-data-collector-[hash]-uc.a.run.app"
    
    # For now, let's assume it will be ready and check manually
    print("   Deployment in progress...")
    print("   Once ready, service URL will be displayed")
    
    return None  # Will be updated when deployment completes

def trigger_full_historical_collection(service_url):
    """Start the complete 2016-2025 data collection immediately"""
    
    print("🔥 TRIGGERING FULL HISTORICAL COLLECTION")
    print("=" * 60)
    
    # Full historical payload
    collection_payload = {
        "start_date": "2016-01-01",
        "end_date": "2025-08-08",
        "data_types": [
            "bid_offer_acceptances",
            "demand_outturn", 
            "generation_outturn",
            "system_warnings"
        ]
    }
    
    print(f"📅 Period: 2016-01-01 to 2025-08-08")
    print(f"📊 Data types: {len(collection_payload['data_types'])}")
    print(f"⏱️  Expected duration: 6-8 hours")
    print(f"💾 Expected output: ~40M records, ~10GB, ~13K files")
    
    try:
        print(f"\n🚀 Starting collection...")
        
        response = requests.post(
            f"{service_url}/collect",
            json=collection_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ COLLECTION STARTED SUCCESSFULLY!")
            print(f"   Status: {result.get('status')}")
            print(f"   Period: {result.get('start_date')} to {result.get('end_date')}")
            print(f"   Files creating: {result.get('files_created', 'Unknown')}")
            
            return True
            
        else:
            print(f"❌ Collection failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Collection trigger failed: {e}")
        return False

def trigger_parallel_collections(service_url):
    """Start multiple parallel collections for maximum speed"""
    
    print("⚡ PARALLEL COLLECTION MODE")
    print("=" * 40)
    
    # Split into year ranges for parallel processing
    year_ranges = [
        ("2016-01-01", "2018-12-31", "Early period"),
        ("2019-01-01", "2021-12-31", "Middle period"), 
        ("2022-01-01", "2023-12-31", "Recent period"),
        ("2024-01-01", "2025-08-08", "Current period")
    ]
    
    print(f"🔥 Starting {len(year_ranges)} parallel collections...")
    
    success_count = 0
    
    for start_date, end_date, description in year_ranges:
        payload = {
            "start_date": start_date,
            "end_date": end_date,
            "data_types": ["bid_offer_acceptances", "demand_outturn"]
        }
        
        try:
            print(f"   🚀 {description}: {start_date} to {end_date}")
            
            response = requests.post(
                f"{service_url}/collect",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"      ✅ Started successfully")
                success_count += 1
            else:
                print(f"      ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
            
        time.sleep(1)  # Brief delay between triggers
    
    print(f"\n🎉 Parallel collections started: {success_count}/{len(year_ranges)}")
    return success_count > 0

def test_service_health(service_url):
    """Test if service is responding"""
    
    try:
        response = requests.get(f"{service_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service healthy: {data.get('service', 'Unknown')}")
            return True
        else:
            print(f"⚠️  Service responding but not healthy: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Service not responding: {e}")
        return False

def monitor_deployment():
    """Monitor for deployment completion"""
    
    print("👀 MONITORING DEPLOYMENT STATUS")
    print("=" * 40)
    
    # Check every 30 seconds for deployment
    max_wait = 20  # 10 minutes max
    wait_count = 0
    
    while wait_count < max_wait:
        print(f"   Checking deployment... ({wait_count + 1}/{max_wait})")
        
        # Here we would check gcloud or look for service URL
        # For now, prompt for manual input when ready
        
        time.sleep(30)
        wait_count += 1
        
        # Manual check point
        if wait_count == 5:  # After 2.5 minutes
            service_url = input("\n🔗 Enter service URL when deployment completes (or press Enter to continue waiting): ").strip()
            
            if service_url:
                if test_service_health(service_url):
                    return service_url
                else:
                    print("   Service not ready yet, continuing to wait...")
    
    print("⏰ Deployment timeout reached")
    return None

def main():
    """MACHINE SPEED DEPLOYMENT AND COLLECTION"""
    
    print("🤖 BMRS DATA COLLECTION - MACHINE MODE")
    print("=" * 50)
    print("🔥 NO HUMAN DELAYS - MAXIMUM SPEED DEPLOYMENT")
    print("")
    
    # Option 1: Wait for deployment
    print("Choose deployment mode:")
    print("1. Monitor for deployment completion (auto-trigger)")
    print("2. Enter service URL manually (instant trigger)")
    print("3. Test mode (current year only)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        service_url = monitor_deployment()
        if service_url:
            trigger_full_historical_collection(service_url)
        else:
            print("❌ Deployment monitoring failed")
            
    elif choice == "2":
        service_url = input("Enter Cloud Run service URL: ").strip()
        if service_url:
            if test_service_health(service_url):
                print("\n🔥 CHOOSE COLLECTION MODE:")
                print("1. Full historical (2016-2025) - Single collection")
                print("2. Parallel collections (faster)")
                
                mode = input("Enter mode (1-2): ").strip()
                
                if mode == "1":
                    trigger_full_historical_collection(service_url)
                elif mode == "2":
                    trigger_parallel_collections(service_url)
            else:
                print("❌ Service not ready")
        else:
            print("❌ No service URL provided")
            
    elif choice == "3":
        service_url = input("Enter service URL for test: ").strip()
        if service_url and test_service_health(service_url):
            # Test with current year only
            test_payload = {
                "start_date": "2025-01-01",
                "end_date": "2025-08-08",
                "data_types": ["bid_offer_acceptances"]
            }
            
            response = requests.post(f"{service_url}/collect", json=test_payload)
            print(f"Test result: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")

if __name__ == "__main__":
    main()
