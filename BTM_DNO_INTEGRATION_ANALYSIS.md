# BtM Sheet - DNO/MPAN/DUoS Integration Analysis

**Created**: December 30, 2025
**Purpose**: Analyze how to incorporate existing DNO lookup functionality into BtM sheet for HH profile generation

---

## 🎯 Current State Analysis

### Existing Systems

#### 1. **BESS Sheet DNO Lookup** (Production)
- **Sheet ID**: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
- **Python Script**: `dno_lookup_python.py` (618 lines)
- **Apps Script**: `bess_dno_lookup.gs` (312 lines)
- **Status**: ✅ Fully functional

**Input Cells (BESS sheet)**:
- A6: Postcode (e.g., "LS1 2TW")
- B6: MPAN ID (10-23) or full MPAN core (13 digits)
- A9: Voltage level dropdown ("LV", "HV", "EHV")

**Output Cells (BESS sheet)**:
- C6-H6: DNO details (Key, Name, Short Code, Market ID, GSP Group)
- B9-D9: DUoS rates (Red, Amber, Green in p/kWh)
- B10-D13: Time band schedules

#### 2. **BtM Sheet HH Generator** (Just Created)
- **Sheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- **Python Script**: `generate_hh_data_api.py` (250 lines)
- **Apps Script**: `btm_hh_generator.gs` (249 lines)
- **Status**: ✅ Functional (uses UK Power Networks API)

**Current Parameters (BtM sheet)**:
- B17: Min kW
- B18: Avg kW
- B19: Max kW
- B20: Supply Type (Commercial, Domestic, Industrial, etc.)

**Output**: HH DATA sheet with 17,520 periods

---

## 🔗 Integration Opportunities

### Scenario A: Site-Specific Load Profiles
**Business Case**: Generate HH profiles that reflect actual DNO DUoS pricing
**Value**: Optimize charge/discharge timing based on Red/Amber/Green bands

**Integration Design**:
```
BtM Sheet Layout (Enhanced):

┌─────────────────────────────────────────────────────┐
│ SITE INFORMATION                                    │
├─────────────────────────────────────────────────────┤
│ A6: Postcode     [INPUT]     ← User enters         │
│ B6: MPAN ID      [INPUT]     ← User enters         │
│ C6-H6: DNO Info  [OUTPUT]    ← Auto-populated      │
├─────────────────────────────────────────────────────┤
│ DUOS RATES & TIME BANDS                             │
├─────────────────────────────────────────────────────┤
│ A9: Voltage      [INPUT - Dropdown: LV/HV/EHV]     │
│ B9: Red Rate     [OUTPUT]    ← From BigQuery       │
│ C9: Amber Rate   [OUTPUT]                          │
│ D9: Green Rate   [OUTPUT]                          │
│ B10-D13: Time Schedules [OUTPUT]                   │
├─────────────────────────────────────────────────────┤
│ HH PROFILE GENERATION                               │
├─────────────────────────────────────────────────────┤
│ B17: Min kW      [INPUT]                           │
│ B18: Avg kW      [INPUT]                           │
│ B19: Max kW      [INPUT]                           │
│ B20: Supply Type [INPUT - Dropdown]                │
│                                                      │
│ [🔄 Generate HH Data] ← Button triggers generation │
└─────────────────────────────────────────────────────┘

Enhanced HH DATA Sheet Output:
┌──────────────┬────────┬──────────┬───────────┬──────────┬──────────┐
│ Timestamp    │ SP     │ Day Type │ Demand kW │ Profile% │ DUoS Band│
├──────────────┼────────┼──────────┼───────────┼──────────┼──────────┤
│ 2025-01-01   │ 1      │ Weekday  │ 7,118     │ 71.18%   │ Green    │
│ 00:00        │        │          │           │          │ 0.038p   │
├──────────────┼────────┼──────────┼───────────┼──────────┼──────────┤
│ 2025-01-01   │ 33     │ Weekday  │ 7,820     │ 78.20%   │ Red      │
│ 16:00        │        │          │           │          │ 4.837p   │
└──────────────┴────────┴──────────┴───────────┴──────────┴──────────┘
```

---

## 📊 Implementation Options

### Option 1: Unified Script (Recommended)
**Create**: `btm_complete_generator.py`
**Combines**:
1. DNO lookup (from `dno_lookup_python.py`)
2. DUoS rate retrieval (from `dno_lookup_python.py`)
3. HH profile generation (from `generate_hh_data_api.py`)
4. Time band classification (new logic)

**Workflow**:
```python
def main():
    # Step 1: Read BtM parameters
    postcode = read_cell('A6')
    mpan_id = read_cell('B6')
    voltage = read_cell('A9')
    scale_value = read_cell('B17/B18/B19')  # Whichever has value
    supply_type = read_cell('B20')

    # Step 2: DNO lookup
    if postcode:
        coords = lookup_postcode(postcode)
        mpan_id = coordinates_to_mpan(*coords)
    dno_info = lookup_dno_by_mpan(mpan_id)

    # Step 3: DUoS rate lookup
    duos_rates = get_duos_rates(dno_info['dno_key'], voltage)

    # Step 4: Update DNO section (rows 6-13)
    update_dno_section(dno_info, duos_rates)

    # Step 5: Fetch UK Power Networks profiles
    profiles = fetch_ukpn_profiles(supply_type)

    # Step 6: Generate HH data with DUoS band classification
    hh_data = []
    for record in profiles:
        timestamp = parse_timestamp(record['timestamp'])
        sp = calculate_settlement_period(timestamp)
        duos_band = classify_time_band(timestamp, duos_rates)
        demand_kw = scale_value * (record[supply_type] / 100)
        duos_rate = duos_rates[duos_band]['rate']

        hh_data.append([
            timestamp,
            sp,
            day_type,
            demand_kw,
            record[supply_type],
            duos_band,
            duos_rate
        ])

    # Step 7: Upload to HH DATA sheet
    upload_hh_data(hh_data)
```

**Advantages**:
- ✅ Single button click → Complete analysis
- ✅ Automatic DUoS cost calculation per settlement period
- ✅ Better arbitrage optimization insights
- ✅ Maintains existing functionality

**Disadvantages**:
- ⚠️ More complex (~800 lines combined)
- ⚠️ Requires testing both components together

---

### Option 2: Separate Scripts (Current State)
**Keep**:
- `dno_lookup_python.py` - Run separately for DNO lookup
- `generate_hh_data_api.py` - Run separately for HH generation

**Enhancement**: Add DUoS band classification to HH generator

**Workflow**:
```bash
# Step 1: Populate DNO info
python3 dno_lookup_python.py

# Step 2: Generate HH profiles (now reads DNO info from sheet)
python3 generate_hh_data_api.py
```

**Advantages**:
- ✅ Less code changes
- ✅ Independent testing
- ✅ Modular design

**Disadvantages**:
- ⚠️ Two-step process
- ⚠️ User must remember to run DNO lookup first

---

### Option 3: Apps Script Integration (Browser-Only)
**Enhance**: `btm_hh_generator.gs`
**Add**:
1. DNO lookup function (call BigQuery via proxy)
2. DUoS rate lookup
3. Time band classification

**Advantages**:
- ✅ No Python required
- ✅ Works in browser
- ✅ Single menu click

**Disadvantages**:
- ⚠️ Apps Script timeout limits (6 min max)
- ⚠️ BigQuery API calls slower from Apps Script
- ⚠️ More complex debugging

---

## 🔧 Technical Implementation Details

### Time Band Classification Logic

```python
def classify_time_band(timestamp, duos_rates):
    """
    Classify timestamp into Red/Amber/Green DUoS band

    Args:
        timestamp: datetime object
        duos_rates: dict from get_duos_rates()

    Returns:
        'Red', 'Amber', or 'Green'
    """
    hour = timestamp.hour
    minute = timestamp.minute
    is_weekend = timestamp.weekday() >= 5

    # Weekend is always Green
    if is_weekend:
        return 'Green'

    # Parse time schedules from duos_rates
    for band in ['Red', 'Amber', 'Green']:
        schedules = duos_rates[band]['schedule']
        for schedule_str in schedules:
            if 'Weekend' in schedule_str or 'weekend' in schedule_str:
                continue
            if time_in_range(hour, minute, schedule_str):
                return band

    # Default to Green if not matched
    return 'Green'

def time_in_range(hour, minute, schedule_str):
    """
    Check if time falls within schedule string
    e.g., "16:00-19:30" or "08:00-16:00"
    """
    # Parse "HH:MM-HH:MM" format
    if '-' not in schedule_str:
        return False

    start_str, end_str = schedule_str.split('-')
    start_h, start_m = map(int, start_str.strip().split(':'))
    end_h, end_m = map(int, end_str.strip().split(':'))

    time_minutes = hour * 60 + minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    return start_minutes <= time_minutes < end_minutes
```

### BigQuery Tables Required

```sql
-- 1. DNO Reference Data
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
-- Returns: mpan_distributor_id, dno_key, dno_name, etc.

-- 2. DUoS Unit Rates
SELECT * FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
WHERE dno_key = 'UKPN-EPN' AND voltage_level = 'HV'
-- Returns: red_rate, amber_rate, green_rate (p/kWh)

-- 3. DUoS Time Bands
SELECT * FROM `inner-cinema-476211-u9.gb_power.duos_time_bands`
WHERE dno_key = 'UKPN-EPN'
-- Returns: time_band (Red/Amber/Green), start_time, end_time, weekday_only
```

### Enhanced HH DATA Schema

```python
hh_headers = [
    'Timestamp',           # YYYY-MM-DD HH:MM
    'Settlement Period',   # 1-48
    'Day Type',           # Weekday/Weekend
    'Demand (kW)',        # Scaled demand
    'Profile %',          # Raw UKPN profile %
    'DUoS Band',          # Red/Amber/Green
    'DUoS Rate (p/kWh)',  # Applicable rate
    'DUoS Cost (£)'       # demand_kw × duos_rate × 0.5h ÷ 100
]
```

---

## 💰 Business Value Examples

### Example 1: Commercial Site Optimization
**Inputs**:
- Postcode: LS1 2TW (Leeds)
- MPAN: 23 (Yorkshire - NPg-Y)
- Voltage: HV
- Max kW: 15,000
- Supply Type: Commercial

**DNO Lookup Results**:
- Red: 5.000 p/kWh (16:00-19:30 weekdays)
- Amber: 1.600 p/kWh (08:00-16:00, 19:30-22:00)
- Green: 0.400 p/kWh (00:00-08:00, weekends)

**HH Profile Peak Analysis** (Commercial profile peaks at 78% at 11am):
```
Settlement Period 23 (11:00-11:30):
- Demand: 15,000 × 0.78 = 11,700 kW
- Time Band: Amber (within 08:00-16:00)
- DUoS Cost: 11,700 × 1.600 ÷ 100 × 0.5h = £93.60

Settlement Period 33 (16:00-16:30):
- Demand: 15,000 × 0.72 = 10,800 kW
- Time Band: Red (within 16:00-19:30)
- DUoS Cost: 10,800 × 5.000 ÷ 100 × 0.5h = £270.00

Annual DUoS Charges = Σ(all 17,520 periods) ≈ £350,000-£600,000
```

**Optimization Insight**: Avoid Red periods → Save £120k/year

---

### Example 2: Datacentre Load (Flat Profile)
**Inputs**:
- MPAN: 12 (London - UKPN-LPN)
- Voltage: EHV
- Max kW: 50,000
- Supply Type: Datacentre (constant 84% profile)

**DNO Lookup Results**:
- Red: 3.200 p/kWh
- Amber: 0.800 p/kWh
- Green: 0.150 p/kWh

**HH Profile Analysis** (Constant 42,000 kW demand):
```
Red periods (3.5h/day × 5 days = 17.5h/week):
- Cost: 42,000 × 3.200 ÷ 100 × 17.5 = £23,520/week

Green periods (8h/day × 5 days + 48h weekend = 88h/week):
- Cost: 42,000 × 0.150 ÷ 100 × 88 = £5,544/week

Annual DUoS Charges = £1.51M
```

**Optimization Insight**: Can't avoid Red periods (constant load) → Consider behind-the-meter battery to shave Red peaks

---

## 📋 Recommended Implementation Plan

### Phase 1: Minimal Integration (1 hour)
✅ **Quick Win - Add DUoS Band Column to HH DATA**

1. **Enhance `generate_hh_data_api.py`**:
   - Add `classify_time_band()` function
   - Read DUoS rates from cells B9-D9 (if populated)
   - Add 'DUoS Band' column to HH DATA output
   - Keep existing functionality intact

2. **User Workflow**:
   ```bash
   # Optional: Run DNO lookup first (populates B9-D9)
   python3 dno_lookup_python.py

   # Generate HH data (now includes DUoS bands if available)
   python3 generate_hh_data_api.py
   ```

3. **Result**: HH DATA sheet shows which periods are Red/Amber/Green

---

### Phase 2: Full Integration (4 hours)
✅ **Complete Solution - Unified Script**

1. **Create `btm_complete_generator.py`**:
   - Merge `dno_lookup_python.py` + `generate_hh_data_api.py`
   - Add postcode/MPAN input reading
   - Add automatic DNO lookup
   - Add DUoS rate retrieval
   - Add time band classification
   - Add cost calculation column

2. **Create Apps Script Menu**:
   ```javascript
   function onOpen() {
     SpreadsheetApp.getUi().createMenu('⚡ BtM Tools')
       .addItem('🔄 Generate Complete HH Analysis', 'runCompleteAnalysis')
       .addItem('📊 View HH DATA Sheet', 'viewHHDataSheet')
       .addToUi();
   }

   function runCompleteAnalysis() {
     // Show instructions to run: python3 btm_complete_generator.py
   }
   ```

3. **Result**: One-click complete analysis with DNO-specific costs

---

### Phase 3: Advanced Features (Future)
🔮 **Enhancement Ideas**

1. **Optimization Recommendations**:
   - Calculate optimal charge/discharge schedule
   - Identify highest-cost periods to avoid
   - Suggest battery sizing based on Red band avoidance

2. **Scenario Analysis**:
   - Compare multiple DNO regions
   - Test different supply type profiles
   - Calculate ROI for different strategies

3. **Alerting**:
   - Flag when current profile exceeds Red band threshold
   - Recommend load shifting opportunities

---

## 🎯 Conclusion & Recommendation

**Recommended Approach**: **Phase 1 (Minimal Integration)**

**Rationale**:
1. ✅ **Low Risk**: Minimal changes to working code
2. ✅ **Quick Value**: Immediate DUoS visibility in HH profiles
3. ✅ **Flexible**: Users can run DNO lookup when needed
4. ✅ **Testable**: Easy to validate each component separately
5. ✅ **Maintainable**: Keep modular design

**Next Steps**:
1. Add `classify_time_band()` function to `generate_hh_data_api.py`
2. Update HH DATA output to include 'DUoS Band' column
3. Test with sample postcode/MPAN
4. Document combined workflow in README

**Future Enhancement**: After Phase 1 validation, consider Phase 2 unified script if users request single-button operation.

---

## 📚 Reference Files

### Python Scripts
- `dno_lookup_python.py` - DNO lookup (618 lines)
- `generate_hh_data_api.py` - HH generator (250 lines)
- `btm_dno_lookup.py` - Alternative BtM lookup (541 lines)

### Apps Scripts
- `bess_dno_lookup.gs` - BESS sheet DNO menu (312 lines)
- `btm_hh_generator.gs` - BtM HH generator menu (249 lines)

### Documentation
- `DNO_MPAN_DUOS_LOOKUP_SYSTEM.md` - Complete DNO system reference (1293 lines)
- `BTM_CALCULATE_BUTTON_SETUP.md` - BtM button guide
- `BtM_HH_GENERATOR_GUIDE.md` - HH generator installation

### BigQuery Tables
- `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
- `inner-cinema-476211-u9.gb_power.duos_unit_rates`
- `inner-cinema-476211-u9.gb_power.duos_time_bands`

---

**Status**: ✅ Analysis Complete
**Ready For**: Implementation Phase 1
**Estimated Time**: 1 hour
**Expected Value**: Enhanced load profile visibility with DUoS band classification
