#!/usr/bin/env python3
"""
Test script for BtM PPA revenue module

Tests the standalone BtM PPA calculations without running the full dashboard.
"""

import os
import sys
from google.cloud import bigquery

# Set up credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json"

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finance.btm_ppa import get_btm_ppa_metrics
from charts.btm_ppa_chart import build_btm_ppa_chart, build_btm_ppa_summary_text


def test_btm_ppa():
    """Test BtM PPA revenue calculations"""
    print("=" * 70)
    print("BtM PPA Revenue Module Test")
    print("=" * 70)
    
    # Create BigQuery client
    print("\n1️⃣  Connecting to BigQuery...")
    client = bigquery.Client(
        project="inner-cinema-476211-u9",
        location="US"
    )
    print("✅ Connected to BigQuery")
    
    # Get BtM PPA metrics
    print("\n2️⃣  Calculating BtM PPA revenue...")
    btm_results, curtailment = get_btm_ppa_metrics(client)
    print("✅ Calculations complete")
    
    # Print summary
    print(build_btm_ppa_summary_text(btm_results, curtailment))
    
    # Generate chart
    print("\n3️⃣  Generating BtM PPA chart...")
    chart_path = build_btm_ppa_chart(btm_results, curtailment, "out/test_btm_ppa.png")
    print(f"✅ Chart saved: {chart_path}")
    
    # Validation checks
    print("\n4️⃣  Validation:")
    s2 = btm_results["stream2"]
    
    checks = [
        ("RED Coverage", btm_results["red_coverage"], 90, 100),
        ("Battery Cycles", s2["cycles"], 100, 400),
        ("Total Profit", btm_results["total_profit"], 100000, 500000),
        ("Charging Cost", s2["charging_cost"], 50000, 200000),
    ]
    
    for name, value, min_val, max_val in checks:
        status = "✅" if min_val <= value <= max_val else "⚠️"
        print(f"   {status} {name}: {value:,.2f} (expected {min_val:,.0f}-{max_val:,.0f})")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    return btm_results, curtailment


if __name__ == "__main__":
    try:
        btm_results, curtailment = test_btm_ppa()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
