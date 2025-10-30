#!/usr/bin/env python3
"""
Energy Data System Startup Manager

This script runs at system startup and:
1. Prompts the user for how many days of historical data to catch up on
2. Runs the initial data ingestion to catch up
3. Sets up a continuous 15-minute update process in the background

This ensures all data is caught up after machine downtime and continues
to stay updated while the machine is running.
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("startup_manager.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Globals
UPDATE_PROCESS = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_days_input():
    """Prompt the user for number of days to ingest"""
    while True:
        try:
            days = input(
                "How many days of historical data would you like to catch up on? [default: 1] "
            )
            if not days.strip():
                return 1
            days = int(days)
            if days < 1:
                print("Please enter a positive number of days.")
                continue
            return days
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


def calculate_date_range(days):
    """Calculate the date range for ingestion"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Format dates as strings
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    return start_str, end_str


def ingest_historical_data(days, dry_run=False, only=""):
    """Run the initial data ingestion to catch up after downtime"""
    logger.info(f"Starting historical data ingestion for past {days} days")

    # Calculate date range
    start_date, end_date = calculate_date_range(days)

    logger.info(f"Ingesting data from {start_date} to {end_date}")

    # Build command for Elexon data
    elexon_script = os.path.join(SCRIPT_DIR, "ingest_elexon_fixed.py")

    command = [
        sys.executable,
        elexon_script,
        "--start",
        start_date,
        "--end",
        end_date,
        "--log-level",
        "INFO",
        "--use-staging-table",
        "--monitor-progress",
    ]

    # Add optional arguments
    if dry_run:
        command.append("--dry-run")

    if only:
        command.extend(["--only", only])
    else:
        # Default to all datasets
        command.extend(
            [
                "--only",
                "FREQ,FUELINST,BOD,BOALF,COSTS,DISBSAD,MELS,MILS,QAS,NETBSAD,PN,QPN",
            ]
        )

    # Execute the command
    logger.info(f"Running Elexon ingest command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info("Elexon data ingestion complete")

        # Now ingest REMIT data if available
        remit_script = os.path.join(SCRIPT_DIR, "ingest_remit.py")
        if os.path.exists(remit_script):
            logger.info("Starting REMIT data ingestion")
            remit_command = [sys.executable, remit_script]
            if dry_run:
                remit_command.append("--check-only")

            remit_result = subprocess.run(
                remit_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("REMIT data ingestion complete")

        # Now run NESO data update if available
        neso_script = os.path.join(SCRIPT_DIR, "neso_data_updater.py")
        if os.path.exists(neso_script):
            logger.info("Starting NESO data ingestion")
            neso_command = [sys.executable, neso_script, "--direct-run"]
            if dry_run:
                neso_command.append("--dry-run")

            neso_result = subprocess.run(
                neso_command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("NESO data ingestion complete")

        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during data ingestion: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False


def start_15min_updater(dry_run=False):
    """Start the 15-minute update process in the background"""
    global UPDATE_PROCESS

    # Kill any existing process
    if UPDATE_PROCESS and UPDATE_PROCESS.poll() is None:
        logger.info("Stopping existing 15-minute updater process")
        os.kill(UPDATE_PROCESS.pid, signal.SIGTERM)
        time.sleep(2)

    # Build command
    updater_script = os.path.join(SCRIPT_DIR, "update_all_data_15min.py")
    command = [
        sys.executable,
        updater_script,
        "--continuous",  # New flag added to update_all_data_15min.py
    ]

    if dry_run:
        command.append("--dry-run")

    # Start process
    logger.info(f"Starting 15-minute updater: {' '.join(command)}")
    UPDATE_PROCESS = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Give it a moment to start up
    time.sleep(1)

    # Check if process is running
    if UPDATE_PROCESS.poll() is None:
        logger.info(f"15-minute updater started with PID {UPDATE_PROCESS.pid}")

        # Write PID to file for monitoring
        with open("update_process.pid", "w") as f:
            f.write(str(UPDATE_PROCESS.pid))

        return True
    else:
        stdout, stderr = UPDATE_PROCESS.communicate()
        logger.error(f"Failed to start 15-minute updater")
        logger.error(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        return False


def cleanup(exit_code=0):
    """Clean up processes before exit"""
    global UPDATE_PROCESS

    if UPDATE_PROCESS and UPDATE_PROCESS.poll() is None:
        logger.info(f"Stopping 15-minute updater process (PID {UPDATE_PROCESS.pid})")
        try:
            os.kill(UPDATE_PROCESS.pid, signal.SIGTERM)
        except:
            pass

    # Remove PID file
    if os.path.exists("update_process.pid"):
        os.remove("update_process.pid")

    logger.info("Cleanup complete")
    sys.exit(exit_code)


def handle_signal(signum, frame):
    """Signal handler for graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup()


def main():
    """Main function"""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    parser = argparse.ArgumentParser(description="Energy Data System Startup Manager")
    parser.add_argument(
        "--days", type=int, help="Number of days to catch up (skips prompt)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    parser.add_argument("--only", default="", help="Comma-separated dataset codes")
    parser.add_argument(
        "--skip-catchup", action="store_true", help="Skip historical data catchup"
    )
    parser.add_argument(
        "--skip-15min", action="store_true", help="Skip 15-minute updater"
    )
    args = parser.parse_args()

    try:
        # Write startup record
        with open("system_startup.json", "w") as f:
            json.dump(
                {"timestamp": datetime.now().isoformat(), "args": vars(args)},
                f,
                indent=2,
            )

        # Step 1: Catch up on historical data
        if not args.skip_catchup:
            days = args.days if args.days else get_days_input()
            logger.info(f"Starting historical data catchup for {days} days")

            success = ingest_historical_data(days, args.dry_run, args.only)
            if not success:
                logger.warning("Historical data catchup had issues, but continuing...")
        else:
            logger.info("Skipping historical data catchup as requested")

        # Step 2: Start 15-minute updater
        if not args.skip_15min:
            logger.info("Starting 15-minute updater process")
            success = start_15min_updater(args.dry_run)
            if not success:
                logger.error("Failed to start 15-minute updater")
                return 1
        else:
            logger.info("Skipping 15-minute updater as requested")

        logger.info("Startup manager completed successfully")

        # If running interactively, keep the script alive to manage the updater process
        if not args.skip_15min and os.isatty(sys.stdin.fileno()):
            try:
                while UPDATE_PROCESS and UPDATE_PROCESS.poll() is None:
                    time.sleep(5)
                logger.warning("15-minute updater process has stopped")
            except KeyboardInterrupt:
                logger.info("User interrupted, shutting down...")
            finally:
                cleanup()

        return 0

    except Exception as e:
        logger.error(f"Error in startup manager: {e}", exc_info=True)
        cleanup(1)
        return 1


if __name__ == "__main__":
    sys.exit(main())
