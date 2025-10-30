# CLAUDE Energy Data Documentation
**Project:** GB Power Market Data Repository  
**Last Updated:** 29 October 2025  
**Purpose:** Comprehensive documentation of all UK electricity market data sources, methodologies, and ingestion processes

---

## Table of Contents
1. [Overview](#1-overview)
2. [Data Categories](#2-data-categories)
3. [DNO License Areas](#3-dno-license-areas)
4. [Data Sources & Methodologies](#4-data-sources--methodologies)
5. [API Endpoints](#5-api-endpoints)
6. [File Structure](#6-file-structure)
7. [Ingestion Pipelines](#7-ingestion-pipelines)
8. [Data Quality & Validation](#8-data-quality--validation)
9. [Update Schedules](#9-update-schedules)
10. [Authentication & Access](#10-authentication--access)

---

## 1) Overview

This repository aggregates and normalizes UK electricity market data from multiple authoritative sources:

- **BMRS (Balancing Mechanism Reporting Service)** - National Grid ESO
- **Elexon Insights API** - Settlement and operational data
- **DNO Portals (14 license areas)** - Distribution charges and network data
- **Ofgem** - Regulatory schemes (FiT, ROC, LEC, BSUoS)
- **NESO (National Energy System Operator)** - System forecasts

**Key Principle:** All data extracted from official sources with NO estimates or synthetic data.

---

## 2) Data Categories

### 2.1 Wholesale Market Data
| Dataset | Source | Update Frequency | Coverage | Storage |
|---------|--------|------------------|----------|---------|
| Market Index Data (MID) | BMRS API | 5 minutes | Real-time | BigQuery: `bmrs_mid` |
| N2EX Day-Ahead Prices | BMRS API | 5 minutes | Real-time | Dashboard Cell A10 |
| EPEX SPOT Prices | BMRS API | 5 minutes | Real-time | Dashboard Cell A11 |
| Fuel Mix (FUELINST) | BMRS API | 5 minutes | Real-time | BigQuery: `bmrs_fuelinst` |
| Wind & Solar Generation | BMRS API | 5 minutes | Real-time | BigQuery: `bmrs_wind_solar_gen` |

**Methodology:**
```python
# Example: MID price ingestion (dashboard_updater_complete.py)
def get_mid_prices():
    url = "https://api.bmrs.co.uk/BMRS/MID/v1"
    params = {"ServiceType": "xml"}
    response = requests.get(url, params=params)
    # Parse XML, extract N2EX and EPEX SPOT prices
    # Update dashboard cells A10, A11 every 5 minutes
```

### 2.2 Distribution Use of System (DUoS)
| Component | Description | Unit | Temporal Resolution |
|-----------|-------------|------|---------------------|
| Red/Amber/Green Bands | Time-of-use periods | Time windows | Daily (weekday/weekend) |
| Unit Rates | Energy charges | p/kWh | Half-hourly |
| Standing Charges | Fixed daily charges | £/day | Annual |
| Capacity Charges | Demand charges | £/kVA/day | Annual |

**14 DNO License Areas** (see Section 3)

**Methodology:**
- **API-based (UKPN, NPg, ENWL, SPEN):** OpenDataSoft JSON/CSV endpoints
- **File-based (NGED, SSEN):** Annual "Schedule of Charges" Excel/PDF downloads
- **Parsing:** Extract Annex 1 (time bands) + HH unit rate tables
- **Normalization:** Map UR1/UR2/UR3 columns to Red/Amber/Green bands per DNO documentation

### 2.3 Transmission Network Use of System (TNUoS)
| Dataset | Source | Coverage | Format |
|---------|--------|----------|--------|
| Zonal Tariffs | National Grid ESO | 5-year forward | Excel (5-Year Report) |
| Generation Tariffs | National Grid ESO | Annual | PDF/Excel |
| Demand Tariffs | National Grid ESO | Annual | PDF/Excel |

**Files Downloaded:** 146 TNUoS files in `google_drive_data/TNUoS/`

**Methodology:**
- Extract zonal tariffs (£/kW) for 2026/27 - 2030/31
- Parse generation and demand tariff tables
- Create BigQuery table: `tnuos_tariffs`
- Dashboard display: "⚡ TNUoS: £X.XX/kW (Zone Y)"

### 2.4 Balancing Services Use of System (BSUoS)
| Dataset | Source | Update Frequency | Unit |
|---------|--------|------------------|------|
| BSUoS Charges | National Grid ESO | Monthly | £/MWh |
| Historical BSUoS | National Grid ESO | Historical archive | £/MWh |

**Files Downloaded:** 107 BSUoS files in `google_drive_data/BSUoS/`

**Methodology:**
```python
# Ingest BSUoS from Current_II_BSUoS_Data_341.xls
# Parse monthly charge tables
# Dashboard display: Cell A13 - "⚡ BSUoS: £4.52/MWh"
```

### 2.5 Feed-in Tariff (FiT) Levelisation
| Component | Description | Unit | Update Frequency |
|-----------|-------------|------|------------------|
| Consumer Levy | Socialized cost on all electricity consumption | p/kWh | Annual + Quarterly |
| Generation Tariff | Payments to FiT installation owners | p/kWh | Annual (historical) |

**Source:** Ofgem Annual Levelisation Notices + Quarterly Reports

**Files Downloaded:**
- 8 Annual Levelisation Notices (2015-16 to 2022-23) - PDFs
- 37 Quarterly Reports (2015-2025) - Excel
- **Actual Data Extracted:** fit_levelisation_actual_rates_2016_2025.csv

**Methodology (NO ESTIMATES):**
1. Download Official Ofgem Annual Levelisation Notices (PDFs)
2. Extract using PyPDF2:
   - Total FiT Levelisation Fund (£)
   - Total Net Liable Electricity Supply (MWh)
3. Calculate: Rate (p/kWh) = (Fund / Electricity) / 1000 × 100
4. Validate against published Ofgem figures
5. Store in Google Sheet: [FiT Consumer Levy 2016-2025](https://docs.google.com/spreadsheets/d/1Js7TkGJMrevCoSUCQ4AjuAdf4s5oaxh8c9B93VDH6qE)

**Actual Rates Extracted (2016-2025):**
- 2016-17: 0.4621 p/kWh (£13.86/year typical household)
- 2017-18: 0.5436 p/kWh (£16.31/year)
- 2018-19: 0.5302 p/kWh (£15.91/year)
- 2019-20: 0.6040 p/kWh (£18.12/year)
- 2020-21: 0.6743 p/kWh (£20.23/year) ← PEAK
- 2021-22: 0.5330 p/kWh (£15.99/year)
- 2022-23: 0.6268 p/kWh (£18.80/year) ← Latest Annual
- 2025-Q4: 0.5066 p/kWh (£15.20/year) ← Latest Quarterly

### 2.6 Renewables Obligation Certificates (ROC)
| Dataset | Source | Coverage | Format |
|---------|--------|----------|--------|
| Obligation Levels | Ofgem | Annual | PDF/Excel |
| ROC Prices | NFFO | Monthly | Excel |

**Files Downloaded:** 113 ROC files in `google_drive_data/ROC/`

### 2.7 Levy Exemption Certificates (LEC)
| Dataset | Source | Coverage | Format |
|---------|--------|----------|--------|
| LEC Rates | Ofgem | Annual | PDF |
| Eligible Generators | Ofgem | Updated periodically | Excel |

**Files Downloaded:** 57 LEC files in `google_drive_data/LEC/`

---

## 3) DNO License Areas (14 Geographic Regions)

### Complete DNO Reference Table

| MPAN/Distributor ID | DNO_Key | DNO_Name | DNO_Short_Code | Market_Participant_ID | GSP_Group_ID | GSP_Group_Name | Company Group |
|---------------------|---------|----------|----------------|------------------------|--------------|----------------|---------------|
| 10 | UKPN-EPN | UK Power Networks (Eastern) | EPN | EELC | A | Eastern | UK Power Networks |
| 12 | UKPN-LPN | UK Power Networks (London) | LPN | LOND | C | London | UK Power Networks |
| 19 | UKPN-SPN | UK Power Networks (South Eastern) | SPN | SEEB | J | South Eastern | UK Power Networks |
| 11 | NGED-EM | National Grid Electricity Distribution – East Midlands | EMID | EMEB | B | East Midlands | NGED |
| 14 | NGED-WM | National Grid Electricity Distribution – West Midlands | WMID | MIDE | E | West Midlands | NGED |
| 21 | NGED-SWales | National Grid Electricity Distribution – South Wales | SWALES | SWAE | K | South Wales | NGED |
| 22 | NGED-SW | National Grid Electricity Distribution – South West | SWEST | SWEB | L | South Western | NGED |
| 15 | NPg-NE | Northern Powergrid (North East) | NE | NEEB | F | North East | Northern Powergrid |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | Y | YELG | M | Yorkshire | Northern Powergrid |
| 16 | ENWL | Electricity North West | ENWL | NORW | G | North West | Electricity North West |
| 18 | SP-Distribution | SP Energy Networks (SPD) | SPD | SPOW | N | South Scotland | SP Energy Networks |
| 13 | SP-Manweb | SP Energy Networks (SPM) | SPM | MANW | D | Merseyside & North Wales | SP Energy Networks |
| 17 | SSE-SHEPD | Scottish Hydro Electric Power Distribution | SHEPD | HYDE | P | North Scotland | SSEN Distribution |
| 20 | SSE-SEPD | Southern Electric Power Distribution | SEPD | SOUT | H | Southern | SSEN Distribution |

### DNO Groupings

**Group 1: UK Power Networks (3 licenses)**
- EPN (Eastern) - MPAN 10
- LPN (London) - MPAN 12
- SPN (South Eastern) - MPAN 19
- **Data Source:** OpenDataSoft API
- **Portal:** https://ukpowernetworks.opendatasoft.com/

**Group 2: National Grid Electricity Distribution (4 licenses)**
- EMID (East Midlands) - MPAN 11
- WMID (West Midlands) - MPAN 14
- SWALES (South Wales) - MPAN 21
- SWEST (South West) - MPAN 22
- **Data Source:** Charging Statements (Excel/PDF)
- **Portal:** https://commercial.nationalgrid.co.uk/

**Group 3: Northern Powergrid (2 licenses)**
- NE (North East) - MPAN 15
- Y (Yorkshire) - MPAN 23
- **Data Source:** OpenDataSoft API + Charging Statements
- **Portal:** https://northernpowergrid.opendatasoft.com/

**Group 4: Electricity North West (1 license)**
- ENWL (North West) - MPAN 16
- **Data Source:** OpenDataSoft API + Charging Statements
- **Portal:** https://electricitynorthwest.opendatasoft.com/

**Group 5: SP Energy Networks (2 licenses)**
- SPD (South Scotland) - MPAN 18
- SPM (Merseyside & North Wales) - MPAN 13
- **Data Source:** OpenDataSoft API + Charging Statements
- **Portal:** https://spenergynetworks.opendatasoft.com/

**Group 6: SSEN Distribution (2 licenses)**
- SHEPD (North Scotland) - MPAN 17
- SEPD (Southern) - MPAN 20
- **Data Source:** Charging Statements (Excel/PDF)
- **Portal:** https://www.ssen.co.uk/

---

## 4) Data Sources & Methodologies

### 4.1 BMRS (Balancing Mechanism Reporting Service)

**Authority:** National Grid ESO  
**Base URL:** https://api.bmrs.co.uk/BMRS/  
**Authentication:** None (public API)  
**Rate Limits:** Fair use policy

**Key Endpoints:**
```
Market Index Data:  /BMRS/MID/v1
Fuel Mix:           /BMRS/FUELINST/v1
Generation:         /BMRS/B1610/v1
System Demand:      /BMRS/B0610/v1
Wind Forecast:      /BMRS/B1440/v1
```

**Ingestion Method:**
```python
# dashboard_updater_complete.py (lines 200-250)
def update_bmrs_data():
    """Update all BMRS datasets every 5 minutes"""
    # 1. Fetch MID prices (N2EX, EPEX SPOT)
    # 2. Fetch fuel mix (FUELINST)
    # 3. Fetch wind/solar generation
    # 4. Store to BigQuery
    # 5. Update dashboard cells
```

**Update Schedule:** Cron job every 5 minutes

### 4.2 Elexon Insights API

**Authority:** Elexon (Electricity Market Reform Delivery Body)  
**Base URL:** https://insights.elexon.co.uk/api/  
**Authentication:** API Key required  
**Rate Limits:** 100 requests/minute

**Datasets Available:** 635+ datasets discovered  
**Manifest Files:**
- `insights_manifest_comprehensive.json` - Full catalog
- `insights_endpoints.with_units.yml` - Endpoints with units metadata

**Discovery Method:**
```python
# discover_all_datasets_dynamic.py
def discover_elexon_datasets():
    """Dynamic discovery of all Elexon Insights datasets"""
    # 1. Enumerate all dataset IDs
    # 2. Fetch metadata for each
    # 3. Extract units, descriptions, update frequencies
    # 4. Save to JSON manifest
```

### 4.3 OpenDataSoft DNO Portals

**DNOs with ODS Portals:**
1. UK Power Networks (EPN/LPN/SPN)
2. Northern Powergrid (NE/Y)
3. Electricity North West (ENWL)
4. SP Energy Networks (SPD/SPM)

**Generic API Pattern:**
```http
GET https://{DNO}.opendatasoft.com/api/records/1.0/search/
  ?dataset={DATASET_ID}
  &rows=1000
  &refine.{field}={value}
```

**Example - UKPN DUoS Annex 1:**
```python
import requests

url = "https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/"
params = {
    "dataset": "ukpn-distribution-use-of-system-charges-annex-1",
    "rows": 1000,
    "refine.licence": "LPN",
    "refine.charging_year": "2024/25"
}
response = requests.get(url, params=params)
data = response.json()
```

### 4.4 Charging Statement Downloads (NGED, SSEN)

**NGED (4 licenses):**
- **URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-statements-archive
- **Format:** Excel (.xlsx) + PDF
- **Structure:**
  - Annex 1: Time-of-Use Periods (Red/Amber/Green)
  - Table XX: HH Unit Rates (p/kWh)
  - Mapping: UR1=Red, UR2=Amber, UR3=Green (varies by license)

**SSEN Distribution (2 licenses):**
- **SHEPD URL:** https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/scottish-hydro-electric-power-distribution/
- **SEPD URL:** https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/southern-electric-power-distribution/
- **Format:** Excel (.xlsx) + PDF
- **Years Available:** 2016-present

**Parsing Method:**
```python
# parse_charging_statement.py
def extract_duos_data(xlsx_path, license_area):
    """Extract DUoS bands and rates from charging statement"""
    # 1. Load Excel file
    xl = pd.ExcelFile(xlsx_path)
    
    # 2. Find Annex 1 sheet (time bands)
    annex_df = find_annex_sheet(xl)
    time_bands = parse_time_bands(annex_df)
    
    # 3. Find HH unit rate table
    rates_df = find_unit_rate_table(xl)
    unit_rates = parse_unit_rates(rates_df, license_area)
    
    # 4. Merge bands + rates
    return merge_duos_data(time_bands, unit_rates)
```

### 4.5 Ofgem Publications (FiT, ROC, LEC)

**FiT (Feed-in Tariff) Levelisation:**
- **Annual Notices:** PDF documents with fund totals and electricity supply
- **Quarterly Reports:** Excel files with payment data
- **Extraction Method:** PyPDF2 text parsing with regex patterns
- **Validation:** Cross-check calculated rates against published summary tables

**Example Extraction:**
```python
# extract_fit_levelisation.py
import PyPDF2, re

def extract_fit_rates(pdf_path):
    """Extract FiT consumer levy from Annual Levelisation Notice"""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = " ".join([page.extract_text() for page in reader.pages])
    
    # Find total fund and electricity supply
    fund_match = re.search(r'Total.*Fund.*£([0-9,\.]+)', text)
    elec_match = re.search(r'Total.*Electricity.*([0-9,\.]+).*MWh', text)
    
    fund = float(fund_match.group(1).replace(',', ''))
    electricity = float(elec_match.group(1).replace(',', ''))
    
    # Calculate rate: p/kWh = (£Fund / MWh) / 1000 * 100
    rate_p_per_kwh = (fund / electricity) / 1000 * 100
    
    return rate_p_per_kwh
```

**ROC & LEC:**
- Similar download + parse methodology
- Sources: Ofgem website + official publications
- Storage: `google_drive_data/ROC/` and `google_drive_data/LEC/`

---

## 5) API Endpoints

### 5.1 BMRS API Endpoints

| Endpoint | Description | Update Freq | Parameters |
|----------|-------------|-------------|------------|
| `/BMRS/MID/v1` | Market Index Data (wholesale prices) | 5 min | ServiceType=xml |
| `/BMRS/FUELINST/v1` | Fuel Mix | 5 min | ServiceType=xml |
| `/BMRS/B1610/v1` | Actual Generation by Fuel Type | 30 min | SettlementDate, Period |
| `/BMRS/B0610/v1` | System Demand | 30 min | SettlementDate |
| `/BMRS/B1440/v1` | Wind & Solar Forecasts | Daily | SettlementDate |

### 5.2 Elexon Insights API

**Base:** `https://insights.elexon.co.uk/api/`

**Dataset Discovery:**
```
GET /datasets
GET /datasets/{dataset_id}
GET /datasets/{dataset_id}/stream
```

**Example Datasets:**
- `generation-mix` - Historical generation by fuel type
- `demand-outturn` - Actual system demand
- `system-prices` - System Buy/Sell Prices
- `wind-availability` - Wind generation availability

### 5.3 OpenDataSoft DNO APIs

**UK Power Networks:**
```
Base: https://ukpowernetworks.opendatasoft.com/api/records/1.0/

Datasets:
- ukpn-distribution-use-of-system-charges-annex-1
- ukpn-future-energy-scenarios
- ukpn-network-capacity-map
```

**Northern Powergrid:**
```
Base: https://northernpowergrid.opendatasoft.com/api/records/1.0/

Datasets:
- charging-statements
- network-information
```

**Electricity North West:**
```
Base: https://electricitynorthwest.opendatasoft.com/api/records/1.0/

Datasets:
- use-of-system-charges
- flexibility-services
```

**SP Energy Networks:**
```
Base: https://spenergynetworks.opendatasoft.com/api/records/1.0/

Datasets:
- distribution-charges
- network-data
```

---

## 6) File Structure

```
GB Power Market JJ/
│
├── docs/
│   ├── CLAUDE_energy_data.md           # This file
│   ├── CLAUDE_duos.md                  # DUoS-specific documentation
│   ├── API_RESEARCH_FINDINGS.md        # API discovery notes
│   └── AUTHENTICATION_FIX.md           # Auth troubleshooting
│
├── data/
│   ├── raw/                            # Downloaded files (not in git)
│   │   ├── google_drive_data/
│   │   │   ├── TNUoS/                  # 146 files
│   │   │   ├── BSUoS/                  # 107 files
│   │   │   ├── DUoS/                   # 107 files
│   │   │   ├── FiT/                    # 105 files
│   │   │   ├── ROC/                    # 113 files
│   │   │   └── LEC/                    # 57 files
│   │   ├── fit_annual_notices/         # 8 PDFs (2015-16 to 2022-23)
│   │   └── fit_levelisation_data/      # 37 quarterly Excel files
│   │
│   ├── processed/
│   │   ├── duos_rates_times.csv        # Normalized DUoS data (all DNOs)
│   │   ├── fit_levelisation_actual_rates_2016_2025.csv
│   │   └── tnuos_tariffs.csv
│   │
│   └── manifests/
│       ├── insights_manifest_comprehensive.json
│       ├── insights_endpoints.with_units.yml
│       └── dataset_special_configs.json
│
├── src/
│   ├── ingest/
│   │   ├── bmrs_ingestion.py
│   │   ├── elexon_ingestion.py
│   │   ├── duos_ingestion.py
│   │   └── fit_ingestion.py
│   │
│   ├── parsers/
│   │   ├── excel_parser.py
│   │   ├── pdf_parser.py
│   │   └── xml_parser.py
│   │
│   ├── normalize/
│   │   ├── schema_mapper.py
│   │   └── data_validator.py
│   │
│   └── dashboard/
│       └── dashboard_updater_complete.py
│
├── bigquery/
│   ├── schemas/
│   │   ├── bmrs_mid.json
│   │   ├── bmrs_fuelinst.json
│   │   └── duos_rates.json
│   │
│   └── queries/
│       ├── daily_aggregates.sql
│       └── monthly_reports.sql
│
├── google_sheets/
│   ├── Dashboard: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
│   └── FiT Consumer Levy: 1Js7TkGJMrevCoSUCQ4AjuAdf4s5oaxh8c9B93VDH6qE
│
├── credentials/
│   ├── jibber_jabber_key.json          # Service account (dashboard updates)
│   ├── credentials.json                # OAuth client (Drive/Sheets)
│   └── token.pickle                    # OAuth token (with Sheets scope)
│
├── config/
│   ├── dno_licenses.json               # 14 DNO license area configs
│   ├── api_endpoints.json              # All API endpoint configurations
│   └── update_schedules.json           # Cron schedules per dataset
│
└── scripts/
    ├── download_all_duos.py            # Download DUoS for all 14 DNOs
    ├── oauth_with_sheets.py            # OAuth re-authorization tool
    └── validate_data_completeness.py   # Data quality checks
```

---

## 7) Ingestion Pipelines

### 7.1 Real-Time BMRS Pipeline (5-minute updates)

**Script:** `dashboard_updater_complete.py`  
**Trigger:** Cron (*/5 * * * *)  
**Process:**
1. Fetch MID prices from BMRS API
2. Extract N2EX and EPEX SPOT values
3. Fetch fuel mix (FUELINST)
4. Fetch wind/solar generation
5. Store to BigQuery tables
6. Update Google Sheets dashboard (31 cells)

**Service Account:** `jibber_jabber_key.json`  
**Scopes:** `spreadsheets`, `drive`

### 7.2 DUoS Data Pipeline (Annual updates)

**Script:** `download_all_duos.py`  
**Trigger:** Manual (October-March charging season)  
**Process:**

```python
# Pseudo-code for DUoS pipeline
for dno in [EPN, LPN, SPN, NE, Y, ENWL, SPD, SPM, EMID, WMID, SWALES, SWEST, SHEPD, SEPD]:
    if dno in [EPN, LPN, SPN, NE, Y, ENWL, SPD, SPM]:
        # OpenDataSoft API route
        data = fetch_ods_data(dno)
    else:
        # Charging statement download route
        files = download_charging_statements(dno, years=[2016..2025])
        data = parse_excel_files(files)
    
    # Normalize to common schema
    normalized = normalize_duos_schema(data, dno)
    
    # Validate
    validate_duos_completeness(normalized)
    
    # Append to master CSV
    append_to_csv('duos_rates_times.csv', normalized)
```

**Output:** `data/processed/duos_rates_times.csv`  
**Schema:** See Section 2.2

### 7.3 FiT Levelisation Pipeline (Annual + Quarterly)

**Script:** `extract_fit_levelisation.py`  
**Trigger:** Manual (when new Ofgem notices published)  
**Process:**
1. Download Annual Levelisation Notices (PDFs) from Ofgem
2. Parse PDFs using PyPDF2
3. Extract fund totals and electricity supply values
4. Calculate consumer levy rates (p/kWh)
5. Download quarterly reports (Excel)
6. Extract quarterly rates where available
7. Create CSV with actual rates
8. Update Google Sheet with OAuth

**Output:** 
- CSV: `fit_levelisation_actual_rates_2016_2025.csv`
- Google Sheet: https://docs.google.com/spreadsheets/d/1Js7TkGJMrevCoSUCQ4AjuAdf4s5oaxh8c9B93VDH6qE

**Critical:** NO ESTIMATES - all data from official Ofgem publications

### 7.4 Elexon Insights Discovery Pipeline

**Script:** `discover_all_datasets_dynamic.py`  
**Trigger:** Monthly (dataset catalog changes)  
**Process:**
1. Enumerate all dataset IDs via API
2. Fetch metadata for each dataset
3. Extract units, descriptions, update frequencies
4. Generate manifest files
5. Store to `insights_manifest_comprehensive.json`

**Result:** 635+ datasets cataloged

---

## 8) Data Quality & Validation

### 8.1 Validation Rules

**BMRS Data:**
- [ ] MID prices: N2EX and EPEX SPOT should be ≥ £0/MWh and ≤ £500/MWh
- [ ] Fuel mix: Sum of all fuel types should equal ~100% (tolerance ±5%)
- [ ] Generation: Wind + Solar values should match BMRS totals
- [ ] Timestamps: All data timestamped in UTC

**DUoS Data:**
- [ ] Time coverage: Red + Amber + Green should cover full 24-hour day
- [ ] Band consistency: Weekday vs weekend bands should be documented
- [ ] Rate reasonableness: Unit rates typically 1-30 p/kWh for LV
- [ ] Year completeness: All 14 DNOs should have data for each year 2016-present

**FiT Data:**
- [ ] Source verification: All rates must have Ofgem Annual Notice reference
- [ ] Calculation check: Rate = (Fund / Electricity) / 1000 × 100
- [ ] Trend validation: Rates should generally increase 2016-2021, then stabilize
- [ ] NO ESTIMATES: Flag any synthetic or estimated values

### 8.2 Data Completeness Checks

```python
# validate_data_completeness.py
def validate_duos_coverage():
    """Check DUoS data completeness across all DNOs and years"""
    dnos = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    years = range(2016, 2026)
    
    for dno in dnos:
        for year in years:
            data = load_duos_data(dno, year)
            assert len(data) > 0, f"Missing {dno} {year}"
            assert validate_24h_coverage(data), f"Incomplete bands {dno} {year}"
            assert validate_rates(data), f"Invalid rates {dno} {year}"

def validate_fit_coverage():
    """Check FiT data has no gaps"""
    data = load_fit_data()
    years = [row['Year'] for row in data]
    
    # Should have continuous coverage 2016-17 onwards
    assert '2016-17' in years
    assert all(row['Source'].startswith('Ofgem') for row in data)
    assert all(row['Rate'] != 'ESTIMATED' for row in data)
```

### 8.3 Anomaly Detection

**Statistical Checks:**
- Detect outliers using IQR method (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
- Flag sudden rate changes > 50% year-over-year
- Monitor API response times and failure rates

**Manual Review Triggers:**
- New DNO charging statement formats
- Ofgem policy changes (e.g., TCR reforms)
- API endpoint changes or deprecations

---

## 9) Update Schedules

| Dataset | Frequency | Trigger | Last Updated |
|---------|-----------|---------|--------------|
| BMRS MID Prices | Every 5 min | Cron: */5 * * * * | 2025-10-29 (ongoing) |
| BMRS Fuel Mix | Every 5 min | Cron: */5 * * * * | 2025-10-29 (ongoing) |
| DUoS Rates (ODS) | Daily | Cron: 0 2 * * * | Pending |
| DUoS Rates (Files) | Annual | Manual (Oct-Mar) | Pending |
| FiT Annual Notices | Annual | Manual (Ofgem publish) | 2025-10-29 |
| FiT Quarterly | Quarterly | Manual | 2025-10-29 (Q4) |
| TNUoS Tariffs | Annual | Manual | Pending |
| BSUoS Charges | Monthly | Manual | Pending |
| Elexon Discovery | Monthly | Cron: 0 3 1 * * | Pending |

**Charging Year Cycle:**
- UK charging year: April 1 - March 31
- New statements published: October-December (for following April)
- Historical data: Available 6-12 months after year-end

---

## 10) Authentication & Access

### 10.1 Google Service Account

**File:** `jibber_jabber_key.json`  
**Email:** all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com  
**Scopes:**
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive`

**Usage:** Dashboard updates (read/write existing files)  
**Limitation:** 15GB storage quota (exceeded) - cannot create new files

**Working Example:**
```python
from google.oauth2.service_account import Credentials
import gspread

SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(DASHBOARD_SHEET_ID)
```

### 10.2 Google OAuth (User Account)

**File:** `credentials.json` (client secrets), `token.pickle` (access token)  
**Email:** george@upowerenergy.co.uk  
**Scopes:**
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/drive.file`
- `https://www.googleapis.com/auth/spreadsheets`

**Storage:** 7TB+ available  
**Usage:** Creating new files, downloading from Drive, creating new Sheets

**Re-authorization:**
```bash
# Run when token expires or scopes change
python oauth_with_sheets.py
# Opens browser for authorization
# Saves new token.pickle with updated scopes
```

**Working Example:**
```python
import pickle
import gspread

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

gc = gspread.authorize(creds)
sh = gc.create("New Spreadsheet")  # Uses personal Drive (7TB)
```

### 10.3 BigQuery

**Project:** inner-cinema-476211-u9  
**Dataset:** uk_energy_prod  
**Location:** EU (europe-west2)

**Tables:**
- `bmrs_mid` - Market Index Data
- `bmrs_fuelinst` - Fuel Mix
- `bmrs_wind_solar_gen` - Renewable Generation
- `duos_rates` (planned) - All DNO DUoS rates

**Authentication:** Service account (`jibber_jabber_key.json`)

**Connection:**
```python
from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')
query = """
    SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
"""
df = client.query(query).to_dataframe()
```

### 10.4 API Keys (if needed)

**Elexon Insights API:**
- Currently using public endpoints (no key required)
- If rate limits encountered, apply for API key at https://insights.elexon.co.uk/

**BMRS API:**
- Public access (no key required)
- Fair use policy applies

---

## 11) Known Issues & Limitations

### 11.1 Data Gaps

**FiT Consumer Levy:**
- ❌ 2010-2015: Not yet extracted (scheme started April 2010)
- ❌ 2023-24: Ofgem Annual Notice not yet published
- ⏳ 2024-25: Year in progress (ends March 2025)

**DUoS Rates:**
- ⏳ All 14 DNOs: Download in progress (see Section 12)
- ⚠️ Historical pre-2016: Some DNOs have limited availability

**BSUoS & TNUoS:**
- 📥 Downloaded but not yet parsed/ingested
- 🔄 Pipeline development required

### 11.2 Authentication Issues

**Service Account Storage:**
- Service account Drive quota exceeded (15GB typical limit)
- Cannot create new files
- Solution: Use OAuth for new file creation

**OAuth Token Expiry:**
- Tokens expire after 7 days of inactivity
- Re-authorization required periodically
- Solution: Run `oauth_with_sheets.py` when needed

### 11.3 API Rate Limits

**OpenDataSoft:**
- Limit: 10,000 requests/day per IP
- Mitigation: Cache responses, batch requests

**Elexon Insights:**
- Limit: 100 requests/minute
- Mitigation: Rate limiting in code

### 11.4 Data Format Changes

**Charging Statements:**
- DNOs periodically change Excel layouts
- Annex numbers may shift between years
- Requires manual parser updates

**ODS Field Names:**
- Field names may change between years
- Maintain mapping files per dataset/year

---

## 12) Next Actions

### Priority 1: Complete DUoS Data Collection (ALL 14 DNOs)

**Status:** IN PROGRESS  
**Script:** Creating `download_all_duos.py`  
**Target:** Download and parse DUoS data for all 14 license areas, 2016-present

**Breakdown by DNO Group:**

1. ✅ **UK Power Networks (EPN/LPN/SPN)** - ODS API available
2. ⏳ **Northern Powergrid (NE/Y)** - ODS API + Charging Statements
3. ⏳ **ENWL (ENWL)** - ODS API + Charging Statements
4. ⏳ **SP Energy Networks (SPD/SPM)** - ODS API + Charging Statements
5. ⏳ **NGED (EMID/WMID/SWALES/SWEST)** - Charging Statements only
6. ⏳ **SSEN (SHEPD/SEPD)** - Charging Statements only

### Priority 2: Parse Downloaded Charges Data

**BSUoS (107 files):**
- Extract monthly charges (£/MWh)
- Create time series 2016-present
- Add to dashboard Cell A13

**TNUoS (146 files):**
- Parse 5-year tariff tables
- Extract zonal tariffs by GSP Group
- Create BigQuery table

**ROC & LEC (170 files total):**
- Extract obligation levels
- Parse certificate prices
- Create historical datasets

### Priority 3: Automate Update Pipelines

**Cron Jobs to Create:**
- DUoS ODS daily refresh
- Elexon dataset discovery (monthly)
- Quarterly FiT report check (quarterly)
- Annual charging statement check (October-December)

### Priority 4: Dashboard Enhancements

**New Cells:**
- A12: BSUoS (£/MWh)
- A13: TNUoS (£/kW or zone)
- A14: DUoS band (Red/Amber/Green based on current time)
- A15: FiT levelisation (p/kWh) - use latest quarterly rate
- A16: ROC obligation (£/MWh)
- A17: Total system cost (aggregate all charges)

**Visualization:**
- Add chart: Historical FiT rates (2016-2025)
- Add chart: DUoS band schedule (current day)
- Add chart: Fuel mix pie chart (real-time)

---

## 13) References & Links

### Official Data Sources

**National Grid ESO:**
- BMRS Portal: https://www.bmreports.com/
- API Documentation: https://api.bmrs.co.uk/
- TNUoS Statements: https://www.nationalgrideso.com/industry-information/charging/transmission-network-use-system-tnuos-charges

**Elexon:**
- Insights Portal: https://insights.elexon.co.uk/
- API Documentation: https://insights.elexon.co.uk/api-documentation
- Settlement Data: https://www.elexon.co.uk/data/

**Ofgem:**
- FiT Levelisation: https://www.ofgem.gov.uk/environmental-and-social-schemes/feed-tariffs-fit/feed-tariff-levelisation-process
- ROC Information: https://www.ofgem.gov.uk/environmental-and-social-schemes/renewables-obligation-ro
- Charging Reforms: https://www.ofgem.gov.uk/electricity/transmission-networks/charging-and-network-access

**DNO Portals:**
- UK Power Networks: https://ukpowernetworks.opendatasoft.com/
- NGED: https://commercial.nationalgrid.co.uk/
- Northern Powergrid: https://www.northernpowergrid.com/
- ENWL: https://www.enwl.co.uk/
- SP Energy Networks: https://www.spenergynetworks.co.uk/
- SSEN Distribution: https://www.ssen.co.uk/

### Google Resources

**Dashboard:**
- Main Dashboard: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
- FiT Consumer Levy Sheet: https://docs.google.com/spreadsheets/d/1Js7TkGJMrevCoSUCQ4AjuAdf4s5oaxh8c9B93VDH6qE

**BigQuery:**
- Project: inner-cinema-476211-u9
- Dataset: uk_energy_prod
- Console: https://console.cloud.google.com/bigquery

### Repository

**GitHub:**
- Repo: jibber-jabber-24-august-2025-big-bop
- Owner: GeorgeDoors888
- Branch: main

---

## 14) Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-10-29 | Initial comprehensive documentation created | AI Assistant |
| 2025-10-29 | FiT actual data extraction completed (2016-2025) | AI Assistant |
| 2025-10-29 | OAuth re-authorized with Sheets scope | AI Assistant |
| 2025-10-29 | FiT Google Sheet created successfully | AI Assistant |
| 2025-10-29 | Started DUoS download for all 14 DNO areas | In Progress |

---

**Document Version:** 1.0  
**Status:** Living Document (update as data sources and methodologies evolve)  
**Maintained By:** GB Power Market JJ Project Team
