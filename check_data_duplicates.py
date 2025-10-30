#!/usr/bin/env python3
"""Check for duplicate data in BigQuery BMRS tables"""

import os
import sys
from datetime import datetime

import pandas as pd
from google.cloud import bigquery


def check_data_duplicates():
    """Check for duplicate data in BigQuery tables"""

    # Set environment for BigQuery
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
        "/Users/georgemajor/.config/gcloud/application_default_credentials.json"
    )

    try:
        client = bigquery.Client(project="jibber-jabber-knowledge")
        dataset_id = "uk_energy_insights"

        print("🔍 Checking for duplicate data in BigQuery BMRS tables...")
        print("=" * 60)

        # Datasets that might have duplicates (completed in multiple runs)
        potentially_duplicated = ["METADATA", "BOAL", "BOD"]

        # All completed datasets to check
        completed_datasets = [
            "METADATA",
            "BOAL",
            "BOD",
            "FOU2T14D",
            "FOU2T3YW",
            "FOUT2T14D",
            "FREQ",
            "MDP",
            "MNZT",
            "MZT",
            "NOU2T14D",
            "NOU2T3YW",
            "NTB",
            "NTO",
            "NDZ",
            "PN",
            "QPN",
            "SEL",
            "SIL",
            "UOU2T14D",
        ]

        duplicate_issues = []

        for dataset in completed_datasets:
            table_id = f"jibber-jabber-knowledge.{dataset_id}.bmrs_{dataset.lower()}"

            try:
                print(f"\n📊 Checking {dataset}...")

                # First, get basic table info
                table_info_query = f"""
                SELECT
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT _hash_key) as unique_hash_keys,
                    MIN(_ingested_utc) as first_ingested,
                    MAX(_ingested_utc) as last_ingested
                FROM `{table_id}`
                """

                result = list(client.query(table_info_query))
                if result and len(result) > 0:
                    row = result[0]
                    total_rows = row.total_rows or 0
                    unique_hashes = row.unique_hash_keys or 0
                    first_ingested = row.first_ingested
                    last_ingested = row.last_ingested

                    print(f"  Total rows: {total_rows:,}")
                    print(f"  Unique hash keys: {unique_hashes:,}")

                    if total_rows > unique_hashes:
                        duplicate_rows = total_rows - unique_hashes
                        duplicate_issues.append(
                            {
                                "dataset": dataset,
                                "total_rows": total_rows,
                                "unique_hashes": unique_hashes,
                                "duplicate_rows": duplicate_rows,
                                "first_ingested": first_ingested,
                                "last_ingested": last_ingested,
                            }
                        )
                        print(
                            f"  ⚠️  DUPLICATES FOUND: {duplicate_rows:,} duplicate rows"
                        )
                    else:
                        print(f"  ✅ No duplicates detected")

                    if first_ingested and last_ingested:
                        print(
                            f"  Ingestion period: {first_ingested} to {last_ingested}"
                        )

                    # Check for duplicate settlement periods (more specific check)
                    if total_rows > 0:
                        settlement_duplicates_query = f"""
                        WITH duplicates AS (
                            SELECT
                                settlement_date,
                                settlement_period,
                                COUNT(*) as count
                            FROM `{table_id}`
                            WHERE settlement_date IS NOT NULL AND settlement_period IS NOT NULL
                            GROUP BY settlement_date, settlement_period
                            HAVING COUNT(*) > 1
                        )
                        SELECT
                            COUNT(*) as duplicate_settlement_groups,
                            SUM(count) as total_settlement_duplicates
                        FROM duplicates
                        """

                        settlement_result = list(
                            client.query(settlement_duplicates_query)
                        )
                        if settlement_result and len(settlement_result) > 0:
                            s_row = settlement_result[0]
                            dup_groups = s_row.duplicate_settlement_groups or 0
                            total_s_dups = s_row.total_settlement_duplicates or 0

                            if dup_groups > 0:
                                print(
                                    f"  ⚠️  Settlement duplicates: {dup_groups} groups, {total_s_dups} total rows"
                                )

            except Exception as e:
                print(f"  ❌ Error checking {dataset}: {e}")
                continue

        print("\n" + "=" * 60)
        print("📊 DUPLICATE DATA SUMMARY:")

        if duplicate_issues:
            print(f"\n⚠️  Found duplicates in {len(duplicate_issues)} tables:")
            for issue in duplicate_issues:
                print(
                    f"   • {issue['dataset']}: {issue['duplicate_rows']:,} duplicate rows "
                    f"({issue['total_rows']:,} total, {issue['unique_hashes']:,} unique)"
                )

                # Show ingestion timing if available
                if issue["first_ingested"] and issue["last_ingested"]:
                    first = issue["first_ingested"]
                    last = issue["last_ingested"]
                    if first != last:
                        print(f"     Multiple ingestion times: {first} → {last}")

        else:
            print("\n✅ No duplicate data detected in any completed tables!")

        return len(duplicate_issues) == 0

    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        print("💡 Try running: gcloud auth application-default login")
        return False


if __name__ == "__main__":
    success = check_data_duplicates()
    sys.exit(0 if success else 1)
