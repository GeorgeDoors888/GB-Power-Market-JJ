#!/usr/bin/env python3
"""
Analyze     print(f"📊 Table: {table_name}")
    print(f"   Description: {table.description or 'No description'}")
    print(f"   Total rows: {table.num_rows:,}" if table.num_rows else "   Total rows: Unknown")

    if table.num_bytes:
        print(f"   Total size: {table.num_bytes / (1024*1024):.2f} MB")
    else:
        print(f"   Total size: Unknown")

    print(f"   Created: {table.created}")
    print(f"   Modified: {table.modified}")Distribution Use of System) charging statements by year and distribution ID
"""

import os
from datetime import datetime

import pandas as pd
from google.cloud import bigquery

# Set up BigQuery client
client = bigquery.Client(project="jibber-jabber-knowledge")
dataset_id = "uk_energy_insights"


def get_all_duos_tables():
    """Get all DUoS-related tables in the dataset"""
    duos_tables = []

    # List all tables in the dataset
    dataset_ref = client.dataset(dataset_id)
    tables = client.list_tables(dataset_ref)

    for table in tables:
        table_name = table.table_id
        # Look for DUoS-related tables
        if any(
            keyword in table_name.lower()
            for keyword in ["duos", "distribution", "charging"]
        ):
            duos_tables.append(table_name)

    return sorted(duos_tables)


def analyze_table_schema(table_name):
    """Analyze the schema of a DUoS table"""
    table_ref = client.dataset(dataset_id).table(table_name)
    table = client.get_table(table_ref)

    print(f"\n📊 Table: {table_name}")
    print(f"   Description: {table.description or 'No description'}")
    print(f"   Total rows: {table.num_rows:,}")
    print(f"   Total size: {table.num_bytes / (1024*1024):.2f} MB")
    print(f"   Created: {table.created}")
    print(f"   Modified: {table.modified}")

    # Get column names and types
    columns = []
    for field in table.schema:
        columns.append(f"{field.name} ({field.field_type})")

    print(f"   Columns ({len(table.schema)}): {', '.join(columns[:10])}")
    if len(columns) > 10:
        print(f"   ... and {len(columns) - 10} more columns")

    return table


def analyze_duos_data_by_year_and_distribution(table_name):
    """Analyze DUoS data by year and distribution ID"""
    print(f"\n🔍 Analyzing data distribution for {table_name}...")

    # First, check what columns are available
    table_ref = client.dataset(dataset_id).table(table_name)
    table = client.get_table(table_ref)

    column_names = [field.name.lower() for field in table.schema]

    # Identify potential date and ID columns
    date_columns = [
        col
        for col in column_names
        if any(keyword in col for keyword in ["date", "year", "time", "period"])
    ]
    id_columns = [
        col
        for col in column_names
        if any(
            keyword in col
            for keyword in ["id", "area", "region", "zone", "district", "distribution"]
        )
    ]

    print(f"   Date-related columns: {date_columns}")
    print(f"   ID-related columns: {id_columns}")

    if not date_columns:
        print("   ⚠️  No date columns found - checking for any temporal data...")
        # Try to sample the data to see what's available
        sample_query = f"""
        SELECT *
        FROM `jibber-jabber-knowledge.{dataset_id}.{table_name}`
        LIMIT 5
        """
        try:
            sample_df = client.query(sample_query).to_dataframe()
            print(f"   Sample data columns: {list(sample_df.columns)}")
            print(f"   Sample data:\n{sample_df.head()}")
        except Exception as e:
            print(f"   ❌ Error sampling data: {e}")
        return None

    # Try to build a query based on available columns
    # Look for the best date column
    best_date_col = None
    for col in date_columns:
        if "date" in col:
            best_date_col = col
            break
    if not best_date_col:
        best_date_col = date_columns[0]

    # Look for the best ID column
    best_id_col = None
    for col in id_columns:
        if any(keyword in col for keyword in ["distribution", "area", "region"]):
            best_id_col = col
            break
    if not best_id_col and id_columns:
        best_id_col = id_columns[0]

    print(f"   Using date column: {best_date_col}")
    print(f"   Using ID column: {best_id_col}")

    # Build the analysis query
    if best_id_col:
        query = f"""
        SELECT
            EXTRACT(YEAR FROM {best_date_col}) as year,
            {best_id_col} as distribution_id,
            COUNT(*) as statement_count,
            MIN({best_date_col}) as earliest_date,
            MAX({best_date_col}) as latest_date
        FROM `jibber-jabber-knowledge.{dataset_id}.{table_name}`
        WHERE {best_date_col} IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
    else:
        query = f"""
        SELECT
            EXTRACT(YEAR FROM {best_date_col}) as year,
            COUNT(*) as statement_count,
            MIN({best_date_col}) as earliest_date,
            MAX({best_date_col}) as latest_date
        FROM `jibber-jabber-knowledge.{dataset_id}.{table_name}`
        WHERE {best_date_col} IS NOT NULL
        GROUP BY 1
        ORDER BY 1
        """

    try:
        print(f"   Executing query: {query}")
        df = client.query(query).to_dataframe()

        if df.empty:
            print("   ⚠️  No data found with valid dates")
            return None

        print(f"   ✅ Found {len(df)} year/distribution combinations")
        return df

    except Exception as e:
        print(f"   ❌ Error analyzing data: {e}")
        return None


def main():
    """Main analysis function"""
    print("🔍 DUOS CHARGING STATEMENTS ANALYSIS")
    print("=" * 50)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Dataset: {dataset_id}")

    # Get all DUoS-related tables
    print("\n📋 Finding DUoS-related tables...")
    duos_tables = get_all_duos_tables()

    if not duos_tables:
        print("❌ No DUoS-related tables found!")
        return

    print(f"✅ Found {len(duos_tables)} DUoS-related tables:")
    for table in duos_tables:
        print(f"   • {table}")

    # Analyze each table
    all_results = {}

    for table_name in duos_tables:
        try:
            # Get table info
            table_info = analyze_table_schema(table_name)

            # Analyze data distribution
            if table_info.num_rows and table_info.num_rows > 0:
                result_df = analyze_duos_data_by_year_and_distribution(table_name)
                if result_df is not None and not result_df.empty:
                    all_results[table_name] = result_df
            else:
                print(f"   ⚠️  Table {table_name} is empty or has unknown row count")

        except Exception as e:
            print(f"   ❌ Error analyzing {table_name}: {e}")

    # Generate summary report
    print("\n" + "=" * 50)
    print("📊 SUMMARY REPORT")
    print("=" * 50)

    if not all_results:
        print("❌ No DUoS charging statement data found!")
        return

    total_statements = 0
    all_years = set()
    all_distributions = set()

    for table_name, df in all_results.items():
        print(f"\n📋 Table: {table_name}")
        print(f"   Total combinations: {len(df)}")

        if "distribution_id" in df.columns:
            print(f"   Distribution IDs: {df['distribution_id'].nunique()}")
            all_distributions.update(df["distribution_id"].unique())

            # Show year breakdown by distribution
            year_dist_summary = (
                df.groupby("year")
                .agg({"distribution_id": "nunique", "statement_count": "sum"})
                .reset_index()
            )

            print("   Year breakdown:")
            for _, row in year_dist_summary.iterrows():
                print(
                    f"     {int(row['year'])}: {int(row['statement_count']):,} statements across {int(row['distribution_id'])} distributions"
                )
                all_years.add(int(row["year"]))
                total_statements += int(row["statement_count"])
        else:
            # No distribution ID, just years
            print("   Year breakdown:")
            for _, row in df.iterrows():
                print(
                    f"     {int(row['year'])}: {int(row['statement_count']):,} statements"
                )
                all_years.add(int(row["year"]))
                total_statements += int(row["statement_count"])

    print(f"\n🎯 OVERALL SUMMARY:")
    print(f"   Total DUoS charging statements: {total_statements:,}")
    print(
        f"   Years covered: {min(all_years) if all_years else 'N/A'} to {max(all_years) if all_years else 'N/A'}"
    )
    print(f"   Number of years: {len(all_years)}")
    print(f"   Distribution IDs found: {len(all_distributions)}")

    if all_distributions:
        print(f"   Distribution areas: {sorted(list(all_distributions))}")

    # Save detailed results
    output_file = f"duos_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, "w") as f:
        f.write("DUoS CHARGING STATEMENTS ANALYSIS\n")
        f.write("=" * 50 + "\n")
        f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {dataset_id}\n\n")

        f.write("DETAILED RESULTS BY TABLE:\n")
        f.write("-" * 30 + "\n")

        for table_name, df in all_results.items():
            f.write(f"\nTable: {table_name}\n")
            f.write(df.to_string(index=False))
            f.write("\n")

        f.write(f"\nOVERALL SUMMARY:\n")
        f.write(f"Total statements: {total_statements:,}\n")
        f.write(
            f"Years: {min(all_years) if all_years else 'N/A'} to {max(all_years) if all_years else 'N/A'}\n"
        )
        f.write(f"Distribution IDs: {len(all_distributions)}\n")
        if all_distributions:
            f.write(f"Areas: {sorted(list(all_distributions))}\n")

    print(f"\n💾 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
