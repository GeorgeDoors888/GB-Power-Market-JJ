#!/usr/bin/env python3

from google.cloud import bigquery
from google.oauth2 import service_account


def get_latest_data():
    # Create credentials from service account
    credentials = service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Create BigQuery client
    client = bigquery.Client(credentials=credentials, project="jibber-jabber-knowledge")

    # Query to get the latest version of each data point
    query = """
    WITH LatestVersions AS (
        SELECT
            settlementDate,
            settlementPeriod,
            fuelType,
            generation,
            _ingested_utc,
            ROW_NUMBER() OVER (
                PARTITION BY settlementDate, settlementPeriod, fuelType
                ORDER BY _ingested_utc DESC
            ) as rn
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
    )
    SELECT
        settlementDate,
        COUNT(DISTINCT CASE WHEN rn = 1 THEN CONCAT(settlementPeriod, fuelType) END) as unique_datapoints,
        COUNT(*) as total_versions,
        COUNT(*) - COUNT(DISTINCT CASE WHEN rn = 1 THEN CONCAT(settlementPeriod, fuelType) END) as duplicate_versions
    FROM LatestVersions
    GROUP BY settlementDate
    ORDER BY settlementDate;
    """

    try:
        print("\nAnalyzing data versions...")
        query_job = client.query(query)
        results = query_job.result()

        for row in results:
            print(f"\nDate: {row.settlementDate}")
            print(f"Unique data points: {row.unique_datapoints}")
            print(f"Total versions in data: {row.total_versions}")
            print(f"Duplicate versions: {row.duplicate_versions}")
            print("-" * 50)

        # Get sample of data showing multiple versions
        sample_query = """
        WITH LatestVersions AS (
            SELECT
                settlementDate,
                settlementPeriod,
                fuelType,
                generation,
                _ingested_utc,
                ROW_NUMBER() OVER (
                    PARTITION BY settlementDate, settlementPeriod, fuelType
                    ORDER BY _ingested_utc DESC
                ) as version_number,
                COUNT(*) OVER (
                    PARTITION BY settlementDate, settlementPeriod, fuelType
                ) as version_count
            FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
        )
        SELECT *
        FROM LatestVersions
        WHERE version_count > 1  -- Only show records with multiple versions
        AND settlementDate = (SELECT MAX(settlementDate) FROM LatestVersions)  -- Latest date
        AND settlementPeriod = 1  -- First period of the day
        ORDER BY fuelType, _ingested_utc DESC
        LIMIT 10
        """

        print("\nSample of multiple versions (for latest date, period 1):")
        print("-" * 80)
        sample_job = client.query(sample_query)
        sample_results = sample_job.result()

        for row in sample_results:
            print(f"\nFuel Type: {row.fuelType}")
            print(
                f"Settlement Date: {row.settlementDate}, Period: {row.settlementPeriod}"
            )
            print(f"Generation: {row.generation}")
            print(f"Ingested at: {row._ingested_utc}")
            print(f"Version: {row.version_number} of {row.version_count}")
            print("-" * 40)

    except Exception as e:
        print(f"Error querying BigQuery: {str(e)}")


if __name__ == "__main__":
    get_latest_data()
