#!/usr/bin/env python3
"""
Elexon Data Ingestor - Startup Edition

This script runs at system startup and prompts the user to specify how many days
of historical data to ingest. It then calls the ingest_elexon_fixed.py script
with the appropriate parameters.

No Google Sheets or external tracking is required.
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta


def get_days_input():
    """Prompt the user for number of days to ingest"""
    while True:
        try:
            days = input(
                "How many days of historical data would you like to ingest? [default: 1] "
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


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Elexon Data Ingestor - Startup Edition"
    )
    parser.add_argument(
        "--days", type=int, help="Number of days to ingest (skips interactive prompt)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no actual updates)"
    )
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated dataset codes, e.g. BOD,BOALF,DISBSAD",
    )
    args = parser.parse_args()

    # Get days from argument or prompt
    days = args.days if args.days else get_days_input()

    # Calculate date range
    start_date, end_date = calculate_date_range(days)

    print(f"Ingesting data from {start_date} to {end_date} ({days} days)...")

    # Build command to run ingest_elexon_fixed.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    elexon_script = os.path.join(script_dir, "ingest_elexon_fixed.py")

    command = [
        sys.executable,  # Current Python interpreter
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
    if args.dry_run:
        command.append("--dry-run")

    if args.only:
        command.extend(["--only", args.only])
    else:
        # Default to high-priority datasets
        command.extend(
            [
                "--only",
                "FREQ,FUELINST,BOD,BOALF,COSTS,DISBSAD,MELS,MILS,QAS,NETBSAD,PN,QPN",
            ]
        )

    # Add REMIT data if needed
    try:
        remit_script = os.path.join(script_dir, "ingest_remit.py")
        if os.path.exists(remit_script):
            print("REMIT script found. Will ingest REMIT data after Elexon data.")
            include_remit = True
        else:
            include_remit = False
    except:
        include_remit = False

    # Execute the command
    print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True)

        # If Elexon ingestion succeeded and REMIT script exists, run it too
        if result.returncode == 0 and include_remit:
            print("Elexon data ingestion complete. Now ingesting REMIT data...")
            remit_command = [sys.executable, remit_script]
            if args.dry_run:
                remit_command.append("--check-only")
            subprocess.run(remit_command, check=True)

        print("✅ Data ingestion complete!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running ingestion script: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
