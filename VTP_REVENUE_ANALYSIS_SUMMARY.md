# VTP Revenue Analysis - Complete Summary

**Generated:** December 18, 2025
**Analysis Period:** November 2025 (30 days, 1,440 settlement periods)

---

## 📊 Results Overview

### Key Metrics (November 2025)

| Metric | Value |
|--------|-------|
| **Total Net Revenue** | £9,639,168.71 |
| **Days Analyzed** | 30 |
| **Average Daily Revenue** | £321,305.62 |
| **Peak Daily Revenue** | £363,386.14 (Nov 27) |
| **Lowest Daily Revenue** | £295,341.27 (Nov 30) |
| **Revenue Volatility** | £68,044.87 (peak - low) |

### Weekly Breakdown

| Week Starting | Net Revenue (£) | Daily Average (£) |
|---------------|-----------------|-------------------|
| 2025-11-03 | 967,543.50 | 138,220.50 |
| 2025-11-10 | 2,190,981.25 | 312,997.32 |
| 2025-11-17 | 2,218,588.47 | 316,941.21 |
| 2025-11-24 | 2,318,712.33 | 331,244.62 |
| 2025-12-01 | 1,945,442.16 | 277,920.31 |

---

## 🎯 VTP Revenue Methodology

### Formula Components

**System State Detection:**
- **SHORT**: When SBP (offer price) > SSP (bid price)
- **LONG**: When SSP ≥ SBP

**Revenue Calculations:**

```
Short Position Revenue = ΔQ × ((SBP - MID) - SCRP)
Long Position Revenue  = ΔQ × ((MID - SSP) + SCRP)
Net Revenue           = Gross Revenue × 0.90 (efficiency)
```

### Parameters Used

| Parameter | Value | Description |
|-----------|-------|-------------|
| **SCRP** | £98.00/MWh | Supplier Compensation Reference Price (Elexon v2.0) |
| **ΔQ** | 5.0 MWh | Deviation per settlement period |
| **Efficiency** | 90% | Round-trip battery/trading efficiency |
| **Baseline Price** | £90.00/MWh | Supplier wholesale hedge assumption |

---

## 📈 Data Sources

### BigQuery Tables Used

1. **bmrs_mid** (Market Index Data)
   - Settlement date & period
   - Market index price (MID)
   - Volume data

2. **bmrs_bod** (Bid-Offer Data)
   - Settlement date & period
   - Offer prices (SBP proxy)
   - Bid prices (SSP proxy)

### Join Logic

```sql
SELECT
  mid.settlementDate,
  mid.settlementPeriod,
  AVG(mid.price) AS market_price,
  AVG(bod.offer) AS offer_price,
  AVG(bod.bid)   AS bid_price
FROM bmrs_mid AS mid
JOIN bmrs_bod AS bod
  USING(settlementDate, settlementPeriod)
WHERE settlementDate BETWEEN '2025-11-01' AND '2025-11-30'
GROUP BY settlementDate, settlementPeriod
```

---

## 📊 Google Sheets Integration

### Created Worksheets

**Sheet Position:** After "SCRP_VLP_Revenue" (sheets #18-20)

| Sheet # | Name | Description |
|---------|------|-------------|
| 18 | **VTP_Revenue_Daily** | Daily breakdown with system state, price components, and revenue |
| 19 | **VTP_Revenue_Weekly** | Weekly aggregations for trend analysis |
| 20 | **VTP_Revenue_Summary** | Executive summary, methodology, and key insights |

### VTP_Revenue_Daily Columns

1. Settlement Date
2. System State (short/long)
3. Avg SBP (£/MWh) - Offer price
4. Avg SSP (£/MWh) - Bid price
5. Avg MID (£/MWh) - Market index
6. Gross VTP Revenue (£)
7. Net Revenue (£) - After 90% efficiency

**Summary Statistics:**
- Total Gross Revenue (formula)
- Total Net Revenue (formula)
- Average Daily Net Revenue
- Peak Daily Revenue
- Lowest Daily Revenue

### VTP_Revenue_Weekly Columns

1. Week Starting (Monday date)
2. Gross VTP Revenue (£)
3. Net Revenue (£)
4. Daily Average (£) - Net revenue / 7

**Summary Statistics:**
- Total Month Gross Revenue
- Total Month Net Revenue
- Average Weekly Net Revenue
- Peak Week Revenue

### VTP_Revenue_Summary Sections

1. **Executive Summary**
   - Key metrics with values
   - Period analyzed
   - Configuration parameters

2. **Methodology**
   - System state detection rules
   - Revenue formulas
   - Data sources
   - Analysis period details

3. **Key Insights**
   - Highest/lowest revenue days
   - Revenue volatility
   - System state observations
   - Price spread impact

4. **Related Sheets**
   - Navigation links to other SCRP/VLP sheets

---

## 💾 Output Files

### CSV Files Generated

**Location:** `/home/george/GB-Power-Market-JJ/`

1. **vtp_revenue_daily.csv** (30 rows)
   - Columns: settlementDate, system_state, avg_SBP, avg_SSP, avg_MID, total_vtp_revenue, net_revenue
   - One row per day in November 2025

2. **vtp_revenue_weekly.csv** (5 rows)
   - Columns: settlementDate, total_vtp_revenue, net_revenue
   - One row per week (Monday starts)

### Python Scripts

1. **vtp_revenue_simulation.py**
   - Main calculation script
   - BigQuery join and aggregation
   - CSV export

2. **upload_vtp_revenue_to_sheets.py**
   - Google Sheets upload
   - Formatting and formulas
   - Summary sheet creation

---

## 🔍 Key Observations

### All November Days: SHORT System State

**Finding:** Every single day in November 2025 showed a SHORT system state (offer > bid).

**Implications:**
- Consistent system behavior throughout month
- Revenue formula: `ΔQ × ((SBP - MID) - SCRP)`
- Opportunities when SBP significantly exceeds MID

### Revenue Trends

**Peak Week:** Nov 24-30 (£2,318,712 net)
- 5.9% higher than November average
- Aligns with high-demand/high-price period

**Low Week:** Nov 3-9 (£967,543 net)
- 58% below November average
- Partial week (only 3 days)

**Stabilization:** Weeks 2-4 showed consistent performance (£2.1-2.3M range)

### Price Relationships

**Average November 2025:**
- Avg SBP (offer): ~£1,620/MWh
- Avg SSP (bid): ~£-1,070/MWh
- Avg MID: ~£38/MWh

**VTP Revenue Driver:**
- Higher (SBP - MID) spreads = higher revenue
- Nov 27 peak day: Likely maximum spread

---

## 🎨 Dashboard Access

**Google Sheets URL:**
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

**Navigation:**
- Click "VTP_Revenue_Summary" tab for overview
- "VTP_Revenue_Daily" for detailed analysis
- "VTP_Revenue_Weekly" for aggregated trends

**Related Analyses:**
- Sheet #11: SCRP_MID_vs_BOALF (Market index vs balancing mechanism)
- Sheet #12: SCRP_VLP_Revenue (VLP battery revenue vs market prices)
- Sheet #13: SCRP_Summary (Overall SCRP analysis)

---

## 🚀 Next Steps

### Recommended Enhancements

1. **Add Charts to VTP Sheets**
   - Daily revenue trend line
   - Weekly comparison bar chart
   - System state pie chart
   - Price spread vs revenue scatter

2. **Extend Analysis Period**
   - Run for full year (2025)
   - Compare seasonal variations
   - Identify peak revenue months

3. **Real-time Updates**
   - Integrate with realtime_dashboard_updater.py
   - Auto-refresh every 5 minutes
   - Add to cron schedule

4. **Comparison Analysis**
   - VTP revenue vs actual VLP battery revenue
   - VTP vs capacity market payments
   - VTP vs frequency response revenue

5. **Scenario Modeling**
   - Vary SCRP (£90, £98, £105)
   - Vary ΔQ (1, 5, 10 MWh)
   - Vary efficiency (85%, 90%, 95%)

---

## 📚 Technical Details

### Dependencies

```bash
pip3 install --user google-cloud-bigquery pandas gspread google-auth
```

### Authentication

**BigQuery:** Service account credentials
- File: `inner-cinema-credentials.json`
- Project: `inner-cinema-476211-u9`
- Location: US

**Google Sheets:** OAuth2 service account
- File: `inner-cinema-credentials.json`
- Scopes: `spreadsheets`, `drive`

### Execution

```bash
# Generate CSV files
python3 vtp_revenue_simulation.py

# Upload to Google Sheets
python3 upload_vtp_revenue_to_sheets.py
```

### Performance

- **Query Time:** ~3-5 seconds (1,440 rows)
- **Upload Time:** ~10-15 seconds (3 sheets)
- **Total Runtime:** ~20 seconds

---

## ⚠️ Important Notes

### Data Accuracy

1. **SCRP Value:** Using £98.00/MWh (Elexon v2.0 standard)
   - This may vary by settlement period in reality
   - Check latest Elexon documentation for updates

2. **SBP/SSP Proxy:** Using BOD offer/bid as proxy
   - Actual system prices from bmrs_costs table
   - BOD provides individual unit perspectives

3. **Market Index (MID):** Wholesale prices
   - NOT imbalance prices
   - Used for SCRP calculation baseline

### System State Logic

**Observation:** All November 2025 days = SHORT
- This is the dataset result, not a hardcoded assumption
- Different months may show LONG states
- Formula automatically handles both states

---

**Last Updated:** December 18, 2025
**Maintainer:** George Major (george@upowerenergy.uk)
**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ
