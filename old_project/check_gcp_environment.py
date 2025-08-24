#!/usr/bin/env python3
"""
BigQuery Environment Test Script

This script checks if Google Cloud libraries are properly installed
and configured.
"""

import os
import sys
import pkg_resources

def check_package(package_name):
    """Check if a package is installed and get its version."""
    try:
        version = pkg_resources.get_distribution(package_name).version
        return True, version
    except pkg_resources.DistributionNotFound:
        return False, None

def main():
    """Main function to check environment."""
    print("Python Environment Check")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Check for required packages
    required_packages = [
        'google-cloud-bigquery',
        'google-cloud-storage',
        'google-auth'
    ]
    
    print("\nChecking required packages:")
    for package in required_packages:
        installed, version = check_package(package)
        if installed:
            print(f"✓ {package} (version {version})")
        else:
            print(f"✗ {package} is not installed")
    
    # Try to import modules
    print("\nImporting modules:")
    modules_to_check = [
        ('google.cloud', 'Google Cloud base module'),
        ('google.cloud.bigquery', 'BigQuery module'),
        ('google.cloud.storage', 'Storage module')
    ]
    
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {description} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {description}: {e}")
    
    # Check authentication
    print("\nChecking authentication:")
    adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    if os.path.exists(adc_path):
        print(f"✓ Application Default Credentials found at {adc_path}")
    else:
        print(f"✗ Application Default Credentials not found at {adc_path}")
    
    # Try to create clients
    print("\nTrying to initialize clients:")
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        print("✓ BigQuery client created successfully")
    except Exception as e:
        print(f"✗ Failed to create BigQuery client: {e}")
    
    try:
        from google.cloud import storage
        client = storage.Client()
        print("✓ Storage client created successfully")
    except Exception as e:
        print(f"✗ Failed to create Storage client: {e}")

if __name__ == "__main__":
    main()
