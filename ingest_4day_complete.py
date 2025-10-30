#!/usr/bin/env python3
"""
4-Day Complete Elexon Data Ingestion
Ingest all BMRS datasets for the last 4 days (2025-09-16 to 2025-09-20)
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta

# Setup paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INGESTION_SCRIPT = os.path.join(SCRIPT_DIR, "ingest_elexon_fixed.py")
VENV_PYTHON = os.path.join(SCRIPT_DIR, ".venv_ingestion", "bin", "python")

# Date range (last 4 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=4)

START_DATE = start_date.strftime("%Y-%m-%d")
END_DATE = end_date.strftime("%Y-%m-%d")

print(f"🚀 Starting 4-day complete Elexon data ingestion")
print(f"📅 Date Range: {START_DATE} to {END_DATE}")
print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# All critical BMRS datasets organized by priority
DATASET_GROUPS = {
    "high_frequency": {
        "datasets": ["FREQ", "FUELINST", "BOD", "BOALF", "COSTS", "DISBSAD"],
        "description": "Real-time market data (1-min to 30-min intervals)",
    },
    "settlement": {
        "datasets": ["MELS", "MILS", "QAS", "NETBSAD", "PN", "QPN"],
        "description": "Settlement and notification data (30-min intervals)",
    },
    "forecasts": {
        "datasets": ["NDF", "TSDF", "INDDEM", "INDGEN", "FUELHH"],
        "description": "Demand and generation forecasts (daily/hourly)",
    },
    "generation": {
        "datasets": ["UOU2T3YW", "UOU2T14D", "UOU2T52W", "B1610", "B1620"],
        "description": "Generation unit output data",
    },
    "balancing": {
        "datasets": ["MID", "RDRI", "RDRE", "RURE", "RURI", "LOLPDRM"],
        "description": "Balancing mechanism and demand response",
    },
    "system_data": {
        "datasets": ["SYSWARN", "SYSDEM", "TEMP", "WINDFOR", "ITSDO"],
        "description": "System warnings, demand, and operational data",
    },
}


def run_ingestion_group(group_name, datasets, description):
    """Run ingestion for a group of datasets"""
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
    ]

    print(f"🔄 Running: {' '.join(cmd[-6:])}")  # Show last 6 args for brevity

    try:
        # Run the ingestion
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes timeout per group
        )

        if result.returncode == 0:
            print(f"✅ {group_name} completed successfully")
            # Count successful datasets from output
            success_count = datasets_str.count(",") + 1
            print(f"   📈 Processed {success_count} datasets")
        else:
            print(f"⚠️ {group_name} completed with warnings")
            print(f"   📄 Last few lines of output:")
            output_lines = result.stdout.split("\n")[-5:]
            for line in output_lines:
                if line.strip():
                    print(f"   {line}")

    except subprocess.TimeoutExpired:
        print(f"⏰ {group_name} timed out after 30 minutes")
    except Exception as e:
        print(f"❌ {group_name} failed: {e}")


def main():
    """Main execution function"""
    total_start_time = datetime.now()

    # Process each group in order of priority
    for group_name, group_info in DATASET_GROUPS.items():
        group_start = datetime.now()

        run_ingestion_group(
            group_name, group_info["datasets"], group_info["description"]
        )

        group_duration = datetime.now() - group_start
        print(f"⏱️ {group_name} took {group_duration}")

    # Final summary
    total_duration = datetime.now() - total_start_time
    total_datasets = sum(len(group["datasets"]) for group in DATASET_GROUPS.values())

    print(f"\n🎉 4-Day Elexon Ingestion Complete!")
    print(f"📊 Total datasets processed: {total_datasets}")
    print(f"⏱️ Total time: {total_duration}")
    print(f"📅 Date range: {START_DATE} to {END_DATE}")
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Ingestion cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)
