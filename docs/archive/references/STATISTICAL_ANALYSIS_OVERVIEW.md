# 📊 Statistical Analysis Functionality Overview

**Date:** October 31, 2025  
**Status:** ✅ Available & Ready  
**Purpose:** Understanding your advanced statistical analysis capabilities

---

## 🎯 What You Have

You have a **comprehensive statistical analysis suite** that generates **9 key outputs** for GB power market analysis:

### 1. **T-Test Results** (SSP vs SBP)
- **Purpose:** Identifies arbitrage opportunities between System Sell Price and System Buy Price
- **Use Case:** Battery storage optimization (when to charge vs discharge)
- **Output:** Statistical comparison showing if price differences are significant
- **Table:** `ttest_results`

### 2. **Temperature Regression** 
- **Purpose:** Quantifies how temperature affects electricity prices
- **Use Case:** Weather-based demand forecasting, seasonal planning
- **Output:** Regression coefficients + scatter plot with trend line
- **Table:** `regression_temperature_ssp`

### 3. **Volume-Price Regression**
- **Purpose:** Multi-factor price modeling (demand, wind, temperature)
- **Use Case:** Understanding price formation mechanics
- **Output:** Regression showing impact of each factor on prices
- **Table:** `regression_volume_price`

### 4. **Correlation Matrix**
- **Purpose:** Shows relationships between all market variables
- **Use Case:** Portfolio risk analysis, variable selection for models
- **Output:** Correlation table + heatmap visualization
- **Table:** `correlation_matrix`

### 5. **ARIMA Forecast**
- **Purpose:** 24-hour price prediction using time series modeling
- **Use Case:** Battery dispatch scheduling, trading strategy
- **Output:** Hour-by-hour forecast with 95% confidence intervals
- **Table:** `arima_forecast_ssp`

### 6. **Seasonal Decomposition**
- **Purpose:** Separates price data into trend, seasonal, and random components
- **Use Case:** Long-term planning, identifying systematic patterns
- **Output:** 4-panel plot showing each component + variance stats
- **Table:** `seasonal_decomposition_stats`

### 7. **Outage Impact Analysis**
- **Purpose:** Measures how system events affect price spreads
- **Use Case:** Risk management, stress testing
- **Output:** Comparison of spreads during vs outside events
- **Table:** `outage_impact_results`

### 8. **NESO Behavior Analysis**
- **Purpose:** Links balancing costs to price spreads
- **Use Case:** Predicting National ESO actions, cost forecasting
- **Output:** Regression showing cost-spread relationship
- **Table:** `neso_behavior_results`

### 9. **ANOVA Seasonal Analysis**
- **Purpose:** Tests if prices differ significantly by season
- **Use Case:** Seasonal trading strategies, long-term contracts
- **Output:** Statistical test showing seasonal price regimes
- **Table:** `anova_results`

---

## ⚠️ Configuration Issues in Your Code

Your posted code has **THREE critical configuration problems**:

### Issue 1: Wrong Project ID ❌
```python
# Current (WRONG):
PROJECT_ID = "jibber-jabber-knowledge"      # You don't have permissions!
LOCATION   = "europe-west2"                  

# Should be:
PROJECT_ID = "inner-cinema-476211-u9"       # Your main project
LOCATION   = "US"                            # Correct region
```

### Issue 2: Wrong Dataset Names ❌
```python
# Current (WRONG):
DATASET_SOURCE = "uk_energy"                 # Doesn't exist in your project

# Should be:
DATASET_SOURCE = "uk_energy_prod"            # Your actual dataset
```

### Issue 3: Wrong Table Names ❌
The code references tables that don't exist in your project:
- `elexon_bid_offer_acceptances` → Should be `bmrs_bod`
- `elexon_demand_outturn` → Should be `bmrs_fuelinst` (for generation)
- `elexon_system_warnings` → Check if exists or skip
- `neso_demand_forecasts` → Check if exists
- `neso_wind_forecasts` → Check if exists
- `neso_balancing_services` → Check if exists

---

## ✅ Corrected Configuration

Here's what you should use:

```python
# =========================
# ========= CONFIG ========
# =========================
PROJECT_ID = "inner-cinema-476211-u9"       # ✅ Your main project
LOCATION   = "US"                            # ✅ Correct region
DATASET_SOURCE    = "uk_energy_prod"         # ✅ Your dataset
DATASET_ANALYTICS = "uk_energy_analysis"     # ✅ Output dataset

# Optional: GCS bucket for plots
GCS_BUCKET = ""  # Leave empty to save locally

# Analysis window
DATE_START = "2024-01-01"  # Start with recent data
DATE_END   = "2025-10-31"
```

---

## 📋 Your Actual Available Tables

Based on your setup, you have these BMRS tables:

### Core Tables (Confirmed)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `bmrs_bod` | Bid-Offer Data | settlement_date, settlement_period, bid_price, offer_price |
| `bmrs_fuelinst` | Generation by Fuel Type | publishTime, fuelType, generation |
| `bmrs_freq` | System Frequency | timestamp, frequency |
| `bmrs_mid` | Market Index Data | settlement_date, settlement_period, price |
| `bmrs_netbsad` | Balancing Services | settlement_date, settlement_period, cost |

### IRIS Real-Time Tables
| Table | Purpose | Note |
|-------|---------|------|
| `bmrs_fuelinst_iris` | Real-time generation | Last 24-48 hours |
| `bmrs_freq_iris` | Real-time frequency | Last 24-48 hours |
| `bmrs_mid_iris` | Real-time prices | Last 24-48 hours |

---

## 🔧 What Needs to Be Modified

To make this analysis work with YOUR data, you need to:

### Step 1: Fix Configuration (Easy)
Update the constants at the top of the script:
- Change PROJECT_ID
- Change LOCATION
- Change DATASET_SOURCE

### Step 2: Rewrite Data Loading Function (Complex)
The `load_harmonised_frame()` function needs to be completely rewritten because:
1. Your tables have different names
2. Your tables have different schemas
3. You may not have all the data sources (NESO forecasts, warnings, etc.)

### Step 3: Simplify or Skip Missing Data
You might not have:
- Temperature forecasts
- Wind forecasts
- System warnings
- Detailed balancing services data

**Options:**
A. Skip analyses that need missing data
B. Use alternative data sources
C. Simplify to only use available data

---

## 🎯 Recommended Approach

### Option A: Use Your Existing Script
Your current `advanced_statistical_analysis_enhanced.py` is **already configured correctly** for your project! 

✅ It uses: `inner-cinema-476211-u9`  
✅ It uses: `uk_energy_prod`  
✅ It uses: `US` region

**Just run it:**
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
source .venv/bin/activate
python advanced_statistical_analysis_enhanced.py --start 2025-10-01 --end 2025-10-31
```

### Option B: Create Simplified Version
Create a new script that only uses data you **definitely have**:

```python
# simplified_analysis.py
from google.cloud import bigquery
import pandas as pd
from scipy import stats
import numpy as np

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID)

# Query only tables you have
query = f"""
SELECT 
    settlement_date,
    settlement_period,
    bid_price,
    offer_price,
    (offer_price - bid_price) AS spread
FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
WHERE settlement_date >= '2025-10-01'
AND settlement_date <= '2025-10-31'
ORDER BY settlement_date, settlement_period
"""

df = client.query(query).to_dataframe()

# Simple T-test
bids = df['bid_price'].dropna()
offers = df['offer_price'].dropna()
tstat, pval = stats.ttest_ind(bids, offers)

print(f"Bid vs Offer T-Test:")
print(f"  t-statistic: {tstat:.3f}")
print(f"  p-value: {pval:.6f}")
print(f"  Mean bid: £{bids.mean():.2f}/MWh")
print(f"  Mean offer: £{offers.mean():.2f}/MWh")
```

---

## 📊 What Each Analysis Tells You

### For Battery Storage Operators:
- **T-Test**: Shows if SSP/SBP spread is profitable
- **ARIMA Forecast**: Predicts when to charge/discharge
- **Seasonal Decomposition**: Identifies best trading months
- **Correlation Matrix**: Shows relationships between price drivers

### For Solar PV Operators:
- **Temperature Regression**: Links weather to prices
- **Volume-Price Regression**: Shows how generation affects prices
- **Seasonal Analysis**: Identifies curtailment risk periods

### For Market Analysts:
- **NESO Behavior**: Predicts system operator actions
- **Outage Impact**: Quantifies event risks
- **Correlation Matrix**: Portfolio risk assessment

### For All Users:
- **All outputs written to BigQuery** for further analysis
- **Plots saved as PNG files** for reports
- **Statistical significance** for decision-making confidence

---

## 🚀 Quick Start (Using Existing Script)

Your existing script is **better** than the one you posted because it's already configured for your project!

### 1. Test with Recent Data (Fast)
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
source .venv/bin/activate

# Last month only (2-3 minutes)
python advanced_statistical_analysis_enhanced.py \
  --start 2025-10-01 \
  --end 2025-10-31 \
  --no-plots
```

### 2. Full Analysis (Slower)
```bash
# Full year with plots (5-10 minutes)
python advanced_statistical_analysis_enhanced.py \
  --start 2025-01-01 \
  --end 2025-10-31
```

### 3. Check Output Tables
```bash
# List created tables
bq ls inner-cinema-476211-u9:uk_energy_analysis

# View sample results
bq head -n 10 inner-cinema-476211-u9:uk_energy_analysis.ttest_results
```

---

## 🔍 Understanding Your Data Needs

The posted code expects this data structure:

### Required (Minimum):
- ✅ **Prices**: SSP and SBP (you have via `bmrs_bod` or `bmrs_mid`)
- ✅ **Timestamps**: Settlement dates/periods (you have)

### Optional (Enhances Analysis):
- ⚠️ **Temperature**: Weather data (may not have)
- ⚠️ **Volume**: Demand data (check if in your tables)
- ⚠️ **Wind Generation**: Renewable output (check if in your tables)
- ⚠️ **System Warnings**: Events/outages (check if in your tables)
- ⚠️ **Balancing Costs**: NESO charges (check if in your tables)

### What to Do:
1. Run `SHOW TABLES` to see what you have
2. Run `DESCRIBE` on key tables to see columns
3. Modify queries to use your actual schema

---

## 📚 Next Steps

### Immediate Actions:

1. **Use Your Existing Script** (Recommended)
   ```bash
   python advanced_statistical_analysis_enhanced.py --start 2025-10-01
   ```

2. **Or Fix the Posted Code**
   - Update PROJECT_ID to `inner-cinema-476211-u9`
   - Update LOCATION to `US`
   - Update DATASET_SOURCE to `uk_energy_prod`
   - Rewrite queries to use your table names/schemas

3. **Or Create Simplified Version**
   - Start with just `bmrs_bod` analysis
   - Add more data sources as you verify they exist

### Documentation:
- **CODE_REVIEW_SUMMARY.md** - Your existing script documentation
- **STATISTICAL_ANALYSIS_GUIDE.md** - How to interpret outputs
- **PROJECT_CONFIGURATION.md** - Correct configuration settings

---

## ✅ Summary

**What You Have:**
- ✅ Powerful statistical analysis capabilities
- ✅ 9 different analysis functions
- ✅ Existing script already configured for your project
- ✅ All dependencies installed

**What's Wrong with Posted Code:**
- ❌ Uses wrong project ID
- ❌ Uses wrong region
- ❌ Uses wrong table names
- ❌ Assumes data you may not have

**What to Do:**
1. **Use your existing `advanced_statistical_analysis_enhanced.py`** (already correct!)
2. Or fix the posted code's configuration
3. Or create simplified version with only your available data

**Best Approach:**
```bash
# Just run what you already have!
python advanced_statistical_analysis_enhanced.py --start 2025-10-01 --end 2025-10-31
```

Your existing code is **production-ready** and properly configured. The posted code is from a different project setup and needs adaptation.

---

**Questions?** Check CODE_REVIEW_SUMMARY.md for complete function documentation.
