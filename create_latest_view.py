#!/usr/bin/env python3

from google.cloud import bigquery
from google.oauth2 import service_account


def create_latest_view():
    # Create credentials from service account
    credentials = service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Create BigQuery client
    client = bigquery.Client(credentials=credentials, project="jibber-jabber-knowledge")

    # Create a view that shows only the latest versions
    view_query = """
    CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest_view` AS
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

    try:
        print("Creating view of latest versions...")
        view_job = client.query(view_query)
        view_job.result()

        # Check counts
        count_query = """
        SELECT
            (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`) as original_count,
            (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest_view`) as deduplicated_count
        """

        print("\nChecking record counts...")
        count_job = client.query(count_query)
        counts = count_job.result()

        for row in counts:
            print(f"\nOriginal table record count: {row.original_count:,}")
            print(f"Deduplicated view record count: {row.deduplicated_count:,}")
            print(
                f"Duplicate records identified: {row.original_count - row.deduplicated_count:,}"
            )

        print("\nYou can now query the latest data using:")
        print(
            "SELECT * FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst_latest_view`"
        )

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    create_latest_view()
