# BESS Sheet Integration Plan
**Preserve Existing + Add Enhanced Revenue Analysis**

## Current BESS Sheet Structure (KEEP AS-IS)

### Section 1: DNO Lookup (Rows 1-14) ✅
**Purpose**: Get distribution network details and DUoS rates  
**Files**: 
- `dno_lookup_python.py` - Python backend
- `bess_auto_trigger.gs` - Apps Script auto-trigger
- `reset_bess_layout.py` - Sheet formatting

**Layout**:
```
Row 1:    "🔋 BESS - Battery Energy Storage System" (title)
Row 4:    Status messages
Row 5-6:  Postcode [A6 INPUT] → DNO details [C6-H6 OUTPUT]
          MPAN ID [B6 INPUT]
Row 9-10: Voltage [A10 INPUT] → Red/Amber/Green rates [B10-D10 OUTPUT]
Row 11-14: Time bands (Red/Amber/Green weekday schedules)
```

### Section 2: HH Profile Generator (Rows 15-20) ✅
**Purpose**: Generate synthetic half-hourly demand profiles  
**Files**:
- `generate_hh_profile.py` - Profile generation
- `bess_hh_generator.gs` - Apps Script trigger

**Layout**:
```
Row 16:    "HH Profile Parameters:" (header)
Row 17-19: Min/Avg/Max kW [B17-B19 INPUT]
Row 20+:   Profile summary (auto-filled)
```

### Section 3: BtM PPA Cost Analysis (Rows 27-50+) ✅
**Purpose**: Calculate behind-the-meter PPA profitability  
**Files**:
- `update_btm_ppa_from_bigquery.py` - Main calculator
- `calculate_bess_element_costs.py` - BESS-specific costs
- `calculate_btm_ppa_with_bess.py` - Combined analysis

**Layout (Two Columns)**:
```
Column A-C: "BtM PPA Direct Flow Excluding BESS"
Column F-I: "BtM PPA Generation PV and BESS"

Both columns show:
- DUoS (Red/Amber/Green) £/MWh
- TNUoS £/MWh
- BSUoS £/MWh
- CCL (Climate Change Levy) £/MWh
- RO (Renewables Obligation) £/MWh
- FiT (Feed-in Tariff) £/MWh
- System Price (Min/Avg/Max) £/MWh
- Import kWh
- PPA Price £/MWh
- PPA kWh
- Profitable Periods
- PPA Revenue
- SO kWh (System Operator)
- SO Revenue
- VLP kWh (Virtual Lead Party)
- VLP Revenue
```

**Key Calculations**:
- **Stream 1** (Direct Import): Import when `system_price + levies + DUoS < PPA_price`
- **Stream 2** (BESS Discharge): Charge in Green (£42/MWh), discharge in Red/Amber (£150 PPA)
- **VLP Revenue**: £12/MWh uplift on 20% of discharge volume
- **DC Revenue**: £195k/year from Dynamic Containment (separate service)

---

## NEW: Enhanced Revenue Analysis (Add to Rows 60+)

### Option A: Extend Existing BESS Tab
Add new sections **below** row 60 in the same BESS sheet:

#### Row 60-80: FR (Frequency Response) Revenue Detail
```
Row 62: "📊 Frequency Response Revenue Breakdown"
Row 65-75: Monthly FR revenues
  - DC (Dynamic Containment) availability £/h
  - DC utilization payments
  - DR (Dynamic Regulation) revenue
  - DM (Dynamic Moderation) revenue
  - Penalties (under-delivery)
  - Net FR revenue per month

Calculation from: bess_profit_model_enhanced.py → compute_fr_revenue()
Data source: v_bess_cashflow_inputs view (fr_avail, fr_util columns)
```

#### Row 82-100: VLP P444 Compensation
```
Row 84: "🔄 VLP P444 Direct Compensation"
Row 87-97: Monthly VLP cashflows
  - DFS events (kWh delivered)
  - DNO flex tenders (kWh)
  - SCRP rate (£/MWh)
  - Supplier compensation (£)
  - VLP compensation received (£)
  - VLP aggregator fee (15%)
  - Net VLP revenue

Calculation from: bess_profit_model_enhanced.py → compute_vlp_revenue()
Data source: v_bess_cashflow_inputs view (vlp_flex, scrp_gbp_mwh columns)
```

#### Row 102-120: BM/BOA Revenue
```
Row 104: "⚡ Balancing Mechanism Revenue"
Row 107-117: Monthly BM revenues
  - Bid acceptances (MW, £/MWh, £ revenue)
  - Offer acceptances (MW, £/MWh, £ revenue)
  - Imbalance exposure (SSP/SBP spread)
  - Net BM revenue

Calculation from: bess_profit_model_enhanced.py → compute_bm_revenue()
Data source: v_bess_cashflow_inputs view (bm_boa columns)
```

### Option B: Create New Tabs
Keep BESS tab as-is, create:

1. **BESS_Revenue** tab:
   - Per-settlement-period cashflow (A2:Q columns)
   - Annual summary KPIs (F3:H9)
   - Revenue waterfall chart

2. **TCR_Model** tab:
   - 2025-2030 scenario forecasts
   - PV+BESS savings analysis

---

## Integration Code Changes

### 1. Update dashboard_pipeline.py
Add call to enhanced model **after** existing BtM PPA update:

```python
def update_all_bess_analyses():
    """Run all BESS calculations in sequence"""
    
    # EXISTING: BtM PPA analysis (rows 27-50)
    from update_btm_ppa_from_bigquery import main as update_btm_ppa
    update_btm_ppa()
    
    # NEW: Enhanced revenue analysis (rows 60+)
    from bess_profit_model_enhanced import compute_bess_profit_detailed, write_bess_to_sheets
    
    # Fetch data from BigQuery view
    df_cashflow = fetch_cashflow_data()  # Uses v_bess_cashflow_inputs
    
    # Compute annual summary
    summary = compute_bess_profit_detailed(df_cashflow)
    
    # Write to BESS sheet starting at row 60
    write_bess_to_sheets(
        df_cashflow, 
        summary, 
        SPREADSHEET_ID, 
        CREDENTIALS_FILE,
        start_row=60  # NEW parameter to avoid overwriting existing content
    )
```

### 2. Modify bess_profit_model_enhanced.py
Add `start_row` parameter to avoid conflicts:

```python
def write_bess_to_sheets(
    df: pd.DataFrame,
    summary: dict,
    spreadsheet_id: str,
    credentials_file: str,
    start_row: int = 60  # NEW: Allow custom starting position
):
    """Write BESS cashflow preserving existing DNO/HH/BtM sections"""
    
    # ... existing code ...
    
    # Write headers at custom row
    bess_sheet.update(headers, f'A{start_row}:Q{start_row}')
    
    # Write timeseries data below
    data_start = start_row + 1
    bess_sheet.update(values, f'A{data_start}:Q{data_start + len(values) - 1}')
    
    # Write KPIs to side panel (doesn't conflict with rows 1-50)
    bess_sheet.update(kpi_values, f'T{start_row}:T{start_row+7}')  # Column T instead of B
```

---

## Migration Steps

### Phase 1: Test Integration (This Week)
```bash
# 1. Backup current sheet
python3 -c "
from gspread_backup import backup_sheet
backup_sheet('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc', 'BESS', 'backup_bess_20251205.json')
"

# 2. Deploy BigQuery view (doesn't affect existing calculations)
bq query --use_legacy_sql=false < bigquery_views/v_bess_cashflow_inputs.sql

# 3. Test enhanced model in isolation (writes to row 60+)
python3 bess_profit_model_enhanced.py --start-row 60 --test-mode

# 4. Verify no conflicts with existing rows 1-50
python3 verify_bess_layout.py
```

### Phase 2: Production Deployment (Next Week)
```bash
# 1. Update dashboard pipeline
python3 dashboard_pipeline.py --update-bess-enhanced

# 2. Schedule automated updates
crontab -e
# Add: */15 * * * * cd /home/george/GB-Power-Market-JJ && python3 dashboard_pipeline.py

# 3. Deploy Apps Script formatting (rows 60+)
# Extensions → Apps Script → Paste apps_script_enhanced/Code.js
# Add formatBESSEnhanced() function for new sections
```

### Phase 3: Documentation Update
```bash
# Create user guide showing both analyses
python3 generate_bess_user_guide.py

# Output: BESS_USER_GUIDE.md with:
# - Section 1: DNO lookup (existing)
# - Section 2: HH profile (existing)
# - Section 3: BtM PPA analysis (existing)
# - Section 4: FR/VLP/BM revenue (NEW)
# - Section 5: TCR forecasting (NEW)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      BESS SHEET                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SECTION 1: DNO LOOKUP (Rows 1-14) ← EXISTING ✅            │
│    ↓                                                          │
│    dno_lookup_python.py → BigQuery (neso_dno_reference)     │
│    postcodes.io API → MPAN extraction                        │
│    → Write to A6-H6, B10-D10                                 │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SECTION 2: HH PROFILE (Rows 15-20) ← EXISTING ✅           │
│    ↓                                                          │
│    generate_hh_profile.py → Synthetic demand curve          │
│    → Write to HH Data sheet                                  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SECTION 3: BTM PPA (Rows 27-50) ← EXISTING ✅              │
│    ↓                                                          │
│    update_btm_ppa_from_bigquery.py                           │
│    ├→ bmrs_costs (system prices)                             │
│    ├→ bmrs_boalf (BM acceptances)                            │
│    ├→ v_curtailment_revenue_daily                            │
│    └→ HH Data sheet (demand profile)                         │
│    → Calculate profitable periods                            │
│    → Write to A27-C50, F27-I50                               │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SECTION 4: ENHANCED REVENUE (Rows 60+) ← NEW 🆕            │
│    ↓                                                          │
│    bess_profit_model_enhanced.py                             │
│    ├→ v_bess_cashflow_inputs (unified view)                  │
│    │  ├→ eso_dc_clearances (FR auctions)                     │
│    │  ├→ eso_dc_performance (FR utilization)                 │
│    │  ├→ bmrs_boalf_iris (BM acceptances)                    │
│    │  ├→ vlp_dfs_events (P444 compensation)                  │
│    │  ├→ wholesale_prices (arbitrage)                        │
│    │  └→ non_energy_levy_rates (BSUoS/RO/FiT)               │
│    └→ Write to A60+, T60+ (separate columns)                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘

AUTOMATION:
  - Apps Script onEdit: A6/B6 changes → trigger DNO lookup
  - Apps Script button: Generate HH Data
  - Cron job (15 min): Run full pipeline (all sections)
  - Manual refresh: Menu → "Update All BESS Analyses"
```

---

## Key Differences: Existing vs Enhanced

| Feature | Existing (Rows 27-50) | Enhanced (Rows 60+) |
|---------|----------------------|---------------------|
| **Focus** | BtM PPA profitability | Full revenue stack |
| **Time Resolution** | Annual aggregates | Per-settlement-period |
| **VLP Revenue** | £12/MWh flat uplift | P444 SCRP compensation |
| **FR Revenue** | £195k DC annual total | DC/DR/DM breakdown by month |
| **BM Revenue** | BOA totals | Bid/Offer split with imbalance |
| **Data Source** | Direct table queries | Unified view (v_bess_cashflow_inputs) |
| **Degradation** | Not included | £10/MWh throughput cost |
| **Capacity Market** | Not included | £30.59/kW/yr with derating |
| **Output** | Two-column comparison | Revenue waterfall + timeseries |

---

## Recommendation: **Option A - Extend Existing Tab**

**Why?**
- ✅ Keeps all BESS analysis in one place
- ✅ No need to switch tabs
- ✅ DNO rates (B10-D10) flow into both analyses automatically
- ✅ HH profile can be used by both sections
- ✅ Easier to compare BtM PPA vs full revenue stack

**Implementation**:
1. Rows 1-50: Keep existing (DNO, HH, BtM PPA)
2. Row 55: Divider "─── Enhanced Revenue Analysis ───"
3. Rows 60-140: New FR/VLP/BM/arbitrage/TCR sections
4. Apps Script: formatBESS() handles rows 1-50, formatBESSEnhanced() handles 60+

---

## Next Steps

1. **Review this plan** - Confirm integration approach
2. **Test in sandbox** - Clone sheet, deploy to test environment
3. **Validate calculations** - Compare existing vs enhanced for overlapping metrics (VLP, DC revenue)
4. **Deploy incrementally** - Add Section 4 first, then expand
5. **Document for users** - Create video walkthrough showing both analyses

**Questions to resolve:**
- Where should TCR forecasting go? (Separate tab or BESS rows 150+?)
- Keep BtM PPA as primary dashboard metric or switch to full revenue stack?
- Integrate CHP analysis into existing structure or separate section?

---

**Last Updated**: 2025-12-05  
**Status**: Ready for implementation  
**Contact**: george@upowerenergy.uk
