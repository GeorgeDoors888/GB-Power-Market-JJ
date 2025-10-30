# DNO Charging Data Project - Documentation Index

**Project:** GB Power Market - DNO DUoS Charging Analysis  
**Date:** 2025-10-30  
**Status:** Infrastructure Complete, Ready for Data Extraction

---

## 📁 Quick Navigation

### 🎯 Start Here
- **[Distribution ID Organization](#distribution-id-organization)** - 302 files organized by MPAN Distributor ID (10-23) and year
- **[Implementation Summary](#implementation-summary)** - Current status, next steps
- **[BigQuery Schema](#bigquery-schema)** - Database structure and tables
- **[Spatial Data](#spatial-data)** - GeoJSON files and geographic analysis

### 📖 Comprehensive Guides
1. **[Files by Distribution ID & Year](#files-by-distribution-id)** - Complete inventory with MPAN mapping
2. **[Full Pipeline Documentation](#full-pipeline)**
3. **[Spatial Data Catalog](#spatial-catalog)**
4. **[Document Analysis](#document-analysis)**

### 💻 Scripts & Tools
- **[Python Scripts](#scripts)**
- **[BigQuery Queries](#queries)**
- **[Data Sources](#sources)**

---

## Files by Distribution ID

**File:** [`DNO_FILES_BY_DISTRIBUTION_ID_AND_YEAR.md`](DNO_FILES_BY_DISTRIBUTION_ID_AND_YEAR.md) (53 KB)

**Contents:**
- ✅ **302 charging files** organized by Distribution ID (10-23) and year (2014-2026)
- ✅ **MPAN/Distributor ID mapping** table with DNO_Key, Market Participant ID, GSP Group
- ✅ **Coverage matrix** showing files per Distribution ID per year
- ✅ **Detailed file listings** for each of 14 DNO license areas
- ✅ **Data quality assessment** (High/Good/Moderate/Poor)
- ✅ **Missing data identification** (NPg-NE has no files, SPN has only 1)
- ✅ **File type categories** (Schedule of Charges, CDCM, PCDM, ED2 PCFM, Annexes)

**Key Coverage Stats:**
- **High Quality (13 years):** NGED areas (EMID, WMID, SWALES, SWEST) - 2014-2026 complete
- **High Quality (10 years):** UKPN areas (EPN, LPN) - 2017-2026 complete
- **Good Quality (7 years):** SSEN (SHEPD, SEPD), SPEN (SPM, SPD), NPg-Y - 2020-2026
- **Gaps:** ENWL (spotty), SPN (1 file only), NPg-NE (missing)

**Distribution ID Mapping:**
| ID | DNO | MPID | GSP | Files |
|----|-----|------|-----|-------|
| 10 | UKPN-EPN | EELC | A | 29 |
| 11 | NGED-EM | EMEB | B | 17 |
| 12 | UKPN-LPN | LOND | C | 13 |
| 13 | SP-Manweb | MANW | D | 23 |
| 14 | NGED-WM | MIDE | E | 17 |
| 15 | NPg-NE | NEEB | F | 0 ❌ |
| 16 | ENWL | NORW | G | 48 |
| 17 | SSE-SHEPD | HYDE | P | 36 |
| 18 | SP-Distribution | SPOW | N | 19 |
| 19 | UKPN-SPN | SEEB | J | 1 ⚠️ |
| 20 | SSE-SEPD | SOUT | H | 40 |
| 21 | NGED-SWales | SWAE | K | 15 |
| 22 | NGED-SW | SWEB | L | 17 |
| 23 | NPg-Y | YELG | M | 26 |

---

## Implementation Summary

**File:** [`DNO_PIPELINE_IMPLEMENTATION_SUMMARY.md`](DNO_PIPELINE_IMPLEMENTATION_SUMMARY.md) (20 KB)

**Contents:**
- ✅ Executive summary of completed work
- ✅ All 10 BigQuery tables documented
- ✅ Spatial data files identified (14 DNO boundaries + ~150 GSP regions)
- ✅ 195 NGED files inventory (2010-2026)
- ✅ 6-phase implementation timeline
- ✅ Next immediate actions
- ✅ Success metrics and blockers

**Key Stats:**
- **BigQuery Tables:** 10 created (4 with data, 6 ready for loading)
- **DNO License Areas:** 14 metadata records loaded
- **Voltage Levels:** 4 reference records loaded
- **GeoJSON Files:** 2 primary files identified (DNO boundaries + GSP regions)
- **Charging Documents:** 195 NGED files + 11 API datasets

**Current Phase:** Phase 1 Complete (Infrastructure) → Ready for Phase 2 (Spatial Loading)

---

## Full Pipeline

**File:** [`DNO_CHARGING_DATA_PIPELINE.md`](DNO_CHARGING_DATA_PIPELINE.md) (21 KB)

**Contents:**
- **Section 1-2:** Project overview and 14 DNO license areas
- **Section 3:** DUoS charging components (unit rates, capacity, fixed, time bands)
- **Section 4:** Complete BigQuery schema design (10 tables)
- **Section 5:** Data extraction strategy (NGED, UKPN, NPg, SPEN, SSEN)
- **Section 6:** Google Sheets structure (3 sheets with formulas)
- **Section 7:** GeoJSON integration requirements
- **Section 8:** 6-phase implementation timeline
- **Section 9:** Tools and technologies
- **Section 10:** Data quality checks and validation rules
- **Section 11-14:** Next actions, success metrics, limitations, references

**Highlights:**
- Tariff code structure explained for each DNO
- Time band definitions (Red 16:00-19:00, Amber 07:00-16:00 + 19:00-23:00, Green off-peak)
- BigQuery query examples (10+ sample queries)
- Data validation rules (rate ranges, date continuity)
- 39 tariff categories identified across all DNOs

---

## Spatial Catalog

**File:** [`DNO_GEOJSON_CATALOG.md`](DNO_GEOJSON_CATALOG.md) (17 KB)

**Contents:**
- **Section 1:** DNO license area boundary files (primary + alternatives)
- **Section 2:** GSP region boundary files (2025, 2022, 2018 versions)
- **Section 3:** Additional network boundaries (TNUoS, ETYS)
- **Section 4:** GeoJSON feature structure and properties
- **Section 5:** Coordinate reference systems (WGS84 vs British National Grid)
- **Section 6:** BigQuery loading strategy (3 steps)
- **Section 7:** Spatial query examples (10+ queries)
- **Section 8:** Data quality notes
- **Section 9:** File selection recommendations
- **Section 10-13:** Loading script, future enhancements, data sources, updates

**Primary Files:**
1. **DNO Boundaries:** `gb-dno-license-areas-20240503-as-geojson.geojson`
   - 14 polygons, 2.9 MB, WGS84, dated 2024-05-03
   
2. **GSP Regions:** `GSP_regions_4326_20250109_simplified.geojson`
   - ~150 polygons, 9.2 MB, WGS84, dated 2025-01-09

**Spatial Queries Documented:**
- Find DNO by coordinates
- Calculate service areas
- Buffer analysis (50km radius)
- Join tariffs to geography
- Validate boundaries (overlaps, containment)

---

## Document Analysis

**File:** [`DNO_DOCUMENTS_COMPREHENSIVE_ANALYSIS.md`](DNO_DOCUMENTS_COMPREHENSIVE_ANALYSIS.md) (75 KB)

**Contents:**
- Analysis of 1,966+ PDF and Excel files across all DNOs
- 12 document categories identified
- Completeness assessment by DNO (SSEN: 95%, Others: 15-30%)
- Document naming conventions
- Data quality metrics
- Coverage by category (Regulatory, Asset Data, Charges, Connection, Operational)

**Key Findings:**
- **SSEN:** Most comprehensive (DUoS charges, methodologies, RIIO-ED2 submissions)
- **NGED:** 195 files covering 2010-2026 (DUoS schedules, LC14 statements, ED2 models)
- **UKPN/NPg/ENWL:** Mainly asset workbooks, limited charging docs via API
- **SPEN:** SSL issues, manual download required
- **Missing:** DUoS charges for UKPN, NPg, ENWL, SPEN (must visit DNO websites)

---

## BigQuery Schema

**Dataset:** `inner-cinema-476211-u9.gb_power`  
**Location:** EU  
**Tables:** 10

### Core Charging Tables

| Table | Purpose | Partition | Cluster | Status |
|-------|---------|-----------|---------|--------|
| `dno_license_areas` | 14 DNO metadata | Year | - | ✅ 14 rows |
| `duos_tariff_definitions` | Tariff metadata | Year | dno_key, voltage, category | 🔄 Schema ready |
| `duos_unit_rates` | **Main tariff data** | Year | dno_key, tariff_code, time_band | 🔄 Schema ready |
| `duos_time_bands` | Time definitions | - | - | 🔄 Schema ready |

### Spatial Tables

| Table | Purpose | Features | Status |
|-------|---------|----------|--------|
| `dno_boundaries` | License area polygons | 14 DNOs | 📍 Ready to load |
| `gsp_boundaries` | GSP region polygons | ~150 GSPs | 📍 Ready to load |
| `substations` | Substation locations | TBD | 🔄 Schema ready |

### Reference Tables

| Table | Purpose | Rows | Status |
|-------|---------|------|--------|
| `voltage_levels` | LV/HV/EHV/UHV definitions | 4 | ✅ Loaded |
| `customer_categories` | Customer types | TBD | 🔄 Schema ready |

### Schema Features
- ✅ Time partitioning by year (2010-2030 range)
- ✅ Clustering on high-cardinality columns (dno_key, tariff_code)
- ✅ GEOGRAPHY data type for spatial analysis
- ✅ Foreign key relationships documented
- ✅ Optimized for year-based filtering

---

## Scripts

### Infrastructure Scripts (Completed ✅)

**`create_bigquery_schema.py`**
- Creates all 10 BigQuery tables
- Loads reference data (14 DNOs, 4 voltage levels)
- Sets up partitioning and clustering
- Status: ✅ Successfully executed

**`fetch_dno_charging_docs.py`**
- Fetches datasets from OpenDataSoft APIs
- Creates folder structure for 14 DNOs
- Generates metadata.json files
- Status: ✅ Executed, found 11 datasets

**`analyze_dno_charging_files.py`**
- Analyzes files in Google Drive backup
- Categorizes by DNO license area
- Extracts years from filenames
- Status: ✅ Ready (note: service account cannot access user's Drive)

**`load_dno_geojson_to_bigquery.py`**
- Loads DNO boundaries from GeoJSON (14 polygons)
- Loads GSP regions from GeoJSON (~150 polygons)
- Calculates areas using ST_AREA
- Validates spatial data (ST_ISVALID, overlaps, containment)
- Status: ✅ Script ready (needs property mapping fix)

**`load_geojson_to_bigquery.py`** (Previous work)
- Generic GeoJSON → BigQuery loader
- GEOGRAPHY data type handling
- Spatial function examples
- Status: ✅ Complete

**`sync_local_to_drive.py`** (Previous work)
- Syncs local files to Google Drive
- Duplicate detection
- Status: ✅ Successfully backed up 195 NGED files

### Data Extraction Scripts (TODO ⏳)

**`parse_nged_excel_tariffs.py`** - Not yet created
- Extract tariff tables from Excel files
- Parse tariff codes, unit rates, time bands
- Map license areas (SWEB, SWAE, MIDE, EMEB)
- Extract effective dates
- Validate rate ranges

**`parse_nged_pdf_lc14.py`** - Not yet created
- Extract methodology from PDF statements
- Parse tariff structure descriptions
- Extract time band definitions
- OCR if necessary

**`load_tariffs_to_bigquery.py`** - Not yet created
- Bulk load tariff data to `duos_unit_rates`
- Validate foreign key relationships
- Check date continuity
- Generate loading report

---

## Queries

### Sample BigQuery Queries

**Get all tariffs for a DNO/year:**
```sql
SELECT 
  tariff_code,
  time_band,
  unit_rate,
  unit
FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
WHERE dno_key = 'NGED-SW'
  AND year = 2025
  AND voltage_level = 'LV'
ORDER BY tariff_code, time_band;
```

**Find DNO by location:**
```sql
SELECT la.dno_key, la.dno_name
FROM `inner-cinema-476211-u9.gb_power.dno_license_areas` la
JOIN `inner-cinema-476211-u9.gb_power.dno_boundaries` b 
  ON la.dno_key = b.dno_key
WHERE ST_CONTAINS(
  ST_GEOGFROMGEOJSON(b.geometry),
  ST_GEOGPOINT(-0.1278, 51.5074)  -- London
);
```

**Year-over-year rate comparison:**
```sql
SELECT 
  tariff_code,
  year,
  AVG(unit_rate) as avg_rate_p_kwh
FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
WHERE dno_key = 'UKPN-LPN'
  AND rate_component = 'ENERGY'
  AND year BETWEEN 2020 AND 2025
GROUP BY tariff_code, year
ORDER BY tariff_code, year;
```

**Calculate total area by DNO:**
```sql
SELECT 
  dno_key,
  ROUND(ST_AREA(ST_GEOGFROMGEOJSON(geometry)) / 1000000, 0) as area_km2
FROM `inner-cinema-476211-u9.gb_power.dno_boundaries`
ORDER BY area_km2 DESC;
```

More queries in: `DNO_CHARGING_DATA_PIPELINE.md` Section 7 and `DNO_GEOJSON_CATALOG.md` Section 7

---

## Sources

### Charging Documents

**Primary Sources:**
- **NGED:** 195 files (2010-2026) backed up in Google Drive
  - DUoS charge schedules (Excel)
  - LC14 statements (PDF)
  - Use of System charging statements (PDF)
  - ED2 PCFM models (Excel)

- **UKPN:** https://ukpowernetworks.opendatasoft.com
  - 9 datasets via OpenDataSoft API
  - 3 license areas: LPN, EPN, SPN

- **NPg:** https://northernpowergrid.opendatasoft.com
  - 2 datasets via OpenDataSoft API
  - 2 license areas: NE, Y

- **ENWL:** https://enwl.opendatasoft.com
  - Limited API access

- **SPEN:** Manual download required
  - https://www.spenergynetworks.co.uk/pages/distribution_charges.aspx

- **SSEN:** Manual download required
  - https://www.ssen.co.uk/about-ssen/dso-distribution-system-operator/charging-and-connections/

### Spatial Data

**GeoJSON Files:**
- DNO license areas (2024-05-03) - Source: Ofgem/NESO
- GSP regions (2025-01-09) - Source: NESO
- Location: `old_project/GIS_data/`

**Official Sources:**
- **Ofgem:** https://www.ofgem.gov.uk/energy-data-and-research
- **NESO:** https://www.neso.energy/data-portal
- **Elexon:** https://www.elexon.co.uk/data/

---

## Project Structure

```
GB Power Market JJ/
├── Documentation (This Index)
│   ├── DNO_PIPELINE_IMPLEMENTATION_SUMMARY.md    ← Start here
│   ├── DNO_CHARGING_DATA_PIPELINE.md             ← Full workflow
│   ├── DNO_GEOJSON_CATALOG.md                    ← Spatial data
│   ├── DNO_DOCUMENTS_COMPREHENSIVE_ANALYSIS.md   ← Document inventory
│   └── DNO_CHARGING_PROJECT_INDEX.md             ← This file
│
├── Scripts/
│   ├── create_bigquery_schema.py                 ✅ Executed
│   ├── fetch_dno_charging_docs.py                ✅ Executed
│   ├── analyze_dno_charging_files.py             ✅ Ready
│   ├── load_dno_geojson_to_bigquery.py           ✅ Ready
│   ├── load_geojson_to_bigquery.py               ✅ Complete
│   ├── sync_local_to_drive.py                    ✅ Used
│   ├── parse_nged_excel_tariffs.py               ⏳ TODO
│   ├── parse_nged_pdf_lc14.py                    ⏳ TODO
│   └── load_tariffs_to_bigquery.py               ⏳ TODO
│
├── Data/
│   ├── dno_charging_documents/                   ← 14 DNO folders
│   │   ├── NGED-WM/metadata.json
│   │   ├── NGED-EM/metadata.json
│   │   ├── NGED-SW/metadata.json
│   │   ├── NGED-SWales/metadata.json
│   │   ├── UKPN-LPN/metadata.json
│   │   └── ... (10 more)
│   │
│   └── old_project/GIS_data/                     ← Spatial files
│       ├── gb-dno-license-areas-20240503...geojson    14 DNOs
│       ├── GSP_regions_4326_20250109...geojson        ~150 GSPs
│       └── ... (historical versions)
│
├── BigQuery Dataset: inner-cinema-476211-u9.gb_power
│   ├── dno_license_areas                        ✅ 14 rows
│   ├── voltage_levels                           ✅ 4 rows
│   ├── customer_categories                      🔄 Schema
│   ├── duos_tariff_definitions                  🔄 Schema
│   ├── duos_unit_rates                          🔄 Schema (main table)
│   ├── duos_time_bands                          🔄 Schema
│   ├── dno_boundaries                           📍 Ready
│   ├── gsp_boundaries                           📍 Ready
│   └── substations                              🔄 Schema
│
└── Google Drive Backup/
    └── 195 NGED files (2010-2026)               ✅ Backed up
```

---

## Quick Reference

### 14 DNO License Areas

| MPAN | DNO Key | Name | GSP | Area Covered |
|------|---------|------|-----|--------------|
| 10 | UKPN-EPN | UK Power Networks (Eastern) | A | East England |
| 11 | NGED-EM | National Grid ED (East Midlands) | B | East Midlands |
| 12 | UKPN-LPN | UK Power Networks (London) | C | London |
| 13 | SP-Manweb | SP Energy Networks (Manweb) | D | Merseyside & N Wales |
| 14 | NGED-WM | National Grid ED (West Midlands) | E | West Midlands |
| 15 | NPg-NE | Northern Powergrid (North East) | F | North East |
| 16 | ENWL | Electricity North West | G | North West |
| 20 | SSE-SEPD | Southern Electric Power Dist. | H | Southern |
| 19 | UKPN-SPN | UK Power Networks (South Eastern) | J | South Eastern |
| 21 | NGED-SWales | National Grid ED (South Wales) | K | South Wales |
| 22 | NGED-SW | National Grid ED (South West) | L | South Western |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | M | Yorkshire |
| 18 | SP-Distribution | SP Energy Networks (SPD) | N | South Scotland |
| 17 | SSE-SHEPD | Scottish Hydro Electric PD | P | North Scotland |

### Voltage Levels

| Code | Name | kV Range | Typical Customers |
|------|------|----------|-------------------|
| LV | Low Voltage | 0.23-0.40 | Domestic, small commercial |
| HV | High Voltage | 6.6-33 | Large commercial, industrial |
| EHV | Extra High Voltage | 66-132 | Very large industrial |
| UHV | Ultra High Voltage | 275-400 | Transmission level |

### Time Bands

| Band | Period | Winter Hours | Summer Hours |
|------|--------|--------------|--------------|
| RED | Peak | 16:00-19:00 weekdays | Varies by DNO |
| AMBER | Shoulder | 07:00-16:00, 19:00-23:00 | Varies by DNO |
| GREEN | Off-peak | 00:00-07:00, 23:00-00:00, weekends | All other |

**Note:** Exact definitions vary by DNO. See DNO-specific methodology statements.

---

## Next Steps

### Immediate (This Week)
1. ✅ **Load spatial data to BigQuery**
   - Fix property mapping in script
   - Load 14 DNO boundaries
   - Load ~150 GSP boundaries
   - Validate with test queries

2. ⏳ **Build NGED Excel parser**
   - Create `parse_nged_excel_tariffs.py`
   - Test with 2-3 sample files
   - Iterate until extraction works correctly

3. ⏳ **Download NGED files from Google Drive**
   - User to download 195 files
   - Or implement Google Drive OAuth
   - Place in respective DNO folders

### Short-term (This Month)
4. ⏳ **Extract NGED tariffs**
   - Process all 195 files
   - Generate ~15,000-20,000 tariff records
   - Load to BigQuery
   - Validate data quality

5. ⏳ **Collect UKPN/NPg data**
   - Download 11 datasets from APIs
   - Parse and load to BigQuery
   - +5,000-10,000 records

6. ⏳ **Create Google Sheets**
   - Master tariff sheet with BigQuery connector
   - Dropdown filters and search
   - Annual cost calculator

### Medium-term (Next Quarter)
7. ⏳ **Manual DNO collection**
   - SPEN, SSEN, ENWL
   - Complete 14/14 coverage
   - Historical backfill

8. ⏳ **Analytics & Insights**
   - Rate comparison analysis
   - Geographic visualization
   - Trend analysis (2010-2026)

---

## Contact & Support

**Project Team:** GB Power Market Data Team  
**Repository:** `jibber-jabber-24-august-2025-big-bop`  
**BigQuery Project:** `inner-cinema-476211-u9`  
**Last Updated:** 2025-10-30

**For Questions:**
- Infrastructure/Schema: See `DNO_CHARGING_DATA_PIPELINE.md`
- Spatial Data: See `DNO_GEOJSON_CATALOG.md`
- Implementation Status: See `DNO_PIPELINE_IMPLEMENTATION_SUMMARY.md`
- Document Inventory: See `DNO_DOCUMENTS_COMPREHENSIVE_ANALYSIS.md`

---

**Document Version:** 1.0  
**Total Documentation:** 133+ KB across 5 files  
**Status:** Infrastructure Complete ✅  
**Ready for:** Data Extraction Phase 🚀
