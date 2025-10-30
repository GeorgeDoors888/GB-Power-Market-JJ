#!/usr/bin/env python3
"""
Comprehensive BMRS Data Completeness Check for 2022-2025
"""

import sys
from datetime import datetime, timedelta

import pandas as pd
from google.cloud import bigquery


def main():
    client = bigquery.Client(project="jibber-jabber-knowledge")
    dataset_id = "uk_energy_insights"

    print("=" * 80)
    print("🔍 COMPREHENSIVE BMRS DATA COMPLETENESS CHECK (2022-2025)")
    print("=" * 80)
    print()

    # All BMRS tables to check
    tables_to_check = [
        "bmrs_bod",  # Bid-Offer Data
        "bmrs_boalf",  # Bid-Offer Acceptance Level Flagging
        "bmrs_mip",  # Market Index Price
        "bmrs_mels",  # Market Entry Load Schedule
        "bmrs_mils",  # Market Index Load Schedule
        "bmrs_freq",  # System Frequency
        "bmrs_fuelinst",  # Fuel Type Generation by Settlement Period
        "bmrs_pn",  # Physical Notifications
        "bmrs_qpn",  # Quiescent Physical Notifications
        "bmrs_disbsad",  # Balancing Services Adjustment Data
        "bmrs_imbalngc",  # Imbalance Prices
        "bmrs_itsdo",  # Initial Transmission System Demand Outturn
        "bmrs_mid",  # Market Index Data
        "bmrs_qas",  # Balancing Services Volume Data
        "bmrs_rdri",  # Run Down Rate Import
        "bmrs_tsdf",  # Transmission System Demand Forecast
        "bmrs_windfor",  # Wind Generation Forecast
    ]

    # Expected years
    target_years = [2022, 2023, 2024, 2025]

    results = {}

    for table_name in tables_to_check:
        print(f"\n📊 Checking {table_name.upper()}")
        print("-" * 60)

        try:
            # First check if table exists
            table_ref = client.dataset(dataset_id).table(table_name)
            try:
                table = client.get_table(table_ref)
                schema_fields = [field.name for field in table.schema]
                total_rows = table.num_rows
            except Exception as e:
                print(f"❌ Table not found: {e}")
                results[table_name] = {"error": "Table not found"}
                continue

            # Use appropriate date column
            date_column = "settlementDate"
            if "settlementDate" not in schema_fields:
                if "startTime" in schema_fields:
                    date_column = "startTime"
                elif "timeFrom" in schema_fields:
                    date_column = "timeFrom"
                elif "measurementTime" in schema_fields:
                    date_column = "measurementTime"
                else:
                    print(
                        f"❌ No recognizable date column found. Available: {schema_fields[:10]}..."
                    )
                    results[table_name] = {"error": "No date column found"}
                    continue

            print(f"📅 Date column: {date_column}")
            print(f"📈 Total rows: {total_rows:,}")

            # Check date range and count by year
            query = f"""
            SELECT
                EXTRACT(YEAR FROM {date_column}) as year,
                COUNT(*) as row_count,
                MIN({date_column}) as earliest_date,
                MAX({date_column}) as latest_date,
                COUNT(DISTINCT DATE({date_column})) as unique_days
            FROM `{client.project}.{dataset_id}.{table_name}`
            WHERE {date_column} IS NOT NULL
            AND EXTRACT(YEAR FROM {date_column}) BETWEEN 2022 AND 2025
            GROUP BY year
            ORDER BY year
            """

            df = client.query(query).to_dataframe()

            if len(df) == 0:
                print("❌ No data found for 2022-2025")
                results[table_name] = {"years": {}, "total_rows": total_rows}
                continue

            year_data = {}
            print("\n📊 Year-by-year breakdown:")

            for target_year in target_years:
                year_row = df[df["year"] == target_year]
                if len(year_row) > 0:
                    row = year_row.iloc[0]
                    count = int(row["row_count"])
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
                    unique_days = (
                        int(row["unique_days"]) if pd.notnull(row["unique_days"]) else 0
                    )

                    # Calculate expected days for the year
                    if target_year == 2025:
                        # Only up to current date
                        expected_days = (datetime.now() - datetime(2025, 1, 1)).days + 1
                    else:
                        # Full year
                        expected_days = 366 if target_year % 4 == 0 else 365

                    coverage = (
                        (unique_days / expected_days) * 100 if expected_days > 0 else 0
                    )

                    status = "✅" if coverage > 90 else "⚠️" if coverage > 50 else "❌"
                    print(
                        f"  {status} {target_year}: {count:,} rows | {unique_days}/{expected_days} days ({coverage:.1f}%) | {earliest} to {latest}"
                    )

                    year_data[target_year] = {
                        "count": count,
                        "earliest": earliest,
                        "latest": latest,
                        "unique_days": unique_days,
                        "expected_days": expected_days,
                        "coverage": coverage,
                    }
                else:
                    print(f"  ❌ {target_year}: No data")
                    year_data[target_year] = {"count": 0, "coverage": 0}

            results[table_name] = {
                "years": year_data,
                "total_rows": total_rows,
                "date_column": date_column,
            }

        except Exception as e:
            print(f"❌ Error checking {table_name}: {e}")
            results[table_name] = {"error": str(e)}

    # Summary report
    print("\n" + "=" * 80)
    print("📋 SUMMARY REPORT")
    print("=" * 80)

    missing_data = []

    for year in target_years:
        print(f"\n🗓️  {year} DATA STATUS:")
        year_missing = []

        for table_name in tables_to_check:
            if table_name in results and "years" in results[table_name]:
                year_data = results[table_name]["years"].get(
                    year, {"count": 0, "coverage": 0}
                )
                count = year_data["count"]
                coverage = year_data.get("coverage", 0)

                if count == 0:
                    status = "❌ MISSING"
                    year_missing.append(table_name)
                elif coverage < 50:
                    status = f"⚠️  PARTIAL ({coverage:.1f}%)"
                    year_missing.append(f"{table_name} (partial)")
                else:
                    status = f"✅ COMPLETE ({coverage:.1f}%)"

                print(f"  {table_name:15} {status:20} {count:>12,} rows")
            else:
                print(f"  {table_name:15} {'❌ ERROR':20}")
                year_missing.append(f"{table_name} (error)")

        if year_missing:
            missing_data.append(f"{year}: {', '.join(year_missing)}")

    if missing_data:
        print(f"\n🚨 MISSING/INCOMPLETE DATA SUMMARY:")
        for item in missing_data:
            print(f"  • {item}")
    else:
        print(f"\n🎉 ALL DATA COMPLETE!")

    print(f"\n📊 Total tables checked: {len(tables_to_check)}")
    print(f"✅ Tables found: {len([t for t in results if 'error' not in results[t]])}")
    print(
        f"❌ Tables missing/error: {len([t for t in results if 'error' in results[t]])}"
    )


if __name__ == "__main__":
    main()
