#!/usr/bin/env python3
"""
Comprehensive test runner for Elexon data ingestion
- Tests all datasets
- Validates schemas
- Monitors quotas
- Detailed error reporting
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("comprehensive_test.log"), logging.StreamHandler()],
)

# All available datasets
ALL_DATASETS = [
    "BOD",
    "FREQ",
    "FUELINST",
    "MID",
    "TEMP",
    "MELS",
    "MILS",
    "RDRE",
    "RDRI",
    "BOALF",
    "NETBSAD",
    "DISBSAD",
    "IMBALNGC",
    "PN",
    "QPN",
    "QAS",
    "RURE",
    "RURI",
    "FUELHH",
    "B1610",
    "NDF",
    "NDFD",
    "NDFW",
    "TSDF",
    "TSDFD",
    "TSDFW",
]

# Test periods - one day per year to start
TEST_PERIODS = [
    ("2022-06-01", "2022-06-02"),
    ("2023-06-01", "2023-06-02"),
    ("2024-06-01", "2024-06-02"),
]


class TestResults:
    def __init__(self):
        self.results: Dict[str, Dict] = {}

    def add_result(self, dataset: str, period: tuple, success: bool, error: str = None):
        if dataset not in self.results:
            self.results[dataset] = {"success": 0, "failures": 0, "errors": []}

        if success:
            self.results[dataset]["success"] += 1
        else:
            self.results[dataset]["failures"] += 1
            if error:
                self.results[dataset]["errors"].append(
                    {"period": period, "error": error}
                )

    def save_report(self):
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Generate summary
        success_count = sum(d["success"] for d in self.results.values())
        failure_count = sum(d["failures"] for d in self.results.values())
        total_tests = success_count + failure_count

        with open("test_summary.txt", "w") as f:
            f.write(f"Test Summary\n{'='*50}\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Successes: {success_count}\n")
            f.write(f"Failures: {failure_count}\n")
            f.write(f"Success Rate: {(success_count/total_tests)*100:.1f}%\n\n")

            if failure_count > 0:
                f.write("Failed Datasets:\n")
                for dataset, results in self.results.items():
                    if results["failures"] > 0:
                        f.write(f"\n{dataset}:\n")
                        for error in results["errors"]:
                            f.write(f"  Period {error['period']}: {error['error']}\n")


def run_comprehensive_test():
    """Run tests for all datasets with detailed monitoring"""

    results = TestResults()
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)

    # Test each dataset individually
    for dataset in ALL_DATASETS:
        logging.info(f"\n{'='*80}\nTesting dataset: {dataset}\n{'='*80}")

        for start_date, end_date in TEST_PERIODS:
            logging.info(f"\nTesting period: {start_date} to {end_date}")

            # Build command
            cmd = [
                sys.executable,
                "ingest_elexon_fixed.py",
                "--start",
                start_date,
                "--end",
                end_date,
                "--only",
                dataset,
                "--use-staging-table",
                "--monitor-progress",
                "--validate-schema",
                "--check-quotas",
                "--data-dir",
                str(test_data_dir.absolute()),
                "--log-level",
                "DEBUG",
            ]

            try:
                # Set up environment
                env = os.environ.copy()
                env["PYTHONPATH"] = os.getcwd()

                # Run the command
                logging.info(f"Running: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    env=env,
                    check=False,  # Don't raise exception on non-zero exit
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd(),
                )

                if result.returncode == 0:
                    logging.info(
                        f"✅ Successfully ingested {dataset} for period {start_date} to {end_date}"
                    )
                    results.add_result(dataset, (start_date, end_date), True)
                else:
                    error_msg = result.stderr or "Unknown error"
                    logging.error(f"❌ Failed to ingest {dataset}: {error_msg}")
                    results.add_result(
                        dataset, (start_date, end_date), False, error_msg
                    )

                    # Add cooling period after failure
                    time.sleep(60)  # 1 minute cooling period

            except Exception as e:
                logging.error(f"Error running test for {dataset}: {e}")
                results.add_result(dataset, (start_date, end_date), False, str(e))
                time.sleep(60)  # Cooling period after error

            # Always add a small delay between tests
            time.sleep(10)

    # Save test results
    results.save_report()
    logging.info(
        "\nTest run completed. Check test_results.json and test_summary.txt for details."
    )


if __name__ == "__main__":
    print(f"Starting comprehensive test run at {datetime.now()}")
    run_comprehensive_test()
    print(f"Test run completed at {datetime.now()}")
