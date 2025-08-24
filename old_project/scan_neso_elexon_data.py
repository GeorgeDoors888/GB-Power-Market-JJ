#!/usr/bin/env python3
"""
Comprehensive Google Cloud Scanner for NESO and Elexon Data

This script scans Google Cloud resources to identify NESO and Elexon data across:
- Google Cloud Storage buckets
- BigQuery datasets and tables
- Any other relevant resources

Usage:
    python scan_neso_elexon_data.py

Requirements:
    - Google Cloud credentials configured (via GOOGLE_APPLICATION_CREDENTIALS or gcloud auth)
    - Appropriate permissions to list resources in the project
"""

import os
import sys
import json
import time
import datetime
import argparse
from typing import Dict, List, Any, Set, Tuple

try:
    from google.cloud import storage, bigquery
    from google.cloud.exceptions import NotFound, Forbidden
    from google.api_core.exceptions import PermissionDenied
except ImportError:
    print("Error: Required Google Cloud libraries not found.")
    print("Please install them using: pip install google-cloud-storage google-cloud-bigquery")
    sys.exit(1)

# Keywords to search for in resource names, labels, and metadata
NESO_KEYWORDS = [
    "neso", "national_eso", "national-eso", "nationaleso", 
    "eso_data", "eso-data", "esodata"
]

ELEXON_KEYWORDS = [
    "elexon", "bmrs", "balancing_mechanism", "balancing-mechanism",
    "bid_offer", "bid-offer", "system_warning", "system-warning"
]

def get_current_time() -> str:
    """Return current timestamp string for logging."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def contains_keywords(text: str, keywords: List[str]) -> bool:
    """Check if any keyword is present in the text (case-insensitive)."""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)

def scan_gcs_buckets(project_id: str) -> List[Dict[str, Any]]:
    """Scan GCS buckets for NESO and Elexon data."""
    print(f"[{get_current_time()}] Scanning GCS buckets in project {project_id}...")
    
    neso_elexon_resources = []
    storage_client = storage.Client(project=project_id)
    
    try:
        buckets = list(storage_client.list_buckets())
        print(f"Found {len(buckets)} buckets to scan.")
        
        for bucket in buckets:
            bucket_name = bucket.name
            print(f"  Scanning bucket: {bucket_name}")
            
            # Check if bucket name contains keywords
            bucket_matches_neso = contains_keywords(bucket_name, NESO_KEYWORDS)
            bucket_matches_elexon = contains_keywords(bucket_name, ELEXON_KEYWORDS)
            
            if bucket_matches_neso or bucket_matches_elexon:
                # Sample files to understand content
                sample_blobs = list(bucket.list_blobs(max_results=10))
                sample_files = [blob.name for blob in sample_blobs]
                
                neso_elexon_resources.append({
                    "resource_type": "gcs_bucket",
                    "name": bucket_name,
                    "full_path": f"gs://{bucket_name}/",
                    "contains_neso_data": bucket_matches_neso,
                    "contains_elexon_data": bucket_matches_elexon,
                    "sample_files": sample_files,
                    "creation_time": bucket._properties.get("timeCreated"),
                    "labels": bucket.labels
                })
                continue
            
            # If bucket name doesn't match, scan a sample of files
            try:
                blobs = list(bucket.list_blobs(max_results=100))
                has_neso_files = False
                has_elexon_files = False
                matching_files = []
                
                for blob in blobs:
                    blob_name = blob.name
                    
                    if contains_keywords(blob_name, NESO_KEYWORDS):
                        has_neso_files = True
                        matching_files.append(blob_name)
                    elif contains_keywords(blob_name, ELEXON_KEYWORDS):
                        has_elexon_files = True
                        matching_files.append(blob_name)
                
                if has_neso_files or has_elexon_files:
                    neso_elexon_resources.append({
                        "resource_type": "gcs_bucket",
                        "name": bucket_name,
                        "full_path": f"gs://{bucket_name}/",
                        "contains_neso_data": has_neso_files,
                        "contains_elexon_data": has_elexon_files,
                        "matching_files": matching_files[:10],  # First 10 matching files
                        "total_matching_files_found": len(matching_files),
                        "creation_time": bucket._properties.get("timeCreated"),
                        "labels": bucket.labels
                    })
            except (Forbidden, PermissionDenied) as e:
                print(f"    Warning: Permission denied for bucket {bucket_name}: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Error scanning GCS buckets: {str(e)}")
    
    return neso_elexon_resources

def scan_bigquery_datasets(project_id: str) -> List[Dict[str, Any]]:
    """Scan BigQuery datasets and tables for NESO and Elexon data."""
    print(f"[{get_current_time()}] Scanning BigQuery datasets in project {project_id}...")
    
    neso_elexon_resources = []
    bq_client = bigquery.Client(project=project_id)
    
    try:
        datasets = list(bq_client.list_datasets())
        print(f"Found {len(datasets)} datasets to scan.")
        
        for dataset_ref in datasets:
            dataset_id = dataset_ref.dataset_id
            print(f"  Scanning dataset: {dataset_id}")
            
            # Check if dataset name contains keywords
            dataset_matches_neso = contains_keywords(dataset_id, NESO_KEYWORDS)
            dataset_matches_elexon = contains_keywords(dataset_id, ELEXON_KEYWORDS)
            
            matching_tables = []
            has_neso_tables = False
            has_elexon_tables = False
            
            # Scan tables in the dataset
            try:
                tables = list(bq_client.list_tables(dataset_ref))
                
                for table_ref in tables:
                    table_id = table_ref.table_id
                    
                    table_matches_neso = contains_keywords(table_id, NESO_KEYWORDS)
                    table_matches_elexon = contains_keywords(table_id, ELEXON_KEYWORDS)
                    
                    if table_matches_neso or table_matches_elexon:
                        has_neso_tables = has_neso_tables or table_matches_neso
                        has_elexon_tables = has_elexon_tables or table_matches_elexon
                        
                        # Get some basic info about the table
                        try:
                            table = bq_client.get_table(table_ref)
                            row_count = table.num_rows
                            
                            # Check schema for indicators in column names
                            schema_contains_neso = any(contains_keywords(field.name, NESO_KEYWORDS) for field in table.schema)
                            schema_contains_elexon = any(contains_keywords(field.name, ELEXON_KEYWORDS) for field in table.schema)
                            
                            # Sample data - careful with large tables, just check schema and stats
                            matching_tables.append({
                                "table_id": table_id,
                                "full_path": f"{project_id}.{dataset_id}.{table_id}",
                                "contains_neso_data": table_matches_neso or schema_contains_neso,
                                "contains_elexon_data": table_matches_elexon or schema_contains_elexon,
                                "row_count": row_count,
                                "size_bytes": table.num_bytes,
                                "creation_time": table.created.isoformat() if table.created else None,
                                "last_modified": table.modified.isoformat() if table.modified else None
                            })
                        except Exception as e:
                            print(f"    Warning: Could not get details for table {table_id}: {str(e)}")
                            matching_tables.append({
                                "table_id": table_id,
                                "full_path": f"{project_id}.{dataset_id}.{table_id}",
                                "contains_neso_data": table_matches_neso,
                                "contains_elexon_data": table_matches_elexon,
                                "error": str(e)
                            })
            
            except (Forbidden, PermissionDenied) as e:
                print(f"    Warning: Permission denied for dataset {dataset_id}: {str(e)}")
                continue
            
            # Add dataset information if it contains NESO/Elexon data or has matching tables
            if dataset_matches_neso or dataset_matches_elexon or has_neso_tables or has_elexon_tables:
                neso_elexon_resources.append({
                    "resource_type": "bigquery_dataset",
                    "name": dataset_id,
                    "full_path": f"{project_id}.{dataset_id}",
                    "contains_neso_data": dataset_matches_neso or has_neso_tables,
                    "contains_elexon_data": dataset_matches_elexon or has_elexon_tables,
                    "tables": matching_tables,
                    "total_tables": len(tables),
                    "matching_tables": len(matching_tables)
                })
    
    except Exception as e:
        print(f"Error scanning BigQuery datasets: {str(e)}")
    
    return neso_elexon_resources

def get_all_gcp_projects() -> List[str]:
    """Attempt to get all accessible GCP projects."""
    try:
        # This uses the gcloud command-line tool since there's no direct SDK for listing all projects
        import subprocess
        result = subprocess.run(
            ["gcloud", "projects", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        projects = json.loads(result.stdout)
        return [p.get("projectId") for p in projects]
    except Exception as e:
        print(f"Warning: Could not list all projects: {str(e)}")
        print("You'll need to specify a project ID.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Scan Google Cloud for NESO and Elexon data")
    parser.add_argument("--project-id", help="Google Cloud project ID to scan")
    parser.add_argument("--output", default="neso_elexon_scan_results.json", help="Output file path")
    parser.add_argument("--scan-all-projects", action="store_true", help="Attempt to scan all accessible projects")
    args = parser.parse_args()
    
    project_ids = []
    
    if args.scan_all_projects:
        print("Attempting to scan all accessible projects...")
        project_ids = get_all_gcp_projects()
        if not project_ids:
            print("Error: Could not retrieve project list and no specific project provided.")
            sys.exit(1)
    elif args.project_id:
        project_ids = [args.project_id]
    else:
        # Try to get default project from environment
        default_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if default_project:
            project_ids = [default_project]
        else:
            print("Error: No project specified. Use --project-id or --scan-all-projects.")
            sys.exit(1)
    
    print(f"[{get_current_time()}] Starting NESO and Elexon data scan for {len(project_ids)} project(s)...")
    
    all_results = {}
    
    for project_id in project_ids:
        print(f"\n[{get_current_time()}] Scanning project: {project_id}")
        project_results = {
            "project_id": project_id,
            "scan_time": datetime.datetime.now().isoformat(),
            "resources": []
        }
        
        # Scan GCS buckets
        gcs_resources = scan_gcs_buckets(project_id)
        project_results["resources"].extend(gcs_resources)
        
        # Scan BigQuery datasets
        bq_resources = scan_bigquery_datasets(project_id)
        project_results["resources"].extend(bq_resources)
        
        # Add summary statistics
        project_results["summary"] = {
            "total_resources_found": len(project_results["resources"]),
            "resources_with_neso_data": sum(1 for r in project_results["resources"] if r.get("contains_neso_data", False)),
            "resources_with_elexon_data": sum(1 for r in project_results["resources"] if r.get("contains_elexon_data", False))
        }
        
        all_results[project_id] = project_results
    
    # Write results to file
    with open(args.output, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n[{get_current_time()}] Scan complete! Results saved to {args.output}")
    
    # Print summary to console
    print("\nSummary of findings:")
    for project_id, results in all_results.items():
        summary = results["summary"]
        print(f"Project {project_id}:")
        print(f"  Total resources with NESO/Elexon data: {summary['total_resources_found']}")
        print(f"  Resources with NESO data: {summary['resources_with_neso_data']}")
        print(f"  Resources with Elexon data: {summary['resources_with_elexon_data']}")
    
    # Generate HTML report for easier viewing
    html_output = args.output.replace('.json', '.html')
    with open(html_output, 'w') as f:
        f.write(generate_html_report(all_results))
    
    print(f"\nHTML report generated: {html_output}")

def generate_html_report(results: Dict[str, Any]) -> str:
    """Generate an HTML report from the scan results."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NESO and Elexon Data Scan Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333; }
            .project { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
            .summary { background-color: #f5f5f5; padding: 10px; margin-bottom: 15px; border-radius: 5px; }
            .resource { margin-bottom: 15px; border-left: 4px solid #2196F3; padding-left: 10px; }
            .neso { color: #4CAF50; font-weight: bold; }
            .elexon { color: #FF9800; font-weight: bold; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .tables-container { max-height: 300px; overflow-y: auto; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>NESO and Elexon Data Scan Results</h1>
        <p>Scan performed: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    """
    
    for project_id, project_data in results.items():
        summary = project_data["summary"]
        resources = project_data["resources"]
        
        html += f"""
        <div class="project">
            <h2>Project: {project_id}</h2>
            <div class="summary">
                <h3>Summary</h3>
                <p>Total resources with NESO/Elexon data: {summary['total_resources_found']}</p>
                <p>Resources with NESO data: {summary['resources_with_neso_data']}</p>
                <p>Resources with Elexon data: {summary['resources_with_elexon_data']}</p>
            </div>
        """
        
        if not resources:
            html += "<p>No NESO or Elexon data found in this project.</p>"
        else:
            # Group resources by type
            gcs_resources = [r for r in resources if r["resource_type"] == "gcs_bucket"]
            bq_resources = [r for r in resources if r["resource_type"] == "bigquery_dataset"]
            
            # GCS buckets
            if gcs_resources:
                html += f"""
                <h3>Google Cloud Storage Buckets ({len(gcs_resources)})</h3>
                """
                
                for resource in gcs_resources:
                    neso_class = "neso" if resource.get("contains_neso_data") else ""
                    elexon_class = "elexon" if resource.get("contains_elexon_data") else ""
                    
                    html += f"""
                    <div class="resource">
                        <h4>Bucket: {resource['name']}</h4>
                        <p>Path: {resource['full_path']}</p>
                        <p>Contains NESO data: <span class="{neso_class}">{resource.get('contains_neso_data', False)}</span></p>
                        <p>Contains Elexon data: <span class="{elexon_class}">{resource.get('contains_elexon_data', False)}</span></p>
                    """
                    
                    if "sample_files" in resource and resource["sample_files"]:
                        html += f"""
                        <p>Sample files:</p>
                        <ul>
                        """
                        for file in resource["sample_files"]:
                            html += f"<li>{file}</li>"
                        html += "</ul>"
                    
                    if "matching_files" in resource and resource["matching_files"]:
                        html += f"""
                        <p>Matching files (showing {len(resource['matching_files'])} of {resource.get('total_matching_files_found', 'unknown')}):</p>
                        <ul>
                        """
                        for file in resource["matching_files"]:
                            html += f"<li>{file}</li>"
                        html += "</ul>"
                    
                    html += "</div>"
            
            # BigQuery datasets
            if bq_resources:
                html += f"""
                <h3>BigQuery Datasets ({len(bq_resources)})</h3>
                """
                
                for resource in bq_resources:
                    neso_class = "neso" if resource.get("contains_neso_data") else ""
                    elexon_class = "elexon" if resource.get("contains_elexon_data") else ""
                    
                    html += f"""
                    <div class="resource">
                        <h4>Dataset: {resource['name']}</h4>
                        <p>Path: {resource['full_path']}</p>
                        <p>Contains NESO data: <span class="{neso_class}">{resource.get('contains_neso_data', False)}</span></p>
                        <p>Contains Elexon data: <span class="{elexon_class}">{resource.get('contains_elexon_data', False)}</span></p>
                        <p>Total tables: {resource.get('total_tables', 'unknown')}, Matching tables: {resource.get('matching_tables', 0)}</p>
                    """
                    
                    if "tables" in resource and resource["tables"]:
                        html += f"""
                        <p>Tables with NESO/Elexon data:</p>
                        <div class="tables-container">
                            <table>
                                <tr>
                                    <th>Table</th>
                                    <th>NESO Data</th>
                                    <th>Elexon Data</th>
                                    <th>Row Count</th>
                                    <th>Size</th>
                                    <th>Created</th>
                                    <th>Modified</th>
                                </tr>
                        """
                        
                        for table in resource["tables"]:
                            html += f"""
                            <tr>
                                <td>{table['table_id']}</td>
                                <td class="{neso_class if table.get('contains_neso_data') else ''}">{table.get('contains_neso_data', False)}</td>
                                <td class="{elexon_class if table.get('contains_elexon_data') else ''}">{table.get('contains_elexon_data', False)}</td>
                                <td>{table.get('row_count', 'unknown')}</td>
                                <td>{table.get('size_bytes', 'unknown')} bytes</td>
                                <td>{table.get('creation_time', 'unknown')}</td>
                                <td>{table.get('last_modified', 'unknown')}</td>
                            </tr>
                            """
                        
                        html += """
                            </table>
                        </div>
                        """
                    
                    html += "</div>"
        
        html += "</div>"
    
    html += """
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    main()
