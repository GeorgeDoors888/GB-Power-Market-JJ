#!/usr/bin/env python3
"""
15-Minute Update System for All Data Sources (Dry-Run Compatible Version)

This script coordinates the 15-minute updates for all data sources:
1. Elexon BMRS data (through ingest_elexon_fixed.py)
2. REMIT data (through ingest_remit.py)
3. NESO data (through neso_data_updater.py)

It ensures that all data sources are updated efficiently with appropriate timing.
This version is modified to work in dry-run mode without Google Sheets authentication.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

# Load environment variables for Google Sheets API
from dotenv import load_dotenv

# Try to load from google_sheets.env if it exists
if os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_sheets.env")
):
    load_dotenv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_sheets.env")
    )
else:
    load_dotenv()  # Fall back to .env if google_sheets.env doesn't exist

# Import the dry run compatible data tracker
from automated_data_tracker_dryrun import DataTracker

try:
    from neso_data_updater import NESODataUpdater

    NESO_AVAILABLE = True
except ImportError:
    NESO_AVAILABLE = False
    print("Warning: NESO data updater not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("15_minute_update.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Constants
ELEXON_HIGH_PRIORITY = ["FREQ", "FUELINST", "BOD", "BOALF", "COSTS", "DISBSAD"]
ELEXON_STANDARD_PRIORITY = ["MELS", "MILS", "QAS", "NETBSAD", "PN", "QPN"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_command(command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a command and return its output"""
    logger.info(f"Running command: {' '.join(command)}")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd or SCRIPT_DIR,
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        logger.error(f"Failed to run command: {e}")
        return 1, "", str(e)


def calculate_elexon_time_window() -> Tuple[str, str, int]:
    """
    Calculate the optimal time window for Elexon BMRS data

    Returns:
        Tuple of (start_time, end_time, window_minutes)
    """
    now = datetime.now(timezone.utc)

    # For high priority data, use a 15-minute window ending 5 minutes ago
    # This ensures we have the latest data that has been fully processed
    end_time = now - timedelta(minutes=5)
    start_time = end_time - timedelta(minutes=15)

    # Format times for the command
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

    return start_str, end_str, 15


def update_elexon_data(
    only_datasets: Optional[List[str]] = None, dry_run: bool = False
) -> Dict[str, Any]:
    """Update Elexon BMRS data"""
    start_time = datetime.now()

    try:
        # Get time window
        start_str, end_str, window_minutes = calculate_elexon_time_window()

        # Build command
        command = [
            "python",
            os.path.join(SCRIPT_DIR, "ingest_elexon_fixed.py"),
            "--start",
            start_str,
            "--end",
            end_str,
        ]

        if only_datasets:
            command.extend(["--only", ",".join(only_datasets)])

        if dry_run:
            command.append("--dry-run")

        # Add options for more efficient processing
        command.extend(
            ["--log-level", "INFO", "--use-staging-table", "--monitor-progress"]
        )

        # Run the command
        returncode, stdout, stderr = run_command(command)

        # Process results
        execution_time = (datetime.now() - start_time).total_seconds()
        result = {
            "success": returncode == 0,
            "datasets": only_datasets or "all",
            "window": {
                "start": start_str,
                "end": end_str,
                "minutes": window_minutes,
            },
            "execution_time_seconds": execution_time,
            "return_code": returncode,
        }

        if returncode != 0:
            logger.error(f"Elexon update failed with code {returncode}")
            logger.error(f"Error: {stderr}")
            result["error"] = stderr.strip()
        else:
            logger.info(f"Elexon update completed in {execution_time:.1f} seconds")

        return result

    except Exception as e:
        logger.error(f"Error in Elexon update: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
        }


def update_remit_data(dry_run: bool = False) -> Dict[str, Any]:
    """Update REMIT data"""
    start_time = datetime.now()

    try:
        # Build command
        command = [
            "python",
            os.path.join(SCRIPT_DIR, "ingest_remit.py"),
        ]

        if dry_run:
            command.append("--check-only")

        # Run the command
        returncode, stdout, stderr = run_command(command)

        # Process results
        execution_time = (datetime.now() - start_time).total_seconds()
        result = {
            "success": returncode == 0,
            "execution_time_seconds": execution_time,
            "return_code": returncode,
        }

        if returncode != 0:
            logger.error(f"REMIT update failed with code {returncode}")
            logger.error(f"Error: {stderr}")
            result["error"] = stderr.strip()
        else:
            logger.info(f"REMIT update completed in {execution_time:.1f} seconds")

        return result

    except Exception as e:
        logger.error(f"Error in REMIT update: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
        }


def update_neso_data(dry_run: bool = False) -> Dict[str, Any]:
    """Update NESO data"""
    start_time = datetime.now()

    if not NESO_AVAILABLE:
        logger.warning("NESO data updater not available. Skipping NESO update.")
        return {
            "success": False,
            "error": "NESO data updater not available",
            "execution_time_seconds": 0,
        }

    try:
        # Use the NESO data updater directly
        updater = NESODataUpdater()
        result = updater.update_neso_data()

        # Process results
        execution_time = (datetime.now() - start_time).total_seconds()
        success = result.get("action") not in ["error", "skip"]

        output = {
            "success": success,
            "action": result.get("action", "unknown"),
            "execution_time_seconds": execution_time,
        }

        if not success and "error" in result:
            logger.error(f"NESO update failed: {result['error']}")
            output["error"] = result["error"]
        else:
            logger.info(f"NESO update completed in {execution_time:.1f} seconds")

        return output

    except Exception as e:
        logger.error(f"Error in NESO update: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
        }


def update_latest_energy_data(dry_run: bool = False) -> Dict[str, Any]:
    """Generate the latest energy data snapshot"""
    start_time = datetime.now()

    try:
        # Build command
        command = [
            "python",
            os.path.join(SCRIPT_DIR, "get_latest_energy_data.py"),
        ]

        # Run the command
        returncode, stdout, stderr = run_command(command)

        # Process results
        execution_time = (datetime.now() - start_time).total_seconds()
        result = {
            "success": returncode == 0,
            "execution_time_seconds": execution_time,
            "return_code": returncode,
        }

        if returncode != 0:
            logger.error(f"Latest energy data update failed with code {returncode}")
            logger.error(f"Error: {stderr}")
            result["error"] = stderr.strip()
        else:
            logger.info(
                f"Latest energy data update completed in {execution_time:.1f} seconds"
            )

        return result

    except Exception as e:
        logger.error(f"Error in latest energy data update: {e}")
        return {
            "success": False,
            "error": str(e),
            "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
        }


def should_update_elexon(tracker: DataTracker, high_priority: bool = True) -> bool:
    """Determine if Elexon data should be updated based on last update time"""
    try:
        last_times = tracker.get_last_ingestion_times()
        current_time = datetime.now(timezone.utc)

        # Get appropriate dataset group for tracking
        key = "ELEXON_HIGH" if high_priority else "ELEXON_STANDARD"

        # Default to updating if no record found
        if key not in last_times:
            return True

        last_update = last_times[key]
        minutes_since_update = (current_time - last_update).total_seconds() / 60

        # High priority data updates every 15 minutes
        # Standard priority data updates every 30 minutes
        threshold = (
            12 if high_priority else 25
        )  # Slightly less than period to ensure regularity

        logger.info(
            f"{key} last updated {minutes_since_update:.1f} minutes ago (threshold: {threshold})"
        )
        return minutes_since_update >= threshold

    except Exception as e:
        logger.error(f"Error checking Elexon update time: {e}")
        # Default to updating if there's an error
        return True


def should_update_remit(tracker: DataTracker) -> bool:
    """Determine if REMIT data should be updated based on last update time"""
    try:
        last_times = tracker.get_last_ingestion_times()
        current_time = datetime.now(timezone.utc)

        # REMIT updates less frequently, check every 30 minutes
        if "REMIT_ALL" not in last_times:
            return True

        last_update = last_times["REMIT_ALL"]
        minutes_since_update = (current_time - last_update).total_seconds() / 60

        logger.info(
            f"REMIT last updated {minutes_since_update:.1f} minutes ago (threshold: 25)"
        )
        return minutes_since_update >= 25  # Check every ~30 minutes

    except Exception as e:
        logger.error(f"Error checking REMIT update time: {e}")
        # Default to updating if there's an error
        return True


def should_update_neso(tracker: DataTracker) -> bool:
    """Determine if NESO data should be updated based on last update time"""
    try:
        last_times = tracker.get_last_ingestion_times()
        current_time = datetime.now(timezone.utc)

        # NESO updates less frequently, check every 2 hours
        if "NESO_ALL" not in last_times:
            return True

        last_update = last_times["NESO_ALL"]
        minutes_since_update = (current_time - last_update).total_seconds() / 60

        logger.info(
            f"NESO last updated {minutes_since_update:.1f} minutes ago (threshold: 115)"
        )
        return minutes_since_update >= 115  # Check approximately every 2 hours

    except Exception as e:
        logger.error(f"Error checking NESO update time: {e}")
        # Default to updating if there's an error
        return True


def main():
    """Main function to coordinate 15-minute updates"""
    parser = argparse.ArgumentParser(
        description="15-Minute Update System for All Data Sources"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no actual updates)"
    )
    parser.add_argument(
        "--elexon-only", action="store_true", help="Only update Elexon data"
    )
    parser.add_argument(
        "--remit-only", action="store_true", help="Only update REMIT data"
    )
    parser.add_argument(
        "--neso-only", action="store_true", help="Only update NESO data"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force updates regardless of timing"
    )
    args = parser.parse_args()

    start_time = datetime.now()
    logger.info(
        f"🚀 Starting 15-minute update at {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )

    # Create tracker with dry-run mode awareness
    tracker = DataTracker(dry_run=args.dry_run)
    results = {}

    try:
        # Update high-priority Elexon data (every 15 minutes)
        if (
            args.force
            or not args.remit_only
            and not args.neso_only
            and should_update_elexon(tracker, high_priority=True)
        ):
            logger.info("Updating high-priority Elexon data...")
            results["elexon_high"] = update_elexon_data(
                ELEXON_HIGH_PRIORITY, args.dry_run
            )
            if not args.dry_run and results["elexon_high"]["success"]:
                tracker.update_ingestion_time(
                    "ELEXON", "HIGH", datetime.now(timezone.utc), "SUCCESS"
                )

        # Update standard-priority Elexon data (every 30 minutes)
        if (
            args.force
            or not args.remit_only
            and not args.neso_only
            and should_update_elexon(tracker, high_priority=False)
        ):
            logger.info("Updating standard-priority Elexon data...")
            results["elexon_standard"] = update_elexon_data(
                ELEXON_STANDARD_PRIORITY, args.dry_run
            )
            if not args.dry_run and results["elexon_standard"]["success"]:
                tracker.update_ingestion_time(
                    "ELEXON", "STANDARD", datetime.now(timezone.utc), "SUCCESS"
                )

        # Update REMIT data (every 30 minutes)
        if (
            args.force
            or args.elexon_only is False
            and (args.remit_only or should_update_remit(tracker))
        ):
            logger.info("Updating REMIT data...")
            results["remit"] = update_remit_data(args.dry_run)
            if not args.dry_run and results["remit"]["success"]:
                tracker.update_ingestion_time(
                    "REMIT", "ALL", datetime.now(timezone.utc), "SUCCESS"
                )

        # Update NESO data (every 2 hours)
        if (
            args.force
            or args.elexon_only is False
            and (args.neso_only or should_update_neso(tracker))
            and NESO_AVAILABLE
        ):
            logger.info("Updating NESO data...")
            results["neso"] = update_neso_data(args.dry_run)
            if not args.dry_run and results["neso"]["success"]:
                tracker.update_ingestion_time(
                    "NESO", "ALL", datetime.now(timezone.utc), "SUCCESS"
                )

        # Always update the latest energy data snapshot
        if not args.dry_run:
            logger.info("Updating latest energy data snapshot...")
            results["latest_energy"] = update_latest_energy_data()

    except Exception as e:
        logger.error(f"Error in 15-minute update: {e}")
        results["error"] = str(e)

    # Calculate total execution time
    execution_time = (datetime.now() - start_time).total_seconds()
    results["total_execution_time_seconds"] = execution_time

    logger.info(f"✅ 15-minute update completed in {execution_time:.1f} seconds")

    # Print summary
    print(json.dumps(results, indent=2))

    # Write results to file for monitoring
    with open("15_minute_update_last_run.json", "w") as f:
        json.dump(
            {"timestamp": datetime.now().isoformat(), "results": results}, f, indent=2
        )

    return results


if __name__ == "__main__":
    main()
