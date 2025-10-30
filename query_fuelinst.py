#!/usr/bin/env python3

from google.cloud import bigquery
from google.oauth2 import service_account


def query_fuelinst():
    # Create credentials from service account
    credentials = service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Create BigQuery client
    client = bigquery.Client(credentials=credentials, project="jibber-jabber-knowledge")

    # First, get the table schema
    table_ref = client.dataset("uk_energy_insights").table("bmrs_fuelinst")
    table = client.get_table(table_ref)

    print("Table Schema:")
    for field in table.schema:
        print(f"{field.name}: {field.field_type}")

    # Write query to get the date range and sample data
    query = """
    SELECT
        MIN(settlementDate) as earliest_date,
        MAX(settlementDate) as latest_date,
        COUNT(*) as row_count
    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    """

    try:
        # Run the query
        query_job = client.query(query)
        results = query_job.result()

        # Print the results
        for row in results:
            print(f"Data Range Summary:")
            print(f"Earliest date: {row.earliest_date}")
            print(f"Latest date: {row.latest_date}")
            print(f"Total rows: {row.row_count}")

        # Get a sample of recent data
        sample_query = """
        SELECT
            settlementDate,
            settlementPeriod,
            fuelType,
            generation,
            _window_from_utc,
            _window_to_utc
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
        ORDER BY settlementDate DESC, settlementPeriod DESC
        LIMIT 5
        """

        sample_job = client.query(sample_query)
        sample_results = sample_job.result()

        # Check for duplicates
        duplicate_query = """
        WITH Counts AS (
            SELECT
                settlementDate,
                settlementPeriod,
                fuelType,
                COUNT(*) as occurrence_count
            FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
            GROUP BY settlementDate, settlementPeriod, fuelType
            HAVING COUNT(*) > 1
        )
        SELECT
            COUNT(*) as duplicate_groups,
            SUM(occurrence_count) as total_duplicate_records
        FROM Counts
        """

        print("\nChecking for duplicates...")
        duplicate_job = client.query(duplicate_query)
        duplicate_results = duplicate_job.result()

        for row in duplicate_results:
            if row.duplicate_groups > 0:
                print(f"Found {row.duplicate_groups} groups with duplicates")
                print(f"Total duplicate records: {row.total_duplicate_records}")

                # Get sample of duplicates
                sample_duplicates_query = """
                WITH Counts AS (
                    SELECT
                        settlementDate,
                        settlementPeriod,
                        fuelType,
                        COUNT(*) as occurrence_count
                    FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
                    GROUP BY settlementDate, settlementPeriod, fuelType
                    HAVING COUNT(*) > 1
                )
                SELECT
                    f.*
                FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst` f
                INNER JOIN Counts c
                    ON f.settlementDate = c.settlementDate
                    AND f.settlementPeriod = c.settlementPeriod
                    AND f.fuelType = c.fuelType
                ORDER BY f.settlementDate, f.settlementPeriod, f.fuelType
                LIMIT 10
                """

                print("\nSample of duplicate records:")
                dup_sample_job = client.query(sample_duplicates_query)
                dup_sample_results = dup_sample_job.result()

                for dup_row in dup_sample_results:
                    print(f"\nSettlement Date: {dup_row.settlementDate}")
                    print(f"Settlement Period: {dup_row.settlementPeriod}")
                    print(f"Fuel Type: {dup_row.fuelType}")
                    print(f"Generation: {dup_row.generation}")
                    print(
                        f"Window: {dup_row._window_from_utc} to {dup_row._window_to_utc}"
                    )
            else:
                print(
                    "No duplicates found! Each combination of settlementDate, settlementPeriod, and fuelType is unique."
                )

        print("\nMost recent records:")
        for row in sample_results:
            print(f"Settlement Date: {row.settlementDate}")
            print(f"Settlement Period: {row.settlementPeriod}")
            print(f"Fuel Type: {row.fuelType}")
            print(f"Generation: {row.generation}")
            print(f"Window: {row._window_from_utc} to {row._window_to_utc}")
            print("---")

    except Exception as e:
        print(f"Error querying BigQuery: {str(e)}")


if __name__ == "__main__":
    query_fuelinst()
