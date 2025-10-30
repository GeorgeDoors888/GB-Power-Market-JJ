# Quick Reference: Data Queries & Dashboard

**Quick access to common queries and data retrieval patterns**

---

## 🚀 Quick Start

### Get Latest Generation Data
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python update_dashboard_clean.py
```

### Check Data Freshness
```bash
python -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
result = client.query('SELECT MAX(startTime) FROM \`inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type\`').result()
for row in result:
    print(f'Latest: {row[0]}')
"
```

---

## 📊 Common Queries

### 1. Latest Generation Mix
```sql
WITH latest_data AS (
    SELECT startTime, data
    FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
    ORDER BY startTime DESC
    LIMIT 1
)
SELECT 
    gen.psrType as fuel_type,
    gen.quantity / 1000 as generation_gw
FROM latest_data,
UNNEST(data) as gen
ORDER BY gen.quantity DESC
```

### 2. Interconnector Flows (Latest)
```sql
SELECT 
    fuelType,
    generation / 1000 as flow_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.fuelinst_sep_oct_2025`
WHERE publishTime = (SELECT MAX(publishTime) FROM `inner-cinema-476211-u9.uk_energy_prod.fuelinst_sep_oct_2025`)
AND fuelType LIKE 'INT%'
ORDER BY generation DESC
```

### 3. Daily Generation Total
```sql
SELECT 
    DATE(startTime) as date,
    SUM(gen.quantity) / 1000 as total_generation_gwh
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`,
UNNEST(data) as gen
GROUP BY date
ORDER BY date DESC
```

### 4. Wind Generation Trend (Last 7 Days)
```sql
SELECT 
    startTime,
    gen.psrType,
    gen.quantity / 1000 as generation_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`,
UNNEST(data) as gen
WHERE gen.psrType LIKE 'Wind%'
AND startTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY startTime DESC
```

---

## 🔌 Interconnector Codes

| Code | Country/Link | Typical Capacity |
|------|--------------|------------------|
| INTFR | France (IFA) | 2 GW |
| INTIFA2 | France (IFA2) | 1 GW |
| INTELEC | France (Eleclink) | 1 GW |
| INTNED | Netherlands (BritNed) | 1 GW |
| INTNEM | Belgium (Nemo) | 1 GW |
| INTEW | Belgium (old) | 0.5 GW |
| INTIRL | Ireland (EWIC) | 0.5 GW |
| INTNSL | Norway (NSL) | 1.4 GW |
| INTVKL | Denmark (Viking) | 1.4 GW |
| INTGRNL | Greenland? | Variable |

**Note:** Positive = Import, Negative = Export

---

## 🎨 Fuel Type Mapping

| API Name | Display Name | Color |
|----------|--------------|-------|
| Wind Offshore | Offshore Wind | 🟦 Blue |
| Wind Onshore | Onshore Wind | 🟦 Light Blue |
| Nuclear | Nuclear | 🟪 Purple |
| Fossil Gas | Gas (CCGT) | 🟧 Orange |
| Solar | Solar | 🟨 Yellow |
| Biomass | Biomass | 🟩 Green |
| Hydro Run-of-river and poundage | Hydro | 🟦 Cyan |
| Hydro Pumped Storage | Pumped Storage | 🔵 Dark Blue |
| Fossil Hard coal | Coal | ⚫ Black |
| Fossil Oil | Oil | ⚫ Dark Gray |
| Other | Other | ⚪ Gray |

---

## 📅 Settlement Periods

```python
# Convert time to settlement period
def time_to_sp(hour, minute):
    return (hour * 2) + (2 if minute >= 30 else 1)

# Convert settlement period to time
def sp_to_time(sp):
    hour = (sp - 1) // 2
    minute = 30 if (sp - 1) % 2 == 1 else 0
    return f"{hour:02d}:{minute:02d}"
```

**Examples:**
- 00:00 = SP 1
- 06:30 = SP 14
- 12:00 = SP 25
- 18:30 = SP 38
- 23:30 = SP 48

---

## 🗂️ Table Reference

| Table Name | Update Frequency | Lag | Use For |
|------------|------------------|-----|---------|
| `generation_actual_per_type` | Daily | D-1 | Generation mix, fuel breakdown |
| `fuelinst_sep_oct_2025` | ~5 min | 5-10 min | Real-time interconnectors |
| `pn_sep_oct_2025` | Real-time | <1 min | BM unit notifications |
| `demand_outturn_summary` | Daily | D-1 | Demand analysis |
| `generation_outturn` | Daily | D-1 | Total generation |

---

## 🛠️ Python Quick Access

### Import Data
```python
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jibber_jabber_key.json"
client = bigquery.Client(project='inner-cinema-476211-u9')
```

### Run Query
```python
query = """
    SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
    LIMIT 10
"""
results = client.query(query).result()
for row in results:
    print(dict(row))
```

### Get Latest Generation
```python
from update_dashboard_clean import get_latest_generation

generation, timestamp = get_latest_generation()
print(f"Wind: {generation.get('WIND_TOTAL', 0):.2f} GW")
print(f"Nuclear: {generation.get('NUCLEAR', 0):.2f} GW")
```

---

## 📱 Dashboard Integration

### Update Google Sheet
```bash
# With sheet ID
python update_dashboard_clean.py --sheet-id YOUR_SHEET_ID

# Just fetch data (no update)
python update_dashboard_clean.py
```

### Cell Mapping Template
```python
# In update_google_sheet() function
worksheet.update_acell('B2', f"{generation.get('WIND_TOTAL', 0):.2f}")
worksheet.update_acell('B3', f"{generation.get('NUCLEAR', 0):.2f}")
worksheet.update_acell('B4', f"{generation.get('GAS', 0):.2f}")
```

---

## 🔍 Troubleshooting

### Query Returns No Data
```sql
-- Check what data exists
SELECT MIN(startTime), MAX(startTime), COUNT(*)
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
```

### Column Not Found Error
```sql
-- Check table schema
SELECT column_name, data_type
FROM `inner-cinema-476211-u9.uk_energy_prod.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'generation_actual_per_type'
```

### Authentication Error
```bash
# Verify credentials
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/jibber_jabber_key.json"
gcloud auth application-default print-access-token
```

---

## 📊 Current Data Summary

**Last Updated:** 26 October 2025

**Generation (25 Oct 2025, 22:00, SP 47):**
- Wind: 19.52 GW (Offshore: 12.16, Onshore: 7.36)
- Nuclear: 3.68 GW
- Gas: 3.22 GW
- Biomass: 0.84 GW
- Other: 0.56 GW
- Hydro: 0.14 GW
- Coal/Oil/Solar: 0.00 GW

**Interconnectors (26 Oct 2025, 11:35, SP 24):**
- Importing: 8.46 GW (France, Norway, Netherlands, Belgium, Eleclink, IFA2, Viking)
- Exporting: 0.70 GW (Ireland, Belgium, INTGRNL)
- Net Import: 6.76 GW

**Storage:**
- 65 tables
- 7.2M records
- 925 MB

---

## 🔗 Quick Links

- **Full Documentation:** `DATA_INGESTION_DOCUMENTATION.md`
- **Streaming Fix Details:** `STREAMING_UPLOAD_FIX.md`
- **Download Strategy:** `MULTI_YEAR_DOWNLOAD_PLAN.md`
- **API Research:** `API_RESEARCH_FINDINGS.md`

---

## 💡 Tips

1. **Always check data freshness** before relying on "latest" queries
2. **Use LIMIT** in exploratory queries to avoid costs
3. **Interconnector data** is more up-to-date than generation mix
4. **Settlement periods** are UK-specific (48 per day, 30 min each)
5. **Positive flows = Import**, Negative = Export (can be confusing!)

---

*For detailed documentation, see DATA_INGESTION_DOCUMENTATION.md*
