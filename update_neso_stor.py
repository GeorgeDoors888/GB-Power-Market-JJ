#!/usr/bin/env python3
"""
NESO Portal Data Updater
Updates STOR (Short-Term Operating Reserves) data from NESO Portal
Runs daily to fetch latest auction results and service windows
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

# NESO datasets to update
NESO_STOR_DATASETS = [
    "short-term-operating-reserve-stor-day-ahead-auction-results",
    "short-term-operating-reserve-stor-day-ahead-buy-curve",
    "short-term-operating-reserve-stor-service-windows",
]


class NESOUpdater:
    def __init__(self, log_file: Optional[str] = None):
        self.setup_logging(log_file)
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.stats = {
            "datasets_processed": 0,
            "total_rows_added": 0,
            "errors": [],
            "start_time": datetime.now(timezone.utc),
        }
        self.neso_script = os.path.join(SCRIPT_DIR, "ingest_stor_neso.py")
        self.venv_python = os.path.join(SCRIPT_DIR, "gsheets_env", "bin", "python")

    def setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration"""
        log_format = "%(asctime)s - NESO_UPDATER - %(levelname)s - %(message)s"

        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file, mode="a"))

        logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

        self.logger = logging.getLogger(__name__)

    def get_table_info(self, table_name: str) -> Dict:
        """Get information about existing NESO table"""
        try:
            query = f"""
            SELECT
                COUNT(*) as row_count,
                MAX(_ingested_utc) as last_ingested
            FROM `jibber-jabber-knowledge.uk_energy_insights.{table_name}`
            """

            result = self.client.query(query)
            for row in result:
                return {
                    "row_count": row.row_count,
                    "last_ingested": (
                        row.last_ingested.replace(tzinfo=timezone.utc)
                        if row.last_ingested
                        else None
                    ),
                }

            return {"row_count": 0, "last_ingested": None}

        except Exception as e:
            self.logger.warning(f"Could not get info for {table_name}: {e}")
            return {"row_count": 0, "last_ingested": None}

    def should_update_dataset(self, table_name: str) -> bool:
        """Determine if a NESO dataset should be updated"""
        info = self.get_table_info(table_name)

        # Always update if no data exists
        if info["row_count"] == 0:
            self.logger.info(f"{table_name}: No existing data, will update")
            return True

        # Update if last ingestion was more than 6 hours ago
        if info["last_ingested"]:
            hours_since_update = (
                datetime.now(timezone.utc) - info["last_ingested"]
            ).total_seconds() / 3600
            if hours_since_update > 6:
                self.logger.info(
                    f"{table_name}: Last updated {hours_since_update:.1f} hours ago, will update"
                )
                return True
            else:
                self.logger.info(
                    f"{table_name}: Recently updated ({hours_since_update:.1f} hours ago), skipping"
                )
                return False

        # Default to update if we can't determine last update time
        self.logger.info(
            f"{table_name}: Cannot determine last update time, will update"
        )
        return True

    def update_neso_data(self) -> Dict:
        """Update all NESO STOR datasets"""
        self.logger.info("Starting NESO STOR data update")

        try:
            # Call the NESO ingestion script
            cmd = [self.venv_python, self.neso_script]

            self.logger.info(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                cwd=SCRIPT_DIR,
            )

            if result.returncode == 0:
                # Parse output for statistics
                output = result.stdout + result.stderr
                rows_added = self._parse_rows_from_output(output)

                return {
                    "status": "success",
                    "rows_added": rows_added,
                    "output": output[-1000:],  # Last 1000 chars
                }
            else:
                error_msg = f"NESO ingestion failed: {result.stderr}"
                self.logger.error(error_msg)

                return {"status": "error", "error": error_msg, "rows_added": 0}

        except subprocess.TimeoutExpired:
            error_msg = "NESO update timed out after 30 minutes"
            self.logger.error(error_msg)
            return {"status": "timeout", "error": error_msg, "rows_added": 0}
        except Exception as e:
            error_msg = f"Failed to update NESO data: {str(e)}"
            self.logger.error(error_msg)
            return {"status": "error", "error": str(e), "rows_added": 0}

    def _parse_rows_from_output(self, output: str) -> int:
        """Parse number of rows added from NESO ingestion output"""
        try:
            # Look for patterns specific to NESO ingestion
            import re

            patterns = [
                r"Successfully uploaded (\d+) rows",
                r"Uploaded (\d+) rows",
                r"Added (\d+) rows",
                r"(\d+) rows.*uploaded",
                r"Total: (\d+) rows",
            ]

            total_rows = 0
            for pattern in patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    total_rows += sum(int(match) for match in matches)

            return total_rows
        except:
            return 0

    def run_update(self) -> Dict:
        """Run the complete NESO update process"""
        self.logger.info("Starting NESO data update process")

        # Check which datasets need updating
        update_needed = False
        for dataset_id in NESO_STOR_DATASETS:
            # Map dataset ID to table name
            table_name = f"neso_{dataset_id.replace('-', '_')}"
            if self.should_update_dataset(table_name):
                update_needed = True
                break

        if not update_needed:
            self.logger.info("All NESO datasets are up to date, skipping update")
            return {
                "summary": {
                    "status": "skipped",
                    "reason": "all_up_to_date",
                    "datasets_processed": 0,
                    "total_rows_added": 0,
                    "errors": [],
                    "total_duration": 0,
                }
            }

        # Run the update
        result = self.update_neso_data()

        # Update statistics
        if result["status"] == "success":
            self.stats["datasets_processed"] = len(NESO_STOR_DATASETS)
            self.stats["total_rows_added"] = result.get("rows_added", 0)
        else:
            self.stats["errors"].append(result.get("error", "Unknown error"))

        # Calculate final statistics
        self.stats["end_time"] = datetime.now(timezone.utc)
        self.stats["total_duration"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()

        return {"summary": {**self.stats, "status": result["status"]}, "result": result}

    def log_summary(self, results: Dict):
        """Log a summary of the update process"""
        summary = results["summary"]

        self.logger.info("=" * 50)
        self.logger.info("NESO DATA UPDATE SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Status: {summary['status']}")
        self.logger.info(f"Datasets Processed: {summary['datasets_processed']}")
        self.logger.info(f"Total Rows Added: {summary['total_rows_added']:,}")
        self.logger.info(f"Total Duration: {summary['total_duration']:.1f}s")
        self.logger.info(f"Errors: {len(summary['errors'])}")

        if summary["errors"]:
            self.logger.error("ERRORS ENCOUNTERED:")
            for error in summary["errors"]:
                self.logger.error(f"  - {error}")

        # Log result details
        if "result" in results:
            result = results["result"]
            status_emoji = (
                "✅"
                if result["status"] == "success"
                else "⚠️" if result["status"] == "skipped" else "❌"
            )
            self.logger.info(f"\n{status_emoji} NESO STOR Update: {result['status']}")
            if result.get("rows_added", 0) > 0:
                self.logger.info(f"   Rows Added: {result['rows_added']:,}")

        self.logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="NESO Portal Data Updater")
    parser.add_argument("--log-file", help="Path to log file for output")
    parser.add_argument(
        "--force", action="store_true", help="Force update even if data appears current"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    updater = NESOUpdater(args.log_file)

    if args.dry_run:
        updater.logger.info("DRY RUN MODE - No data will be updated")
        for dataset_id in NESO_STOR_DATASETS:
            table_name = f"neso_{dataset_id.replace('-', '_')}"
            if updater.should_update_dataset(table_name):
                updater.logger.info(f"Would update: {dataset_id}")
            else:
                updater.logger.info(f"Would skip: {dataset_id} (up to date)")
        return

    try:
        results = updater.run_update()
        updater.log_summary(results)

        # Exit with error code if there were failures
        if results["summary"]["errors"]:
            sys.exit(1)

    except Exception as e:
        updater.logger.error(f"Critical failure in NESO updater: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
