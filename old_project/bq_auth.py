#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BigQuery Authentication Helper
=============================

This module provides robust authentication for BigQuery with multiple fallback methods:
1. Service account key (explicit path)
2. Application Default Credentials
3. User account with OAuth flow
4. Interactive password input

Usage:
    python bq_auth.py [--project PROJECT_ID] [--test] [--reset]

Options:
    --project PROJECT_ID    Google Cloud project ID
    --test                  Test authentication and show available datasets
    --reset                 Force re-authentication even if cached credentials exist
"""

import os
import sys
import json
import getpass
import argparse
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Google Cloud imports
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Try to import OAuth dependencies (optional)
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False

# Constants
DEFAULT_PROJECT_ID = "jibber-jabber-knowledge"
BIGQUERY_SCOPES = ["https://www.googleapis.com/auth/bigquery"]
TOKEN_PATH = os.path.expanduser("~/.config/bod_analysis/token.json")
SERVICE_ACCOUNT_PATH = "service_account_key.json"
CLIENT_SECRET_PATH = "client_secret.json"
CREDENTIALS_CACHE_PATH = os.path.expanduser("~/.config/bod_analysis/credentials_cache.json")
APPLICATION_DEFAULT_CREDENTIALS_PATH = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")

# Credentials cache (in-memory)
CREDENTIALS_CACHE = {}

def get_auth_client(project_id: str = DEFAULT_PROJECT_ID, 
                   service_account_path: str = None,
                   force_reset: bool = False) -> Tuple[bigquery.Client, str]:
    """
    Get an authenticated BigQuery client using the best available method.
    
    Args:
        project_id: Google Cloud project ID
        service_account_path: Path to service account key file
        force_reset: Force re-authentication even if cached credentials exist
        
    Returns:
        Tuple of (BigQuery client, auth method description)
    """
    # Track authentication attempts
    auth_attempts = []
    auth_method = "unknown"
    
    # Check for cached credentials
    if not force_reset and os.path.exists(CREDENTIALS_CACHE_PATH):
        try:
            with open(CREDENTIALS_CACHE_PATH, 'r') as f:
                cache = json.load(f)
                
            if 'service_account_path' in cache and os.path.exists(cache['service_account_path']):
                print(f"Using cached credentials from {cache['service_account_path']}")
                service_account_path = cache['service_account_path']
        except Exception as e:
            print(f"Error reading credentials cache: {e}")
    
    # 1. Try explicit service account path if provided
    if service_account_path and os.path.exists(service_account_path):
        try:
            print(f"Attempting authentication with service account: {service_account_path}")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=BIGQUERY_SCOPES
            )
            auth_attempts.append(f"Service account file: {service_account_path}")
            auth_method = "service_account"
            
            # Cache successful credentials
            os.makedirs(os.path.dirname(CREDENTIALS_CACHE_PATH), exist_ok=True)
            with open(CREDENTIALS_CACHE_PATH, 'w') as f:
                json.dump({'service_account_path': service_account_path}, f)
                
            return bigquery.Client(credentials=credentials, project=project_id), auth_method
        except Exception as e:
            print(f"Failed to authenticate with service account: {e}")
    
    # 2. Try environment variable GOOGLE_APPLICATION_CREDENTIALS
    env_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_creds_path and os.path.exists(env_creds_path):
        try:
            print(f"Attempting authentication with GOOGLE_APPLICATION_CREDENTIALS: {env_creds_path}")
            credentials = service_account.Credentials.from_service_account_file(
                env_creds_path, scopes=BIGQUERY_SCOPES
            )
            auth_attempts.append(f"GOOGLE_APPLICATION_CREDENTIALS: {env_creds_path}")
            auth_method = "service_account_env"
            
            # Cache successful credentials
            os.makedirs(os.path.dirname(CREDENTIALS_CACHE_PATH), exist_ok=True)
            with open(CREDENTIALS_CACHE_PATH, 'w') as f:
                json.dump({'service_account_path': env_creds_path}, f)
                
            return bigquery.Client(credentials=credentials, project=project_id), auth_method
        except Exception as e:
            print(f"Failed to authenticate with GOOGLE_APPLICATION_CREDENTIALS: {e}")
    
    # 3. Try common credential file locations
    common_paths = [
        SERVICE_ACCOUNT_PATH,
        "key.json",
        "credentials.json",
        os.path.expanduser("~/.config/gcloud/service-account.json")
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            try:
                print(f"Attempting authentication with file: {path}")
                credentials = service_account.Credentials.from_service_account_file(
                    path, scopes=BIGQUERY_SCOPES
                )
                auth_attempts.append(f"Found credentials file: {path}")
                auth_method = "service_account_auto"
                
                # Cache successful credentials
                os.makedirs(os.path.dirname(CREDENTIALS_CACHE_PATH), exist_ok=True)
                with open(CREDENTIALS_CACHE_PATH, 'w') as f:
                    json.dump({'service_account_path': path}, f)
                    
                return bigquery.Client(credentials=credentials, project=project_id), auth_method
            except Exception as e:
                print(f"Failed to authenticate with {path}: {e}")
    
    # 4. Try application default credentials
    try:
        print("Attempting authentication with application default credentials")
        credentials, project = default(scopes=BIGQUERY_SCOPES)
        auth_attempts.append("Application Default Credentials")
        auth_method = "application_default"
        return bigquery.Client(credentials=credentials, project=project_id), auth_method
    except Exception as e:
        print(f"Failed to authenticate with application default credentials: {e}")
    
    # 5. Try OAuth flow if available
    if HAS_OAUTH:
        try:
            print("Attempting OAuth authentication flow")
            
            # Find client secret file
            client_secret_file = None
            if os.path.exists(CLIENT_SECRET_PATH):
                client_secret_file = CLIENT_SECRET_PATH
                
            if client_secret_file:
                # Check for existing token
                token_dir = os.path.dirname(TOKEN_PATH)
                os.makedirs(token_dir, exist_ok=True)
                
                creds = None
                if os.path.exists(TOKEN_PATH) and not force_reset:
                    with open(TOKEN_PATH, "r") as token:
                        try:
                            creds = Credentials.from_authorized_user_info(
                                json.load(token), BIGQUERY_SCOPES
                            )
                        except Exception:
                            creds = None
                
                # Refresh token or run flow
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif not creds:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secret_file, BIGQUERY_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(TOKEN_PATH, "w") as token:
                    token.write(creds.to_json())
                
                auth_attempts.append(f"OAuth flow using {client_secret_file}")
                auth_method = "oauth"
                return bigquery.Client(credentials=creds, project=project_id), auth_method
            else:
                print("No client_secret.json found for OAuth flow")
        except Exception as e:
            print(f"Failed to authenticate with OAuth: {e}")
    
    # 6. Final attempt with no credentials (works on GCP or if user already set up ADC)
    try:
        print("Attempting to create client with no explicit credentials")
        client = bigquery.Client(project=project_id)
        
        # Test with a minimal query
        client.query("SELECT 1").result()
        
        auth_attempts.append("Default authentication (implicit)")
        auth_method = "implicit"
        return client, auth_method
    except Exception as e:
        print(f"Failed to create client with default authentication: {e}")
    
    # 7. Ask user for new service account key location
    print("\nAll automatic authentication methods failed. Let's try manual entry.")
    print("Options:")
    print("  1. Enter path to a service account key file")
    print("  2. Help me create application default credentials")
    print("  3. Generate a new service account key file")
    print("  4. Cancel and exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        path = input("Enter the full path to your service account key file: ").strip()
        if os.path.exists(path):
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    path, scopes=BIGQUERY_SCOPES
                )
                
                # Cache successful credentials
                os.makedirs(os.path.dirname(CREDENTIALS_CACHE_PATH), exist_ok=True)
                with open(CREDENTIALS_CACHE_PATH, 'w') as f:
                    json.dump({'service_account_path': path}, f)
                
                auth_method = "service_account_manual"
                return bigquery.Client(credentials=credentials, project=project_id), auth_method
            except Exception as e:
                print(f"Failed to authenticate with provided key file: {e}")
        else:
            print(f"File not found: {path}")
    
    elif choice == '2':
        print("\nTo create application default credentials:")
        print("1. Install Google Cloud SDK if not already installed")
        print("2. Run this command in your terminal:")
        print("   gcloud auth application-default login")
        print("3. Follow the browser authentication flow")
        print("4. Run this script again after completing these steps")
        
        open_browser = input("Would you like to open the gcloud download page? (y/n): ")
        if open_browser.lower() == 'y':
            webbrowser.open("https://cloud.google.com/sdk/docs/install")
    
    elif choice == '3':
        print("\nTo create a new service account key:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Navigate to IAM & Admin > Service Accounts")
        print("3. Create or select a service account")
        print("4. Create a new key (JSON type)")
        print("5. Download the key file")
        print("6. Save it to a secure location and note the path")
        
        open_browser = input("Would you like to open the Google Cloud Console? (y/n): ")
        if open_browser.lower() == 'y':
            webbrowser.open("https://console.cloud.google.com/iam-admin/serviceaccounts")
    
    # All authentication methods failed
    print("\nAuthentication failed. Authentication attempts:")
    for i, attempt in enumerate(auth_attempts, 1):
        print(f"  {i}. {attempt}")
    
    raise Exception("Could not authenticate with BigQuery using any available method")

def clear_cached_credentials():
    """Clear any cached credentials"""
    if os.path.exists(TOKEN_PATH):
        try:
            os.remove(TOKEN_PATH)
            print(f"Removed OAuth token: {TOKEN_PATH}")
        except Exception as e:
            print(f"Failed to remove OAuth token: {e}")
    
    if os.path.exists(CREDENTIALS_CACHE_PATH):
        try:
            os.remove(CREDENTIALS_CACHE_PATH)
            print(f"Removed credentials cache: {CREDENTIALS_CACHE_PATH}")
        except Exception as e:
            print(f"Failed to remove credentials cache: {e}")

def test_authentication(project_id: str, service_account_path: str = None, force_reset: bool = False):
    """Test authentication and list available datasets"""
    try:
        client, auth_method = get_auth_client(project_id, service_account_path, force_reset)
        print(f"\n✅ Authentication successful using method: {auth_method}")
        
        # List datasets
        print(f"\nAvailable datasets in project {project_id}:")
        datasets = list(client.list_datasets())
        if datasets:
            for dataset in datasets:
                print(f"- {dataset.dataset_id}")
        else:
            print("No datasets found in this project.")
        
        # Show some account info if available
        try:
            query_job = client.query("SELECT current_user() as user, current_date() as date")
            for row in query_job:
                print(f"\nCurrently authenticated as: {row.user}")
                print(f"Current date in BigQuery: {row.date}")
        except Exception as e:
            print(f"Could not retrieve user information: {e}")
            
        return True
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="BigQuery Authentication Helper")
    parser.add_argument("--project", type=str, default=DEFAULT_PROJECT_ID, 
                        help=f"Google Cloud project ID (default: {DEFAULT_PROJECT_ID})")
    parser.add_argument("--key-file", type=str, help="Path to service account key file")
    parser.add_argument("--test", action="store_true", help="Test authentication and show available datasets")
    parser.add_argument("--reset", action="store_true", help="Force re-authentication")
    
    args = parser.parse_args()
    
    if args.reset:
        clear_cached_credentials()
    
    if args.test or args.reset:
        success = test_authentication(args.project, args.key_file, args.reset)
        sys.exit(0 if success else 1)
    else:
        try:
            # Just get a client to verify authentication works
            client, auth_method = get_auth_client(args.project, args.key_file, args.reset)
            print(f"\n✅ Authentication successful using method: {auth_method}")
            
            # Show some account info
            query_job = client.query("SELECT current_user() as user")
            for row in query_job:
                print(f"Currently authenticated as: {row.user}")
                
            print("\nTo test authentication and view available datasets, run:")
            print(f"python {sys.argv[0]} --test")
            print("\nTo re-authenticate and clear cached credentials, run:")
            print(f"python {sys.argv[0]} --reset")
            
            return 0
        except Exception as e:
            print(f"\n❌ Authentication failed: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
