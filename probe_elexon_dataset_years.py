
import requests
import json
from datetime import datetime

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
API_KEY_FILE = "api.env"
API_KEYS = []
# Load all BMRS_API_KEY_X keys from api.env
with open(API_KEY_FILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "BMRS_API_KEY" in line:
            API_KEYS.append(line.split("=")[-1].strip())
if not API_KEYS:
    raise RuntimeError("No BMRS_API_KEYs found in api.env")

def get_dataset_list():
    params = {"apiKey": API_KEYS[0]}
    url = f"{ELEXON_BASE_URL}/datasets"
    try:
        resp = requests.get(url, params=params, timeout=30)
        print(f"Fetching dataset list: {url} {params} -> {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data:
                return [d["name"] for d in data["data"] if "name" in d]
            elif isinstance(data, list):
                return [d["name"] for d in data if "name" in d]
        else:
            print(f"Failed to fetch dataset list: {resp.text}")
    except Exception as e:
        print(f"ERROR fetching dataset list: {e}")
    return []

def probe_dataset_years(dataset_id, start_year, end_year):
    available_years = []
    key_idx = 0
    for year in range(start_year, end_year + 1):
        params = {
            "from": f"{year}-01-01",
            "to": f"{year}-01-02",
            "format": "json",
            "apiKey": API_KEYS[key_idx % len(API_KEYS)]
        }
        url = f"{ELEXON_BASE_URL}/datasets/{dataset_id}"
        try:
            resp = requests.get(url, params=params, timeout=30)
            print(f"DEBUG: {url} {params} -> {resp.status_code}")
            try:
                print(f"RESPONSE: {resp.text[:300]}")
            except Exception:
                pass
            if resp.status_code == 200 and resp.json().get("data"):
                available_years.append(year)
            elif resp.status_code == 200:
                available_years.append(year)
        except Exception as e:
            print(f"ERROR: {e}")
        key_idx += 1
    return available_years


def main():
    start_year = 2016
    end_year = datetime.now().year
    dataset_ids = get_dataset_list()
    if not dataset_ids:
        print("No datasets found from API. Exiting.")
        return
    mapping = {}
    for ds in dataset_ids:
        print(f"Probing {ds}...")
        years = probe_dataset_years(ds, start_year, end_year)
        mapping[ds] = years
        print(f"  Available years: {years}")
    with open("elexon_dataset_years.json", "w") as f:
        json.dump(mapping, f, indent=2)
    print("\nSaved mapping to elexon_dataset_years.json")

    dataset_ids = get_dataset_list()
    if not dataset_ids:
        print("No datasets found from API. Exiting.")
        return
    mapping = {}
    for ds in dataset_ids:
        print(f"Probing {ds}...")
        years = probe_dataset_years(ds, start_year, end_year)
        mapping[ds] = years
        print(f"  Available years: {years}")
    with open("elexon_dataset_years.json", "w") as f:
        json.dump(mapping, f, indent=2)
    print("\nSaved mapping to elexon_dataset_years.json")

if __name__ == "__main__":
    main()
