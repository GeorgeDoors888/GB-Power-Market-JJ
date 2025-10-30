#!/usr/bin/env python3
"""
Auto-discover all available Elexon datasets from the BMRS API
Generates a comprehensive manifest file for downloading
"""

import json
import os
import httpx
from typing import Dict, List, Any

# Elexon Insights API base URL
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
API_KEY = os.getenv("BMRS_API_KEY_1", "")

# Known dataset categories and endpoints from Elexon documentation
DATASET_ENDPOINTS = [
    # System data
    {"code": "FREQ", "route": "/datasets/FREQ/stream", "name": "System Frequency"},
    {"code": "SYSWARN", "route": "/datasets/SYSWARN/stream", "name": "System Warnings"},
    {"code": "TEMPO", "route": "/datasets/TEMPO/stream", "name": "Temperature Data"},
    
    # Demand data
    {"code": "ITSDO", "route": "/datasets/ITSDO/stream", "name": "Initial Transmission System Demand Outturn"},
    {"code": "MELIMBALNGC", "route": "/datasets/MELIMBALNGC/stream", "name": "Imbalance Prices"},
    {"code": "NDF", "route": "/datasets/NDF/stream", "name": "National Demand Forecast"},
    {"code": "NDFD", "route": "/datasets/NDFD/stream", "name": "National Demand Forecast (Day Ahead)"},
    {"code": "NDFW", "route": "/datasets/NDFW/stream", "name": "National Demand Forecast (Week Ahead)"},
    {"code": "TSDFD", "route": "/datasets/TSDFD/stream", "name": "Transmission System Demand Forecast"},
    {"code": "TSDF", "route": "/datasets/TSDF/stream", "name": "Transmission System Demand Forecast (Day Ahead)"},
    {"code": "ROLSYSDEM", "route": "/datasets/ROLSYSDEM/stream", "name": "Rolling System Demand"},
    
    # Generation data
    {"code": "FUELINST", "route": "/datasets/FUELINST/stream", "name": "Generation by Fuel Type (Instant)"},
    {"code": "FUELHH", "route": "/datasets/FUELHH/stream", "name": "Generation by Fuel Type (Half Hourly)"},
    {"code": "WINDFOR", "route": "/datasets/WINDFOR/stream", "name": "Wind Generation Forecast"},
    {"code": "INDGEN", "route": "/datasets/INDGEN/stream", "name": "Generation by Individual BM Unit"},
    {"code": "INDOD", "route": "/datasets/INDOD/stream", "name": "Initial National Demand Outturn Daily"},
    {"code": "FORDAYDEM", "route": "/datasets/FORDAYDEM/stream", "name": "Day Ahead Demand"},
    
    # Balancing Mechanism
    {"code": "BOD", "route": "/datasets/BOD/stream", "name": "Bid Offer Data"},
    {"code": "DISBSAD", "route": "/datasets/DISBSAD/stream", "name": "Disaggregated Balancing Services Adjustment Data"},
    {"code": "NETBSAD", "route": "/datasets/NETBSAD/stream", "name": "Net Balancing Services Adjustment Data"},
    {"code": "QAS", "route": "/datasets/QAS/stream", "name": "Quiescent Physical Notifications"},
    {"code": "MID", "route": "/datasets/MID/stream", "name": "Market Index Data"},
    {"code": "MSGARMGIN", "route": "/datasets/MSGARMGIN/stream", "name": "Margin Notice"},
    {"code": "INDOITSDO", "route": "/datasets/INDOITSDO/stream", "name": "Initial National Demand Outturn Instantaneous"},
    
    # Settlement
    {"code": "DETSYSPRICES", "route": "/datasets/DETSYSPRICES/stream", "name": "Detailed System Prices"},
    {"code": "CDN", "route": "/datasets/CDN/stream", "name": "Credit Default Notice"},
    {"code": "SYSDEMDATA", "route": "/datasets/SYSDEMDATA/stream", "name": "System Demand Data"},
    
    # Interconnector
    {"code": "INTERFUELHH", "route": "/datasets/INTERFUELHH/stream", "name": "Interconnector Fuel (Half Hourly)"},
    {"code": "NONBM", "route": "/datasets/NONBM/stream", "name": "Non-BM STOR"},
    
    # Market Data
    {"code": "IMBALNGC", "route": "/datasets/IMBALNGC/stream", "name": "Imbalance Prices"},
    {"code": "MIL", "route": "/datasets/MIL/stream", "name": "Maximum Import Limit"},
    {"code": "MEL", "route": "/datasets/MEL/stream", "name": "Maximum Export Limit"},
    {"code": "SEL", "route": "/datasets/SEL/stream", "name": "Stable Export Limit"},
    {"code": "PHYBMDATA", "route": "/datasets/PHYBMDATA/stream", "name": "Physical BM Unit Data"},
    {"code": "SOSO", "route": "/datasets/SOSO/stream", "name": "SO-SO Prices"},
    
    # System Operator Data
    {"code": "LOLPDRM", "route": "/datasets/LOLPDRM/stream", "name": "Loss of Load Probability De-rated Margin"},
    {"code": "OCNMFW", "route": "/datasets/OCNMFW/stream", "name": "Output Usable by Fuel Type"},
    {"code": "OCNMF2T", "route": "/datasets/OCNMF2T/stream", "name": "Output Usable by Fuel Type (2-14 Days)"},
    {"code": "OCNMF2T52W", "route": "/datasets/OCNMF2T52W", "name": "Output Usable by Fuel Type (2-52 Weeks)"},
    
    # Reference/Balancing data
    {"code": "REMIT", "route": "/datasets/REMIT/stream", "name": "REMIT Messages"},
    {"code": "UOU2T14D", "route": "/datasets/UOU2T14D/stream", "name": "2-14 Days Ahead Output Usable"},
    {"code": "UOU2T52W", "route": "/datasets/UOU2T52W/stream", "name": "2-52 Weeks Ahead Output Usable"},
    
    # Legacy/Additional REST endpoints (non-stream)
    {"code": "DEMAND_OUTTURN", "route": "/demand/outturn", "name": "Demand Outturn Total"},
    {"code": "GENERATION_OUTTURN", "route": "/generation/outturn/summary", "name": "Generation Outturn Summary"},
    {"code": "GENERATION_ACTUAL", "route": "/generation/actual/per-type", "name": "Actual Generation per Type"},
    {"code": "BALANCING_SERVICES", "route": "/balancing/settlement/stack", "name": "Balancing Services Adjustment"},
    {"code": "SYSTEM_PRICES", "route": "/system/prices", "name": "System Prices"},
    {"code": "IMBALANCE_PRICES", "route": "/balancing/settlement/system-prices", "name": "Imbalance Settlement Prices"},
    {"code": "DERIVED_DATA", "route": "/datasets/derived", "name": "Derived System Data"},
]

def test_endpoint(code: str, route: str, name: str) -> Dict[str, Any]:
    """Test if an endpoint is accessible and return metadata"""
    from datetime import date, timedelta
    
    # Test with a small date range
    end_date = date.today()
    start_date = end_date - timedelta(days=1)
    
    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "format": "json"
    }
    
    if API_KEY:
        params["apiKey"] = API_KEY
    
    url = f"{BASE_URL}{route}"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params, follow_redirects=True)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check if we got data
                    if isinstance(data, dict):
                        records = data.get("data", [])
                    elif isinstance(data, list):
                        records = data
                    else:
                        records = []
                    
                    return {
                        "code": code,
                        "route": route,
                        "name": name,
                        "status": "available",
                        "sample_size": len(records) if isinstance(records, list) else 1,
                        "bq_table": f"uk_energy_prod.{code.lower()}"
                    }
                except json.JSONDecodeError:
                    return {
                        "code": code,
                        "route": route,
                        "name": name,
                        "status": "invalid_json",
                        "bq_table": f"uk_energy_prod.{code.lower()}"
                    }
            else:
                return {
                    "code": code,
                    "route": route,
                    "name": name,
                    "status": f"http_{response.status_code}",
                    "bq_table": f"uk_energy_prod.{code.lower()}"
                }
    except httpx.TimeoutException:
        return {
            "code": code,
            "route": route,
            "name": name,
            "status": "timeout",
            "bq_table": f"uk_energy_prod.{code.lower()}"
        }
    except Exception as e:
        return {
            "code": code,
            "route": route,
            "name": name,
            "status": f"error: {str(e)}",
            "bq_table": f"uk_energy_prod.{code.lower()}"
        }

def main():
    print("=" * 80)
    print("🔍 Discovering Elexon BMRS API Datasets")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing {len(DATASET_ENDPOINTS)} known endpoints...")
    print()
    
    available_datasets = {}
    unavailable_datasets = []
    
    for idx, endpoint in enumerate(DATASET_ENDPOINTS, 1):
        code = endpoint["code"]
        route = endpoint["route"]
        name = endpoint["name"]
        
        print(f"[{idx}/{len(DATASET_ENDPOINTS)}] Testing {code}: {name}")
        result = test_endpoint(code, route, name)
        
        if result["status"] == "available":
            print(f"  ✅ Available - {result.get('sample_size', 0)} records in test")
            available_datasets[code] = {
                "route": route,
                "name": name,
                "params": {"from": "{start_iso}", "to": "{end_iso}"},
                "bq_table": result["bq_table"]
            }
        else:
            print(f"  ❌ {result['status']}")
            unavailable_datasets.append(result)
    
    print()
    print("=" * 80)
    print(f"✅ Available datasets: {len(available_datasets)}")
    print(f"❌ Unavailable datasets: {len(unavailable_datasets)}")
    print("=" * 80)
    print()
    
    # Create comprehensive manifest
    manifest = {
        "base_url": BASE_URL,
        "auth": {
            "header": "apiKey",
            "value_env": "BMRS_API_KEY_1"
        },
        "datasets": available_datasets
    }
    
    # Save to file
    output_file = "insights_manifest_complete.json"
    with open(output_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"💾 Saved complete manifest to: {output_file}")
    print(f"📊 Total available datasets: {len(available_datasets)}")
    print()
    
    # Show unavailable datasets
    if unavailable_datasets:
        print("⚠️  Unavailable datasets:")
        for ds in unavailable_datasets:
            print(f"  - {ds['code']}: {ds['status']}")
    
    print()
    print("✅ Discovery complete!")
    print(f"You can now use: python download_last_7_days.py --manifest {output_file}")

if __name__ == "__main__":
    main()
