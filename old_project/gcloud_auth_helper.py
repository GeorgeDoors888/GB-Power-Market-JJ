#!/usr/bin/env python3
"""
Google Cloud Authentication Helper (Simplified)

This script helps you authenticate with Google Cloud using the standard gcloud auth flow.
It provides step-by-step instructions for authentication through a browser.

Usage:
    python3 gcloud_auth_helper.py
"""

import subprocess
import platform
import os
import sys
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def run_command(command, capture=True):
    """Run a command and optionally capture its output."""
    try:
        if capture:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            # Run without capturing output (interactive mode)
            result = subprocess.run(command, shell=True)
            return "", "", result.returncode
    except Exception as e:
        return "", str(e), -1

def main():
    print_header("Google Cloud Authentication Helper")
    
    # Check for gcloud installation
    stdout, stderr, rc = run_command("gcloud --version | head -1")
    if rc != 0:
        print("❌ Google Cloud SDK is not installed or not in PATH")
        print("Please install it from: https://cloud.google.com/sdk/docs/install")
        return
    
    print(f"✅ Found Google Cloud SDK: {stdout}")
    
    # Check current auth status
    print_header("Current Authentication Status")
    stdout, stderr, rc = run_command("gcloud auth list")
    if rc == 0:
        print(stdout if stdout else "No authenticated accounts found.")
    else:
        print("❌ Error checking authentication status:")
        print(stderr)
    
    # Check current project
    stdout, stderr, rc = run_command("gcloud config get-value project")
    if rc == 0 and stdout and stdout != "(unset)":
        print(f"✅ Current project: {stdout}")
    else:
        print("❓ No project is currently set")
    
    print_header("Authentication Options")
    print("1. Authenticate with User Account (for browser-based auth)")
    print("2. Set up Application Default Credentials (for development)")
    
    choice = input("\nSelect an option (1/2): ").strip() or "1"
    
    if choice == "1":
        print_header("User Account Authentication")
        print("This will open your default browser for authentication.")
        print("After authenticating in your browser, return to this terminal.")
        input("Press Enter to continue...")
        
        # Run the login command interactively (without capturing output)
        print("\nStarting authentication process...")
        _, _, rc = run_command("gcloud auth login", capture=False)
        
        if rc == 0:
            print("✅ Authentication successful")
        else:
            print("❌ Authentication failed. Please try again.")
            return
    
    elif choice == "2":
        print_header("Application Default Credentials")
        print("This will set up credentials for local development tools.")
        print("After authenticating in your browser, return to this terminal.")
        input("Press Enter to continue...")
        
        # Run the application-default login command interactively
        print("\nStarting authentication process...")
        _, _, rc = run_command("gcloud auth application-default login", capture=False)
        
        if rc == 0:
            print("✅ Application default credentials set up successfully")
        else:
            print("❌ Failed to set up application default credentials")
            return
    
    else:
        print("Invalid option. Please run the script again.")
        return
    
    # Set project after authentication
    print_header("Project Configuration")
    
    # Check if project is set
    stdout, stderr, rc = run_command("gcloud config get-value project")
    current_project = stdout.strip() if rc == 0 and stdout and stdout != "(unset)" else None
    
    if current_project:
        print(f"Current project is set to: {current_project}")
        change = input("Do you want to change the project? (y/N): ").strip().lower()
        if change == 'y':
            set_project()
    else:
        print("No project is currently set.")
        set_project()
    
    # Final check
    print_header("Verification Tests")
    
    # Test BigQuery access
    print("Testing BigQuery access...")
    stdout, stderr, rc = run_command("bq ls")
    if rc == 0:
        print("✅ BigQuery access successful")
    else:
        print("❌ BigQuery access failed:")
        print(stderr)
    
    # Test Cloud Storage access
    print("\nTesting Cloud Storage access...")
    stdout, stderr, rc = run_command("gsutil ls")
    if rc == 0:
        print("✅ Cloud Storage access successful")
    else:
        print("❌ Cloud Storage access failed:")
        print(stderr)
    
    print_header("Next Steps")
    print("1. Try creating a dataset in BigQuery: bq mk --dataset PROJECT_ID:uk_energy_prod")
    print("2. Update tables: python3 export_bq_to_eu.py")
    print("3. Update PROJECT_MEMORY.md with your findings")

def set_project():
    """Set the Google Cloud project."""
    project_id = input("Enter the project ID (e.g., jibber-jabber-knowledge): ").strip()
    if project_id:
        stdout, stderr, rc = run_command(f"gcloud config set project {project_id}")
        if rc == 0:
            print(f"✅ Project set to: {project_id}")
        else:
            print(f"❌ Failed to set project to {project_id}:")
            print(stderr)

if __name__ == "__main__":
    main()
