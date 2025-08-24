#!/usr/bin/env python3
"""
Check GCS buckets for NESO and Elexon data files

This script focuses specifically on checking Google Cloud Storage buckets
for files related to NESO and Elexon data.
"""

import os
import sys
import json
import datetime
import argparse
from typing import Dict, List, Any, Set

try:
    from google.cloud import storage
    from google.cloud.exceptions import NotFound, Forbidden
    from google.api_core.exceptions import PermissionDenied
except ImportError:
    print("Error: Required Google Cloud libraries not found.")
    print("Please install them using: pip install google-cloud-storage")
    sys.exit(1)

# Keywords to search for in file names
NESO_KEYWORDS = [
    "neso", "national_eso", "national-eso", "nationaleso", 
    "eso_data", "eso-data", "esodata"
]

ELEXON_KEYWORDS = [
    "elexon", "bmrs", "balancing_mechanism", "balancing-mechanism",
    "bid_offer", "bid-offer", "system_warning", "system-warning"
]

# Patterns that might indicate year in filenames
YEAR_PATTERNS = [
    "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025",
    "16_", "17_", "18_", "19_", "20_", "21_", "22_", "23_", "24_", "25_"
]

def contains_keywords(text: str, keywords: List[str]) -> bool:
    """Check if any keyword is present in the text (case-insensitive)."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)

def extract_year_info(filename: str) -> List[str]:
    """Extract potential year information from filename."""
    years_found = []
    for pattern in YEAR_PATTERNS:
        if pattern in filename:
            years_found.append(pattern)
    return years_found

def scan_gcs_bucket(client: storage.Client, bucket_name: str) -> Dict[str, Any]:
    """Scan a single GCS bucket for NESO and Elexon data files."""
    print(f"Scanning bucket: {bucket_name}")
    
    result = {
        "bucket_name": bucket_name,
        "neso_files": [],
        "elexon_files": [],
        "sample_files": [],
        "years_mentioned": set(),
        "total_files": 0,
        "total_bytes": 0
    }
    
    try:
        bucket = client.get_bucket(bucket_name)
        
        # Get sample of files
        blobs = list(bucket.list_blobs(max_results=1000))
        result["total_files"] = len(blobs)
        
        if len(blobs) > 0:
            # Add up to 10 sample files
            result["sample_files"] = [blob.name for blob in blobs[:10]]
            
            # Calculate total size
            result["total_bytes"] = sum(blob.size for blob in blobs if blob.size)
            
            # Check for NESO and Elexon files
            for blob in blobs:
                filename = blob.name
                
                # Extract year information
                years = extract_year_info(filename)
                for year in years:
                    result["years_mentioned"].add(year)
                
                if contains_keywords(filename, NESO_KEYWORDS):
                    result["neso_files"].append({
                        "name": filename,
                        "size": blob.size,
                        "years": years
                    })
                
                if contains_keywords(filename, ELEXON_KEYWORDS):
                    result["elexon_files"].append({
                        "name": filename,
                        "size": blob.size,
                        "years": years
                    })
        
        # If we have more than 1000 files, try to count total number
        if len(blobs) == 1000:
            try:
                # This is an approximation
                result["total_files"] = sum(1 for _ in bucket.list_blobs())
            except Exception:
                result["total_files"] = "1000+ (exact count unknown)"
    
    except Exception as e:
        print(f"Error scanning bucket {bucket_name}: {str(e)}")
        result["error"] = str(e)
    
    # Convert set to list for JSON serialization
    result["years_mentioned"] = list(result["years_mentioned"])
    
    # Print summary
    neso_count = len(result["neso_files"])
    elexon_count = len(result["elexon_files"])
    print(f"  - Found {neso_count} NESO files and {elexon_count} Elexon files")
    if result["years_mentioned"]:
        print(f"  - Years mentioned: {', '.join(sorted(result['years_mentioned']))}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Check GCS buckets for NESO and Elexon data files")
    parser.add_argument("--project", default="jibber-jabber-knowledge", help="Google Cloud project ID")
    parser.add_argument("--buckets", nargs="+", help="Specific buckets to check (default: all in project)")
    parser.add_argument("--output", default="gcs_neso_elexon_report.json", help="Output file path")
    args = parser.parse_args()
    
    print(f"Checking GCS buckets in project {args.project} for NESO and Elexon data files...")
    
    client = storage.Client(project=args.project)
    results = {}
    
    # Get list of buckets
    if args.buckets:
        bucket_names = args.buckets
    else:
        try:
            buckets = list(client.list_buckets())
            bucket_names = [bucket.name for bucket in buckets]
        except Exception as e:
            print(f"Error listing buckets: {str(e)}")
            sys.exit(1)
    
    print(f"Found {len(bucket_names)} buckets to scan.")
    
    # Scan each bucket
    for bucket_name in bucket_names:
        results[bucket_name] = scan_gcs_bucket(client, bucket_name)
    
    # Add summary information
    summary = {
        "total_buckets": len(results),
        "buckets_with_neso_files": sum(1 for r in results.values() if r.get("neso_files")),
        "buckets_with_elexon_files": sum(1 for r in results.values() if r.get("elexon_files")),
        "total_neso_files": sum(len(r.get("neso_files", [])) for r in results.values()),
        "total_elexon_files": sum(len(r.get("elexon_files", [])) for r in results.values()),
        "years_found": sorted(set().union(*[set(r.get("years_mentioned", [])) for r in results.values()])),
        "scan_time": datetime.datetime.now().isoformat()
    }
    
    # Write results to file
    with open(args.output, 'w') as f:
        json.dump({"summary": summary, "buckets": results}, f, indent=2)
    
    print(f"\nScan complete! Results saved to {args.output}")
    
    # Print summary
    print("\nSummary:")
    print(f"  Total buckets scanned: {summary['total_buckets']}")
    print(f"  Buckets with NESO files: {summary['buckets_with_neso_files']}")
    print(f"  Buckets with Elexon files: {summary['buckets_with_elexon_files']}")
    print(f"  Total NESO files found: {summary['total_neso_files']}")
    print(f"  Total Elexon files found: {summary['total_elexon_files']}")
    if summary['years_found']:
        print(f"  Years found in filenames: {', '.join(summary['years_found'])}")

if __name__ == "__main__":
    main()
