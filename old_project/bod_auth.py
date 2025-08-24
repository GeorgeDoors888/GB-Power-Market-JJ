#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended Authentication Module for BOD Analysis
==============================================

This module provides advanced authentication functionality that can be imported 
into the direct_bod_analysis.py script. It implements multiple authentication
fallback mechanisms for BigQuery access.

Usage:
    from bod_auth import get_bigquery_client
    
    client = get_bigquery_client(
        project_id="your-project-id",
        service_account_path="/path/to/key.json",  # optional
    )

Authentication Methods (in order of precedence):
1. Service account JSON key file (explicit path)
2. GOOGLE_APPLICATION_CREDENTIALS environment variable
3. Common credential file locations
4. Application Default Credentials (ADC)
5. OAuth browser flow (if dependencies are available)
6. Default authentication (works on GCP or with ADC)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Google Cloud
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# Constants
BIGQUERY_SCOPES = ["https://www.googleapis.com/auth/bigquery"]
DEFAULT_CREDENTIALS_PATHS = [
    "client_secret.json",
    "service-account.json",
    "key.json",
    "credentials.json",
    os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
]
TOKEN_PATH = os.path.expanduser("~/.config/bod_analysis/token.json")

# Try to import OAuth dependencies
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False


def get_bigquery_client(
    project_id: str,
    service_account_path: Optional[str] = None,
    verbose: bool = False
) -> Optional[bigquery.Client]:
    """
    Get a BigQuery client with credentials from any available source.
    
    Args:
        project_id: The Google Cloud project ID
        service_account_path: Optional path to a service account key file
        verbose: Whether to print verbose authentication messages
    
    Returns:
        A BigQuery client object or None if all authentication methods fail
    """
    # Track authentication attempts
    auth_attempts = []
    
    if verbose:
        log.setLevel(logging.DEBUG)
    
    # 1. Try explicit service account path if provided
    if service_account_path:
        try:
            log.debug(f"Attempting authentication with service account: {service_account_path}")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=BIGQUERY_SCOPES
            )
            auth_attempts.append(f"Service account file (explicit): {service_account_path}")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as e:
            log.warning(f"Failed to authenticate with explicit service account: {e}")
    
    # 2. Try GOOGLE_APPLICATION_CREDENTIALS environment variable
    env_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if env_creds_path:
        try:
            log.debug(f"Attempting authentication with GOOGLE_APPLICATION_CREDENTIALS: {env_creds_path}")
            credentials = service_account.Credentials.from_service_account_file(
                env_creds_path, scopes=BIGQUERY_SCOPES
            )
            auth_attempts.append(f"GOOGLE_APPLICATION_CREDENTIALS: {env_creds_path}")
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as e:
            log.warning(f"Failed to authenticate with GOOGLE_APPLICATION_CREDENTIALS: {e}")
    
    # 3. Try common credential file locations
    for path in DEFAULT_CREDENTIALS_PATHS:
        if os.path.exists(path):
            try:
                log.debug(f"Attempting authentication with file: {path}")
                credentials = service_account.Credentials.from_service_account_file(
                    path, scopes=BIGQUERY_SCOPES
                )
                auth_attempts.append(f"Found credentials file: {path}")
                return bigquery.Client(credentials=credentials, project=project_id)
            except Exception as e:
                log.warning(f"Failed to authenticate with {path}: {e}")
    
    # 4. Try application default credentials
    try:
        log.debug("Attempting authentication with application default credentials")
        credentials, _ = default(scopes=BIGQUERY_SCOPES)
        auth_attempts.append("Application Default Credentials")
        return bigquery.Client(credentials=credentials, project=project_id)
    except Exception as e:
        log.warning(f"Failed to authenticate with application default credentials: {e}")
    
    # 5. Try OAuth flow if available
    if HAS_OAUTH:
        try:
            log.debug("Attempting OAuth authentication flow")
            
            # Find client secret file
            client_secret_file = None
            for path in ["client_secret.json", "oauth_client.json"]:
                if os.path.exists(path):
                    client_secret_file = path
                    break
            
            if client_secret_file:
                # Check for existing token
                token_dir = os.path.dirname(TOKEN_PATH)
                os.makedirs(token_dir, exist_ok=True)
                
                creds = None
                if os.path.exists(TOKEN_PATH):
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
                return bigquery.Client(credentials=creds, project=project_id)
            else:
                log.warning("No client_secret.json found for OAuth flow")
        except Exception as e:
            log.warning(f"Failed to authenticate with OAuth: {e}")
    
    # 6. Final attempt with no credentials (works on GCP or if user already set up ADC)
    try:
        log.debug("Attempting to create client with no explicit credentials")
        client = bigquery.Client(project=project_id)
        
        # Test with a minimal query
        client.query("SELECT 1").result()
        
        auth_attempts.append("Default authentication (implicit)")
        return client
    except Exception as e:
        log.error(f"Failed to create client with default authentication: {e}")
    
    # All authentication methods failed
    log.error("All authentication methods failed. Authentication attempts:")
    for i, attempt in enumerate(auth_attempts, 1):
        log.error(f"  {i}. {attempt}")
    
    return None


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Test BigQuery Authentication")
    parser.add_argument("--project", required=True, help="Google Cloud project ID")
    parser.add_argument("--key-file", help="Optional service account key file path")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Test authentication
    client = get_bigquery_client(
        project_id=args.project,
        service_account_path=args.key_file,
        verbose=args.verbose
    )
    
    if client:
        print("\n✅ Successfully authenticated with BigQuery")
        
        # Run a test query
        try:
            query_job = client.query("SELECT 1 as test")
            results = list(query_job.result())
            print(f"✅ Test query result: {results[0].test}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
    else:
        print("\n❌ Failed to authenticate with BigQuery")
        sys.exit(1)
