# Analysis Sheet Report System - User Guide

**Created**: December 22, 2025
**Google Sheet**: Analysis Tab

---

## 📊 Overview

The Analysis sheet now has a **complete dropdown-driven report system** that generates custom reports and graphs based on 8 data categories.

---

## 🎯 How to Use

### Step 1: Set Filters (Rows 4-9)

| Row | Filter | Options |
|-----|--------|---------|
| **Row 4** | Date Range | From Date (B4), To Date (D4) |
| **Row 5** | Party Role | Generator, Supplier, Trader, Interconnector, Storage |
| **Row 6** | BMU IDs | 1,644 units (searchable) |
| **Row 7** | Unit Names | 2,717 units with company names |
| **Row 8** | Generation Type | WIND, NUCLEAR, CCGT, BIOMASS, etc. |
| **Row 9** | Lead Party | 258 party prefixes |

**Tip**: Use "All" for no filtering

### Step 2: Choose Report Category (Row 11)

Select from 8 data categories:

| Category | What It Analyzes |
|----------|------------------|
| **⚡ Generation & Fuel Mix** | MW output by fuel type, wind/solar forecasts, unit generation |
| **💰 Balancing Mechanism (Trading)** | Bid-offer prices, acceptances, VLP revenues, arbitrage |
| **💷 Pricing & Settlement** | Imbalance prices (SSP/SBP), market index, settlement data |
| **📡 System Operations** | Grid frequency (50Hz), demand forecasts, system margins |
| **🔌 Grid Infrastructure** | DNO boundaries, DUoS rates, GSP groups, interconnectors |
| **📋 Reference Data** | BMU metadata, company names, capacities, fuel types |
| **📊 Analytics & Derived** | Pre-calculated KPIs, revenue summaries, benchmarks |
| **🗂️ REMIT & Compliance** | Outage notifications, unavailability messages |

### Step 3: Choose Report Type (Row 12)

| Report Type | Description |
|-------------|-------------|
| **Summary Dashboard** | Key metrics overview with sparklines |
| **Trend Analysis (7 days)** | Week-over-week comparison |
| **Trend Analysis (30 days)** | Monthly patterns and trends |
| **Detailed Table** | Full data export with all columns |
| **Time Series Chart** | Line/area charts over time |
| **Distribution Chart** | Histograms and frequency analysis |
| **Comparison Report** | Side-by-side unit/party comparisons |
| **Top 10 Ranking** | Leaderboard by revenue/volume/price |
| **Export to CSV** | Download data for external analysis |

### Step 4: Choose Graph Type (Row 13)

| Graph Type | Best For |
|------------|----------|
| **Line Chart (Time Series)** | Prices, generation over time |
| **Bar Chart (Comparison)** | Unit-to-unit, fuel type comparisons |
| **Stacked Area Chart** | Fuel mix breakdown (100% stacked) |
| **Scatter Plot** | Price vs volume relationships |
| **Heatmap** | Hourly/daily pattern identification |
| **Histogram** | Price/generation distributions |
| **Box Plot** | Outlier detection, quartile analysis |
| **Sparkline Summary** | Inline mini-charts for dashboards |

### Step 5: Generate Report

Click **[Click to Generate]** button in Row 14 or run:
```bash
python3 generate_analysis_report.py
```

Results appear in **Row 18+** with data table and charts.

---

## 📊 Example Report Queries

### Example 1: Battery VLP Revenue (Oct 17-23 Event)

**Settings**:
- Date Range: 2025-10-17 → 2025-10-23
- Generation Type: All (or filter to specific battery)
- Report Category: 💰 Balancing Mechanism (Trading)
- Report Type: Top 10 Ranking
- Graph Type: Bar Chart (Comparison)

**Result**: Top earners during high-price event, FFSEN005/FBPGM002 revenues

### Example 2: Wind Generation Trends

**Settings**:
- Date Range: Last 30 days
- Generation Type: WIND
- Report Category: ⚡ Generation & Fuel Mix
- Report Type: Trend Analysis (30 days)
- Graph Type: Line Chart (Time Series)

**Result**: Daily wind output patterns, forecasting accuracy

### Example 3: Imbalance Price Analysis

**Settings**:
- Date Range: Last 7 days
- Report Category: 💷 Pricing & Settlement
- Report Type: Time Series Chart
- Graph Type: Line Chart (Time Series)

**Result**: SSP/SBP hourly prices, arbitrage opportunities

### Example 4: Grid Frequency Stability

**Settings**:
- Date Range: Today
- Report Category: 📡 System Operations
- Report Type: Detailed Table
- Graph Type: Histogram

**Result**: Frequency distribution around 50Hz, deviation events

### Example 5: DNO Charges Comparison

**Settings**:
- Report Category: 🔌 Grid Infrastructure
- Report Type: Comparison Report
- Graph Type: Bar Chart (Comparison)

**Result**: DUoS rates by DNO/voltage (Red/Amber/Green pricing)

---

## 🔍 Data Sources by Category

### ⚡ Generation & Fuel Mix
**Primary Tables**: `bmrs_fuelinst_iris`, `bmrs_indgen`, `bmrs_windfor`
**Metrics**: MW output, fuel mix %, utilization rates
**Updates**: Every 30 minutes (settlement period)

### 💰 Balancing Mechanism (Trading)
**Primary Tables**: `boalf_with_prices`, `bmrs_bod`, `bmrs_boalf_iris`
**Metrics**: Acceptance prices (£/MWh), volumes (MWh), revenues (£)
**Updates**: Real-time via IRIS, historical every 30 min

### 💷 Pricing & Settlement
**Primary Tables**: `bmrs_costs`, `bmrs_mid`, `bmrs_disbsad`
**Metrics**: SSP/SBP (£/MWh), market index, settlement volumes
**Updates**: Every settlement period (30 min)

### 📡 System Operations
**Primary Tables**: `bmrs_freq_iris`, `bmrs_demandoutturn`, `bmrs_lolp`
**Metrics**: Frequency (Hz), demand (MW), loss of load probability
**Updates**: Frequency every 10 seconds, demand hourly

### 🔌 Grid Infrastructure
**Primary Tables**: `neso_dno_reference`, `gb_power.duos_unit_rates`
**Metrics**: DUoS rates (p/kWh), DNO boundaries, interconnector flows
**Updates**: Static reference (updated annually)

### 📋 Reference Data
**Primary Tables**: `dim_bmu`, `bmu_metadata`, `bmu_registration_data`
**Metrics**: Unit capacities (MW), fuel types, company names
**Updates**: Daily refresh

### 📊 Analytics & Derived
**Primary Tables**: `bm_bmu_kpis`, `vlp_revenue_analysis`
**Metrics**: Pre-calculated averages, totals, rankings
**Updates**: Daily aggregation

### 🗂️ REMIT & Compliance
**Primary Tables**: `bmrs_remit_iris`, `bmrs_unavailability`
**Metrics**: Outage start/end times, MW unavailable, reasons
**Updates**: Real-time event-driven

---

## 💡 Advanced Use Cases

### Battery Arbitrage Strategy
1. **Report Category**: 💷 Pricing & Settlement
2. **Date Range**: Last 30 days
3. **Graph Type**: Heatmap
4. **Analysis**: Identify high-price periods (>£70/MWh) → schedule discharges

### VLP Performance Benchmarking
1. **Report Category**: 💰 Balancing Mechanism (Trading)
2. **BMU ID**: FFSEN005 (or FBPGM002)
3. **Report Type**: Top 10 Ranking
4. **Result**: Compare to market average acceptance prices

### Wind Curtailment Detection
1. **Report Category**: ⚡ Generation & Fuel Mix
2. **Generation Type**: WIND
3. **Report Type**: Comparison Report
4. **Analysis**: Forecast vs actual generation gaps

### Frequency Response Revenue
1. **Report Category**: 📡 System Operations
2. **Graph Type**: Histogram
3. **Analysis**: Frequency deviation events (opportunities for FR payments)

### DNO Cost Optimization
1. **Report Category**: 🔌 Grid Infrastructure
2. **Report Type**: Comparison Report
3. **Result**: Find lowest DUoS zones for battery siting

---

## 🚀 Automation

### Python Script
```bash
# Generate report from command line
cd /home/george/GB-Power-Market-JJ
python3 generate_analysis_report.py
```

### Cron Job (Scheduled Reports)
```bash
# Add to crontab for daily 06:00 generation report
0 6 * * * cd /home/george/GB-Power-Market-JJ && python3 generate_analysis_report.py >> logs/analysis_reports.log 2>&1
```

### Apps Script Button (Coming Soon)
- Click button in B14 to trigger report
- Apps Script calls Python via webhook
- Results auto-populate in sheet

---

## 📈 Output Format

Reports appear in **Row 18+** with:

1. **Header Row**: Column names
2. **Data Rows**: Up to 1,000 rows of results
3. **Summary Stats**: Total rows, date range, category
4. **Charts**: (Manual creation or Apps Script)

### Example Output Structure

```
Row 18:  | date       | settlementPeriod | fuelType | generation_mw |
Row 19:  | 2025-12-22 | 27               | WIND     | 8234.5        |
Row 20:  | 2025-12-22 | 27               | NUCLEAR  | 3489.2        |
Row 21:  | 2025-12-22 | 27               | CCGT     | 14420.8       |
...
```

---

## 🔧 Troubleshooting

### No Data Returned
- **Check date range**: Ensure dates are valid and not future
- **Check filters**: "All" for broadest results
- **Check category**: Some categories have limited historical data

### Timeout Errors
- **Reduce date range**: Query max 30 days at a time
- **Add filters**: Narrow by BMU ID or fuel type
- **Use IRIS tables**: Faster for recent data (last 55 days)

### Wrong Data Appearing
- **Verify category selection**: Each category queries different tables
- **Check historical vs IRIS**: Some data only in IRIS (last 55 days)
- **See data status**: Review `BIGQUERY_DATA_STATUS_DEC22_2025.md`

---

## 📚 Related Documentation

- **Data Categories**: [`BIGQUERY_DATA_CATEGORIES.md`](BIGQUERY_DATA_CATEGORIES.md) - Detailed category descriptions
- **Data Status**: [`BIGQUERY_DATA_STATUS_DEC22_2025.md`](BIGQUERY_DATA_STATUS_DEC22_2025.md) - Current table status
- **Architecture**: [`docs/UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`](docs/UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md) - Pipeline design
- **Configuration**: [`PROJECT_CONFIGURATION.md`](PROJECT_CONFIGURATION.md) - BigQuery setup

---

## 🎯 Quick Reference

| I Want To... | Category | Report Type | Graph Type |
|--------------|----------|-------------|------------|
| Track battery earnings | 💰 Balancing | Top 10 Ranking | Bar Chart |
| Analyze wind patterns | ⚡ Generation | Trend Analysis (30d) | Line Chart |
| Find arbitrage opportunities | 💷 Pricing | Time Series | Line Chart |
| Check grid stability | 📡 System Operations | Detailed Table | Histogram |
| Compare DNO charges | 🔌 Grid Infrastructure | Comparison | Bar Chart |
| Identify top performers | 📊 Analytics | Top 10 Ranking | Bar Chart |
| Review outages | 🗂️ REMIT | Detailed Table | Timeline |
| Lookup unit details | 📋 Reference | Detailed Table | - |

---

*Last Updated: December 22, 2025*
