#!/usr/bin/env python3
"""Check for duplicate rows in BigQuery tables"""

import os
import sys

from google.cloud import bigquery


def check_duplicates():
    """Check for duplicate rows in BMRS tables"""

    # Initialize BigQuery client
    client = bigquery.Client(project="jibber-jabber-knowledge")
    dataset_id = "uk_energy_insights"

    print("🔍 Checking for duplicate rows in BigQuery tables...")

    # List of completed datasets to check
    completed_datasets = [
        "BOD",
        "FREQ",
        "FOU2T14D",
        "FOU2T3YW",
        "NOU2T14D",
        "NOU2T3YW",
        "NTB",
        "NTO",
        "NDZ",
        "SEL",
        "SIL",
        "UOU2T14D",
    ]

    duplicate_tables = []

    for dataset in completed_datasets:
        table_id = f"jibber-jabber-knowledge.{dataset_id}.bmrs_{dataset.lower()}"

        try:
            # Check for duplicates based on common key columns
            duplicate_query = f"""
            WITH duplicates AS (
                SELECT
                    settlement_date,
                    settlement_period,
                    COUNT(*) as row_count
                FROM `{table_id}`
                GROUP BY settlement_date, settlement_period
                HAVING COUNT(*) > 1
            )
            SELECT
                COUNT(*) as duplicate_groups,
                SUM(row_count) as total_duplicate_rows
            FROM duplicates
            """

            result = list(client.query(duplicate_query))
            if result and len(result) > 0:
                dup_groups = result[0].duplicate_groups or 0
                total_dups = result[0].total_duplicate_rows or 0

                if dup_groups > 0:
                    duplicate_tables.append(
                        {
                            "table": dataset,
                            "duplicate_groups": dup_groups,
                            "total_duplicate_rows": total_dups,
                        }
                    )
                    print(
                        f"⚠️  {dataset}: {dup_groups} duplicate groups, {total_dups} total duplicate rows"
                    )
                else:
                    print(f"✅ {dataset}: No duplicates found")

        except Exception as e:
            print(f"❌ {dataset}: Error checking duplicates - {e}")

    if duplicate_tables:
        print(f"\n⚠️  Found duplicates in {len(duplicate_tables)} tables:")
        for table in duplicate_tables:
            print(
                f"   • {table['table']}: {table['duplicate_groups']} groups, {table['total_duplicate_rows']} rows"
            )
        return False
    else:
        print("\n✅ No duplicates found in any completed tables!")
        return True


if __name__ == "__main__":
    check_duplicates()
