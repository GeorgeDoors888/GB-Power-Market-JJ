#!/usr/bin/env python3
"""
Google Cloud Authorization Helper

This script helps you authorize with Google Cloud through a web browser.
It will generate a URL for you to open in Safari or any browser to authenticate.

Usage:
    python3 authorize_gcp_browser.py
"""

import os
import webbrowser
import subprocess
import json
from pathlib import Path
import platform

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def run_command(command):
    """Run a command and return its output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def open_in_safari(url):
    """Open URL in Safari browser."""
    if platform.system() == 'Darwin':  # macOS
        try:
            subprocess.run(['open', '-a', 'Safari', url])
            return True
        except Exception as e:
            print(f"Error opening Safari: {e}")
            return False
    else:
        print("Safari is only available on macOS. Using default browser instead.")
        return False

def main():
    print_header("Google Cloud Authorization Helper")
    
    # Check if gcloud is installed
    stdout, stderr, rc = run_command("gcloud --version")
    if rc != 0:
        print("❌ gcloud command-line tool is not installed or not in PATH")
        print("Please install the Google Cloud SDK first: https://cloud.google.com/sdk/docs/install")
        return
    
    print("✅ Google Cloud SDK is installed")
    
    # Show current auth status
    print_header("Current Authentication Status")
    stdout, stderr, rc = run_command("gcloud auth list")
    if rc == 0:
        print(stdout)
    else:
        print("❌ Error checking authentication status:")
        print(stderr)
    
    # Print the current project
    stdout, stderr, rc = run_command("gcloud config get-value project")
    if rc == 0 and stdout and stdout != "(unset)":
        print(f"✅ Current project: {stdout}")
    else:
        print("❓ No project is currently set")
    
    # Offer options to the user
    print_header("Authentication Options")
    print("1. User Account Authentication (for browser-based authorization)")
    print("2. Application Default Credentials (for local development)")
    
    choice = input("\nPlease select an option (1 or 2, default is 1): ").strip() or "1"
    
    if choice == "1":
        print_header("User Account Authentication")
        print("This will open your browser for authentication...")
        
        # Generate a login URL and open in Safari
        if open_in_safari("https://accounts.google.com/o/oauth2/auth?client_id=32555940559.apps.googleusercontent.com&redirect_uri=https://gcp-auth-helper.web.app/auth&response_type=code&scope=openid%20https://www.googleapis.com/auth/userinfo.email%20https://www.googleapis.com/auth/cloud-platform&access_type=offline"):
            print("✅ Safari should now be open. Please log in with your Google account.")
        else:
            # Fall back to gcloud auth login which will open the default browser
            print("Falling back to gcloud auth login...")
            stdout, stderr, rc = run_command("gcloud auth login")
            if rc == 0:
                print("✅ Authentication successful")
            else:
                print("❌ Authentication failed:")
                print(stderr)
    
    elif choice == "2":
        print_header("Application Default Credentials")
        print("This will set up application default credentials for local development...")
        
        # Generate a login URL for application default credentials and open in Safari
        if open_in_safari("https://accounts.google.com/o/oauth2/auth?client_id=764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com&redirect_uri=https://gcp-auth-helper.web.app/auth&response_type=code&scope=openid%20https://www.googleapis.com/auth/userinfo.email%20https://www.googleapis.com/auth/cloud-platform&access_type=offline"):
            print("✅ Safari should now be open. Please log in with your Google account.")
        else:
            # Fall back to gcloud auth application-default login which will open the default browser
            print("Falling back to gcloud auth application-default login...")
            stdout, stderr, rc = run_command("gcloud auth application-default login")
            if rc == 0:
                print("✅ Application default credentials set up successfully")
            else:
                print("❌ Failed to set up application default credentials:")
                print(stderr)
    
    else:
        print("Invalid option selected. Please run the script again.")
        return
    
    # After authentication, check project
    print_header("Project Selection")
    stdout, stderr, rc = run_command("gcloud config get-value project")
    current_project = stdout.strip() if rc == 0 and stdout and stdout != "(unset)" else None
    
    if current_project:
        print(f"Current project is set to: {current_project}")
        change = input(f"Do you want to change the project? (y/N): ").strip().lower()
        if change == 'y':
            project_id = input("Enter the project ID: ").strip()
            if project_id:
                stdout, stderr, rc = run_command(f"gcloud config set project {project_id}")
                if rc == 0:
                    print(f"✅ Project set to: {project_id}")
                else:
                    print(f"❌ Failed to set project to {project_id}:")
                    print(stderr)
    else:
        project_id = input("No project is set. Enter the project ID (e.g., jibber-jabber-knowledge): ").strip()
        if project_id:
            stdout, stderr, rc = run_command(f"gcloud config set project {project_id}")
            if rc == 0:
                print(f"✅ Project set to: {project_id}")
            else:
                print(f"❌ Failed to set project to {project_id}:")
                print(stderr)
    
    # Final check
    print_header("Final Authentication Status")
    stdout, stderr, rc = run_command("gcloud auth list")
    if rc == 0:
        print(stdout)
    else:
        print("❌ Error checking authentication status:")
        print(stderr)
    
    stdout, stderr, rc = run_command("gcloud config get-value project")
    if rc == 0 and stdout and stdout != "(unset)":
        print(f"✅ Current project: {stdout}")
    else:
        print("❓ No project is currently set")
    
    print("\nYou should now be able to use BigQuery and other Google Cloud services.")
    print("Try running 'bq ls' to check if you can access BigQuery datasets.")

if __name__ == "__main__":
    main()
