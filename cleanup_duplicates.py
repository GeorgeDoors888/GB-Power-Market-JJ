#!/usr/bin/env python3

from google.cloud import bigquery
from google.oauth2 import service_account


def cleanup_duplicates():
    # Create credentials from service account
    credentials = service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Create BigQuery client
    client = bigquery.Client(credentials=credentials, project="jibber-jabber-knowledge")

    print("Starting cleanup process...")

    # Step 1: Create new table with only latest versions
    create_latest_query = """
    CREATE OR REPLACE TABLE `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest` AS
    WITH LatestVersions AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY settlementDate, settlementPeriod, fuelType
                ORDER BY _ingested_utc DESC
            ) as rn
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    )
    SELECT * EXCEPT(rn)
    FROM LatestVersions
    WHERE rn = 1
    """

    print("\nCreating new table with latest versions...")
    create_job = client.query(create_latest_query)
    create_job.result()  # Wait for the query to complete

    # Step 2: Verify counts
    count_query = """
    SELECT
        (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`) as original_count,
        (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest`) as new_count
    """

    print("\nVerifying record counts...")
    count_job = client.query(count_query)
    counts = count_job.result()

    for row in counts:
        print(f"\nOriginal table record count: {row.original_count:,}")
        print(f"New table record count: {row.new_count:,}")
        print(
            f"Duplicate records that will be removed: {row.original_count - row.new_count:,}"
        )

    # Step 3: Ask for confirmation before proceeding with deletion
    confirmation = input(
        "\nDo you want to proceed with replacing the original table? (yes/no): "
    )

    if confirmation.lower() == "yes":
        replace_query = """
        DROP TABLE `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`;
        ALTER TABLE `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest`
        RENAME TO `bmrs_fuelinst`;
        """

        print("\nReplacing original table with deduplicated version...")
        replace_job = client.query(replace_query)
        replace_job.result()
        print("Cleanup complete!")
    else:
        print(
            "\nCleanup cancelled. The new table 'bmrs_fuelinst_latest' contains the deduplicated data."
        )
        print("You can review it before manually replacing the original table.")


if __name__ == "__main__":
    cleanup_duplicates()
