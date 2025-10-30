#!/usr/bin/env python3
"""
Detailed DUoS charging statements analysis by year and distribution ID
"""

import pandas as pd
from google.cloud import bigquery


def main():
    # Set up BigQuery client
    client = bigquery.Client(project="jibber-jabber-knowledge")

    print("🔍 DETAILED DUOS CHARGING STATEMENTS ANALYSIS")
    print("=" * 60)

    print("\n📊 UKPN DUoS Charges Annex 1 Analysis")
    print("-" * 40)

    # Analysis for Annex 1
    annex1_query = """
    SELECT
        year,
        dno_area,
        COUNT(*) as statement_count,
        COUNT(DISTINCT type) as unique_types,
        COUNT(DISTINCT voltage_level) as unique_voltage_levels
    FROM `jibber-jabber-knowledge.uk_energy_insights.ukpn_duos_charges_annex1`
    GROUP BY year, dno_area
    ORDER BY year, dno_area
    """

    annex1_df = client.query(annex1_query).to_dataframe()

    if not annex1_df.empty:
        print(f"Total records: {annex1_df['statement_count'].sum():,}")
        print(f"Years covered: {sorted(annex1_df['year'].unique())}")
        print(f"Distribution areas: {sorted(annex1_df['dno_area'].unique())}")

        print("\nBreakdown by Year and Distribution Area:")
        for year in sorted(annex1_df["year"].unique()):
            year_data = annex1_df[annex1_df["year"] == year]
            total_for_year = year_data["statement_count"].sum()
            areas_count = len(year_data)
            print(
                f"  {year}: {total_for_year:,} statements across {areas_count} distribution areas"
            )

            for _, row in year_data.iterrows():
                print(f"    • {row['dno_area']}: {row['statement_count']} statements")

    print("\n📊 UKPN DUoS Charges Annex 2 Analysis")
    print("-" * 40)

    # Analysis for Annex 2
    annex2_query = """
    SELECT
        year,
        dno,
        COUNT(*) as statement_count,
        COUNT(DISTINCT import_unique_identifier) as unique_import_ids,
        COUNT(DISTINCT export_unique_identifier) as unique_export_ids
    FROM `jibber-jabber-knowledge.uk_energy_insights.ukpn_duos_charges_annex2`
    GROUP BY year, dno
    ORDER BY year, dno
    """

    annex2_df = client.query(annex2_query).to_dataframe()

    if not annex2_df.empty:
        print(f"Total records: {annex2_df['statement_count'].sum():,}")
        print(f"Years covered: {sorted(annex2_df['year'].unique())}")
        print(f"Distribution Network Operators: {sorted(annex2_df['dno'].unique())}")

        print("\nBreakdown by Year and DNO:")
        for year in sorted(annex2_df["year"].unique()):
            year_data = annex2_df[annex2_df["year"] == year]
            total_for_year = year_data["statement_count"].sum()
            dnos_count = len(year_data)
            print(f"  {year}: {total_for_year:,} statements across {dnos_count} DNOs")

            for _, row in year_data.iterrows():
                print(f"    • {row['dno']}: {row['statement_count']} statements")

    print("\n📊 COMBINED SUMMARY")
    print("-" * 40)

    # Get unique identifiers from both tables
    print("Getting unique distribution identifiers...")

    annex1_ids_query = """
    SELECT DISTINCT dno_area as distribution_id, 'Annex1' as source
    FROM `jibber-jabber-knowledge.uk_energy_insights.ukpn_duos_charges_annex1`
    """

    annex2_ids_query = """
    SELECT DISTINCT dno as distribution_id, 'Annex2' as source
    FROM `jibber-jabber-knowledge.uk_energy_insights.ukpn_duos_charges_annex2`
    """

    annex1_ids_df = client.query(annex1_ids_query).to_dataframe()
    annex2_ids_df = client.query(annex2_ids_query).to_dataframe()

    # Combine all distribution IDs
    all_dist_ids = set(
        annex1_ids_df["distribution_id"].tolist()
        + annex2_ids_df["distribution_id"].tolist()
    )

    # Get all years
    all_years = set(annex1_df["year"].tolist() + annex2_df["year"].tolist())

    total_statements = (
        annex1_df["statement_count"].sum() + annex2_df["statement_count"].sum()
    )

    print(f"📈 OVERALL SUMMARY:")
    print(f"   Total DUoS charging statements: {total_statements:,}")
    print(f"   Years covered: {min(all_years)} to {max(all_years)}")
    print(f"   Number of years: {len(all_years)}")
    print(f"   Total distribution identifiers: {len(all_dist_ids)}")

    print(f"\n📍 All Distribution Areas/Networks:")
    for i, dist_id in enumerate(sorted(all_dist_ids), 1):
        print(f"   {i:2d}. {dist_id}")

    # Detailed breakdown by source table
    print(f"\n📋 Breakdown by Data Source:")
    print(
        f"   • Annex 1 (Domestic/Commercial tariffs): {annex1_df['statement_count'].sum():,} statements"
    )
    print(f"     - Distribution areas: {len(annex1_df['dno_area'].unique())}")
    print(f"     - Years: {len(annex1_df['year'].unique())}")

    print(
        f"   • Annex 2 (EHV/LDNO charges): {annex2_df['statement_count'].sum():,} statements"
    )
    print(f"     - DNO networks: {len(annex2_df['dno'].unique())}")
    print(f"     - Years: {len(annex2_df['year'].unique())}")

    # Check for any other DUoS tables in the dataset
    print(f"\n🔍 Checking for other DUoS-related tables...")

    list_tables_query = """
    SELECT table_name
    FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
    WHERE table_name LIKE '%duos%'
       OR table_name LIKE '%distribution%'
       OR table_name LIKE '%charging%'
    ORDER BY table_name
    """

    try:
        tables_df = client.query(list_tables_query).to_dataframe()
        other_tables = [
            t
            for t in tables_df["table_name"].tolist()
            if t not in ["ukpn_duos_charges_annex1", "ukpn_duos_charges_annex2"]
        ]

        if other_tables:
            print(f"   Found {len(other_tables)} other related tables:")
            for table in other_tables:
                print(f"     • {table}")
        else:
            print("   No other DUoS-related tables found")
    except Exception as e:
        print(f"   ❌ Error checking for other tables: {e}")


if __name__ == "__main__":
    main()
