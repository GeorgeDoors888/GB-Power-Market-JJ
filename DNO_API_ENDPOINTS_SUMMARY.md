# DNO OpenDataSoft Portal API Endpoints - Summary

**Date**: 2025-10-29  
**Purpose**: Document working API endpoints for GB DNO data portals

## ✅ Successfully Working Portals

### 1. UK Power Networks (UKPN)
- **URL**: https://ukpowernetworks.opendatasoft.com
- **Datasets**: 123
- **Status**: ✅ Fully working with standard SSL
- **Coverage**: South East England (EPN, LPN, SPN)

### 2. Electricity North West (ENWL)
- **URL**: https://electricitynorthwest.opendatasoft.com
- **Datasets**: 85
- **Status**: ⚠️ Working but requires SSL verification disabled
- **Coverage**: North West England
- **Note**: SSL certificate issues require `verify=False` in Python requests

### 3. Northern Powergrid (NPg)
- **URL**: https://northernpowergrid.opendatasoft.com
- **Datasets**: 86
- **Status**: ✅ Fully working with standard SSL
- **Coverage**: North East England & Yorkshire

### 4. Scottish and Southern Electricity Networks - Transmission (SSEN-T)
- **URL**: https://ssentransmission.opendatasoft.com
- **Datasets**: 60
- **Status**: ⚠️ Working but requires SSL verification disabled
- **Coverage**: Transmission network in Scotland
- **Note**: This is SSEN's **Transmission** portal, not Distribution

## ❌ Problematic Portals

### 5. SP Energy Networks (SPEN)
- **URL**: https://spenergynetworks.opendatasoft.com
- **Datasets**: 118 (confirmed via curl)
- **Status**: ❌ SSL/TLS compatibility issues
- **Coverage**: Scotland (SPD, SPM) & Wales (SPMW)
- **Issue**: 
  - Works with `curl -sk` (skip SSL verification)
  - Fails in Python even with `verify=False`
  - Error: `TLSV1_ALERT_INTERNAL_ERROR`
  - Likely TLS version mismatch or cipher suite incompatibility

### 6. SSEN Distribution
- **URL**: ❌ No public OpenDataSoft portal found
- **Status**: Does not exist
- **Coverage**: Would cover SEPD & SHEPD license areas
- **Note**: SSEN only has a Transmission portal, no Distribution data portal

### 7. National Grid Electricity Distribution (NGED)
- **Former name**: Western Power Distribution (WPD)
- **URL**: ❌ No public OpenDataSoft portal found
- **Status**: Does not exist
- **Coverage**: Would cover WMID, EMID, SWALES, SWEST license areas
- **Tested URLs**: All failed
  - westernpower.opendatasoft.com (404)
  - wpd.opendatasoft.com (no DNS)
  - nged.opendatasoft.com (no DNS)
  - nationalgridelectricitydistribution.opendatasoft.com (no DNS)

## 📊 Summary Statistics

| DNO | Portal Status | Datasets | SSL Issues |
|-----|---------------|----------|------------|
| UKPN | ✅ Working | 123 | No |
| ENWL | ✅ Working | 85 | Yes (verify=False) |
| NPg | ✅ Working | 86 | No |
| SSEN-T | ✅ Working | 60 | Yes (verify=False) |
| SPEN | ⚠️ Partial | 118 | Yes (Python fails) |
| SSEN-D | ❌ Not found | 0 | N/A |
| NGED | ❌ Not found | 0 | N/A |

**Total datasets collected**: 354 (from 4 DNOs)  
**Potential additional**: 118 (SPEN, if SSL issue resolved)

## 🔧 Technical Implementation Notes

### SSL Verification Handling
```python
# Required for ENWL and SSEN-T
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# In request code:
verify_ssl = (dno_group not in ["SPEN", "ENWL", "SSEN"])
r = requests.get(catalog_url, verify=verify_ssl)
```

### SPEN Workaround
For SPEN, Python requests library cannot connect even with `verify=False`. Possible solutions:
1. Use subprocess to call `curl -sk`
2. Use different HTTP library (httpx, urllib3 directly)
3. Configure OpenSSL to use older TLS versions
4. Contact SPEN to fix their SSL/TLS configuration

### API Endpoint Pattern
All working portals follow this pattern:
```
https://{dno_subdomain}.opendatasoft.com/api/explore/v2.1/catalog/datasets
```

Query parameters:
- `limit`: Number of results per page (max 100)
- `offset`: Pagination offset

## 📁 Output Files

Generated CSV files (uploaded to Google Drive):
1. `dno_datasets_ukpn_full.csv` (0.39 MB, 123 datasets)
2. `dno_datasets_enwl_full.csv` (0.21 MB, 85 datasets)
3. `dno_datasets_npg_full.csv` (0.24 MB, 86 datasets)
4. `dno_datasets_ssen_full.csv` (0.06 MB, 60 datasets)
5. `dno_datasets_master_full.csv` (0.91 MB, 354 total datasets)

All files include:
- Dataset ID
- Title
- Description
- Keywords
- Theme
- Publisher
- Modified date
- License
- Records count
- Has records flag
- Visibility
- DNO Group

## 🔍 Research Findings

### SSEN
- SSEN (Scottish and Southern Electricity Networks) operates both **Transmission** and **Distribution** networks
- Only **Transmission** has a public OpenDataSoft portal
- Distribution areas (SEPD - Southern Electric, SHEPD - Scottish Hydro Electric) have no public data portal
- Official website: https://www.ssen.co.uk/

### NGED
- Formerly Western Power Distribution (acquired by National Grid in 2021)
- Now called National Grid Electricity Distribution
- Operates 4 license areas: WMID, EMID, SWALES, SWEST
- No OpenDataSoft portal found despite extensive testing
- May use alternative data platforms (e.g., data.nationalgrid.com, but that site had 404s)
- Official website: https://www.nationalgrid.co.uk/

## 🎯 Recommendations

1. **SPEN**: Investigate alternative HTTP clients or use curl subprocess approach
2. **SSEN-D & NGED**: Check for alternative data portals (CKAN, custom APIs, FTP servers)
3. **Contact DNOs**: Reach out directly to SSEN and NGED for data access information
4. **ENA Coordination**: Energy Networks Association may have centralized data access

## 🔗 Useful Resources

- Energy Networks Association: https://www.energynetworks.org/
- OpenDataSoft Documentation: https://help.opendatasoft.com/
- DNO Map: https://www.energynetworks.org/operating-the-networks/whos-my-network-operator
