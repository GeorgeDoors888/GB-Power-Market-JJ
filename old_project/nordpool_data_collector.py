#!/usr/bin/env python3
"""
nordpool_data_collector.py

This script fetches historical intraday data from the Nord Pool public API
and uploads it to Google Cloud Storage.

It handles OAuth 2.0 authentication to get an access token and then uses
that token to download data from the specified endpoints.
"""
import os
import sys
import requests
import json
import time
import base64
from datetime import datetime, timedelta
from google.cloud import storage
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv('api.env')

# Nord Pool API Credentials and URLs
NORDPOOL_CLIENT_ID = os.getenv('NORDPOOL_CLIENT_ID')
NORDPOOL_CLIENT_SECRET = os.getenv('NORDPOOL_CLIENT_SECRET')
NORDPOOL_USERNAME = os.getenv('NORDPOOL_USERNAME')
NORDPOOL_PASSWORD = os.getenv('NORDPOOL_PASSWORD')
TOKEN_URL = 'https://sts.nordpoolgroup.com/connect/token'
API_BASE_URL = 'https://www.nordpoolgroup.com/api'

# Google Cloud Storage
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'jibber-jabber-knowledge-bmrs-data')
ROOT_PREFIX = 'nordpool_data'

# Data Collection Settings
START_DATE = datetime(2022, 1, 1)  # Nord Pool public API has data from late 2021
END_DATE = datetime.now()

# Initialize Google Cloud Storage client
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def get_access_token():
    """
    Retrieves an OAuth 2.0 access token from the Nord Pool authentication server
    using the Resource Owner Password Credentials grant type.
    """
    if not all([NORDPOOL_CLIENT_ID, NORDPOOL_CLIENT_SECRET, NORDPOOL_USERNAME, NORDPOOL_PASSWORD]):
        print("❌ ERROR: NORDPOOL_CLIENT_ID, NORDPOOL_CLIENT_SECRET, NORDPOOL_USERNAME, and NORDPOOL_PASSWORD must be set in api.env")
        return None

    # Create the Basic Auth string by base64 encoding client_id:client_secret
    auth_string = f"{NORDPOOL_CLIENT_ID}:{NORDPOOL_CLIENT_SECRET}"
    encoded_auth_string = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

    headers = {
        'Authorization': f'Basic {encoded_auth_string}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = {
        'grant_type': 'password',
        'scope': 'public-data-api', # Scope for the public data API
        'username': NORDPOOL_USERNAME,
        'password': NORDPOOL_PASSWORD
    }

    try:
        auth_response = requests.post(TOKEN_URL, headers=headers, data=payload)
        auth_response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to get access token. Exception: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Body: {e.response.text}")
        return None

    token_data = auth_response.json()
    print("✅ Successfully obtained Nord Pool API access token.")
    return token_data.get('access_token')

def main():
    """
    Main function to orchestrate the data collection process.
    """
    print("--- Starting Nord Pool Data Collector ---")
    
    access_token = get_access_token()
    if not access_token:
        sys.exit(1)

    # In the next steps, we will add functions here to:
    # 1. List existing files in GCS to avoid re-downloads.
    # 2. Create a list of download tasks (e.g., one per day for each endpoint).
    # 3. Fetch data using the access token.
    # 4. Upload the data to GCS.
    
    print("--- Nord Pool Data Collector Finished ---")


if __name__ == '__main__':
    main()
