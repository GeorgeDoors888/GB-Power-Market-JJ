#!/usr/bin/env python3
"""
GB Power Market - Battery Arbitrage Analysis
Runs automatically daily at 04:00 UTC via systemd timer
"""
import os
import pathlib
import json
from datetime import datetime, date, timedelta, timezone
from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig
import pandas as pd

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Safety: Max bytes to process (2TB limit)
MAX_BYTES_PROCESSED = 2e12  # 2 TB

def main():
    print(f"⚡ Starting GB Power Market Analysis")
    print(f"   Time: {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S UTC}")
    print(f"   Project: {PROJECT}")
    print(f"   Dataset: {DATASET}")
    print()
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT)
    
    # Query: Last 14 days of market price data with automatic backfill
    # Note: bmrs_mid has 'price' and 'volume' columns (Market Index Data)
    query = f"""
    SELECT 
        DATE(settlementDate) AS date,
        settlementPeriod AS sp,
        dataset,
        AVG(price) AS avg_price,
        SUM(volume) AS total_volume,
        COUNT(*) AS records
    FROM `{PROJECT}.{DATASET}.bmrs_mid`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
    GROUP BY date, sp, dataset
    ORDER BY date DESC, sp
    LIMIT 672  -- 14 days * 48 periods
    """
    
    # Cost safety check: dry run to check bytes processed
    print("� Checking query cost...")
    dry_run_config = QueryJobConfig(dry_run=True, use_query_cache=True)
    dry_run_job = client.query(query, job_config=dry_run_config)
    bytes_processed = dry_run_job.total_bytes_processed
    print(f"   Query will process: {bytes_processed:,} bytes ({bytes_processed/1e9:.2f} GB)")
    
    if bytes_processed > MAX_BYTES_PROCESSED:
        raise Exception(f"Query would process {bytes_processed/1e12:.1f} TB, exceeding {MAX_BYTES_PROCESSED/1e12:.1f} TB limit")
    
    print("�📊 Querying BigQuery for last 14 days of price data...")
    df = client.query(query).to_dataframe()
    
    if len(df) == 0:
        print("⚠️  No data returned from query")
        return
    
    # Calculate basic statistics
    avg_price = df['avg_price'].mean()
    max_price = df['avg_price'].max()
    min_price = df['avg_price'].min()
    
    print(f"✅ Query complete!")
    print(f"   Rows retrieved: {len(df):,}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Average price: £{avg_price:.2f}/MWh")
    print(f"   Price range: £{min_price:.2f} to £{max_price:.2f}/MWh")
    print(f"   Total volume: {df['total_volume'].sum():,.0f} MWh")
    print()
    
    # Save results
    outdir = pathlib.Path("reports/data")
    outdir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_file = outdir / f"price_data_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    
    # Also save summary
    summary = {
        'run_time': datetime.now(timezone.utc).isoformat(),
        'rows': len(df),
        'date_from': str(df['date'].min()),
        'date_to': str(df['date'].max()),
        'avg_price_£_per_mwh': round(avg_price, 2),
        'min_price_£_per_mwh': round(min_price, 2),
        'max_price_£_per_mwh': round(max_price, 2),
        'total_volume_mwh': round(df['total_volume'].sum(), 0),
        'bytes_processed': bytes_processed,
        'query_cost_gb': round(bytes_processed / 1e9, 2)
    }
    
    summary_file = outdir / f"summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Write health check file for monitoring
    health_file = outdir / "health.json"
    health = {
        'ok': True,
        'last_run_utc': datetime.now(timezone.utc).isoformat(),
        'last_run_status': 'success',
        'rows_retrieved': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'next_run_due_utc': (datetime.now(timezone.utc).replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
    }
    with open(health_file, 'w') as f:
        json.dump(health, f, indent=2)
    
    print(f"💾 Results saved:")
    print(f"   Data: {output_file}")
    print(f"   Summary: {summary_file}")
    print(f"   Health: {health_file}")
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
