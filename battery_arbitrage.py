#!/usr/bin/env python3
"""
GB Power Market - Battery Arbitrage Analysis
Runs automatically via Cloud Run on schedule
"""
import os
import pathlib
from datetime import datetime
from google.cloud import bigquery
import pandas as pd

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def main():
    print(f"🚀 Starting GB Power Market Analysis")
    print(f"   Time: {datetime.utcnow():%Y-%m-%d %H:%M:%S UTC}")
    print(f"   Project: {PROJECT}")
    print(f"   Dataset: {DATASET}")
    print()
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT)
    
    # Query: Last 7 days of price data
    query = f"""
    SELECT 
        DATE(settlement_date) AS date,
        settlement_period AS sp,
        AVG(system_sell_price) AS avg_sell_price,
        AVG(system_buy_price) AS avg_buy_price,
        MAX(system_sell_price) AS max_sell_price,
        MIN(system_buy_price) AS min_buy_price,
        COUNT(*) AS records
    FROM `{PROJECT}.{DATASET}.bmrs_mid`
    WHERE DATE(settlement_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY date, sp
    ORDER BY date DESC, sp
    LIMIT 336  -- 7 days * 48 periods
    """
    
    print("📊 Querying BigQuery for last 7 days of price data...")
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        print("⚠️  No data returned from query")
        return
    
    # Calculate basic statistics
    avg_spread = (df['avg_sell_price'] - df['avg_buy_price']).mean()
    max_spread = (df['max_sell_price'] - df['min_buy_price']).max()
    
    print(f"✅ Query complete!")
    print(f"   Rows retrieved: {len(df):,}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Average spread: £{avg_spread:.2f}/MWh")
    print(f"   Maximum spread: £{max_spread:.2f}/MWh")
    print()
    
    # Save results
    outdir = pathlib.Path("reports/data")
    outdir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = outdir / f"price_data_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    
    # Also save summary
    summary = {
        'run_time': datetime.utcnow().isoformat(),
        'rows': len(df),
        'date_from': str(df['date'].min()),
        'date_to': str(df['date'].max()),
        'avg_spread_£_per_mwh': round(avg_spread, 2),
        'max_spread_£_per_mwh': round(max_spread, 2)
    }
    
    summary_file = outdir / f"summary_{timestamp}.json"
    import json
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"💾 Results saved:")
    print(f"   Data: {output_file}")
    print(f"   Summary: {summary_file}")
    print()
    print("✅ Analysis complete!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
