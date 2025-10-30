#!/usr/bin/env python3
"""
NESO Data Collection Launcher
============================

Quick launcher for comprehensive NESO data collection.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Launch NESO collection."""

    print("🚀 NESO Comprehensive Data Collection")
    print("=" * 40)

    # Check environment
    venv_path = Path("environment/bin/python")
    if not venv_path.exists():
        print("❌ Virtual environment not found")
        print("Please run from the project root directory")
        return 1

    # Check collector script
    collector_script = Path("collect_neso_comprehensive.py")
    if not collector_script.exists():
        print("❌ Collection script not found")
        return 1

    print("📊 What will be collected:")
    print("  ✅ Carbon Intensity API (real-time)")
    print("  ✅ NESO Data Portal (121 datasets)")
    print("  📈 Embedded wind/solar forecasts")
    print("  📈 Demand forecasts (1-day, 2-day, 7-day)")
    print("  📈 BSUoS charges and forecasts")
    print("  📈 Carbon intensity of balancing actions")
    print("  📈 Capacity market data")
    print("  📈 System warnings and constraints")
    print()

    # Run collection
    print("🔄 Starting collection...")
    try:
        result = subprocess.run(
            [str(venv_path), "collect_neso_comprehensive.py"], check=True
        )

        print("\n✅ NESO collection completed!")
        print("\n📁 Output locations:")
        print("  📊 Files: ./neso_data_comprehensive/")
        print("  🗄️  SQLite: ./neso_data_comprehensive/neso_comprehensive.sqlite")
        print("  ☁️  BigQuery: jibber-jabber-knowledge.uk_energy_insights.neso_*")
        print("\n🎯 Integration ready with BMRS and UKPN data!")

        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Collection failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n🛑 Collection interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
