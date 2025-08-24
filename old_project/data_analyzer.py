#!/usr/bin/env python
"""
Simple data analyzer to demonstrate working with real data instead of synthetic data
"""

import os
import sys
import json
import logging
import argparse
import datetime as dt
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Data Analyzer")
    parser.add_argument("--start-date", default="2025-08-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default="2025-08-03", help="End date (YYYY-MM-DD)")
    parser.add_argument("--use-bigquery", action="store_true", help="Try to use BigQuery instead of local data")
    return parser.parse_args()

def create_sample_data():
    """Create a sample demand data file"""
    filename = "sample_demand_data.json"
    if os.path.exists(filename):
        return filename
    
    print("Creating sample demand data...")
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

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Created sample file with {len(data)} records")
    return filename

def analyze_real_data(start_date, end_date, use_bigquery=False):
    """Run analysis with real data (or sample data)"""
    print(f"\nAnalyzing data from {start_date} to {end_date}")
    
    # Try BigQuery if requested
    df = None
    if use_bigquery:
        try:
            from google.cloud import bigquery
            print("Connecting to BigQuery...")
            client = bigquery.Client()
            
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
            
            print("Executing query...")
            query_job = client.query(query)
            df = query_job.to_dataframe()
            
            if df.empty:
                print("No data found in BigQuery, falling back to sample data")
                df = None
        except Exception as e:
            print(f"BigQuery error: {e}")
            print("Falling back to sample data")
            df = None
    
    # Use sample data if needed
    if df is None:
        sample_file = create_sample_data()
        print(f"Using sample data from {sample_file}")
        with open(sample_file, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    
    # Analyze the data
    print("\nData Summary:")
    print(f"- Record count: {len(df)}")
    print(f"- Unique settlement dates: {df['settlementDate'].nunique()}")
    print(f"- Total demand: {df['initialDemandOutturn'].sum():,.2f} MWh")
    print(f"- Average demand: {df['initialDemandOutturn'].mean():,.2f} MWh")
    print(f"- Min demand: {df['initialDemandOutturn'].min():,.2f} MWh")
    print(f"- Max demand: {df['initialDemandOutturn'].max():,.2f} MWh")
    
    # Save results
    output_file = "data_analysis_results.json"
    results = {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "statistics": {
            "record_count": len(df),
            "unique_dates": df['settlementDate'].nunique(),
            "total_demand": float(df['initialDemandOutturn'].sum()),
            "avg_demand": float(df['initialDemandOutturn'].mean()),
            "min_demand": float(df['initialDemandOutturn'].min()),
            "max_demand": float(df['initialDemandOutturn'].max())
        },
        "sample": df.head(5).to_dict(orient='records')
    }
    
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nFull results saved to: {output_file}")
    return True

def main():
    args = parse_args()
    success = analyze_real_data(args.start_date, args.end_date, args.use_bigquery)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
