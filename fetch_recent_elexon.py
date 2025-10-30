#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch recent Elexon data specifically targeting the last 15-30 minutes
This is a modified version of ingest_elexon_fixed.py focusing on recent data
"""

import datetime
import logging
import os
import sys
from datetime import timedelta

# Verify Python environment first
try:
    import pandas as pd
    import requests
    from google.cloud import bigquery
except ImportError:
    print(
        "Required dependencies not installed. Please activate your virtual environment first."
    )
    print(
        "If you haven't set it up yet, run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    )
    sys.exit(1)


def main():
    # Calculate time windows for recent data
    now = datetime.datetime.now(datetime.timezone.utc)

    # High priority datasets (15-minute window, ending 5 minutes ago)
    high_priority_end = now - timedelta(minutes=5)
    high_priority_start = high_priority_end - timedelta(minutes=15)

    # Standard priority datasets (30-minute window, ending 10 minutes ago)
    standard_priority_end = now - timedelta(minutes=10)
    standard_priority_start = standard_priority_end - timedelta(minutes=30)

    # Format dates for ingest_elexon_fixed.py
    high_priority_start_str = high_priority_start.strftime("%Y-%m-%dT%H:%M:%S")
    high_priority_end_str = high_priority_end.strftime("%Y-%m-%dT%H:%M:%S")
    standard_priority_start_str = standard_priority_start.strftime("%Y-%m-%dT%H:%M:%S")
    standard_priority_end_str = standard_priority_end.strftime("%Y-%m-%dT%H:%M:%S")

    # High priority datasets
    high_priority_datasets = ["FREQ", "FUELINST", "BOD", "BOALF", "COSTS", "DISBSAD"]
    high_priority_cmd = (
        f"python ingest_elexon_fixed.py "
        f"--start {high_priority_start_str} "
        f"--end {high_priority_end_str} "
        f"--only {','.join(high_priority_datasets)} "
        f"--log-level DEBUG"
    )

    # Standard priority datasets
    standard_priority_datasets = [
        "MELS",
        "MILS",
        "QAS",
        "NETBSAD",
        "PN",
        "QPN",
        "IMBALNGC",
    ]
    standard_priority_cmd = (
        f"python ingest_elexon_fixed.py "
        f"--start {standard_priority_start_str} "
        f"--end {standard_priority_end_str} "
        f"--only {','.join(standard_priority_datasets)} "
        f"--log-level DEBUG "
        f"--include-offline"  # For MELS and MILS
    )

    print("=" * 80)
    print(f"FETCHING RECENT ELEXON DATA ({now.strftime('%Y-%m-%d %H:%M:%S UTC')})")
    print("=" * 80)

    # Run high priority datasets command
    print(f"\nRunning high priority datasets ({', '.join(high_priority_datasets)})")
    print(f"Time window: {high_priority_start_str} to {high_priority_end_str}")
    print(f"Command: {high_priority_cmd}")
    os.system(high_priority_cmd)

    # Run standard priority datasets command
    print(
        f"\nRunning standard priority datasets ({', '.join(standard_priority_datasets)})"
    )
    print(f"Time window: {standard_priority_start_str} to {standard_priority_end_str}")
    print(f"Command: {standard_priority_cmd}")
    os.system(standard_priority_cmd)

    print("\nFinished fetching recent data!")


if __name__ == "__main__":
    main()
