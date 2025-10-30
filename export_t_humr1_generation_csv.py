#!/usr/bin/env python3
"""
Export T_HUMR-1 Generation Data to CSV
=====================================

This script extracts half-hourly generation data for T_HUMR-1 power station
from the last 24 months and exports it to a CSV file.
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from google.cloud import bigquery


def export_t_humr1_generation_csv(months=24, limit=None):
    """Export T_HUMR-1 generation data to CSV

    Args:
        months (int, optional): Number of months of data to export. Defaults to 24.
        limit (int, optional): Limit the number of records for quick testing. None means no limit.
    """

    print("Initializing BigQuery client...")
    client = bigquery.Client()

    # SQL query to get half-hourly generation data
    query = """
    SELECT
        settlementDate,
        settlementPeriod,
        DATETIME_ADD(
            DATETIME(DATE(settlementDate), TIME(0, 0, 0)),
            INTERVAL (settlementPeriod - 1) * 30 MINUTE
        ) as datetime_utc,
        levelFrom as generation_mw,
        levelTo,
        bmUnit,
        nationalGridBmUnit,
        _ingested_utc as data_ingested_timestamp
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_pn`
    WHERE bmUnit = 'T_HUMR-1'
    AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {} MONTH)
    ORDER BY settlementDate, settlementPeriod
    """.format(
        months
    )

    # Add a LIMIT clause for testing if needed
    if limit:
        query += f"\nLIMIT {limit}"

    print(f"Executing query to fetch T_HUMR-1 generation data...")
    print(f"Query period: Last {months} months")
    if limit:
        print(f"Testing mode: Limited to {limit} records")
    print("Target: Half-hourly generation data")
    print("⏳ This may take several minutes for large date ranges...")

    try:
        # Start timing the query
        start_time = datetime.now()
        print(f"Query started at: {start_time.strftime('%H:%M:%S')}")

        # Execute the query
        job = client.query(query)

        # Show query job ID for reference
        print(f"BigQuery job ID: {job.job_id}")
        print("Waiting for query to complete... (this may take some time)")

        # Wait for the query to complete and get results
        df = job.to_dataframe()

        # Calculate elapsed time
        elapsed_time = datetime.now() - start_time
        print(f"Query completed in: {elapsed_time}")

        if df.empty:
            print("❌ No data found for T_HUMR-1 in the specified period")
            return None

        # Data preprocessing
        print(f"✅ Data fetched successfully: {len(df):,} records")

        # Convert data types
        df["settlementDate"] = pd.to_datetime(df["settlementDate"])
        df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])
        df["data_ingested_timestamp"] = pd.to_datetime(df["data_ingested_timestamp"])

        # Add derived columns
        df["generation_gw"] = df["generation_mw"] / 1000  # Convert MW to GW
        df["hour_of_day"] = df["datetime_utc"].dt.hour
        df["day_of_week"] = df["datetime_utc"].dt.day_name()
        df["month"] = df["datetime_utc"].dt.month
        df["year"] = df["datetime_utc"].dt.year

        # Print data summary
        print("\n📊 Data Summary:")
        print("-" * 50)
        print(
            f"Date range: {df['settlementDate'].min().date()} to {df['settlementDate'].max().date()}"
        )
        print(f"Total records: {len(df):,}")
        print(
            f"Settlement periods: {df['settlementPeriod'].min()} to {df['settlementPeriod'].max()}"
        )

        print("\n⚡ Generation Statistics:")
        print("-" * 50)
        print(
            f"Average Generation: {df['generation_mw'].mean():.2f} MW ({df['generation_gw'].mean():.3f} GW)"
        )
        print(
            f"Peak Generation: {df['generation_mw'].max():.2f} MW ({df['generation_gw'].max():.3f} GW)"
        )
        print(
            f"Minimum Generation: {df['generation_mw'].min():.2f} MW ({df['generation_gw'].min():.3f} GW)"
        )
        print(
            f"Total MWh generated: {df['generation_mw'].sum() * 0.5:,.0f} MWh"
        )  # Half-hourly data

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"T_HUMR-1_Generation_Data_{timestamp}.csv"

        # Export to CSV
        print(f"\n💾 Exporting to CSV: {filename}")
        df.to_csv(filename, index=False)

        print("✅ CSV export completed successfully!")
        print("\n📁 CSV File Contents:")
        print("-" * 50)
        print("Columns included:")
        for col in df.columns:
            print(f"  • {col}")

        print(f"\n📈 Sample data (first 5 rows):")
        print(
            df[["settlementDate", "settlementPeriod", "generation_mw", "generation_gw"]]
            .head()
            .to_string()
        )

        return filename

    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Export T_HUMR-1 generation data to CSV"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=24,
        help="Number of months of data to export (default: 24)",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit the number of records for testing"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run in test mode with 100 records"
    )
    args = parser.parse_args()

    print("T_HUMR-1 Generation Data Export")
    print("=" * 40)

    # If test mode is enabled, override the limit
    if args.test:
        args.limit = 100
        print("Running in TEST MODE with 100 records")

    # Export the data
    csv_file = export_t_humr1_generation_csv(months=args.months, limit=args.limit)

    if csv_file:
        print(f"\n🎉 Export completed successfully!")
        print(f"📁 File saved as: {csv_file}")
        print(
            "\nThe CSV contains half-hourly generation data for T_HUMR-1 power station"
        )
        print(f"covering the last {args.months} months with the following information:")
        print("• Settlement date and period")
        print("• Generation in MW and GW")
        print("• Timestamp information")
        print("• Additional derived columns for analysis")
    else:
        print("\n❌ Export failed. Please check the error messages above.")
