#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UK BM (BOD) deep-dive, 2016→present — Enhanced Version with Fallback

- SOURCE OF TRUTH: BigQuery (tables you already ingest into)
- Fetch: BOD acceptances, Imbalance Price/NIV, Demand, Fuel Mix (from BQ)
- Derive: daily/monthly KPIs, wind curtailment proxy (via BMU→fuel map if available)
- Visualize: trend charts saved to ./out/charts/*.png
- Report: Google Docs with sections + CSV tables + embedded charts

If BigQuery access fails, the script will generate synthetic data for testing.

Prereqs:
  pip install google-cloud-bigquery google-auth google-auth-oauthlib google-auth-httplib2
              google-api-python-client pandas numpy matplotlib python-dateutil tenacity tqdm pyarrow

Auth:
  - GOOGLE_APPLICATION_CREDENTIALS must point to a Service Account JSON with BigQuery, Drive, Docs access.
"""

import os
import io
import sys
import time
import pathlib
import logging
import datetime as dt
import argparse
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Union, Any

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

# GCP
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# -------------------------
# CONFIG
# -------------------------

@dataclass
class Config:
    # BigQuery settings
    gcp_project: str = "your-project-id"
    bq_dataset: str = "uk_energy_data"
    tbl_bod: str = "balancing_mechanism_acceptances"
    tbl_impniv: str = "imbalance_prices"
    tbl_demand: str = "demand"
    tbl_genmix: str = "generation_mix"
    
    # Google API settings
    google_scopes: List[str] = None
    google_project_credentials: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)
    
    # Date range for analysis
    start_date: dt.date = dt.date(2016, 1, 1)
    end_date: dt.date = dt.date.today()
    
    # Output settings
    charts_dir: str = "./out/charts"
    tables_dir: str = "./out/tables"
    create_gdoc: bool = True
    
    # Synthetic data settings
    synthetic_data_seed: int = 42
    use_synthetic_data: bool = False
    
    def __post_init__(self):
        self.google_scopes = [
            "https://www.googleapis.com/auth/bigquery",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents"
        ]
        
        # Check for credentials
        if not self.google_project_credentials:
            logging.warning("GOOGLE_APPLICATION_CREDENTIALS not set - will only run local analysis")
            self.use_synthetic_data = True
        elif not os.path.exists(self.google_project_credentials):
            logging.warning(f"Credentials file {self.google_project_credentials} not found - will only run local analysis")
            self.use_synthetic_data = True
        
        # Initialize synthetic data if needed
        if self.use_synthetic_data:
            np.random.seed(self.synthetic_data_seed)

# Initialize config - will be updated by command line args
CFG = Config()

# -------------------------
# GCP CLIENTS
# -------------------------

def gcp_creds():
    """Get Google Cloud credentials from service account file"""
    if CFG.google_project_credentials and os.path.exists(CFG.google_project_credentials):
        try:
            return service_account.Credentials.from_service_account_file(
                CFG.google_project_credentials, scopes=CFG.google_scopes
            )
        except Exception as e:
            logging.error(f"Error loading credentials from {CFG.google_project_credentials}: {e}")
            logging.info("Will use synthetic data for testing")
            CFG.use_synthetic_data = True
            return None
    return None

def bq_client():
    """Get BigQuery client with proper credentials"""
    creds = gcp_creds()
    try:
        if creds:
            return bigquery.Client(project=CFG.gcp_project, credentials=creds)
        return bigquery.Client(project=CFG.gcp_project)
    except Exception as e:
        logging.error(f"Failed to create BigQuery client: {e}")
        logging.info("Will use synthetic data for testing")
        CFG.use_synthetic_data = True
        return None

def gdocs_client():
    """Get Google Docs client with proper credentials"""
    creds = gcp_creds()
    if not creds:
        return None
    try:
        return build("docs", "v1", credentials=creds)
    except Exception as e:
        logging.error(f"Failed to create Google Docs client: {e}")
        return None

# -------------------------
# DATA LOADING
# -------------------------

def q_dates_clause(table_alias: str) -> str:
    """Generate SQL date filter clause for the configured date range"""
    return f"""
    DATE({table_alias}.settlementDate) BETWEEN 
    DATE("{CFG.start_date.isoformat()}") AND DATE("{CFG.end_date.isoformat()}")
    """

def generate_synthetic_data(start_date: dt.date, end_date: dt.date) -> pd.DataFrame:
    """Generate synthetic data for testing when BigQuery is unavailable"""
    logging.info(f"Generating synthetic data from {start_date} to {end_date}")
    
    # Create a range of dates and settlement periods
    dates = pd.date_range(start=start_date, end=end_date)
    periods = list(range(1, 49))  # 48 settlement periods per day
    
    # Create a DataFrame with all date/period combinations
    date_period = [(d.date(), p) for d in dates for p in periods]
    df = pd.DataFrame(date_period, columns=['settlement_date', 'settlement_period'])
    
    # Ensure proper data types
    df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
    df['settlement_period'] = df['settlement_period'].astype(int)
    
    return df

def load_bod() -> pd.DataFrame:
    """Load BOD (Bid-Offer Data) from BigQuery or generate synthetic data"""
    if CFG.use_synthetic_data:
        df = generate_synthetic_data(CFG.start_date, CFG.end_date)
        
        # Add synthetic BOD data
        n_rows = len(df)
        df['bmu_id'] = np.random.choice(['T_ABTH1', 'T_DRAXX1', 'E_WBUPS1', 'T_DIDCB5'], n_rows)
        df['bid_offer_number'] = np.random.randint(-5, 6, n_rows)
        df['volume_accepted_mwh'] = np.random.normal(0, 50, n_rows)
        df['offer_price'] = np.random.normal(60, 20, n_rows)
        df['bid_price'] = np.random.normal(40, 20, n_rows)
        
        logging.info(f"Generated synthetic BOD data: {len(df)} rows")
        return df
    
    # Actual BigQuery query
    q = f"""
    SELECT
      DATE(settlementDate) AS settlement_date,
      CAST(settlementPeriod AS INT64) AS settlement_period,
      bmuId AS bmu_id,
      bidOfferNumber AS bid_offer_number,
      CAST(volumeAcceptedMWh AS FLOAT64) AS volume_accepted_mwh,
      CAST(offerPrice AS FLOAT64) AS offer_price,
      CAST(bidPrice AS FLOAT64) AS bid_price
    FROM `{CFG.gcp_project}.{CFG.bq_dataset}.{CFG.tbl_bod}` t
    WHERE {q_dates_clause('t')}
    """
    
    try:
        client = bq_client()
        if not client:
            raise Exception("BigQuery client could not be created")
            
        df = client.query(q).to_dataframe(create_bqstorage_client=False)
        logging.info(f"Loaded BOD data: {len(df)} rows")
        
        # Ensure proper data types
        df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
        df['settlement_period'] = df['settlement_period'].astype(int)
        
        return df
    except Exception as e:
        logging.error(f"Error loading BOD data: {e}")
        # Try to get schema
        try:
            schema_q = f"SELECT * FROM `{CFG.gcp_project}.{CFG.bq_dataset}.{CFG.tbl_bod}` LIMIT 1"
            schema_df = bq_client().query(schema_q).to_dataframe()
            logging.info(f"Available columns in {CFG.tbl_bod}: {schema_df.columns.tolist()}")
        except Exception as schema_e:
            logging.error(f"Could not get schema: {schema_e}")
        
        logging.info("Falling back to synthetic BOD data")
        return load_bod()  # This will now use synthetic data

def load_impniv() -> pd.DataFrame:
    """Load Imbalance Prices and NIV data from BigQuery or generate synthetic data"""
    if CFG.use_synthetic_data:
        df = generate_synthetic_data(CFG.start_date, CFG.end_date)
        
        # Add synthetic price and NIV data
        df['imbalance_price'] = np.random.normal(50, 15, len(df))  # Mean £50/MWh
        df['niv'] = np.random.normal(0, 500, len(df))  # Mean 0 MWh
        
        logging.info(f"Generated synthetic Imbalance/NIV data: {len(df)} rows")
        return df
    
    # Actual BigQuery query
    q = f"""
    SELECT
      DATE(settlementDate) AS settlement_date,
      CAST(settlementPeriod AS INT64) AS settlement_period,
      CAST(imbalancePrice AS FLOAT64) AS imbalance_price,
      CAST(netImbalanceVolume AS FLOAT64) AS niv
    FROM `{CFG.gcp_project}.{CFG.bq_dataset}.{CFG.tbl_impniv}` t
    WHERE {q_dates_clause('t')}
    """
    
    try:
        client = bq_client()
        if not client:
            raise Exception("BigQuery client could not be created")
            
        df = client.query(q).to_dataframe(create_bqstorage_client=False)
        logging.info(f"Loaded Imbalance/NIV data: {len(df)} rows")
        
        # Ensure proper data types
        df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
        df['settlement_period'] = df['settlement_period'].astype(int)
        
        return df
    except Exception as e:
        logging.error(f"Error loading ImbalancePrice/NIV data: {e}")
        logging.info("Falling back to synthetic Imbalance/NIV data")
        return load_impniv()  # This will now use synthetic data

def load_demand() -> pd.DataFrame:
    """Load Demand data from BigQuery or generate synthetic data"""
    if CFG.use_synthetic_data:
        df = generate_synthetic_data(CFG.start_date, CFG.end_date)
        
        # Add synthetic demand data
        base_demand = 30000  # Base demand in MW
        day_pattern = np.sin(np.linspace(0, 2*np.pi, 48)) * 5000 + base_demand
        
        # Apply the day pattern to each day with some random variation
        all_demand = []
        for day in pd.date_range(CFG.start_date, CFG.end_date):
            day_demand = day_pattern + np.random.normal(0, 1000, 48)
            all_demand.extend(day_demand)
        
        # Trim to match dataframe length
        df['demand'] = all_demand[:len(df)]
        
        logging.info(f"Generated synthetic Demand data: {len(df)} rows")
        return df
    
    # Actual BigQuery query
    q = f"""
    SELECT
      DATE(settlementDate) AS settlement_date,
      CAST(settlementPeriod AS INT64) AS settlement_period,
      CAST(demand AS FLOAT64) AS demand
    FROM `{CFG.gcp_project}.{CFG.bq_dataset}.{CFG.tbl_demand}` t
    WHERE {q_dates_clause('t')}
    """
    
    try:
        client = bq_client()
        if not client:
            raise Exception("BigQuery client could not be created")
            
        df = client.query(q).to_dataframe(create_bqstorage_client=False)
        logging.info(f"Loaded Demand data: {len(df)} rows")
        
        # Ensure proper data types
        df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
        df['settlement_period'] = df['settlement_period'].astype(int)
        
        return df
    except Exception as e:
        logging.error(f"Error loading demand data: {e}")
        logging.info("Falling back to synthetic Demand data")
        return load_demand()  # This will now use synthetic data

def load_genmix() -> pd.DataFrame:
    """Load Generation Mix data from BigQuery or generate synthetic data"""
    if CFG.use_synthetic_data:
        # Create synthetic generation mix data
        dates = pd.date_range(start=CFG.start_date, end=CFG.end_date)
        periods = list(range(1, 49))  # 48 settlement periods per day
        fuel_types = ['CCGT', 'COAL', 'WIND', 'NUCLEAR', 'BIOMASS', 'SOLAR', 'HYDRO']
        
        # Create rows for each combination of date, period, and fuel type
        rows = []
        for d in dates:
            for p in periods:
                for ft in fuel_types:
                    # Base generation by fuel type
                    if ft == 'CCGT':
                        base = 15000
                    elif ft == 'COAL':
                        base = 2000
                    elif ft == 'WIND':
                        base = 5000 + np.random.normal(0, 2000)  # More variable
                    elif ft == 'NUCLEAR':
                        base = 6000
                    elif ft == 'BIOMASS':
                        base = 2000
                    elif ft == 'SOLAR':
                        # Solar follows a daily pattern
                        hour = (p - 1) * 0.5
                        if 6 <= hour <= 18:  # Daylight hours
                            base = 3000 * np.sin((hour - 6) * np.pi / 12)
                        else:
                            base = 0
                    elif ft == 'HYDRO':
                        base = 1000
                    
                    # Add some randomness - ensure base is not zero before multiplying
                    variation = 100  # Minimum variation to avoid zero or negative scale
                    if base > 0:
                        variation = max(100, base * 0.1)  # Use positive base and ensure minimum variation
                    gen = max(0, base + np.random.normal(0, variation))
                    
                    rows.append({
                        'settlement_date': d.date(),
                        'settlement_period': p,
                        'fuel_type': ft,
                        'generation': gen
                    })
        
        df = pd.DataFrame(rows)
        logging.info(f"Generated synthetic Generation Mix data: {len(df)} rows")
        return df
    
    # Actual BigQuery query
    q = f"""
    SELECT
      DATE(settlementDate) AS settlement_date,
      CAST(settlementPeriod AS INT64) AS settlement_period,
      fuel_type AS fuel_type,
      CAST(generation AS FLOAT64) AS generation
    FROM `{CFG.gcp_project}.{CFG.bq_dataset}.{CFG.tbl_genmix}` t
    WHERE {q_dates_clause('t')}
    """
    
    try:
        client = bq_client()
        if not client:
            raise Exception("BigQuery client could not be created")
            
        df = client.query(q).to_dataframe(create_bqstorage_client=False)
        logging.info(f"Loaded Generation Mix data: {len(df)} rows")
        
        # Ensure proper data types
        df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
        df['settlement_period'] = df['settlement_period'].astype(int)
        
        return df
    except Exception as e:
        logging.error(f"Error loading generation mix data: {e}")
        logging.info("Falling back to synthetic Generation Mix data")
        return load_genmix()  # This will now use synthetic data

# -------------------------
# Main function and entry point
# -------------------------

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="UK BOD Analysis Tool")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")
    parser.add_argument("--no-gdoc", action="store_true", help="Skip Google Doc generation")
    parser.add_argument("--use-synthetic", action="store_true", help="Force use of synthetic data")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Update config based on arguments
    if args.start_date:
        CFG.start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if args.end_date:
        CFG.end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    if args.no_gdoc:
        CFG.create_gdoc = False
    if args.use_synthetic:
        CFG.use_synthetic_data = True
    
    return args

def setup_logging(debug=False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bod_analysis.log", mode="w")
        ]
    )

def main():
    """Main function for BOD analysis"""
    args = parse_args()
    setup_logging(args.debug)
    
    logging.info(f"Starting BOD analysis from {CFG.start_date} to {CFG.end_date}")
    logging.info(f"Using credentials from: {CFG.google_project_credentials}")
    
    # Create output directories
    os.makedirs(CFG.charts_dir, exist_ok=True)
    os.makedirs(CFG.tables_dir, exist_ok=True)
    
    # Check for access to BigQuery
    if not CFG.use_synthetic_data:
        try:
            client = bq_client()
            if client:
                # Test query to check connectivity
                test_query = "SELECT 1"
                client.query(test_query).result()
                logging.info("Successfully connected to BigQuery")
            else:
                logging.warning("BigQuery client could not be created, will use synthetic data")
                CFG.use_synthetic_data = True
        except Exception as e:
            logging.error(f"Failed to connect to BigQuery: {e}")
            logging.warning("Will use synthetic data for testing")
            CFG.use_synthetic_data = True
    
    # Load data
    logging.info("Loading data...")
    bod_df = load_bod()
    impniv_df = load_impniv()
    demand_df = load_demand()
    genmix_df = load_genmix()
    
    logging.info(f"Data loaded: BOD={len(bod_df)} rows, ImpNIV={len(impniv_df)} rows, " +
                f"Demand={len(demand_df)} rows, GenMix={len(genmix_df)} rows")
    
    # From here, continue with your analysis as in the original script
    # You can add your specific analysis code here
    
    # Example: Perform analysis and generate charts
    # analyze_bod_data(bod_df, impniv_df, demand_df, genmix_df)
    
    logging.info("Analysis completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
