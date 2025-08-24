#!/usr/bin/env python
"""
Real Data BOD Adapter
A version of the simple_bod_adapter.py that works with real demand data instead of synthetic data
"""

import os
import sys
import json
import logging
import argparse
import datetime as dt
import pandas as pd
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("real_bod_adapter")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Real Data BOD Analysis Adapter")
    
    # Default date range
    default_end_date = dt.datetime.now().date().isoformat()
    default_start_date = (dt.datetime.now() - dt.timedelta(days=30)).date().isoformat()
    
    parser.add_argument("--start-date", type=str, default=default_start_date,
                        help=f"Start date (YYYY-MM-DD, default: {default_start_date})")
    parser.add_argument("--end-date", type=str, default=default_end_date,
                        help=f"End date (YYYY-MM-DD, default: {default_end_date})")
    parser.add_argument("--use-local-data", action="store_true",
                        help="Use local sample data instead of BigQuery")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress non-essential output")
    
    return parser.parse_args()

def date_serializer(obj):
    """Helper function to serialize date objects to JSON"""
    if isinstance(obj, (dt.date, dt.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def ensure_sample_data_exists():
    """Ensure sample data file exists"""
    sample_file = "sample_demand_data.json"
    
    if not os.path.exists(sample_file):
        logger.info("Creating sample demand data...")
        # Create sample demand data
        data = []
        start_date = dt.datetime(2025, 8, 1)
        for day in range(3):
            date = (start_date + dt.timedelta(days=day)).date()
            for period in range(1, 49):
                data.append({
                    'publishTime': (start_date + dt.timedelta(days=day, hours=period//2)).isoformat(),
                    'startTime': (start_date + dt.timedelta(days=day, hours=period//2)).isoformat(),
                    'settlementDate': date.isoformat(),
                    'settlementPeriod': period,
                    'initialDemandOutturn': round(np.random.normal(35000, 5000), 2),
                    'initialTransmissionSystemDemandOutturn': round(np.random.normal(30000, 4000), 2)
                })

        # Save to sample file
        with open(sample_file, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Created sample file with {len(data)} records")
    
    return sample_file

def run_demand_analysis(start_date, end_date, use_local_data=False, debug=False):
    """Run an analysis using real demand data"""
    logger.info(f"Running demand data analysis from {start_date} to {end_date}")
    
    try:
        if use_local_data:
            # Use local sample data
            sample_file = ensure_sample_data_exists()
            logger.info(f"Using local sample data from {sample_file}")
            
            # Load sample data
            with open(sample_file, "r") as f:
                data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
        else:
            # Try to use BigQuery
            from google.cloud import bigquery
            
            logger.info("Connecting to BigQuery...")
            client = bigquery.Client()
            
            # Query for demand data
            query = f"""
            SELECT 
                settlementDate,
                settlementPeriod,
                initialDemandOutturn,
                initialTransmissionSystemDemandOutturn
            FROM 
                `jibber-jabber-knowledge.uk_energy_prod.elexon_demand_outturn`
            WHERE 
                settlementDate BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY
                settlementDate, settlementPeriod
            LIMIT 1000
            """
            
            logger.info("Executing BigQuery query...")
            query_job = client.query(query)
            
            # Convert to pandas for easier analysis
            df = query_job.to_dataframe()
            
            if df.empty:
                logger.warning("No data found in BigQuery for the specified date range")
                logger.info("Falling back to local sample data...")
                return run_demand_analysis(start_date, end_date, use_local_data=True, debug=debug)
        
        # Filter to the requested date range
        if isinstance(start_date, str):
            start_date_dt = dt.datetime.fromisoformat(start_date).date()
        else:
            start_date_dt = start_date
        
        if isinstance(end_date, str):
            end_date_dt = dt.datetime.fromisoformat(end_date).date()
        else:
            end_date_dt = end_date
        
        # Convert settlement dates to datetime for filtering
        if not pd.api.types.is_datetime64_dtype(df['settlementDate']):
            df['settlementDate'] = pd.to_datetime(df['settlementDate']).dt.date
        
        # Filter to requested date range
        df = df[(df['settlementDate'] >= start_date_dt) & (df['settlementDate'] <= end_date_dt)]
        
        if df.empty:
            logger.warning("No data found for the specified date range after filtering")
            return False
        
        # Calculate statistics
        total_demand = df['initialDemandOutturn'].sum()
        avg_demand = df['initialDemandOutturn'].mean()
        min_demand = df['initialDemandOutturn'].min()
        max_demand = df['initialDemandOutturn'].max()
        
        # Save results
        output_file = "energy_analysis_results.json"
        results = {
            "query_period": {
                "start_date": start_date_dt,
                "end_date": end_date_dt
            },
            "record_count": len(df),
            "date_range": f"{min(df['settlementDate'])} to {max(df['settlementDate'])}",
            "settlement_periods": df['settlementPeriod'].nunique(),
            "total_demand": float(total_demand),
            "average_demand": float(avg_demand),
            "min_demand": float(min_demand),
            "max_demand": float(max_demand),
            "available_columns": df.columns.tolist(),
            "data_preview": df.head(10).to_dict(orient='records')
        }
        
        # Print summary
        data_type = "Local Sample Data" if use_local_data else "Real Data"
        print(f"\n===== Energy Analysis Summary ({data_type}) =====")
        print(f"Period: {start_date} to {end_date}")
        print(f"Records found: {len(df)}")
        print(f"Settlement dates: {min(df['settlementDate'])} to {max(df['settlementDate'])}")
        print(f"Settlement periods: {df['settlementPeriod'].nunique()}")
        print(f"Total demand: {total_demand:.2f} MWh")
        print(f"Average demand: {avg_demand:.2f} MWh")
        print(f"Min demand: {min_demand:.2f} MWh")
        print(f"Max demand: {max_demand:.2f} MWh")
        print(f"Full results saved to: {output_file}")
        
        # Save with custom JSON serializer for dates
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=date_serializer)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in energy analysis: {e}", exc_info=debug)
        
        if not use_local_data:
            # Fall back to local data
            logger.info("Falling back to local sample data due to error...")
            return run_demand_analysis(start_date, end_date, use_local_data=True, debug=debug)
        else:
            # Already using local data, so just report the error
            return False
        
        # Filter to the requested date range
        if isinstance(start_date, str):
            start_date_dt = dt.datetime.fromisoformat(start_date).date()
        else:
            start_date_dt = start_date
        
        if isinstance(end_date, str):
            end_date_dt = dt.datetime.fromisoformat(end_date).date()
        else:
            end_date_dt = end_date
        
        # Convert settlement dates to datetime for filtering
        if not pd.api.types.is_datetime64_dtype(df['settlementDate']):
            df['settlementDate'] = pd.to_datetime(df['settlementDate']).dt.date
        
        # Filter to requested date range
        df = df[(df['settlementDate'] >= start_date_dt) & (df['settlementDate'] <= end_date_dt)]
        
        if df.empty:
            logger.warning("No data found for the specified date range after filtering")
            return False
        
        # Calculate statistics
        total_demand = df['initialDemandOutturn'].sum()
        avg_demand = df['initialDemandOutturn'].mean()
        min_demand = df['initialDemandOutturn'].min()
        max_demand = df['initialDemandOutturn'].max()
        
        # Save results
        output_file = "energy_analysis_results.json"
        results = {
            "query_period": {
                "start_date": start_date_dt.isoformat(),
                "end_date": end_date_dt.isoformat()
            },
            "record_count": len(df),
            "date_range": f"{df['settlementDate'].min()} to {df['settlementDate'].max()}",
            "settlement_periods": df['settlementPeriod'].nunique(),
            "total_demand": float(total_demand),
            "average_demand": float(avg_demand),
            "min_demand": float(min_demand),
            "max_demand": float(max_demand),
            "available_columns": df.columns.tolist(),
            "data_preview": df.head(10).to_dict(orient='records')
        }
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        # Print summary
        data_type = "Local Sample Data" if use_local_data else "Real Data"
        print(f"
===== Energy Analysis Summary ({data_type}) =====")
        print(f"Period: {start_date} to {end_date}")
        print(f"Records found: {len(df)}")
        print(f"Settlement dates: {min(df['settlementDate'])} to {max(df['settlementDate'])}")
        print(f"Settlement periods: {df['settlementPeriod'].nunique()}")
        print(f"Total demand: {total_demand:.2f} MWh")
        print(f"Average demand: {avg_demand:.2f} MWh")
        print(f"Min demand: {min_demand:.2f} MWh")
        print(f"Max demand: {max_demand:.2f} MWh")
        print(f"Full results saved to: {output_file}")
        
        # Convert dates to strings for JSON serialization
        results["query_period"]["start_date"] = results["query_period"]["start_date"]
        results["query_period"]["end_date"] = results["query_period"]["end_date"]
        results["date_range"] = f"{df['settlementDate'].min().isoformat() if hasattr(df['settlementDate'].min(), 'isoformat') else str(df['settlementDate'].min())} to {df['settlementDate'].max().isoformat() if hasattr(df['settlementDate'].max(), 'isoformat') else str(df['settlementDate'].max())}"
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in energy analysis: {e}", exc_info=debug)
        
        if not use_local_data:
            # Fall back to local data
            logger.info("Falling back to local sample data due to error...")
            return run_demand_analysis(start_date, end_date, use_local_data=True, debug=debug)
        else:
            # Already using local data, so just report the error
            return False

def main():
    """Main entry point."""
    args = parse_args()
    
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    if args.quiet:
        logger.setLevel(logging.WARNING)
    
    # Run analysis
    success = run_demand_analysis(
        start_date=args.start_date,
        end_date=args.end_date,
        use_local_data=args.use_local_data,
        debug=args.debug
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    # Check for required packages
    try:
        import pandas
        import numpy
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "numpy", "google-cloud-bigquery"])
    
    sys.exit(main())
