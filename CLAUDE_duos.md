
# CLAUDE.md — GB DUoS R/A/G (2016→Present) Harvester
**Goal:** Ingest **Distribution Use of System (DUoS)** **Red/Amber/Green** band **time windows** and **unit rates (p/kWh)** for **all 14 GB licence areas**, 2016 → present, and normalise to one tidy table for analysis (CSV + Google Sheets).

> DUoS rates/time-bands are published by each **DNO licence** (not one value per company). Some DNOs expose **OpenDataSoft (ODS)** APIs (UKPN, NPg, ENWL, SPEN). Others (NGED, SSEN Distribution) publish **annual “Schedule of charges and other tables”** (Excel/PDF). This project pulls **API data where available** and **downloads+parses** the rest.

---

## 0) Licence Areas (14)
| ID | Licence (short) | Company |
|---:|---|---|
| 10 | EPN (UKPN-Eastern) | UK Power Networks |
| 12 | LPN (UKPN-London) | UK Power Networks |
| 19 | SPN (UKPN-South Eastern) | UK Power Networks |
| 11 | EMID | National Grid Electricity Distribution (NGED) |
| 14 | WMID | NGED |
| 21 | SWALES | NGED |
| 22 | SWEST | NGED |
| 15 | NE (NEDL) | Northern Powergrid (NPg) |
| 23 | Y (YEDL) | Northern Powergrid (NPg) |
| 16 | ENWL | Electricity North West (ENWL) |
| 18 | SPD | SP Energy Networks (SPEN) |
| 13 | SPM | SP Energy Networks (SPEN) |
| 17 | SHEPD | SSEN Distribution |
| 20 | SEPD | SSEN Distribution |

---

## 1) Output Schema (single tidy table)
**File:** `duos_rates_times.csv`

| column | type | example |
|---|---|---|
| `licence` | string | LPN, EPN, etc. |
| `dno_group` | string | UKPN / NGED / NPg / ENWL / SPEN / SSEN |
| `charging_year` | string | `2016/17` |
| `band` | string | `red` / `amber` / `green` |
| `day_type` | string | `weekday` / `weekend` / `all` |
| `start_time` | string | `16:00` |
| `end_time` | string | `19:00` |
| `unit_rate_p_per_kwh` | float | 12.345 |
| `voltage_class` | string | LV / HV (per publication table) |
| `valid_from` | date | ISO (usually 01-Apr) |
| `valid_to` | date | ISO (usually 31-Mar) |
| `source_url` | string | statement/API URL |
| `source_format` | string | `json` / `csv` / `xlsx` / `pdf` |
| `last_seen_utc` | datetime | ingestion timestamp |

Notes:
- Time bands are in **Annex 1 (Time Periods)** of each licence’s schedule.
- Unit rates are in **HH demand tables** (CDCM). Map tables to R/A/G bands per licence notes.

---

## 2) Data Sources (by DNO)
### A) **OpenDataSoft APIs** (JSON/CSV)
Use when available; no scraping required.

- **UK Power Networks (EPN/LPN/SPN)**  
  ODS portal: `https://ukpowernetworks.opendatasoft.com/pages/home/`  
  **Annex 1 dataset**: `ukpn-distribution-use-of-system-charges-annex-1`  
  API (JSON):  
  ```
  https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/?dataset=ukpn-distribution-use-of-system-charges-annex-1&rows=1000
  ```

- **Northern Powergrid (NE/Y)**  
  ODS portal: `https://northernpowergrid.opendatasoft.com/pages/home/`  
  (Inspect portal for DUoS/charging datasets; some require login.)

- **Electricity North West (ENWL)**  
  ODS portal home: `https://electricitynorthwest.opendatasoft.com/pages/homepage/`

- **SP Energy Networks (SPD/SPM)**  
  ODS portal home: `https://spenergynetworks.opendatasoft.com/pages/home/`

> For each ODS dataset: open its **“API”** tab to view field names. Keep a **mapping** file if names differ by year.

---

### B) **Charging Statement Libraries** (Excel/PDF)
Use for licences without ODS data or to complete historical backfill (2016→).

- **NGED (EMID/WMID/SWALES/SWEST)**  
  Charging statements + archive (Excel/PDF):  
  `https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-statements-archive`

- **SSEN Distribution (SHEPD, SEPD)**  
  SHEPD library: `https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/scottish-hydro-electric-power-distribution/`  
  SEPD library:  `https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/southern-electric-power-distribution/`

- **Northern Powergrid (NE/Y)**  
  Library: `https://www.northernpowergrid.com/use-of-system-charges` (and document library/charges)

- **Electricity North West (ENWL)**  
  UoS charges (historic pages link to year folders):  
  `https://www.enwl.co.uk/about-us/regulatory-information/use-of-system-charges/`

- **SP Energy Networks (SPD/SPM)**  
  Connections / Use-of-System & Statements section (per-year schedules).

> In each workbook: **Annex 1 / Time Periods** = band times (weekday/weekend). The **HH unit-rate tables** give p/kWh; some licences express **Unit Rate 1/2/3** mapping to R/A/G in notes—capture that mapping.

---

## 3) API Patterns

### OpenDataSoft (generic)
```http
GET /api/records/1.0/search/
  ?dataset=<DATASET_ID>
  &rows=1000
  &refine.<field>=<value>      # optional filters (e.g. licence=LPN, year=2024/25)
```

### CKAN (for catalog search e.g., data.gov.uk or NGED Connected Data)
```http
GET https://data.gov.uk/api/3/action/package_search?q="use of system" AND (duos OR "charging statements" OR "schedule of charges")&rows=100
```

---

## 4) Ingestion Pipeline
```
src/
  sources/
    ukpn_ods.py         # fetch UKPN Annex 1 and related tables
    n_pg_ods.py         # NPg ODS (if DUoS datasets present)
    enwl_ods.py         # ENWL ODS (if DUoS datasets present)
    spen_ods.py         # SPEN ODS (if DUoS datasets present)
    ckan_search.py      # CKAN search helper (data.gov.uk/NGED Connected Data)
    dno_html.py         # scrape “charging statements” pages for file URLs
  parse/
    duos_excel.py       # parse XLSX: Annex 1 time bands + HH unit rates
    duos_pdf.py         # PDF table extraction fallback (pdfplumber/tabula)
  normalise/
    map_fields.py       # align ODS fields → schema
    map_bands.py        # unit rate columns (UR1/2/3) → R/A/G
  pipeline/
    run_all.py
config/
  licences.json         # 14 licences + DNO group + MPAN distributor ID
  datasets.json         # ODS dataset IDs + field mappings
  years.json            # 2016..present
output/
  duos_rates_times.csv
```

### Steps
1. **Discover**: ODS datasets per DNO (read `datasets.json`), and **Charging Statement** URLs per licence/year via HTML/CKAN.  
2. **Fetch**: API pull (ODS) or download file (XLSX/PDF).  
3. **Parse**: 
   - ODS: read JSON/CSV; extract `{licence, year, band, day_type, start_time, end_time, unit_rate_p_per_kwh, voltage_class}`.
   - XLSX: read **Annex 1** for time bands; read HH **unit rate** tables and map **UR1/2/3 → R/A/G**.
4. **Normalise**: add metadata (valid_from/to, source URL, format); enforce types/time.  
5. **Save**: append into `duos_rates_times.csv`.  
6. **Publish** (optional): push to Google Sheets (service account).

---

## 5) Validation
- **Band coverage**: Expect **weekday + weekend** rows per band where licences differentiate.  
- **Time windows**: Ensure **24h coverage** when combining bands + day-types.  
- **Rates check**: Compare annual totals vs the original workbook’s summary table.  
- **Change points**: Pay attention to **DCP228 (Apr-2018)** and **TCR reforms (from 2022)** which changed level/structure; **Annex 1 band times are the authority** for HH banding.

---

## 6) Example Code (Python)

### 6.1 UKPN (ODS) — Annex 1
```python
import requests, pandas as pd

URL = "https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/"
params = {"dataset": "ukpn-distribution-use-of-system-charges-annex-1", "rows": 1000}
js = requests.get(URL, params=params, timeout=30).json()
records = [r["fields"] | {"_src": r.get("recordid")} for r in js.get("records", [])]
df = pd.DataFrame(records)
# TODO: map field names (licence/year/band/start_time/end_time/rate_p_per_kwh/voltage_class)
```

### 6.2 CKAN search (catalog → files)
```python
import requests

CKAN = "https://data.gov.uk/api/3/action/package_search"
q = '"distribution use of system" AND (duos OR "charging statements" OR "schedule of charges")'
resp = requests.get(CKAN, params={"q": q, "rows": 100}, timeout=30).json()
datasets = resp.get("result", {}).get("results", [])
# Examine `resources` for file URLs (XLSX/PDF) per year/licence; then download.
```

### 6.3 Parse XLSX (Annex 1 + unit rates)
```python
import pandas as pd, re
from pathlib import Path

def load_sheets(xlsx_path: Path):
    xl = pd.ExcelFile(xlsx_path)
    frames = {s: xl.parse(s, header=None) for s in xl.sheet_names}
    return frames

def extract_timebands(frames):
    text = " ".join(map(str, pd.concat(frames.values(), axis=None).fillna("").astype(str).values.flatten()))
    out = []
    for band in ("Red","Amber","Green"):
        for m in re.finditer(rf"{band}[^\d]*(\d{{1,2}}:\d{{2}})[^\d]+(\d{{1,2}}:\d{{2}})", text, flags=re.I):
            out.append({"band": band.lower(), "start_time": m.group(1), "end_time": m.group(2)})
    return out
```

---

## 7) Scheduling (optional)
- **Python**: cron (e.g., daily in Oct–Mar; monthly otherwise).  
- **Google Apps Script**: time-based triggers to refresh the Google Sheet from the CSV.  

---

## 8) Known Gaps & Tips
- **NGED/SSEN**: no ODS DUoS datasets → rely on **charging statements** (2016→present).  
- **ODS field drift**: year-to-year schema changes; maintain `datasets.json` mappings.  
- **Units**: always store rates as **p/kWh**; confirm where some tables show **£/MWh**.  
- **Timezones**: store times in **local clock (HH:MM)** as published.

---

## 9) Licences & Reuse
- Check each portal’s **licence** (many ODS datasets are **CC BY 4.0**; PDFs/XLSX may have reuse terms).  
- This repository’s code is **MIT**; data remains © respective publishers.

---

## 10) Quick Smoke Test
1. Run UKPN ODS pull → confirm LPN/EPN/SPN rows with year & bands.  
2. Download **NGED WMID 2024/25** schedule → parse Annex 1 band times + HH unit rates.  
3. Append both results → `duos_rates_times.csv`.  
4. Spot-check against original tables.
