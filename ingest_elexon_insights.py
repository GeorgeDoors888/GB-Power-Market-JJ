#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Elexon Insights API data ingestion script.

This script downloads data from the Elexon Insights API for a specified date range
and saves it to local JSON files. It is designed to be robust against API
inconsistencies and provides progress tracking.
"""

import argparse
import logging
import os
import time
import inspect
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from elexonpy.api_client import ApiClient
from elexonpy.api.datasets_api import DatasetsApi
from elexonpy.configuration import Configuration

# --- Configuration ---
API_KEY = os.environ.get("ELEXON_API_KEY")
if not API_KEY:
    print("Error: ELEXON_API_KEY environment variable not set.")
    exit(1)

# --- Main Functions ---

def get_valid_date_params(method):
    """
    Inspects a method to find valid date parameter names.
    Elexon's API is inconsistent, so we need to check for common variants.
    """
    spec = inspect.getfullargspec(method)
    possible_date_params = [
        'from_date', 'from_datetime', 'start_date', 'start_time',
        'publish_date', 'publish_date_time_from', 'settlement_date_from'
    ]
    
    # Find the 'from' and 'to' parameters
    from_param = None
    to_param = None

    for param in spec.args:
        if param in possible_date_params:
            from_param = param
            # Construct the corresponding 'to' parameter
            if 'from' in param:
                to_param = param.replace('from', 'to')
            elif 'start' in param:
                to_param = param.replace('start', 'end')
            
            if to_param in spec.args:
                return from_param, to_param

    return None, None


def discover_dataset_methods(api_instance):
    """
    Discovers all public methods on the DatasetsApi that appear to be for
    fetching datasets and have date range parameters.
    """
    dataset_methods = {}
    for name, method in inspect.getmembers(api_instance, predicate=inspect.ismethod):
        if not name.startswith('_') and 'get' in name:
            from_param, to_param = get_valid_date_params(method)
            if from_param and to_param:
                dataset_methods[name] = {
                    "method": method,
                    "from_param": from_param,
                    "to_param": to_param
                }
    return dataset_methods

def ingest_data(start_date_str, end_date_str, data_dir, log_file):
    """
    Main function to ingest data from the Elexon Insights API.
    """
    # --- Setup Logging ---
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
    logging.info("--- Starting Elexon Insights Ingestion ---")

    # --- Setup API Client ---
    config = Configuration()
    config.api_key['api_key'] = API_KEY
    api_client = ApiClient(configuration=config)
    datasets_api = DatasetsApi(api_client)

    # --- Discover Methods ---
    logging.info("Discovering available dataset methods...")
    dataset_methods = discover_dataset_methods(datasets_api)
    if not dataset_methods:
        logging.error("No date-range compatible dataset methods were found. Exiting.")
        return
    logging.info(f"Found {len(dataset_methods)} compatible dataset methods.")

    # --- Date Range ---
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    date_range = pd.date_range(start_date, end_date, freq='D')

    # --- Setup Data Directory ---
    data_path = Path(data_dir)
    data_path.mkdir(exist_ok=True)
    logging.info(f"Saving raw data to: {data_path.resolve()}")

    # --- Main Ingestion Loop ---
    overall_progress = tqdm(total=len(dataset_methods), desc="Overall Progress")
    for method_name, method_info in dataset_methods.items():
        overall_progress.set_description(f"Processing: {method_name}")
        dataset_dir = data_path / method_name
        dataset_dir.mkdir(exist_ok=True)
        
        day_progress = tqdm(total=len(date_range), desc=f"{method_name[:20]:<20}", leave=False)
        
        for single_date in date_range:
            day_str = single_date.strftime('%Y-%m-%d')
            day_progress.set_description(f"{method_name[:20]:<20} ({day_str})")
            
            output_file = dataset_dir / f"{day_str}.json"
            if output_file.exists():
                day_progress.update(1)
                continue

            try:
                # Prepare arguments for the API call
                api_args = {
                    method_info['from_param']: single_date.strftime('%Y-%m-%d %H:%M:%S'),
                    method_info['to_param']: (single_date + timedelta(days=1) - timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'format': 'json'
                }
                
                # Call the API method
                api_response = method_info['method'](**api_args)
                
                # Save the response
                with open(output_file, 'w') as f:
                    f.write(api_response)
                
                logging.info(f"Successfully downloaded {method_name} for {day_str}")
                time.sleep(0.5) # Be nice to the API

            except Exception as e:
                logging.error(f"Failed to download {method_name} for {day_str}. Error: {e}")

            day_progress.update(1)
        
        day_progress.close()
        overall_progress.update(1)

    overall_progress.close()
    logging.info("--- Elexon Insights Ingestion Complete ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest data from the Elexon Insights API.")
    parser.add_argument("--start", required=True, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument("--data-dir", default="raw_data", help="Directory to save the raw JSON data.")
    parser.add_argument("--log-file", default="ingestion.log", help="Path to the log file.")
    
    args = parser.parse_args()
    
    ingest_data(args.start, args.end, args.data_dir, args.log_file)
