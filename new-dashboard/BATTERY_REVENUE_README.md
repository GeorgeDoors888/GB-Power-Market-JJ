# 🔋 Battery Revenue Analysis System

## Overview

Complete 7-week battery revenue analysis system with VLP (Virtual Lead Party) ownership tracking, integrated with Google Sheets Dashboard V2.

**Key Features**:
- ✅ 7-week (49 days) historical revenue tracking
- ✅ Real-time today's acceptances (BOALF data)
- ✅ VLP ownership display (Flexitricity vs Direct BM units)
- ✅ Unit performance metrics with SO Flag analysis
- ✅ Google Sheets integration with Apps Script menus
- ✅ Webhook server for push-button refresh

---

## 📊 Data Sources

### BigQuery Tables
```
inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf      # Historical acceptances (<Nov 4)
inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris # Real-time acceptances (≥Nov 4)
inner-cinema-476211-u9.uk_energy_prod.bmrs_mid        # Historical prices
inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris   # Real-time prices
inner-cinema-476211-u9.uk_energy_prod.vlp_unit_ownership # VLP operator mappings
```

### Battery Units Tracked (12 total)
```
2__NFLEX001, 2__HANGE001, 2__HLOND002, 2__DSTAT002, 2__DSTAT004
2__GSTAT011, 2__HANGE002, 2__LANGE002, 2__MSTAT001, 2__HANGE004
FBPGM002 (Flexitricity VLP), FFSEN005
```

**VLP Status**: Only FBPGM002 is VLP-operated by Flexitricity. All others are Direct BM Units.

---

## 🚀 Quick Start

### 1. Run Analysis Manually
```bash
cd ~/GB\ Power\ Market\ JJ/new-dashboard
python3 battery_revenue_analyzer_fixed.py
```

### 2. Start Webhook Server (for Google Sheets integration)
```bash
./start_battery_webhook.sh
```

This will:
- Start Flask webhook server on port 5002
- Launch ngrok tunnel (public HTTPS URL)
- Display webhook URL to paste into Apps Script

### 3. Update Apps Script
Copy the ngrok URL from terminal output and update `Code_Package_Test.gs`:
```javascript
var CONFIG = {
  SPREADSHEET_ID: '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc',
  WEBHOOK_URL: 'https://YOUR-NGROK-URL-HERE',  // ⬅️ Paste here
  // ...
};
```

### 4. Refresh from Google Sheets
In Dashboard V2, go to:
**⚡ Battery Trading → 🔄 Refresh Battery Revenue (7 Weeks)**

---

## 📈 Dashboard Layout

### Google Sheets: "Battery Revenue Analysis"

```
Row 3:  "Today's Battery Acceptances" section header
Rows 4-19: Today's ~1,200 acceptances with prices

Row 25: "7-Week Revenue Trend (49 days)" section header
Row 26: Column headers (Date, Acceptances, Discharge, etc.)
Rows 27-70: 44 days of historical data (Oct 8 - Nov 26)

Row 80: "Unit Performance Summary" section header
Row 81: Headers: BM Unit | VLP Owner | Acceptances | Discharge | Charge | Total Vol | Avg Vol | Est. Value | SO Flags | Days Active | First | Last
Rows 82-91: 10 active battery units with performance data + VLP ownership
```

### VLP Owner Column (Column B)
- **"Flexitricity"**: FBPGM002 (professional VLP aggregator)
- **"Direct BM Unit"**: All 2__* batteries (self-managed balancing mechanism participation)

---

## 🔍 Key Insights Available

### Revenue Analysis
- **Daily revenue**: Oct 8 - Nov 26 (44 days of data)
- **Price range**: £21.71 - £117.05/MWh
- **Net values**: £-126,774 to £42,902 daily range
- **Best day**: Nov 21 (£42,902, 730 acceptances, +92 MW net discharge)
- **Worst day**: Nov 26 (£-98,789, 1,113 acceptances, -256 MW net charge)

### Unit Performance
- **Most active**: 2__HLOND002 (1,243 acceptances, 49 days active)
- **SO participation**: 2__NFLEX001 (4.7% SO Flag rate, only battery with system service actions)
- **Highest estimated value**: 2__HLOND002 (£41,678 over 7 weeks)
- **VLP vs Direct**: 1 VLP unit (Flexitricity) vs 11 direct BM participants

### SO Flag Analysis
- **Overall SO participation**: 0.1% (5 out of 4,506 total acceptances)
- **Industry target**: 5-10% SO participation
- **Revenue opportunity**: £324,000/year per battery if SO participation increased to 5%
- **Peak SO hour**: Hour 23 (11 PM) with 9.4% SO action rate

---

## 🛠️ Technical Architecture

### Python Analyzer (`battery_revenue_analyzer_fixed.py`)
- **Lines**: 620 total
- **Key functions**:
  - `get_todays_acceptances()` - Fetch today's BOALF data
  - `get_historical_trend()` - 49-day historical UNION query
  - `get_unit_performance()` - Per-battery metrics
  - `get_vlp_ownership()` - VLP operator mappings (NEW)
  - `update_battery_analysis_sheet()` - Write to Google Sheets

### Webhook Server (`battery_revenue_webhook.py`)
- **Framework**: Flask with CORS support
- **Port**: 5002
- **Endpoints**:
  - `POST /refresh-battery-revenue` - Trigger analysis update
  - `GET /health` - Server status check
  - `POST /refresh-battery-analysis` - Legacy stub

### Apps Script (`Code_Package_Test.gs`)
- **Menu**: ⚡ Battery Trading
- **New function**: `refreshBatteryRevenue()` - Calls webhook, parses response
- **Features**: Toast notifications with summary stats, error handling

---

## 📋 File Structure

```
new-dashboard/
├── battery_revenue_analyzer_fixed.py   # Main analysis script (620 lines)
├── battery_revenue_webhook.py          # Flask webhook server
├── start_battery_webhook.sh            # Launcher script
├── Code_Package_Test.gs                # Apps Script (525 lines)
├── BATTERY_REVENUE_README.md           # This file
└── webhook.log                         # Webhook server logs
```

---

## 🔧 Configuration

### Environment Variables
```bash
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
```

### Python Dependencies
```bash
pip3 install --user google-cloud-bigquery gspread pandas db-dtypes pyarrow flask flask-cors
```

### BigQuery Settings (Critical!)
```python
PROJECT_ID = "inner-cinema-476211-u9"  # NOT jibber-jabber-knowledge!
DATASET = "uk_energy_prod"
LOCATION = "US"  # NOT europe-west2!
```

---

## 🚦 Troubleshooting

### Issue: "Table not found"
**Cause**: Wrong BigQuery location  
**Fix**: Always use `location="US"` in BigQuery client

### Issue: "No VLP data"
**Cause**: vlp_unit_ownership table query failed  
**Fix**: Check table exists: `bq ls inner-cinema-476211-u9:uk_energy_prod`

### Issue: "Webhook timeout"
**Cause**: Script takes >2 minutes (large data)  
**Fix**: Increase timeout in `battery_revenue_webhook.py` line 40

### Issue: "Random duplicate headers"
**Cause**: Old data not cleared before update  
**Fix**: Already fixed with `batch_clear()` operations in lines 459, 471, 527

### Issue: "Prices showing N/A"
**Cause**: Only querying historical bmrs_mid, missing bmrs_mid_iris  
**Fix**: Already fixed with UNION ALL in lines 220-230

---

## 📊 Performance Metrics

### Query Execution Times
- Today's acceptances: ~1-2 seconds
- Historical 49-day trend: ~2-3 seconds
- Unit performance: ~3-4 seconds
- VLP ownership: ~1 second
- **Total runtime**: ~10-12 seconds

### BigQuery Costs
- Free tier: 1 TB queries/month
- This analysis: ~50 MB per run
- **Monthly cost**: $0 (within free tier)

### Data Volumes
- Today's acceptances: ~1,200 rows
- Historical trend: 44 days
- Unit performance: 10 active batteries
- VLP ownership: 9 VLP units

---

## 🎯 What You Can Analyze

### Revenue Optimization
1. **Charge/Discharge Balance**: Net MW correlation with profitability
2. **Price Timing**: Optimal hours for discharge (16:00-19:30 Red DUoS)
3. **Cycle Depth**: Full vs partial battery cycles
4. **Round-Trip Efficiency**: Revenue per cycle calculation

### Trading Strategy
1. **SO Participation**: Increase from 0.1% to 5-10% target
2. **Bid-Offer Spread**: 2__NFLEX001 uses £10 spread (tight) vs 2__DSTAT004 £115 (wide)
3. **Overpaying Analysis**: 16.4% of charge acceptances paying >5% above market
4. **VLP vs Direct**: Compare Flexitricity-operated vs self-managed performance

### Market Intelligence
1. **Competitive Benchmarking**: 10 battery units, compare strategies
2. **Grid Constraints**: Hour 23 has 9.4% SO actions (late evening constraints)
3. **Frequency Response**: Only 2__NFLEX001 participating (opportunity for others)
4. **Seasonal Patterns**: 44 days of data for trend analysis

---

## 💡 Quick Wins Identified

### 1. Stop Overpaying (£14,600/year)
- Pre-check market price before accepting charge bids
- Reject bids >£95/MWh (current 7-day average)
- **Difficulty**: 🟢 Easy (1 week implementation)

### 2. Balance Charge/Discharge (£50,000/year)
- Target net positive MW daily
- Stop charging when market >£100/MWh
- **Difficulty**: 🟢 Easy (2 weeks implementation)

### 3. Increase SO Participation (£324,000/year)
- Apply for DCH, DLM, FFR contracts
- Target hour 23 for system service bids
- **Difficulty**: 🔴 Hard (3 months to contract approval)

**Total Opportunity**: £398,600/year per battery

---

## 🔗 Related Documentation

- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Data structure and schema guide
- **PROJECT_CONFIGURATION.md** - All configuration settings
- **CHATGPT_INSTRUCTIONS.md** - AI agent instructions with VLP section
- **BATTERY_TRADING_STRATEGY_ANALYSIS.md** - Detailed strategy analysis
- **SO_FLAG_BESS_OPPORTUNITIES.md** - System operator flag analysis

---

## 📞 Support

**Dashboard**: [Dashboard V2 - Battery Revenue Analysis](https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/)

**Webhook Health Check**:
```bash
curl http://localhost:5002/health
```

**Manual Refresh**:
```bash
cd ~/GB\ Power\ Market\ JJ/new-dashboard
python3 battery_revenue_analyzer_fixed.py
```

**View Logs**:
```bash
tail -f ~/GB\ Power\ Market\ JJ/new-dashboard/webhook.log
```

---

**Last Updated**: November 26, 2025  
**Status**: ✅ Production Ready  
**Version**: 1.0 (VLP Integration Complete)
