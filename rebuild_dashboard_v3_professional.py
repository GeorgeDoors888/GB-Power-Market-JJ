#!/usr/bin/env python3
"""
rebuild_dashboard_v3_professional.py

Single entrypoint to:
1) Populate all backing tables (Chart Data, Outages, ESO_Actions, DNO_Map, Market_Prices, VLP_Data)
2) Apply the full Dashboard V3 design (layout, KPIs, charts)

This is the definitive rebuild script for the GB Energy Dashboard V3.

Usage:
    python3 rebuild_dashboard_v3_professional.py
"""

import sys
import time

# Import the two main modules
try:
    from populate_dashboard_tables_v3_new import populate_dashboard_tables
    from apply_dashboard_design_v3_new import setup_dashboard_v3
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure both populate_dashboard_tables_v3_new.py and apply_dashboard_design_v3_new.py are in the same directory.")
    sys.exit(1)


def main():
    print("\n" + "=" * 80)
    print("🚀 GB ENERGY DASHBOARD V3 - PROFESSIONAL REBUILD")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. Populate all backing data tables from BigQuery")
    print("  2. Apply the complete V3 dashboard design")
    print("  3. Create charts and visualizations")
    print("\n" + "=" * 80 + "\n")
    
    start_time = time.time()
    
    try:
        # Step 1: Refresh backing tables from BigQuery
        print("\n📊 PHASE 1: POPULATING BACKING TABLES")
        print("-" * 80)
        populate_dashboard_tables()
        
        # Small delay to ensure Google Sheets processes the data
        print("\n⏱️  Waiting 3 seconds for data to settle...")
        time.sleep(3)
        
        # Step 2: Apply layout + charts
        print("\n🎨 PHASE 2: APPLYING DASHBOARD DESIGN")
        print("-" * 80)
        setup_dashboard_v3()
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 80)
        print(f"✅ DASHBOARD V3 REBUILD COMPLETE ({elapsed:.1f}s)")
        print("=" * 80)
        print("\n🔗 View your dashboard:")
        print("   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/")
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERROR DURING REBUILD: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
