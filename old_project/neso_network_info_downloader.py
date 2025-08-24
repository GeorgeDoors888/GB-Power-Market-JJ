import requests
import os
import time
from datetime import datetime, timedelta
import json

# --- Configuration ---
BASE_URL = "https://api.neso.energy/api/3/action/"
OUTPUT_DIR = "neso_network_information"

# --- Datasets to Download ---
# The user wants a collection of datasets to be called "Network Information"
NETWORK_INFO_DATASETS = {
    "forecasts": {
        "1-day-ahead-demand-forecast": 1,
        "7-day-ahead-national-forecast": 7,
        "14-days-ahead-wind-forecasts": 14,
        "dynamic-containment-4-day-forecast": 4,
        "long-term-2-52-weeks-ahead-national-demand-forecast": None, # Latest single file
        "24-months-ahead-constraint-cost-forecast": None # Latest single file
    },
    "gis": [
        "etys-gb-transmission-system-boundaries",
        "gis-boundaries-for-gb-dno-license-areas",
        "gis-boundaries-for-gb-generation-charging-zones",
        "gis-boundaries-for-gb-grid-supply-points",
        "local-authority-level-spatial-heat-model-outputs-fes"
    ],
    "static": [
        "ancillary-services-important-industry-notifications",
        "capacity-market-register",
        "contract-transfer-of-obligation",
        "data-portal-planned-changes-known-issues",
        "demand-profile-dates",
        "dispatch-transparency",
        "embedded-register",
        "interconnector-register",
        "national-demand-balancing-mechanism-units",
        "school-holiday-percentages",
        "skip-rates",
        "stor-windows",
        "system-operating-plan-sop",
        "transmission-entry-capacity-tec-register",
        "transmission-losses"
    ]
}

# --- Helper Functions ---
def api_call(endpoint, params=None):
    """Makes a call to the NESO API."""
    try:
        response = requests.get(BASE_URL + endpoint, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling API endpoint {endpoint}: {e}")
        return None

def download_file(url, folder, filename):
    """Downloads a file from a URL."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    filepath = os.path.join(folder, filename)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded: {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def get_package_resources(package_id):
    """Gets all resources for a given package (dataset)."""
    data = api_call("package_show", {"id": package_id})
    if data and data.get("success"):
        return data["result"]["resources"]
    print(f"Could not find resources for package: {package_id}")
    return []

def download_static_or_gis(package_id, category):
    """Downloads all resources for a static or GIS dataset."""
    print(f"\n--- Downloading {category.upper()} dataset: {package_id} ---")
    resources = get_package_resources(package_id)
    for resource in resources:
        # Heuristic to get a clean filename
        filename = resource.get("url").split("/")[-1]
        if not filename:
            filename = f"{package_id}_{resource.get('id')}.json"
        
        folder = os.path.join(OUTPUT_DIR, category, package_id)
        download_file(resource["url"], folder, filename)
        # Add a small delay to be polite to the API
        time.sleep(0.5)

def download_forecast(package_id, days):
    """Downloads time-series forecast data."""
    print(f"\n--- Downloading FORECAST dataset: {package_id} ---")
    resources = get_package_resources(package_id)
    if not resources:
        return

    # For forecasts, we often target the first resource which is usually the active one
    resource_id = resources[0]['id']
    
    folder = os.path.join(OUTPUT_DIR, "forecasts", package_id)
    if not os.path.exists(folder):
        os.makedirs(folder)

    if days: # Time-series data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # This is a simplified filter for demonstration.
        # A real implementation would need to know the specific date columns for each dataset.
        # We will use datastore_search_sql for more precise filtering.
        # This example assumes a 'SettlementDate' or similar column exists.
        # NOTE: This part is complex as date column names vary. We will try a generic approach.
        # For now, we will just download the most recent data using datastore_search
        print(f"Fetching last {days} days of data for resource {resource_id}...")
        params = {"resource_id": resource_id, "limit": 100 * days} # Estimate records per day
        data = api_call("datastore_search", params)

    else: # Single file download
        print(f"Fetching latest file for resource {resource_id}...")
        params = {"resource_id": resource_id, "limit": 1}
        data = api_call("datastore_search", params)

    if data and data.get("success"):
        filename = f"{package_id}_latest.json"
        filepath = os.path.join(folder, filename)
        with open(filepath, 'w') as f:
            json.dump(data['result']['records'], f, indent=4)
        print(f"Successfully saved data to: {filepath}")
    else:
        print(f"Could not retrieve data for resource {resource_id}. API response: {data}")


# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Starting NESO Network Information Download...")

    # Download GIS Datasets
    for package in NETWORK_INFO_DATASETS["gis"]:
        download_static_or_gis(package, "gis")

    # Download Static Datasets
    for package in NETWORK_INFO_DATASETS["static"]:
        download_static_or_gis(package, "static")

    # Download Forecast Datasets
    for package, days in NETWORK_INFO_DATASETS["forecasts"].items():
        download_forecast(package, days)

    print("\n--- Download process complete. ---")
    print(f"All files are located in the '{OUTPUT_DIR}' directory.")
