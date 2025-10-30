#!/usr/bin/env python3
"""
Fetch all datasets from DNO OpenDataSoft portals and save to CSV.
"""
import requests
import pandas as pd
from datetime import datetime
import urllib3

# Disable SSL warnings for SPEN and ENWL (certificate issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------
# CONFIGURATION: DNO portals
# ----------------------------
DNO_PORTALS = {
    # Phase 1 - ✅ Working
    "UKPN": "https://ukpowernetworks.opendatasoft.com",
    "ENWL": "https://electricitynorthwest.opendatasoft.com",
    # Phase 2 - ✅ Working
    "NPg": "https://northernpowergrid.opendatasoft.com",
    # Phase 3 - ✅ Working (requires SSL verification disabled)
    "SPEN": "https://spenergynetworks.opendatasoft.com",
    # Phase 4 - ✅ Working (Transmission only, not Distribution)
    "SSEN": "https://ssentransmission.opendatasoft.com",
    # Phase 5 - ❌ No OpenDataSoft portal found
    # "NGED": None  # Commented out - no public OpenDataSoft portal exists
}

# ----------------------------
# FUNCTION: fetch all datasets for a given DNO
# ----------------------------
def fetch_portal_datasets(dno_group, base_url):
    print(f"\n🔹 Fetching datasets for {dno_group} ({base_url}) ...")
    datasets = []
    catalog_url = f"{base_url}/api/explore/v2.1/catalog/datasets"
    
    # Fetch all datasets with pagination
    offset = 0
    limit = 100
    total_count = None
    
    while True:
        try:
            # SPEN and ENWL require SSL verification to be disabled due to certificate issues
            verify_ssl = (dno_group not in ["SPEN", "ENWL"])
            r = requests.get(catalog_url, params={'limit': limit, 'offset': offset}, 
                           timeout=60, verify=verify_ssl)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"⚠️ Error fetching catalog for {dno_group}: {e}")
            break
        
        if total_count is None:
            total_count = data.get("total_count", 0)
            print(f"   Total datasets: {total_count}")
        
        results = data.get("results", [])
        if not results:
            break
        
        # API v2.1 uses "results" not "datasets"
        for ds in results:
            dataset_id = ds.get("dataset_id")
            metas = ds.get("metas", {})
            
            # Extract metadata
            title = metas.get("default", {}).get("title", dataset_id)
            description = metas.get("default", {}).get("description", "")
            keywords = metas.get("default", {}).get("keyword", [])
            modified = metas.get("default", {}).get("modified", "")
            license_ = metas.get("default", {}).get("license", "")
            
            visibility = ds.get("visibility", "public")
            has_records = ds.get("has_records", False)
            tags = ", ".join(keywords) if isinstance(keywords, list) else ""
            
            explore_link = f"{base_url}/explore/dataset/{dataset_id}/"
            api_link = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}"
            
            # Try to get record count from the dataset info
            record_count = ""
            if has_records:
                try:
                    records_url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
                    rc = requests.get(records_url + "?limit=0", timeout=20).json()
                    record_count = rc.get("total_count", "")
                except Exception:
                    pass
            
            datasets.append({
                "portal": base_url.replace("https://", ""),
                "DNO_Group": dno_group,
                "dataset_id": dataset_id,
                "title": title,
                "description": description,
                "modified": modified,
                "license": license_,
                "visibility": visibility,
                "has_records": has_records,
                "tags": tags,
                "record_count": record_count,
                "explore_link": explore_link,
                "api_link": api_link
            })
        
        # Check if we got all datasets
        offset += limit
        if offset >= total_count:
            break
    
    print(f"✅ {len(datasets)} datasets fetched for {dno_group}")
    return datasets

# ----------------------------
# MAIN SCRIPT EXECUTION
# ----------------------------
if __name__ == '__main__':
    all_datasets = []

    for dno_group, base_url in DNO_PORTALS.items():
        data = fetch_portal_datasets(dno_group, base_url)
        all_datasets.extend(data)

    # Combine all into one DataFrame
    df = pd.DataFrame(all_datasets)
    
    if len(df) == 0:
        print("\n❌ No datasets found!")
        exit(0)
    
    df["modified"] = pd.to_datetime(df["modified"], errors="coerce")
    df.sort_values(["DNO_Group", "modified"], ascending=[True, False], inplace=True)

    # Save individual files by DNO group
    for dno_group in df["DNO_Group"].unique():
        subset = df[df["DNO_Group"] == dno_group]
        filename = f"dno_datasets_{dno_group.lower()}_full.csv"
        subset.to_csv(filename, index=False)
        print(f"💾 Saved {len(subset)} rows → {filename}")

    # Save master merged file
    master_filename = "dno_datasets_master_full.csv"
    df.to_csv(master_filename, index=False)
    print(f"\n🎯 Saved combined master file → {master_filename}")
    print(f"Total datasets across all DNOs: {len(df)}")
