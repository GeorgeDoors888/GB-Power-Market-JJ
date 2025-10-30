# Distribution ID Quick Reference Card

## MPAN Structure
**MPAN (Meter Point Administration Number)**: `DD PPPP SSSS NNNN NNN CC`
- **DD** = Distribution ID (first 2 digits) - determines DNO license area
- **PPPP** = Profile Class
- **SSSS** = Meter Time Switch Code  
- **NNNN NNN** = Line Loss Factor Class and unique identifier
- **CC** = Check digits

## Distribution ID to DNO Mapping

| ID | DNO_Key | Short | MPID | GSP | Region | Files | Coverage |
|----|---------|-------|------|-----|--------|-------|----------|
| **10** | UKPN-EPN | EPN | EELC | A | Eastern | 29 | 2017-2026 ✅ |
| **11** | NGED-EM | EMID | EMEB | B | East Midlands | 17 | 2014-2026 ✅ |
| **12** | UKPN-LPN | LPN | LOND | C | London | 13 | 2017-2026 ✅ |
| **13** | SP-Manweb | SPM | MANW | D | Merseyside & N Wales | 23 | 2020-2026 ✅ |
| **14** | NGED-WM | WMID | MIDE | E | West Midlands | 17 | 2014-2026 ✅ |
| **15** | NPg-NE | NE | NEEB | F | North East | 0 | ❌ MISSING |
| **16** | ENWL | ENWL | NORW | G | North West | 48 | 2018-2026 ⚠️ |
| **17** | SSE-SHEPD | SHEPD | HYDE | P | North Scotland | 36 | 2020-2026 ✅ |
| **18** | SP-Distribution | SPD | SPOW | N | South Scotland | 19 | 2020-2026 ✅ |
| **19** | UKPN-SPN | SPN | SEEB | J | South Eastern | 1 | ⚠️ INCOMPLETE |
| **20** | SSE-SEPD | SEPD | SOUT | H | Southern | 40 | 2020-2026 ✅ |
| **21** | NGED-SWales | SWALES | SWAE | K | South Wales | 15 | 2014-2026 ✅ |
| **22** | NGED-SW | SWEST | SWEB | L | South Western | 17 | 2014-2026 ✅ |
| **23** | NPg-Y | Y | YELG | M | Yorkshire | 26 | 2017-2026 ✅ |

## GSP Groups (A-P, excluding I and O)

| GSP | Name | Distribution ID |
|-----|------|-----------------|
| **A** | Eastern | 10 (UKPN-EPN) |
| **B** | East Midlands | 11 (NGED-EM) |
| **C** | London | 12 (UKPN-LPN) |
| **D** | Merseyside & North Wales | 13 (SP-Manweb) |
| **E** | West Midlands | 14 (NGED-WM) |
| **F** | North East | 15 (NPg-NE) |
| **G** | North West | 16 (ENWL) |
| **H** | Southern | 20 (SSE-SEPD) |
| **J** | South Eastern | 19 (UKPN-SPN) |
| **K** | South Wales | 21 (NGED-SWales) |
| **L** | South Western | 22 (NGED-SW) |
| **M** | Yorkshire | 23 (NPg-Y) |
| **N** | South Scotland | 18 (SP-Distribution) |
| **P** | North Scotland | 17 (SSE-SHEPD) |

## Market Participant IDs (MPID)

| MPID | DNO | Distribution ID | Region |
|------|-----|-----------------|--------|
| **EELC** | UKPN-EPN | 10 | Eastern |
| **EMEB** | NGED-EM | 11 | East Midlands |
| **LOND** | UKPN-LPN | 12 | London |
| **MANW** | SP-Manweb | 13 | Merseyside & N Wales |
| **MIDE** | NGED-WM | 14 | West Midlands |
| **NEEB** | NPg-NE | 15 | North East |
| **NORW** | ENWL | 16 | North West |
| **HYDE** | SSE-SHEPD | 17 | North Scotland |
| **SPOW** | SP-Distribution | 18 | South Scotland |
| **SEEB** | UKPN-SPN | 19 | South Eastern |
| **SOUT** | SSE-SEPD | 20 | Southern |
| **SWAE** | NGED-SWales | 21 | South Wales |
| **SWEB** | NGED-SW | 22 | South Western |
| **YELG** | NPg-Y | 23 | Yorkshire |

## Example MPAN Decoding

### Example 1: `10 1234 5678 9012 345 67`
- **Distribution ID**: 10 → UKPN-EPN (Eastern Power Networks)
- **GSP Group**: A (Eastern)
- **Market Participant**: EELC
- **Charging Schedule**: Eastern Power Networks rates apply
- **Region**: Eastern England

### Example 2: `12 0456 1234 5678 901 23`
- **Distribution ID**: 12 → UKPN-LPN (London Power Networks)
- **GSP Group**: C (London)
- **Market Participant**: LOND
- **Charging Schedule**: London Power Networks rates apply
- **Region**: London and surrounding area

### Example 3: `22 3456 7890 1234 567 89`
- **Distribution ID**: 22 → NGED-SW (South West)
- **GSP Group**: L (South Western)
- **Market Participant**: SWEB
- **Charging Schedule**: NGED South West (formerly WPD South West) rates apply
- **Region**: Devon, Cornwall, Somerset, parts of Wiltshire

## DNO Group Structure

### National Grid Electricity Distribution (NGED)
Formerly Western Power Distribution (WPD)
- **ID 11**: East Midlands (EMID/EMEB) - GSP B
- **ID 14**: West Midlands (WMID/MIDE) - GSP E
- **ID 21**: South Wales (SWALES/SWAE) - GSP K
- **ID 22**: South West (SWEST/SWEB) - GSP L

**Total**: 4 license areas, 66 charging files, 13 years coverage (2014-2026)

### UK Power Networks (UKPN)
- **ID 10**: Eastern (EPN/EELC) - GSP A
- **ID 12**: London (LPN/LOND) - GSP C
- **ID 19**: South Eastern (SPN/SEEB) - GSP J ⚠️ (1 file only)

**Total**: 3 license areas, 43 charging files (42 + 1), 10 years coverage (2017-2026)

### Scottish and Southern Electricity Networks (SSEN)
- **ID 17**: Scottish Hydro Electric Power Distribution (SHEPD/HYDE) - GSP P
- **ID 20**: Southern Electric Power Distribution (SEPD/SOUT) - GSP H

**Total**: 2 license areas, 76 charging files, 7 years coverage (2020-2026)

### SP Energy Networks (SPEN)
- **ID 13**: SP Manweb (SPM/MANW) - GSP D
- **ID 18**: SP Distribution (SPD/SPOW) - GSP N

**Total**: 2 license areas, 42 charging files, 7 years coverage (2020-2026)

### Northern Powergrid (NPg)
- **ID 15**: North East (NE/NEEB) - GSP F ❌ (no files)
- **ID 23**: Yorkshire (Y/YELG) - GSP M

**Total**: 2 license areas, 26 charging files (0 + 26), 7 years coverage (2017-2026)

### Electricity North West (ENWL)
- **ID 16**: North West (ENWL/NORW) - GSP G

**Total**: 1 license area, 48 charging files, spotty coverage (2018-2026)

## File Naming Patterns by DNO

### NGED (IDs 11, 14, 21, 22)
**Pattern**: `[MPID]-Schedule-of-charges-and-other-tables-[YEAR]-[VERSION].xlsx`

**Examples**:
- `EMEB-Schedule-of-charges-and-other-tables-2025-V.0.2-for-publishing.xlsx`
- `MIDE-Schedule-of-charges-and-other-tables-2024-V.0.1-for-publishing.xlsx`
- `SWAE-Schedule-of-charges-and-other-tables-2023-V.0.1-for-publishing.xlsx`
- `SWEB-Schedule-of-charges-and-other-tables-2022-V.0.1.xlsx`

### UKPN (IDs 10, 12, 19)
**Pattern**: `[region]-power-networks-schedule-of-charges-and-other-tables-[YEAR]-[VERSION].xlsx`

**Examples**:
- `eastern-power-networks-schedule-of-charges-and-other-tables-2025-v1-6.xlsx`
- `london-power-networks-schedule-of-charges-and-other-tables-2024-v13.xlsx`
- `south-eastern-power-networks-schedule-of-charges-and-other-tables-2023-v1-5.xlsx`

### SSEN (IDs 17, 20)
**Pattern**: `[short_code]---schedule-of-charges-and-other-tables_april-[YEAR]_[VERSION].xlsx`

**Examples**:
- `shepd---schedule-of-charges-and-other-tables_april-2025_v0.2.xlsx`
- `sepd---schedule-of-charges-and-other-tables_april-2024_v1.2.xlsx`

**Additional Files**:
- Embedded networks: `[short_code]---schedule-of-charges-and-other-tables-embedded-networks-april-[YEAR]_[VERSION].xlsx`
- CDCM models: `[short_code]_cdcm_v[X]_[DATE]_[YEAR-YEAR]_[STATUS].xlsx`

### SPEN (IDs 13, 18)
**Pattern**: `[SHORT]-Schedule-of-charges-and-other-tables-[YEAR]-[VERSION]-Annex-6.xlsx`

**Examples**:
- `SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx`
- `SPD-Schedule-of-charges-and-other-tables-2024-V.0.12-Annex-6.xlsx`

**Additional Files**:
- CDCM models: `[SHORT]_[YEAR-YEAR]_CDCM_v[X]_[DATE]_[STATUS].xlsx`
- ED2 PCFM: `ED2-PCFM-[SHORT]-[DATE].xlsx`

### NPg (ID 23 only, ID 15 missing)
**Pattern**: `Northern Powergrid (Yorkshire) - [YEAR-YEAR] [TYPE] [VERSION].xlsx`

**Examples**:
- `Northern Powergrid (Yorkshire) - 2025-26 Schedule of charges and other tables v0.2.xlsx`
- `Northern Powergrid (Yorkshire) - 2024-25 CDCM Model v0.1.xlsx`

### ENWL (ID 16)
**Pattern**: `enwl---schedule-of-charges-and-other-tables--[YEAR]-[VERSION].xlsx`

**Examples**:
- `enwl---schedule-of-charges-and-other-tables--2025-v2_0.xlsx`
- `enwl---schedule-of-charges-and-other-tables--2023-final-v2.xlsx`

## BigQuery Integration

### Add Distribution ID to Tables

```sql
-- Add distribution_id column to dno_license_areas
ALTER TABLE `inner-cinema-476211-u9.gb_power.dno_license_areas`
ADD COLUMN distribution_id INT64;

-- Update with Distribution IDs
UPDATE `inner-cinema-476211-u9.gb_power.dno_license_areas`
SET distribution_id = CASE dno_key
  WHEN 'UKPN-EPN' THEN 10
  WHEN 'NGED-EM' THEN 11
  WHEN 'UKPN-LPN' THEN 12
  WHEN 'SP-Manweb' THEN 13
  WHEN 'NGED-WM' THEN 14
  WHEN 'NPg-NE' THEN 15
  WHEN 'ENWL' THEN 16
  WHEN 'SSE-SHEPD' THEN 17
  WHEN 'SP-Distribution' THEN 18
  WHEN 'UKPN-SPN' THEN 19
  WHEN 'SSE-SEPD' THEN 20
  WHEN 'NGED-SWales' THEN 21
  WHEN 'NGED-SW' THEN 22
  WHEN 'NPg-Y' THEN 23
END
WHERE TRUE;

-- Add distribution_id to duos_unit_rates
ALTER TABLE `inner-cinema-476211-u9.gb_power.duos_unit_rates`
ADD COLUMN distribution_id INT64;

-- Query example: Find all tariffs for a specific MPAN
SELECT 
  distribution_id,
  dno_key,
  tariff_code,
  unit_rate_p_kwh,
  time_band,
  year
FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
WHERE distribution_id = 10  -- Eastern Power Networks
  AND year = 2025
ORDER BY tariff_code, time_band;
```

## Usage in Data Pipelines

### Python: Extract Distribution ID from MPAN
```python
def get_distribution_id(mpan):
    """Extract Distribution ID from MPAN (first 2 digits)"""
    mpan_clean = mpan.replace(' ', '')
    return int(mpan_clean[:2])

def get_dno_key(distribution_id):
    """Map Distribution ID to DNO_Key"""
    mapping = {
        10: "UKPN-EPN", 11: "NGED-EM", 12: "UKPN-LPN",
        13: "SP-Manweb", 14: "NGED-WM", 15: "NPg-NE",
        16: "ENWL", 17: "SSE-SHEPD", 18: "SP-Distribution",
        19: "UKPN-SPN", 20: "SSE-SEPD", 21: "NGED-SWales",
        22: "NGED-SW", 23: "NPg-Y"
    }
    return mapping.get(distribution_id)

# Example usage
mpan = "10 1234 5678 9012 345 67"
dist_id = get_distribution_id(mpan)  # 10
dno = get_dno_key(dist_id)  # "UKPN-EPN"
```

### SQL: Join with Distribution ID
```sql
-- Find customers and their DNO from MPAN
SELECT 
  customer_id,
  mpan,
  CAST(SUBSTR(REPLACE(mpan, ' ', ''), 1, 2) AS INT64) AS distribution_id,
  d.dno_key,
  d.dno_name,
  d.gsp_group_id
FROM `project.dataset.customers` c
LEFT JOIN `inner-cinema-476211-u9.gb_power.dno_license_areas` d
  ON CAST(SUBSTR(REPLACE(c.mpan, ' ', ''), 1, 2) AS INT64) = d.distribution_id
```

## Data Quality Status

### ✅ Production Ready (13+ years, consistent structure)
- NGED areas (IDs 11, 14, 21, 22): 66 files, 2014-2026
- UKPN EPN/LPN (IDs 10, 12): 42 files, 2017-2026

### ✅ Good Quality (7+ years)
- SSEN (IDs 17, 20): 76 files, 2020-2026
- SPEN (IDs 13, 18): 42 files, 2020-2026
- NPg Yorkshire (ID 23): 26 files, 2017-2026

### ⚠️ Needs Cleanup
- ENWL (ID 16): 48 files, 35 with unknown year

### ❌ Missing/Incomplete
- NPg North East (ID 15): 0 files found
- UKPN South Eastern (ID 19): Only 1 file (should have ~20)

---

**Document**: Distribution ID Quick Reference  
**Date**: 30 October 2025  
**Related**: DNO_FILES_BY_DISTRIBUTION_ID_AND_YEAR.md  
**Project**: GB Power Market - DNO DUoS Charging Analysis
