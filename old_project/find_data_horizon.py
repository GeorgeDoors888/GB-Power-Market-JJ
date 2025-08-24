
import requests
from datetime import date, timedelta

def find_earliest_date(dataset_code, api_key):
    """
    Finds the earliest date for which data is available for a given dataset.
    """
    base_url = f"https://data.elexon.co.uk/bmrs/api/v1/datasets/{dataset_code}"
    
    # Start searching from a reasonable date
    current_date = date(2019, 1, 1)
    last_successful_date = None

    print(f"Starting search for dataset {dataset_code}...")

    # Broad search (monthly)
    while current_date > date(2017, 1, 1):
        params = {
            'publishDateTimeFrom': current_date.strftime('%Y-%m-%d'),
            'publishDateTimeTo': current_date.strftime('%Y-%m-%d'),
            'format': 'json',
            'api_key': api_key 
        }
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 200 and response.json().get('data'):
                print(f"SUCCESS: Found data for {current_date.strftime('%Y-%m-%d')}")
                last_successful_date = current_date
                current_date -= timedelta(days=30) # Go back a month
            else:
                print(f"INFO: No data for {current_date.strftime('%Y-%m-%d')}, stopping broad search.")
                break
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed for {current_date.strftime('%Y-%m-%d')}: {e}")
            break
        
    if not last_successful_date:
        print("Could not find any data in the initial search range.")
        return None

    # Fine search (daily)
    current_date = last_successful_date - timedelta(days=1)
    final_date = last_successful_date
    
    print("\nStarting fine search (daily)...")
    while current_date > last_successful_date - timedelta(days=35): # Search around the last success
        params['publishDateTimeFrom'] = current_date.strftime('%Y-%m-%d')
        params['publishDateTimeTo'] = current_date.strftime('%Y-%m-%d')
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 200 and response.json().get('data'):
                print(f"SUCCESS: Found data for {current_date.strftime('%Y-%m-%d')}")
                final_date = current_date
            else:
                print(f"INFO: No data for {current_date.strftime('%Y-%m-%d')}. Stopping.")
                break
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed for {current_date.strftime('%Y-%m-%d')}: {e}")
            break
        current_date -= timedelta(days=1)

    return final_date

if __name__ == '__main__':
    # NOTE: This script requires an API key to be set in an environment variable 
    # or passed directly. For this test, we will assume the key is handled by the API gateway
    # or is not strictly required for basic metadata checks, which might not be true.
    # The downloader script uses a key from a file, but for this standalone test,
    # we will proceed without one initially.
    
    # The BOALF dataset is not found under /datasets, it's a special balancing endpoint
    boalf_endpoint = "https://data.elexon.co.uk/bmrs/api/v1/balancing/bid-offer-acceptances/all"

    # A simplified function for the specific BOALF endpoint
    def find_boalf_horizon():
        current_date = date(2019, 1, 1)
        last_successful_date = None

        print("--- Starting BOALF Horizon Search ---")
        print("--- Phase 1: Monthly Jumps ---")
        
        while current_date.year >= 2018:
            params = {
                'publishDateTimeFrom': current_date.strftime('%Y-%m-%d'),
                'publishDateTimeTo': current_date.strftime('%Y-%m-%d'),
                'format': 'json'
            }
            try:
                response = requests.get(boalf_endpoint, params=params)
                if response.status_code == 200 and len(response.text) > 50: # Check for non-empty response
                    print(f"SUCCESS: Found data around {current_date.strftime('%Y-%m')}")
                    last_successful_date = current_date
                else:
                    print(f"INFO: No data found for {current_date.strftime('%Y-%m')}. Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request failed for {current_date.strftime('%Y-%m')}: {e}")
            
            current_date -= timedelta(days=30)

        if not last_successful_date:
            print("Could not find any BOALF data in 2018 or 2019.")
            return

        print("\n--- Phase 2: Daily Search ---")
        current_date = last_successful_date
        final_date = last_successful_date
        # Go back 35 days from the last successful month
        for i in range(35):
            test_date = current_date - timedelta(days=i)
            params = {
                'publishDateTimeFrom': test_date.strftime('%Y-%m-%d'),
                'publishDateTimeTo': test_date.strftime('%Y-%m-%d'),
                'format': 'json'
            }
            try:
                response = requests.get(boalf_endpoint, params=params)
                if response.status_code == 200 and len(response.text) > 50:
                    print(f"SUCCESS: Found data on {test_date.strftime('%Y-%m-%d')}")
                    final_date = test_date
                else:
                    # Stop once we hit the first day with no data
                    print(f"INFO: No data for {test_date.strftime('%Y-%m-%d')}. Stopping search.")
                    break
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Request failed for {test_date.strftime('%Y-%m-%d')}: {e}")
                break
        
        print(f"\n--- Earliest available date for BOALF data is: {final_date.strftime('%Y-%m-%d')} ---")


    find_boalf_horizon()
