#!/usr/bin/env python3
"""
Daily Priority BMRS Data Updater
Updates low-frequency BMRS datasets once per day at 06:00
Focuses on daily forecasts and aggregated data
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Import BigQuery client
from google.cloud import bigquery

# Daily priority datasets for once-per-day updates
DAILY_PRIORITY_DATASETS = [
    "NDF",  # Day-ahead national demand forecast
    "TSDF",  # Transmission system demand forecast
    "FUELHH",  # Half-hourly fuel mix aggregates
    "INDDEM",  # Indicative demand data
    "INDGEN",  # Indicative generation data
    "NONBM",  # Non-BM STOR data
    "RDRI",  # Replacement reserve data
]


class DailyPriorityUpdater:
    def __init__(self, log_file: Optional[str] = None):
        self.setup_logging(log_file)
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.stats = {
            "datasets_processed": 0,
            "total_rows_added": 0,
            "total_windows_processed": 0,
            "errors": [],
            "start_time": datetime.now(timezone.utc),
        }
        self.ingestion_script = os.path.join(SCRIPT_DIR, "ingest_elexon_fixed.py")
        self.venv_python = os.path.join(SCRIPT_DIR, ".venv_ingestion", "bin", "python")

    def setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration"""
        log_format = "%(asctime)s - DAILY_PRIORITY - %(levelname)s - %(message)s"

        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file, mode="a"))

        logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

        self.logger = logging.getLogger(__name__)

    def get_last_update_time(self, dataset: str) -> datetime:
        """Get the last update timestamp for a dataset"""
        try:
            query = f"""
            SELECT MAX(_window_to_utc) as last_update
            FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_{dataset.lower()}`
            WHERE _window_to_utc IS NOT NULL
            """

            result = self.client.query(query)
            for row in result:
                if row.last_update:
                    return row.last_update.replace(tzinfo=timezone.utc)

            # If no data exists, start from 7 days ago
            return datetime.now(timezone.utc) - timedelta(days=7)

        except Exception as e:
            self.logger.warning(f"Could not get last update for {dataset}: {e}")
            # Default to 3 days ago for safety
            return datetime.now(timezone.utc) - timedelta(days=3)

    def calculate_update_window(self, dataset: str) -> tuple:
        """Calculate the time window to update for a dataset"""
        last_update = self.get_last_update_time(dataset)

        # Add 1 day buffer for daily data
        window_start = last_update - timedelta(days=1)

        # End time is current time minus 1 hour (daily data often has delays)
        window_end = datetime.now(timezone.utc) - timedelta(hours=1)

        # For daily data, ensure we have at least 1 day to fetch
        if window_end - window_start < timedelta(hours=12):
            self.logger.warning(f"Dataset {dataset} appears up to date, skipping")
            return None, None

        return window_start, window_end

    def update_dataset(self, dataset: str) -> Dict:
        """Update a single daily-priority dataset"""
        self.logger.info(f"Starting update for dataset: {dataset}")

        window_start, window_end = self.calculate_update_window(dataset)

        if window_start is None:
            return {
                "dataset": dataset,
                "status": "skipped",
                "reason": "already_up_to_date",
                "windows_processed": 0,
                "rows_added": 0,
            }

        # Format dates for API
        start_date = window_start.strftime("%Y-%m-%d")
        end_date = window_end.strftime("%Y-%m-%d")

        self.logger.info(f"Updating {dataset} from {start_date} to {end_date}")

        try:
            # Call existing ingestion script
            cmd = [
                self.venv_python,
                self.ingestion_script,
                "--start",
                start_date,
                "--end",
                end_date,
                "--only",
                dataset,
                "--log-level",
                "INFO",
                "--project",
                "jibber-jabber-knowledge",
                "--dataset",
                "uk_energy_insights",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout for daily datasets
            )

            if result.returncode == 0:
                # Parse output for statistics
                output = result.stdout + result.stderr
                rows_added = self._parse_rows_from_output(output)

                return {
                    "dataset": dataset,
                    "status": "success",
                    "windows_processed": 1,  # Estimate
                    "rows_added": rows_added,
                    "output": output[-500:],  # Last 500 chars
                }
            else:
                error_msg = f"Ingestion failed: {result.stderr}"
                self.logger.error(error_msg)

                return {
                    "dataset": dataset,
                    "status": "error",
                    "error": error_msg,
                    "windows_processed": 0,
                    "rows_added": 0,
                }

        except subprocess.TimeoutExpired:
            error_msg = f"Update timed out after 30 minutes"
            self.logger.error(error_msg)
            return {
                "dataset": dataset,
                "status": "timeout",
                "error": error_msg,
                "windows_processed": 0,
                "rows_added": 0,
            }
        except Exception as e:
            error_msg = f"Failed to update {dataset}: {str(e)}"
            self.logger.error(error_msg)
            self.stats["errors"].append(error_msg)

            return {
                "dataset": dataset,
                "status": "error",
                "error": str(e),
                "windows_processed": 0,
                "rows_added": 0,
            }

    def _parse_rows_from_output(self, output: str) -> int:
        """Parse number of rows added from ingestion output"""
        try:
            # Look for patterns like "Loaded X rows" or "Added X rows"
            import re

            patterns = [
                r"Loaded (\d+) rows",
                r"Added (\d+) rows",
                r"(\d+) rows.*loaded",
                r"Total rows: (\d+)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    return max(int(match) for match in matches)

            return 0
        except:
            return 0

    def run_updates(self) -> Dict:
        """Run updates for all daily-priority datasets"""
        self.logger.info(
            f"Starting daily-priority updates for {len(DAILY_PRIORITY_DATASETS)} datasets"
        )

        results = []

        for dataset in DAILY_PRIORITY_DATASETS:
            try:
                result = self.update_dataset(dataset)
                results.append(result)

                # Update statistics
                if result["status"] == "success":
                    self.stats["datasets_processed"] += 1
                    self.stats["total_rows_added"] += result.get("rows_added", 0)
                    self.stats["total_windows_processed"] += result.get(
                        "windows_processed", 0
                    )

            except Exception as e:
                error_msg = f"Critical error updating {dataset}: {str(e)}"
                self.logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                results.append(
                    {"dataset": dataset, "status": "critical_error", "error": str(e)}
                )

        # Calculate final statistics
        self.stats["end_time"] = datetime.now(timezone.utc)
        self.stats["total_duration"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()

        return {"summary": self.stats, "results": results}

    def log_summary(self, results: Dict):
        """Log a summary of the update process"""
        summary = results["summary"]

        self.logger.info("=" * 50)
        self.logger.info("DAILY PRIORITY UPDATE SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(
            f"Datasets Processed: {summary['datasets_processed']}/{len(DAILY_PRIORITY_DATASETS)}"
        )
        self.logger.info(f"Total Rows Added: {summary['total_rows_added']:,}")
        self.logger.info(
            f"Total Windows Processed: {summary['total_windows_processed']}"
        )
        self.logger.info(f"Total Duration: {summary['total_duration']:.1f}s")
        self.logger.info(f"Errors: {len(summary['errors'])}")

        if summary["errors"]:
            self.logger.error("ERRORS ENCOUNTERED:")
            for error in summary["errors"]:
                self.logger.error(f"  - {error}")

        # Log individual dataset results
        self.logger.info("\nDETAILED RESULTS:")
        for result in results["results"]:
            status_emoji = (
                "✅"
                if result["status"] == "success"
                else "⚠️" if result["status"] == "skipped" else "❌"
            )
            self.logger.info(
                f"  {status_emoji} {result['dataset']}: {result['status']} "
                f"({result.get('rows_added', 0):,} rows, {result.get('windows_processed', 0)} windows)"
            )

        self.logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Daily Priority BMRS Data Updater")
    parser.add_argument("--log-file", help="Path to log file for output")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DAILY_PRIORITY_DATASETS,
        help="Specific datasets to update (default: all daily priority)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    # Override datasets if specified
    global DAILY_PRIORITY_DATASETS
    DAILY_PRIORITY_DATASETS = args.datasets

    updater = DailyPriorityUpdater(args.log_file)

    if args.dry_run:
        updater.logger.info("DRY RUN MODE - No data will be updated")
        for dataset in DAILY_PRIORITY_DATASETS:
            window_start, window_end = updater.calculate_update_window(dataset)
            if window_start:
                updater.logger.info(
                    f"Would update {dataset}: {window_start.isoformat()} to {window_end.isoformat()}"
                )
            else:
                updater.logger.info(f"Would skip {dataset}: already up to date")
        return

    try:
        results = updater.run_updates()
        updater.log_summary(results)

        # Exit with error code if there were failures
        if results["summary"]["errors"]:
            sys.exit(1)

    except Exception as e:
        updater.logger.error(f"Critical failure in daily priority updater: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
