# UK Electricity System Charges - Data Sources

**Created:** 29 October 2025  
**Purpose:** Comprehensive guide to finding TNUoS, FiT, ROC, LEC, and BSUoS charges data  
**Status:** Research in Progress

---

## 📋 Overview of Charges

| Charge | Full Name | Purpose | Typical Cost | Who Pays |
|--------|-----------|---------|--------------|----------|
| **TNUoS** | Transmission Network Use of System | Transmission network costs | £0.50-15/kW/year | Generators & suppliers |
| **BSUoS** | Balancing Services Use of System | System balancing costs | £2-8/MWh | All users |
| **DUoS** | Distribution Use of System | Distribution network costs | Variable by DNO | End consumers |
| **FiT** | Feed-in Tariff | Support for small renewables | Variable | Suppliers (passed to consumers) |
| **ROC** | Renewables Obligation Certificates | Large-scale renewable support | £40-55/MWh | Suppliers |
| **LEC** | Levy Exemption Certificates | Exemption from CCL | £0-10/MWh | Exempt generators |

---

## 🔍 Data Sources Found in Your Workspace

### ✅ BSUoS (Balancing Services Use of System)

**Status:** Already available in your project!

**Location:**
- BMRS API Code: `BSUOS`
- BigQuery Table: `uk_energy_prod.bsuos` (mentioned in manifests)
- Historical Data: Found in GCS (`neso/balancing-services-use-of-system-bsuos-daily-forecast/`)

**API Endpoint:**
```
GET https://data.elexon.co.uk/bmrs/api/v1/datasets/BSUOS
```

**Data Available:**
- Daily BSUoS tariff (£/MWh)
- Settlement period level data
- Forecasts and actuals

**To Fetch:**
```bash
# Add to your ingest_elexon_fixed.py
python ingest_elexon_fixed.py --start 2025-01-01 --end 2025-10-29 --only BSUOS
```

---

### 🔍 TNUoS (Transmission Network Use of System)

**Status:** GIS zones found, tariff data needs sourcing

**Your Existing Data:**
- ✅ TNUoS Generation Zones (shapefiles): `/old_project/GIS_data/tnuosgenzones/`
- ❌ Tariff rates not yet ingested

**Official Data Sources:**

#### 1. National Grid ESO - TNUoS Tariffs
- **URL:** https://www.nationalgrideso.com/charging/transmission-network-use-system-tnuos-charges
- **Format:** Excel workbooks published annually
- **File Pattern:** `TNUoS Tariff for <YEAR>-<YEAR>.xlsx`
- **Content:**
  - Generation tariffs by zone (£/kW)
  - Demand tariffs by GSP Group
  - Zonal and residual charges

#### 2. Connected Data Portal
```
https://connecteddata.nationalgrideso.com/dataset/tnuos-tariff-information
```

#### 3. Elexon Portal
- Tariff data also republished via Elexon for settlement

**API Availability:** ❌ No direct API - Excel download required

**Recommended Approach:**
```python
# Similar to your DUoS pipeline
def fetch_tnuos_tariffs(year):
    url = f"https://www.nationalgrideso.com/document/tnuos-tariff-{year}-{year+1}"
    # Download Excel
    # Parse sheets: "Generation Tariffs", "Demand Tariffs"
    # Normalize to BigQuery schema
```

---

### 🔍 FiT (Feed-in Tariff)

**Status:** Data available from Ofgem

**Official Data Sources:**

#### 1. Ofgem FiT Register
- **URL:** https://www.ofgem.gov.uk/environmental-and-social-schemes/feed-in-tariff-fit-scheme
- **Data Portal:** https://www.ofgem.gov.uk/publications/feed-tariff-installation-report

#### 2. FiT Installation Data (CSV)
```
https://www.ofgem.gov.uk/publications/fit-installation-report-<MONTH>-<YEAR>
```

**Contains:**
- Installation capacity (kW)
- Technology type (Solar PV, Wind, Hydro, AD, CHP)
- Tariff generation rate (p/kWh)
- Tariff export rate (p/kWh)
- Installation date
- Accreditation number

#### 3. FiT Tariff Tables (Historical)
```
https://www.ofgem.gov.uk/environmental-and-social-schemes/feed-tariff-fit-scheme/tariff-tables
```

**API Availability:** ❌ CSV downloads only

**Typical Tariff Rates (2019 - scheme closed):**
| Technology | Generation Rate | Export Rate |
|------------|----------------|-------------|
| Solar PV <4kW | 3.93p/kWh | 5.24p/kWh |
| Wind <50kW | 8.74p/kWh | 5.24p/kWh |
| Hydro <100kW | 9.82p/kWh | 5.24p/kWh |

**Note:** FiT scheme closed to new applications 31 March 2019. Existing installations continue receiving payments.

---

### 🔍 ROC (Renewables Obligation Certificates)

**Status:** Data available from Ofgem

**Official Data Sources:**

#### 1. Ofgem ROC Register (Public)
- **URL:** https://www.renewablesandchp.ofgem.gov.uk/Public/ReportManager.aspx
- **Format:** CSV/Excel downloads
- **Content:**
  - ROC issuance by station
  - Technology type
  - Capacity (MW)
  - Output period
  - ROCs issued

#### 2. ROC Buy-Out Price (Annual)
```
https://www.ofgem.gov.uk/environmental-and-social-schemes/renewables-obligation-ro
```

**Historical Buy-Out Prices:**
| Year | Buy-Out Price | Recycle Value |
|------|---------------|---------------|
| 2024/25 | £60.10/ROC | TBD |
| 2023/24 | £58.05/ROC | £55.02/ROC |
| 2022/23 | £56.04/ROC | £53.38/ROC |
| 2021/22 | £54.06/ROC | £48.78/ROC |

#### 3. ROC Market Prices
- **E-ROC Auction:** https://www.emrdeliverybody.com/lists/ROC.aspx
- **Secondary Market:** Various brokers (not publicly available API)

**API Availability:** ❌ Manual downloads from Ofgem portal

**Recommended Scraping:**
```python
def fetch_roc_register():
    # Selenium/requests to Ofgem public reports
    base = "https://www.renewablesandchp.ofgem.gov.uk/Public/"
    # Download "Station Search" CSV
    # Download "ROC Issuance" reports
    # Parse into: station_id, technology, capacity_mw, rocs_issued, period
```

---

### 🔍 LEC (Levy Exemption Certificates)

**Status:** Data available from Ofgem

**Official Data Sources:**

#### 1. Ofgem LEC Register
- **URL:** https://www.ofgem.gov.uk/environmental-and-social-schemes/climate-change-levy/lec-register
- **Format:** CSV downloads
- **Content:**
  - Station name and location
  - Technology type (CHP, renewable)
  - Exemption level (%)
  - Output period
  - LECs issued (kWh)

#### 2. LEC Market Information
- **No centralized pricing** - bilateral OTC market
- **Typical Range:** £0.50-2.00 per LEC (1 LEC = 1 kWh exempt)

#### 3. CCL Rates (Context for LEC Value)
```
https://www.gov.uk/government/publications/rates-and-allowances-excise-duty-climate-change-levy
```

**Current CCL Rates (2024/25):**
- Electricity: £0.00775/kWh
- Gas: £0.00672/kWh
- LPG: £0.02175/kg

**API Availability:** ❌ CSV downloads only

---

## 🚀 Recommended Implementation Plan

### Phase 1: BSUoS (Immediate - Already Available)
```bash
# Add BSUOS to your real-time updater
.venv/bin/python ingest_elexon_fixed.py --start 2025-01-01 --end 2025-10-29 --only BSUOS

# Verify in BigQuery
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bsuos` 
ORDER BY settlementDate DESC LIMIT 10;

# Add to dashboard (new cell A13)
# Show: "⚡ BSUoS: £4.52/MWh"
```

### Phase 2: TNUoS (1-2 days work)
1. Download latest TNUoS tariff Excel from National Grid ESO
2. Parse generation zones (already have shapefiles)
3. Parse demand tariffs by GSP group
4. Create BigQuery table: `uk_energy_prod.tnuos_tariffs`
5. Schema:
```python
{
    "charging_year": "2025/26",
    "zone_id": "ZONE_1",
    "zone_name": "North Scotland",
    "tariff_type": "generation",  # or "demand"
    "tariff_gbp_per_kw": 15.23,
    "valid_from": "2025-04-01",
    "valid_to": "2026-03-31"
}
```

### Phase 3: ROC & FiT (2-3 days work)
1. **ROC:**
   - Scrape Ofgem public register
   - Manual entry of annual buy-out prices
   - Track issuance by technology type
   
2. **FiT:**
   - Download historical installation CSVs
   - Parse tariff tables (scheme closed but data valuable)
   - Create time series of installations

### Phase 4: LEC (1 day work)
1. Download Ofgem LEC register CSVs
2. Parse station exemptions
3. Manual tracking of CCL rates for context

---

## 📊 Proposed BigQuery Schema

### `tnuos_tariffs`
```sql
CREATE TABLE uk_energy_prod.tnuos_tariffs (
    charging_year STRING,
    zone_id STRING,
    zone_name STRING,
    tariff_type STRING,  -- 'generation' or 'demand'
    tariff_gbp_per_kw FLOAT64,
    gsp_group STRING,  -- for demand tariffs
    valid_from DATE,
    valid_to DATE,
    source_url STRING,
    last_updated TIMESTAMP
);
```

### `roc_register`
```sql
CREATE TABLE uk_energy_prod.roc_register (
    station_id STRING,
    station_name STRING,
    technology STRING,
    capacity_mw FLOAT64,
    output_period STRING,  -- 'Apr-2024'
    rocs_issued INT64,
    accreditation_date DATE,
    source STRING
);
```

### `roc_prices`
```sql
CREATE TABLE uk_energy_prod.roc_prices (
    obligation_year STRING,  -- '2024/25'
    buyout_price_gbp FLOAT64,
    recycle_value_gbp FLOAT64,
    market_price_gbp FLOAT64,  -- if available
    price_date DATE
);
```

### `fit_installations`
```sql
CREATE TABLE uk_energy_prod.fit_installations (
    installation_id STRING,
    technology STRING,
    capacity_kw FLOAT64,
    generation_tariff_p_per_kwh FLOAT64,
    export_tariff_p_per_kwh FLOAT64,
    installation_date DATE,
    tariff_start_date DATE,
    postcode_district STRING,
    dno STRING
);
```

### `lec_register`
```sql
CREATE TABLE uk_energy_prod.lec_register (
    station_id STRING,
    station_name STRING,
    technology STRING,
    exemption_level_pct INT64,
    output_period STRING,
    lecs_issued_kwh INT64,
    source STRING
);
```

---

## 🔗 Integration with Dashboard

Add new cells to show all charges:

```
Row 12: ⚡ BSUoS: £4.52/MWh
Row 13: 🔌 TNUoS (Gen): £12.34/kW/yr
Row 14: 🌍 ROC Price: £55.02
Row 15: 💰 Current Charges: £X.XX/MWh total
```

Calculate total system cost:
```python
def calculate_total_system_cost(mwh):
    bsuos = get_latest_bsuos()  # £/MWh
    tnuos = get_annual_tnuos() / 8760  # Convert annual to hourly
    duos = get_current_duos_band()  # p/kWh -> £/MWh
    
    total = bsuos + tnuos + duos
    return total * mwh
```

---

## 📚 Reference Documentation

### Official Sources
1. **Ofgem Data Portal:** https://www.ofgem.gov.uk/data-portal
2. **National Grid ESO Charging:** https://www.nationalgrideso.com/industry-information/charging
3. **BMRS API Docs:** https://data.elexon.co.uk/bmrs/api-documentation
4. **Connected Data Portal:** https://connecteddata.nationalgrideso.com

### Existing Code to Leverage
- `ingest_elexon_fixed.py` - Add BSUOS dataset
- `dashboard_updater_complete.py` - Add BSUoS/TNUoS cells
- `CLAUDE.md` - DUoS pipeline as template for TNUoS
- `old_project/GIS_data/tnuosgenzones/` - TNUoS zone shapefiles

---

## ✅ Action Items

### Immediate (Today)
- [x] Search workspace for existing charge data
- [ ] Enable BSUOS ingestion (already configured!)
- [ ] Add BSUoS to dashboard (cell A12 or A13)

### This Week
- [ ] Download latest TNUoS tariff Excel
- [ ] Create TNUoS parser similar to DUoS Excel parser
- [ ] Ingest TNUoS to BigQuery

### This Month
- [ ] Scrape Ofgem ROC register
- [ ] Download FiT installation CSVs
- [ ] Create LEC register table
- [ ] Build comprehensive cost calculator

---

## 🎯 Expected Outcomes

Once complete, your dashboard will show:
1. ✅ Real-time generation (FUELINST, WIND_SOLAR_GEN)
2. ✅ Wholesale prices (MID: N2EX, EPEX SPOT)
3. ✅ Distribution charges (DUoS - from CLAUDE project)
4. 🔜 Balancing charges (BSUoS)
5. 🔜 Transmission charges (TNUoS)
6. 🔜 Policy costs (ROC, FiT, LEC)
7. 🔜 **Total system cost per MWh**

This gives you the **complete UK electricity cost stack** from generation to consumer!

---

**Next Step:** Would you like me to:
1. Enable BSUoS ingestion immediately?
2. Build TNUoS tariff downloader/parser?
3. Create unified cost calculator function?
4. Set up ROC/FiT data scrapers?

Let me know which charge type is highest priority! 🚀
