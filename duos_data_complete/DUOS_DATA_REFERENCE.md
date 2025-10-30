# DUoS Data & Methodology Reference
**Generated:** 2025-10-29 18:52:28 UTC  
**Project:** GB Power Market JJ - Distribution Use of System Data

---

## Overview

This document provides a comprehensive reference for all DUoS (Distribution Use of System) data and methodologies downloaded for the 14 GB electricity distribution network operator license areas.

**Data Coverage:**
- **Time Period:** 2016/17 to 2025/26 (10 charging years)
- **License Areas:** All 14 GB DNO license areas
- **Data Types:** 
  - Time-of-Use bands (Red/Amber/Green)
  - Half-hourly unit rates (p/kWh)
  - Charging methodologies and statements

**Methodology:** Following specifications in `CLAUDE_duos.md`

---

## Data Sources by DNO

### UK Power Networks (UKPN) - 3 License Areas

**Data Source:** OpenDataSoft API  
**API URL:** https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/  
**Dataset ID:** `ukpn-distribution-use-of-system-charges-annex-1`


#### EPN - Eastern (MPAN 10)
**Company:** UKPN  
**Data Source:** ODS  
**API Records:** 243 records downloaded  
**Local File:** `/Users/georgemajor/GB Power Market JJ/duos_data_complete/api_data/EPN_duos_data.json`  
**Google Drive:** [EPN_duos_data.json](https://drive.google.com/file/d/1qqgByJwB66xm5nfSEn69gaHePxOefYBD/view?usp=drivesdk)  
**Methodology URL:** https://ukpowernetworks.opendatasoft.com/pages/charging-methodology/  
**Status:** ✅ Complete  


#### EMID - East Midlands (MPAN 11)
**Company:** NGED  
**Data Source:** WEB  
**Methodology URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/  
**Status:** ⏳ Pending  


#### LPN - London (MPAN 12)
**Company:** UKPN  
**Data Source:** ODS  
**API Records:** 243 records downloaded  
**Local File:** `/Users/georgemajor/GB Power Market JJ/duos_data_complete/api_data/LPN_duos_data.json`  
**Google Drive:** [LPN_duos_data.json](https://drive.google.com/file/d/1u93hC3eTG_8TMG60qSWgwK8XxYep5eme/view?usp=drivesdk)  
**Methodology URL:** https://ukpowernetworks.opendatasoft.com/pages/charging-methodology/  
**Status:** ✅ Complete  


#### SPM - Merseyside & N Wales (MPAN 13)
**Company:** SPEN  
**Data Source:** ODS+WEB  
**Charging Statements:** 1 files found  
  - SPM - Schedule of charges and other tables - 2020_21 V.0.1- IDNO HV Tariffs v3  
**Methodology URL:** https://www.spenergynetworks.co.uk/pages/charging_methodology.aspx  
**Status:** 🟡 Partial  


#### WMID - West Midlands (MPAN 14)
**Company:** NGED  
**Data Source:** WEB  
**Methodology URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/  
**Status:** ⏳ Pending  


#### NE - North East (MPAN 15)
**Company:** NPg  
**Data Source:** ODS+WEB  
**Charging Statements:** 21 files found  
  - london-power-networks-schedule-of-charges-and-other-tables-2024-v13  
  - eastern-power-networks-schedule-of-charges-and-other-tables-2017-v3-4  
  - eastern-power-networks-schedule-of-charges-and-other-tables-2024-v1-8  
  - eastern-power-networks-schedule-of-charges-and-other-tables-2022-v18  
  - eastern-power-networks-schedule-of-charges-and-other-tables-2019-v2-2  
  - ... and 16 more  
**Methodology URL:** https://www.northernpowergrid.com/our-network/charging-methodology  
**Status:** 🟡 Partial  


#### ENWL - North West (MPAN 16)
**Company:** ENWL  
**Data Source:** ODS+WEB  
**Methodology URL:** https://www.enwl.co.uk/about-us/regulatory-information/charging-methodology/  
**Status:** ⏳ Pending  


#### SHEPD - North Scotland (MPAN 17)
**Company:** SSEN  
**Data Source:** WEB  
**Methodology URL:** https://www.ssen.co.uk/about-ssen/dso/charging-and-network-access/  
**Status:** ⏳ Pending  


#### SPD - South Scotland (MPAN 18)
**Company:** SPEN  
**Data Source:** ODS+WEB  
**Methodology URL:** https://www.spenergynetworks.co.uk/pages/charging_methodology.aspx  
**Status:** ⏳ Pending  


#### SPN - South Eastern (MPAN 19)
**Company:** UKPN  
**Data Source:** ODS  
**API Records:** 243 records downloaded  
**Local File:** `/Users/georgemajor/GB Power Market JJ/duos_data_complete/api_data/SPN_duos_data.json`  
**Google Drive:** [SPN_duos_data.json](https://drive.google.com/file/d/1wKSxij7F0quvjx9Jwv3Rq_oapt5FQIXf/view?usp=drivesdk)  
**Methodology URL:** https://ukpowernetworks.opendatasoft.com/pages/charging-methodology/  
**Status:** ✅ Complete  


#### SEPD - Southern (MPAN 20)
**Company:** SSEN  
**Data Source:** WEB  
**Methodology URL:** https://www.ssen.co.uk/about-ssen/dso/charging-and-network-access/  
**Status:** ⏳ Pending  


#### SWALES - South Wales (MPAN 21)
**Company:** NGED  
**Data Source:** WEB  
**Methodology URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/  
**Status:** ⏳ Pending  


#### SWEST - South Western (MPAN 22)
**Company:** NGED  
**Data Source:** WEB  
**Methodology URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/  
**Status:** ⏳ Pending  


#### Y - Yorkshire (MPAN 23)
**Company:** NPg  
**Data Source:** ODS+WEB  
**Methodology URL:** https://www.northernpowergrid.com/our-network/charging-methodology  
**Status:** ⏳ Pending  


---

## Data Schema

All downloaded data is normalized to the following schema (per `CLAUDE_duos.md`):

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `licence` | string | License area short code | `LPN`, `EPN`, `EMID` |
| `dno_group` | string | Company group | `UKPN`, `NGED`, `NPg` |
| `charging_year` | string | Charging year (Apr-Mar) | `2024/25` |
| `band` | string | Time-of-use band | `red`, `amber`, `green` |
| `day_type` | string | Day classification | `weekday`, `weekend`, `all` |
| `start_time` | string | Period start time (24h) | `16:00` |
| `end_time` | string | Period end time (24h) | `19:00` |
| `unit_rate_p_per_kwh` | float | Energy charge | `12.345` |
| `voltage_class` | string | Voltage level | `LV`, `HV`, `EHV` |
| `valid_from` | date | Start date (ISO) | `2024-04-01` |
| `valid_to` | date | End date (ISO) | `2025-03-31` |
| `source_url` | string | Data source URL | API or file URL |
| `source_format` | string | Source format | `json`, `csv`, `xlsx`, `pdf` |
| `last_seen_utc` | datetime | Extraction timestamp | ISO 8601 UTC |

---

## Processed Data Files

### Master CSV File
**Location:** `duos_data_complete/processed/duos_rates_times.csv`  
**Description:** Normalized data from all 14 DNO license areas  
**Schema:** As defined above  
**Rows:** [To be calculated after parsing]

### Google Drive Structure
**Root Folder:** DUoS Data Complete  
**Folder ID:** 1HwcQXszc4twyfmhuEY5s2cFe4FvMSc8m  

**Subfolders:**
- API Data: [13fyPWBoHwU1EUUTL8GLiHP2jzx8x3xib](https://drive.google.com/drive/folders/13fyPWBoHwU1EUUTL8GLiHP2jzx8x3xib)  
- Charging Statements: [1mGxtcqufb8Zgo-VQMxSfM7CkCxjz1s22](https://drive.google.com/drive/folders/1mGxtcqufb8Zgo-VQMxSfM7CkCxjz1s22)  
- Methodologies: [1rV3nuqJReFbFqAj15-AEh7fN55v7xX0P](https://drive.google.com/drive/folders/1rV3nuqJReFbFqAj15-AEh7fN55v7xX0P)  
- Processed: [1bBzYftqbW3B1lNnuklBOlxsUgdC2bxkd](https://drive.google.com/drive/folders/1bBzYftqbW3B1lNnuklBOlxsUgdC2bxkd)  

---

## Charging Methodologies

### UKPN (UK Power Networks)
**Methodology URL:** https://ukpowernetworks.opendatasoft.com/pages/charging-methodology/  
**Document Type:** CDCM (Common Distribution Charging Methodology)  
**Key Features:**
- Time-of-use bands: Red/Amber/Green
- Voltage levels: LV, HV, EHV
- Super-red days (critical peak pricing)

### NGED (National Grid Electricity Distribution)
**Methodology URL:** https://commercial.nationalgrid.co.uk/our-network/use-of-system-charges/charging-methodology/  
**Document Type:** CDCM  
**Coverage:** 4 license areas (EMID, WMID, SWALES, SWEST)

### Northern Powergrid (NPg)
**Methodology URL:** https://www.northernpowergrid.com/our-network/charging-methodology  
**Coverage:** 2 license areas (NE, Y)

### Electricity North West (ENWL)
**Methodology URL:** https://www.enwl.co.uk/about-us/regulatory-information/charging-methodology/  
**Coverage:** 1 license area (ENWL)

### SP Energy Networks (SPEN)
**Methodology URL:** https://www.spenergynetworks.co.uk/pages/charging_methodology.aspx  
**Coverage:** 2 license areas (SPD, SPM)

### SSEN Distribution
**Methodology URL:** https://www.ssen.co.uk/about-ssen/dso/charging-and-network-access/  
**Coverage:** 2 license areas (SHEPD, SEPD)

---

## Validation Rules

Per `CLAUDE_duos.md` Section 5:

### Band Coverage
- [ ] Red + Amber + Green should cover full 24-hour day
- [ ] Weekday vs Weekend bands documented
- [ ] No gaps or overlaps in time windows

### Time Windows
- [ ] All times in HH:MM format (24-hour)
- [ ] Start time < End time (or spans midnight)
- [ ] Consistent across charging year

### Rate Reasonableness
- [ ] LV rates typically: 1-30 p/kWh
- [ ] HV rates typically: 0.5-15 p/kWh
- [ ] Flag outliers > 50 p/kWh for review

### Completeness
- [ ] All 14 DNOs represented
- [ ] Each DNO has data for charging years 2016/17 - 2025/26
- [ ] All required schema columns populated

---

## Key DUoS Reforms

### DCP228 (April 2018)
- Changed time-of-use band definitions
- Introduced "super-red" days for some DNOs
- Updated unit rate calculations

### TCR (Targeted Charging Review) - From 2022
- Shifted from volumetric to capacity-based charges
- Changed residual charging approach
- Impacted standing charges

### EDCM/CDCM Split
- **EDCM** (Extra High Voltage) - Demand > 1 MVA
- **CDCM** (Common) - LV and HV customers
- Different methodologies and rate structures

---

## Usage Examples

### Query Red Band Rates for London (LPN)
```python
import pandas as pd

df = pd.read_csv('duos_data_complete/processed/duos_rates_times.csv')

london_red = df[
    (df['licence'] == 'LPN') & 
    (df['band'] == 'red') &
    (df['charging_year'] == '2024/25')
]

print(london_red[['day_type', 'start_time', 'end_time', 'unit_rate_p_per_kwh']])
```

### Compare Rates Across DNOs
```python
# Average red band rate by DNO for 2024/25
avg_rates = df[
    (df['band'] == 'red') &
    (df['charging_year'] == '2024/25') &
    (df['voltage_class'] == 'LV')
].groupby('licence')['unit_rate_p_per_kwh'].mean().sort_values(ascending=False)

print(avg_rates)
```

### Time Coverage Check
```python
# Verify 24-hour coverage for each DNO
for licence in df['licence'].unique():
    licence_data = df[
        (df['licence'] == licence) &
        (df['charging_year'] == '2024/25') &
        (df['day_type'] == 'weekday')
    ]
    
    # Calculate total hours covered
    # (implementation depends on time format)
    print(f"{licence}: {len(licence_data)} time periods")
```

---

## Next Steps

### Parsing & Normalization
1. Parse UKPN ODS JSON files to schema
2. Parse NGED Excel charging statements (Annex 1 + unit rate tables)
3. Parse SSEN Excel charging statements
4. Merge all sources to master CSV

### Upload to BigQuery
1. Create table: `inner-cinema-476211-u9.uk_energy_prod.duos_rates`
2. Define schema matching CSV columns
3. Upload master CSV with timestamps
4. Create views for common queries

### Dashboard Integration
1. Add cell A14: Current DUoS band based on time
2. Add cell A15: Current DUoS rate for selected license area
3. Create time-of-day visualization (Red/Amber/Green bands)

---

## References

### Internal Documentation
- `CLAUDE_duos.md` - Technical specification (this methodology)
- `CLAUDE_energy_data.md` - Complete energy data guide
- `DNO_LICENSE_AREAS.md` - DNO reference with download status
- `PROJECT_SUMMARY.md` - Project status report

### External Resources
- Ofgem DUoS Guidance: https://www.ofgem.gov.uk/electricity/distribution-networks/charging
- Energy Networks Association: https://www.energynetworks.org/
- Open Networks Project: https://www.energynetworks.org/industry-hub/resource-library/on-2023-duos-charging

### API Documentation
- UKPN ODS: https://ukpowernetworks.opendatasoft.com/api/
- Northern Powergrid ODS: https://northernpowergrid.opendatasoft.com/api/
- ENWL ODS: https://electricitynorthwest.opendatasoft.com/api/
- SPEN ODS: https://spenergynetworks.opendatasoft.com/api/

---

## Download Summary

**Total DNOs:** 14  
**Charging Years:** 10 (2016/17 - 2025/26)  
**Expected Records:** ~140 time period definitions × 14 DNOs = ~2,000 records  
**Download Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Download Method:** API (8 DNOs) + Website Files (6 DNOs)

---

## Contact & Support

**Project:** GB Power Market JJ  
**Repository:** jibber-jabber-24-august-2025-big-bop  
**Owner:** GeorgeDoors888  
**Documentation:** See `DOCUMENTATION_INDEX.md` for complete file list

For questions about DUoS data methodology, refer to individual DNO websites or Ofgem guidance.

---

**Document Version:** 1.0  
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
