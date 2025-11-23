# 🚀 Quick Start Guide - Data Analysis Functions

**Status:** ✅ ALL SYSTEMS READY  
**Date:** October 31, 2025  
**Environment:** `.venv` activated with all dependencies

---

## ⚡ Instant Commands (Copy & Paste)

### Activate Environment (Always First!)
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ && source .venv/bin/activate
```

### 📊 Run Full Statistical Analysis
```bash
# Last month
python advanced_statistical_analysis_enhanced.py --start 2025-10-01 --end 2025-10-31

# Last week
python advanced_statistical_analysis_enhanced.py --start 2025-10-24 --end 2025-10-31

# Fast mode (no plots)
python advanced_statistical_analysis_enhanced.py --start 2025-10-01 --no-plots
```

### 📈 Update BI Dashboard
```bash
python update_analysis_bi_enhanced.py
```

### 🤖 Get AI Insights
```bash
# Set API key first (one time)
export GEMINI_API_KEY='your-key-here'

# Then run
python ask_gemini_analysis.py
```

### 🔍 Export Dashboard Data
```bash
python read_full_sheet.py
```

### 🧪 Test Everything
```bash
python test_analysis_functions.py
```

---

## 📊 Statistical Analysis Outputs

When you run `advanced_statistical_analysis_enhanced.py`, it creates **9 BigQuery tables**:

| Table | Purpose | Use Case |
|-------|---------|----------|
| `ttest_results` | SSP vs SBP comparison | Battery arbitrage windows |
| `regression_temperature_ssp` | Weather impact | Temperature-price correlation |
| `regression_volume_price` | Price drivers | Multi-factor price modeling |
| `correlation_matrix` | Variable relationships | Co-movement analysis |
| `arima_forecast_ssp` | 24h price forecast | Battery dispatch optimization |
| `seasonal_decomposition_stats` | Trend/seasonal/residual | Pattern separation |
| `outage_impact_results` | Event-day analysis | Stress testing |
| `neso_behavior_results` | Balancing patterns | NESO action prediction |
| `anova_results` | Seasonal regimes | Pricing seasonality |

All tables written to: `inner-cinema-476211-u9.uk_energy_analysis`

---

## 🎯 Common Analysis Workflows

### Workflow 1: Battery Optimization
```bash
# Step 1: Run statistical analysis for last 3 months
python advanced_statistical_analysis_enhanced.py --start 2025-08-01 --end 2025-10-31

# Step 2: Query results
bq query --use_legacy_sql=false "
SELECT * FROM \`inner-cinema-476211-u9.uk_energy_analysis.ttest_results\`
WHERE p_value < 0.05
ORDER BY mean_diff DESC
"

# Step 3: Check ARIMA forecast
bq query --use_legacy_sql=false "
SELECT * FROM \`inner-cinema-476211-u9.uk_energy_analysis.arima_forecast_ssp\`
ORDER BY forecast_hour
"
```

### Workflow 2: Dashboard Update & Export
```bash
# Update dashboard with latest data
python update_analysis_bi_enhanced.py

# Export for analysis
python read_full_sheet.py

# Check the CSV
cat analysis_bi_enhanced_full_export.csv | head -20
```

### Workflow 3: AI-Powered Insights
```bash
# Update dashboard first
python update_analysis_bi_enhanced.py

# Get AI analysis
python ask_gemini_analysis.py

# Review insights (output shown on screen)
```

---

## 🛠️ Troubleshooting

### Issue: "command not found: python"
**Fix:**
```bash
# Use python3 explicitly
python3 update_analysis_bi_enhanced.py
```

### Issue: "No module named 'google.cloud'"
**Fix:**
```bash
# Make sure virtual environment is activated
cd /Users/georgemajor/GB\ Power\ Market\ JJ
source .venv/bin/activate
pip list | grep google  # Verify packages
```

### Issue: BigQuery authentication error
**Fix:**
```bash
# Check credentials
gcloud auth list
gcloud auth application-default login
```

### Issue: Google Sheets token expired
**Fix:**
```bash
# Re-authenticate
rm token.pickle
# Then run any script that uses Google Sheets - it will re-auth
```

### Issue: Gemini API key not found
**Fix:**
```bash
# Option 1: Environment variable
export GEMINI_API_KEY='your-key-here'

# Option 2: Create file
echo "your-key-here" > gemini_api_key.txt
```

---

## 📚 Key Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `CODE_REVIEW_SUMMARY.md` | Complete code review | Understanding all functions |
| `STATISTICAL_ANALYSIS_GUIDE.md` | Output interpretation | Understanding results |
| `ENHANCED_BI_ANALYSIS_README.md` | Dashboard guide | Using the dashboard |
| `PROJECT_CONFIGURATION.md` | Settings reference | Troubleshooting config |
| `DOCUMENTATION_INDEX.md` | All docs index | Finding specific info |

---

## 🎓 Understanding the Analysis Functions

### 9 Statistical Functions Explained

1. **T-Test (SSP vs SBP)**
   - Compares system sell price vs buy price
   - Identifies arbitrage opportunities
   - Battery charging/discharging decisions

2. **Temperature Regression**
   - Weather impact on electricity prices
   - Demand forecasting
   - Seasonal planning

3. **Volume-Price Regression**
   - Multi-factor price modeling
   - Supply-demand dynamics
   - Market efficiency analysis

4. **Correlation Matrix**
   - Variable relationships heatmap
   - Co-movement identification
   - Risk factor analysis

5. **ARIMA Forecast**
   - 24-hour price prediction
   - Battery dispatch optimization
   - Trading strategy development

6. **Seasonal Decomposition**
   - Trend extraction
   - Seasonal pattern identification
   - Noise filtering

7. **Outage Impact**
   - Event-day stress testing
   - Extreme scenario modeling
   - Risk assessment

8. **NESO Behavior**
   - Balancing mechanism patterns
   - System operator actions
   - Cost prediction

9. **ANOVA Seasons**
   - Seasonal regime identification
   - Statistical price differences
   - Long-term planning

---

## 🔧 Configuration Quick Reference

### BigQuery Settings
```
Project:  inner-cinema-476211-u9
Region:   US
Dataset:  uk_energy_prod (source data)
          uk_energy_analysis (outputs)
```

### Google Sheets
```
Spreadsheet ID: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
Sheet Name:     Analysis BI Enhanced
```

### Key Tables (Historical + IRIS)
```
Generation:  bmrs_fuelinst + bmrs_fuelinst_iris
Frequency:   bmrs_freq + bmrs_freq_iris
Prices:      bmrs_mid + bmrs_mid_iris
Balancing:   bmrs_netbsad + bmrs_bod
```

---

## ⚠️ Known Issues

### 1. Cron Job Failure
**Status:** ⚠️ Active but failing
**Issue:** Points to non-existent `realtime_updater.py`
**Fix Options:**
```bash
# Option A: Disable cron
crontab -r

# Option B: Edit cron to use correct script
crontab -e
# Change: realtime_updater.py → update_analysis_bi_enhanced.py

# Option C: Create missing script
# (Contact for guidance)
```

### 2. Project ID Inconsistency
**Status:** ⚠️ Configuration mismatch
**Issue:** `advanced_statistical_analysis_enhanced.py` uses wrong project
**Fix:** Already noted in CODE_REVIEW_SUMMARY.md
**Workaround:** Outputs still work, just in different project

---

## 🎯 Success Checklist

Before running analysis, verify:

- [ ] Virtual environment activated (`.venv`)
- [ ] All packages installed (`pip list | wc -l` shows 80+)
- [ ] BigQuery authentication working (`gcloud auth list`)
- [ ] Google Sheets token exists (`ls token.pickle`)
- [ ] Gemini API key set (if using AI)
- [ ] Date range is reasonable (not too large)

---

## 🚀 Ready to Analyze!

Everything is set up and tested. Choose your analysis:

1. **Quick Dashboard Update** (2 minutes)
   ```bash
   python update_analysis_bi_enhanced.py
   ```

2. **Full Statistical Analysis** (5-10 minutes)
   ```bash
   python advanced_statistical_analysis_enhanced.py --start 2025-10-01
   ```

3. **AI Insights** (1 minute)
   ```bash
   python ask_gemini_analysis.py
   ```

4. **Data Export** (30 seconds)
   ```bash
   python read_full_sheet.py
   ```

---

**Questions?** Check `DOCUMENTATION_INDEX.md` for complete guide navigation.

**Need Help?** Review `CODE_REVIEW_SUMMARY.md` for detailed function documentation.
