#!/usr/bin/env python3
"""
Complete 2022 BMRS Dataset Ingestion
===================================

This script provides commands to systematically complete all BMRS datasets for 2022.
Execute in phases to manage resource usage and monitor progress.
"""

import subprocess
import sys
import time
from pathlib import Path

# Configuration
BASE_CMD = [
    "python", "ingest_elexon_fixed.py",
    "--start", "2022-01-01",
    "--end", "2023-01-01",
    "--log-level", "INFO",
    "--monitor-progress",
    "--use-staging-table",
    "--batch-size", "50",
    "--flush-seconds", "180"
]

# Dataset phases
PHASES = {
    "phase1_core": {
        "description": "Core Market Data (Quick wins, ~30 min each)",
        "datasets": ["FREQ", "TEMP", "METADATA", "MID", "QAS", "IMBALNGC"],
        "batch_size": "50",
        "flush_seconds": "180"
    },
    "phase2_generation": {
        "description": "Generation & Demand (Medium, ~45 min each)",
        "datasets": ["FUELINST", "FUELHH", "INDGEN", "INDDEM", "INDO", "ITSDO"],
        "batch_size": "50",
        "flush_seconds": "180"
    },
    "phase3_forecasting": {
        "description": "Forecasting & System Data (Medium, ~60 min each)",
        "datasets": ["WINDFOR", "NDF", "NDFD", "NDFW", "TSDF", "TSDFD", "TSDFW"],
        "batch_size": "40",
        "flush_seconds": "240"
    },
    "phase4_high_volume": {
        "description": "HIGH VOLUME (Large, 2-4 hours each)",
        "datasets": ["BOD", "BOAL"],
        "batch_size": "25",
        "flush_seconds": "300"
    },
    "phase5_special": {
        "description": "Outages & Special (Variable time)",
        "datasets": [
            "FOU2T14D", "FOU2T3YW", "FOUT2T14D", "NOU2T14D", "NOU2T3YW",
            "UOU2T14D", "UOU2T3YW", "OCNMF3Y", "OCNMF3Y2", "OCNMFD",
            "OCNMFD2", "COSTS", "SEL", "SIL", "NTB", "NTO", "MDV", "MDP",
            "MELNGC", "DISBSAD", "NETBSAD", "NONBM", "RDRE", "RDRI",
            "RURE", "RURI", "NDZ", "MNZT", "MZT"
        ],
        "batch_size": "50",
        "flush_seconds": "180"
    }
}

def print_phase_commands(phase_name, phase_info):
    """Print commands for a specific phase."""
    print(f"\n🚀 {phase_info['description']}")
    print("=" * 60)

    for i, dataset in enumerate(phase_info['datasets'], 1):
        terminal_name = f"{phase_name}-{dataset.lower()}"
        batch_size = phase_info['batch_size']
        flush_seconds = phase_info['flush_seconds']

        cmd = (
            f'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && '
            f'source .venv_2022_ingest/bin/activate && '
            f'echo "🚀 Starting 2022 {dataset} ingestion ({i}/{len(phase_info["datasets"])})" && '
            f'python ingest_elexon_fixed.py '
            f'--start 2022-01-01 --end 2023-01-01 '
            f'--only {dataset} '
            f'--log-level INFO --monitor-progress --use-staging-table '
            f'--batch-size {batch_size} --flush-seconds {flush_seconds}'
        )

        print(f"\n# Terminal: {terminal_name}")
        print(f"# Dataset: {dataset} (Batch: {batch_size}, Flush: {flush_seconds}s)")
        print(cmd)

def main():
    print("📊 COMPLETE 2022 BMRS DATASETS")
    print("=" * 50)
    print("This script provides terminal commands to complete all 2022 BMRS datasets.")
    print("Copy and paste the commands into separate terminals for parallel execution.")
    print("\n⚠️  IMPORTANT:")
    print("- Run phases sequentially or monitor BigQuery quotas")
    print("- Phase 4 (BOD/BOAL) should be run during off-peak hours")
    print("- Monitor system resources during execution")

    for phase_name, phase_info in PHASES.items():
        print_phase_commands(phase_name, phase_info)

    print("\n\n🎯 EXECUTION STRATEGY:")
    print("1. Start with Phase 1 (core datasets) - can run all in parallel")
    print("2. Move to Phase 2 (generation) - run 2-3 in parallel")
    print("3. Phase 3 (forecasting) - run 2-3 in parallel")
    print("4. Phase 4 (high volume) - run BOD and BOAL separately")
    print("5. Phase 5 (remaining) - batch in groups of 3-4")

    print("\n📊 MONITORING:")
    print("Use this command to check progress:")
    print('python -c "from bigquery_utils import *; check_2022_completeness()"')

if __name__ == "__main__":
    main()
gcloud auth application-default login
