# 🚀 Quick Reference: Enhanced BI Analysis Sheet

## Current Status: ✅ ALL WORKING

**Last Update**: October 31, 2025, 15:23:45  
**Data Range**: 30 days (Oct 1-31, 2025)  
**Sections**: 4/4 working with real data

---

## 📊 Latest Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Generation | 227,105 MWh | ✅ |
| Renewable % | 50.6% | ✅ Target! |
| Avg Frequency | 49.965 Hz | ✅ Normal |
| Avg Market Price | £37.46/MWh | ✅ |
| Peak Demand | 17,866 MW | ✅ |
| Grid Stability | Normal | ✅ |

---

## 🔗 Quick Links

**Sheet URL**:  
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

**Tab Name**: Analysis BI Enhanced

---

## ⚡ Quick Commands

### Refresh All Data
```bash
cd ~/GB\ Power\ Market\ JJ
python3 update_analysis_bi_enhanced.py
```

### Recreate Sheet (if needed)
```bash
python3 create_analysis_bi_enhanced.py
```

### Check Data Status
```bash
# Check how much data you have
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

tables = {
    'Generation': 'bmrs_fuelinst',
    'Frequency': 'bmrs_freq', 
    'Prices': 'bmrs_mid',
    'Balancing': 'bmrs_netbsad'
}

for name, table in tables.items():
    query = f'SELECT COUNT(*) as cnt FROM \`inner-cinema-476211-u9.uk_energy_prod.{table}\`'
    result = list(client.query(query).result())[0]
    print(f'{name:12} {result.cnt:,} rows')
"
```

---

## 📋 Data Sources

| Section | Table | IRIS Table | Status |
|---------|-------|------------|--------|
| Generation | `bmrs_fuelinst` | `bmrs_fuelinst_iris` | ✅ Both |
| Frequency | `bmrs_freq` | `bmrs_freq_iris` | ✅ Both |
| Prices | `bmrs_mid` | N/A | ✅ Historical |
| Balancing | `bmrs_netbsad` | N/A | ✅ Historical |

---

## 🎛️ Using the Dropdowns

### Quick Select (Cell B5)
Click and choose:
- **24 Hours** - Last day
- **1 Week** - Last 7 days ⭐ Default
- **1 Month** - Last 30 days ⭐ Current
- **3 Months** - Last 90 days
- **6 Months** - Last 180 days
- **1 Year** - Last 365 days
- **Custom** - Use D5 and F5

### Custom Dates
1. Set B5 to "Custom"
2. Enter start date in D5 (format: DD/MM/YYYY)
3. Enter end date in F5 (format: DD/MM/YYYY)
4. Run update script

---

## 📊 Understanding the Data

### Generation Mix Table
- **Fuel Type**: CCGT, Wind, Nuclear, Coal, etc.
- **Total MWh**: Total energy generated
- **Avg MW**: Average power output
- **% Share**: Percentage of total generation
- **Source Mix**: Historical vs IRIS record counts

### System Frequency Table
- **Timestamp**: When measured
- **Frequency (Hz)**: Actual grid frequency
- **Deviation (mHz)**: Distance from 50 Hz
- **Status**: Normal (49.8-50.2) or Alert
- **Source**: historical or real-time

### Market Index Data Table
- **Date**: Settlement date
- **Settlement Period**: 1-50 (48 per day)
- **Market Price**: £/MWh traded price
- **Volume**: MWh traded volume
- **Data Provider**: Source of data

### Balancing Costs Table
- **Cost Breakdown**: Buy and Sell costs
- **Net Cost**: Total balancing cost
- **Net Volume**: Total balancing volume
- **Price Adj**: Buy/Sell price adjustments

---

## 🔍 Troubleshooting

### "No data showing"
1. Check date range (might be too narrow)
2. Verify tables exist in BigQuery
3. Run update script again
4. Refresh browser (Ctrl+R or Cmd+R)

### "Old data still showing"
- Close and reopen the Google Sheet
- Or: File → Reload
- Or: Wait 1-2 minutes for cache to clear

### "Script fails"
```bash
# Check authentication
ls -la ~/GB\ Power\ Market\ JJ/token.pickle

# Check BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"

# Check Google Sheets connection  
python3 -c "import pickle; f=open('token.pickle','rb'); creds=pickle.load(f); print('✅ Token valid')"
```

---

## 📈 What the Metrics Mean

### Renewable %
- **Target**: 50%+ (UK net-zero pathway)
- **Includes**: Wind, Solar, Hydro, Biomass, Nuclear
- **Current**: 50.6% ✅ Meeting target!

### Grid Frequency
- **Nominal**: 50 Hz exactly
- **Normal Range**: 49.8 - 50.2 Hz
- **Warning**: 49.5 - 49.8 or 50.2 - 50.5 Hz
- **Critical**: <49.5 or >50.5 Hz
- **Current**: 49.965 Hz ✅ Normal

### Market Price
- **Typical Range**: £20-80/MWh
- **Low**: Off-peak, high renewables
- **High**: Peak demand, low renewables
- **Current**: £37.46/MWh (average)

---

## 💡 Tips

1. **Short date ranges load faster** - Use 1 Week for quick checks
2. **Monitor frequency for grid stress** - Watch for deviations
3. **Compare renewable % over time** - Track progress to targets
4. **Check balancing costs** - High costs = grid stress
5. **Use custom dates for events** - Analyze specific periods

---

## 📁 Related Files

- `create_analysis_bi_enhanced.py` - Setup script
- `update_analysis_bi_enhanced.py` - Refresh script
- `ENHANCED_BI_SUCCESS.md` - Full documentation
- `ENHANCED_BI_STATUS.md` - Status report
- `ENHANCED_BI_ANALYSIS_README.md` - Complete guide

---

**Need help?** Check ENHANCED_BI_SUCCESS.md for detailed explanations!
