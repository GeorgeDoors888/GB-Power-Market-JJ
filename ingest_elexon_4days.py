#!/usr/bin/env python3
"""
Comprehensive 4-Day Elexon Data Ingestion
Ingests all critical BMRS datasets for the last 4 days with proper error handling
"""

import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta

# Setup paths and ensure dependencies
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTION_SCRIPT = os.path.join(SCRIPT_DIR, "ingest_elexon_fixed.py")
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv_ingestion", "bin", "python")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f'logs/4day_ingestion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
    ],
)

# Date range (last 4 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=4)

START_DATE = start_date.strftime("%Y-%m-%d")
END_DATE = end_date.strftime("%Y-%m-%d")


def check_environment():
    """Check if virtual environment and dependencies are properly set up"""
    print("🔍 Checking environment setup...")

    # Check if virtual environment exists
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ Virtual environment not found at {VENV_PYTHON}")
        print("💡 Run ./setup_environment.sh first to set up the environment")
        return False

    # Check if ingestion script exists
    if not os.path.exists(INGESTION_SCRIPT):
        print(f"❌ Ingestion script not found at {INGESTION_SCRIPT}")
        return False

    # Test Python environment
    try:
        result = subprocess.run(
            [
                VENV_PYTHON,
                "-c",
                'import pandas, google.cloud.bigquery, requests, tqdm, dotenv; print("✅ All dependencies available")',
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ Environment check passed")
            return True
        else:
            print(f"❌ Dependency check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        return False


def run_ingestion_batch(group_name, datasets, description, timeout_minutes=45):
    """Run ingestion for a batch of datasets"""
    print(f"\n📊 Processing {group_name}: {description}")
    print(f"🎯 Datasets: {', '.join(datasets)}")

    # Build command
    datasets_str = ",".join(datasets)
    cmd = [
        VENV_PYTHON,
        INGESTION_SCRIPT,
        "--start",
        START_DATE,
        "--end",
        END_DATE,
        "--only",
        datasets_str,
        "--log-level",
        "INFO",
        "--include-offline",  # Include MILS/MELS
        "--batch-size",
        "5",  # Smaller batches for stability
        "--flush-seconds",
        "180",  # 3-minute flush interval
    ]

    print(f"🔄 Running: {' '.join(cmd[-8:])}")  # Show last 8 args for brevity

    try:
        # Run the ingestion with timeout
        result = subprocess.run(
            cmd, timeout=timeout_minutes * 60, text=True  # Convert to seconds
        )

        if result.returncode == 0:
            print(f"✅ {group_name} completed successfully")
            return True
        else:
            print(f"⚠️ {group_name} completed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {group_name} timed out after {timeout_minutes} minutes")
        return False
    except Exception as e:
        print(f"❌ {group_name} failed: {e}")
        return False


def main():
    """Main execution function"""
    print(f"🚀 Starting 4-day complete Elexon data ingestion")
    print(f"📅 Date Range: {START_DATE} to {END_DATE}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment first
    if not check_environment():
        print("❌ Environment check failed. Exiting.")
        sys.exit(1)

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Dataset groups organized by priority and processing requirements
    dataset_groups = [
        {
            "name": "critical_real_time",
            "datasets": ["FREQ", "FUELINST", "COSTS"],
            "description": "Critical real-time market data (fastest)",
            "timeout": 30,
        },
        {
            "name": "trading_data",
            "datasets": ["BOD", "BOALF", "DISBSAD"],
            "description": "Trading and balancing data",
            "timeout": 45,
        },
        {
            "name": "settlement_data",
            "datasets": ["MELS", "MILS", "QAS", "NETBSAD"],
            "description": "Settlement and adjustment data",
            "timeout": 60,
        },
        {
            "name": "notifications",
            "datasets": ["PN", "QPN"],
            "description": "Physical notifications",
            "timeout": 30,
        },
        {
            "name": "forecasts",
            "datasets": ["NDF", "TSDF", "INDDEM", "INDGEN"],
            "description": "Demand and generation forecasts",
            "timeout": 30,
        },
        {
            "name": "generation_small",
            "datasets": ["UOU2T14D", "B1610", "B1620"],
            "description": "Generation unit output (smaller datasets)",
            "timeout": 45,
        },
        {
            "name": "balancing",
            "datasets": ["MID", "RDRI", "RDRE", "RURE", "RURI"],
            "description": "Balancing mechanism data",
            "timeout": 30,
        },
        {
            "name": "system_data",
            "datasets": ["TEMP", "WINDFOR", "ITSDO"],
            "description": "System and weather data",
            "timeout": 30,
        },
    ]

    # Process large datasets separately at the end
    large_datasets = [
        {
            "name": "generation_large",
            "datasets": ["UOU2T3YW"],
            "description": "Large generation dataset (3-year window)",
            "timeout": 90,
        }
    ]

    total_start_time = datetime.now()
    successful_groups = 0
    total_groups = len(dataset_groups) + len(large_datasets)

    # Process regular dataset groups
    for group in dataset_groups:
        group_start = datetime.now()

        success = run_ingestion_batch(
            group["name"], group["datasets"], group["description"], group["timeout"]
        )

        if success:
            successful_groups += 1

        group_duration = datetime.now() - group_start
        print(f"⏱️ {group['name']} took {group_duration}")

        # Brief pause between groups to avoid overwhelming the API
        print("⏸️ Brief pause between groups...")
        import time

        time.sleep(5)

    # Process large datasets last
    print(f"\n🔄 Processing large datasets...")
    for group in large_datasets:
        group_start = datetime.now()

        success = run_ingestion_batch(
            group["name"], group["datasets"], group["description"], group["timeout"]
        )

        if success:
            successful_groups += 1

        group_duration = datetime.now() - group_start
        print(f"⏱️ {group['name']} took {group_duration}")

    # Final summary
    total_duration = datetime.now() - total_start_time
    total_datasets = sum(
        len(group["datasets"]) for group in dataset_groups + large_datasets
    )

    print(f"\n🎉 4-Day Elexon Ingestion Complete!")
    print(f"📊 Successful groups: {successful_groups}/{total_groups}")
    print(f"📊 Total datasets processed: {total_datasets}")
    print(f"⏱️ Total time: {total_duration}")
    print(f"📅 Date range: {START_DATE} to {END_DATE}")
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if successful_groups == total_groups:
        print("✅ All dataset groups completed successfully!")
    else:
        failed_groups = total_groups - successful_groups
        print(f"⚠️ {failed_groups} dataset groups had issues - check logs for details")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Ingestion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)
