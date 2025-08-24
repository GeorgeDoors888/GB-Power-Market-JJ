#!/usr/bin/env python3
"""
BigQuery Simple Authentication Helper
====================================

This is a simplified version of the authentication helper that doesn't rely on
other modules. It provides a clean standalone solution for BigQuery authentication.

Usage:
    python simple_bq_auth.py [--project PROJECT_ID] [--test]
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# Try importing BigQuery library
try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-cloud-bigquery"])
    
    # Now try importing again
    from google.cloud import bigquery
    from google.oauth2 import service_account
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError

# Constants
DEFAULT_PROJECT_ID = "jibber-jabber-knowledge"
CREDENTIALS_DIRS = [
    ".",  # Current directory
    os.path.expanduser("~"),  # Home directory
    os.path.expanduser("~/.config/gcloud"),  # GCloud config
    os.path.expanduser("~/.config/bod_analysis")  # Our app config
]
CREDENTIALS_FILES = [
    "client_secret.json",
    "service_account.json",
    "service-account.json",
    "key.json",
    "application_default_credentials.json"
]

def find_credentials_file():
    """Search for credentials file in common locations"""
    for directory in CREDENTIALS_DIRS:
        for filename in CREDENTIALS_FILES:
            path = os.path.join(directory, filename)
            if os.path.exists(path):
                print(f"Found credentials file: {path}")
                return path
    return None

def get_bigquery_client(project_id=DEFAULT_PROJECT_ID, credentials_file=None):
    """
    Get an authenticated BigQuery client using the best available method.
    
    Args:
        project_id (str): Google Cloud project ID
        credentials_file (str): Path to service account key file
        
    Returns:
        bigquery.Client: Authenticated BigQuery client
    """
    # Track authentication attempts
    auth_methods_tried = []
    
    # 1. Try using explicit credentials file if provided
    if credentials_file and os.path.exists(credentials_file):
        try:
            print(f"Trying authentication with provided credentials file: {credentials_file}")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file
            )
            auth_methods_tried.append(f"Explicit credentials file: {credentials_file}")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as e:
            print(f"Failed to authenticate with provided credentials file: {e}")
    
    # 2. Try using GOOGLE_APPLICATION_CREDENTIALS environment variable
    env_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_creds and os.path.exists(env_creds):
        try:
            print(f"Trying authentication with GOOGLE_APPLICATION_CREDENTIALS: {env_creds}")
            credentials = service_account.Credentials.from_service_account_file(
                env_creds
            )
            auth_methods_tried.append(f"GOOGLE_APPLICATION_CREDENTIALS: {env_creds}")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as e:
            print(f"Failed to authenticate with GOOGLE_APPLICATION_CREDENTIALS: {e}")
    
    # 3. Try to find credentials file in common locations
    auto_creds = find_credentials_file()
    if auto_creds:
        try:
            print(f"Trying authentication with discovered credentials file: {auto_creds}")
            credentials = service_account.Credentials.from_service_account_file(
                auto_creds
            )
            auth_methods_tried.append(f"Auto-discovered credentials file: {auto_creds}")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as e:
            print(f"Failed to authenticate with discovered credentials file: {e}")
    
    # 4. Try application default credentials
    try:
        print("Trying authentication with application default credentials")
        credentials, detected_project = default()
        used_project = project_id or detected_project
        auth_methods_tried.append("Application Default Credentials")
        return bigquery.Client(credentials=credentials, project=used_project)
    except Exception as e:
        print(f"Failed to authenticate with application default credentials: {e}")
    
    # 5. Try to create client directly (works if ADC is set up properly)
    try:
        print("Trying to create client directly (implicit credentials)")
        client = bigquery.Client(project=project_id)
        # Test with a minimal query
        client.query("SELECT 1").result()
        auth_methods_tried.append("Implicit credentials")
        return client
    except Exception as e:
        print(f"Failed to create client with implicit credentials: {e}")
    
    # If we get here, all authentication methods failed
    print("All authentication methods failed:")
    for i, method in enumerate(auth_methods_tried, 1):
        print(f"  {i}. {method}")
    
    print("\nPlease set up authentication using one of these methods:")
    print("1. Run 'gcloud auth application-default login'")
    print("2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    print("3. Place a service account key file in the current directory")
    
    return None

def list_datasets(client):
    """List all datasets in the project"""
    print("\nAvailable datasets:")
    print("------------------")
    try:
        datasets = list(client.list_datasets())
        if datasets:
            for dataset in datasets:
                print(f"- {dataset.dataset_id}")
        else:
            print("No datasets found in the project.")
    except Exception as e:
        print(f"Error listing datasets: {e}")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Simple BigQuery Authentication Helper")
    parser.add_argument("--project", type=str, default=DEFAULT_PROJECT_ID,
                        help=f"Google Cloud project ID (default: {DEFAULT_PROJECT_ID})")
    parser.add_argument("--credentials", type=str,
                        help="Path to service account credentials file")
    parser.add_argument("--test", action="store_true",
                        help="Test authentication and list available datasets")
    args = parser.parse_args()
    
    # Get authenticated client
    client = get_bigquery_client(project_id=args.project, credentials_file=args.credentials)
    
    if client:
        print("\n✅ Authentication successful!")
        
        # Print project info
        print(f"Project: {client.project}")
        
        # List datasets if requested
        if args.test:
            list_datasets(client)
        
        return 0
    else:
        print("\n❌ Authentication failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
