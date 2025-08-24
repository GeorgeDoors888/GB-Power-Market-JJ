#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BigQuery Authentication Diagnostic Tool

This script tests authentication with BigQuery using different methods and
provides detailed diagnostics about the authentication issues.
"""

import os
import sys
import json
import logging
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

def check_environment_variables():
    """Check if required environment variables are set"""
    creds_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    log.info(f"GOOGLE_APPLICATION_CREDENTIALS: {creds_path or 'Not set'}")
    return creds_path

def validate_service_account_file(file_path):
    """Validate the service account file format"""
    if not os.path.exists(file_path):
        log.error(f"Service account file not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            creds_json = json.load(f)
        
        # Check for required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                          'client_email', 'client_id', 'auth_uri', 'token_uri']
        
        missing_fields = [field for field in required_fields if field not in creds_json]
        if missing_fields:
            log.error(f"Service account file missing required fields: {', '.join(missing_fields)}")
            return False
        
        # Check type
        if creds_json.get('type') != 'service_account':
            log.error(f"Invalid credential type: {creds_json.get('type')}. Expected 'service_account'")
            return False
        
        # Check private key format
        if not creds_json.get('private_key', '').startswith('-----BEGIN PRIVATE KEY-----'):
            log.error("Private key is not in the correct format")
            return False
        
        log.info(f"Service account file format is valid")
        log.info(f"Project ID: {creds_json.get('project_id')}")
        log.info(f"Client email: {creds_json.get('client_email')}")
        return True
    
    except json.JSONDecodeError:
        log.error(f"Service account file is not valid JSON")
        return False
    except Exception as e:
        log.error(f"Error validating service account file: {e}")
        return False

def test_service_account_auth(file_path):
    """Test authentication using service account"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            file_path,
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        log.info(f"Successfully loaded service account credentials")
        
        # Test with BigQuery
        client = bigquery.Client(credentials=credentials)
        log.info(f"Successfully created BigQuery client")
        
        # Try a simple query
        query = "SELECT 1"
        query_job = client.query(query)
        result = query_job.result()
        log.info(f"Successfully executed test query")
        
        return True
    
    except Exception as e:
        log.error(f"Error authenticating with service account: {e}")
        return False

def test_default_auth():
    """Test authentication using default credentials"""
    try:
        client = bigquery.Client()
        log.info(f"Successfully created BigQuery client with default credentials")
        
        # Try a simple query
        query = "SELECT 1"
        query_job = client.query(query)
        result = query_job.result()
        log.info(f"Successfully executed test query with default credentials")
        
        return True
    
    except DefaultCredentialsError:
        log.error("No default credentials available")
        return False
    except Exception as e:
        log.error(f"Error authenticating with default credentials: {e}")
        return False

def suggest_fixes(creds_path):
    """Suggest fixes for authentication issues"""
    log.info("\n--- SUGGESTIONS ---")
    
    if not creds_path:
        log.info("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable to the path of your service account key file")
        log.info("   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account_key.json")
    
    log.info("2. Make sure the service account key file is valid JSON and has all required fields")
    log.info("3. Check that the service account has necessary permissions in Google Cloud")
    log.info("4. Try generating a new service account key in the Google Cloud Console")
    log.info("5. For local development, you can also use 'gcloud auth application-default login'")
    
    log.info("\nTo create a new service account and key file:")
    log.info("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    log.info("2. Navigate to IAM & Admin > Service Accounts")
    log.info("3. Create a new service account or select an existing one")
    log.info("4. Add BigQuery User and BigQuery Data Viewer roles")
    log.info("5. Create and download a new key file (JSON format)")
    log.info("6. Set GOOGLE_APPLICATION_CREDENTIALS to point to the downloaded file")

def main():
    log.info("=== BigQuery Authentication Diagnostic Tool ===")
    
    # Check environment variables
    creds_path = check_environment_variables()
    
    # If credentials path is set, validate the file
    if creds_path:
        file_valid = validate_service_account_file(creds_path)
        if file_valid:
            # Test authentication with service account
            auth_success = test_service_account_auth(creds_path)
            if auth_success:
                log.info("Service account authentication successful!")
            else:
                log.warning("Service account authentication failed!")
    else:
        log.warning("GOOGLE_APPLICATION_CREDENTIALS not set")
    
    # Try default authentication
    log.info("\nTrying default authentication method...")
    default_auth_success = test_default_auth()
    if default_auth_success:
        log.info("Default authentication successful!")
    else:
        log.warning("Default authentication failed!")
    
    # If both authentication methods failed, suggest fixes
    if (creds_path and not auth_success) or (not creds_path and not default_auth_success):
        suggest_fixes(creds_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
