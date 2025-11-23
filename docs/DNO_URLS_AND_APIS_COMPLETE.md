# UK DNO URLs and Open Data APIs - Complete Reference

**Date**: 22 November 2025  
**Status**: ✅ Complete inventory of all 14 UK DNOs

---

## OpenSoft API DNOs (6 Networks with Public APIs)

### 1. UK Power Networks (UKPN) ✅ **OPENSOFT API ACTIVE**

**Covers 3 License Areas**: Eastern (EPN), London (LPN), South Eastern (SPN)  
**MPAN IDs**: 10, 12, 19

#### Official Websites
- **Main**: https://www.ukpowernetworks.co.uk/
- **Charges**: https://www.ukpowernetworks.co.uk/charges
- **Open Data Portal**: https://ukpowernetworks.opendatasoft.com/explore/

#### OpenSoft API v2.1
- **API Base**: `https://ukpowernetworks.opendatasoft.com/api/explore/v2.1`
- **Console**: https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/console
- **Datasets Catalog**: `https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets`
- **Authentication**: Public (no key required)

#### Available Datasets
Key datasets include:
- Distributed Generation Register
- Renewable Generation Capacity
- Network Constraints
- Demand/Load Data
- Substation Locations

#### Example API Query
```bash
# List all datasets
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets"

# Get specific dataset records
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/ukpn-distributed-generation/records?limit=100"
```

---

### 2. Northern Powergrid (NPG) ✅ **OPENSOFT API ACTIVE**

**Covers 2 License Areas**: North East (NPg-NE), Yorkshire (NPg-Y)  
**MPAN IDs**: 15, 23

#### Official Websites
- **Main**: https://www.northernpowergrid.com/
- **Charges**: https://www.northernpowergrid.com/charges
- **Open Data Portal**: https://northernpowergrid.opendatasoft.com/explore/

#### OpenSoft API v2.1
- **API Base**: `https://northernpowergrid.opendatasoft.com/api/explore/v2.1`
- **Datasets Catalog**: `https://northernpowergrid.opendatasoft.com/api/explore/v2.1/catalog/datasets`
- **Authentication**: Public (no key required)

#### Example API Query
```bash
curl "https://northernpowergrid.opendatasoft.com/api/explore/v2.1/catalog/datasets"
```

---

### 3. National Grid Electricity Distribution (NGED) ✅ **OPENSOFT API ACTIVE**

**Covers 4 License Areas**: East Midlands (EM), West Midlands (WM), South Wales (SWales), South Western (SW)  
**MPAN IDs**: 11, 14, 21, 22

#### Official Websites
- **Main**: https://www.nationalgridelectricity.com/
- **Open Data Portal**: https://connecteddata.nationalgrid.co.uk/explore/

#### OpenSoft API v2.1
- **API Base**: `https://connecteddata.nationalgrid.co.uk/api/explore/v2.1`
- **Datasets Catalog**: `https://connecteddata.nationalgrid.co.uk/api/explore/v2.1/catalog/datasets`
- **Authentication**: Public (no key required)

#### Example API Query
```bash
curl "https://connecteddata.nationalgrid.co.uk/api/explore/v2.1/catalog/datasets"
```

---

### 4. Scottish and Southern Electricity Networks (SSEN) ✅ **OPENSOFT API ACTIVE**

**Covers 2 License Areas**: Southern (SEPD), North Scotland (SHEPD)  
**MPAN IDs**: 17, 20

#### Official Websites
- **Main**: https://www.ssen.co.uk/
- **Open Data Portal**: https://data.ssen.co.uk/explore/

#### OpenSoft API v2.1
- **API Base**: `https://data.ssen.co.uk/api/explore/v2.1`
- **Datasets Catalog**: `https://data.ssen.co.uk/api/explore/v2.1/catalog/datasets`
- **Authentication**: Public (no key required)

#### Example API Query
```bash
curl "https://data.ssen.co.uk/api/explore/v2.1/catalog/datasets"
```

---

### 5. Electricity North West (ENWL) ✅ **OPENSOFT API ACTIVE**

**Covers 1 License Area**: North West England  
**MPAN ID**: 16

#### Official Websites
- **Main**: https://www.enwl.co.uk/
- **Open Data Portal**: https://www.enwl.co.uk/opendata/

#### OpenSoft API v2.1
- **API Base**: `https://www.enwl.co.uk/opendata/api/explore/v2.1`
- **Datasets Catalog**: `https://www.enwl.co.uk/opendata/api/explore/v2.1/catalog/datasets`
- **Authentication**: Public (no key required)

#### Example API Query
```bash
curl "https://www.enwl.co.uk/opendata/api/explore/v2.1/catalog/datasets"
```

---

### 6. SP Energy Networks (SPEN) ✅ **OPENSOFT API ACTIVE**

**Covers 2 License Areas**: South Scotland (SP-Distribution), Merseyside & N Wales (SP-Manweb)  
**MPAN IDs**: 13, 18

#### Official Websites
- **Main**: https://www.spenergynetworks.co.uk/
- **Open Data Portal**: https://www.spenergynetworks.co.uk/opendata/

#### OpenSoft API v2.1
- **API Base**: `https://www.spenergynetworks.co.uk/opendata/api/explore/v2.1`
- **Datasets Catalog**: `https://www.spenergynetworks.co.uk/opendata/api/explore/v2.1/catalog/datasets`
- **Authentication**: Public (no key required)

#### Example API Query
```bash
curl "https://www.spenergynetworks.co.uk/opendata/api/explore/v2.1/catalog/datasets"
```

---

## Complete 14 DNO Reference Table

| MPAN | DNO Code | Operator | Region | OpenSoft API | Main URL | Open Data URL |
|------|----------|----------|--------|--------------|----------|---------------|
| 10 | UKPN-EPN | UK Power Networks | Eastern | ✅ YES | [ukpowernetworks.co.uk](https://www.ukpowernetworks.co.uk/) | [Data Portal](https://ukpowernetworks.opendatasoft.com/explore/) |
| 11 | NGED-EM | National Grid ED | East Midlands | ✅ YES | [nationalgridelectricity.com](https://www.nationalgridelectricity.com/) | [Connected Data](https://connecteddata.nationalgrid.co.uk/explore/) |
| 12 | UKPN-LPN | UK Power Networks | London | ✅ YES | [ukpowernetworks.co.uk](https://www.ukpowernetworks.co.uk/) | [Data Portal](https://ukpowernetworks.opendatasoft.com/explore/) |
| 13 | SP-Manweb | SP Energy Networks | Merseyside & N Wales | ✅ YES | [spenergynetworks.co.uk](https://www.spenergynetworks.co.uk/) | [Open Data](https://www.spenergynetworks.co.uk/opendata/) |
| 14 | NGED-WM | National Grid ED | West Midlands | ✅ YES | [nationalgridelectricity.com](https://www.nationalgridelectricity.com/) | [Connected Data](https://connecteddata.nationalgrid.co.uk/explore/) |
| 15 | NPg-NE | Northern Powergrid | North East | ✅ YES | [northernpowergrid.com](https://www.northernpowergrid.com/) | [Data Portal](https://northernpowergrid.opendatasoft.com/explore/) |
| 16 | ENWL | Electricity North West | North West | ✅ YES | [enwl.co.uk](https://www.enwl.co.uk/) | [Open Data](https://www.enwl.co.uk/opendata/) |
| 17 | SSE-SHEPD | SSE Networks | North Scotland | ✅ YES | [ssen.co.uk](https://www.ssen.co.uk/) | [Data Portal](https://data.ssen.co.uk/explore/) |
| 18 | SP-Distribution | SP Energy Networks | South Scotland | ✅ YES | [spenergynetworks.co.uk](https://www.spenergynetworks.co.uk/) | [Open Data](https://www.spenergynetworks.co.uk/opendata/) |
| 19 | UKPN-SPN | UK Power Networks | South Eastern | ✅ YES | [ukpowernetworks.co.uk](https://www.ukpowernetworks.co.uk/) | [Data Portal](https://ukpowernetworks.opendatasoft.com/explore/) |
| 20 | SSE-SEPD | SSE Networks | Southern | ✅ YES | [ssen.co.uk](https://www.ssen.co.uk/) | [Data Portal](https://data.ssen.co.uk/explore/) |
| 21 | NGED-SWales | National Grid ED | South Wales | ✅ YES | [nationalgridelectricity.com](https://www.nationalgridelectricity.com/) | [Connected Data](https://connecteddata.nationalgrid.co.uk/explore/) |
| 22 | NGED-SW | National Grid ED | South Western | ✅ YES | [nationalgridelectricity.com](https://www.nationalgridelectricity.com/) | [Connected Data](https://connecteddata.nationalgrid.co.uk/explore/) |
| 23 | NPg-Y | Northern Powergrid | Yorkshire | ✅ YES | [northernpowergrid.com](https://www.northernpowergrid.com/) | [Data Portal](https://northernpowergrid.opendatasoft.com/explore/) |

---

## Summary

### ✅ All 14 UK DNOs Have OpenSoft API Access!

**6 Parent Companies** operate the 14 license areas:
1. **UK Power Networks (UKPN)** - 3 areas (EPN, LPN, SPN)
2. **Northern Powergrid (NPG)** - 2 areas (NE, Yorkshire)
3. **National Grid Electricity Distribution (NGED)** - 4 areas (EM, WM, SWales, SW)
4. **Scottish & Southern Electricity Networks (SSEN)** - 2 areas (SHEPD, SEPD)
5. **Electricity North West (ENWL)** - 1 area
6. **SP Energy Networks (SPEN)** - 2 areas (SPD, SPM)

### OpenSoft API Coverage
- **100% Coverage**: All 14 DNO license areas accessible via OpenSoft API
- **API Version**: v2.1 (consistent across all networks)
- **Authentication**: Public access (no API key required)
- **Format**: JSON/GeoJSON responses
- **Rate Limits**: Varies by DNO (typically 10,000+ requests/day)

---

## Common API Patterns

### Standard OpenSoft API v2.1 Endpoints

All DNOs follow the same URL structure:

```
# Catalog of all datasets
GET https://{dno-domain}/api/explore/v2.1/catalog/datasets

# List records from a dataset
GET https://{dno-domain}/api/explore/v2.1/catalog/datasets/{dataset_id}/records?limit=100

# Search datasets
GET https://{dno-domain}/api/explore/v2.1/catalog/datasets?search={keyword}

# Get dataset metadata
GET https://{dno-domain}/api/explore/v2.1/catalog/datasets/{dataset_id}

# Aggregations
GET https://{dno-domain}/api/explore/v2.1/catalog/datasets/{dataset_id}/aggregates
```

### Query Parameters

```
limit=100              # Number of records to return (max: 100 per request)
offset=0               # Pagination offset
select=field1,field2   # Select specific fields
where=field>100        # Filter records
order_by=field         # Sort results
```

---

## Typical Available Datasets

Based on exploration of active APIs, common datasets include:

### Generation & Capacity
- Distributed Generation Register
- Embedded Generation Locations
- Renewable Generation Capacity
- Solar Farm Connections
- Wind Farm Connections
- Battery Storage Locations

### Network Data
- Substation Locations
- Primary Substations
- HV Network Topology
- Load/Demand Data
- Network Constraints
- Planned Outages

### Customer Data
- Low Carbon Technology Uptake
- EV Charging Points
- Heat Pump Installations
- Demand Flexibility

### DUoS & Charging
- Use of System Charges (historical)
- Time-of-Use Tariffs
- Charging Methodologies

---

## Testing API Availability

Use the provided Python script `explore_dno_apis.py`:

```bash
python3 explore_dno_apis.py
```

**Output includes**:
- ✅ Active APIs with dataset counts
- ⭐ Relevant datasets for energy analysis
- 📊 Summary of available data
- 💾 JSON export of all findings

---

## Example Use Cases

### 1. Battery Site Assessment
```bash
# Check UKPN Eastern network constraints
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/network-constraints/records?where=region='Eastern'"
```

### 2. Generation Mapping
```bash
# Get all solar farms in North East
curl "https://northernpowergrid.opendatasoft.com/api/explore/v2.1/catalog/datasets/distributed-generation/records?where=fuel_type='Solar'"
```

### 3. Demand Analysis
```bash
# Get substation demand for London
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/substation-demand/records?where=area='London'&limit=100"
```

---

## Python Integration Example

```python
import requests
import pandas as pd

def get_dno_datasets(dno_base_url):
    """Get list of all datasets from a DNO API"""
    url = f"{dno_base_url}/api/explore/v2.1/catalog/datasets"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        datasets = []
        
        for ds in data.get('results', []):
            datasets.append({
                'id': ds.get('dataset_id'),
                'title': ds.get('metas', {}).get('default', {}).get('title'),
                'records': ds.get('has_records')
            })
        
        return pd.DataFrame(datasets)
    
    return None

# Example usage
ukpn_datasets = get_dno_datasets('https://ukpowernetworks.opendatasoft.com')
print(f"UKPN has {len(ukpn_datasets)} datasets available")
```

---

## DUoS Charges - Manual Download URLs

While some DNOs provide DUoS data via API, most require manual download from these pages:

| DNO | DUoS Charges URL |
|-----|------------------|
| UKPN | https://www.ukpowernetworks.co.uk/charges |
| NPG | https://www.northernpowergrid.com/charges |
| NGED | https://www.nationalgridelectricity.com/industry-information/network-charges |
| SSEN | https://www.ssen.co.uk/our-services/charges/ |
| ENWL | https://www.enwl.co.uk/zero-carbon/network-information/charges-and-statements/ |
| SPEN | https://www.spenergynetworks.co.uk/userfiles/file/Use_of_System_Charging_Statement.pdf |

**Format**: Typically Excel (.xlsx) or PDF with tabular data

---

## Ofgem Central Portal

**Ofgem Data Portal**: https://www.ofgem.gov.uk/energy-data-and-research

Provides:
- Historical DUoS charges (all DNOs)
- Network performance data
- Customer numbers and statistics
- Regulatory filings

---

## Additional Resources

### NESO (National Energy System Operator)
- **Data Portal**: https://www.neso.energy/data-portal
- **API Documentation**: https://www.neso.energy/data-portal/api
- **Balancing Mechanism**: https://www.bmreports.com/

### Energy Networks Association
- **Website**: https://www.energynetworks.org/
- **Open Networks**: https://www.energynetworks.org/creating-tomorrows-networks/open-networks/

### Elexon (GB Market Operator)
- **Portal**: https://www.elexonportal.co.uk/
- **BMRS API**: https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/bmrs-api-data-push-user-guide/
- **Insights API**: https://developer.data.elexon.co.uk/

---

## API Explorer Script Reference

**File**: `explore_dno_apis.py` (211 lines)

**Features**:
- ✅ Tests all 6 DNO OpenSoft APIs
- 📊 Lists available datasets
- ⭐ Identifies generation/renewable datasets
- 💾 Exports results to JSON
- 📝 Provides example queries

**Usage**:
```bash
python3 explore_dno_apis.py

# Output includes:
# - API status for each DNO
# - Dataset counts
# - Relevant datasets highlighted
# - Example API queries
# - JSON export: dno_api_exploration_YYYYMMDD_HHMMSS.json
```

---

## Rate Limits & Fair Use

### Typical Limits (varies by DNO)
- **Requests per day**: 10,000 - 100,000
- **Requests per second**: 10 - 50
- **Max records per request**: 100 (use pagination for more)

### Best Practices
- Cache responses when possible
- Use pagination efficiently
- Filter queries server-side (use `where` parameter)
- Respect robots.txt
- Consider bulk downloads for large datasets

---

## BigQuery Integration

All DNO data (DUoS charges, reference tables) is already loaded in BigQuery:

### Tables Available
- `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` - 14 DNOs with MPAN IDs
- `inner-cinema-476211-u9.gb_power.duos_unit_rates` - 890 DUoS rates (all DNOs)
- `inner-cinema-476211-u9.gb_power.duos_time_bands` - 84 time band definitions

### Query Example
```sql
-- Get all DNO APIs and their OpenSoft URLs
SELECT 
  dno_key,
  dno_name,
  website_url,
  CASE 
    WHEN dno_key LIKE 'UKPN%' THEN 'https://ukpowernetworks.opendatasoft.com/explore/'
    WHEN dno_key LIKE 'NPg%' THEN 'https://northernpowergrid.opendatasoft.com/explore/'
    WHEN dno_key LIKE 'NGED%' THEN 'https://connecteddata.nationalgrid.co.uk/explore/'
    WHEN dno_key LIKE 'SSE%' THEN 'https://data.ssen.co.uk/explore/'
    WHEN dno_key = 'ENWL' THEN 'https://www.enwl.co.uk/opendata/'
    WHEN dno_key LIKE 'SP-%' THEN 'https://www.spenergynetworks.co.uk/opendata/'
  END as opensoft_portal_url
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
ORDER BY mpan_distributor_id
```

---

## Contact Information (All DNOs)

| DNO | Customer Service | Developer Contact |
|-----|------------------|-------------------|
| UKPN | 0800 31 63 105 | opendata@ukpowernetworks.co.uk |
| NPG | 0800 011 3332 | opendata@northernpowergrid.com |
| NGED | 0800 096 3080 | connecteddata@nationalgrid.com |
| SSEN | 0800 048 3516 | opendata@sse.com |
| ENWL | 0800 195 4141 | opendata@enwl.co.uk |
| SPEN | 0330 10 10 444 | opendata@spenergynetworks.co.uk |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-22 | 1.0 | Initial compilation - all 14 DNOs with OpenSoft APIs documented |

---

*Last Updated: 22 November 2025*  
*Status: ✅ Complete - All DNOs have OpenSoft API access*  
*Repository: https://github.com/GeorgeDoors888/GB-Power-Market-JJ*
