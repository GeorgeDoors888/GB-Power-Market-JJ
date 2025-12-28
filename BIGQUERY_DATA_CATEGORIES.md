# BigQuery Data Categorization by Purpose

**Generated**: December 22, 2025
**Project**: `inner-cinema-476211-u9.uk_energy_prod`

---

## 📊 Data Categories Overview

All tables are categorized by what they capture/produce for analysis:

---

## ⚡ GENERATION & FUEL MIX

**Purpose**: Real-time and historical power generation by fuel type, individual unit output

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **bmrs_fuelinst** | Generation by fuel type (MW) - WIND, NUCLEAR, CCGT, etc. | Every settlement period (30min) |
| **bmrs_fuelinst_iris** | Real-time generation by fuel type (last 55 days) | Continuous streaming |
| **bmrs_indgen** | Individual BM unit generation output | Every settlement period |
| **bmrs_indgen_iris** | Real-time individual unit output | Continuous streaming |
| **bmrs_windfor** | Wind generation forecasts (1-14 days ahead) | Every hour |
| **bmrs_temp** | Temperature data (affects demand) | Every hour |
| **bmrs_phybmdata** | Physical BM unit data | Every settlement period |

**Use Cases**:
- Battery arbitrage timing (when is wind high/low?)
- Fuel mix analysis (coal vs gas vs renewables)
- Individual power station tracking (Drax, Hinckley Point C)
- Generation capacity utilization

**Key Metrics You Get**:
- Current MW output by fuel type
- 24-hour generation trends (sparklines in dashboard)
- Wind/solar penetration percentages
- Nuclear baseload tracking

---

## 💰 BALANCING MECHANISM (TRADING)

**Purpose**: Bid-offer prices, accepted trades, BM unit revenues, National Grid balancing actions

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **bmrs_bod** | Bid-Offer Data - what units OFFERED to generate/reduce at what price | Every settlement period |
| **bmrs_boalf** | Balancing Acceptances - which bids/offers National Grid ACCEPTED | Every settlement period |
| **bmrs_boalf_iris** | Real-time acceptances (last 53 days) | Continuous streaming |
| **boalf_with_prices** | Acceptances WITH price estimates (derived from BOD matching) | Daily refresh |
| **bmrs_boalf_complete** | All acceptances + validation flags + revenue estimates | Daily refresh |
| **bmrs_netbsad** | Net balancing services adjustment data | Every settlement period |
| **bmrs_ebocf** | Energy bid-offer curves forecast | Every settlement period |
| **bm_bmu_kpis** | BM unit KPIs (average prices, volumes, success rates) | Daily aggregation |

**Use Cases**:
- **VLP Revenue Analysis**: How much did FFSEN005 earn from balancing?
- **Battery Strategy**: What prices trigger profitable discharges?
- **Market Behavior**: Which units consistently win acceptances?
- **Arbitrage Opportunities**: Spread between bid/offer prices

**Key Metrics You Get**:
- Offer prices (£/MWh) - what units charge to generate MORE
- Bid prices (£/MWh) - what units charge to generate LESS
- Acceptance volumes (MWh) - actual trades executed
- Revenue estimates (£) - earnings per unit per settlement period
- Oct 17-23 high-price event: £79.83/MWh average (6-day VLP windfall)

**Critical Tables for Battery Analysis**:
- `boalf_with_prices`: Individual acceptance prices (£85-110/MWh for Oct 17 VLP offers)
- `bmrs_disbsad`: Volume-weighted settlement proxy (£79.83/MWh Oct 17-23 avg)

---

## 💷 PRICING & SETTLEMENT

**Purpose**: Market prices (wholesale, imbalance, settlement), system costs

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **bmrs_mid** | Market Index Data - wholesale day-ahead/within-day prices | Every settlement period |
| **bmrs_mid_iris** | Real-time market index (last 55 days) | Continuous streaming |
| **bmrs_costs** | System Buy Price (SBP) & System Sell Price (SSP) - imbalance prices | Every settlement period |
| **bmrs_disbsad** | Disaggregated Imbalance Settlement - volume-weighted prices | Every settlement period |
| **bmrs_sip** | System imbalance prices | Every settlement period |
| **bmrs_mip** | Market index prices (detailed) | Every settlement period |

**Use Cases**:
- **Battery Revenue Forecasting**: When are imbalance prices high?
- **Wholesale vs Imbalance**: Compare day-ahead to real-time prices
- **Market Volatility**: Track price swings for trading strategies
- **Settlement Reconciliation**: Validate trading P&L

**Key Metrics You Get**:
- System Sell Price (£/MWh) - what you get PAID for surplus generation
- System Buy Price (£/MWh) - what you PAY for deficit (under-generation)
- Market Index Price (£/MWh) - wholesale benchmark
- Price volatility indicators

**CRITICAL**: SSP = SBP since Nov 2015 (BSC Mod P305 single imbalance price). Battery arbitrage is **temporal** (charge low, discharge high), not SSP/SBP spread (which is zero).

**Pricing Hierarchy**:
1. **Wholesale (MID)**: Day-ahead contract prices (~£50-80/MWh typical)
2. **Imbalance (COSTS/DISBSAD)**: Real-time balancing prices (can spike to £110+/MWh)
3. **Individual Acceptances (BOALF)**: Actual unit-specific clearing prices

---

## 📡 SYSTEM OPERATIONS

**Purpose**: Grid frequency, demand forecasts, system margins, operational warnings

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **bmrs_freq** | Grid frequency (Hz) - stability indicator | Every 10 seconds |
| **bmrs_freq_iris** | Real-time frequency (last 55 days) | Continuous streaming (10sec) |
| **bmrs_demandoutturn** | Actual demand outturn | Every settlement period |
| **bmrs_detsysprices** | Detailed system prices | Every settlement period |
| **bmrs_lolp** | Loss of load probability | Every settlement period |
| **bmrs_melimbalngc** | MEL imbalance NGC | Every settlement period |
| **bmrs_tbod** | Transmission boundary operating data | Every settlement period |
| **bmrs_tsdf** | Transmission system demand forecast | Daily |

**Use Cases**:
- **Frequency Response Revenue**: Track 50Hz stability (batteries earn for frequency correction)
- **Demand Forecasting**: Predict high-demand periods for premium pricing
- **System Stress**: Identify low-margin periods (scarcity pricing events)
- **Grid Stability**: Monitor frequency deviations triggering response payments

**Key Metrics You Get**:
- Grid frequency (target: 50.0Hz, acceptable: 49.5-50.5Hz)
- Demand forecasts (MW) for next 2-96 hours
- De-rated margins (available capacity vs demand)
- Loss of load probability (LOLP) - scarcity risk indicator

**Frequency Revenue Context**:
- Batteries earn £5-15k/MW/year for Dynamic Containment (frequency response)
- Grid frequency <49.5Hz or >50.5Hz = emergency response triggered
- Oct 17-23 high prices partly driven by frequency instability

---

## 🔌 GRID INFRASTRUCTURE

**Purpose**: Distribution network boundaries, grid supply points, interconnector flows

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **neso_dno_boundaries** | Distribution Network Operator geographical boundaries | Static reference |
| **neso_dno_reference** | DNO company details, contact info, license info | Static reference |
| **neso_gsp_boundaries** | Grid Supply Point geographical boundaries | Static reference |
| **neso_gsp_groups** | GSP group definitions and mappings | Static reference |
| **gb_power.duos_unit_rates** | DUoS rates by DNO/voltage (Red/Amber/Green pricing) | Annually updated |
| **gb_power.duos_time_bands** | Time periods for DUoS charges | Annually updated |
| **bmrs_intercon** | Interconnector flows (imports/exports) | Every settlement period |

**Use Cases**:
- **DNO Lookup for BESS**: Find DUoS charges by postcode/MPAN
- **Location Analysis**: Map BMUs to grid regions
- **Import/Export Tracking**: Monitor ElecLink, IFA, Viking Link flows
- **Network Constraint Identification**: Find congested GSP groups

**Key Metrics You Get**:
- DUoS charges: Red (16:00-19:30 weekdays), Amber (08:00-16:00), Green (overnight/weekend)
- Example UKPN-EPN HV: Red 4.837 p/kWh, Amber 0.457 p/kWh, Green 0.038 p/kWh
- Interconnector capacity: ElecLink 1000 MW, IFA 2000 MW, IFA2 1000 MW
- GSP demand by region

**BESS Integration**:
- DNO charges impact battery payback periods
- Red period charging (16:00-19:30) adds 4-5 p/kWh cost
- Green period charging (overnight) only 0.03-0.05 p/kWh
- Strategy: Charge Green, discharge Red = maximize arbitrage

---

## 📋 REFERENCE DATA

**Purpose**: BMU metadata, unit registrations, party information, fuel type lookups

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **dim_bmu** | BMU dimensional data - master reference for all BM units | Daily refresh |
| **bmu_metadata** | BMU metadata (capacity, fuel type, effective dates) | Daily refresh |
| **bmu_registration_data** | Full BMU registration details from Elexon | Monthly/on-demand |
| **vlp_unit_ownership** | Virtual Lead Party ownership mappings | Manual updates |
| **bmrs_derived_fuel_type_mapping** | Fuel type standardization lookups | Static reference |

**Use Cases**:
- **Unit Identification**: Map BMU ID to company name (FFSEN005 = F&S Energy)
- **Capacity Verification**: Check registered capacity vs actual output
- **Party Analysis**: Group units by owner/operator
- **Fuel Type Normalization**: Standardize CCGT/OCGT/GAS variations

**Key Metadata Available**:
- BMU ID → Company name (e.g., T_DRAXX-1 → Drax Power Limited)
- Registered capacity (MW)
- Fuel type (WIND, NUCLEAR, CCGT, BATTERY, etc.)
- Lead party name (trading entity)
- GSP group (location)
- Effective dates (when unit active)
- VLP/VTP flags (aggregator vs physical unit)

**Example Lookups**:
- FFSEN005 → F & S Energy Ltd (VLP Battery)
- FBPGM002 → Flexgen (VLP Battery)
- T_DRAXX-1 → Drax Power Station Unit 1 (BIOMASS)
- E_BRADB-1 → Bradford Renewable Energy (WIND)

---

## 📊 ANALYTICS & DERIVED DATA

**Purpose**: Pre-calculated KPIs, revenue summaries, aggregated metrics

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **bm_bmu_kpis** | BMU key performance indicators (avg prices, volumes, success rates) | Daily |
| **vlp_revenue_analysis** | Virtual Lead Party revenue breakdowns | Daily/on-demand |
| **bess_revenue_summary** | Battery energy storage system P&L summaries | Daily |
| **market_analysis_summary** | Market-wide metrics and trends | Daily |
| **capacity_market_revenue** | Capacity Market auction results and payments | Annually + monthly |

**Use Cases**:
- **VLP Dashboard**: Pre-built revenue metrics for FFSEN005, FBPGM002
- **Battery Performance**: Compare actual vs theoretical arbitrage revenue
- **Market Benchmarking**: How does your unit compare to market average?
- **Historical Trends**: Multi-year revenue/performance patterns

**Pre-Calculated Metrics**:
- Average acceptance prices by unit
- Daily/monthly revenue estimates
- Utilization rates (% of time unit active)
- Success rates (% of bids accepted)
- Capacity Market payments (£/kW/year)

**Analytics Features**:
- Trend analysis (7-day, 30-day, 90-day rolling averages)
- Percentile rankings (top 10% performers)
- Seasonal patterns (summer vs winter pricing)
- Event detection (high-price periods flagged)

---

## 🗂️ REMIT & COMPLIANCE

**Purpose**: Outage notifications, unavailability messages, regulatory transparency

### Key Tables

| Table | What It Captures | Update Frequency |
|-------|------------------|------------------|
| **bmrs_remit** | REMIT outage notifications (regulatory transparency) | Real-time |
| **bmrs_remit_iris** | Real-time REMIT messages (last ~50 days) | Continuous streaming |
| **bmrs_itsdo** | Intended transmission system demand outturn | Every settlement period |
| **bmrs_message** | System messages and alerts | Real-time |
| **bmrs_unavailability** | Unit unavailability declarations | Real-time |

**Use Cases**:
- **Outage Tracking**: Which power stations are offline and why?
- **Capacity Availability**: Real available vs registered capacity
- **Market Impact Analysis**: How did Sizewell B outage affect nuclear output?
- **Compliance Monitoring**: REMIT transparency requirements

**Key Information**:
- Unit unavailability start/end times
- Outage reasons (planned maintenance, forced outage, breakdown)
- Capacity reductions (MW unavailable)
- Expected return-to-service dates
- REMIT message types (withdrawal, modification, cancellation)

**Regulatory Context**:
- REMIT = Regulation on Energy Market Integrity and Transparency
- Units >100MW must report outages within 1 hour
- Affects wholesale prices (reduced supply = higher prices)
- Oct 17-23 high prices potentially linked to multiple outages

---

## 🎯 DATA USAGE BY ANALYSIS TYPE

### Battery Arbitrage Analysis
**Primary Tables**:
- `bmrs_costs` - Imbalance prices (charge cheap, discharge expensive)
- `boalf_with_prices` - Actual acceptance prices achieved
- `bmrs_fuelinst` - Fuel mix (high wind = low prices)
- `bmrs_freq` - Frequency response opportunities

**Example Query**: "Find settlement periods where imbalance price >£70/MWh AND wind generation >50%"

### VLP Revenue Tracking
**Primary Tables**:
- `bmrs_boalf` - Acceptance volumes
- `boalf_with_prices` - Acceptance prices
- `bmrs_disbsad` - Settlement proxy prices
- `dim_bmu` - Unit metadata

**Example Analysis**: "Calculate FFSEN005 monthly revenue from Oct 17-23 high-price event"

### Market Price Forecasting
**Primary Tables**:
- `bmrs_mid` - Wholesale prices
- `bmrs_windfor` - Wind forecasts (affects prices)
- `bmrs_demandoutturn` - Demand levels
- `bmrs_lolp` - Scarcity indicators

**Example Model**: "Predict next-day imbalance price based on wind forecast + demand + LOLP"

### Unit Performance Benchmarking
**Primary Tables**:
- `bm_bmu_kpis` - Pre-calculated KPIs
- `bmrs_indgen` - Individual unit output
- `bmrs_boalf` - Acceptance history
- `bmu_metadata` - Capacity/fuel type

**Example Comparison**: "Compare T_DRAXX-1 utilization rate vs other BIOMASS units"

---

## 📈 DATA VOLUMES & COVERAGE

### Massive Historical Tables (Multi-Year)
- **bmrs_bod**: 405M rows (3.5 years) - 40GB+ - Every bid/offer from every unit
- **bmrs_boalf**: 12.3M rows (3.5 years) - 5GB - All accepted balancing actions
- **bmrs_fuelinst**: 5.7M rows (3 years) - 2GB - 30-min fuel mix snapshots

### Real-Time IRIS Tables (Last 55 Days)
- **bmrs_fuelinst_iris**: 305k rows - Live generation data
- **bmrs_freq_iris**: 257k rows - 10-second frequency measurements
- **bmrs_boalf_iris**: 917k rows - Recent acceptances

### Reference Tables (Static/Slowly Changing)
- **dim_bmu**: 2,716 units - Master BM unit registry
- **neso_dno_reference**: 14 DNOs - Network operator details
- **gb_power.duos_unit_rates**: DUoS pricing by DNO/voltage

---

## 🔍 HOW TO FIND SPECIFIC DATA

### "I want to know..."

**"...what Drax is generating right now"**
→ `bmrs_indgen_iris` WHERE bmUnitId LIKE 'T_DRAXX%'

**"...when imbalance prices are highest"**
→ `bmrs_costs` ORDER BY systemSellPrice DESC

**"...which batteries made the most money in October"**
→ `boalf_with_prices` WHERE is_battery_storage = TRUE

**"...if grid frequency is stable"**
→ `bmrs_freq_iris` WHERE measurementTime >= NOW() - INTERVAL 1 HOUR

**"...what my DUoS charges are"**
→ `gb_power.duos_unit_rates` JOIN neso_dno_reference

**"...wind generation forecast for tomorrow"**
→ `bmrs_windfor` WHERE forecastDate = CURRENT_DATE() + 1

---

## 📚 Documentation Cross-References

- **Table Schemas**: [`docs/STOP_DATA_ARCHITECTURE_REFERENCE.md`](docs/STOP_DATA_ARCHITECTURE_REFERENCE.md)
- **Current Status**: [`BIGQUERY_DATA_STATUS_DEC22_2025.md`](BIGQUERY_DATA_STATUS_DEC22_2025.md)
- **Architecture**: [`docs/UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`](docs/UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)
- **Configuration**: [`PROJECT_CONFIGURATION.md`](PROJECT_CONFIGURATION.md)

---

*Last Updated: December 22, 2025*
