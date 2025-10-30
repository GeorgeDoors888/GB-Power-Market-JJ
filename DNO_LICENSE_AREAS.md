# DNO License Areas - Complete Reference Documentation

## Overview
This document provides the complete reference for all 14 GB electricity Distribution Network Operator (DNO) license areas, their data sources, and download methodologies.

---

## Complete DNO Reference Table

| MPAN ID | DNO Key | DNO Name | Short Code | Market Part. ID | GSP Group | GSP Name | Company Group | Data Source |
|---------|---------|----------|------------|-----------------|-----------|----------|---------------|-------------|
| 10 | UKPN-EPN | UK Power Networks (Eastern) | EPN | EELC | A | Eastern | UKPN | ✅ ODS API |
| 11 | NGED-EM | National Grid Electricity Distribution – East Midlands | EMID | EMEB | B | East Midlands | NGED | 📄 Files |
| 12 | UKPN-LPN | UK Power Networks (London) | LPN | LOND | C | London | UKPN | ✅ ODS API |
| 13 | SP-Manweb | SP Energy Networks (SPM) | SPM | MANW | D | Merseyside & North Wales | SPEN | 🔄 ODS + Files |
| 14 | NGED-WM | National Grid Electricity Distribution – West Midlands | WMID | MIDE | E | West Midlands | NGED | 📄 Files |
| 15 | NPg-NE | Northern Powergrid (North East) | NE | NEEB | F | North East | NPg | 🔄 ODS + Files |
| 16 | ENWL | Electricity North West | ENWL | NORW | G | North West | ENWL | 🔄 ODS + Files |
| 17 | SSE-SHEPD | Scottish Hydro Electric Power Distribution | SHEPD | HYDE | P | North Scotland | SSEN | 📄 Files |
| 18 | SP-Distribution | SP Energy Networks (SPD) | SPD | SPOW | N | South Scotland | SPEN | 🔄 ODS + Files |
| 19 | UKPN-SPN | UK Power Networks (South Eastern) | SPN | SEEB | J | South Eastern | UKPN | ✅ ODS API |
| 20 | SSE-SEPD | Southern Electric Power Distribution | SEPD | SOUT | H | Southern | SSEN | 📄 Files |
| 21 | NGED-SWales | National Grid Electricity Distribution – South Wales | SWALES | SWAE | K | South Wales | NGED | 📄 Files |
| 22 | NGED-SW | National Grid Electricity Distribution – South West | SWEST | SWEB | L | South Western | NGED | 📄 Files |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | Y | YELG | M | Yorkshire | NPg | 🔄 ODS + Files |

---

## Download Status (2025-10-29)

### ✅ Successfully Retrieved (3 DNOs via ODS API)

**UK Power Networks (3 licenses):**
- ✅ EPN (Eastern) - 243 records from ODS API
- ✅ LPN (London) - 243 records from ODS API
- ✅ SPN (South Eastern) - 243 records from ODS API

**ODS Dataset ID:** `ukpn-distribution-use-of-system-charges-annex-1`  
**API URL:** https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/  
**Data Stored:** `data/duos/ods_api/[EPN|LPN|SPN]_ods_data.json`

### 📥 Partial Success (2 DNOs - 8 files downloaded)

**SSEN Distribution (2 licenses):**
- 🟡 SHEPD (North Scotland) - 4 PDF files downloaded
- 🟡 SEPD (Southern) - 4 PDF files downloaded

**Files:** Connection methodology documents (need actual charging statement Excel files)  
**Note:** These appear to be connection policy docs, not annual charging schedules

### ⏳ Pending - ODS Dataset Discovery Required (4 DNOs)

**Northern Powergrid (2 licenses):**
- ⚠️ NE (North East) - ODS dataset ID unknown
- ⚠️ Y (Yorkshire) - ODS dataset ID unknown
- **Portal:** https://northernpowergrid.opendatasoft.com/
- **Action Required:** Browse portal to find DUoS dataset ID

**Electricity North West (1 license):**
- ⚠️ ENWL (North West) - ODS dataset ID unknown
- **Portal:** https://electricitynorthwest.opendatasoft.com/
- **Action Required:** Browse portal to find DUoS dataset ID

**SP Energy Networks (2 licenses):**
- ⚠️ SPD (South Scotland) - ODS dataset ID unknown
- ⚠️ SPM (Merseyside & North Wales) - ODS dataset ID unknown
- **Portal:** https://spenergynetworks.opendatasoft.com/
- **Action Required:** Browse portal to find DUoS dataset ID

### 🔍 Pending - Website Scraping Required (4 DNOs)

**National Grid Electricity Distribution (4 licenses):**
- 🔴 EMID (East Midlands) - No files found in Drive
- 🔴 WMID (West Midlands) - No files found in Drive
- 🔴 SWALES (South Wales) - No files found in Drive
- 🔴 SWEST (South West) - No files found in Drive

**Source URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-statements-archive  
**Action Required:** Download from NGED website directly

---

## Data Source Details by Company Group

### Group 1: UK Power Networks ✅ COMPLETE

**Licenses:** EPN (10), LPN (12), SPN (19)  
**Status:** ✅ 100% Complete (243 records each)

**ODS API Configuration:**
```python
url = "https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/"
params = {
    'dataset': 'ukpn-distribution-use-of-system-charges-annex-1',
    'rows': 10000,
    'refine.licence': '[EPN|LPN|SPN]'
}
```

**Data Fields:**
- licence (EPN/LPN/SPN)
- charging_year (e.g., "2024/25")
- band (Red/Amber/Green)
- day_type (Weekday/Weekend)
- start_time (HH:MM)
- end_time (HH:MM)
- unit_rate_p_per_kwh
- voltage_class (LV/HV)

**Next Steps:**
- ✅ Data already downloaded
- Parse JSON files
- Extract time bands and rates
- Normalize to schema

---

### Group 2: National Grid Electricity Distribution (NGED) 🔴 PENDING

**Licenses:** EMID (11), WMID (14), SWALES (21), SWEST (22)  
**Status:** 🔴 0% Complete - Need to download from website

**Source:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-statements-archive

**Document Structure:**
- Annual "Schedule of Charges" Excel workbooks (one per license per year)
- Annex 1: Time-of-Use Periods (Red/Amber/Green time windows)
- Annex X: Half-Hourly Unit Rates tables (p/kWh by voltage level)
- Mapping varies by license: UR1/UR2/UR3 → R/A/G

**Action Required:**
1. Navigate to NGED charging statements archive
2. Download Excel files for each license area (EMID, WMID, SWALES, SWEST)
3. Download years 2016/17 through 2025/26
4. Parse Annex 1 (time bands) + Unit Rate tables

**Alternative - NGED Connected Data Portal:**
- URL: https://connecteddata.nationalgrid.co.uk/
- May have API access to charging data
- Requires investigation

---

### Group 3: Northern Powergrid ⚠️ ODS DISCOVERY REQUIRED

**Licenses:** NE (15), Y (23)  
**Status:** ⚠️ 0% - ODS dataset ID unknown

**ODS Portal:** https://northernpowergrid.opendatasoft.com/

**Action Required:**
1. Browse ODS portal datasets
2. Look for: "DUoS", "Charges", "Schedule", "Use of System"
3. Identify dataset ID for each license (NE, Y)
4. Test API endpoint with sample queries
5. Update `ODS_DATASETS` dict in `download_all_duos.py`

**Fallback - Website Download:**
- URL: https://www.northernpowergrid.com/use-of-system-charges
- "Charging and Connection Documents" section
- Download Excel/PDF files per license per year

---

### Group 4: Electricity North West ⚠️ ODS DISCOVERY REQUIRED

**License:** ENWL (16)  
**Status:** ⚠️ 0% - ODS dataset ID unknown

**ODS Portal:** https://electricitynorthwest.opendatasoft.com/

**Action Required:**
1. Browse ODS portal datasets
2. Look for DUoS/charging datasets
3. Identify dataset ID
4. Test API endpoint
5. Update script with dataset ID

**Fallback - Website Download:**
- URL: https://www.enwl.co.uk/about-us/regulatory-information/use-of-system-charges/
- Historic charges section links to year-specific folders
- Download Excel schedules for 2016/17 onwards

---

### Group 5: SP Energy Networks ⚠️ ODS DISCOVERY REQUIRED

**Licenses:** SPD (18), SPM (13)  
**Status:** ⚠️ 0% - ODS dataset ID unknown + Google Docs issue

**ODS Portal:** https://spenergynetworks.opendatasoft.com/

**Action Required:**
1. Browse ODS portal datasets
2. Identify dataset IDs for SPD and SPM
3. Test API endpoints
4. Update script

**Google Drive Issue:**
- Found 1 file but it's a Google Doc (not downloadable binary)
- Error: "Only files with binary content can be downloaded"
- Need to download directly from SPEN website instead

**Website Download:**
- URL: https://www.spenergynetworks.co.uk/pages/distribution_code.aspx
- Look for "Use of System Charges" or "Charging Statements"
- Download Excel files per license (SPD, SPM) per year

---

### Group 6: SSEN Distribution 🟡 PARTIAL - Need Annual Schedules

**Licenses:** SHEPD (17), SEPD (20)  
**Status:** 🟡 Partial - Downloaded 8 PDFs but they are connection methodology docs

**Downloaded Files:**
- 4 PDFs for SHEPD (connection methodology)
- 4 PDFs for SEPD (connection methodology)
- ❌ NOT the annual "Schedule of Charges" Excel files we need

**Correct Sources:**
- **SHEPD:** https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/scottish-hydro-electric-power-distribution/
- **SEPD:** https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/southern-electric-power-distribution/

**Action Required:**
1. Navigate to SSEN library pages (above)
2. Find "Schedule of Charges" or "Statement of Use of System Charges"
3. Download Excel files for years 2016/17 through 2025/26
4. Look for files like "SHEPD_Schedule_of_Charges_2024-25.xlsx"

---

## Data Schema (Target Format)

All downloaded data will be normalized to this schema for `duos_rates_times.csv`:

```csv
licence,dno_group,charging_year,band,day_type,start_time,end_time,unit_rate_p_per_kwh,voltage_class,valid_from,valid_to,source_url,source_format,last_seen_utc
EPN,UKPN,2024/25,red,weekday,16:00,19:00,12.345,LV,2024-04-01,2025-03-31,https://ukpowernetworks.opendatasoft.com,json,2025-10-29T18:38:00Z
LPN,UKPN,2024/25,amber,weekday,07:00,16:00,8.765,LV,2024-04-01,2025-03-31,https://ukpowernetworks.opendatasoft.com,json,2025-10-29T18:38:00Z
...
```

**Field Definitions:**
- `licence`: Short code (EPN, LPN, SPN, etc.)
- `dno_group`: Company group (UKPN, NGED, NPg, ENWL, SPEN, SSEN)
- `charging_year`: Format "YYYY/YY" (e.g., "2024/25")
- `band`: red | amber | green
- `day_type`: weekday | weekend | all
- `start_time`: HH:MM format (24-hour)
- `end_time`: HH:MM format (24-hour)
- `unit_rate_p_per_kwh`: Numeric rate in pence per kWh
- `voltage_class`: LV (Low Voltage) | HV (High Voltage) | EHV (Extra High Voltage)
- `valid_from`: ISO date (charging year start, usually April 1)
- `valid_to`: ISO date (charging year end, usually March 31)
- `source_url`: Original data source URL
- `source_format`: json | csv | xlsx | pdf
- `last_seen_utc`: UTC timestamp of data extraction

---

## Next Actions Priority List

### Priority 1: Complete UKPN Data Parsing ✅
**Status:** Downloaded, ready to parse  
**Files:** `data/duos/ods_api/[EPN|LPN|SPN]_ods_data.json`  
**Action:** Create `parse_ukpn_ods.py` to extract and normalize

### Priority 2: Download NGED Charging Statements 🔴
**Status:** Not started  
**Licenses:** EMID, WMID, SWALES, SWEST  
**Action:** Create web scraper or manual download from NGED archive

### Priority 3: Discover ODS Datasets ⚠️
**Status:** Awaiting investigation  
**DNOs:** NPg, ENWL, SPEN  
**Action:** Browse each ODS portal, identify dataset IDs

### Priority 4: Download SSEN Annual Schedules 🟡
**Status:** Wrong files downloaded  
**Licenses:** SHEPD, SEPD  
**Action:** Download actual "Schedule of Charges" Excel files from SSEN website

### Priority 5: Create Master CSV 📊
**Status:** Pending completion of downloads  
**Action:** Parse all sources, normalize, merge into `duos_rates_times.csv`

### Priority 6: Upload to BigQuery 💾
**Status:** Pending master CSV creation  
**Table:** `inner-cinema-476211-u9.uk_energy_prod.duos_rates`

### Priority 7: Add to Dashboard 📈
**Status:** Pending BigQuery upload  
**Cell:** A14 - Display current DUoS band based on time of day

---

## Technical Notes

### ODS API Rate Limits
- **Limit:** ~10,000 requests/day per IP
- **Current Usage:** 3 requests (minimal)
- **Mitigation:** Cache responses, use batch queries

### File Parsing Challenges

**Excel (XLSX):**
- Different layouts between DNOs
- Different layouts between years for same DNO
- Annex numbers vary (Annex 1, Annex 2, Appendix A, etc.)
- Unit rate column names vary (UR1/UR2/UR3, Rate 1/Rate 2/Rate 3, Red/Amber/Green)
- Requires flexible parsing with pattern matching

**PDF:**
- Last resort for older years
- Use pdfplumber or tabula-py
- Table extraction more error-prone
- Manual validation required

### Validation Rules

**Time Coverage:**
- Red + Amber + Green should cover full 24 hours
- Weekday vs Weekend may differ
- No gaps or overlaps allowed

**Rate Reasonableness:**
- LV rates typically: 1-30 p/kWh
- HV rates typically: 0.5-15 p/kWh
- Flag outliers for manual review

**Year Completeness:**
- All 14 DNOs should have data for each year 2016/17 onwards
- Track coverage in completion matrix

---

## Completion Matrix

| DNO | 16/17 | 17/18 | 18/19 | 19/20 | 20/21 | 21/22 | 22/23 | 23/24 | 24/25 | 25/26 | Status |
|-----|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|--------|
| EPN | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | Downloaded |
| LPN | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | Downloaded |
| SPN | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | Downloaded |
| EMID | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Pending |
| WMID | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Pending |
| SWALES | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Pending |
| SWEST | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Pending |
| NE | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ODS Discovery |
| Y | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ODS Discovery |
| ENWL | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ODS Discovery |
| SPD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ODS Discovery |
| SPM | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ODS Discovery |
| SHEPD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Wrong Files |
| SEPD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Wrong Files |

**Legend:**
- ✅ Parsed and validated
- ⏳ Downloaded, pending parsing
- ❌ Not yet downloaded
- ⚠️ Partial/incorrect data

**Overall Progress:** 21.4% (3/14 DNOs with data)

---

## References

**Documentation:**
- See `CLAUDE_duos.md` for detailed DUoS methodology
- See `CLAUDE_energy_data.md` for complete energy data overview

**Downloaded Data:**
- ODS API data: `data/duos/ods_api/`
- Charging statements: `data/duos/charging_statements/`
- Download summary: `data/duos/download_summary_20251029_183849.json`

**Scripts:**
- Download all: `download_all_duos.py`
- Parse UKPN: `parse_ukpn_ods.py` (to be created)
- Parse NGED: `parse_nged_excel.py` (to be created)
- Normalize all: `normalize_duos_data.py` (to be created)

---

**Last Updated:** 2025-10-29 18:38 UTC  
**Next Review:** After ODS dataset discovery completion
