#!/usr/bin/env python3
"""
Deploy BigQuery Views and Run BtM PPA Revenue Analysis
Alternative to shell script for Windows/environments without bash
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import os
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

def deploy_views():
    """Deploy all BigQuery views"""
    print("=" * 70)
    print("DEPLOYING BIGQUERY VIEWS")
    print("=" * 70)
    
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    views = [
        'sql/v_system_prices_sp.sql',
        'sql/v_bm_bids_offers_classified.sql', 
        'sql/v_bm_system_direction_classified.sql',
        'sql/v_curtailment_revenue_daily.sql'
    ]
    
    for view_file in views:
        print(f"\n📝 Deploying {os.path.basename(view_file)}...")
        try:
            with open(view_file, 'r') as f:
                sql = f.read()
            
            job = client.query(sql)
            job.result()  # Wait for completion
            print(f"   ✅ Deployed successfully")
        except Exception as e:
            error_msg = str(e)
            if "Already Exists" in error_msg:
                print(f"   ℹ️  View already exists (OK)")
            else:
                print(f"   ⚠️  Error: {error_msg[:200]}")
    
    print("\n✅ All views processed")
    return True


def run_analysis():
    """Run the revenue analysis script"""
    print("\n" + "=" * 70)
    print("RUNNING REVENUE ANALYSIS")
    print("=" * 70 + "\n")
    
    # Import and run the main script
    import update_btm_ppa_from_bigquery
    

def main():
    print("\n" + "=" * 70)
    print("BIGQUERY BtM PPA SYSTEM DEPLOYMENT")
    print("=" * 70 + "\n")
    
    # Step 1: Deploy views
    try:
        deploy_views()
    except Exception as e:
        print(f"\n⚠️  View deployment error: {e}")
        print("Continuing with analysis (views may already exist)...")
    
    # Step 2: Run analysis
    try:
        run_analysis()
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 70)
    print("\nCheck your Google Sheets:")
    print("  - Dashboard Row 7: BtM PPA Profit KPI")
    print("  - Dashboard Row 8: Curtailment Revenue KPI")
    print("  - BESS Sheet: Detailed breakdown (rows 45, 60-66)")
    print()


if __name__ == "__main__":
    main()
