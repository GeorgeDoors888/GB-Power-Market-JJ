#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOD Analysis Helper
==================

This script provides easy access to BOD (Bid-Offer Data) analysis using our custom authentication
module for BigQuery.

Usage:
    python run_bod_with_auth.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] 
                               [--key-file PATH] [--reset] [--synthetic]

Options:
    --start-date YYYY-MM-DD   Start date for analysis (default: 30 days ago)
    --end-date YYYY-MM-DD     End date for analysis (default: today)
    --key-file PATH           Path to service account key file
    --reset                   Force re-authentication
    --synthetic               Use synthetic data (don't connect to BigQuery)
"""

import os
import sys
import logging
import argparse
import datetime as dt
import subprocess
from pathlib import Path

# Add the current directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Try to import our custom authentication module
try:
    from bq_auth import get_auth_client, clear_cached_credentials
    HAS_AUTH_MODULE = True
except ImportError as e:
    print(f"WARNING: Custom authentication module (bq_auth.py) not found: {e}")
    print("Please ensure bq_auth.py is in the same directory as this script.")
    print(f"Current directory: {current_dir}")
    print(f"Files in directory: {os.listdir(current_dir)}")
    HAS_AUTH_MODULE = False

# Constants
DEFAULT_PROJECT_ID = "jibber-jabber-knowledge"
DEFAULT_DATASET = "uk_energy_prod"
DEFAULT_OUTPUT_DIR = "./bod_analysis_output"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("bod_analysis")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="BOD Analysis with Custom Authentication")
    
    parser.add_argument("--start-date", type=str,
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str,
                        help="End date (YYYY-MM-DD)")
    parser.add_argument("--key-file", type=str,
                        help="Path to service account key file")
    parser.add_argument("--reset", action="store_true",
                        help="Force re-authentication")
    parser.add_argument("--synthetic", action="store_true",
                        help="Use synthetic data (don't connect to BigQuery)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Handle authentication if needed
    if not args.synthetic and HAS_AUTH_MODULE:
        try:
            logger.info("Authenticating with BigQuery...")
            client, auth_method = get_auth_client(
                project_id=DEFAULT_PROJECT_ID,
                service_account_path=args.key_file,
                force_reset=args.reset
            )
            logger.info(f"Authentication successful using method: {auth_method}")
            
            # Test connection with a simple query
            query = "SELECT CURRENT_TIMESTAMP() as now"
            result = client.query(query).result().to_dataframe()
            logger.info(f"Current time in BigQuery: {result['now'].iloc[0]}")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            if not args.synthetic:
                logger.info("Falling back to synthetic data")
                args.synthetic = True
    elif not HAS_AUTH_MODULE and not args.synthetic:
        logger.warning("Authentication module not available. Using default authentication or synthetic data.")
    
    # Process dates
    end_date = dt.datetime.now().date()
    if args.end_date:
        try:
            end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid end date format: {args.end_date}. Using today.")
    
    start_date = end_date - dt.timedelta(days=30)  # Default to 30 days ago
    if args.start_date:
        try:
            start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid start date format: {args.start_date}. Using 30 days ago.")
    
    logger.info(f"Analysis period: {start_date} to {end_date}")
    
    # Run BOD analysis using the direct_bod_analysis.py script
    try:
        logger.info("Running BOD analysis...")
        
        # Build command
        cmd_parts = []
        
        # Use the Python executable from the current environment
        if os.path.exists("venv/bin/python"):
            cmd_parts.append("venv/bin/python")
        elif os.path.exists("./venv/bin/python"):
            cmd_parts.append("./venv/bin/python")
        elif sys.executable:
            cmd_parts.append(f'"{sys.executable}"')
        else:
            cmd_parts.append("python3")  # Fallback to python3
            
        cmd_parts.append("direct_bod_analysis.py")
        cmd_parts.append(f"--start-date={start_date.strftime('%Y-%m-%d')}")
        cmd_parts.append(f"--end-date={end_date.strftime('%Y-%m-%d')}")
        
        if args.synthetic:
            cmd_parts.append("--use-synthetic")
        
        if args.debug:
            cmd_parts.append("--debug")
        
        # Execute the command
        import subprocess
        cmd = " ".join(cmd_parts)
        logger.info(f"Executing: {cmd}")
        
        result = subprocess.run(cmd, shell=True, check=True)
        
        if result.returncode == 0:
            logger.info("BOD analysis completed successfully")
            return 0
        else:
            logger.error(f"BOD analysis failed with exit code: {result.returncode}")
            return result.returncode
            
    except Exception as e:
        logger.error(f"Failed to run BOD analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
