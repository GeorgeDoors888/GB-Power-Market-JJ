import requests
import os
import json
import subprocess
from pathlib import Path
import asyncio
import aiohttp
from datetime import datetime

def load_api_keys():
    """Loads one or more API keys from the environment file."""
    api_env_file = 'api.env'
    if not Path(api_env_file).exists():
        return []
    
    keys = []
    with open(api_env_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('BMRS_API_KEY'):
                try:
                    key = line.split('=', 1)[1].strip().strip('\'"')
                    if key:
                        keys.append(key)
                except IndexError:
                    continue
    return keys

def check_gcp_credentials():
    """Checks Google Cloud credentials."""
    print("\n=== Google Cloud Credentials Check ===")
    
    # Check client_secret.json
    if Path("client_secret.json").exists():
        print("✅ client_secret.json file exists")
        try:
            with open("client_secret.json", "r") as f:
                data = json.load(f)
            if "installed" in data or "web" in data:
                print("✅ client_secret.json appears to be valid")
            else:
                print("❌ client_secret.json does not contain expected fields")
        except:
            print("❌ client_secret.json is not valid JSON")
    else:
        print("❌ client_secret.json file not found")
    
    # Check application default credentials
    adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
    if adc_path.exists():
        print("✅ Application Default Credentials exist")
    else:
        print("❌ Application Default Credentials not found")
    
    # Check gcloud auth
    try:
        result = subprocess.run(["gcloud", "auth", "list"], 
                               capture_output=True, text=True, check=True)
        if "No credentialed accounts" in result.stdout:
            print("❌ No gcloud authenticated accounts found")
        else:
            print("✅ gcloud authentication is set up")
    except Exception as e:
        print(f"❌ Error checking gcloud authentication: {e}")
    
    # Check project
    try:
        result = subprocess.run(["gcloud", "config", "get-value", "project"], 
                               capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"✅ Current project: {result.stdout.strip()}")
        else:
            print("❌ No project configured in gcloud")
    except Exception as e:
        print(f"❌ Error checking gcloud project: {e}")
    
    # Check BigQuery access
    try:
        result = subprocess.run(["bq", "ls"], 
                               capture_output=True, text=True, check=True)
        print("✅ Successfully accessed BigQuery")
    except Exception as e:
        print(f"❌ Error accessing BigQuery: {e}")
    
    # Check Cloud Storage access
    try:
        result = subprocess.run(["gsutil", "ls"], 
                               capture_output=True, text=True, check=True)
        print("✅ Successfully accessed Cloud Storage")
    except Exception as e:
        print(f"❌ Error accessing Cloud Storage: {e}")

async def check_key(session, key, key_num):
    """Checks a single API key."""
    # A simple, lightweight endpoint for testing
    test_url = f"https://data.elexon.co.uk/bmrs/api/v1/balancing/acceptances/all?settlementDate=2025-08-20&settlementPeriod=1&apikey={key}"
    try:
        async with session.get(test_url, timeout=15) as response:
            if response.status == 200:
                print(f"  - Key #{key_num:02d}: VALID")
                return True
            elif response.status == 403:
                print(f"  - Key #{key_num:02d}: INVALID (Forbidden/Inactive)")
                return False
            else:
                print(f"  - Key #{key_num:02d}: FAILED (HTTP Status: {response.status})")
                return False
    except Exception as e:
        print(f"  - Key #{key_num:02d}: FAILED (Error: {e.__class__.__name__})")
        return False

async def main():
    """Main function to load and check all keys."""
    print("🔍 Reading API keys from api.env...")
    api_keys = load_api_keys()

    if not api_keys:
        print("❌ No API keys found in api.env file.")
    else:
        print(f"✅ Found {len(api_keys)} API keys.")
        print("\n=== API Key Validation ===")
        
        # Set up async HTTP session for key validation
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i, key in enumerate(api_keys, 1):
                tasks.append(check_key(session, key, i))
            
            # Run all validation checks concurrently
            results = await asyncio.gather(*tasks)
            
            # Count valid keys
            valid_count = sum(1 for r in results if r)
            print(f"\n✅ {valid_count}/{len(api_keys)} API keys are valid.")
    
    # Check Google Cloud credentials
    check_gcp_credentials()
    
    print("\n=== Checks completed ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("=== API Key & Credentials Check ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {os.getcwd()}")
    
    asyncio.run(main())

    print(f"Found {len(api_keys)} API keys. Starting validation...\n")
    
    valid_count = 0
    async with aiohttp.ClientSession() as session:
        tasks = [check_key(session, key, i+1) for i, key in enumerate(api_keys)]
        results = await asyncio.gather(*tasks)
        valid_count = sum(1 for r in results if r)

    print("\n---------------------------------")
    print("✅ Validation Complete.")
    print(f"Total Keys Found: {len(api_keys)}")
    print(f"Valid Keys:       {valid_count}")
    print(f"Invalid/Failed:   {len(api_keys) - valid_count}")
    print("---------------------------------")

if __name__ == "__main__":
    asyncio.run(main())
