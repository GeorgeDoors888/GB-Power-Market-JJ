#!/usr/bin/env python3
"""
Standard Priority BMRS Data Updater
Updates moderate-frequency BMRS datasets every 30 minutes (offset by 15 minutes)
Focuses on settlement and balancing data that updates every 30 minutes
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

# Standard priority datasets for 30-minute updates
STANDARD_PRIORITY_DATASETS = [
    "MELS",  # Meter Energy/Loss Settlement (30-minute)
    "MILS",  # Meter Incremental/Loss Settlement (30-minute)
    "QAS",  # Quiescent Acceptance/Settlement (30-minute)
    "NETBSAD",  # Net Balancing Services Adjustment (30-minute)
    "PN",  # Physical Notifications (real-time but lower priority)
    "QPN",  # Quiescent Physical Notifications (real-time but lower priority)
]


class StandardPriorityUpdater:
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
        log_format = "%(asctime)s - STANDARD_PRIORITY - %(levelname)s - %(message)s"

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

            # If no data exists, start from 24 hours ago
            return datetime.now(timezone.utc) - timedelta(hours=24)

        except Exception as e:
            self.logger.warning(f"Could not get last update for {dataset}: {e}")
            # Default to 6 hours ago for safety
            return datetime.now(timezone.utc) - timedelta(hours=6)

    def calculate_update_window(self, dataset: str) -> tuple:
        """Calculate the time window to update for a dataset - LAST 30 MINUTES ONLY"""
        now = datetime.now(timezone.utc)

        # Target the last 30-minute period ending 10 minutes ago (settlement data has delays)
        window_end = now - timedelta(minutes=10)
        window_start = window_end - timedelta(minutes=30)

        # Check if we already have recent data (within last 45 minutes)
        last_update = self.get_last_update_time(dataset)
        time_since_last_update = now - last_update

        if time_since_last_update < timedelta(minutes=45):
            self.logger.warning(
                f"Dataset {dataset} updated {time_since_last_update} ago, skipping (data is current)"
            )
            return None, None

        self.logger.info(
            f"Fetching {dataset} for last 30-min window: {window_start.strftime('%Y-%m-%d %H:%M')} to {window_end.strftime('%Y-%m-%d %H:%M')}"
        )
        return window_start, window_end

    def update_dataset(self, dataset: str) -> Dict:
        """Update a single standard-priority dataset"""
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

            # Add include-offline for MELS/MILS
            if dataset in ["MELS", "MILS"]:
                cmd.append("--include-offline")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout for larger datasets
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
            error_msg = f"Update timed out after 15 minutes"
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
        """Run updates for all standard-priority datasets"""
        self.logger.info(
            f"Starting standard-priority updates for {len(STANDARD_PRIORITY_DATASETS)} datasets"
        )

        results = []

        for dataset in STANDARD_PRIORITY_DATASETS:
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
        self.logger.info("STANDARD PRIORITY UPDATE SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(
            f"Datasets Processed: {summary['datasets_processed']}/{len(STANDARD_PRIORITY_DATASETS)}"
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
    parser = argparse.ArgumentParser(description="Standard Priority BMRS Data Updater")
    parser.add_argument("--log-file", help="Path to log file for output")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=STANDARD_PRIORITY_DATASETS,
        help="Specific datasets to update (default: all standard priority)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    # Override datasets if specified
    global STANDARD_PRIORITY_DATASETS
    STANDARD_PRIORITY_DATASETS = args.datasets

    updater = StandardPriorityUpdater(args.log_file)

    if args.dry_run:
        updater.logger.info("DRY RUN MODE - No data will be updated")
        for dataset in STANDARD_PRIORITY_DATASETS:
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
        updater.logger.error(f"Critical failure in standard priority updater: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
