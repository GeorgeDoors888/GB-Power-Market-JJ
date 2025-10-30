#!/usr/bin/env python3
"""
Quick script to check data completeness in BigQuery
"""

from datetime import datetime, timedelta

import pandas as pd
from google.cloud import bigquery


def main():
    client = bigquery.Client(project="jibber-jabber-knowledge")
    dataset_id = "uk_energy_insights"

    print("=== BMRS Data Completeness Check ===\n")

    # Check main BMRS tables
    tables_to_check = [
        "bmrs_bod",
        "bmrs_boalf",
        "bmrs_mip",
        "bmrs_mels",
        "bmrs_mils",
        "bmrs_freq",
        "bmrs_fuelinst",
        "bmrs_pn",
        "bmrs_qpn",
    ]

    for table_name in tables_to_check:
        print(f"\n📊 {table_name.upper()}")
        print("-" * 50)

        try:
            # First check if table exists
            table_ref = client.dataset(dataset_id).table(table_name)
            try:
                table = client.get_table(table_ref)
                schema_fields = [field.name for field in table.schema]
            except:
                print("❌ Table not found")
                continue

            # Use appropriate date column
            date_column = "settlementDate"
            if "settlementDate" not in schema_fields:
                if "startTime" in schema_fields:
                    date_column = "startTime"
                elif "timeFrom" in schema_fields:
                    date_column = "timeFrom"
                else:
                    print(
                        f"❌ No recognizable date column found. Available: {schema_fields}"
                    )
                    continue

            # Check date range and count by year
            query = f"""
            SELECT
                EXTRACT(YEAR FROM {date_column}) as year,
                COUNT(*) as row_count,
                MIN({date_column}) as earliest_date,
                MAX({date_column}) as latest_date
            FROM `{client.project}.{dataset_id}.{table_name}`
            WHERE {date_column} IS NOT NULL
            GROUP BY year
            ORDER BY year
            """

            df = client.query(query).to_dataframe()

            if len(df) == 0:
                print("❌ No data found")
                continue

            print(f"Total years: {len(df)}")
            print(f"Date column: {date_column}")
            print("\nYear breakdown:")
            for _, row in df.iterrows():
                year = row["year"]
                count = row["row_count"]
                earliest = (
                    row["earliest_date"].strftime("%Y-%m-%d")
                    if pd.notnull(row["earliest_date"])
                    else "N/A"
                )
                latest = (
                    row["latest_date"].strftime("%Y-%m-%d")
                    if pd.notnull(row["latest_date"])
                    else "N/A"
                )

                if pd.notnull(year):
                    print(
                        f"  {int(year)}: {int(count):,} rows ({earliest} to {latest})"
                    )

            # Check total rows
            total_rows = df["row_count"].sum()
            print(f"\n✅ Total rows: {int(total_rows):,}")

            # Check for 2022 specifically
            df_2022 = df[df["year"] == 2022]
            if len(df_2022) > 0:
                count_2022 = int(df_2022["row_count"].iloc[0])
                print(f"📅 2022 data: {count_2022:,} rows ✅")
            else:
                print("📅 2022 data: ❌ MISSING")

        except Exception as e:
            print(f"❌ Error checking {table_name}: {e}")

    print("\n" + "=" * 60)
    print("Summary:")
    print("- The ingestion process for 2022 is currently running")
    print("- Check above for which tables already have 2022 data")
    print("- Missing 2022 data will be filled by the running process")


if __name__ == "__main__":
    main()
