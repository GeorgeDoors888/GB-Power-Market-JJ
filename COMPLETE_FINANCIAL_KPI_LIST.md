# Complete Financial KPI List - Live Dashboard v2

## Overview
All financial and market KPIs tracked in the GB Power Market JJ dashboard.

---

## 📊 PRIMARY FINANCIAL KPIs (Live Dashboard v2)

### Market Dynamics Section (Rows 5-9)

| Cell | KPI | Description | Units | Source Table |
|------|-----|-------------|-------|--------------|
| **A5-B5** | **BM-MID Spread** | Balancing Mechanism vs Market Index spread | £/MWh | bmrs_costs, bmrs_mid |
| **A6** | BM-MID Spread Value | Current spread value | £ | Calculated |
| **C5-D5** | **Market Index Price** | Wholesale day-ahead/within-day price | £/MWh | bmrs_mid |
| **C6** | Market Index Value | Current MID price | £ | bmrs_mid |

### Combined KPI Section (Rows 12-31) - **SYSTEM PRICE + BM MARKET** ✅ WITH SPACED LAYOUT

**Layout**: K12 header + 10 KPI rows in K13:K31 (spaced: 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
**Row Heights**: Header=60px, KPI rows=80px, Spacer rows (14,16,18,20,22,24,26,28,30)=10px
**Cell Merges**:
- K12:S12 = Header "📊 MARKET DYNAMICS - 24 HOUR VIEW" (9 columns wide)
- N13:S13, N15:S15, N17:S17, etc. = Sparklines (6 columns wide each KPI row)

| Row | Col K (KPI Name) | Col L (Value + Units) | Col M (Description) | Col N-S (Sparkline - 6 cols) | Extra Notes |
|-----|------------------|----------------------|---------------------|------------------------------|--------------------|
| **K12** | 📊 Bar MARKET DYNAMICS - 24 HOUR VIEW | | | (MERGED K12:S12) | |
| **K13** | Real-time imbalance price | £65.11/MWh | SSP=SBP | Line chart (N-S merged) | ⚖ Balanced |
| **K14** | 7-Day Average | £74.28/MWh | Rolling mean | Line chart (N-S merged) | |
| **K15** | 30-Day Average | £73.74/MWh | Rolling mean | Line chart (N-S merged) | |
| **K16** | Deviation from 7d | +2.80% | vs 7-day avg | Pos/neg bars (N-S merged) | |
| **K17** | 30-Day High | £203.37/MWh | Max price | Line chart (N-S merged) | |
| **K18** | 30-Day Low | £-17.03/MWh | Min price | Line chart (N-S merged) | |
| **K19** | Total BM Cashflow | £232.3k | Σ(Vol × Price) | Column chart (N-S merged) | |
| **K20** | EWAP Offer | £85.50/MWh | Energy-weighted avg | Column chart (N-S merged) | |
| **K21** | EWAP Bid | £42.30/MWh | Energy-weighted avg | Column chart (N-S merged) | |
| **K22** | Dispatch Intensity | 68.2/hr | Acceptances/hour | Column chart (N-S merged) | 10.4% active |

**KPI Definitions**:
- **Real-time imbalance price**: Current system imbalance settlement price (SSP=SBP since Nov 2015)
- **7-Day Average**: Rolling 7-day mean system price
- **30-Day Average**: Rolling 30-day mean system price
- **Deviation from 7d**: (Current - 7-day avg) / 7-day avg × 100%
- **30-Day High**: Highest price in last 30 days
- **30-Day Low**: Lowest price in last 30 days (can be negative)
- **Total BM Cashflow**: Σ(Volume × Price) | Typical: £50k-£500k/day
- **EWAP Offer**: Σ(Offer £) / Σ(Offer MWh) | Typical: £50-150/MWh
- **EWAP Bid**: Σ(Bid £) / Σ(Bid MWh) | Typical: £30-80/MWh
- **Dispatch Intensity**: Acceptances / Hours | Typical: 5-30 actions/hr

**Source Tables**: `bmrs_costs` (system price), `bmrs_ebocf` (BM cashflow), `bmrs_boav` (BM volumes)

---

## 💰 VLP REVENUE ANALYSIS (Rows 54-67) - **BATTERY ARBITRAGE**

### Top 10 Operator Metrics (28-Day Rolling)

| Column | KPI | Description | Source |
|--------|-----|-------------|--------|
| **M** | Operator Name | VLP unit name (e.g., FFSEN005) | bmrs_boalf |
| **N** | Total MWh | Total energy dispatched | bmrs_boalf |
| **O** | Revenue (£k) | Gross revenue from BM actions | bmrs_boalf_complete |
| **P** | Margin (£/MWh) | Average revenue per MWh | Calculated |
| **Q** | BM Price | Average imbalance price received | bmrs_costs |
| **R** | Wholesale | Average wholesale price | bmrs_mid |

**Row 67 Totals**:
- **N67**: Total MWh (all operators)
- **O67**: Total Revenue (£k)
- **P67**: Average Margin (£/MWh)

**Business Context**:
- High margin (>£500/MWh) = Premium arbitrage windows
- Oct 17-23 event: £79.83/MWh avg = 80% of monthly revenue
- Battery strategy: Deploy at £70+/MWh, preserve cycles <£40/MWh

---

## 📐 DASHBOARD LAYOUT STANDARDS

### Column Structure for Combined KPI Section (K13:K31 spaced)

All KPIs in rows 13, 15, 17, 19, 21, 23, 25, 27, 29, 31 follow this 9-column layout:

| Column | Purpose | Format | Example |
|--------|---------|--------|----------|
| **K** | KPI Name | Plain text | "Real-time imbalance price" |
| **L** | Value + Units | Formatted string | "£65.11/MWh" |
| **M** | Description/Formula | Plain text | "SSP=SBP" or "Σ(Vol × Price)" |
| **N:S** | Sparkline (merged 6 cols) | SPARKLINE formula | =SPARKLINE(Data_Hidden!B2:AW2, {...}) |

**Row Heights**: KPI rows are 80px tall (rows 13,15,17,19,21,23,25,27,29,31), spacer rows are 10px (rows 14,16,18,20,22,24,26,28,30)

### Formatting Examples by KPI Type

**Price Metrics** (K13, K15, K17, K19, K21, K23):
```
K: "Real-time imbalance price"
L: "£65.11/MWh"
M: "SSP=SBP"
N:S: Line chart (red, merged 6 columns, 80px tall)
```

**BM Financial Metrics** (K25, K27, K29, K31):
```
K: "Total BM Cashflow"
L: "£232.3k"
M: "Σ(Vol × Price)"
N:S: Column chart (red, merged 6 columns, 80px tall)
```

**Rate Metrics**:
```
K: "Dispatch Intensity"
L: "68.2/hr"
M: "Acceptances/hour"
N:S: Column chart (orange, merged 6 columns, 80px tall)
```

**Note on Sparklines**: If sparklines show #N/A, this indicates insufficient data periods (BM data can be sparse during low activity periods). Sparklines require at least 3-5 periods with non-zero values to render correctly.

### Section Locations

| Section | Data Range | Rows | Columns |
|---------|-----------|------|----------|
| **Combined KPIs (System Price + BM)** | K12:S31 | 20 (10 data + 9 spacers + header) | K-S (9 cols, N-S merged) |
| **Active Outages** | G25:K41 | 16 | G-K (5 cols) |
| **Interconnectors** | G13:I22 | 10 | G-I (3 cols) |
| **VLP Revenue** | M54:R67 | 13 | M-R (6 cols) |

---

## 📈 MARKET DYNAMICS KPIs (Detailed)

### Spread Analysis (Row 7)

| Cell | KPI | Value | Description |
|------|-----|-------|-------------|
| **A7-B9** | **Spread Sparkline** | Formula | LET formula showing BM-MID spread over 48 periods |
| **M13** | Current BM Price | £56.38/MWh | System imbalance price (SSP=SBP) |
| **M14** | Current Spread | £24.69/MWh | Difference: BM - MID |
| **M15** | Imbalance Price | £65.10/MWh | Settlement price label |
| **M17** | BM Average | £40.62/MWh | Volume-weighted BM average |
| **M18** | MID Price | £40.41/MWh | Wholesale market price |

### Market Component Breakdown (Rows 27-29)

| Cell | Component | Value | Description |
|------|-----------|-------|-------------|
| **A27** | BM_Avg_Price | -£4.98 | Average BM price (negative = system long) |
| **C27** | BM Value | -£32,890 | Total BM cashflow snapshot |
| **A29** | MID_Price | Value | Market Index Data price |
| **B28** | Price/MWh | £-14.54/MWh | Negative pricing event |

---

## 🔋 GENERATION & DEMAND KPIs

### Live Metrics (Row 6 KPIs)

| Cell | KPI | Value | Units | Refresh Rate |
|------|-----|-------|-------|--------------|
| **C6** | Wholesale Price | £40.41 | £/MWh | 5 min |
| **E6** | Grid Frequency | ~50.00 | Hz | 5 min |
| **G6** | Total Generation | ~30 | GW | 5 min |
| **I6** | Wind Output | ~12 | GW | 5 min |
| **K6** | System Demand | ~35 | GW | 5 min |

**Row 7**: Sparklines showing 48 half-hourly periods for each KPI
- **C7**: Wholesale Price sparkline (column chart, orchid #DA70D6)
- **E7**: Grid Frequency sparkline (line chart, gold #FFD700)
- **G7**: Total Generation sparkline (column chart, royal blue #4169E1)
- **I7**: Wind Output sparkline (column chart, dark turquoise #00CED1)
- **K7**: System Demand sparkline (column chart, orange red #FF4500)

---

## 💡 FREQUENCY & PHYSICS

### Grid Stability Metrics

| KPI | Description | Units | Critical Thresholds |
|-----|-------------|-------|---------------------|
| **Frequency** | Grid frequency (50Hz nominal) | Hz | <49.8 or >50.2 = stress |
| **Deviation** | Frequency - 50Hz | Hz | ±0.2 Hz = warning |
| **NIV** | Net Imbalance Volume | MWh | >500 MWh = system imbalance |

**Business Impact**: Low frequency (<49.9 Hz) = high EWAP offers (discharge premium)

---

## 📊 DATA SOURCES & UPDATE FREQUENCY

### BigQuery Tables

| Table | Purpose | Update Frequency | Lag |
|-------|---------|------------------|-----|
| `bmrs_costs` | System prices (SSP/SBP) | 5 min | ~30-60 min |
| `bmrs_mid` | Wholesale prices | 5 min | Real-time |
| `bmrs_ebocf` | BM cashflow | 5 min | ~2-4 hours |
| `bmrs_boav` | BM volumes | 5 min | ~2-4 hours |
| `bmrs_boalf_complete` | Acceptance prices | Daily | ~24 hours |
| `bmrs_indgen_iris` | Unit generation | 5 min | Real-time |
| `bmrs_freq` | Grid frequency | 5 min | Real-time |

### Dashboard Update Scripts

| Script | Purpose | Cron Schedule | Target Sheet |
|--------|---------|---------------|--------------|
| `update_live_metrics.py` | Main dashboard refresh | Every 5 min | Live Dashboard v2 |
| `build_publication_table_current.py` | Wind forecast | Every 15 min | publication_dashboard_live |
| `update_gb_live_complete.py` | Legacy GB Live sheet | Manual/Disabled | GB Live |

---

## 💼 FINANCIAL CALCULATIONS

### Key Formulas

**BM Cashflow**:
```
Total Cashflow = Σ(Offer Cashflow) + Σ(Bid Cashflow)
              = Σ(acceptanceVolume × acceptancePrice)
```

**EWAP (Energy Weighted Average Price)**:
```
EWAP Offer = Σ(Offer Cashflow) / Σ(Offer MWh)
EWAP Bid = Σ(Bid Cashflow) / Σ(Bid MWh)
```

**Dispatch Intensity**:
```
Dispatch Intensity = Total Acceptances / Hours in Period
```

**Workhorse Index**:
```
Workhorse Index = (Settlement Periods with Activity / 48) × 100
```

**BM-MID Spread**:
```
Spread = System Price (bmrs_costs) - Market Index (bmrs_mid)
```

**VLP Revenue**:
```
Revenue = Σ(Acceptance Volume × Acceptance Price)
Margin = Revenue / Total MWh
```

---

## 🎯 BATTERY TRADING SIGNALS

### Revenue Optimization Thresholds

| EWAP Offer Range | Strategy | Expected Margin |
|------------------|----------|-----------------|
| **>£70/MWh** | Aggressive discharge | £50-100/MWh |
| **£40-70/MWh** | Moderate discharge | £20-50/MWh |
| **£25-40/MWh** | Preserve cycles | £0-20/MWh |
| **<£25/MWh** | Charge if EWAP Bid >£50 | -£10-£10/MWh |

### High-Value Events (Historical)

**Oct 17-23, 2025**:
- EWAP Offer: £110/MWh avg
- Total BM Cashflow: £18M+ (week)
- VLP Unit FFSEN005: £80k/day revenue
- Dispatch Intensity: 25+ actions/hour
- Workhorse Index: 100% (all periods active)

**Strategy**: 80%+ of monthly revenue earned in 6-day high-price events

---

## 📋 SCHEMA REFERENCE

### Active Outages Table (G25:K41) - CURRENT LAYOUT

**Section Structure**:
- **G25**: Header row with totals (e.g., "⚠️ ACTIVE OUTAGES - Top 15 by Capacity | Total: 15 units | Offline: 6,524 MW | Normal Capacity: 7,400 MW")
- **G26:K26**: Column headers
- **G27:K41**: Data rows (up to 15 units, sorted by unavailable capacity DESC)

| Column | Header | Data Type | Example | Notes |
|--------|--------|-----------|---------|-------|
| **G** | Asset Name | String | DIDCB6 | Generator/unit name |
| **H** | Fuel Type | String | 🇮🇪 Moyle | Emoji + text label |
| **I** | Unavail (MW) | Integer | 485 | Offline capacity |
| **J** | Normal (MW) | Integer | 485 | Installed capacity |
| **K** | Cause | String | Planned outage | Truncated to 30 chars |

**Fuel Type Display Format**: "Emoji + Text" for readability (e.g., "🇮🇪 Moyle", "🏭 CCGT", "⚛️ Nuclear")

**Interconnector Emojis**:
- 🇫🇷 IFA, IFA2, ElecLink (France)
- 🇮🇪 Moyle, E-W, Greenlink (Ireland)
- 🇳🇱 BritNed (Netherlands)
- 🇧🇪 Nemo (Belgium)

**Generation Emojis**: 🏭 CCGT, 🔥 OCGT, ⚛️ Nuclear, 🌬️ Wind, 🔋 Storage

**Source Table**: `bmrs_remit_unavailability` (REMIT messages)

**Previously Removed**: Columns L-O (Type, Category, Expected Return, Duration, Operator) - streamlined to 5 columns only

---

## 🔧 MAINTENANCE & MONITORING

### Health Checks

1. **Data Freshness**: Check AA1 timestamp (should update every 5 min)
2. **Sparklines**: Row 7 (C7/E7/G7/I7/K7) and rows 13,15,17,19,21,23,25,27,29,31 (N:S) should show dynamic charts
3. **Row Heights**: KPI rows should be 80px tall with 10px spacers between them
4. **BM KPIs**: M27-M33 should have non-zero values during active hours
5. **VLP Revenue**: O67 should be >£100k for 28-day period

### Troubleshooting

**If BM KPIs show zeros**:
- EBOCF/BOAV data lags 2-4 hours
- Check `bmrs_ebocf` table for latest data
- Verify cron job running: `crontab -l | grep update_live_metrics`

**If sparklines missing**:
- Run: Extensions → Apps Script → `updateKPISparklines`
- Check Data_Hidden sheet has data in rows 2-25

**If wind forecast chart empty**:
- Set up Apps Script trigger: `updateDashboard` every 15 min
- Verify `publication_dashboard_live` table has data

---

## 📖 RELATED DOCUMENTATION

- `BM_MARKET_KPI_DEFINITIONS.md` - Detailed KPI explanations
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas
- `PROJECT_CONFIGURATION.md` - BigQuery settings
- `DASHBOARD_FIXES_COMPLETION_REPORT.md` - Recent updates

---

**Last Updated**: December 23, 2024
**Dashboard Version**: Live Dashboard v2 (PYTHON_MANAGED)
**Script Version**: update_live_metrics.py v4.2
**Total KPIs Tracked**: 40+ (7 financial, 15+ market, 10+ VLP, 8+ technical)
