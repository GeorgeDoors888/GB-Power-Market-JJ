#!/usr/bin/env python3
"""
Scan Google Cloud Storage for NESO and Elexon data files from 2016-2022.
This script looks for files in GCS buckets that might contain the missing historical data.
"""

import os
import sys
import json
import re
from datetime import datetime
from google.cloud import storage

# Initialize the GCS client
client = storage.Client()

def print_with_timestamp(message):
    """Print message with timestamp."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] {message}")
    sys.stdout.flush()  # Ensure output is displayed immediately

def scan_buckets_for_data(project_id='jibber-jabber-knowledge'):
    """Scan GCS buckets for NESO and Elexon data files from 2016-2022."""
    print_with_timestamp(f"Starting scan for NESO and Elexon data in GCS buckets (2016-2022)")
    
    results = {
        "buckets_with_neso_data": [],
        "buckets_with_elexon_data": [],
        "files_by_year": {str(year): [] for year in range(2016, 2023)},
        "summary": {}
    }
    
    # Regular expressions to match filenames containing years 2016-2022
    year_patterns = {
        str(year): re.compile(f'.*({year}|{str(year)[-2:]})[-_.]') for year in range(2016, 2023)
    }
    
    try:
        # Get all buckets in the project
        buckets = list(client.list_buckets())
        print_with_timestamp(f"Found {len(buckets)} buckets to scan")
        
        for bucket in buckets:
            bucket_name = bucket.name
            print_with_timestamp(f"Scanning bucket: {bucket_name}")
            
            # Check if bucket name suggests energy data
            is_energy_bucket = any(x in bucket_name.lower() for x in ['energy', 'elexon', 'neso', 'uk'])
            
            if not is_energy_bucket:
                print_with_timestamp(f"  Skipping non-energy bucket")
                continue
            
            # Initialize counters for this bucket
            bucket_stats = {
                "elexon_files": 0,
                "neso_files": 0,
                "total_files": 0,
                "files_by_year": {str(year): 0 for year in range(2016, 2023)}
            }
            
            # List the first 1000 files in the bucket (to avoid timeout on large buckets)
            blobs = list(client.list_blobs(bucket_name, max_results=1000))
            
            # Get date modified and name for each blob
            for blob in blobs:
                bucket_stats["total_files"] += 1
                file_name = blob.name.lower()
                
                # Check if file is NESO or Elexon related
                is_neso = 'neso' in file_name
                is_elexon = 'elexon' in file_name
                
                if is_neso:
                    bucket_stats["neso_files"] += 1
                if is_elexon:
                    bucket_stats["elexon_files"] += 1
                
                # Check if file contains a year in the filename
                for year, pattern in year_patterns.items():
                    if pattern.search(file_name):
                        bucket_stats["files_by_year"][year] += 1
                        
                        # Add first 100 files to detailed results to avoid excessive output
                        if len(results["files_by_year"][year]) < 100:
                            results["files_by_year"][year].append({
                                "bucket": bucket_name,
                                "file": blob.name,
                                "size": blob.size,
                                "updated": blob.updated.isoformat() if blob.updated else None
                            })
            
            # Add bucket to appropriate lists if it contains relevant files
            if bucket_stats["neso_files"] > 0:
                results["buckets_with_neso_data"].append({
                    "bucket": bucket_name,
                    "neso_files": bucket_stats["neso_files"]
                })
            
            if bucket_stats["elexon_files"] > 0:
                results["buckets_with_elexon_data"].append({
                    "bucket": bucket_name,
                    "elexon_files": bucket_stats["elexon_files"]
                })
            
            # Print summary for this bucket
            if bucket_stats["neso_files"] > 0 or bucket_stats["elexon_files"] > 0:
                print_with_timestamp(f"  Found {bucket_stats['neso_files']} NESO files, {bucket_stats['elexon_files']} Elexon files")
                for year in range(2016, 2023):
                    year_str = str(year)
                    if bucket_stats["files_by_year"][year_str] > 0:
                        print_with_timestamp(f"    Year {year}: {bucket_stats['files_by_year'][year_str]} files")
        
        # Generate summary
        total_neso_buckets = len(results["buckets_with_neso_data"])
        total_elexon_buckets = len(results["buckets_with_elexon_data"])
        files_by_year_count = {year: len(files) for year, files in results["files_by_year"].items()}
        
        results["summary"] = {
            "total_neso_buckets": total_neso_buckets,
            "total_elexon_buckets": total_elexon_buckets,
            "files_by_year_count": files_by_year_count,
            "scan_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gcs_historical_data_scan_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print_with_timestamp(f"Results saved to {filename}")
        
        # Print summary
        print_with_timestamp("\nSUMMARY:")
        print(f"NESO data buckets: {total_neso_buckets}")
        print(f"Elexon data buckets: {total_elexon_buckets}")
        print("Files by year:")
        for year in range(2016, 2023):
            year_str = str(year)
            print(f"  {year}: {files_by_year_count[year_str]} files")
        
        # Generate a simple markdown report
        md_report = f"""# GCS Historical Data Scan Report (2016-2022)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **NESO data buckets:** {total_neso_buckets}
- **Elexon data buckets:** {total_elexon_buckets}
- **Files by year:**
  - 2016: {files_by_year_count['2016']} files
  - 2017: {files_by_year_count['2017']} files
  - 2018: {files_by_year_count['2018']} files
  - 2019: {files_by_year_count['2019']} files
  - 2020: {files_by_year_count['2020']} files
  - 2021: {files_by_year_count['2021']} files
  - 2022: {files_by_year_count['2022']} files

## Buckets with NESO Data
"""
        for bucket in results["buckets_with_neso_data"]:
            md_report += f"- **{bucket['bucket']}**: {bucket['neso_files']} files\n"
        
        md_report += "\n## Buckets with Elexon Data\n"
        for bucket in results["buckets_with_elexon_data"]:
            md_report += f"- **{bucket['bucket']}**: {bucket['elexon_files']} files\n"
        
        # Add sample files for each year if available
        for year in range(2016, 2023):
            year_str = str(year)
            if files_by_year_count[year_str] > 0:
                md_report += f"\n## Sample Files from {year}\n"
                # Show up to 10 sample files
                for i, file in enumerate(results["files_by_year"][year_str][:10]):
                    md_report += f"{i+1}. `{file['file']}` ({file['size']} bytes) - Last updated: {file['updated']}\n"
        
        md_filename = f"gcs_historical_data_scan_{timestamp}.md"
        with open(md_filename, 'w') as f:
            f.write(md_report)
        
        print_with_timestamp(f"Markdown report saved to {md_filename}")
        
    except Exception as e:
        print_with_timestamp(f"Error: {str(e)}")

if __name__ == "__main__":
    scan_buckets_for_data()
