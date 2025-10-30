#!/usr/bin/env python3
"""
Dynamic Dataset Discovery for Elexon BMRS API
Queries the API's metadata endpoint to discover ALL available datasets
NO hardcoded lists - fully automatic and self-updating!
"""

import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

# Elexon Insights API base URL
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
API_KEY = os.getenv("BMRS_API_KEY_1", "")

# Special endpoint configurations for known constraints
SPECIAL_CONFIGS = {
    "MELS": {"max_hours": 1, "note": "Maximum Export Limit - requires 1-hour max range"},
    "MILS": {"max_hours": 1, "note": "Maximum Import Limit - requires 1-hour max range"},
    "BOALF": {"max_days": 1, "note": "Bid Offer Acceptance Level - requires 1-day max range"},
    "NONBM": {"max_days": 1, "note": "Non-BM STOR - requires 1-day max range"},
}


def get_all_dataset_codes() -> List[str]:
    """
    Query the API metadata endpoint to get ALL available dataset codes
    Returns: List of dataset code strings (e.g., ['FREQ', 'FUELHH', 'PN', ...])
    """
    print("🔍 Querying API metadata endpoint for available datasets...")
    
    metadata_url = f"{BASE_URL}/datasets/metadata/latest"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(metadata_url, follow_redirects=True)
            
            if response.status_code != 200:
                print(f"❌ Metadata endpoint returned {response.status_code}")
                return []
            
            metadata = response.json()
            dataset_codes = [item['dataset'] for item in metadata.get('data', [])]
            
            print(f"✅ Found {len(dataset_codes)} datasets in API metadata")
            return dataset_codes
            
    except Exception as e:
        print(f"❌ Error fetching metadata: {e}")
        return []


def test_dataset_endpoint(code: str, test_range: Tuple[str, str]) -> Dict[str, Any]:
    """
    Test a dataset endpoint to see if it's accessible and working
    
    Args:
        code: Dataset code (e.g., 'FREQ', 'PN')
        test_range: Tuple of (start_iso, end_iso) datetime strings
        
    Returns:
        Dictionary with test results and metadata
    """
    route = f"/datasets/{code}/stream"
    url = f"{BASE_URL}{route}"
    
    params = {
        "from": test_range[0],
        "to": test_range[1],
        "format": "json"
    }
    
    if API_KEY:
        params["apiKey"] = API_KEY
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params, follow_redirects=True)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Handle both list and dict responses
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict):
                        records = data.get('data', [])
                    else:
                        records = []
                    
                    # Check for nested data structures
                    has_nested = False
                    if records and isinstance(records, list) and len(records) > 0:
                        first_record = records[0]
                        if isinstance(first_record, dict):
                            # Check if any field contains lists or nested objects
                            for key, value in first_record.items():
                                if isinstance(value, (list, dict)):
                                    has_nested = True
                                    break
                    
                    result = {
                        "code": code,
                        "route": route,
                        "name": f"{code} Dataset",
                        "category": "discovered",
                        "status": "available",
                        "sample_size": len(records) if isinstance(records, list) else 0,
                        "has_nested_structure": has_nested,
                        "bq_table": f"uk_energy_prod.{code.lower().replace('-', '_')}"
                    }
                    
                    # Add special config if exists
                    if code in SPECIAL_CONFIGS:
                        result["special_config"] = SPECIAL_CONFIGS[code]
                    
                    return result
                    
                except json.JSONDecodeError:
                    return {
                        "code": code,
                        "route": route,
                        "status": "invalid_json",
                        "error": "Response is not valid JSON"
                    }
                    
            elif response.status_code == 400:
                # May need special parameters (shorter range)
                error_msg = "Unknown"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_data.get('error', str(error_data)))
                except:
                    error_msg = response.text[:200]
                
                return {
                    "code": code,
                    "route": route,
                    "status": "needs_special_params",
                    "error": error_msg,
                    "note": "May require 1-hour or 1-day max range"
                }
                
            elif response.status_code == 404:
                return {
                    "code": code,
                    "route": route,
                    "status": "not_found_404",
                    "error": "Endpoint not found (may not support stream format)"
                }
                
            else:
                return {
                    "code": code,
                    "route": route,
                    "status": f"http_{response.status_code}",
                    "error": response.text[:200]
                }
                
    except httpx.TimeoutException:
        return {
            "code": code,
            "route": route,
            "status": "timeout",
            "error": "Request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "code": code,
            "route": route,
            "status": "error",
            "error": str(e)
        }


def test_with_shorter_range(code: str) -> Dict[str, Any]:
    """
    Test dataset with 1-hour range for datasets that may have constraints
    """
    end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=1)
    
    test_range = (
        start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    
    print(f"  🔄 Retrying {code} with 1-hour range...")
    return test_dataset_endpoint(code, test_range)


def discover_all_datasets_dynamic() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Main discovery function - finds all datasets dynamically
    
    Returns:
        Tuple of (available_datasets_dict, failed_datasets_list)
    """
    # Step 1: Get all dataset codes from metadata
    dataset_codes = get_all_dataset_codes()
    
    if not dataset_codes:
        print("❌ No datasets found in metadata. Cannot proceed.")
        return {}, []
    
    print(f"\n📊 Testing {len(dataset_codes)} datasets...")
    print("=" * 80)
    
    # Step 2: Test each dataset with 7-day range
    available_datasets = {}
    failed_datasets = []
    needs_retry = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    test_range_7d = (
        start_date.strftime("%Y-%m-%dT00:00:00Z"),
        end_date.strftime("%Y-%m-%dT23:59:59Z")
    )
    
    for idx, code in enumerate(dataset_codes, 1):
        print(f"[{idx}/{len(dataset_codes)}] Testing {code}...", end=" ")
        
        result = test_dataset_endpoint(code, test_range_7d)
        
        if result["status"] == "available":
            print(f"✅ {result['sample_size']} records")
            if result.get("has_nested_structure"):
                print(f"          ⚠️  Has nested structure - may need flattening")
            
            available_datasets[code] = {
                "route": result["route"],
                "name": result["name"],
                "category": result["category"],
                "bq_table": result["bq_table"]
            }
            
            if result.get("special_config"):
                available_datasets[code]["special_config"] = result["special_config"]
            if result.get("has_nested_structure"):
                available_datasets[code]["has_nested_structure"] = True
                
        elif result["status"] == "needs_special_params":
            print(f"⚠️  Needs special params")
            needs_retry.append(code)
            
        else:
            print(f"❌ {result['status']}")
            failed_datasets.append(result)
    
    # Step 3: Retry failed ones with shorter range
    if needs_retry:
        print(f"\n🔄 Retrying {len(needs_retry)} datasets with 1-hour range...")
        print("=" * 80)
        
        for code in needs_retry:
            result = test_with_shorter_range(code)
            
            if result["status"] == "available":
                print(f"  ✅ {code}: Works with 1-hour range ({result['sample_size']} records)")
                available_datasets[code] = {
                    "route": result["route"],
                    "name": result["name"],
                    "category": result["category"],
                    "bq_table": result["bq_table"],
                    "special_config": SPECIAL_CONFIGS.get(code, {"max_hours": 1})
                }
            else:
                print(f"  ❌ {code}: Still failing - {result['status']}")
                failed_datasets.append(result)
    
    return available_datasets, failed_datasets


def save_results(available: Dict[str, Any], failed: List[Dict[str, Any]]) -> None:
    """Save discovery results to files"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create manifest for download scripts
    manifest = {
        "discovered_at": datetime.now().isoformat(),
        "discovery_method": "dynamic_metadata_query",
        "base_url": BASE_URL,
        "auth": {
            "header": "apiKey",
            "value_env": "BMRS_API_KEY_1"
        },
        "total_available": len(available),
        "total_failed": len(failed),
        "datasets": available
    }
    
    manifest_file = "insights_manifest_dynamic.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"💾 Saved manifest: {manifest_file}")
    
    # Save detailed results including failures
    detailed_results = {
        "discovered_at": datetime.now().isoformat(),
        "discovery_method": "dynamic_metadata_query",
        "summary": {
            "total_discovered": len(get_all_dataset_codes()),
            "total_available": len(available),
            "total_failed": len(failed),
            "success_rate": f"{len(available)/(len(available)+len(failed))*100:.1f}%"
        },
        "available_datasets": available,
        "failed_datasets": failed
    }
    
    detailed_file = f"discovery_results_dynamic_{timestamp}.json"
    with open(detailed_file, "w") as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"💾 Saved detailed results: {detailed_file}")
    
    # Create human-readable summary
    summary_md = f"""# Dynamic Dataset Discovery Results

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Method**: Dynamic metadata query (no hardcoded lists)

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total datasets in API | {len(get_all_dataset_codes())} |
| Successfully discovered | {len(available)} |
| Failed/unavailable | {len(failed)} |
| Success rate | {len(available)/(len(available)+len(failed))*100:.1f}% |

---

## ✅ Available Datasets ({len(available)})

"""
    
    for code, config in sorted(available.items()):
        summary_md += f"- **{code}**: {config['route']}"
        if config.get('special_config'):
            summary_md += f" ⚠️ {config['special_config'].get('note', 'Special config needed')}"
        if config.get('has_nested_structure'):
            summary_md += f" 🔄 Nested structure"
        summary_md += "\n"
    
    if failed:
        summary_md += f"\n## ❌ Failed Datasets ({len(failed)})\n\n"
        for result in failed:
            summary_md += f"- **{result['code']}**: {result['status']}"
            if 'error' in result:
                summary_md += f" - {result['error'][:100]}"
            summary_md += "\n"
    
    summary_md += f"""
---

## 🎯 Key Findings

### Datasets with Special Requirements

"""
    
    special_count = sum(1 for d in available.values() if d.get('special_config'))
    if special_count > 0:
        summary_md += f"Found {special_count} datasets that require special handling:\n\n"
        for code, config in sorted(available.items()):
            if config.get('special_config'):
                summary_md += f"- **{code}**: {config['special_config'].get('note', 'See config')}\n"
    else:
        summary_md += "None found - all datasets support standard 7-day queries.\n"
    
    summary_md += f"""
### Datasets with Nested Structures

"""
    
    nested_count = sum(1 for d in available.values() if d.get('has_nested_structure'))
    if nested_count > 0:
        summary_md += f"Found {nested_count} datasets with nested JSON (need flattening for BigQuery):\n\n"
        for code, config in sorted(available.items()):
            if config.get('has_nested_structure'):
                summary_md += f"- **{code}**\n"
    else:
        summary_md += "None found - all datasets have flat structures.\n"
    
    summary_md += """
---

## 📋 Usage

```bash
# Use the generated manifest with download scripts
python download_last_7_days.py --manifest insights_manifest_dynamic.json

# Or download all 2025 data
python download_all_2025_data.py --manifest insights_manifest_dynamic.json
```

## 🔄 Re-running Discovery

To update the dataset list (e.g., when Elexon adds new datasets):

```bash
python discover_all_datasets_dynamic.py
```

No need to manually update code - it queries the API automatically!
"""
    
    summary_file = f"DISCOVERY_RESULTS_{timestamp}.md"
    with open(summary_file, "w") as f:
        f.write(summary_md)
    
    print(f"💾 Saved summary: {summary_file}")


def main():
    print("=" * 80)
    print("🚀 DYNAMIC Dataset Discovery")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Method: Query metadata endpoint (no hardcoded lists)")
    print("=" * 80)
    print()
    
    # Run discovery
    available, failed = discover_all_datasets_dynamic()
    
    # Print summary
    print()
    print("=" * 80)
    print("📊 DISCOVERY COMPLETE")
    print("=" * 80)
    print(f"✅ Available datasets: {len(available)}")
    print(f"❌ Failed datasets: {len(failed)}")
    print(f"📈 Success rate: {len(available)/(len(available)+len(failed))*100:.1f}%")
    print("=" * 80)
    
    # Save results
    save_results(available, failed)
    
    print()
    print("🎉 Done! Use the generated manifest with your download scripts:")
    print("   python download_last_7_days.py --manifest insights_manifest_dynamic.json")
    print()


if __name__ == "__main__":
    main()
