# 📖 API Reference

Complete Python function documentation for the BESS Dashboard system.

---

## 📋 Table of Contents

- [Core Scripts](#core-scripts)
  - [calculate_ppa_arbitrage.py](#calculate_ppa_arbitragepy)
  - [calculate_bess_revenue.py](#calculate_bess_revenuepy)
  - [visualize_ppa_costs.py](#visualize_ppa_costspy)
  - [update_bess_dashboard.py](#update_bess_dashboardpy)
- [Utility Functions](#utility-functions)
- [Configuration](#configuration)
- [Data Models](#data-models)

---

## 🎯 Core Scripts

### calculate_ppa_arbitrage.py

**Purpose:** Analyze 24-month PPA arbitrage opportunities comparing SSP vs PPA pricing

**Runtime:** ~60 seconds

**Output:** Rows 90-162 (73 rows: 24 months × 3 time bands + 1 header)

#### Functions

##### `connect()`

Establish connections to Google Cloud services.

**Returns:**
- `tuple`: `(bq_client, gc_client, worksheet)`
  - `bq_client` (bigquery.Client): BigQuery client
  - `gc_client` (gspread.Client): Google Sheets client  
  - `worksheet` (gspread.Worksheet): BESS worksheet

**Raises:**
- `FileNotFoundError`: If credentials.json missing
- `google.auth.exceptions.DefaultCredentialsError`: Invalid credentials

**Example:**
```python
bq, gc, sheet = connect()
print(f"Connected to: {sheet.title}")
```

**Environment:**
- Requires: `GOOGLE_APPLICATION_CREDENTIALS` or `credentials.json` in project root
- Project: `inner-cinema-476211-u9`
- Dashboard: `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`

---

##### `get_system_prices(bq_client, months_back=24)`

Fetch historical System Sell Prices from BigQuery.

**Parameters:**
- `bq_client` (bigquery.Client): Authenticated BigQuery client
- `months_back` (int, optional): Number of months to retrieve. Default: 24

**Returns:**
- `pd.DataFrame`: Columns:
  - `settlement_date` (datetime): Date of settlement
  - `settlement_period` (int): Period number (1-48)
  - `ssp` (float): System Sell Price (£/MWh)

**Query:**
```sql
SELECT 
  settlement_date,
  settlement_period,
  system_sell_price as ssp
FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_prices`
WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {months_back} MONTH)
ORDER BY settlement_date, settlement_period
```

**Example:**
```python
df = get_system_prices(bq_client, months_back=12)
print(f"Retrieved {len(df):,} settlement periods")
# Output: Retrieved 17,520 settlement periods

# Data structure
print(df.head())
#   settlement_date  settlement_period    ssp
# 0      2024-01-01                  1  45.23
# 1      2024-01-01                  2  43.87
```

**Sample Data Fallback:**
If BigQuery unavailable, generates synthetic data:
- Date range: Last 24 months
- SSP range: £40-120/MWh
- Realistic variation: ±15% around £75/MWh average

---

##### `get_time_band_for_sp(settlement_period)`

Determine time band (RED/AMBER/GREEN) for a settlement period.

**Parameters:**
- `settlement_period` (int): Period number (1-48)

**Returns:**
- `str`: `'RED'`, `'AMBER'`, or `'GREEN'`

**Time Band Definitions:**
```python
RED_PERIODS = [33, 34, 35, 36, 37, 38]  # 16:00-19:00 (3 hours)
AMBER_PERIODS = [13, 14, 15, 16, 29, 30, 31, 32]  # 06:00-08:00, 14:00-16:00 (4 hours)
# GREEN: All other periods (17 hours)
```

**Example:**
```python
# Morning off-peak
band = get_time_band_for_sp(1)  # 00:00-00:30
print(band)  # 'GREEN'

# Morning peak
band = get_time_band_for_sp(15)  # 07:00-07:30
print(band)  # 'AMBER'

# Evening peak
band = get_time_band_for_sp(35)  # 17:00-17:30
print(band)  # 'RED'
```

**Time Band Map:**
| Period | Time | Band |
|--------|------|------|
| 1-12 | 00:00-06:00 | GREEN |
| 13-16 | 06:00-08:00 | AMBER |
| 17-28 | 08:00-14:00 | GREEN |
| 29-32 | 14:00-16:00 | AMBER |
| 33-38 | 16:00-19:00 | RED |
| 39-48 | 19:00-00:00 | GREEN |

---

##### `calculate_total_cost(ssp_mwh, duos_rates, time_band)`

Calculate total cost per MWh including all levies and charges.

**Parameters:**
- `ssp_mwh` (float): System Sell Price (£/MWh)
- `duos_rates` (dict): DUoS rates by time band
  ```python
  {'RED': 8.50, 'AMBER': 2.10, 'GREEN': 0.45}  # p/kWh
  ```
- `time_band` (str): `'RED'`, `'AMBER'`, or `'GREEN'`

**Returns:**
- `float`: Total cost (£/MWh)

**Cost Components:**
```python
# Fixed levies (£/MWh)
BSUoS = 3.40          # Balancing Services Use of System
ENERGY_LEVIES = 10.25  # RO + FiT + CfD
TNUoS = 15.50         # Transmission Network Use of System
FCP = 9.00            # Feed-in Tariff

# Variable charges
DUoS = duos_rates[time_band] * 10  # Convert p/kWh to £/MWh

# Total
total = ssp_mwh + BSUoS + ENERGY_LEVIES + TNUoS + FCP + DUoS
```

**Example:**
```python
duos = {'RED': 8.50, 'AMBER': 2.10, 'GREEN': 0.45}

# RED period (expensive)
cost_red = calculate_total_cost(75.00, duos, 'RED')
print(f"RED: £{cost_red:.2f}/MWh")
# Output: RED: £198.15/MWh
# Breakdown: 75.00 + 3.40 + 10.25 + 15.50 + 9.00 + 85.00 = 198.15

# GREEN period (cheap)
cost_green = calculate_total_cost(75.00, duos, 'GREEN')
print(f"GREEN: £{cost_green:.2f}/MWh")
# Output: GREEN: £117.65/MWh
# Breakdown: 75.00 + 3.40 + 10.25 + 15.50 + 9.00 + 4.50 = 117.65

# Savings: £80.50/MWh (41% cheaper)
```

**DUoS Rate Reference (NGED-WM LV 2024/25):**
- RED: 8.50 p/kWh (£85.00/MWh)
- AMBER: 2.10 p/kWh (£21.00/MWh)
- GREEN: 0.45 p/kWh (£4.50/MWh)

---

##### `main()`

Main execution function orchestrating PPA arbitrage analysis.

**Process:**
1. Connect to Google Cloud services
2. Fetch 24 months of System Sell Prices
3. Read DUoS rates and PPA price from sheet
4. Calculate costs for each settlement period
5. Aggregate by month and time band
6. Calculate PPA comparison and profitability
7. Write results to rows 90-162
8. Update summary statistics

**Output Structure (Rows 90-162):**
```
Row 90: Headers
  Month | Time Band | Avg SSP | Total Cost | PPA Price | Diff | Profit %

Rows 91-162: Data (24 months × 3 bands = 72 rows)
  2024-01 | RED    | 85.23 | 198.15 | 150.00 | -48.15 | 24.3%
  2024-01 | AMBER  | 73.45 | 135.60 | 150.00 | +14.40 | -10.6%
  2024-01 | GREEN  | 62.10 | 120.25 | 150.00 | +29.75 | -24.7%
  ...
```

**Performance:**
- BigQuery query: ~5 seconds
- Pandas processing: ~12 seconds (17,520 rows)
- Aggregation: ~2 seconds
- Sheets write: ~4 seconds
- **Total: ~60 seconds**

**Example:**
```python
if __name__ == '__main__':
    main()
```

**Logging:**
- File: `logs/ppa_arbitrage_YYYYMMDD.log`
- Level: INFO
- Retention: 7 days

---

### calculate_bess_revenue.py

**Purpose:** Calculate 90-day revenue breakdown across 5 streams

**Runtime:** ~45 seconds

**Output:** Rows 170-205 (36 rows: revenue streams + summary)

#### Functions

##### `calculate_arbitrage_revenue(prices_df, battery_params, duos_rates)`

Calculate revenue from energy arbitrage (buy low, sell high).

**Parameters:**
- `prices_df` (pd.DataFrame): System prices with columns:
  - `settlement_date`, `settlement_period`, `ssp`, `time_band`
- `battery_params` (dict): Battery configuration
  ```python
  {
    'capacity_mwh': 2.5,
    'power_mw': 1.0,
    'efficiency': 0.85,
    'cycles_per_day': 2
  }
  ```
- `duos_rates` (dict): DUoS rates by time band

**Returns:**
- `dict`: Revenue breakdown
  ```python
  {
    'total_revenue': 125430.00,
    'daily_avg': 1393.67,
    'cycles_executed': 180,
    'energy_traded_mwh': 450.0,
    'avg_margin': 35.5
  }
  ```

**Algorithm:**
1. Identify cheapest periods (buy opportunities)
2. Identify expensive periods (sell opportunities)
3. Apply battery constraints:
   - Max charge/discharge: 1 MW
   - Capacity: 2.5 MWh
   - Round-trip efficiency: 85%
   - Cycles per day: 2
4. Calculate revenue per cycle
5. Aggregate over 90 days

**Example:**
```python
battery = {
    'capacity_mwh': 2.5,
    'power_mw': 1.0,
    'efficiency': 0.85,
    'cycles_per_day': 2
}

duos = {'RED': 8.50, 'AMBER': 2.10, 'GREEN': 0.45}

revenue = calculate_arbitrage_revenue(prices_df, battery, duos)

print(f"Total Revenue: £{revenue['total_revenue']:,.2f}")
# Output: Total Revenue: £125,430.00

print(f"Daily Average: £{revenue['daily_avg']:,.2f}")
# Output: Daily Average: £1,393.67

print(f"Cycles: {revenue['cycles_executed']}")
# Output: Cycles: 180 (2/day × 90 days)
```

**Typical Cycle:**
```
Buy at 02:00 (GREEN): £50/MWh × 2.5 MWh = £125
  + DUoS GREEN: £4.50/MWh × 2.5 = £11.25
  + Fixed levies: £38.15/MWh × 2.5 = £95.38
  Total Cost: £231.63

Sell at 17:00 (RED): £120/MWh × 2.125 MWh = £255.00  (85% efficiency)
  - Total Cost: £231.63
  Gross Profit: £23.37

Cycles per day: 2
Daily profit: £46.74
90-day total: £4,206.60
```

---

##### `calculate_so_payments(battery_params, days=30)`

Calculate System Operator payments for frequency response services.

**Parameters:**
- `battery_params` (dict): Battery configuration
- `days` (int): Analysis period. Default: 30

**Returns:**
- `dict`: SO payment breakdown
  ```python
  {
    'total': 72500.00,
    'ffr': 45000.00,  # Firm Frequency Response
    'dcr': 12000.00,  # Demand Control Response
    'dm': 8500.00,    # Dynamic Moderation
    'dr': 4500.00,    # Dynamic Regulation
    'bid': 1500.00,   # Balance Mechanism bids
    'bod': 1000.00    # Balance Mechanism offers
  }
  ```

**Service Rates (2024/25):**
```python
FFR_RATE = 50.00  # £/MW/day (primary)
DCR_RATE = 13.33  # £/MW/day (secondary)
DM_RATE = 9.44    # £/MW/day (dynamic mod)
DR_RATE = 5.00    # £/MW/day (dynamic reg)
BID_RATE = 1.67   # £/MW/day (BM bids)
BOD_RATE = 1.11   # £/MW/day (BM offers)
```

**Example:**
```python
battery = {'power_mw': 1.0}
payments = calculate_so_payments(battery, days=90)

print(f"Total SO Payments: £{payments['total']:,.2f}")
# Output: Total SO Payments: £72,500.00

print(f"FFR (Primary): £{payments['ffr']:,.2f}")
# Output: FFR (Primary): £45,000.00
# Calculation: £50/MW/day × 1 MW × 90 days

print(f"DCR (Secondary): £{payments['dcr']:,.2f}")
# Output: DCR (Secondary): £12,000.00
# Calculation: £13.33/MW/day × 1 MW × 90 days
```

**Service Availability:**
- FFR: 24/7 availability required
- DCR: 16 hours/day (06:00-22:00)
- DM: 12 hours/day (peak periods)
- DR: 8 hours/day (super peak)
- BID/BOD: As dispatched

---

##### `calculate_capacity_market(battery_params)`

Calculate Capacity Market payments (annual contract).

**Parameters:**
- `battery_params` (dict): Battery configuration

**Returns:**
- `float`: Annual CM payment (£)

**Rate (2024/25 T-4 Auction):**
```python
CM_RATE = 28.00  # £/kW/year
```

**Example:**
```python
battery = {'power_mw': 1.0}  # 1,000 kW

cm_annual = calculate_capacity_market(battery)
print(f"CM Annual: £{cm_annual:,.2f}")
# Output: CM Annual: £28,000.00

cm_daily = cm_annual / 365
print(f"CM Daily: £{cm_daily:.2f}")
# Output: CM Daily: £76.71

cm_90d = cm_daily * 90
print(f"CM (90 days): £{cm_90d:,.2f}")
# Output: CM (90 days): £6,904.11
```

**Contract Terms:**
- Duration: 1 year (Oct 2024 - Sep 2025)
- Availability: ≥85% (de-rating applies)
- Penalties: £0.10/kW per hour unavailable
- Testing: Stress events (4 hours notice)

---

##### `calculate_ppa_revenue(battery_params, ppa_price, days=30)`

Calculate revenue from Power Purchase Agreement.

**Parameters:**
- `battery_params` (dict): Battery configuration
- `ppa_price` (float): Fixed PPA rate (£/MWh)
- `days` (int): Analysis period. Default: 30

**Returns:**
- `dict`: PPA revenue breakdown
  ```python
  {
    'total': 76950.00,
    'daily_avg': 855.00,
    'energy_sold_mwh': 513.0,
    'rate': 150.00
  }
  ```

**Calculation:**
```python
# Discharge cycles per day
cycles = battery_params['cycles_per_day']  # 2

# Energy per cycle (with efficiency loss)
energy_per_cycle = battery_params['capacity_mwh'] * battery_params['efficiency']
# 2.5 MWh × 0.85 = 2.125 MWh

# Daily energy
daily_energy = cycles * energy_per_cycle
# 2 × 2.125 = 4.25 MWh/day

# Revenue
daily_revenue = daily_energy * ppa_price
# 4.25 MWh × £150/MWh = £637.50/day

total_revenue = daily_revenue * days
```

**Example:**
```python
battery = {
    'capacity_mwh': 2.5,
    'cycles_per_day': 2,
    'efficiency': 0.85
}

ppa_revenue = calculate_ppa_revenue(battery, ppa_price=150.00, days=90)

print(f"PPA Total: £{ppa_revenue['total']:,.2f}")
# Output: PPA Total: £57,375.00

print(f"Energy Sold: {ppa_revenue['energy_sold_mwh']:.1f} MWh")
# Output: Energy Sold: 382.5 MWh

print(f"Rate: £{ppa_revenue['rate']:.2f}/MWh")
# Output: Rate: £150.00/MWh
```

**PPA Types:**
- Fixed: Constant £/MWh (e.g., £150)
- Index-linked: Baseload + premium (e.g., Baseload + £10)
- Shared savings: % of arbitrage profits

---

##### `main()`

Main execution function for revenue calculation.

**Process:**
1. Connect to services
2. Fetch 90 days System Sell Prices
3. Read battery parameters and DUoS rates
4. Calculate 5 revenue streams:
   - Arbitrage
   - SO Payments (6 services)
   - Capacity Market
   - PPA Revenue
   - Other (ancillary services)
5. Calculate costs (energy, DUoS, levies)
6. Compute profit (Revenue - Costs)
7. Write results to rows 170-205

**Output Structure:**
```
Row 170: Summary
  Total Revenue: £343,828
  Total Costs: £259,049
  Net Profit: £84,779
  Profit Margin: 24.7%

Rows 171-175: Revenue Breakdown
  PPA Revenue: £123,750 (36%)
  SO Payments: £116,550 (34%)
  Arbitrage: £95,400 (28%)
  Capacity Market: £6,904 (2%)
  Other: £1,224 (0%)

Rows 180-185: Cost Breakdown
  Energy (SSP): £143,550 (55%)
  DUoS Charges: £68,500 (26%)
  BSUoS: £17,200 (7%)
  TNUoS: £19,650 (8%)
  Levies: £10,149 (4%)

Rows 190-195: Performance Metrics
  Cycles Executed: 180
  Energy Traded: 765 MWh
  Avg Buy Price: £62.30/MWh
  Avg Sell Price: £118.75/MWh
  Round-trip Efficiency: 85%
```

**Runtime:** ~45 seconds

---

### visualize_ppa_costs.py

**Purpose:** Generate cost analysis charts and statistics

**Runtime:** ~30 seconds

**Output:** 
- `ppa_cost_analysis.png` (664 KB)
- `ppa_cost_summary.png` (477 KB)
- Rows 210-245 (statistics)

#### Functions

##### `get_system_prices(bq_client, days=30)`

Fetch recent System Sell Prices for visualization.

**Parameters:**
- `bq_client` (bigquery.Client): Authenticated client
- `days` (int, optional): Number of days to retrieve. Default: 30

**Returns:**
- `pd.DataFrame`: Columns:
  - `settlement_date`, `settlement_period`, `ssp`, `time_band`

**Data Volume:**
- 30 days × 48 periods = 1,440 rows
- ~115 KB

**Example:**
```python
df = get_system_prices(bq_client, days=30)
print(f"Data points: {len(df):,}")
# Output: Data points: 1,440

print(df.describe())
#             ssp
# count  1440.00
# mean     75.23
# std      28.45
# min      35.10
# 25%      52.80
# 50%      71.50
# 75%      92.30
# max     148.90
```

---

##### `calculate_cost_components(ssp_mwh, duos_rates, time_band)`

Break down total cost into components for visualization.

**Parameters:**
- `ssp_mwh` (float): System Sell Price
- `duos_rates` (dict): DUoS rates
- `time_band` (str): Time band

**Returns:**
- `dict`: Cost components
  ```python
  {
    'ssp': 75.00,
    'bsuos': 3.40,
    'tnuos': 15.50,
    'duos': 85.00,  # RED band
    'levies': 19.25,
    'total': 198.15
  }
  ```

**Example:**
```python
duos = {'RED': 8.50, 'AMBER': 2.10, 'GREEN': 0.45}
components = calculate_cost_components(75.00, duos, 'RED')

for key, value in components.items():
    print(f"{key.upper()}: £{value:.2f}/MWh")

# Output:
# SSP: £75.00/MWh
# BSUOS: £3.40/MWh
# TNUOS: £15.50/MWh
# DUOS: £85.00/MWh
# LEVIES: £19.25/MWh
# TOTAL: £198.15/MWh
```

---

##### `create_stacked_bar_chart(df, output_file='ppa_cost_analysis.png')`

Generate main cost analysis chart (stacked bar).

**Parameters:**
- `df` (pd.DataFrame): Price data with cost components
- `output_file` (str, optional): Output filename

**Chart Specifications:**
- **Type:** Stacked bar chart
- **Size:** 16" × 10" (1600 × 1000 px)
- **DPI:** 100
- **X-axis:** Settlement periods (1-48)
- **Y-axis:** Cost (£/MWh)
- **Stacks:** 5 components (SSP, BSUoS, TNUoS, DUoS, Levies)
- **Colors:** Colorblind-friendly palette
  - SSP: #1f77b4 (blue)
  - BSUoS: #ff7f0e (orange)
  - TNUoS: #2ca02c (green)
  - DUoS: #d62728 (red)
  - Levies: #9467bd (purple)

**Features:**
- Time band shading (RED: red, AMBER: yellow, GREEN: green)
- PPA price line (dashed black)
- Average cost line (solid black)
- Legend with totals
- Grid lines

**Example:**
```python
create_stacked_bar_chart(df, output_file='costs.png')
# Creates: costs.png (664 KB)
```

**Output:**
```
📊 Stacked Bar Chart
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
200 ┤                              ████████
    │                         ████████████
150 ┤                    ████████████████
    │               ████████████████████
100 ┤          ████████████████████████
    │     ████████████████████████████
 50 ┤████████████████████████████████
    │
  0 └─────────────────────────────────────
    0   6   12  18  24  30  36  42  48
         Settlement Period (HH)

Legend:
  ████ SSP (£75.23 avg)
  ████ BSUoS (£3.40)
  ████ TNUoS (£15.50)
  ████ DUoS (varies by band)
  ████ Levies (£19.25)
  ---- PPA Price (£150.00)
```

---

##### `create_summary_charts(df, output_file='ppa_cost_summary.png')`

Generate 2×2 summary charts.

**Parameters:**
- `df` (pd.DataFrame): Price data
- `output_file` (str, optional): Output filename

**Chart Specifications:**
- **Layout:** 2×2 grid (4 subplots)
- **Size:** 12" × 10" (1200 × 1000 px)
- **DPI:** 100

**Subplots:**

1. **Top-Left: Cost by Time Band**
   - Type: Bar chart
   - Shows: Avg cost for RED, AMBER, GREEN
   - Colors: Band colors
   - Values: £198.15, £135.60, £120.25

2. **Top-Right: Cost Components**
   - Type: Pie chart
   - Shows: Proportion of each cost
   - Labels: SSP 38%, DUoS 43%, Other 19%

3. **Bottom-Left: Daily Profile**
   - Type: Line chart
   - Shows: Avg cost by hour (0-23)
   - Highlights: Peak hours

4. **Bottom-Right: Cost Distribution**
   - Type: Histogram
   - Shows: Frequency of cost ranges
   - Bins: 20
   - Range: £50-200/MWh

**Example:**
```python
create_summary_charts(df, output_file='summary.png')
# Creates: summary.png (477 KB)
```

---

##### `main()`

Main execution for visualization.

**Process:**
1. Connect to services
2. Fetch 30 days price data
3. Calculate cost components
4. Generate main stacked bar chart
5. Generate 2×2 summary charts
6. Calculate statistics
7. Write stats to rows 210-245

**Output Statistics (Rows 210-245):**
```
Row 210: Chart Files
  Main: ppa_cost_analysis.png (664 KB)
  Summary: ppa_cost_summary.png (477 KB)

Rows 215-220: Cost Statistics
  Avg Total Cost: £145.67/MWh
  Min Cost: £98.30/MWh (GREEN, 03:00)
  Max Cost: £215.40/MWh (RED, 17:30)
  Std Dev: £32.18/MWh

Rows 225-230: Time Band Averages
  RED Avg: £198.15/MWh (16:00-19:00)
  AMBER Avg: £135.60/MWh (06:00-08:00, 14:00-16:00)
  GREEN Avg: £120.25/MWh (Other)

Rows 235-240: PPA Comparison
  PPA Price: £150.00/MWh
  Times Cheaper: 892/1440 (62%)
  Times More Expensive: 548/1440 (38%)
  Avg Savings: £17.53/MWh (when cheaper)
```

**Runtime:** ~30 seconds

---

### update_bess_dashboard.py

**Purpose:** Create/update dashboard UI elements (dropdowns, tables)

**Runtime:** ~20 seconds

**Output:**
- Cell L6: Time period dropdown
- Rows 250-285: Cost breakdown table

#### Functions

##### `create_time_period_dropdown(bess)`

Create data validation dropdown for time period selection.

**Parameters:**
- `bess` (gspread.Worksheet): BESS worksheet

**Dropdown Options:**
```python
[
  '30 Days',
  '90 Days',
  '6 Months',
  '1 Year',
  '2 Years (Full Analysis)'
]
```

**Cell:** L6

**Example:**
```python
create_time_period_dropdown(bess)
# Creates dropdown in L6
# Default: '90 Days'
```

**Implementation:**
```python
from gspread_formatting import DataValidationRule

rule = DataValidationRule(
    condition_type='ONE_OF_LIST',
    condition_values=['30 Days', '90 Days', ...],
    strict=True,
    show_custom_ui=True
)

set_data_validation_for_cell_range(bess, 'L6', rule)
```

---

##### `create_cost_breakdown_table(bess)`

Create comprehensive cost breakdown table with formulas.

**Parameters:**
- `bess` (gspread.Worksheet): BESS worksheet

**Table Structure (Rows 250-285):**

```
Row 250: Table Header
  A250: "Cost Component"
  B250: "£/MWh"
  C250: "% of Total"
  D250: "Annual (£)"
  E250: "Source"
  F250: "Notes"

Rows 252-258: Fixed Levies
  SSP (Variable) | =B6 | % | Annual | BigQuery | Market price
  BSUoS | 3.40 | 3% | 14,400 | Elexon | Fixed 24/25
  TNUoS | 15.50 | 14% | 65,700 | NESO | Fixed 24/25
  Energy Levies | 10.25 | 9% | 43,450 | Ofgem | RO+FiT+CfD
  FCP | 9.00 | 8% | 38,150 | Ofgem | Feed-in Premium

Rows 260-262: Variable DUoS
  DUoS RED | =B10 | % | Annual | BigQuery | DNO rates
  DUoS AMBER | =C10 | % | Annual | BigQuery | DNO rates  
  DUoS GREEN | =D10 | % | Annual | BigQuery | DNO rates

Rows 264-268: Summary
  Sub-total (Fixed) | 38.15 | 35% | 161,700 | Calculated | Sum
  Sub-total (Variable) | Varies | 65% | Varies | Calculated | SSP+DUoS
  Total (RED) | =SUM | 100% | Annual | Calculated | Worst case
  Total (GREEN) | =SUM | 100% | Annual | Calculated | Best case
  Difference | =DIFF | % | Annual | Calculated | Savings

Rows 270-275: Optimization Opportunities
  1. Shift to GREEN: Save £80.50/MWh (41%)
  2. Reduce RED exposure: Target <20% cycles
  3. Optimize charge timing: 02:00-04:00 cheapest
  4. Battery capacity: 2.5 MWh optimal
  5. Efficiency gains: 85%→90% = +5.9% profit

Rows 280-285: References
  Data Sources:
  - Elexon BMRS: System prices
  - NESO DNO Reference: Network codes
  - Ofgem: Levies and tariffs
  - DUoS Data: DNO-specific rates
  
  Update Frequency:
  - SSP: Real-time (5min delay)
  - DUoS: Annual (April)
  - Levies: Annual (April)
  - TNUoS: Annual (April)
```

**Formulas:**
```python
# Percentage of total
=B252/B268*100

# Annual cost
=B252*4242  # 4,242 MWh annual consumption (2.5 MW × 1,697 hours)

# RED total
=SUM(B252:B256)+B260  # Fixed + RED DUoS

# GREEN total  
=SUM(B252:B256)+B262  # Fixed + GREEN DUoS

# Savings
=B266-B267  # RED - GREEN
```

**Formatting:**
- Header row: Bold, background #1f77b4 (blue), white text
- Fixed levies: Background #f0f0f0 (light gray)
- DUoS rows: Background based on band (red/yellow/green tint)
- Summary rows: Bold, border-top
- Currency: £#,##0.00
- Percentage: 0.0%

**Example:**
```python
create_cost_breakdown_table(bess)
# Creates table in A250:F285
# Updates automatically when B6, B10:D10 change
```

---

##### `create_period_definitions(bess)`

Add period definitions and time band details.

**Parameters:**
- `bess` (gspread.Worksheet): BESS worksheet

**Location:** Rows 288-320

**Content:**
```
Row 288: Period Definitions Header

Rows 290-295: Time Bands
  RED (Super Peak): 16:00-19:00 (3 hours)
    Periods: 33-38
    Characteristics: Highest demand, highest prices
    Strategy: Discharge (sell)
  
  AMBER (Peak): 06:00-08:00, 14:00-16:00 (4 hours)
    Periods: 13-16, 29-32
    Characteristics: Morning & afternoon peaks
    Strategy: Variable (depends on price)
  
  GREEN (Off-Peak): All other times (17 hours)
    Periods: 1-12, 17-28, 39-48
    Characteristics: Low demand, low prices
    Strategy: Charge (buy)

Rows 300-310: Settlement Period Map
  Period | Time | Band | Typical SSP | Strategy
  1 | 00:00 | GREEN | £45 | Charge
  2 | 00:30 | GREEN | £43 | Charge
  ...
  33 | 16:00 | RED | £120 | Discharge
  34 | 16:30 | RED | £125 | Discharge
  ...
  48 | 23:30 | GREEN | £52 | Charge

Rows 315-320: Optimization Tips
  - Maximum 2 cycles per day to preserve battery life
  - Target 85% round-trip efficiency
  - Avoid partial cycles (reduces efficiency)
  - Monitor DUoS rate changes (April annually)
  - Track SSP volatility (adjust strategy)
```

---

##### `main()`

Main execution for dashboard update.

**Process:**
1. Connect to Google Sheets
2. Create/update time period dropdown (L6)
3. Create/update cost breakdown table (A250:F285)
4. Add period definitions (288-320)
5. Update control panel formatting
6. Add usage instructions (A325+)

**Runtime:** ~20 seconds

**Side Effects:**
- Modifies BESS worksheet
- Adds data validation rules
- Applies formatting
- Creates formulas

---

## 🔧 Utility Functions

### Connection Management

#### `connect()`

Used by all scripts. Establishes connections to:
1. BigQuery (data queries)
2. Google Sheets (output writing)

**Environment Variables:**
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON
- If not set, looks for `credentials.json` in project root

**Error Handling:**
```python
try:
    bq_client = bigquery.Client(project='inner-cinema-476211-u9')
except Exception as e:
    print(f"❌ BigQuery connection failed: {e}")
    sys.exit(1)

try:
    gc = gspread.service_account(filename='credentials.json')
    sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
    worksheet = sheet.worksheet('BESS')
except Exception as e:
    print(f"❌ Sheets connection failed: {e}")
    sys.exit(1)
```

### Data Validation

#### `validate_mpan(mpan_id)`

Validate MPAN ID format and range.

**Parameters:**
- `mpan_id` (str|int): MPAN to validate

**Returns:**
- `bool`: True if valid, False otherwise

**Rules:**
- Must be integer
- Range: 10-23 (inclusive)
- Maps to valid DNO

**Example:**
```python
validate_mpan(14)  # True (NGED-WM)
validate_mpan(9)   # False (too low)
validate_mpan(24)  # False (too high)
validate_mpan('14-WMID')  # True (extracts 14)
```

---

## ⚙️ Configuration

### Constants

```python
# BigQuery
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Google Sheets
DASHBOARD_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
WORKSHEET_NAME = 'BESS'

# Time Bands
RED_PERIODS = [33, 34, 35, 36, 37, 38]  # 16:00-19:00
AMBER_PERIODS = [13, 14, 15, 16, 29, 30, 31, 32]  # 06:00-08:00, 14:00-16:00
GREEN_PERIODS = [list of other 38 periods]

# Fixed Levies (£/MWh)
BSUOS_RATE = 3.40
TNUOS_RATE = 15.50
ENERGY_LEVIES = 10.25  # RO + FiT + CfD
FCP_RATE = 9.00

# Battery Defaults
DEFAULT_CAPACITY_MWH = 2.5
DEFAULT_POWER_MW = 1.0
DEFAULT_EFFICIENCY = 0.85
DEFAULT_CYCLES_PER_DAY = 2

# SO Payment Rates (£/MW/day)
FFR_RATE = 50.00
DCR_RATE = 13.33
DM_RATE = 9.44
DR_RATE = 5.00
BID_RATE = 1.67
BOD_RATE = 1.11

# Capacity Market (£/kW/year)
CM_RATE = 28.00

# Logging
LOG_DIR = 'logs'
LOG_RETENTION_DAYS = 7
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### Environment Setup

**credentials.json:**
```json
{
  "type": "service_account",
  "project_id": "inner-cinema-476211-u9",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "bess-dashboard@inner-cinema-476211-u9.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

**requirements.txt:**
```
gspread==6.2.1
google-cloud-bigquery==3.25.0
pandas==2.2.3
numpy==2.1.3
matplotlib==3.9.2
seaborn==0.13.2
google-auth==2.35.0
gspread-formatting==1.2.1
oauth2client==4.1.3
python-dateutil==2.9.0
pytz==2024.2
requests==2.32.3
urllib3==2.2.3
openpyxl==3.1.5
Pillow==11.0.0
```

---

## 📊 Data Models

### System Price Record

```python
{
  'settlement_date': datetime.date(2024, 11, 30),
  'settlement_period': 35,  # 1-48
  'ssp': 118.75,  # £/MWh
  'ssp_value': 118.75,  # Alias
  'time_band': 'RED',  # RED|AMBER|GREEN
  'hour': 17,  # 0-23
  'is_peak': True,  # RED or AMBER
  'day_of_week': 5  # 0=Mon, 6=Sun
}
```

### Cost Breakdown

```python
{
  'ssp': 75.00,  # System Sell Price
  'bsuos': 3.40,  # Balancing Services
  'tnuos': 15.50,  # Transmission Network
  'duos': 85.00,  # Distribution (varies by band)
  'energy_levies': 10.25,  # RO + FiT + CfD
  'fcp': 9.00,  # Feed-in Premium
  'total': 198.15,  # Sum of all
  'time_band': 'RED'
}
```

### Battery Parameters

```python
{
  'capacity_mwh': 2.5,  # Storage capacity
  'power_mw': 1.0,  # Max charge/discharge rate
  'efficiency': 0.85,  # Round-trip efficiency (85%)
  'cycles_per_day': 2,  # Daily cycles
  'degradation_rate': 0.02,  # 2% per year
  'warranty_cycles': 7300,  # 10 years × 2 cycles/day
  'voltage_level': 'LV'  # LV|HV|EHV
}
```

### Revenue Breakdown

```python
{
  'total_revenue': 343828.00,
  'streams': {
    'ppa': 123750.00,  # 36%
    'so_payments': 116550.00,  # 34%
    'arbitrage': 95400.00,  # 28%
    'capacity_market': 6904.00,  # 2%
    'other': 1224.00  # 0%
  },
  'total_costs': 259049.00,
  'costs': {
    'energy': 143550.00,  # 55%
    'duos': 68500.00,  # 26%
    'bsuos': 17200.00,  # 7%
    'tnuos': 19650.00,  # 8%
    'levies': 10149.00  # 4%
  },
  'net_profit': 84779.00,
  'profit_margin': 0.247,  # 24.7%
  'period_days': 90
}
```

---

**Next Steps:**
- [Apps Script Guide](APPS_SCRIPT_GUIDE.md) - Apps Script functions
- [Troubleshooting](TROUBLESHOOTING.md) - Issue resolution
- [Architecture](ARCHITECTURE.md) - System design
- [Configuration](CONFIGURATION.md) - Settings guide
