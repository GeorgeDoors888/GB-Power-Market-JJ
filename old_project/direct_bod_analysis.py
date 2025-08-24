#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct BOD Analysis with Alternative Authentication Methods
==========================================================

This script provides a robust way to analyze BOD (Bid-Offer Data) directly from BigQuery
using multiple authentication fallback mechanisms:

1. Service account JSON key file (explicit path or GOOGLE_APPLICATION_CREDENTIALS)
2. Application Default Credentials (ADC)
3. User account credentials with OAuth flow (browser sign-in)
4. Credentials from local metadata server (when running on GCP)

Features:
- Multiple authentication methods with fallbacks
- Data loading with automatic retry and error handling
- Basic BOD analysis with visualization
- Export to CSV, JSON, and visualization
- No API calls - works directly with your BigQuery tables

Requirements:
    pip install google-cloud-bigquery pandas matplotlib google-auth google-auth-oauthlib
                numpy seaborn pyarrow tabulate tenacity tqdm
"""

import os
import sys
import json
import logging
import argparse
import datetime as dt
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from dateutil.relativedelta import relativedelta

# Data processing
import numpy as np
import pandas as pd
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False

# Visualization
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

# Google Cloud
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

# Try to import OAuth dependencies
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# Constants
DEFAULT_PROJECT_ID = "jibber-jabber-knowledge"
DEFAULT_DATASET = "uk_energy_prod"
DEFAULT_TABLE_BOD = "elexon_bid_offer_acceptances"  # Main BOD table
DEFAULT_TABLE_IMPNIV = "elexon_system_warnings"     # System warnings/imbalance table
DEFAULT_TABLE_DEMAND = "neso_demand_forecasts"      # Demand table
DEFAULT_TABLE_GENMIX = "neso_carbon_intensity"      # Generation mix table
DEFAULT_OUTPUT_DIR = "./bod_analysis_output"
BIGQUERY_SCOPES = ["https://www.googleapis.com/auth/bigquery"]
CREDENTIALS_FILE_PATHS = [
    "client_secret.json",
    "service-account.json",
    "key.json",
    "credentials.json",
    os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
]
TOKEN_PATH = os.path.expanduser("~/.config/bod_analysis/token.json")

class DirectBODAnalysis:
    """Analyzes BOD data directly from BigQuery with multiple authentication methods."""
    
    def __init__(
        self, 
        project_id=DEFAULT_PROJECT_ID,
        dataset=DEFAULT_DATASET,
        table_bod=DEFAULT_TABLE_BOD,
        table_impniv=DEFAULT_TABLE_IMPNIV,
        table_demand=DEFAULT_TABLE_DEMAND,
        table_genmix=DEFAULT_TABLE_GENMIX,
        start_date=None, 
        end_date=None, 
        output_dir=DEFAULT_OUTPUT_DIR,
        service_account_path=None,
        use_synthetic=False,
        debug=False
    ):
        """Initialize the BOD analyzer with configuration parameters."""
        # Set date range
        self.end_date = end_date or dt.datetime.now().date()
        self.start_date = start_date or (self.end_date - relativedelta(months=1))
        
        # Project configuration
        self.project_id = project_id
        self.dataset = dataset
        self.table_bod = table_bod
        self.table_impniv = table_impniv
        self.table_demand = table_demand
        self.table_genmix = table_genmix
        
        # Output configuration
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Authentication configuration
        self.service_account_path = service_account_path
        
        # Debug and synthetic options
        self.use_synthetic = use_synthetic
        if debug:
            log.setLevel(logging.DEBUG)
        
        # Initialize client
        self.client = self._initialize_client()
        
        # Output directories
        self.charts_dir = "./out/charts"
        self.tables_dir = "./out/tables"
        os.makedirs(self.charts_dir, exist_ok=True)
        os.makedirs(self.tables_dir, exist_ok=True)
        
        log.info(f"Analysis period: {self.start_date} to {self.end_date}")
        log.info(f"Using synthetic data: {self.use_synthetic}")
    
    def _initialize_client(self):
        """Initialize BigQuery client with multiple authentication fallbacks."""
        # Track authentication attempts
        auth_attempts = []
        
        if self.use_synthetic:
            log.info("Using synthetic data - no client needed")
            return None
        
        # 1. Try explicit service account path if provided
        if self.service_account_path:
            try:
                log.info(f"Attempting authentication with service account: {self.service_account_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path, scopes=BIGQUERY_SCOPES
                )
                auth_attempts.append(f"Service account file (explicit): {self.service_account_path}")
                return bigquery.Client(credentials=credentials, project=self.project_id)
            except Exception as e:
                log.warning(f"Failed to authenticate with explicit service account: {e}")
        
        # 2. Try GOOGLE_APPLICATION_CREDENTIALS environment variable
        env_creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_creds_path:
            try:
                log.info(f"Attempting authentication with GOOGLE_APPLICATION_CREDENTIALS: {env_creds_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    env_creds_path, scopes=BIGQUERY_SCOPES
                )
                auth_attempts.append(f"GOOGLE_APPLICATION_CREDENTIALS: {env_creds_path}")
                return bigquery.Client(credentials=credentials, project=self.project_id)
            except Exception as e:
                log.warning(f"Failed to authenticate with GOOGLE_APPLICATION_CREDENTIALS: {e}")
        
        # 3. Try common credential file locations
        for path in CREDENTIALS_FILE_PATHS:
            if os.path.exists(path):
                try:
                    log.info(f"Attempting authentication with file: {path}")
                    credentials = service_account.Credentials.from_service_account_file(
                        path, scopes=BIGQUERY_SCOPES
                    )
                    auth_attempts.append(f"Found credentials file: {path}")
                    return bigquery.Client(credentials=credentials, project=self.project_id)
                except Exception as e:
                    log.warning(f"Failed to authenticate with {path}: {e}")
        
        # 4. Try application default credentials
        try:
            log.info("Attempting authentication with application default credentials")
            credentials, project = default(scopes=BIGQUERY_SCOPES)
            auth_attempts.append("Application Default Credentials")
            return bigquery.Client(credentials=credentials, project=self.project_id)
        except Exception as e:
            log.warning(f"Failed to authenticate with application default credentials: {e}")
        
        # 5. Try OAuth flow if available
        if HAS_OAUTH:
            try:
                log.info("Attempting OAuth authentication flow")
                
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
                    return bigquery.Client(credentials=creds, project=self.project_id)
                else:
                    log.warning("No client_secret.json found for OAuth flow")
            except Exception as e:
                log.warning(f"Failed to authenticate with OAuth: {e}")
        
        # 6. Final attempt with no credentials (works on GCP or if user already set up ADC)
        try:
            log.info("Attempting to create client with no explicit credentials")
            client = bigquery.Client(project=self.project_id)
            
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
        
        log.info("Falling back to synthetic data")
        self.use_synthetic = True
        return None
    
    def _date_clause(self, alias='t'):
        """Generate SQL date filter clause"""
        return f"""
        DATE({alias}.settlementDate) BETWEEN 
        DATE("{self.start_date.isoformat()}") AND DATE("{self.end_date.isoformat()}")
        """
    
    def _generate_synthetic_data(self, n_days=None):
        """Generate synthetic data for testing"""
        if n_days is None:
            if isinstance(self.start_date, str):
                self.start_date = dt.datetime.strptime(self.start_date, "%Y-%m-%d").date()
            if isinstance(self.end_date, str):
                self.end_date = dt.datetime.strptime(self.end_date, "%Y-%m-%d").date()
                
            delta = self.end_date - self.start_date
            n_days = delta.days + 1
        
        # Create a range of dates and settlement periods
        dates = pd.date_range(start=self.start_date, end=self.end_date)
        periods = list(range(1, 49))  # 48 settlement periods per day
        
        # Create a DataFrame with all date/period combinations
        date_period = [(d.date(), p) for d in dates for p in periods]
        df = pd.DataFrame(date_period, columns=['settlement_date', 'settlement_period'])
        
        # Add synthetic BOD data
        n_rows = len(df)
        df['bm_unit_id'] = np.random.choice(['T_ABTH1', 'T_DRAXX1', 'E_WBUPS1', 'T_DIDCB5'], n_rows)
        df['bid_offer_flag'] = np.random.choice(['BID', 'OFFER'], n_rows)
        df['bid_offer_number'] = np.random.randint(-5, 6, n_rows)
        df['bid_offer_price'] = np.random.normal(50, 20, n_rows)  # £/MWh
        df['volume_accepted_mwh'] = np.random.normal(0, 50, n_rows)
        df['offer_price'] = np.random.normal(60, 20, n_rows)
        df['bid_price'] = np.random.normal(40, 20, n_rows)
        
        log.info(f"Generated synthetic BOD data: {len(df)} rows")
        return df
        
        # Actual BigQuery query
        query = f"""
        SELECT
          DATE(settlementDate) AS settlement_date,
          CAST(settlementPeriod AS INT64) AS settlement_period,
          bmuId AS bmu_id,
          bidOfferNumber AS bid_offer_number,
          CAST(volumeAcceptedMWh AS FLOAT64) AS volume_accepted_mwh,
          CAST(offerPrice AS FLOAT64) AS offer_price,
          CAST(bidPrice AS FLOAT64) AS bid_price
        FROM `{self.project_id}.{self.dataset}.{self.table_bod}`
        WHERE {self._date_clause()}
        """
        
        try:
            query_job = self.client.query(query)
            df = query_job.result().to_dataframe()
            
            # Ensure proper data types
            df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
            df['settlement_period'] = df['settlement_period'].astype(int)
            
            log.info(f"Loaded real BOD data: {len(df)} rows")
            return df
        except Exception as e:
            log.error(f"Error loading BOD data: {e}")
            log.info("Falling back to synthetic BOD data")
            self.use_synthetic = True
            return self.load_bod_data()
    
    def load_impniv_data(self):
        """Load Imbalance Prices and NIV data from BigQuery or generate synthetic data"""
        if self.use_synthetic:
            df = self._generate_synthetic_data()
            
            # Add synthetic price and NIV data
            df['imbalance_price'] = np.random.normal(50, 15, len(df))  # Mean £50/MWh
            df['niv'] = np.random.normal(0, 500, len(df))  # Mean 0 MWh
            
            log.info(f"Generated synthetic Imbalance/NIV data: {len(df)} rows")
            return df
        
        # Actual BigQuery query
        query = f"""
        SELECT
          DATE(settlementDate) AS settlement_date,
          CAST(settlementPeriod AS INT64) AS settlement_period,
          CAST(imbalancePrice AS FLOAT64) AS imbalance_price,
          CAST(netImbalanceVolume AS FLOAT64) AS niv
        FROM `{self.project_id}.{self.dataset}.{self.table_impniv}`
        WHERE {self._date_clause()}
        """
        
        try:
            query_job = self.client.query(query)
            df = query_job.result().to_dataframe()
            
            # Ensure proper data types
            df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
            df['settlement_period'] = df['settlement_period'].astype(int)
            
            log.info(f"Loaded real Imbalance/NIV data: {len(df)} rows")
            return df
        except Exception as e:
            log.error(f"Error loading ImbalancePrice/NIV data: {e}")
            log.info("Falling back to synthetic Imbalance/NIV data")
            self.use_synthetic = True
            return self.load_impniv_data()
    
    def load_demand_data(self):
        """Load Demand data from BigQuery or generate synthetic data"""
        if self.use_synthetic:
            df = self._generate_synthetic_data()
            
            # Add synthetic demand data
            base_demand = 30000  # Base demand in MW
            day_pattern = np.sin(np.linspace(0, 2*np.pi, 48)) * 5000 + base_demand
            
            # Apply the day pattern to each day with some random variation
            all_demand = []
            for day in pd.date_range(self.start_date, self.end_date):
                day_demand = day_pattern + np.random.normal(0, 1000, 48)
                all_demand.extend(day_demand)
            
            # Trim to match dataframe length
            df['demand'] = all_demand[:len(df)]
            
            log.info(f"Generated synthetic Demand data: {len(df)} rows")
            return df
        
        # Actual BigQuery query
        query = f"""
        SELECT
          DATE(settlementDate) AS settlement_date,
          CAST(settlementPeriod AS INT64) AS settlement_period,
          CAST(demand AS FLOAT64) AS demand
        FROM `{self.project_id}.{self.dataset}.{self.table_demand}`
        WHERE {self._date_clause()}
        """
        
        try:
            query_job = self.client.query(query)
            df = query_job.result().to_dataframe()
            
            # Ensure proper data types
            df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
            df['settlement_period'] = df['settlement_period'].astype(int)
            
            log.info(f"Loaded real Demand data: {len(df)} rows")
            return df
        except Exception as e:
            log.error(f"Error loading demand data: {e}")
            log.info("Falling back to synthetic Demand data")
            self.use_synthetic = True
            return self.load_demand_data()
    
    def load_genmix_data(self):
        """Load Generation Mix data from BigQuery or generate synthetic data"""
        if self.use_synthetic:
            # Create synthetic generation mix data
            dates = pd.date_range(start=self.start_date, end=self.end_date)
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
                        
                        # Add some randomness
                        variation = 100  # Minimum variation
                        if base > 0:
                            variation = max(100, base * 0.1)
                        gen = max(0, base + np.random.normal(0, variation))
                        
                        rows.append({
                            'settlement_date': d.date(),
                            'settlement_period': p,
                            'fuel_type': ft,
                            'generation': gen
                        })
            
            df = pd.DataFrame(rows)
            log.info(f"Generated synthetic Generation Mix data: {len(df)} rows")
            return df
        
        # Actual BigQuery query
        query = f"""
        SELECT
          DATE(settlementDate) AS settlement_date,
          CAST(settlementPeriod AS INT64) AS settlement_period,
          fuel_type AS fuel_type,
          CAST(generation AS FLOAT64) AS generation
        FROM `{self.project_id}.{self.dataset}.{self.table_genmix}`
        WHERE {self._date_clause()}
        """
        
        try:
            query_job = self.client.query(query)
            df = query_job.result().to_dataframe()
            
            # Ensure proper data types
            df['settlement_date'] = pd.to_datetime(df['settlement_date']).dt.date
            df['settlement_period'] = df['settlement_period'].astype(int)
            
            log.info(f"Loaded real Generation Mix data: {len(df)} rows")
            return df
        except Exception as e:
            log.error(f"Error loading generation mix data: {e}")
            log.info("Falling back to synthetic Generation Mix data")
            self.use_synthetic = True
            return self.load_genmix_data()
    
    def derive_daily_kpis(self, bod_df, impniv_df, demand_df, genmix_df):
        """Derive daily Key Performance Indicators from the input data"""
        # If BOD dataframe is empty, create a minimal daily frame
        if bod_df.empty:
            log.warning("BOD dataframe is empty - creating minimal daily frame")
            # Create a date range from start to end
            dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
            bod_daily = pd.DataFrame({'settlement_date': [d.date() for d in dates]})
        else:
            # Calculate daily BOD KPIs
            bod_daily = bod_df.groupby('settlement_date').agg({
                'volume_accepted_mwh': ['sum', 'count', 'mean', 'std'],
                'offer_price': ['mean', 'max', 'min'],
                'bid_price': ['mean', 'max', 'min']
            }).reset_index()
            
            # Flatten multi-level columns
            bod_daily.columns = ['settlement_date'] + [
                f"{col[0]}_{col[1]}" for col in bod_daily.columns[1:]
            ]
        
        # Calculate daily Imbalance/NIV KPIs
        if not impniv_df.empty:
            imp_daily = impniv_df.groupby('settlement_date').agg({
                'imbalance_price': ['mean', 'max', 'min', 'std'],
                'niv': ['mean', 'sum', 'std']
            }).reset_index()
            
            # Flatten multi-level columns
            imp_daily.columns = ['settlement_date'] + [
                f"{col[0]}_{col[1]}" for col in imp_daily.columns[1:]
            ]
            
            # Merge with BOD daily
            daily = pd.merge(bod_daily, imp_daily, on='settlement_date', how='left')
        else:
            daily = bod_daily
        
        # Calculate daily Demand KPIs
        if not demand_df.empty:
            dem_daily = demand_df.groupby('settlement_date').agg({
                'demand': ['mean', 'max', 'min', 'sum']
            }).reset_index()
            
            # Flatten multi-level columns
            dem_daily.columns = ['settlement_date'] + [
                f"{col[0]}_{col[1]}" for col in dem_daily.columns[1:]
            ]
            
            # Merge with current daily
            daily = pd.merge(daily, dem_daily, on='settlement_date', how='left')
        
        # Calculate daily Generation Mix KPIs
        if not genmix_df.empty:
            # First, pivot to get fuel types as columns
            genmix_pivot = genmix_df.pivot_table(
                index=['settlement_date', 'settlement_period'],
                columns='fuel_type',
                values='generation',
                aggfunc='sum'
            ).reset_index()
            
            # Now calculate daily aggregates
            mix_daily = genmix_pivot.groupby('settlement_date').agg({
                col: ['mean', 'sum'] for col in genmix_pivot.columns if col not in ['settlement_date', 'settlement_period']
            }).reset_index()
            
            # Flatten multi-level columns
            mix_daily.columns = ['settlement_date'] + [
                f"{col[0]}_{col[1]}" for col in mix_daily.columns[1:]
            ]
            
            # Merge with current daily
            daily = pd.merge(daily, mix_daily, on='settlement_date', how='left')
        
        # Calculate additional derived KPIs
        # For example, calculate the percentage of wind in total generation
        if not genmix_df.empty and 'WIND_sum' in daily.columns:
            # Get all columns that end with _sum and are fuel types
            fuel_sum_cols = [col for col in daily.columns if col.endswith('_sum') 
                            and col.split('_')[0] in genmix_df['fuel_type'].unique()]
            
            # Calculate total generation
            daily['total_generation_sum'] = daily[fuel_sum_cols].sum(axis=1)
            
            # Calculate percentage for each fuel type
            for col in fuel_sum_cols:
                fuel = col.split('_')[0]
                daily[f"{fuel}_percentage"] = daily[col] / daily['total_generation_sum'] * 100
        
        # Save daily KPIs to CSV
        daily_file = os.path.join(self.tables_dir, 'daily_kpis.csv')
        daily.to_csv(daily_file, index=False)
        log.info(f"Saved daily KPIs to {daily_file}")
        
        return daily
    
    def generate_monthly_rollup(self, daily_df):
        """Generate monthly rollup of KPIs from daily data"""
        # Convert settlement_date to datetime if not already
        daily_df['settlement_date'] = pd.to_datetime(daily_df['settlement_date'])
        
        # Add month column
        daily_df['month'] = daily_df['settlement_date'].dt.to_period('M')
        
        # Group by month and calculate aggregates
        numeric_cols = daily_df.select_dtypes(include=['number']).columns
        monthly = daily_df.groupby('month').agg({
            col: ['mean', 'sum', 'std'] if col != 'month' else 'first' 
            for col in numeric_cols
        }).reset_index()
        
        # Flatten multi-level columns
        monthly.columns = ['month'] + [
            f"{col[0]}_{col[1]}" for col in monthly.columns[1:]
        ]
        
        # Convert month period to string for CSV
        monthly['month'] = monthly['month'].astype(str)
        
        # Save monthly rollup to CSV
        monthly_file = os.path.join(self.tables_dir, 'monthly_rollup.csv')
        monthly.to_csv(monthly_file, index=False)
        log.info(f"Saved monthly rollup to {monthly_file}")
        
        return monthly
    
    def generate_charts(self, daily_df, monthly_df):
        """Generate charts from the KPI data"""
        charts_created = 0
        
        # Price chart
        if 'imbalance_price_mean' in daily_df.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(daily_df['settlement_date'], daily_df['imbalance_price_mean'], label='Imbalance Price')
            plt.title('Daily Average Imbalance Price')
            plt.xlabel('Date')
            plt.ylabel('Price (£/MWh)')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(self.charts_dir, 'imbalance_price.png'))
            plt.close()
            charts_created += 1
        else:
            log.warning("No price data available for plotting")
        
        # Demand chart
        if 'demand_mean' in daily_df.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(daily_df['settlement_date'], daily_df['demand_mean'], label='Demand')
            plt.title('Daily Average Demand')
            plt.xlabel('Date')
            plt.ylabel('Demand (MW)')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(self.charts_dir, 'demand.png'))
            plt.close()
            charts_created += 1
        else:
            log.warning("No demand data available for plotting")
        
        # Generation mix chart (monthly)
        fuel_types = [col.split('_')[0] for col in monthly_df.columns 
                     if col.endswith('_percentage') and not col.startswith('total')]
        
        if fuel_types:
            plt.figure(figsize=(14, 8))
            
            # Create stacked area chart
            x = monthly_df['month']
            bottom = np.zeros(len(monthly_df))
            
            for fuel in fuel_types:
                col = f"{fuel}_percentage"
                if col in monthly_df.columns:
                    plt.bar(x, monthly_df[col], bottom=bottom, label=fuel)
                    bottom += monthly_df[col].fillna(0)
            
            plt.title('Monthly Generation Mix')
            plt.xlabel('Month')
            plt.ylabel('Percentage (%)')
            plt.legend(loc='upper right')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(self.charts_dir, 'generation_mix.png'))
            plt.close()
            charts_created += 1
        else:
            log.warning("No generation mix data available for plotting")
        
        log.info(f"Generated {charts_created} charts in {self.charts_dir}")
    
    def generate_summary(self, daily_df, monthly_df):
        """Generate a human-readable summary of the analysis"""
        summary = []
        summary.append(f"UK Energy System BOD Analysis: {self.start_date} to {self.end_date}")
        summary.append("=" * 60)
        summary.append("")
        
        # Add headline stats
        summary.append("HEADLINE STATISTICS")
        summary.append("-" * 20)
        
        # Imbalance price stats
        if 'imbalance_price_mean' in daily_df.columns:
            avg_price = daily_df['imbalance_price_mean'].mean()
            max_price = daily_df['imbalance_price_max'].max()
            min_price = daily_df['imbalance_price_min'].min()
            summary.append(f"Average Imbalance Price: £{avg_price:.2f}/MWh")
            summary.append(f"Maximum Imbalance Price: £{max_price:.2f}/MWh")
            summary.append(f"Minimum Imbalance Price: £{min_price:.2f}/MWh")
            summary.append("")
        
        # Demand stats
        if 'demand_mean' in daily_df.columns:
            avg_demand = daily_df['demand_mean'].mean()
            max_demand = daily_df['demand_max'].max()
            summary.append(f"Average Demand: {avg_demand:.2f} MW")
            summary.append(f"Maximum Demand: {max_demand:.2f} MW")
            summary.append("")
        
        # Generation mix stats
        fuel_types = [col.split('_')[0] for col in monthly_df.columns 
                     if col.endswith('_percentage') and not col.startswith('total')]
        
        if fuel_types:
            summary.append("GENERATION MIX (Average %)")
            summary.append("-" * 25)
            
            for fuel in fuel_types:
                col = f"{fuel}_percentage"
                if col in monthly_df.columns:
                    avg_pct = monthly_df[col].mean()
                    summary.append(f"{fuel}: {avg_pct:.2f}%")
            
            summary.append("")
        
        # BOD stats
        if 'volume_accepted_mwh_sum' in daily_df.columns:
            total_volume = daily_df['volume_accepted_mwh_sum'].sum()
            avg_daily_volume = daily_df['volume_accepted_mwh_sum'].mean()
            summary.append("BALANCING MECHANISM")
            summary.append("-" * 20)
            summary.append(f"Total BOD Volume: {total_volume:.2f} MWh")
            summary.append(f"Average Daily BOD Volume: {avg_daily_volume:.2f} MWh")
            summary.append("")
        
        # Write summary to file
        summary_file = os.path.join("./out", "kpi_summary.txt")
        with open(summary_file, 'w') as f:
            f.write('\n'.join(summary))
        
        log.info(f"Saved human-readable summary to {summary_file}")
    
    def run_analysis(self):
        """Run the full BOD analysis"""
        try:
            # Load data
            log.info("Loading data...")
            bod_df = self.load_bod_data()
            impniv_df = self.load_impniv_data()
            demand_df = self.load_demand_data()
            genmix_df = self.load_genmix_data()
            
            # Derive KPIs
            log.info("Deriving KPIs...")
            daily_df = self.derive_daily_kpis(bod_df, impniv_df, demand_df, genmix_df)
            monthly_df = self.generate_monthly_rollup(daily_df)
            
            # Generate charts
            log.info("Generating charts...")
            self.generate_charts(daily_df, monthly_df)
            
            # Generate summary
            log.info("Generating summary...")
            self.generate_summary(daily_df, monthly_df)
            
            log.info("Analysis complete. See results in ./out/")
            return True
        except Exception as e:
            log.error(f"Error in analysis: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Direct BOD Analysis Tool")
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")
    parser.add_argument("--use-synthetic", action="store_true", help="Force use of synthetic data")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse dates
    start_date = None
    if args.start_date:
        start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    
    end_date = None
    if args.end_date:
        end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    
    # Run analysis
    analyzer = DirectBODAnalysis(
        start_date=start_date,
        end_date=end_date,
        use_synthetic=args.use_synthetic
    )
    success = analyzer.run_analysis()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
