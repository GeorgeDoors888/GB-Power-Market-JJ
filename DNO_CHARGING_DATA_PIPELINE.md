# DNO Charging Data Pipeline - Complete Implementation Plan

**Generated:** 2025-10-30  
**Status:** Planning Phase  
**Objective:** Create automated pipeline to ingest, structure, and query DUoS charging data for all 14 GB DNO license areas

---

## 1. Overview

This pipeline will:
1. **Extract** charging data from 195+ PDF/Excel files (currently in Google Drive backup)
2. **Transform** into structured format with consistent schema across all DNOs
3. **Load** into BigQuery for analysis and querying
4. **Publish** to Google Sheets for business user access
5. **Map** to geographic boundaries (GeoJSON) for spatial analysis

---

## 2. DNO License Areas (14 Areas)

| MPAN ID | DNO Key | DNO Name | Short Code | GSP Group | GSP Name | Files Available |
|---------|---------|----------|------------|-----------|----------|-----------------|
| 12 | UKPN-LPN | UK Power Networks (London) | LPN | C | London | ✅ Via API |
| 10 | UKPN-EPN | UK Power Networks (Eastern) | EPN | A | Eastern | ✅ Via API |
| 19 | UKPN-SPN | UK Power Networks (South Eastern) | SPN | J | South Eastern | ✅ Via API |
| 16 | ENWL | Electricity North West | ENWL | G | North West | ⚠️ Limited API |
| 15 | NPg-NE | Northern Powergrid (North East) | NE | F | North East | ✅ Via API |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | Y | M | Yorkshire | ✅ Via API |
| 18 | SP-Distribution | SP Energy Networks (SPD) | SPD | N | South Scotland | ❌ No API |
| 13 | SP-Manweb | SP Energy Networks (SPM) | SPM | D | Merseyside & N Wales | ❌ No API |
| 17 | SSE-SHEPD | Scottish Hydro Electric (SHEPD) | SHEPD | P | North Scotland | ❌ No API |
| 20 | SSE-SEPD | Southern Electric (SEPD) | SEPD | H | Southern | ❌ No API |
| 14 | NGED-WM | National Grid ED – West Midlands | WMID | E | West Midlands | ✅ **195 files** |
| 11 | NGED-EM | National Grid ED – East Midlands | EMID | B | East Midlands | ✅ **195 files** |
| 22 | NGED-SW | National Grid ED – South West | SWEST | L | South Western | ✅ **195 files** |
| 21 | NGED-SWales | National Grid ED – South Wales | SWALES | K | South Wales | ✅ **195 files** |

**Current Status:**
- ✅ **NGED (4 areas):** 195 charging files (2010-2026) backed up in Google Drive
- ✅ **UKPN (3 areas):** 9 datasets available via OpenDataSoft API
- ✅ **NPg (2 areas):** 2 datasets available via OpenDataSoft API
- ⚠️ **ENWL (1 area):** Limited API access
- ❌ **SPEN (2 areas):** No public API, manual download required
- ❌ **SSEN (2 areas):** No distribution portal, manual download required

---

## 3. Data Structure

### 3.1 DUoS Charging Components

DNO charges consist of several components:

1. **Unit Rates (p/kWh)** - Energy consumption charges
   - Time-banded (Red/Amber/Green periods)
   - Voltage level dependent (LV/HV/EHV)
   - Customer category (Domestic/Non-Domestic)

2. **Capacity Charges (p/kVA/day)** - Maximum demand charges
   - Based on agreed or measured capacity
   - Voltage level dependent

3. **Fixed Charges (p/day)** - Standing charges
   - Per MPAN per day
   - Independent of consumption

4. **Residual/Reactive Charges** - Additional components
   - Residual charges (spreading non-time-of-use costs)
   - Reactive power charges (power factor penalties)
   - Excess capacity charges

### 3.2 Tariff Code Structure

Example NGED tariff code: `EMEB-LV-UMS-1-R`

Components:
- `EMEB` = License area (East Midlands)
- `LV` = Voltage level (Low Voltage)
- `UMS` = Metering type (Unmetered Supply)
- `1` = Time band profile (1-8)
- `R` = Rate type (R=Red, A=Amber, G=Green)

Other DNOs use different structures:
- UKPN: `LPN-HH-UMS1-R` (HH = Half-Hourly metered)
- SSEN: `SEPD-DOMESTIC-TWO-RATE`
- NPg: `NEEB-LV-PROFILE-CLASS-1`

### 3.3 Time Bands

**Red Period** (Peak)
- Winter: 16:00-19:00 weekdays (Nov-Feb)
- Summer: Usually not applicable
- Highest unit rates

**Amber Period** (Shoulder)
- 07:00-16:00 and 19:00-23:00 weekdays
- Medium unit rates

**Green Period** (Off-Peak)
- 00:00-07:00 and 23:00-00:00 weekdays
- All weekend hours
- Lowest unit rates

**Note:** Some DNOs use different time band definitions or flat rates

---

## 4. BigQuery Schema Design

### 4.1 Core Tables

#### Table: `dno_license_areas`
```sql
CREATE TABLE gb_power.dno_license_areas (
  mpan_id INT64 NOT NULL,
  dno_key STRING NOT NULL,
  dno_name STRING NOT NULL,
  short_code STRING NOT NULL,
  market_participant_id STRING NOT NULL,
  gsp_group_id STRING NOT NULL,
  gsp_group_name STRING NOT NULL,
  dno_group STRING NOT NULL,  -- UKPN, NGED, SSEN, SPEN, NPg, ENWL
  website STRING,
  data_portal STRING,
  boundary GEOGRAPHY,  -- License area polygon
  effective_from DATE,
  effective_to DATE
)
PARTITION BY DATE_TRUNC(effective_from, YEAR);
```

#### Table: `duos_tariff_definitions`
```sql
CREATE TABLE gb_power.duos_tariff_definitions (
  tariff_id STRING NOT NULL,  -- Unique identifier
  dno_key STRING NOT NULL,    -- Foreign key to dno_license_areas
  tariff_code STRING NOT NULL,
  tariff_name STRING,
  tariff_description STRING,
  voltage_level STRING NOT NULL,  -- LV, HV, EHV, UHV
  customer_category STRING NOT NULL,  -- DOMESTIC, NON_DOMESTIC, GENERATION
  metering_type STRING,  -- HH (Half-Hourly), NHH (Non-Half-Hourly), UMS
  profile_class INT64,   -- 1-8 for NHH customers
  time_pattern STRING,   -- FLAT, TWO_RATE, THREE_RATE, etc.
  effective_from DATE NOT NULL,
  effective_to DATE,
  source_document STRING,
  source_document_url STRING,
  extracted_date DATE
)
PARTITION BY DATE_TRUNC(effective_from, YEAR);
```

#### Table: `duos_unit_rates`
```sql
CREATE TABLE gb_power.duos_unit_rates (
  rate_id STRING NOT NULL,  -- Unique identifier
  tariff_id STRING NOT NULL,  -- Foreign key to duos_tariff_definitions
  dno_key STRING NOT NULL,
  tariff_code STRING NOT NULL,
  rate_component STRING NOT NULL,  -- ENERGY, CAPACITY, FIXED, REACTIVE, RESIDUAL
  time_band STRING,  -- RED, AMBER, GREEN, FLAT, SUPER_RED
  unit_rate FLOAT64 NOT NULL,  -- In pence
  unit STRING NOT NULL,  -- p/kWh, p/kVA/day, p/day, p/kVArh
  effective_from DATE NOT NULL,
  effective_to DATE,
  year INT64 NOT NULL,  -- For easy querying
  season STRING,  -- WINTER, SUMMER, YEAR_ROUND
  day_type STRING  -- WEEKDAY, WEEKEND, ALL
)
PARTITION BY DATE_TRUNC(effective_from, YEAR)
CLUSTER BY dno_key, tariff_code, time_band;
```

#### Table: `duos_time_bands`
```sql
CREATE TABLE gb_power.duos_time_bands (
  time_band_id STRING NOT NULL,
  dno_key STRING NOT NULL,
  time_band STRING NOT NULL,  -- RED, AMBER, GREEN
  season STRING,  -- WINTER, SUMMER, YEAR_ROUND
  day_type STRING NOT NULL,  -- WEEKDAY, WEEKEND
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  start_month INT64,  -- 1-12
  end_month INT64,
  effective_from DATE NOT NULL,
  effective_to DATE
);
```

### 4.2 Spatial Tables

#### Table: `dno_boundaries`
```sql
CREATE TABLE gb_power.dno_boundaries (
  dno_key STRING NOT NULL,
  boundary_name STRING,
  boundary_type STRING,  -- LICENSE_AREA, GSP_GROUP, SERVICE_AREA
  geometry GEOGRAPHY NOT NULL,
  area_km2 FLOAT64,
  population_served INT64,
  source STRING,
  source_date DATE
);
```

#### Table: `gsp_boundaries`
```sql
CREATE TABLE gb_power.gsp_boundaries (
  gsp_id STRING NOT NULL,
  gsp_name STRING NOT NULL,
  gsp_group_id STRING NOT NULL,
  dno_key STRING NOT NULL,
  geometry GEOGRAPHY NOT NULL,
  area_km2 FLOAT64,
  source STRING
);
```

#### Table: `substations`
```sql
CREATE TABLE gb_power.substations (
  substation_id STRING NOT NULL,
  substation_name STRING,
  dno_key STRING NOT NULL,
  voltage_level STRING,
  location GEOGRAPHY NOT NULL,
  capacity_mva FLOAT64,
  commissioning_date DATE,
  source STRING
);
```

### 4.3 Supporting Tables

#### Table: `voltage_levels`
```sql
CREATE TABLE gb_power.voltage_levels (
  voltage_code STRING NOT NULL,
  voltage_name STRING NOT NULL,
  voltage_kv_min FLOAT64,
  voltage_kv_max FLOAT64,
  typical_customers STRING
);

-- Data:
-- LV: Low Voltage, 0.230-0.400 kV, Domestic and small commercial
-- HV: High Voltage, 6.6-33 kV, Large commercial and industrial
-- EHV: Extra High Voltage, 66-132 kV, Very large industrial
-- UHV: Ultra High Voltage, 275-400 kV, Transmission level
```

#### Table: `customer_categories`
```sql
CREATE TABLE gb_power.customer_categories (
  category_code STRING NOT NULL,
  category_name STRING NOT NULL,
  category_description STRING,
  typical_consumption_kwh_year INT64
);

-- Data:
-- DOMESTIC: Residential customers
-- SME: Small/Medium Enterprises
-- LARGE_COMMERCIAL: Large commercial customers
-- INDUSTRIAL: Industrial customers
-- GENERATION: Embedded generators
-- UMS: Unmetered Supply (street lighting, traffic signals)
```

---

## 5. Data Extraction Strategy

### 5.1 NGED Files (195 Files, 2010-2026)

**File Types:**
1. DUoS Charge Schedules (Excel) - Main tariff tables
2. LC14 Statements (PDF) - Methodology and tariff structure
3. Use of System Charging Statements (PDF) - Annual summaries
4. ED2 PCFM Models (Excel) - Price control financial models
5. Addendums and Annexes (PDF/Excel) - Updates and corrections

**Extraction Approach:**

**Excel Files:**
- Use `openpyxl` or `pandas` to read worksheets
- Identify tariff tables by headers: "Tariff Code", "p/kWh", "p/kVA/day"
- Extract effective dates from worksheet names or cell values
- Parse license area from filename (SWEB, SWAE, MIDE, EMEB)

**PDF Files:**
- Use `pdfplumber` to extract tables
- OCR if necessary with `pytesseract`
- Regex patterns to identify tariff codes and rates
- Manual validation for complex layouts

**Year Detection:**
- Filename: "2024-25", "April 2025", "FY2024"
- Document content: "Effective from 1 April 2024"
- Use financial year convention (April-March)

### 5.2 UKPN/NPg OpenDataSoft Datasets

**API Approach:**
- Use existing `fetch_dno_datasets.py` script
- Download CSV datasets
- Parse with `pandas`
- Map to BigQuery schema

### 5.3 SPEN/SSEN Manual Collection

**Website Scraping:**
- Use `requests` + `BeautifulSoup`
- Download PDFs/Excel from charging pages
- Follow same extraction process as NGED

---

## 6. Google Sheets Structure

### 6.1 Master Tariff Lookup Sheet

**Sheet 1: Tariff Rates (Dynamic)**
```
Columns:
A: Year (2010-2030)
B: DNO License Area (dropdown: 14 areas)
C: Voltage Level (dropdown: LV/HV/EHV/UHV)
D: Customer Category (dropdown: Domestic/Commercial/Industrial/etc)
E: Tariff Code
F: Tariff Name
G: Red Rate (p/kWh)
H: Amber Rate (p/kWh)
I: Green Rate (p/kWh)
J: Capacity Charge (p/kVA/day)
K: Fixed Charge (p/day)
L: Effective From
M: Effective To
N: Source Document
```

**Formulas:**
```javascript
// Filter by year
=QUERY(ImportRange("bigquery_link"), 
  "SELECT * WHERE Year = "&A2&" AND DNO_Key = '"&B2&"'")

// Search by tariff code
=FILTER(ImportRange(...), SEARCH(E2, TariffCode) > 0)

// Calculate annual cost
=G2*RedKWh + H2*AmberKWh + I2*GreenKWh + J2*365*Capacity + K2*365
```

### 6.2 Year-by-Year Comparison Sheet

**Sheet 2: Rate Evolution**
```
Columns:
A: Tariff Code
B-M: Years 2010-2021
N-Y: Years 2022-2033

Rows show rate changes over time for each tariff
Conditional formatting highlights increases/decreases
```

### 6.3 Voltage Level Comparison

**Sheet 3: LV vs HV vs EHV**
```
Compare same tariff across voltage levels
Show percentage difference
Identify cost-optimization opportunities
```

---

## 7. GeoJSON Integration

### 7.1 Required Spatial Data

**Priority 1 - DNO License Areas:**
- 14 polygon boundaries defining service territories
- Sources: Ofgem, DNO websites, NESO data portal
- Format: GeoJSON FeatureCollection with properties (dno_key, name)

**Priority 2 - GSP Group Boundaries:**
- 14 Grid Supply Point regions
- Matches license areas but important for transmission context
- Sources: NESO, Elexon

**Priority 3 - Primary Substations:**
- ~1,000-2,000 substation locations across GB
- Point geometries with properties (voltage, capacity)
- Sources: DNO asset registers, OpenDataSoft portals

### 7.2 Spatial Queries

**Find DNO by Location:**
```sql
SELECT la.dno_key, la.dno_name
FROM gb_power.dno_license_areas la
WHERE ST_CONTAINS(la.boundary, ST_GEOGPOINT(-0.1278, 51.5074))  -- London coordinates
  AND la.effective_to IS NULL;
```

**Find Nearest Substation:**
```sql
SELECT 
  s.substation_name,
  s.voltage_level,
  ST_DISTANCE(s.location, ST_GEOGPOINT(-0.1278, 51.5074))/1000 as distance_km
FROM gb_power.substations s
WHERE s.dno_key = 'UKPN-LPN'
ORDER BY distance_km
LIMIT 5;
```

**Calculate Service Area:**
```sql
SELECT 
  dno_key,
  ST_AREA(boundary)/1000000 as area_km2,
  ST_PERIMETER(boundary)/1000 as perimeter_km
FROM gb_power.dno_boundaries;
```

---

## 8. Implementation Timeline

### Phase 1: Foundation (Week 1) ✅ IN PROGRESS
- ✅ Create folder structure for 14 DNOs
- ✅ Fetch available datasets from OpenDataSoft (11 datasets)
- ✅ Backup NGED files to Google Drive (195 files)
- ✅ Design BigQuery schema
- 🔄 Create documentation

### Phase 2: Data Extraction (Week 2)
- Download NGED files from Google Drive to workspace
- Build Excel parser for NGED tariff schedules
- Build PDF parser for LC14 statements
- Extract 2010-2026 tariff data
- Validate data quality

### Phase 3: BigQuery Ingestion (Week 3)
- Create BigQuery dataset `gb_power`
- Create all tables with schema above
- Load NGED tariff data (4 license areas × 15 years)
- Load UKPN/NPg data from API
- Create views for common queries

### Phase 4: Google Sheets (Week 4)
- Create master tariff sheet with BigQuery connection
- Build dropdown filters and search functions
- Add year-by-year comparison charts
- Test query performance
- Document user guide

### Phase 5: GeoJSON (Week 5)
- Find/create DNO boundary files
- Download GSP group boundaries from NESO
- Extract substation locations from OpenDataSoft
- Load to BigQuery GEOGRAPHY tables
- Build spatial query examples

### Phase 6: Automation (Week 6)
- Schedule BigQuery data refreshes
- Create Cloud Function for new file uploads
- Set up email alerts for rate changes
- Build API endpoint for external access

---

## 9. Tools and Technologies

### Development Stack
- **Language:** Python 3.11+
- **Data Processing:** `pandas`, `numpy`, `openpyxl`
- **PDF Extraction:** `pdfplumber`, `PyPDF2`, `tabula-py`
- **Google Cloud:** `google-cloud-bigquery`, `google-api-python-client`
- **Spatial:** `geopandas`, `shapely`, `fiona`
- **Web Scraping:** `requests`, `beautifulsoup4`

### Storage
- **Staging:** Local workspace folders
- **Backup:** Google Drive (personal account)
- **Analytics:** BigQuery `gb_power` dataset
- **User Access:** Google Sheets with BigQuery connector

### Validation
- **Data Quality:** Row counts, rate ranges, date continuity
- **Schema:** BigQuery table schemas
- **Geographic:** ST_ISVALID checks on GEOGRAPHY columns

---

## 10. Data Quality Checks

### 10.1 Validation Rules

**Tariff Rates:**
- Unit rates: 0.1 to 100 p/kWh (fail if outside range)
- Capacity charges: 0.1 to 50 p/kVA/day
- Fixed charges: 1 to 500 p/day
- Time bands: RED > AMBER > GREEN (generally)

**Dates:**
- effective_from < effective_to (if not null)
- No gaps in year coverage (annual statements required)
- Financial year alignment (April 1 start dates)

**References:**
- dno_key must exist in dno_license_areas
- tariff_id must exist in duos_tariff_definitions
- voltage_level must exist in voltage_levels

### 10.2 Completeness Checks

```sql
-- Check year coverage per DNO
SELECT 
  dno_key,
  COUNT(DISTINCT year) as years_covered,
  MIN(year) as first_year,
  MAX(year) as last_year,
  ARRAY_AGG(DISTINCT year ORDER BY year) as years
FROM gb_power.duos_unit_rates
GROUP BY dno_key
ORDER BY dno_key;

-- Expected: 14 rows (14 DNOs), years_covered ~10-15 each
```

---

## 11. Next Actions

### Immediate (This Session)
1. ✅ Complete this documentation
2. Create BigQuery dataset and tables
3. Build NGED Excel parser prototype
4. Test with 1-2 sample files
5. Search for GeoJSON boundary files

### Short-term (This Week)
1. Download NGED files from Google Drive
2. Process all 195 NGED files
3. Load to BigQuery
4. Create initial Google Sheet
5. Find license area boundaries

### Medium-term (This Month)
1. Add UKPN, NPg, ENWL data
2. Manually collect SPEN, SSEN files
3. Complete spatial data ingestion
4. Build comprehensive Sheets dashboards
5. Document all processes

---

## 12. Success Metrics

- **Coverage:** 14/14 license areas with tariff data
- **Years:** 2010-2026 (15+ years per DNO)
- **Completeness:** >90% of expected tariff codes per DNO/year
- **Quality:** <1% data validation errors
- **Spatial:** All 14 license area boundaries loaded
- **Usability:** Google Sheets response time <3 seconds for queries
- **Documentation:** 100% of processes documented

---

## 13. Known Limitations

1. **API Access:** Only 5/14 DNOs have public data portals
2. **File Formats:** PDFs require complex parsing, some may need OCR
3. **Tariff Complexity:** Different DNOs use different structures
4. **Rate Changes:** Mid-year changes may be published separately
5. **Historical Data:** Pre-2015 data may be incomplete or archived
6. **Spatial Data:** High-quality boundary files may not be freely available
7. **Service Account:** Cannot access user's personal Google Drive

---

## 14. References

### DNO Websites
- UKPN: https://www.ukpowernetworks.co.uk/electricity/distribution-use-of-system-charges
- ENWL: https://www.enwl.co.uk/about-us/regulatory-information/
- NPg: https://www.northernpowergrid.com/asset-management/network-pricing
- SPEN: https://www.spenergynetworks.co.uk/pages/distribution_charges.aspx
- SSEN: https://www.ssen.co.uk/about-ssen/dso-distribution-system-operator/charging-and-connections/
- NGED: https://www.nationalgrid.com/electricity-distribution/network-and-assets/distribution-use-of-system-duos-charges

### Regulatory
- Ofgem DUoS Guidance: https://www.ofgem.gov.uk/
- DCUSA (Distribution Connection and Use of System Agreement)
- Common Distribution Charging Methodology (CDCM)

### Technical
- BigQuery Geography: https://cloud.google.com/bigquery/docs/geospatial-data
- GeoJSON Specification: https://geojson.org/
- MPAN Structure: https://www.energy-stats.uk/mpan-structure/

---

**Document Status:** DRAFT v1.0  
**Last Updated:** 2025-10-30  
**Next Review:** After Phase 1 completion
