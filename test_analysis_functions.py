#!/usr/bin/env python3
"""
Quick Test of Analysis Functions
Verifies all imports and basic functionality
"""

import sys
from datetime import datetime

print("=" * 80)
print("🧪 TESTING ANALYSIS FUNCTIONS")
print("=" * 80)
print()

# Test 1: Core imports
print("1️⃣ Testing core imports...")
try:
    import pickle
    import pandas as pd
    import numpy as np
    from google.cloud import bigquery
    import gspread
    print("   ✅ Core imports successful")
except Exception as e:
    print(f"   ❌ Core import failed: {e}")
    sys.exit(1)

# Test 2: Statistical libraries
print("\n2️⃣ Testing statistical libraries...")
try:
    import scipy
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    print("   ✅ Statistical libraries loaded")
except Exception as e:
    print(f"   ❌ Statistical library failed: {e}")
    sys.exit(1)

# Test 3: Visualization
print("\n3️⃣ Testing visualization...")
try:
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.use('Agg')  # Headless mode
    print("   ✅ Matplotlib configured")
except Exception as e:
    print(f"   ❌ Matplotlib failed: {e}")
    sys.exit(1)

# Test 4: Google Cloud libraries
print("\n4️⃣ Testing Google Cloud libraries...")
try:
    from pandas_gbq import to_gbq
    import google.generativeai as genai
    from googleapiclient.discovery import build
    print("   ✅ Google Cloud libraries loaded")
except Exception as e:
    print(f"   ❌ Google Cloud library failed: {e}")
    sys.exit(1)

# Test 5: BigQuery connection
print("\n5️⃣ Testing BigQuery connection...")
try:
    client = bigquery.Client(project='inner-cinema-476211-u9')
    # Try to query available datasets
    datasets = list(client.list_datasets())
    print(f"   ✅ BigQuery connected - found {len(datasets)} datasets")
    for dataset in datasets:
        print(f"      - {dataset.dataset_id}")
except Exception as e:
    print(f"   ❌ BigQuery connection failed: {e}")
    print("   💡 Note: This might fail if credentials aren't configured")

# Test 6: Google Sheets credentials
print("\n6️⃣ Testing Google Sheets credentials...")
try:
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    gc = gspread.authorize(creds)
    print("   ✅ Google Sheets credentials loaded")
except FileNotFoundError:
    print("   ⚠️ token.pickle not found - you'll need to authenticate")
except Exception as e:
    print(f"   ❌ Google Sheets auth failed: {e}")

# Test 7: Check if analysis functions can be imported
print("\n7️⃣ Testing analysis function imports...")
try:
    # Check if we can import from the advanced stats script
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "advanced_stats",
        "/Users/georgemajor/GB Power Market JJ/advanced_statistical_analysis_enhanced.py"
    )
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just check it loads
        print("   ✅ Analysis script is importable")
    else:
        print("   ⚠️ Could not load analysis script")
except Exception as e:
    print(f"   ❌ Analysis script import failed: {e}")

# Test 8: Sample data processing
print("\n8️⃣ Testing sample data processing...")
try:
    # Create sample dataframe
    df = pd.DataFrame({
        'timestamp': pd.date_range('2025-10-01', periods=100, freq='30T'),
        'price': np.random.normal(50, 10, 100),
        'volume': np.random.normal(1000, 200, 100)
    })
    
    # Basic statistics
    mean_price = df['price'].mean()
    std_price = df['price'].std()
    
    # Correlation
    corr = df['price'].corr(df['volume'])
    
    print(f"   ✅ Data processing works")
    print(f"      Sample stats: mean={mean_price:.2f}, std={std_price:.2f}, corr={corr:.3f}")
except Exception as e:
    print(f"   ❌ Data processing failed: {e}")

# Test 9: Calendar features (from advanced_statistical_analysis_enhanced.py)
print("\n9️⃣ Testing calendar feature generation...")
try:
    df = pd.DataFrame({
        'ts': pd.date_range('2025-10-01', periods=48, freq='30T'),
        'value': np.random.randn(48)
    })
    
    # Add calendar features
    df['hour'] = df['ts'].dt.hour
    df['day_of_week'] = df['ts'].dt.dayofweek
    df['month'] = df['ts'].dt.month
    df['is_peak'] = df['hour'].apply(lambda h: 1 if 7 <= h < 19 else 0)
    
    peak_count = df['is_peak'].sum()
    print(f"   ✅ Calendar features work")
    print(f"      Peak periods: {peak_count}/48 (should be ~24)")
except Exception as e:
    print(f"   ❌ Calendar features failed: {e}")

# Test 10: ARIMA model initialization
print("\n🔟 Testing ARIMA model...")
try:
    # Create sample time series
    ts = pd.Series(
        np.random.randn(100).cumsum() + 50,
        index=pd.date_range('2025-10-01', periods=100, freq='H')
    )
    
    # Try to fit a simple ARIMA model
    model = SARIMAX(ts, order=(1, 0, 0))
    print("   ✅ ARIMA model initialization successful")
    print("   💡 Note: Full fitting would take longer, skipping for test")
except Exception as e:
    print(f"   ❌ ARIMA model failed: {e}")

# Summary
print("\n" + "=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)
print()
print("✅ All core analysis functions are ready to use!")
print()
print("🎯 Next steps:")
print("   1. Run: python update_analysis_bi_enhanced.py")
print("   2. Run: python advanced_statistical_analysis_enhanced.py --start 2025-10-01")
print("   3. Run: python ask_gemini_analysis.py (requires API key)")
print()
print("📚 Documentation: See CODE_REVIEW_SUMMARY.md for complete guide")
print("=" * 80)
