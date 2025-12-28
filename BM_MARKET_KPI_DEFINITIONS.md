# Balancing Mechanism (BM) Market KPI Definitions

## Overview
The UK Balancing Mechanism (BM) is National Grid ESO's primary tool for balancing electricity supply and demand in real-time. System operators issue Balancing Mechanism Unit (BMU) instructions to generators and demand-side participants to maintain grid stability.

---

## Key Performance Indicators (KPIs)

### 1. **Total BM Cashflow (£)**
**Definition**: The sum of all payments made to (or received from) BMUs for accepted balancing actions during the reporting period.

**Formula**: `Σ (Acceptance Volume × Acceptance Price)` for all accepted bids and offers

**Interpretation**:
- **Positive value**: System paid generators/operators (typical)
- **High values**: Indicate tight margins, high balancing costs, or system stress
- **Correlation**: Often tracks imbalance price movements

**Example**: If Total BM Cashflow = £2.5M for a day, ESO spent £2.5M balancing the system.

---

### 2. **Total BM Volume (MWh)**
**Definition**: The total energy volume (in MegaWatt-hours) of all accepted balancing actions during the reporting period.

**Formula**: `Σ |Acceptance Volume|` for all accepted bids and offers

**Interpretation**:
- **High volume**: Indicates significant balancing activity (forecast errors, unexpected outages, interconnector trips)
- **Low volume**: System running close to plan, minimal intervention needed
- **Typical range**: 500-5000 MWh/day (varies seasonally)

**Example**: If Total BM Volume = 3,200 MWh, ESO instructed BMUs to adjust output by 3.2 GWh total.

---

### 3. **EWAP Offer (£/MWh)**
**Definition**: Energy Weighted Average Price of accepted **offers** (instructions to increase generation or decrease demand).

**Formula**: `Σ (Offer Volume × Offer Price) / Σ Offer Volume`

**Interpretation**:
- **High EWAP Offer**: System short on generation, paying premium to increase output
- **Above imbalance price**: Indicates expensive marginal units called upon
- **Comparison**: Compare with EWAP Bid to assess system direction

**Typical Range**: £50-150/MWh (can spike to £500+/MWh during scarcity events)

**Example**: EWAP Offer = £85/MWh means ESO paid average of £85 per MWh to increase generation.

---

### 4. **EWAP Bid (£/MWh)**
**Definition**: Energy Weighted Average Price of accepted **bids** (instructions to decrease generation or increase demand).

**Formula**: `Σ (Bid Volume × Bid Price) / Σ Bid Volume`

**Interpretation**:
- **High EWAP Bid**: System long on generation, paying to reduce output (renewable curtailment)
- **Negative values**: System receiving payment to reduce output (rare)
- **Wind/Solar Impact**: High renewable output drives up bid activity and prices

**Typical Range**: £30-80/MWh (can be lower during high wind/solar periods)

**Example**: EWAP Bid = £45/MWh means ESO paid average of £45 per MWh to decrease generation.

---

### 5. **Dispatch Intensity (Actions/Hour)**
**Definition**: Average number of balancing mechanism actions (accepted bids/offers) per hour during the reporting period.

**Formula**: `Total Number of Acceptances / Hours in Period`

**Interpretation**:
- **High intensity (>20 actions/hour)**: Active balancing, volatile system conditions
- **Low intensity (<10 actions/hour)**: Stable system, minimal intervention
- **Peak times**: Morning (6-9am) and evening (4-7pm) see highest intensity

**Example**: Dispatch Intensity = 15.3 actions/hour means ESO issued average of 15 balancing instructions per hour.

---

### 6. **Workhorse Index (%)**
**Definition**: Percentage of settlement periods (out of 48 half-hourly periods per day) where at least one balancing action occurred.

**Formula**: `(Settlement Periods with BM Activity / 48) × 100`

**Interpretation**:
- **100%**: Balancing action in every half-hour period (very active day)
- **50%**: Balancing action in 24 out of 48 periods (moderate activity)
- **<30%**: Quiet day, system mostly self-balanced

**Use Case**: Measures how "busy" the BM was throughout the day, independent of volume/cost.

**Example**: Workhorse Index = 85% means 41 out of 48 settlement periods had balancing activity.

---

## Data Sources

- **Primary Table**: `bmrs_boalf_complete` (Balancing Mechanism Acceptance Log with prices)
- **Alternative**: `bmrs_boalf` (raw acceptances, no prices), `bmrs_disbsad` (settlement prices)
- **Price Matching**: BOD (Bid-Offer Data) matched to BOALF acceptances via `pairId` + `settlementPeriod`

---

## Business Context: Battery VLP Analysis

### Why These Metrics Matter for Battery Storage

**VLP (Virtual Lead Party) Revenue Drivers**:
1. **EWAP Offer Spikes**: High offer prices = premium revenue opportunity for discharge
2. **Dispatch Intensity**: High activity = more opportunities for stacking revenues
3. **Workhorse Index**: High index = consistent arbitrage windows throughout day

**Optimal Trading Strategy**:
- **EWAP Offer >£70/MWh**: Aggressive discharge (capture 80%+ of daily revenue in 6-hour windows)
- **EWAP Offer £40-70/MWh**: Moderate discharge (preserve cycles)
- **EWAP Bid >£50/MWh**: Consider charge arbitrage (absorb excess renewable generation)

**Historical Example - Oct 17-23, 2025**:
- **EWAP Offer Avg**: £110/MWh (6-day high-price event)
- **Total BM Cashflow**: £18M+ (week)
- **VLP Revenue Impact**: FFSEN005 earned ~£80k/day (discharge at premium)

---

## Visualization Recommendations

### Dashboard Display Options

**Option 1: Metrics Table** (Current)
```
+-------------------------+----------+
| Metric                  | Value    |
+-------------------------+----------+
| Total BM Cashflow       | £2.5M    |
| Total BM Volume         | 3,200 MWh|
| EWAP Offer              | £85/MWh  |
| EWAP Bid                | £45/MWh  |
| Dispatch Intensity      | 15.3/hr  |
| Workhorse Index         | 85%      |
+-------------------------+----------+
```

**Option 2: Google Sheets Cell Notes**
- Add cell comments with definitions (hover tooltips)
- Use Data Validation > Input message for inline help

**Option 3: Separate "ℹ️ Definitions" Sheet**
- Hyperlink from metric names to definitions sheet
- Include examples and typical ranges

---

## Implementation in Google Sheets

### Adding Tooltips/Notes to Cells

**Apps Script Method**:
```javascript
function addBMKPIDefinitions() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Live Dashboard v2');
  
  const definitions = {
    'A25': 'Total BM Cashflow: Sum of all balancing mechanism payments (£). High values indicate tight margins or system stress.',
    'A26': 'Total BM Volume: Total energy adjusted via balancing actions (MWh). High volume suggests forecast errors or outages.',
    'A27': 'EWAP Offer: Energy-weighted average price paid to increase generation (£/MWh). Spikes indicate system shortages.',
    'A28': 'EWAP Bid: Energy-weighted average price paid to decrease generation (£/MWh). High values during excess renewable output.',
    'A29': 'Dispatch Intensity: Average balancing actions per hour. >20 actions/hr indicates volatile system.',
    'A30': 'Workhorse Index: % of half-hourly periods with balancing activity. 100% = action in every period.'
  };
  
  for (const [cell, note] of Object.entries(definitions)) {
    sheet.getRange(cell).setNote(note);
  }
  
  Logger.log('✅ Added BM KPI definitions to cells');
}
```

**Manual Method**:
1. Right-click metric label cell (e.g., A25)
2. Select "Insert note"
3. Paste definition from above
4. Hover over cell shows tooltip

---

## Related Documentation

- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas and query patterns
- `PROJECT_CONFIGURATION.md` - BigQuery project settings
- `STATISTICAL_ANALYSIS_GUIDE.md` - Advanced analysis techniques
- `analyze_vlp_bm_revenue.py` - VLP revenue analysis script

---

**Last Updated**: December 23, 2024  
**Author**: GB Power Market JJ Project  
**Contact**: george@upowerenergy.uk
