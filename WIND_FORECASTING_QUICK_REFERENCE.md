# Wind Forecasting Quick Reference - Execution Commands

**Date**: December 30, 2025  
**Status**: All 12 todos completed - Ready to execute

---

## IMMEDIATE EXECUTION (Run these now)

### Step 1: Download Strategic ERA5 Grids (5 minutes)
```bash
cd /home/george/GB-Power-Market-JJ
python3 download_strategic_era5_grids.py
```
**Expected**: 8 grids, 421,472 observations, 5 minutes  
**Output**: BigQuery table `era5_wind_upstream` updated

### Step 2: Train Optimized Models (10-15 minutes)
```bash
python3 build_wind_power_curves_optimized.py
```
**Expected**: 28 XGBoost models, 15 features each, ~72 MW MAE  
**Output**: `models/wind_power_curves_optimized/` directory

### Step 3: Validate Performance (1 minute)
```bash
# Check results
cat wind_power_curves_optimized_results.csv | head -10

# Calculate improvement
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('wind_power_curves_optimized_results.csv')
baseline = 90.0
optimized = df['mae'].mean()
improvement = ((baseline - optimized) / baseline) * 100
print(f"Baseline: {baseline:.1f} MW")
print(f"Optimized: {optimized:.1f} MW")
print(f"Improvement: {improvement:.1f}%")
if improvement >= 20:
    print("✅ TARGET ACHIEVED!")
else:
    print(f"⚠️  Gap: {20 - improvement:.1f}%")
EOF
```

---

## DEPLOYMENT COMMANDS (After validation)

### Deploy Real-Time Forecasting
```bash
# Test manually
python3 realtime_wind_forecasting.py

# View output
ls -lh wind_forecasts_*.csv
```

### Deploy Wind Drop Alerts
```bash
# Test manually
python3 wind_drop_alerts.py

# View alerts
ls -lh wind_drop_alerts_*.csv

# Add to crontab (every 15 minutes)
crontab -e
# Add this line:
# */15 * * * * cd /home/george/GB-Power-Market-JJ && python3 wind_drop_alerts.py >> logs/wind_alerts.log 2>&1
```

### Deploy Dashboard Graphics
```bash
python3 add_wind_forecasting_dashboard.py
```
**View**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

### Met Office Investigation (Conditional)
```bash
# Only run if optimized model achieves >15% improvement
python3 investigate_met_office.py
```

---

## VERIFICATION COMMANDS

### Check ERA5 Grid Coverage
```bash
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = '''
SELECT 
    grid_point,
    COUNT(*) as observations,
    MIN(time_utc) as first_date,
    MAX(time_utc) as last_date
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_wind_upstream`
GROUP BY grid_point
ORDER BY grid_point
'''
df = client.query(query).to_dataframe()
print(f"Total grid points: {len(df)}")
print(f"Total observations: {df['observations'].sum():,}")
print(df)
EOF
```
**Expected**: 18 grid points (10 original + 8 strategic)

### Check Model Files
```bash
ls -lh models/wind_power_curves_optimized/ | head -10
echo "Total models:"
ls models/wind_power_curves_optimized/*.pkl | wc -l
```
**Expected**: 28 model files

### Check Feature Importance
```bash
python3 << 'EOF'
import joblib
import pandas as pd

# Load one model
model_data = joblib.load('models/wind_power_curves_optimized/Hornsea_One_optimized_model.pkl')
model = model_data['model']
features = model_data['features']

# Get feature importance
importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("Top 10 Features:")
print(importance.head(10))
EOF
```

---

## MONITORING COMMANDS

### Monitor Forecast Accuracy (Daily)
```bash
python3 << 'EOF'
import pandas as pd
from datetime import datetime, timedelta

# Check recent forecasts
df = pd.read_csv(f'wind_forecasts_{datetime.now().strftime("%Y%m%d")}*.csv')
print(f"Forecasts generated: {len(df)}")
print(f"Farms: {df['farm_name'].nunique()}")
print(f"Avg forecast: {df['forecast_mw'].mean():.0f} MW")
print(f"Trading signals:")
print(df['signal'].value_counts())
EOF
```

### Monitor Wind Alerts (Real-time)
```bash
# Check latest alerts
ls -lt wind_drop_alerts_*.csv | head -1 | xargs cat

# Count critical alerts
python3 << 'EOF'
import pandas as pd
import glob

latest = sorted(glob.glob('wind_drop_alerts_*.csv'))[-1]
df = pd.read_csv(latest)
print(f"Total alerts: {len(df)}")
print(f"Critical: {len(df[df['alert_level'] == 'CRITICAL'])}")
print(f"Warning: {len(df[df['alert_level'] == 'WARNING'])}")
print(f"Stable: {len(df[df['alert_level'] == 'NORMAL'])}")
EOF
```

### Monitor Model Performance (Weekly)
```bash
python3 << 'EOF'
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

# Compare last week's forecasts vs actuals
query = '''
SELECT 
    farm_name,
    AVG(ABS(forecast_mw - actual_mw)) as mae
FROM forecast_accuracy_tracking
WHERE forecast_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY farm_name
ORDER BY mae
'''

df = client.query(query).to_dataframe()
print(f"Weekly MAE: {df['mae'].mean():.1f} MW")
print("\nWorst performers:")
print(df.tail(5))
EOF
```

---

## ROLLBACK COMMANDS (If needed)

### Revert to ERA5 Basic Models
```bash
# Use ERA5 basic models instead of optimized
cp -r models/wind_power_curves_era5/ models/wind_power_curves_active/
```

### Revert to Spatial Models
```bash
# Use spatial-only models
cp -r models/wind_power_curves_spatial/ models/wind_power_curves_active/
```

### Revert to Baseline
```bash
# Use baseline B1610 models
cp -r models/wind_power_curves_actual/ models/wind_power_curves_active/
```

---

## TROUBLESHOOTING

### Download Fails
```bash
# Check internet connection
ping -c 3 archive-api.open-meteo.com

# Check credentials
ls -lh inner-cinema-credentials.json

# Retry with verbose logging
python3 download_strategic_era5_grids.py 2>&1 | tee download.log
```

### Training Fails
```bash
# Check memory
free -h

# Check disk space
df -h

# Run with smaller batch
# Edit build_wind_power_curves_optimized.py:
# Change n_estimators from 300 to 200
```

### XGBoost Import Error
```bash
# Reinstall XGBoost
pip3 uninstall xgboost -y
pip3 install --user xgboost

# Check installation
python3 -c "import xgboost as xgb; print(xgb.__version__)"
```

### BigQuery Timeout
```bash
# Increase timeout
export BIGQUERY_TIMEOUT=600

# Or run query in smaller chunks
# Edit query to add: LIMIT 100000
```

---

## SUCCESS CRITERIA

### ✅ Download Complete
- 18 grid points in `era5_wind_upstream` table
- 947,312 total observations (525,840 original + 421,472 strategic)
- Date range: 2020-01-01 to 2025-12-30

### ✅ Training Complete
- 28 model files in `models/wind_power_curves_optimized/`
- Average MAE < 75 MW (target: 72 MW)
- Total improvement > 20% (vs 90 MW baseline)

### ✅ Deployment Complete
- Real-time forecasting generating 4 horizons
- Wind alerts running every 15 minutes (cron)
- Dashboard updated with graphics
- All systems green in monitoring

---

## NEXT ACTIONS CHECKLIST

- [ ] Execute Step 1: Download strategic ERA5 grids
- [ ] Execute Step 2: Train optimized models  
- [ ] Execute Step 3: Validate performance (>20%?)
- [ ] Deploy real-time forecasting
- [ ] Deploy wind drop alerts (cron)
- [ ] Deploy dashboard graphics
- [ ] Evaluate Met Office (if >15%)
- [ ] Set up monitoring alerts
- [ ] Document operations runbook
- [ ] Train operations team

---

**Quick Reference**: WIND_FORECASTING_QUICK_REFERENCE.md  
**For Details**: See WIND_FORECASTING_COMPLETE_IMPLEMENTATION.md  
**Status**: ✅ Ready to execute  
**Date**: December 30, 2025
