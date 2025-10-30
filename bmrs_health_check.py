#!/usr/bin/env python3
"""
BMRS Data Health Check and Repair
=================================

This script checks the health of all BMRS datasets across all years
and provides repair commands for any issues found.
"""

import sys

sys.path.append(".")
from google.cloud import bigquery


def check_data_completeness():
    """Check completeness of all BMRS datasets across all years."""
    print("🔍 BMRS DATA HEALTH CHECK")
    print("=" * 40)

    try:
        client = bigquery.Client(project="jibber-jabber-knowledge")

        # Check year-by-year coverage
        query = """
        SELECT
          EXTRACT(YEAR FROM DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\d{8})')))) as year,
          COUNT(DISTINCT table_name) as unique_datasets,
          COUNT(*) as total_partitions,
          MIN(DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\d{8})')))) as earliest_date,
          MAX(DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\d{8})')))) as latest_date
        FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.PARTITIONS`
        WHERE table_name LIKE 'bmrs_%'
          AND partition_id IS NOT NULL
          AND partition_id != '__NULL__'
          AND REGEXP_CONTAINS(partition_id, r'^\\d{8}$')
        GROUP BY year
        ORDER BY year
        """

        results = client.query(query).result()

        print("📊 Current Status by Year:")
        year_data = {}
        for row in results:
            year = int(row.year)
            datasets = row.unique_datasets
            partitions = row.total_partitions
            earliest = row.earliest_date.strftime("%Y-%m-%d")
            latest = row.latest_date.strftime("%Y-%m-%d")
            year_data[year] = datasets
            print(
                f"  {year}: {datasets:2d} datasets, {partitions:,} partitions ({earliest} to {latest})"
            )

        print()

        # Load expected datasets
        exec(open("ingest_elexon_fixed.py").read())
        total_supported = len(DATASET_CONFIGS)

        if year_data:
            max_datasets = max(year_data.values())
            print(f"📋 Analysis:")
            print(f"  Total supported datasets: {total_supported}")
            print(f"  Best year coverage: {max_datasets} datasets")
            print()

            print("📈 Completeness by Year:")
            incomplete_years = []
            for year in [2022, 2023, 2024, 2025]:
                current = year_data.get(year, 0)
                missing = max_datasets - current
                pct = (current / max_datasets * 100) if max_datasets > 0 else 0

                if missing == 0:
                    status = "✅ COMPLETE"
                else:
                    status = f"❌ Missing {missing} datasets"
                    incomplete_years.append((year, missing))

                print(f"  {year}: {current:2d}/{max_datasets} ({pct:5.1f}%) {status}")

            # Provide specific recommendations
            print()
            if incomplete_years:
                print("🎯 REPAIR RECOMMENDATIONS:")
                for year, missing_count in incomplete_years:
                    if year == 2022:
                        print(
                            f"  {year}: Run complete_2022_datasets.py to add remaining {missing_count} datasets"
                        )
                    else:
                        print(
                            f"  {year}: Investigate why {missing_count} datasets are missing"
                        )

                        # Get specific missing datasets for non-2022 years
                        missing_query = f"""
                        WITH complete_datasets AS (
                          SELECT DISTINCT table_name
                          FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.PARTITIONS`
                          WHERE table_name LIKE 'bmrs_%'
                            AND EXTRACT(YEAR FROM DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\\\d{{8}})')))) = {max(year_data.keys())}
                        ),
                        year_{year}_datasets AS (
                          SELECT DISTINCT table_name
                          FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.PARTITIONS`
                          WHERE table_name LIKE 'bmrs_%'
                            AND EXTRACT(YEAR FROM DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\\\d{{8}})')))) = {year}
                        )
                        SELECT c.table_name
                        FROM complete_datasets c
                        LEFT JOIN year_{year}_datasets y ON c.table_name = y.table_name
                        WHERE y.table_name IS NULL
                        ORDER BY c.table_name
                        """

                        try:
                            missing_results = client.query(missing_query).result()
                            missing_datasets = [
                                row.table_name for row in missing_results
                            ]
                            if missing_datasets and len(missing_datasets) <= 10:
                                print(f"      Missing: {', '.join(missing_datasets)}")
                        except Exception as e:
                            print(
                                f"      Could not determine specific missing datasets: {e}"
                            )
            else:
                print("🎉 ALL YEARS COMPLETE!")
                print("   No action needed - all datasets are present for all years.")

        return year_data, total_supported

    except Exception as e:
        print(f"❌ Error checking data: {e}")
        print("🔧 Potential fixes:")
        print("  1. Check BigQuery connection")
        print("  2. Verify dataset permissions")
        print("  3. Ensure bigquery_utils.py is working")
        return None, None


def check_data_quality():
    """Check for data quality issues."""
    print("\n🔍 DATA QUALITY CHECKS")
    print("=" * 30)

    try:
        client = bigquery.Client(project="jibber-jabber-knowledge")

        # Check for tables with no recent data
        staleness_query = """
        SELECT
          table_name,
          MAX(DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\d{8})')))) as latest_date,
          DATE_DIFF(CURRENT_DATE(), MAX(DATE(PARSE_TIMESTAMP('%Y%m%d', REGEXP_EXTRACT(partition_id, r'(\\d{8})')))), DAY) as days_stale
        FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.PARTITIONS`
        WHERE table_name LIKE 'bmrs_%'
          AND partition_id IS NOT NULL
          AND partition_id != '__NULL__'
          AND REGEXP_CONTAINS(partition_id, r'^\\d{8}$')
        GROUP BY table_name
        HAVING days_stale > 30
        ORDER BY days_stale DESC
        """

        stale_results = client.query(staleness_query).result()
        stale_tables = list(stale_results)

        if stale_tables:
            print(f"⚠️  Found {len(stale_tables)} tables with stale data:")
            for row in stale_tables:
                print(
                    f"  {row.table_name}: {row.days_stale} days old (latest: {row.latest_date})"
                )
        else:
            print("✅ All tables have recent data")

    except Exception as e:
        print(f"❌ Error checking data quality: {e}")


def main():
    """Main health check routine."""
    year_data, total_supported = check_data_completeness()
    check_data_quality()

    print("\n🎯 NEXT STEPS:")
    if year_data:
        incomplete_years = [
            year
            for year in [2022, 2023, 2024, 2025]
            if year_data.get(year, 0) < max(year_data.values())
        ]

        if incomplete_years:
            print("1. Review the repair recommendations above")
            print("2. For 2022: Run 'python complete_2022_datasets.py' for commands")
            print("3. For other years: Investigate why datasets are missing")
            print("4. Monitor ingestion progress with this script")
        else:
            print("1. ✅ All years appear complete!")
            print("2. Consider running data validation checks")
            print("3. Monitor for ongoing data freshness")
    else:
        print("1. Fix BigQuery connection issues")
        print("2. Re-run this health check")


if __name__ == "__main__":
    main()
