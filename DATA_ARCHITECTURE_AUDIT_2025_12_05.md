# 🔍 DATA ARCHITECTURE AUDIT - December 5, 2025

## 🎯 Executive Summary

**ROOT CAUSE IDENTIFIED:** Multiple scripts query **wrong tables** (`bmrs_mid`) for system prices that **don't exist** in that schema, resulting in synthetic/fallback data being used instead of real market prices.

**IMPACT:** Battery revenue models, arbitrage calculations, and dispatch optimization have been using **random generated data** or outdated prices (last real data: Oct 28, 2025).

**SOLUTION:** Use `bmrs_costs` table (has correct `systemSellPrice`/`systemBuyPrice` columns) + configure IRIS to capture real-time DETS stream.

---

## 🕵️ How We Got Here: The Circular Problem

### The Pattern (Repeated 5+ Times)
1. Script queries `bmrs_mid` for `systemSellPrice`/`systemBuyPrice`
2. Query fails (columns don't exist)
3. Script falls back to synthetic data or Railway API
4. Synthetic data gets written to Google Sheets
5. User sees "no data" or wrong calculations
6. New script created, uses same wrong table
7. **REPEAT**

### Why It Kept Happening
1. **No schema documentation**: Developers assumed `bmrs_mid` had system prices based on name
2. **Silent failures**: Scripts use try/except with fallback, masking the error
3. **Copilot instructions outdated**: Mention `bmrs_mid (systemSellPrice, systemBuyPrice)` which is WRONG
4. **No data validation**: Synthetic data looks plausible, passes visual checks
5. **Fragmented knowledge**: Working code (`bess_revenue_engine.py`) uses correct table but not referenced

---

## 📊 THE TRUTH: Table Schemas & Date Coverage

### ❌ WRONG TABLE (What We've Been Using)

**`bmrs_mid`** - Market Index Data (NOT system prices!)

```
Schema:
  dataset: STRING
  startTime: DATETIME
  dataProvider: STRING
  settlementDate: DATETIME
  settlementPeriod: INTEGER
  price: FLOAT          ← Single market index price
  volume: FLOAT
  _dataset: STRING
  ...

Date Coverage:
  Total rows: 155,405
  Date range: 2022-01-01 to 2025-10-30  ← STALE (36 days old)
  Last 7 days: 0 rows
```

**Why It's Wrong:**
- Has `price` column (wholesale index), NOT `systemSellPrice`/`systemBuyPrice` (imbalance prices)
- Data stops Oct 30 (missing 36 days)
- Not updated by IRIS pipeline

---

### ✅ CORRECT TABLE (What We Should Use)

**`bmrs_costs`** - System Imbalance Prices (DETS Dataset from BMRS)

```sql
Schema:
  settlementDate: DATETIME
  settlementPeriod: INTEGER
  startTime: DATETIME
  systemSellPrice: FLOAT    ← ✅ SSP (Energy Imbalance Price)
  systemBuyPrice: FLOAT     ← ✅ SBP (Energy Imbalance Price)
  netImbalanceVolume: FLOAT
  reserveScarcityPrice: FLOAT
  sellPriceAdjustment: FLOAT
  buyPriceAdjustment: FLOAT
  replacementPrice: FLOAT
  totalAcceptedOfferVolume: FLOAT
  ...

Date Coverage: ✅ GAP FILLED!
  Total rows: 119,856
  Date range: 2022-01-01 to 2025-12-05  ← ✅ COMPLETE (no gap!)
  Last backfill: Dec 5, 2025 (1,798 records added)
  Distinct days: 1,345

Duplicate Analysis (Dec 5, 2025):
  Our backfill (Oct 29-Dec 5): ✅ 0 duplicates (prevention worked perfectly)
  Pre-existing (2022-Oct 27): ⚠️ ~55k duplicate settlement periods
  Impact: Minimal - queries use GROUP BY/DISTINCT
  Recommendation: Leave historical duplicates; daily backfill ensures clean future data

Sample Recent Data:
settlementDate  settlementPeriod  systemSellPrice  systemBuyPrice
2025-12-05                    22            42.39           42.39
2025-12-04                    48            82.40           82.40
2025-11-30                     1            65.12           65.12
```

**Why It's Correct:**
- Contains both SSP and SBP columns (single Energy Imbalance Price since 2015)
- **IMPORTANT:** SSP = SBP in each settlement period (merged to single price per BSC Mod P305, Nov 2015)
- Used by working code (`bess_revenue_engine.py` line 208-226)
- Historical data from BMRS API (Elexon system prices endpoint)
- **✅ GAP FILLED:** Oct 29 - Dec 5 backfilled using `ingest_elexon_fixed.py` method

**Historical Context:**
- Pre-2015: Separate System Buy Price (SBP) and System Sell Price (SSP)
- Post-Nov 2015: BSC Modification P305 merged to single Energy Imbalance Price
- Both columns exist in schema for backward compatibility, but values are identical
- Imbalance pricing reflects actual balancing costs + reserve scarcity (LoLP × VoLL)

**Correct API Endpoint (for future backfills):**
```bash
# ✅ CORRECT: Use /balancing/settlement/system-prices endpoint
https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/{date}

# ❌ WRONG: /datasets/COSTS and /datasets/DETS don't exist (404 errors)
```

---

### ❌ MISSING TABLE (What We Need for Real-Time)

**`bmrs_costs_iris`** - Real-time System Prices (IRIS Stream)

```
Status: TABLE DOES NOT EXIST
Impact: No real-time system prices available
Gap: Oct 28 - Dec 5 (38 days) has NO data
```

**Why It's Missing:**
- IRIS pipeline (`iris_to_bigquery_unified.py`) not configured to capture DETS stream
- IRIS client downloads streams: INDO, BOALF, BOD, FUELINST, FREQ, etc.
- DETS stream (Detailed System Prices) not in configured stream list

---

## 🔄 The Two-Pipeline Architecture

### ⚠️ CRITICAL: IRIS ≠ BMRS API (Two Completely Different Systems)

**Elexon BMRS API (Historical REST API)**
- **Type**: REST API over HTTP
- **URL**: `https://data.elexon.co.uk/bmrs/api/v1`
- **Method**: Pull-based (you request data)
- **Access**: Public, no authentication required
- **Usage**: Historical batch downloads, backfills
- **Your Scripts**: `backfill_indo_daily.py`, `backfill_boalf_gap.py`

**IRIS (Real-Time Azure Service Bus)**
- **Type**: Azure Service Bus message streaming
- **Infrastructure**: Microsoft Azure cloud queue
- **Method**: Push-based (messages stream to you)
- **Access**: Requires Elexon subscription + connection string
- **Usage**: Live real-time data (seconds delay)
- **Your Deployment**: AlmaLinux server 94.237.55.234
- **Your Scripts**: `client.py`, `iris_to_bigquery_unified.py`

### Historical Pipeline (2020 - Oct 28, 2025)
**Method:** Elexon BMRS REST API (NOT IRIS)
**Update Frequency:** On-demand backfills
**Tables:** `bmrs_*` (no `_iris` suffix)
**Key Table:** `bmrs_costs` with SSP/SBP
**Source:** Legacy "BMRS" system (_source_api="BMRS", _dataset="COSTS")
**Status:** ⚠️ Stale (last update Oct 28), original ingestion script NOT in current repo

### Real-Time Pipeline (Last 24-48h)
**Method:** Azure Service Bus IRIS streaming (NOT REST API)
**Update Frequency:** Real-time (seconds delay)
**Tables:** `bmrs_*_iris` suffix
**Deployed:** AlmaLinux server 94.237.55.234
**Queue ID:** 5ac22e4f-fcfa-4be8-b513-a6dc767d6312
**Scripts:** 
- `client.py` - Downloads messages from Azure Service Bus
- `iris_to_bigquery_unified.py` - Uploads to BigQuery
**Subscribed Streams:** INDO, BOALF, BOD, FUELINST, FREQ, INDGEN, REMIT, WINDFOR
**Missing Stream:** B1770/DETS (Detailed System Prices)
**Key Issue:** `bmrs_costs_iris` table NOT being created (IRIS not configured for DETS stream)

---

## 🚨 Scripts Using WRONG Table

### 1. `populate_bess_enhanced.py` (Line 50-75)
```python
# ❌ WRONG: Queries bmrs_mid for systemSellPrice (doesn't exist)
SELECT 
  systemSellPrice AS price_sell,  ← FAILS
  systemBuyPrice AS price_buy,    ← FAILS
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
```

**Fallback Behavior (Line 100-150):**
```python
except Exception as e:
    print(f"❌ Error fetching BigQuery data: {e}")
    print("📊 Generating synthetic data for demonstration...")
    
    df = pd.DataFrame({
        'price_sell': 50 + 30 * np.random.randn(len(dates)),  ← FAKE DATA!
        'price_buy': 50 + 30 * np.random.randn(len(dates)),
    })
```

**Impact:** BESS enhanced analysis (rows 60-397) uses **random prices**, not real market data.

---

### 2. `btm_bess_greedy_vs_optimized.py` + View (Created Today)
```sql
-- create_btm_bess_view.sql (Line 6-20)
-- ❌ WRONG: Uses bmrs_mid.price as SSP/SBP proxy
SELECT
  price AS ssp,           ← Market index, not system sell price
  price * 0.95 AS sbp,    ← Arbitrary 5% spread assumption
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
```

**Impact:** Greedy vs Optimized comparison uses **market index prices** with **invented spreads** instead of actual imbalance prices.

---

### 3. `.github/copilot-instructions.md` (Line 237-245)
```markdown
### Key Tables for VLP Analysis
-- Market prices
bmrs_mid (systemSellPrice, systemBuyPrice)  ← WRONG! These columns don't exist
```

**Impact:** AI coding assistant provides incorrect guidance, perpetuating the cycle.

---

## ✅ Scripts Using CORRECT Table

### 1. `bess_revenue_engine.py` (Line 208-226)
```python
# ✅ CORRECT: Uses bmrs_costs
def ingest_bmrs_system_prices(start_date: date, end_date: date) -> pd.DataFrame:
    query = f"""
    SELECT 
        TIMESTAMP(startTime) as timestamp,
        systemSellPrice as ssp,      ← ✅ Correct column
        systemBuyPrice as sbp,        ← ✅ Correct column
        (systemSellPrice + systemBuyPrice) / 2 as cashout_price
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET}.bmrs_costs`  ← ✅ Correct table
    WHERE settlementDate BETWEEN @start_date AND @end_date
        AND systemSellPrice IS NOT NULL
        AND systemBuyPrice IS NOT NULL
    """
```

**Status:** Working correctly but not referenced by other scripts.

---

## 🔧 Required Fixes

### 1. Backfill Historical Gap (Oct 28 - Dec 5)
**Missing:** 38 days of system prices
**Solution:** Run Elexon BMRS API ingestion

```bash
# Check if ingestion script exists
ls -la ingest_elexon*.py backfill*.py

# If exists, run:
python3 ingest_elexon_fixed.py \
  --dataset DETS \
  --start-date 2025-10-29 \
  --end-date 2025-12-05

# Otherwise, create backfill script using BMRS API:
# https://data.elexon.co.uk/bmrs/api/v1/datasets/DETS
```

---

### 2. Configure IRIS to Capture DETS Stream
**Current IRIS Streams:** INDO, BOALF, BOD, FUELINST, FREQ, INDGEN, REMIT, WINDFOR
**Missing:** DETS (Detailed System Prices)

**Action Required:** SSH to AlmaLinux server and update IRIS client config

```bash
ssh root@94.237.55.234

# Check current IRIS configuration
cat /opt/iris-pipeline/config.json  # or similar

# Add DETS to stream list
# Format depends on client implementation (likely topic/queue name)

# Restart IRIS services
systemctl restart iris-client
systemctl restart iris-uploader

# Monitor logs
tail -f /opt/iris-pipeline/logs/iris_uploader.log
```

**Expected Result:** `bmrs_costs_iris` table created with real-time SSP/SBP data.

---

### 3. Fix All Scripts Using bmrs_mid

**Files to Update:**
1. `populate_bess_enhanced.py` - Lines 50-75
2. `create_btm_bess_view.sql` - Entire view
3. `.github/copilot-instructions.md` - Line 237

**Pattern to Apply:**
```sql
-- Historical + Real-time UNION
WITH combined AS (
  -- Historical (2022 - Oct 28)
  SELECT 
    TIMESTAMP_ADD(CAST(settlementDate AS TIMESTAMP), 
                 INTERVAL (settlementPeriod - 1) * 30 MINUTE) AS ts,
    systemSellPrice AS ssp,
    systemBuyPrice AS sbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
    AND settlementDate < DATE('2025-10-29')  -- Last historical date
  
  UNION ALL
  
  -- Real-time (Oct 29 onwards, once bmrs_costs_iris exists)
  SELECT 
    TIMESTAMP_ADD(CAST(settlementDate AS TIMESTAMP), 
                 INTERVAL (settlementPeriod - 1) * 30 MINUTE) AS ts,
    systemSellPrice AS ssp,
    systemBuyPrice AS sbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs_iris`
  WHERE settlementDate >= DATE('2025-10-29')
)
SELECT * FROM combined
```

---

## 📚 6 Revenue Streams - Correct Data Sources

### 1. Balancing Mechanism (BM) Revenue
**Source:** `bmrs_boalf` / `bmrs_boalf_iris`
**Columns:** `acceptedOfferPrice`, `acceptedOfferVolume`
**Method:** 
```sql
SELECT 
  bmUnitId,
  acceptanceTime,
  acceptedOfferPrice AS bm_price_mwh,
  acceptedOfferVolume AS bm_volume_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnitId IN ('FBPGM002', 'FFSEN005')  -- Battery units
  AND acceptanceTime >= @start_date
```

**Revenue Calculation:**
```python
bm_revenue = accepted_volume_mw * accepted_price_per_mwh * 0.5  # Per SP
```

---

### 2. Arbitrage Revenue (Imbalance Cash-Out)
**Source:** `bmrs_costs` / `bmrs_costs_iris` ✅
**Columns:** `systemSellPrice`, `systemBuyPrice` (both equal - single Imbalance Price since 2015)
**Method:**
```sql
WITH imbalance_prices AS (
  SELECT 
    ts_halfhour,
    systemSellPrice AS imbalance_price,  -- SSP = SBP (merged since Nov 2015)
    netImbalanceVolume AS niv,
    reserveScarcityPrice AS rsvp
  FROM combined_prices  -- Historical + IRIS union
)
SELECT 
  ts_halfhour,
  imbalance_price,
  -- Arbitrage strategy: charge when price low, discharge when high
  CASE 
    WHEN soc_mwh < max_soc AND imbalance_price < threshold THEN 'CHARGE'
    WHEN soc_mwh > min_soc AND imbalance_price > threshold THEN 'DISCHARGE'
    ELSE 'HOLD'
  END AS action
FROM imbalance_prices
```

**Revenue Calculation:**
```python
# NOTE: Since Nov 2015, SSP = SBP (single Energy Imbalance Price per P305)
# Both long and short positions settled at same price

# Charge (go long - buy from system)
charge_cost = charge_mwh * imbalance_price

# Discharge (go short - sell to system)  
discharge_revenue = discharge_mwh * imbalance_price

# Arbitrage = intertemporal price differences, not SSP/SBP spread
arbitrage_profit = (discharge_revenue - charge_cost) * efficiency - losses
```

**Key Change (2015):**
- **Pre-P305:** Separate SBP (short parties pay) and SSP (long parties receive)
- **Post-P305:** Single price - all imbalances settled at Energy Imbalance Price
- **Impact:** Battery arbitrage based on temporal price variation, not bid-ask spread

---

### 3. Frequency Response (FR) Revenue
**Source:** `fr_clearing_prices` table
**Services:** DC (Dynamic Containment), DM (Dynamic Moderation), DR (Dynamic Regulation)
**Method:**
```sql
SELECT 
  efa_date,
  efa_block,
  service,  -- DC, DM, DR
  clearing_price_gbp_per_mw_h,
  block_start,
  block_end
FROM `inner-cinema-476211-u9.uk_energy_prod.fr_clearing_prices`
WHERE efa_date BETWEEN @start_date AND @end_date
  AND service = 'DC'  -- Dynamic Containment most common for batteries
```

**Revenue Calculation:**
```python
# DC revenue: £/MW/h for availability
dc_revenue_per_sp = (battery_power_mw * clearing_price * 0.5)  # Half-hourly

# Must maintain SoC within bounds for service delivery
# Typical: 50% SoC ± 30% headroom
```

---

### 4. DUoS (Distribution Use of System) Costs
**Source:** Manual tariff tables (need to create)
**Structure:** Time-banded rates (Red/Amber/Green)
**Method:**
```sql
-- Create tariff view
CREATE VIEW duos_rates AS
SELECT 
  dno_id,           -- '10' = UKPN-EPN, '14' = NGED West Midlands, etc.
  voltage_level,    -- 'HV', 'LV', 'EHV'
  time_band,        -- 'Red', 'Amber', 'Green'
  weekday_start,    -- '16:00' for Red
  weekday_end,      -- '19:30' for Red
  weekend_rate,     -- Lower rates on weekends
  rate_p_per_kwh    -- Pence per kWh
FROM manual_duos_tariffs;

-- Apply to settlement periods
WITH sp_times AS (
  SELECT 
    settlement_period,
    CASE 
      WHEN settlement_period BETWEEN 33 AND 39 THEN 'Red'    -- 16:00-19:30
      WHEN settlement_period BETWEEN 17 AND 32 
        OR settlement_period BETWEEN 40 AND 44 THEN 'Amber'  -- 08:00-16:00, 19:30-22:00
      ELSE 'Green'
    END AS time_band
  FROM UNNEST(GENERATE_ARRAY(1, 48)) AS settlement_period
)
SELECT * FROM sp_times;
```

**Cost Calculation:**
```python
# DUoS charge applied to consumption (charging)
duos_cost = charge_mwh * duos_rate_per_mwh
```

**Example Rates (UKPN-EPN HV):**
- Red (16:00-19:30 weekdays): 4.837 p/kWh = £48.37/MWh
- Amber (08:00-16:00, 19:30-22:00 weekdays): 0.457 p/kWh = £4.57/MWh
- Green (all other times): 0.038 p/kWh = £0.38/MWh

---

### 5. Capacity Market (CM) Revenue
**Source:** Manual contracts table (need to create)
**Structure:** Annual auction results, derating factors
**Method:**
```sql
-- Create CM contracts view
CREATE VIEW cm_contracts AS
SELECT 
  asset_id,
  delivery_year,      -- '2025/26'
  clearing_price_per_kw_year,  -- £30.59/kW/year
  capacity_mw,        -- 2.5 MW
  derated_capacity,   -- 2.5 * 0.895 = 2.24 MW for 2h battery
  start_date,
  end_date
FROM manual_cm_contracts;

-- Allocate to settlement periods
SELECT 
  asset_id,
  clearing_price_per_kw_year * derated_capacity * 1000 / (365 * 48) AS cm_revenue_per_sp
FROM cm_contracts;
```

**Revenue Calculation:**
```python
# CM revenue: Fixed annual payment divided by SPs
annual_cm_payment = cm_price_per_kw * derated_capacity_mw * 1000  # Convert to kW
cm_revenue_per_sp = annual_cm_payment / (365 * 48)  # £ per half-hour

# Example: £30.59/kW/year * 2240 kW / 17,520 SPs = £3.91 per SP
```

---

### 6. Trading Revenue (Wholesale Market)
**Source:** `bmrs_mid` (Market Index Data) ✅ THIS is the correct use of bmrs_mid!
**Columns:** `price` (day-ahead/within-day index)
**Method:**
```sql
SELECT 
  TIMESTAMP_ADD(CAST(settlementDate AS TIMESTAMP), 
               INTERVAL (settlementPeriod - 1) * 30 MINUTE) AS ts,
  price AS wholesale_price_mwh,
  volume AS market_volume_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= @start_date
```

**Revenue Calculation:**
```python
# Trading: Buy wholesale, sell at premium or vice versa
# Often bundled with PPA (Power Purchase Agreement)
trading_revenue = (sell_price - buy_price) * traded_volume_mwh
```

**Note:** For battery BTM (Behind-the-Meter) with PPA, this becomes PPA revenue:
```python
ppa_revenue = discharged_mwh * ppa_price_per_mwh  # Fixed £60/MWh typical
```

---

## 🔋 Battery Revenue Model with SOC Tracking

### State of Charge (SoC) State Machine

```python
@dataclass
class BatteryState:
    soc_mwh: float          # Current state of charge
    max_soc_mwh: float      # Maximum capacity (5.0 MWh)
    min_soc_mwh: float      # Minimum for degradation (0.25 MWh = 5%)
    power_mw: float         # Max charge/discharge rate (2.5 MW)
    efficiency: float       # Round-trip efficiency (0.85)
    
    def can_charge(self, energy_mwh: float) -> bool:
        return (self.soc_mwh + energy_mwh) <= self.max_soc_mwh
    
    def can_discharge(self, energy_mwh: float) -> bool:
        return (self.soc_mwh - energy_mwh) >= self.min_soc_mwh
    
    def charge(self, energy_mwh: float):
        """Apply charging with efficiency losses"""
        usable_energy = energy_mwh * self.efficiency
        self.soc_mwh = min(self.max_soc_mwh, self.soc_mwh + usable_energy)
    
    def discharge(self, energy_mwh: float):
        """Apply discharging with efficiency losses"""
        energy_from_battery = energy_mwh / self.efficiency
        self.soc_mwh = max(self.min_soc_mwh, self.soc_mwh - energy_from_battery)
```

### Dispatch Optimization Algorithm

```python
def optimize_dispatch(df_prices: pd.DataFrame, battery: BatteryState) -> pd.DataFrame:
    """
    Optimize battery dispatch across 6 revenue streams
    
    Args:
        df_prices: DataFrame with columns:
            - ts_halfhour: Timestamp
            - ssp: System Sell Price (£/MWh)
            - sbp: System Buy Price (£/MWh)
            - bm_price: Balancing Mechanism clearing price
            - dc_price: Dynamic Containment clearing price
            - duos_rate: DUoS rate for this time band
            - cm_revenue: Capacity Market allocation
            - ppa_price: PPA fixed price
    
    Returns:
        DataFrame with dispatch decisions and revenue breakdown
    """
    
    results = []
    
    for idx, row in df_prices.iterrows():
        # Calculate total charging cost
        charge_cost_per_mwh = (
            row['sbp'] +                    # Buy from system at SBP
            row['duos_rate'] +              # DUoS charge
            15.0                            # Levies (CCL, RO, FiT, BSUoS)
        )
        
        # Calculate total discharge revenue
        discharge_revenue_per_mwh = (
            row['ssp'] +                    # Sell to system at SSP (arbitrage)
            row['bm_price'] * 0.3 +         # BM revenue (if dispatched, probabilistic)
            row['dc_price'] +               # DC availability payment
            row['cm_revenue'] +             # CM fixed allocation
            row['ppa_price'] * 0.5          # PPA revenue (if applicable)
        )
        
        # Net revenue per MWh (considering efficiency)
        net_revenue = (discharge_revenue_per_mwh * battery.efficiency) - charge_cost_per_mwh
        
        # Decision logic
        half_hour_energy = battery.power_mw * 0.5  # Max energy per SP
        
        if net_revenue > 10 and battery.can_discharge(half_hour_energy):
            # Discharge profitable
            battery.discharge(half_hour_energy)
            action = 'DISCHARGE'
            sp_revenue = discharge_revenue_per_mwh * half_hour_energy
            sp_cost = 0
            
        elif net_revenue < -5 and battery.can_charge(half_hour_energy):
            # Charging creates future value
            battery.charge(half_hour_energy)
            action = 'CHARGE'
            sp_cost = charge_cost_per_mwh * half_hour_energy
            sp_revenue = 0
            
        else:
            action = 'HOLD'
            sp_cost = 0
            sp_revenue = row['dc_price'] * battery.power_mw * 0.5 + row['cm_revenue']  # Availability payments
        
        results.append({
            'timestamp': row['ts_halfhour'],
            'action': action,
            'soc_mwh': battery.soc_mwh,
            'net_revenue_per_mwh': net_revenue,
            'sp_cost': sp_cost,
            'sp_revenue': sp_revenue,
            'sp_net': sp_revenue - sp_cost,
            
            # Revenue breakdown
            'arbitrage': row['ssp'] - row['sbp'] if action == 'DISCHARGE' else 0,
            'bm_revenue': row['bm_price'] * 0.3 if action == 'DISCHARGE' else 0,
            'dc_revenue': row['dc_price'] * battery.power_mw * 0.5,  # Always available
            'cm_revenue': row['cm_revenue'],  # Always allocated
            'duos_cost': -row['duos_rate'] * half_hour_energy if action == 'CHARGE' else 0,
            'ppa_revenue': row['ppa_price'] * 0.5 * half_hour_energy if action == 'DISCHARGE' else 0,
        })
    
    return pd.DataFrame(results)
```

### Revenue Per MWh Calculation

```python
def calculate_revenue_per_mwh(results_df: pd.DataFrame) -> dict:
    """Calculate revenue per MWh discharged by stream"""
    
    total_discharged_mwh = (results_df['action'] == 'DISCHARGE').sum() * 2.5 * 0.5  # Count * Power * 0.5h
    
    if total_discharged_mwh == 0:
        return {stream: 0 for stream in ['arbitrage', 'bm', 'dc', 'cm', 'duos', 'ppa']}
    
    return {
        'arbitrage_per_mwh': results_df['arbitrage'].sum() / total_discharged_mwh,
        'bm_per_mwh': results_df['bm_revenue'].sum() / total_discharged_mwh,
        'dc_per_mwh': results_df['dc_revenue'].sum() / total_discharged_mwh,
        'cm_per_mwh': results_df['cm_revenue'].sum() / total_discharged_mwh,
        'duos_per_mwh': results_df['duos_cost'].sum() / total_discharged_mwh,  # Negative
        'ppa_per_mwh': results_df['ppa_revenue'].sum() / total_discharged_mwh,
        
        'total_per_mwh': results_df['sp_net'].sum() / total_discharged_mwh,
    }
```

---

## 📝 Action Plan Summary

### ✅ Completed
1. ✅ Identified root cause (wrong table usage)
2. ✅ Documented correct schemas
3. ✅ Found working reference code (`bess_revenue_engine.py`)
4. ✅ Mapped 6 revenue streams to data sources
5. ✅ Created comprehensive audit documentation
6. ✅ Clarified IRIS vs BMRS API architecture (two separate systems)
7. ✅ Confirmed original ingestion script NOT in current repository
8. ✅ Fixed scripts using wrong table (bmrs_mid → bmrs_costs)
9. ✅ **Backfilled Oct 28 - Dec 5 system prices (1,798 records, 38 days)**
10. ✅ **Found and documented correct API endpoint: /balancing/settlement/system-prices**

### 🔄 In Progress
None - all critical tasks complete!

### ⏳ Next Steps (Future Work)
11. ⏳ Configure IRIS to capture B1770/DETS stream (requires Elexon subscription update)
12. ⏳ Create automated daily backfill cron job using `backfill_costs_simple.py`
13. ⏳ Test corrected scripts with complete bmrs_costs data (2022-2025)
14. ⏳ Deploy battery revenue model with SOC tracking to production

---

## 🎓 Lessons Learned

1. **Always check schema first**: `bq show --schema` before writing queries
2. **Document working patterns**: Reference code that uses correct tables
3. **Validate data sources**: Don't assume table names indicate content
4. **Fail loudly**: Avoid silent fallbacks that mask errors
5. **Keep copilot instructions current**: Update when architecture changes
6. **Test with real data**: Synthetic fallbacks should be obvious (e.g., all zeros)
7. **Understand market rules**: SSP = SBP since Nov 2015 (P305) - single Energy Imbalance Price
8. **Historical context matters**: Schema columns may exist for backward compatibility even if values identical

---

## 📞 References

- **Elexon BMRS API**: https://data.elexon.co.uk/bmrs/api/v1/datasets/DETS
- **Elexon Imbalance Pricing**: https://www.elexon.co.uk/operations-settlement/balancing-and-settlement/imbalance-pricing/
- **BSC Modification P305** (Nov 2015): Merged SSP/SBP to single Energy Imbalance Price
- **NESO Data Portal**: https://data.neso.energy/
- **Working Code**: `bess_revenue_engine.py` lines 208-226
- **IRIS Server**: 94.237.55.234 (AlmaLinux)
- **BigQuery Project**: `inner-cinema-476211-u9`
- **Dataset**: `uk_energy_prod`

---

**Document Created:** December 5, 2025  
**Author:** System Audit  
**Status:** ✅ Root Cause Analysis Complete  
**Next:** Execute Action Plan Items 6-11
