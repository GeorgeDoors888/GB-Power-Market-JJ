#!/usr/bin/env python3
"""
Met Office DataPoint API Investigation

Evaluates cost-benefit of Met Office weather station data for wind forecasting.
Only proceed if ERA5 optimization achieves >15% improvement.

Met Office DataPoint features:
- 150 weather stations across UK
- 15-minute resolution (vs ERA5 hourly)
- Surface wind (10m) + pressure + temperature
- Cost: £1-2k/year for commercial license

Expected additional improvement: +10-15%
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Hypothetical Met Office stations near offshore wind farms
MET_OFFICE_STATIONS = {
    'ABERDEEN': (57.16, -2.08, ['Seagreen Phase 1', 'Moray East', 'Beatrice']),
    'LEUCHARS': (56.38, -2.86, ['Seagreen Phase 1', 'Neart Na Gaoithe']),
    'LOSSIEMOUTH': (57.72, -3.32, ['Moray East', 'Moray West', 'Beatrice']),
    'TIREE': (56.50, -6.88, ['Hywind Scotland', 'Kincardine']),
    'LIVERPOOL': (53.42, -2.98, ['Walney Extension', 'Burbo Bank', 'Ormonde']),
    'VALLEY': (53.25, -4.53, ['Rhyl Flats', 'North Hoyle']),
    'WITTERING': (52.61, -0.47, ['Triton Knoll', 'Race Bank', 'Sheringham Shoal']),
    'WATTISHAM': (52.13, 0.96, ['Greater Gabbard', 'Galloper']),
    'MANSTON': (51.35, 1.35, ['Thanet', 'London Array']),
    'SHOREHAM': (50.84, -0.30, ['Rampion']),
    'HURN': (50.78, -1.84, ['Rampion', 'Wight']),
    'CONINGSBY': (53.09, -0.17, ['Lincs', 'Lynn', 'Inner Dowsing']),
}

print("=" * 80)
print("Met Office DataPoint API - Cost-Benefit Analysis")
print("=" * 80)
print()

# Check if ERA5 optimization achieved >15% improvement
print("📊 Checking ERA5 optimization results...")

try:
    df_results = pd.read_csv('wind_power_curves_optimized_results.csv')
    
    baseline_mae = 90.0
    optimized_mae = df_results['mae'].mean()
    improvement = ((baseline_mae - optimized_mae) / baseline_mae) * 100
    
    print(f"   Baseline MAE: {baseline_mae:.1f} MW")
    print(f"   Optimized MAE: {optimized_mae:.1f} MW")
    print(f"   Improvement: {improvement:.1f}%")
    print()
    
    if improvement < 15:
        print(f"⚠️  THRESHOLD NOT MET")
        print(f"   Required: >15% improvement")
        print(f"   Achieved: {improvement:.1f}%")
        print(f"   Gap: {15 - improvement:.1f}%")
        print()
        print("Recommendation: Complete ERA5 optimization first before pursuing Met Office data.")
        exit(0)
    
    print(f"✅ THRESHOLD MET ({improvement:.1f}% > 15%)")
    print("   Proceeding with Met Office evaluation...")
    print()

except FileNotFoundError:
    print("⚠️  Optimization results not found. Run build_wind_power_curves_optimized.py first.")
    exit(1)

# Met Office DataPoint features
print("=" * 80)
print("Met Office DataPoint Features")
print("=" * 80)
print()

print("📡 Weather Stations:")
print(f"   Total stations: {len(MET_OFFICE_STATIONS)}")
print(f"   Coverage: UK mainland + islands")
print()

print("📊 Data Specifications:")
print("   Resolution: 15 minutes (vs ERA5 1 hour)")
print("   Variables: Wind speed, wind direction, pressure, temperature")
print("   Wind height: 10m (vs ERA5 100m) - requires extrapolation")
print("   Latency: ~10 minutes (near real-time)")
print()

print("💰 Cost Analysis:")
print("   License fee: £1,000-2,000/year (commercial use)")
print("   Data volume: ~2.5M observations/year (12 stations × 15min × 8760h × 2 vars)")
print("   Storage cost: Minimal (~£10/year in BigQuery)")
print("   Development time: 2-3 days integration")
print()

# Expected improvement calculation
print("=" * 80)
print("Expected Performance Improvement")
print("=" * 80)
print()

print("📈 Improvement Factors:")
print("   1. Higher temporal resolution (15min vs 1h): +3-5%")
print("   2. Coastal station proximity (<50km): +4-6%")
print("   3. Surface pressure gradients (storm prediction): +2-3%")
print("   4. Temperature effects (air density): +1-2%")
print()
print(f"   Total expected additional improvement: +10-15%")
print(f"   Current: {optimized_mae:.1f} MW → Target: {optimized_mae * 0.875:.1f} MW")
print()

# Business value calculation
revenue_per_mw_improvement = 8760 * 50 * 0.2  # hours × £/MWh × capture rate
additional_improvement_mw = optimized_mae * 0.125  # 12.5% mid-point

annual_value = additional_improvement_mw * revenue_per_mw_improvement

print("=" * 80)
print("Business Value Assessment")
print("=" * 80)
print()

print(f"💷 Revenue Impact:")
print(f"   Additional MAE improvement: {additional_improvement_mw:.1f} MW")
print(f"   Annual revenue uplift: £{annual_value:,.0f}/year")
print()

print(f"📊 ROI Calculation:")
cost = 1500  # Mid-point license fee
payback_months = (cost / annual_value) * 12
roi = ((annual_value - cost) / cost) * 100

print(f"   Annual cost: £{cost:,}")
print(f"   Annual benefit: £{annual_value:,.0f}")
print(f"   Payback period: {payback_months:.1f} months")
print(f"   ROI: {roi:.0f}%")
print()

if roi > 500:
    print("✅ STRONG ROI - Recommended to proceed")
    recommendation = "PROCEED"
elif roi > 200:
    print("✅ GOOD ROI - Recommended to proceed")
    recommendation = "PROCEED"
elif roi > 100:
    print("⚠️  MODERATE ROI - Consider proceeding")
    recommendation = "CONSIDER"
else:
    print("❌ WEAK ROI - Not recommended")
    recommendation = "SKIP"

print()

# Implementation plan
if recommendation in ['PROCEED', 'CONSIDER']:
    print("=" * 80)
    print("Implementation Plan")
    print("=" * 80)
    print()
    
    print("Phase 1: Setup (1-2 days)")
    print("   1. Register for Met Office DataPoint API key")
    print("   2. Test API access and data format")
    print("   3. Create BigQuery table: met_office_observations")
    print()
    
    print("Phase 2: Historical Download (2-3 days)")
    print("   1. Download 2020-2025 historical data")
    print("   2. Wind speed extrapolation: 10m → 100m using log law")
    print("   3. Upload to BigQuery and validate coverage")
    print()
    
    print("Phase 3: Model Integration (2-3 days)")
    print("   1. Add Met Office features to training pipeline")
    print("   2. Train hybrid models (ERA5 + Met Office)")
    print("   3. Validate >10% additional improvement")
    print()
    
    print("Phase 4: Real-Time Integration (1-2 days)")
    print("   1. Set up 15-minute API polling")
    print("   2. Update real-time forecasting pipeline")
    print("   3. Deploy to production")
    print()
    
    print(f"Total timeline: 6-10 days")
    print(f"Total cost: £{cost + 500:,} (license + development time)")
    print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()

if recommendation == "PROCEED":
    print("✅ PROCEED with Met Office DataPoint integration")
    print(f"   Expected total improvement: {improvement + 12.5:.1f}%")
    print(f"   Expected MAE: {optimized_mae * 0.875:.1f} MW")
    print(f"   Annual value: £{annual_value:,.0f}")
    print()
    print("Next steps:")
    print("   1. Register at: https://www.metoffice.gov.uk/services/data/datapoint")
    print("   2. Request commercial license quote")
    print("   3. Download historical data sample for testing")

elif recommendation == "CONSIDER":
    print("⚠️  CONSIDER Met Office DataPoint (moderate ROI)")
    print("   May be worth it if:")
    print("   - Real-time latency is critical (<10 min)")
    print("   - 15-min resolution needed for intraday trading")
    print("   - Pressure gradients improve storm prediction")

else:
    print("❌ SKIP Met Office DataPoint (weak ROI)")
    print("   Current ERA5 optimization provides sufficient accuracy")
    print("   Focus on model optimization and feature engineering instead")

print()
print("=" * 80)
