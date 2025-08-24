#!/usr/bin/env python3
"""
BigQuery Connection Diagnostic Script

This script performs a series of diagnostics to troubleshoot BigQuery connection issues:
1. Checks for environment variables and API keys
2. Validates project access
3. Tests dataset operations
4. Verifies table access

Usage:
    python bq_diagnostics.py
"""

import os
import sys
import json
import subprocess
from google.cloud import bigquery
from google.oauth2 import service_account
import google.auth
from google.auth.exceptions import DefaultCredentialsError
import google.api_core.exceptions

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def run_command(cmd):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

def check_environment():
    """Check environment variables related to GCP."""
    print_section("Environment Variables")
    
    # Check for GOOGLE_APPLICATION_CREDENTIALS
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_path:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS is set to: {creds_path}")
        if os.path.exists(creds_path):
            print(f"✅ Credentials file exists at: {creds_path}")
            try:
                with open(creds_path, 'r') as f:
                    creds_content = json.load(f)
                print(f"✅ Credentials file is valid JSON")
                print(f"   - project_id: {creds_content.get('project_id')}")
                print(f"   - client_email: {creds_content.get('client_email')}")
            except json.JSONDecodeError:
                print(f"❌ Credentials file is not valid JSON")
            except Exception as e:
                print(f"❌ Error reading credentials file: {str(e)}")
        else:
            print(f"❌ Credentials file does not exist at: {creds_path}")
    else:
        print("❓ GOOGLE_APPLICATION_CREDENTIALS is not set")
        print("   - Will try to use Application Default Credentials")
    
    # Check for PROJECT_ID
    project_id = os.environ.get('PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT')
    if project_id:
        print(f"✅ Project ID is set to: {project_id}")
    else:
        print("❓ PROJECT_ID or GOOGLE_CLOUD_PROJECT is not set")
        print("   - Will try to detect from credentials")
    
    # Check for other relevant env vars
    for var in ['GCLOUD_PROJECT', 'SOURCE_DATASET', 'DEST_DATASET', 'US_BUCKET', 'EU_BUCKET']:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var} is set to: {value}")
        else:
            print(f"❓ {var} is not set")

def check_gcloud_config():
    """Check gcloud configuration."""
    print_section("gcloud Configuration")
    
    # Check if gcloud is installed
    gcloud_version = run_command("gcloud --version | head -1")
    if "Error" in gcloud_version:
        print("❌ gcloud CLI is not installed or not in PATH")
        return
    
    print(f"✅ {gcloud_version}")
    
    # Check current project
    project = run_command("gcloud config get-value project")
    if project and "Error" not in project:
        print(f"✅ Current gcloud project: {project}")
    else:
        print(f"❌ Could not determine current gcloud project: {project}")
    
    # Check current account
    account = run_command("gcloud config get-value account")
    if account and "Error" not in account:
        print(f"✅ Current gcloud account: {account}")
    else:
        print(f"❌ Could not determine current gcloud account: {account}")
    
    # Check auth list
    auth_list = run_command("gcloud auth list --format='value(account)'")
    if auth_list and "Error" not in auth_list:
        accounts = auth_list.split('\n')
        print(f"✅ Authenticated accounts ({len(accounts)}):")
        for acc in accounts:
            print(f"   - {acc}")
    else:
        print(f"❌ Could not list authenticated accounts: {auth_list}")

def check_bigquery_auth():
    """Check BigQuery authentication."""
    print_section("BigQuery Authentication")
    
    # Try to authenticate with BigQuery
    try:
        # First try with explicit credentials if available
        creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and os.path.exists(creds_path):
            print(f"🔍 Attempting to authenticate with credentials file: {creds_path}")
            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            client = bigquery.Client(credentials=credentials)
            print(f"✅ Successfully authenticated with credentials file")
        else:
            # Fall back to application default credentials
            print("🔍 Attempting to authenticate with Application Default Credentials")
            credentials, project = google.auth.default()
            client = bigquery.Client(credentials=credentials, project=project)
            print(f"✅ Successfully authenticated with Application Default Credentials")
        
        print(f"✅ Using project: {client.project}")
        return client
    
    except DefaultCredentialsError as e:
        print(f"❌ Authentication failed: {str(e)}")
        print("   - You may need to run 'gcloud auth application-default login'")
        return None
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None

def check_bigquery_datasets(client):
    """Check BigQuery datasets."""
    print_section("BigQuery Datasets")
    
    if not client:
        print("❌ Skipping dataset checks because authentication failed")
        return
    
    try:
        print("🔍 Listing datasets in project")
        datasets = list(client.list_datasets())
        
        if datasets:
            print(f"✅ Found {len(datasets)} datasets:")
            for dataset in datasets:
                dataset_id = dataset.dataset_id
                try:
                    dataset_ref = client.get_dataset(dataset_id)
                    location = dataset_ref.location
                    print(f"   - {dataset_id} (location: {location})")
                except Exception as e:
                    print(f"   - {dataset_id} (❌ Error getting details: {str(e)})")
        else:
            print("❓ No datasets found in the project")
        
        # Try to get specific datasets
        for dataset_id in ['uk_energy', 'uk_energy_prod']:
            try:
                dataset_ref = client.get_dataset(dataset_id)
                print(f"✅ Successfully accessed dataset: {dataset_id}")
                print(f"   - Location: {dataset_ref.location}")
                print(f"   - Created: {dataset_ref.created.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   - Description: {dataset_ref.description}")
            except google.api_core.exceptions.NotFound:
                print(f"❓ Dataset {dataset_id} does not exist")
            except Exception as e:
                print(f"❌ Error accessing dataset {dataset_id}: {str(e)}")
        
        # Try to create a test dataset
        test_dataset_id = f"{client.project}.bq_test_dataset"
        try:
            print(f"🔍 Attempting to create test dataset: bq_test_dataset")
            dataset = bigquery.Dataset(test_dataset_id)
            dataset.location = "europe-west2"
            dataset = client.create_dataset(dataset, exists_ok=True)
            print(f"✅ Successfully created/accessed test dataset")
            
            # Cleanup
            client.delete_dataset(
                test_dataset_id, delete_contents=True, not_found_ok=True
            )
            print(f"✅ Successfully deleted test dataset")
        except Exception as e:
            print(f"❌ Error creating test dataset: {str(e)}")
            print("   - This may indicate permission issues")
    
    except Exception as e:
        print(f"❌ Error listing datasets: {str(e)}")

def check_bigquery_tables(client):
    """Check BigQuery tables in specific datasets."""
    print_section("BigQuery Tables")
    
    if not client:
        print("❌ Skipping table checks because authentication failed")
        return
    
    # Define datasets to check
    datasets_to_check = ['uk_energy']
    
    for dataset_id in datasets_to_check:
        try:
            print(f"🔍 Listing tables in dataset: {dataset_id}")
            tables = list(client.list_tables(dataset_id))
            
            if tables:
                print(f"✅ Found {len(tables)} tables in {dataset_id}:")
                for table in tables[:5]:  # Limit to first 5 to avoid too much output
                    table_id = table.table_id
                    try:
                        table_ref = client.get_table(f"{dataset_id}.{table_id}")
                        row_count = table_ref.num_rows
                        print(f"   - {table_id} (rows: {row_count})")
                    except Exception as e:
                        print(f"   - {table_id} (❌ Error getting details: {str(e)})")
                
                if len(tables) > 5:
                    print(f"   ... and {len(tables) - 5} more tables")
            else:
                print(f"❓ No tables found in dataset {dataset_id}")
        
        except google.api_core.exceptions.NotFound:
            print(f"❓ Dataset {dataset_id} does not exist")
        except Exception as e:
            print(f"❌ Error listing tables in {dataset_id}: {str(e)}")
    
    # Check specific tables
    specific_tables = [
        'uk_energy.neso_demand_forecasts',
        'uk_energy.neso_balancing_services',
        'uk_energy.neso_wind_forecasts'
    ]
    
    for table_path in specific_tables:
        try:
            print(f"🔍 Checking table: {table_path}")
            table = client.get_table(table_path)
            print(f"✅ Successfully accessed table: {table_path}")
            print(f"   - Rows: {table.num_rows}")
            print(f"   - Created: {table.created.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # If table has data, try to query it
            if table.num_rows > 0:
                query = f"SELECT COUNT(*) as count FROM `{table_path}`"
                query_job = client.query(query)
                results = query_job.result()
                for row in results:
                    print(f"   - Query count: {row.count}")
            else:
                print(f"   - Table is empty, skipping query test")
                
        except google.api_core.exceptions.NotFound:
            print(f"❓ Table {table_path} does not exist")
        except Exception as e:
            print(f"❌ Error accessing table {table_path}: {str(e)}")

def check_cloud_storage():
    """Check Cloud Storage buckets."""
    print_section("Cloud Storage")
    
    # List buckets
    buckets = run_command("gsutil ls")
    if "Error" not in buckets:
        bucket_list = buckets.split('\n')
        print(f"✅ Found {len(bucket_list)} buckets:")
        for bucket in bucket_list:
            if bucket:
                print(f"   - {bucket}")
    else:
        print(f"❌ Error listing buckets: {buckets}")
    
    # Check specific buckets from env vars
    us_bucket = os.environ.get('US_BUCKET')
    eu_bucket = os.environ.get('EU_BUCKET')
    
    for bucket_name, bucket_var in [('US bucket', us_bucket), ('EU bucket', eu_bucket)]:
        if bucket_var:
            bucket_uri = f"gs://{bucket_var}"
            if bucket_uri in buckets:
                print(f"✅ {bucket_name} exists: {bucket_uri}")
                
                # Try to write a test file
                test_file = f"{bucket_uri}/test_file.txt"
                write_result = run_command(f"echo 'test' | gsutil cp - {test_file}")
                if "Error" not in write_result:
                    print(f"✅ Successfully wrote test file to {bucket_name}")
                    
                    # Cleanup
                    delete_result = run_command(f"gsutil rm {test_file}")
                    if "Error" not in delete_result:
                        print(f"✅ Successfully deleted test file from {bucket_name}")
                    else:
                        print(f"❌ Error deleting test file from {bucket_name}: {delete_result}")
                else:
                    print(f"❌ Error writing to {bucket_name}: {write_result}")
            else:
                print(f"❓ {bucket_name} ({bucket_var}) not found in bucket list")
        else:
            print(f"❓ {bucket_name} environment variable not set")

def check_client_secret():
    """Check if client_secret.json file exists and is valid."""
    print_section("Client Secret")
    
    client_secret_path = "client_secret.json"
    if os.path.exists(client_secret_path):
        print(f"✅ client_secret.json file exists")
        try:
            with open(client_secret_path, 'r') as f:
                secret_content = json.load(f)
            print(f"✅ client_secret.json is valid JSON")
            
            # Check for required fields
            required_fields = ['installed', 'web']
            found_fields = [field for field in required_fields if field in secret_content]
            if found_fields:
                print(f"✅ client_secret.json contains required fields: {', '.join(found_fields)}")
                if 'installed' in secret_content:
                    client_id = secret_content['installed'].get('client_id')
                    if client_id:
                        print(f"✅ client_id: {client_id[:10]}...{client_id[-5:]}")
            else:
                print(f"❌ client_secret.json is missing required fields")
        except json.JSONDecodeError:
            print(f"❌ client_secret.json is not valid JSON")
        except Exception as e:
            print(f"❌ Error reading client_secret.json: {str(e)}")
    else:
        print(f"❓ client_secret.json file not found")

def main():
    """Run all diagnostic checks."""
    print_section("BigQuery Diagnostics")
    print(f"Running diagnostics at: {os.getcwd()}")
    
    # Run checks
    check_environment()
    check_gcloud_config()
    check_client_secret()
    client = check_bigquery_auth()
    check_bigquery_datasets(client)
    check_bigquery_tables(client)
    check_cloud_storage()
    
    print("\n" + "=" * 80)
    print(" DIAGNOSTIC SUMMARY ".center(80, "="))
    print("=" * 80)
    print("If you're seeing authentication errors, try these steps:")
    print("1. Run 'gcloud auth login' to authenticate with your Google account")
    print("2. Run 'gcloud auth application-default login' to set up application default credentials")
    print("3. Check if GOOGLE_APPLICATION_CREDENTIALS is set correctly")
    print("4. Verify that you have the necessary permissions in the GCP project")
    print("5. Check if there are any organization policies restricting your actions")
    print("=" * 80)

if __name__ == "__main__":
    main()
