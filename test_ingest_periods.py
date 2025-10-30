#!/usr/bin/env python3
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


def run_test_periods():
    """Run test ingestion for 1 week periods across 2022-2024"""
    print("Starting test ingestion...")  # Debug print

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("test_ingest.log"), logging.StreamHandler()],
    )

    # Create test data directory
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)

    # Test periods - 1 week each from June
    test_periods = [
        ("2022-06-01", "2022-06-08"),
        ("2023-06-01", "2023-06-08"),
        ("2024-06-01", "2024-06-08"),
    ]

    # Key test datasets
    test_datasets = "BOD,FREQ,FUELINST,MID"

    # Run tests for each period
    for start_date, end_date in test_periods:
        logging.info(
            f"\n{'='*80}\nTesting period: {start_date} to {end_date}\n{'='*80}"
        )

        # Use the virtual environment's Python
        venv_python = os.path.join(os.getcwd(), "venv", "bin", "python3")

        # Verify Python executable exists
        if not os.path.exists(venv_python):
            logging.error(f"Python executable not found at {venv_python}")
            return False

        # Check if GOOGLE_APPLICATION_CREDENTIALS is set
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logging.warning(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set"
            )
            # Set default credentials path
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
                "~/.config/gcloud/application_default_credentials.json"
            )

        # Get the absolute path to the ingest script
        ingest_script = os.path.join(os.getcwd(), "ingest_elexon_fixed.py")

        # Build command as a list for subprocess
        cmd = [
            sys.executable,  # Use current Python interpreter
            ingest_script,
            "--start",
            start_date,
            "--end",
            end_date,
            "--only",
            test_datasets,
            "--use-staging-table",
            "--monitor-progress",
            "--data-dir",
            str(test_data_dir.absolute()),
            "--log-level",
            "INFO",
            "--sandbox-mode=false",
        ]

        logging.info(f"Running command with Python: {sys.executable}")
        logging.info(f"Command args: {' '.join(cmd[1:])}")

        # Set up environment
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()  # Use absolute path

        try:
            import subprocess

            result = subprocess.run(
                cmd,
                env=env,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logging.info(result.stdout)
            if result.stderr:
                logging.warning(result.stderr)
            exit_code = result.returncode
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed with code {e.returncode}")
            logging.error(f"Output: {e.output}")
            logging.error(f"Stderr: {e.stderr}")
            exit_code = e.returncode
        except Exception as e:
            logging.error(f"Failed to run command: {e}")
            exit_code = 1

        if exit_code != 0:
            logging.error(f"Test failed for period {start_date} to {end_date}")
            # Add cooling period between retries
            time.sleep(300)  # 5 minutes cooling period
        else:
            logging.info(
                f"Test completed successfully for period {start_date} to {end_date}"
            )
            # Add small delay between successful periods
            time.sleep(60)  # 1 minute between periods


if __name__ == "__main__":
    print("Script starting at", datetime.now())
    print("Current working directory:", os.getcwd())
    print("Python executable:", sys.executable)
    print("PYTHONPATH:", os.environ.get("PYTHONPATH", "Not set"))
    run_test_periods()
    print("Script finished at", datetime.now())
