"""
Real VLP Unit Tracking
Track actual battery units (FBPGM002, FFSEN005) vs model assumptions
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Known VLP battery units
VLP_UNITS = [
    {'bmUnit': 'FBPGM002', 'name': 'Flexgen Battery', 'capacity_mw': 2.5, 'capacity_mwh': 5.0},
    {'bmUnit': 'FFSEN005', 'name': 'Gresham House / Harmony', 'capacity_mw': 1.8, 'capacity_mwh': 3.6},
]

def track_vlp_bm_activity(bmUnit, days=30):
    """Track BM activity for specific VLP unit"""
    print(f"\n📊 TRACKING {bmUnit} (Last {days} Days)...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        DATE(acceptanceTime) as date,
        COUNT(*) as dispatch_count,
        MIN(acceptanceTime) as first_dispatch,
        MAX(acceptanceTime) as last_dispatch
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE bmUnit = '{bmUnit}'
        AND acceptanceTime >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        AND acceptanceTime < CURRENT_DATE()
    GROUP BY date
    ORDER BY date DESC
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if len(df) > 0:
            print(f"   ✅ Found BM activity on {len(df)} days")
            print(f"   Total dispatches: {df['dispatch_count'].sum()}")
            print(f"   Avg dispatches per active day: {df['dispatch_count'].mean():.1f}")
            print(f"\n   Recent activity:")
            for idx, row in df.head(5).iterrows():
                print(f"      {row['date']}: {row['dispatch_count']} dispatches")
            
            return df
        else:
            print(f"   ⚠️  No BM activity found for {bmUnit}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def compare_model_vs_actual():
    """Compare revenue model assumptions vs actual VLP data"""
    print("\n" + "="*70)
    print("🔍 VLP MODEL VS ACTUAL COMPARISON")
    print("="*70)
    
    for unit in VLP_UNITS:
        print(f"\n{'='*70}")
        print(f"Unit: {unit['bmUnit']} ({unit['name']})")
        print(f"Capacity: {unit['capacity_mw']} MW / {unit['capacity_mwh']} MWh")
        
        # Track BM activity
        activity = track_vlp_bm_activity(unit['bmUnit'], days=30)
        
        if activity is not None and len(activity) > 0:
            # Calculate actual utilization
            active_days = len(activity)
            avg_dispatches = activity['dispatch_count'].mean()
            hours_per_day = avg_dispatches * 0.5  # Each dispatch ~30 min
            
            print(f"\n   📈 ACTUAL PERFORMANCE:")
            print(f"      Active days: {active_days}/30 ({active_days/30*100:.1f}%)")
            print(f"      Avg BM hours per day: {hours_per_day:.2f}h")
            
            # Compare vs model
            model_bm_hours = 2.0
            print(f"\n   📊 MODEL COMPARISON:")
            print(f"      Model assumption: {model_bm_hours:.2f}h/day BM dispatch")
            print(f"      Actual: {hours_per_day:.2f}h/day")
            
            variance = abs(hours_per_day - model_bm_hours)
            if variance < 0.5:
                print(f"      ✅ MATCH - Within 0.5h")
            else:
                print(f"      ⚠️  VARIANCE - {variance:.2f}h difference")
            
            # Revenue implications
            model_bm_revenue_annual = 25 * unit['capacity_mwh'] * model_bm_hours * 365
            actual_bm_revenue_annual = 25 * unit['capacity_mwh'] * hours_per_day * 365
            
            print(f"\n   💰 REVENUE IMPACT:")
            print(f"      Model BM revenue: £{model_bm_revenue_annual:,.0f}/year")
            print(f"      Actual BM revenue: £{actual_bm_revenue_annual:,.0f}/year")
            print(f"      Difference: £{actual_bm_revenue_annual - model_bm_revenue_annual:,.0f}/year")
    
    print("\n" + "="*70)
    print("💡 RECOMMENDATION:")
    print("   If actual BM hours consistently differ >20% from model:")
    print("   1. Update BM_HOURS_PER_DAY in bess_revenue_stack_analyzer.py")
    print("   2. Re-run revenue analysis")
    print("   3. Track monthly to identify trends")
    print("="*70)

if __name__ == "__main__":
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/inner-cinema-credentials.json'
    compare_model_vs_actual()
