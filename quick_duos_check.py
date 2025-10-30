#!/usr/bin/env python3
"""
Quick DUoS charging statements analysis
"""

import pandas as pd
from google.cloud import bigquery


def main():
    # Set up BigQuery client
    client = bigquery.Client(project="jibber-jabber-knowledge")

    print("🔍 DUOS CHARGING STATEMENTS ANALYSIS")
    print("=" * 50)

    # Check for UKPN DUoS tables specifically
    ukpn_tables = ["ukpn_duos_charges_annex1", "ukpn_duos_charges_annex2"]

    for table_name in ukpn_tables:
        print(f"\n📊 Analyzing table: {table_name}")

        try:
            # Get table info
            table_ref = client.dataset("uk_energy_insights").table(table_name)
            table = client.get_table(table_ref)

            print(f"   Rows: {table.num_rows:,}")
            print(f"   Columns: {len(table.schema)}")

            # Get column names
            columns = [field.name for field in table.schema]
            print(f"   Column names: {columns[:10]}")

            # Sample the data to understand structure
            sample_query = f"""
            SELECT *
            FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
            LIMIT 5
            """

            df = client.query(sample_query).to_dataframe()
            print(f"   Sample data shape: {df.shape}")

            if not df.empty:
                print("   Sample columns and data:")
                for col in df.columns[:5]:  # Show first 5 columns
                    sample_vals = df[col].dropna().head(3).tolist()
                    print(f"     {col}: {sample_vals}")

            # Try to find year/distribution information
            year_cols = [
                col for col in columns if "year" in col.lower() or "date" in col.lower()
            ]
            dist_cols = [
                col
                for col in columns
                if any(
                    keyword in col.lower()
                    for keyword in ["area", "region", "zone", "distribution", "id"]
                )
            ]

            print(f"   Date-related columns: {year_cols}")
            print(f"   Distribution-related columns: {dist_cols}")

            # If we have year/distribution data, analyze it
            if year_cols or dist_cols:
                count_query = f"""
                SELECT COUNT(*) as total_records
                FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
                """

                total_df = client.query(count_query).to_dataframe()
                print(
                    f"   Total charging statements: {total_df['total_records'].iloc[0]:,}"
                )

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Also check for any other DUoS-related tables
    print(f"\n🔍 Searching for other DUoS tables...")

    list_tables_query = """
    SELECT table_name, row_count, size_bytes
    FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
    WHERE table_name LIKE '%duos%'
       OR table_name LIKE '%distribution%'
       OR table_name LIKE '%charging%'
    ORDER BY table_name
    """

    try:
        tables_df = client.query(list_tables_query).to_dataframe()
        if not tables_df.empty:
            print(f"   Found {len(tables_df)} related tables:")
            for _, row in tables_df.iterrows():
                size_mb = row["size_bytes"] / (1024 * 1024) if row["size_bytes"] else 0
                print(
                    f"     • {row['table_name']}: {row['row_count']:,} rows, {size_mb:.1f} MB"
                )
        else:
            print("   No DUoS-related tables found")
    except Exception as e:
        print(f"   ❌ Error searching tables: {e}")


if __name__ == "__main__":
    main()
