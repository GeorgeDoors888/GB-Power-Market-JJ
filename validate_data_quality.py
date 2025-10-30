#!/usr/bin/env python3
"""
Data Quality Validation Script
Validates data quality after updates and reports anomalies
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Import BigQuery client
from google.cloud import bigquery


class DataQualityValidator:
    def __init__(self, log_file: Optional[str] = None):
        self.setup_logging(log_file)
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.issues = []
        self.warnings = []
        self.validation_results = {}

    def setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration"""
        log_format = "%(asctime)s - DATA_VALIDATOR - %(levelname)s - %(message)s"

        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file, mode="a"))

        logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

        self.logger = logging.getLogger(__name__)

    def check_table_freshness(
        self, table_pattern: str, max_age_hours: int = 24
    ) -> Dict:
        """Check if tables have been updated recently"""
        self.logger.info(f"Checking freshness of tables matching: {table_pattern}")

        query = f"""
        SELECT
            table_name,
            MAX(_ingested_utc) as last_ingested,
            MAX(_window_to_utc) as last_data_window,
            COUNT(*) as row_count
        FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES` t
        JOIN `jibber-jabber-knowledge.uk_energy_insights.*` data
        WHERE t.table_name LIKE '{table_pattern}'
        AND t.table_type = 'BASE_TABLE'
        GROUP BY table_name
        ORDER BY table_name
        """

        try:
            results = self.client.query(query)
            stale_tables = []
            current_time = datetime.now(timezone.utc)
            tables_checked = 0

            for row in results:
                tables_checked += 1
                table_name = row.table_name
                last_ingested = row.last_ingested
                last_data_window = row.last_data_window
                row_count = row.row_count

                if last_ingested:
                    hours_since_update = (
                        current_time - last_ingested.replace(tzinfo=timezone.utc)
                    ).total_seconds() / 3600

                    if hours_since_update > max_age_hours:
                        stale_tables.append(
                            {
                                "table": table_name,
                                "hours_stale": hours_since_update,
                                "last_ingested": last_ingested.isoformat(),
                                "row_count": row_count,
                            }
                        )
                        self.issues.append(
                            f"Table {table_name} is {hours_since_update:.1f} hours stale"
                        )
                else:
                    stale_tables.append(
                        {
                            "table": table_name,
                            "hours_stale": float("inf"),
                            "last_ingested": None,
                            "row_count": row_count,
                        }
                    )
                    self.issues.append(f"Table {table_name} has no ingestion timestamp")

            return {
                "status": "error" if stale_tables else "ok",
                "stale_tables": stale_tables,
                "total_checked": tables_checked,
            }

        except Exception as e:
            error_msg = f"Failed to check table freshness: {e}"
            self.logger.error(error_msg)
            self.issues.append(error_msg)
            return {"status": "error", "error": str(e)}

    def check_data_completeness(
        self, table_name: str, expected_frequency_minutes: int = 30
    ) -> Dict:
        """Check for gaps in time series data"""
        self.logger.info(f"Checking data completeness for: {table_name}")

        # Get the time range of data
        query = f"""
        WITH time_gaps AS (
            SELECT
                _window_from_utc as current_time,
                LAG(_window_to_utc) OVER (ORDER BY _window_from_utc) as previous_end,
                DATETIME_DIFF(_window_from_utc, LAG(_window_to_utc) OVER (ORDER BY _window_from_utc), MINUTE) as gap_minutes
            FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
            WHERE _window_from_utc IS NOT NULL
            AND _window_to_utc IS NOT NULL
            AND _window_from_utc >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            ORDER BY _window_from_utc
        )
        SELECT
            COUNT(*) as total_periods,
            COUNT(CASE WHEN gap_minutes > {expected_frequency_minutes * 2} THEN 1 END) as significant_gaps,
            MAX(gap_minutes) as max_gap_minutes,
            AVG(gap_minutes) as avg_gap_minutes
        FROM time_gaps
        WHERE gap_minutes IS NOT NULL
        """

        try:
            result = self.client.query(query)
            for row in result:
                total_periods = row.total_periods
                significant_gaps = row.significant_gaps
                max_gap_minutes = row.max_gap_minutes
                avg_gap_minutes = row.avg_gap_minutes

                if significant_gaps > 0:
                    self.warnings.append(
                        f"Table {table_name} has {significant_gaps} significant gaps out of {total_periods} periods"
                    )

                return {
                    "status": "warning" if significant_gaps > 0 else "ok",
                    "total_periods": total_periods,
                    "significant_gaps": significant_gaps,
                    "max_gap_minutes": max_gap_minutes,
                    "avg_gap_minutes": avg_gap_minutes,
                }

            return {"status": "ok", "total_periods": 0, "significant_gaps": 0}

        except Exception as e:
            error_msg = f"Failed to check completeness for {table_name}: {e}"
            self.logger.error(error_msg)
            self.issues.append(error_msg)
            return {"status": "error", "error": str(e)}

    def check_duplicate_data(self, table_name: str) -> Dict:
        """Check for duplicate data based on hash keys"""
        self.logger.info(f"Checking for duplicates in: {table_name}")

        query = f"""
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT _hash_key) as unique_hashes,
            COUNT(*) - COUNT(DISTINCT _hash_key) as duplicate_count
        FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
        WHERE _hash_key IS NOT NULL
        """

        try:
            result = self.client.query(query)
            for row in result:
                total_rows = row.total_rows
                unique_hashes = row.unique_hashes
                duplicate_count = row.duplicate_count

                if duplicate_count > 0:
                    self.warnings.append(
                        f"Table {table_name} has {duplicate_count} duplicate rows out of {total_rows} total"
                    )

                return {
                    "status": "warning" if duplicate_count > 0 else "ok",
                    "total_rows": total_rows,
                    "unique_hashes": unique_hashes,
                    "duplicate_count": duplicate_count,
                }

            return {
                "status": "ok",
                "total_rows": 0,
                "unique_hashes": 0,
                "duplicate_count": 0,
            }

        except Exception as e:
            error_msg = f"Failed to check duplicates for {table_name}: {e}"
            self.logger.error(error_msg)
            self.issues.append(error_msg)
            return {"status": "error", "error": str(e)}

    def check_data_ranges(self, table_name: str, numeric_columns: List[str]) -> Dict:
        """Check for unrealistic values in numeric columns"""
        self.logger.info(f"Checking data ranges for: {table_name}")

        range_checks = {}

        for column in numeric_columns:
            query = f"""
            SELECT
                MIN({column}) as min_value,
                MAX({column}) as max_value,
                AVG({column}) as avg_value,
                STDDEV({column}) as stddev_value,
                COUNT(CASE WHEN {column} IS NULL THEN 1 END) as null_count,
                COUNT(*) as total_count
            FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
            WHERE _window_from_utc >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
            """

            try:
                result = self.client.query(query)
                for row in result:
                    min_val = row.min_value
                    max_val = row.max_value
                    avg_val = row.avg_value
                    stddev_val = row.stddev_value
                    null_count = row.null_count
                    total_count = row.total_count

                    # Check for obviously wrong values
                    issues = []
                    if (
                        min_val is not None
                        and min_val < 0
                        and "price" not in column.lower()
                    ):
                        issues.append(f"Negative values found (min: {min_val})")

                    if null_count > total_count * 0.5:  # More than 50% nulls
                        issues.append(
                            f"High null percentage: {null_count}/{total_count} ({null_count/total_count*100:.1f}%)"
                        )

                    range_checks[column] = {
                        "min": min_val,
                        "max": max_val,
                        "avg": avg_val,
                        "stddev": stddev_val,
                        "null_count": null_count,
                        "total_count": total_count,
                        "issues": issues,
                    }

                    if issues:
                        for issue in issues:
                            self.warnings.append(
                                f"Table {table_name}.{column}: {issue}"
                            )

            except Exception as e:
                error_msg = f"Failed to check ranges for {table_name}.{column}: {e}"
                self.logger.warning(error_msg)
                range_checks[column] = {"error": str(e)}

        return {"status": "ok", "column_checks": range_checks}

    def validate_high_priority_tables(self) -> Dict:
        """Validate high-priority BMRS tables"""
        high_priority_tables = [
            ("bmrs_freq", 15, ["frequency"]),
            ("bmrs_fuelinst", 15, []),
            ("bmrs_bod", 15, []),
            ("bmrs_boalf", 15, []),
            ("bmrs_costs", 30, ["systemSellPrice", "systemBuyPrice"]),
            ("bmrs_disbsad", 30, []),
        ]

        results = {}

        for table_name, max_age_hours, numeric_cols in high_priority_tables:
            self.logger.info(f"Validating {table_name}...")

            table_results = {}

            # Check freshness
            table_results["freshness"] = self.check_table_freshness(
                table_name, max_age_hours
            )

            # Check completeness
            table_results["completeness"] = self.check_data_completeness(table_name, 30)

            # Check duplicates
            table_results["duplicates"] = self.check_duplicate_data(table_name)

            # Check data ranges if numeric columns specified
            if numeric_cols:
                table_results["ranges"] = self.check_data_ranges(
                    table_name, numeric_cols
                )

            results[table_name] = table_results

        return results

    def validate_neso_tables(self) -> Dict:
        """Validate NESO tables"""
        neso_tables = [
            "neso_stor_auction_results",
            "neso_stor_buy_curve",
            "neso_stor_windows",
        ]

        results = {}

        for table_name in neso_tables:
            self.logger.info(f"Validating {table_name}...")

            table_results = {}

            # Check freshness (NESO data updated daily)
            table_results["freshness"] = self.check_table_freshness(table_name, 48)

            # Check duplicates
            table_results["duplicates"] = self.check_duplicate_data(table_name)

            results[table_name] = table_results

        return results

    def run_validation(self) -> Dict:
        """Run complete data validation"""
        self.logger.info("Starting data quality validation")

        validation_start = datetime.now(timezone.utc)

        # Validate high-priority BMRS tables
        self.logger.info("Validating high-priority BMRS tables...")
        bmrs_results = self.validate_high_priority_tables()

        # Validate NESO tables
        self.logger.info("Validating NESO tables...")
        neso_results = self.validate_neso_tables()

        validation_end = datetime.now(timezone.utc)
        duration = (validation_end - validation_start).total_seconds()

        return {
            "summary": {
                "start_time": validation_start.isoformat(),
                "end_time": validation_end.isoformat(),
                "duration_seconds": duration,
                "total_issues": len(self.issues),
                "total_warnings": len(self.warnings),
                "issues": self.issues,
                "warnings": self.warnings,
            },
            "bmrs_validation": bmrs_results,
            "neso_validation": neso_results,
        }

    def log_summary(self, results: Dict):
        """Log validation summary"""
        summary = results["summary"]

        self.logger.info("=" * 50)
        self.logger.info("DATA QUALITY VALIDATION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Duration: {summary['duration_seconds']:.1f}s")
        self.logger.info(f"Issues: {summary['total_issues']}")
        self.logger.info(f"Warnings: {summary['total_warnings']}")

        if summary["issues"]:
            self.logger.error("CRITICAL ISSUES:")
            for issue in summary["issues"]:
                self.logger.error(f"  ❌ {issue}")

        if summary["warnings"]:
            self.logger.warning("WARNINGS:")
            for warning in summary["warnings"]:
                self.logger.warning(f"  ⚠️  {warning}")

        if not summary["issues"] and not summary["warnings"]:
            self.logger.info("✅ All data quality checks passed!")

        self.logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Data Quality Validator")
    parser.add_argument("--log-file", help="Path to log file for output")
    parser.add_argument("--output-json", help="Path to save detailed results as JSON")

    args = parser.parse_args()

    validator = DataQualityValidator(args.log_file)

    try:
        results = validator.run_validation()
        validator.log_summary(results)

        # Save detailed results if requested
        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump(results, f, indent=2, default=str)
            validator.logger.info(f"Detailed results saved to: {args.output_json}")

        # Exit with error code if there were critical issues
        if results["summary"]["total_issues"] > 0:
            sys.exit(1)

    except Exception as e:
        validator.logger.error(f"Critical failure in data validator: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
