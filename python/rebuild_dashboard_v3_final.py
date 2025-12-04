"""
rebuild_dashboard_v3_final.py

Single entrypoint to:
1) Populate all backing tables (Chart Data, Outages, ESO_Actions, DNO_Map, Market_Prices, VLP_Data)
2) Apply the full Dashboard V3 design (layout, KPIs, charts)

Usage:
    python python/rebuild_dashboard_v3_final.py
"""

from __future__ import annotations

import sys
import time

# Import the two main modules
try:
    from apply_dashboard_design import setup_dashboard_v3
    from populate_dashboard_tables import populate_dashboard_tables
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure both apply_dashboard_design.py and populate_dashboard_tables.py are in the same directory.")
    sys.exit(1)


def main():
    print("\n" + "=" * 80)
    print("🚀 GB ENERGY DASHBOARD V3 - PROFESSIONAL REBUILD")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Populate all backing data tables from BigQuery")
    print("  2. Apply the complete V3 dashboard design")
    print("  3. Create charts and visualizations")
    print("\n" + "=" * 80)
    
    start_time = time.time()
    
    # Phase 1: Populate backing tables
    print("\n📊 PHASE 1: POPULATING BACKING TABLES")
    print("-" * 80)
    populate_dashboard_tables()
    
    # Small delay to ensure data is settled
    print("\n⏱️  Waiting 3 seconds for data to settle...")
    time.sleep(3)
    
    # Phase 2: Apply design
    print("\n🎨 PHASE 2: APPLYING DASHBOARD DESIGN")
    print("-" * 80)
    print("\n" + "=" * 70)
    print("🚀 APPLYING GB ENERGY DASHBOARD V3 DESIGN")
    print("=" * 70)
    setup_dashboard_v3()
    print("\n" + "=" * 70)
    print("✅ DASHBOARD V3 DESIGN COMPLETE")
    print("=" * 70)
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"✅ DASHBOARD V3 REBUILD COMPLETE ({elapsed:.1f}s)")
    print("=" * 80)
    print("\n🔗 View your dashboard:")
    print("   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
