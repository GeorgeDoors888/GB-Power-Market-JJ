#!/usr/bin/env python3
"""
FR Clearing Prices - Sample Data Generator
===========================================
Generates realistic EFA block-level FR clearing prices with:
- Time-of-day patterns (higher prices during peak demand)
- Day-of-week patterns (weekday vs weekend)
- Seasonal patterns (higher summer/spring for DC)
- Service-specific pricing (DR > DM > DC typical)
- Realistic volatility

Based on NESO August 2025 data:
- DC: £2.82/MW/h average (range £1-5)
- DM: £4.00/MW/h average (range £2-6)
- DR: £4.45/MW/h average (range £2-7)

Author: George Major
Date: 1 December 2025
"""

import os
import datetime as dt
import numpy as np
import pandas as pd
from google.cloud import bigquery


class FRPriceGenerator:
    """Generate realistic FR clearing prices with time/seasonal patterns"""
    
    # Base prices from NESO August 2025
    BASE_PRICES = {
        'DC': 2.82,
        'DM': 4.00,
        'DR': 4.45,
    }
    
    # Volatility factors (standard deviation as % of base)
    VOLATILITY = {
        'DC': 0.30,  # ±30%
        'DM': 0.25,  # ±25%
        'DR': 0.28,  # ±28%
    }
    
    # Time of day multipliers (6 EFA blocks per day)
    # Higher prices during morning/evening peaks
    TIME_MULTIPLIERS = {
        1: 0.90,  # 00:00-04:00 (night)
        2: 1.05,  # 04:00-08:00 (morning ramp)
        3: 1.15,  # 08:00-12:00 (morning peak)
        4: 1.20,  # 12:00-16:00 (afternoon peak)
        5: 1.30,  # 16:00-20:00 (evening peak - highest)
        6: 1.00,  # 20:00-00:00 (evening decline)
    }
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility"""
        np.random.seed(seed)
    
    def generate_price(
        self,
        service: str,
        efa_block: int,
        date: dt.date,
    ) -> float:
        """
        Generate realistic clearing price for given service, block, and date
        
        Factors:
        - Base price for service
        - Time of day (EFA block)
        - Day of week (lower weekends)
        - Random volatility
        - Seasonal (higher summer for DC)
        """
        base = self.BASE_PRICES[service]
        volatility = self.VOLATILITY[service]
        
        # Time of day multiplier
        tod_mult = self.TIME_MULTIPLIERS[efa_block]
        
        # Day of week multiplier (lower on weekends)
        dow = date.weekday()  # 0=Monday, 6=Sunday
        dow_mult = 0.85 if dow >= 5 else 1.0
        
        # Seasonal multiplier (DC higher in summer)
        month = date.month
        if service == 'DC':
            # Higher Apr-Sep (spring/summer - less inertia)
            seasonal_mult = 1.15 if 4 <= month <= 9 else 0.90
        else:
            seasonal_mult = 1.0
        
        # Random volatility (normal distribution)
        random_mult = 1.0 + np.random.normal(0, volatility)
        
        # Calculate final price
        price = base * tod_mult * dow_mult * seasonal_mult * random_mult
        
        # Floor at £0.50 (never negative or too low)
        price = max(0.50, price)
        
        return round(price, 2)
    
    def generate_date_range(
        self,
        start_date: dt.date,
        end_date: dt.date,
    ) -> pd.DataFrame:
        """Generate prices for all services and blocks in date range"""
        
        records = []
        
        current_date = start_date
        while current_date <= end_date:
            for efa_block in range(1, 7):  # 6 blocks per day
                # Calculate block timestamps
                block_start_hour = (efa_block - 1) * 4
                block_start = dt.datetime.combine(
                    current_date, 
                    dt.time(block_start_hour, 0)
                )
                block_end = block_start + dt.timedelta(hours=4)
                
                # Generate prices for each service
                for service in ['DC', 'DM', 'DR']:
                    price = self.generate_price(service, efa_block, current_date)
                    
                    records.append({
                        'efa_date': current_date,
                        'efa_block': efa_block,
                        'service': service,
                        'clearing_price_gbp_per_mw_h': price,
                        'block_start': block_start,
                        'block_end': block_end,
                        'created_at': dt.datetime.utcnow(),
                    })
            
            current_date += dt.timedelta(days=1)
        
        df = pd.DataFrame(records)
        
        print(f"✅ Generated {len(df)} price records")
        print(f"   Date range: {start_date} to {end_date}")
        print(f"   Services: DC, DM, DR")
        print(f"   Blocks per day: 6")
        
        # Summary statistics
        print(f"\n📊 Price Statistics:")
        for service in ['DC', 'DM', 'DR']:
            svc_prices = df[df['service'] == service]['clearing_price_gbp_per_mw_h']
            print(f"   {service}: £{svc_prices.mean():.2f} avg (£{svc_prices.min():.2f}-£{svc_prices.max():.2f})")
        
        return df


def main():
    """Generate sample data and upload to BigQuery"""
    
    print("🔄 FR Clearing Prices - Sample Data Generator")
    print("=" * 80)
    
    # Configuration
    PROJECT_ID = "inner-cinema-476211-u9"
    DATASET = "uk_energy_prod"
    TABLE = "fr_clearing_prices"
    
    # Date range (1 month of data for testing)
    start_date = dt.date(2025, 1, 1)
    end_date = dt.date(2025, 1, 31)
    
    # Generate prices
    generator = FRPriceGenerator(seed=42)
    df = generator.generate_date_range(start_date, end_date)
    
    # Upload to BigQuery
    print(f"\n🔄 Uploading to BigQuery...")
    print(f"   Table: {PROJECT_ID}.{DATASET}.{TABLE}")
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("efa_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("efa_block", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("service", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("clearing_price_gbp_per_mw_h", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("block_start", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("block_end", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded {len(df)} rows to BigQuery")
    
    # Verify upload
    query = f"""
    SELECT 
        service,
        COUNT(*) as records,
        MIN(clearing_price_gbp_per_mw_h) as min_price,
        AVG(clearing_price_gbp_per_mw_h) as avg_price,
        MAX(clearing_price_gbp_per_mw_h) as max_price
    FROM `{table_id}`
    GROUP BY service
    ORDER BY service
    """
    
    print(f"\n🔍 Verification Query:")
    result = client.query(query).to_dataframe()
    print(result.to_string(index=False))
    
    # Export sample to CSV
    sample_file = "fr_clearing_prices_sample.csv"
    df.head(50).to_csv(sample_file, index=False)
    print(f"\n✅ Sample exported to: {sample_file}")
    
    print(f"\n🎉 Done! Ready to run optimizer.")


if __name__ == "__main__":
    main()
