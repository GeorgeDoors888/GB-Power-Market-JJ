#!/usr/bin/env python3
"""
Simple Energy Data System Starter

This script provides a simplified, error-free way to:
1. Catch up on missed data since your machine was off
2. Start continuous updates that run in the background

Just run this script and follow the prompts.
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

# Set up simple logging with less verbose output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.FileHandler("energy_system.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Globals
UPDATE_PROCESS = None
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_days_input():
    """Prompt the user for number of days to ingest"""
    while True:
        try:
            days = input("How many days of data to catch up on? [default: 1] ")
            if not days.strip():
                return 1
            days = int(days)
            if days < 1:
                print("Please enter a positive number.")
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


def run_command(command, silent=False):
    """Run a command and handle errors gracefully"""
    if not silent:
        print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE if silent else None,
            stderr=subprocess.PIPE if silent else None,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False


def catch_up_data(days, dry_run=False):
    """Catch up on missed data"""
    print(f"\n📥 Catching up on {days} days of missed data...")

    # Calculate date range
    start_date, end_date = calculate_date_range(days)
    print(f"Date range: {start_date} to {end_date}")

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
    ]

    if dry_run:
        command.append("--dry-run")

    # Run the command
    print("\n⚡ Ingesting Elexon BMRS data...")
    success = run_command(command)

    if success:
        print("✅ Elexon data ingestion complete")
    else:
        print("⚠️ Elexon data ingestion had some issues")

    # Try REMIT data
    remit_script = os.path.join(SCRIPT_DIR, "ingest_remit.py")
    if os.path.exists(remit_script):
        print("\n⚡ Ingesting REMIT data...")
        remit_command = [sys.executable, remit_script]

        if dry_run:
            remit_command.append("--check-only")

        success = run_command(remit_command)

        if success:
            print("✅ REMIT data ingestion complete")
        else:
            print("⚠️ REMIT data ingestion had some issues")

    print("\n🎉 Data catch-up process finished")


def start_continuous_updates(dry_run=False):
    """Start the 15-minute updater in the background"""
    global UPDATE_PROCESS

    print("\n🔄 Starting continuous updates (every 15 minutes)...")

    # Build command
    updater_script = os.path.join(SCRIPT_DIR, "update_all_data_15min.py")
    command = [sys.executable, updater_script, "--continuous"]

    if dry_run:
        command.append("--dry-run")

    # Start process (detached)
    try:
        log_file = open("updater.log", "a")

        # Use Popen to start process in background
        UPDATE_PROCESS = subprocess.Popen(
            command, stdout=log_file, stderr=log_file, text=True
        )

        # Give it a moment to start
        time.sleep(1)

        # Check if running
        if UPDATE_PROCESS.poll() is None:
            print(f"✅ Continuous updates started (PID: {UPDATE_PROCESS.pid})")

            # Write PID to file
            with open("updater.pid", "w") as f:
                f.write(str(UPDATE_PROCESS.pid))

            return True
        else:
            print("❌ Failed to start continuous updates")
            return False

    except Exception as e:
        print(f"❌ Error starting continuous updates: {e}")
        return False


def cleanup():
    """Clean up resources before exit"""
    if UPDATE_PROCESS and UPDATE_PROCESS.poll() is None:
        print(f"Stopping continuous updates (PID: {UPDATE_PROCESS.pid})...")
        try:
            UPDATE_PROCESS.terminate()
        except:
            pass


def handle_signals(signum, frame):
    """Handle interrupt signals gracefully"""
    print("\nShutting down...")
    cleanup()
    sys.exit(0)


def main():
    """Main function"""
    # Set up signal handling
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    parser = argparse.ArgumentParser(description="Simple Energy Data System")
    parser.add_argument("--days", type=int, help="Days to catch up on (skips prompt)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without updating data"
    )
    parser.add_argument(
        "--skip-catchup", action="store_true", help="Skip data catch-up"
    )
    parser.add_argument(
        "--skip-continuous", action="store_true", help="Skip continuous updates"
    )
    args = parser.parse_args()

    try:
        print("=" * 60)
        print(" ENERGY DATA SYSTEM - SIMPLE STARTER ")
        print("=" * 60)

        # Step 1: Catch up on missed data
        if not args.skip_catchup:
            days = args.days if args.days is not None else get_days_input()
            catch_up_data(days, args.dry_run)
        else:
            print("\n⏩ Skipping data catch-up as requested")

        # Step 2: Start continuous updates
        if not args.skip_continuous:
            success = start_continuous_updates(args.dry_run)
            if not success:
                print("⚠️ Continuous updates couldn't be started")
        else:
            print("\n⏩ Skipping continuous updates as requested")

        print("\n✨ Energy data system setup complete!")
        print("=" * 60)

        if not args.skip_continuous:
            print("\nThe system is now running in the background.")
            print("You can close this terminal if desired.")
            print("To stop the system, press Ctrl+C in this window or run:")
            print(f"kill $(cat updater.pid)")

            # Keep running to allow Ctrl+C to work
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
            finally:
                cleanup()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())
