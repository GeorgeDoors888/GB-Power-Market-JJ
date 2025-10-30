# DNO Charging Data Summary Report

**Generated:** 2025-10-30 01:45:23

**Project:** GB Power Market - DNO DUoS Charging Analysis

---

## Executive Summary

- **Total Files Found:** 743
- **Unique Files:** 323
- **Distribution IDs Found:** 14/14
- **Year Coverage:** 2014-2026 (13 years)
- **Total Data Size:** 106.7 MB

## GeoJSON Files Backup Summary

**Location:** `/Users/georgemajor/GB Power Market JJ/old_project/GIS_data/`

**Files Copied:** 19 GeoJSON files (~150 MB total)


### GeoJSON Inventory:

| File | Size | Description |
|------|------|-------------|
| GSP_regions_4326_20250109.geojson | 9.9M | GSP Regions (WGS84) - Latest |
| GSP_regions_4326_20250109_simplified.geojson | 9.2M | GSP Regions (WGS84) - Simplified |
| GSP_regions_4326_20250102.geojson | 9.7M | GSP Regions (WGS84) - Jan 2 |
| GSP_regions_4326_20250102_simplified.geojson | 9.1M | GSP Regions (WGS84) - Simplified |
| GSP_regions_27700_20250109.geojson | 10M | GSP Regions (British National Grid) |
| GSP_regions_27700_20250109_simplified.geojson | 9.5M | GSP Regions (BNG) - Simplified |
| GSP_regions_27700_20250102.geojson | 10M | GSP Regions (BNG) - Jan 2 |
| GSP_regions_27700_20250102_simplified.geojson | 9.4M | GSP Regions (BNG) - Simplified |
| gsp_regions_20220314.geojson | 13M | GSP Regions - March 2022 |
| gsp_regions_20220314_simplified.geojson | 11M | GSP Regions - 2022 Simplified |
| gsp_regions_20181031.geojson | 3.2M | GSP Regions - Oct 2018 |
| gsp_regions_20181031_simplified.geojson | 2.5M | GSP Regions - 2018 Simplified |
| gb-dno-license-areas-20240503-as-geojson.geojson | 2.9M | DNO License Areas - May 2024 |
| gb-dno-license-areas-20240503-as-geojson_simplified.geojson | 2.3M | DNO Areas - Simplified |
| dno_license_areas_20200506.geojson | 2.9M | DNO License Areas - May 2020 |
| dno_license_areas_20200506_simplified.geojson | 2.3M | DNO Areas - 2020 Simplified |
| merged_geojson.geojson | 29M | Merged/Combined Dataset |
| tnuosgenzones_geojs.geojson | 46K | TNUoS Generation Zones |
| tnuosgenzones_geojs_simplified.geojson | 43K | TNUoS Zones - Simplified |

**Key Features:**
- Multiple GSP region versions: 2018, 2022, and 2025 (Jan 2 & Jan 9)
- Both coordinate systems: WGS84 (EPSG:4326) and British National Grid (EPSG:27700)
- Simplified versions for faster rendering
- DNO boundary versions from 2020 and 2024
- TNUoS generation zones (new data source)
- Ready for BigQuery import with GEOGRAPHY type

## Charging Data Summary by Year

| Year | Files | DNOs | Excel | PDF | CSV | Size (MB) |
|------|-------|------|-------|-----|-----|-----------|
| 2014 | 8 | 4 | 8 | 0 | 0 | 1.1 |
| 2015 | 4 | 4 | 4 | 0 | 0 | 1.2 |
| 2016 | 4 | 4 | 4 | 0 | 0 | 1.2 |
| 2017 | 10 | 8 | 9 | 0 | 1 | 2.8 |
| 2018 | 9 | 8 | 8 | 0 | 1 | 2.4 |
| 2019 | 9 | 8 | 8 | 0 | 1 | 3.0 |
| 2020 | 20 | 12 | 19 | 0 | 1 | 10.3 |
| 2021 | 31 | 12 | 29 | 0 | 2 | 14.8 |
| 2022 | 31 | 13 | 29 | 1 | 1 | 15.3 |
| 2023 | 31 | 14 | 30 | 1 | 0 | 17.9 |
| 2024 | 31 | 13 | 31 | 0 | 0 | 17.3 |
| 2025 | 35 | 14 | 27 | 1 | 7 | 11.0 |
| 2026 | 26 | 14 | 26 | 0 | 0 | 8.4 |
| **TOTAL** | **249** | **14** | **232** | **3** | **14** | **106.7** |

## Charging Data Summary by DNO (All 14 Distribution IDs)

| ID | DNO | Name | Files | Years | Coverage | Excel | PDF | CSV | Size (MB) |
|----|-----|------|-------|-------|----------|-------|-----|-----|-----------|
| 10 | EPN | UK Power Networks (Eastern)... | 18 | 10 | 2017-2026 | 10 | 0 | 6 | 3.2 |
| 11 | EMID | National Grid Electricity Dist... | 17 | 13 | 2014-2026 | 14 | 0 | 0 | 4.4 |
| 12 | LPN | UK Power Networks (London)... | 13 | 10 | 2017-2026 | 10 | 0 | 1 | 2.1 |
| 13 | SPM | SP Energy Networks (SPM)... | 23 | 7 | 2020-2026 | 18 | 0 | 0 | 14.7 |
| 14 | WMID | National Grid Electricity Dist... | 17 | 13 | 2014-2026 | 14 | 0 | 0 | 3.8 |
| 15 | NE | Northern Powergrid (North East... | 22 | 4 | 2023-2026 | 20 | 0 | 1 | 5.7 |
| 16 | ENWL | Electricity North West... | 48 | 7 | 2018-2026 | 8 | 3 | 2 | 7.1 |
| 17 | SHEPD | Scottish Hydro Electric Power ... | 36 | 7 | 2020-2026 | 33 | 0 | 0 | 15.2 |
| 18 | SPD | SP Energy Networks (SPD)... | 19 | 7 | 2020-2026 | 17 | 0 | 0 | 14.8 |
| 19 | SPN | UK Power Networks (South Easte... | 11 | 10 | 2017-2026 | 10 | 0 | 0 | 2.4 |
| 20 | SEPD | Southern Electric Power Distri... | 40 | 7 | 2020-2026 | 28 | 0 | 3 | 18.1 |
| 21 | SWALES | National Grid Electricity Dist... | 16 | 13 | 2014-2026 | 14 | 0 | 0 | 4.0 |
| 22 | SWEST | National Grid Electricity Dist... | 17 | 13 | 2014-2026 | 14 | 0 | 0 | 4.4 |
| 23 | Y | Northern Powergrid (Yorkshire)... | 26 | 7 | 2017-2026 | 22 | 0 | 1 | 6.9 |

**Total:** 323 files | 106.7 MB

## Detailed Analysis by DNO

### Distribution ID 10: UKPN-EPN - UK Power Networks (Eastern)

**Short Code:** EPN  
**Total Files:** 18  
**Year Coverage:** 2017-2026 (10 years)  
**Total Size:** 3.2 MB

**File Types:**
- Excel: 10 files
- CSV: 6 files

**Years with Data:** 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 11: NGED-EM - National Grid Electricity Distribution – East Midlands

**Short Code:** EMID  
**Total Files:** 17  
**Year Coverage:** 2014-2026 (13 years)  
**Total Size:** 4.4 MB

**File Types:**
- Excel: 14 files

**Years with Data:** 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 12: UKPN-LPN - UK Power Networks (London)

**Short Code:** LPN  
**Total Files:** 13  
**Year Coverage:** 2017-2026 (10 years)  
**Total Size:** 2.1 MB

**File Types:**
- Excel: 10 files
- CSV: 1 files

**Years with Data:** 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 13: SP-Manweb - SP Energy Networks (SPM)

**Short Code:** SPM  
**Total Files:** 23  
**Year Coverage:** 2020-2026 (7 years)  
**Total Size:** 14.7 MB

**File Types:**
- Excel: 18 files

**Years with Data:** 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 14: NGED-WM - National Grid Electricity Distribution – West Midlands

**Short Code:** WMID  
**Total Files:** 17  
**Year Coverage:** 2014-2026 (13 years)  
**Total Size:** 3.8 MB

**File Types:**
- Excel: 14 files

**Years with Data:** 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 15: NPg-NE - Northern Powergrid (North East)

**Short Code:** NE  
**Total Files:** 22  
**Year Coverage:** 2023-2026 (4 years)  
**Total Size:** 5.7 MB

**File Types:**
- Excel: 20 files
- CSV: 1 files

**Years with Data:** 2023, 2024, 2025, 2026

### Distribution ID 16: ENWL - Electricity North West

**Short Code:** ENWL  
**Total Files:** 48  
**Year Coverage:** 2018-2026 (7 years)  
**Total Size:** 7.1 MB

**File Types:**
- Excel: 8 files
- PDF: 3 files
- CSV: 2 files

**Years with Data:** 2018, 2020, 2021, 2022, 2023, 2025, 2026

### Distribution ID 17: SSE-SHEPD - Scottish Hydro Electric Power Distribution

**Short Code:** SHEPD  
**Total Files:** 36  
**Year Coverage:** 2020-2026 (7 years)  
**Total Size:** 15.2 MB

**File Types:**
- Excel: 33 files

**Years with Data:** 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 18: SP-Distribution - SP Energy Networks (SPD)

**Short Code:** SPD  
**Total Files:** 19  
**Year Coverage:** 2020-2026 (7 years)  
**Total Size:** 14.8 MB

**File Types:**
- Excel: 17 files

**Years with Data:** 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 19: UKPN-SPN - UK Power Networks (South Eastern)

**Short Code:** SPN  
**Total Files:** 11  
**Year Coverage:** 2017-2026 (10 years)  
**Total Size:** 2.4 MB

**File Types:**
- Excel: 10 files

**Years with Data:** 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 20: SSE-SEPD - Southern Electric Power Distribution

**Short Code:** SEPD  
**Total Files:** 40  
**Year Coverage:** 2020-2026 (7 years)  
**Total Size:** 18.1 MB

**File Types:**
- Excel: 28 files
- CSV: 3 files

**Years with Data:** 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 21: NGED-SWales - National Grid Electricity Distribution – South Wales

**Short Code:** SWALES  
**Total Files:** 16  
**Year Coverage:** 2014-2026 (13 years)  
**Total Size:** 4.0 MB

**File Types:**
- Excel: 14 files

**Years with Data:** 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 22: NGED-SW - National Grid Electricity Distribution – South West

**Short Code:** SWEST  
**Total Files:** 17  
**Year Coverage:** 2014-2026 (13 years)  
**Total Size:** 4.4 MB

**File Types:**
- Excel: 14 files

**Years with Data:** 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### Distribution ID 23: NPg-Y - Northern Powergrid (Yorkshire)

**Short Code:** Y  
**Total Files:** 26  
**Year Coverage:** 2017-2026 (7 years)  
**Total Size:** 6.9 MB

**File Types:**
- Excel: 22 files
- CSV: 1 files

**Years with Data:** 2017, 2019, 2022, 2023, 2024, 2025, 2026

## Year Coverage Matrix

| DNO | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|-----|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EPN | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| EMID | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| LPN | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| SPM | — | — | — | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| WMID | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| NE | — | — | — | — | — | — | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| ENWL | — | — | — | — | ✓ (2) | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | — | ✓ (2) | ✓ (2) |
| SHEPD | — | — | — | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| SPD | — | — | — | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| SPN | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| SEPD | — | — | — | — | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| SWALES | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| SWEST | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |
| Y | — | — | — | ✓ (2) | — | ✓ (2) | — | — | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) | ✓ (2) |

**Legend:** ✓ (n) = Data available (n files), — = No data

## Data Quality Assessment

### High Quality Coverage (10+ years)

| DNO | Years | Coverage | Assessment |
|-----|-------|----------|------------|
| EPN | 10 | 2017-2026 | Very Good |
| EMID | 13 | 2014-2026 | Excellent |
| LPN | 10 | 2017-2026 | Very Good |
| WMID | 13 | 2014-2026 | Excellent |
| SPN | 10 | 2017-2026 | Very Good |
| SWALES | 13 | 2014-2026 | Excellent |
| SWEST | 13 | 2014-2026 | Excellent |

### Moderate Coverage (5-9 years)

| DNO | Years | Coverage | Assessment |
|-----|-------|----------|------------|
| SPM | 7 | 2020-2026 | Good |
| ENWL | 7 | 2018-2026 | Good |
| SHEPD | 7 | 2020-2026 | Good |
| SPD | 7 | 2020-2026 | Good |
| SEPD | 7 | 2020-2026 | Good |
| Y | 7 | 2017-2026 | Good |

### Limited Coverage (< 5 years)

| DNO | Years | Coverage | Assessment |
|-----|-------|----------|------------|
| NE | 4 | 2023-2026 | Fair |

## Next Steps

### 1. GeoJSON Import to BigQuery
- Import DNO boundaries (3 versions: 2020, 2024) to `dno_boundaries` table
- Import GSP regions (4 versions: 2018, 2022, 2025) to `gsp_boundaries` table
- Import TNUoS generation zones to `tnuos_zones` table
- Validate with ST_ISVALID and area calculations
- Enable spatial queries (point-in-polygon, distance, intersection)

### 2. Parse Charging Files
**Priority Order:**
1. **NGED areas (IDs 11, 14, 21, 22):** 67 files, 2014-2026 (13 years) - Most complete dataset
2. **UKPN areas (IDs 10, 12, 19):** 42 files, 2017-2026 (10 years) - London and South East
3. **SSEN areas (IDs 17, 20):** 76 files, 2017-2026 (10 years) - Scotland and Southern
4. **NPg areas (IDs 15, 23):** 48 files, 2023-2026 (4 years) - North East and Yorkshire
5. **SPEN areas (IDs 13, 18):** 42 files, 2020-2026 (7 years) - Scotland and Merseyside
6. **ENWL (ID 16):** 48 files, 2020-2026 (7 years) - North West

**Extract from Excel/PDF:**
- Tariff codes (LV/HV, domestic/commercial/industrial)
- Unit rates (p/kWh) by time band (day/night/peak/off-peak)
- Capacity charges (p/kVA/day)
- Fixed charges (p/day)
- Effective dates and change history
- Customer categories (UMS, domestic, non-domestic)
- Voltage levels (LV, HV, EHV, 132kV)

### 3. Load to BigQuery
- Table: `charging_tariffs` (partitioned by year, clustered by dno_key)
- Schema: year, dno_key, distribution_id, tariff_code, rate_type, time_band, unit_rate, capacity_charge, fixed_charge, voltage, category
- Enable time-series analysis and DNO comparison queries

### 4. Create Google Sheets Dashboard
- Master tariff lookup with year/DNO/voltage dropdowns
- Year-by-year comparison view
- Search by tariff code
- Annual cost calculator
- Connected to BigQuery for real-time data

---


**Report Generated:** 2025-10-30 01:45:23

**Source Data:** `dno_files_by_distribution_id_and_year.json`

**GeoJSON Location:** `/Users/georgemajor/GB Power Market JJ/old_project/GIS_data/`