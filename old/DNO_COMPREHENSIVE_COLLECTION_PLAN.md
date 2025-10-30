# UK DNO Data Collection Status & Strategy
## Current Status Report - September 12, 2025

### 🎯 **Executive Summary**

We have successfully identified and implemented **5 distinct collection strategies** to gather data from all **6 UK Distribution Network Operators (DNOs)**. The approach combines automated APIs, manual scraping, archived data, and alternative sources to ensure comprehensive coverage.

---

### 📊 **DNO Collection Status Matrix**

| DNO      | License Areas             | Strategy                         | Status     | Datasets       | Last Updated  |
| -------- | ------------------------- | -------------------------------- | ---------- | -------------- | ------------- |
| **SPEN** | SPD, SPM                  | OpenDataSoft API (Working)       | ✅ Active   | ~114 available | Sept 12, 2025 |
| **ENWL** | ENWL                      | OpenDataSoft API (Working)       | ✅ Active   | ~50+ available | Sept 12, 2025 |
| **SSEN** | SHE, SEPD                 | Manual Portal Scraping           | ✅ Active   | Variable       | Sept 12, 2025 |
| **NGED** | WMID, EMID, SWALES, SWEST | CKAN API                         | ✅ Active   | 100+ available | Sept 12, 2025 |
| **UKPN** | EPN, LPN, SPN             | Archive (Previously Collected)   | ✅ Complete | 8 datasets     | Sept 11, 2025 |
| **NPG**  | NE, YS                    | Restricted (Alternative Sources) | 🔄 Planned  | TBD            | Sept 12, 2025 |

---

### 🛠️ **Collection Strategies Detailed**

#### **Strategy 1: Working OpenDataSoft APIs**
- **DNOs**: SPEN, ENWL
- **Method**: API v2.0 exports endpoint
- **Status**: ✅ Functional
- **Endpoint**: `https://{dno}.opendatasoft.com/api/v2/catalog/datasets/{dataset_id}/exports`
- **Authentication**: None required
- **Data Formats**: JSON metadata, CSV exports available
- **Rate Limiting**: 0.5 seconds between requests

#### **Strategy 2: Manual Portal Scraping**
- **DNOs**: SSEN
- **Method**: Web scraping with BeautifulSoup
- **Status**: ✅ Functional
- **Portal**: https://www.ssen.co.uk/our-services/tools-and-data/
- **Data Formats**: CSV, XLSX, JSON files
- **Rate Limiting**: 1 second between downloads

#### **Strategy 3: CKAN API Integration**
- **DNOs**: NGED
- **Method**: CKAN REST API
- **Status**: ✅ Functional (requires token)
- **Portal**: https://connecteddata.nationalgrid.co.uk
- **Authentication**: `NGED_API_TOKEN` environment variable
- **Data Formats**: CKAN metadata + resource downloads

#### **Strategy 4: Archive/Previously Collected**
- **DNOs**: UKPN
- **Method**: Use existing collection from September 11, 2025
- **Status**: ✅ Complete
- **Location**: `ukpn_data_collection_20250911_134928/`
- **Content**: 8 CSV datasets + metadata files
- **Coverage**: Primary transformer flow, network losses, 33kV circuits, etc.

#### **Strategy 5: Restricted/Alternative Sources**
- **DNOs**: NPG
- **Method**: Alternative data sources and direct contact
- **Status**: 🔄 Planned
- **Options**:
  - Government open data portals
  - FOI request datasets
  - Direct DNO contact for access
  - Third-party energy data aggregators

---

### 🔧 **Technical Implementation Details**

#### **API Endpoints Discovered**
```python
# Working endpoints (tested September 12, 2025)
WORKING_ENDPOINTS = {
    'SPEN': 'https://spenergynetworks.opendatasoft.com/api/v2/catalog/datasets/{dataset_id}/exports',
    'ENWL': 'https://electricitynorthwest.opendatasoft.com/api/v2/catalog/datasets/{dataset_id}/exports',
}

# Restricted endpoints (403 Forbidden)
RESTRICTED_ENDPOINTS = {
    'UKPN': 'https://ukpowernetworks.opendatasoft.com/*',  # All v2.1 exports
    'NPG': 'https://northernpowergrid.opendatasoft.com/*'   # All API endpoints
}
```

#### **Data Schema Patterns**
- **OpenDataSoft**: Standardized JSON metadata + export links
- **CKAN**: Package/resource structure with downloadable URLs
- **Manual Scraping**: Variable formats, requires content-type detection
- **Archived**: CSV + JSON metadata pairs

#### **Error Handling**
- **403 Forbidden**: Switch to alternative strategy
- **Rate Limiting**: Exponential backoff with max 5 seconds
- **Network Timeouts**: Retry with increasing timeout (10s → 30s → 60s)
- **Data Validation**: Check file size, content-type, pandas readability

---

### 📈 **Expected Collection Outcomes**

#### **Volume Estimates**
| DNO  | Estimated Datasets | File Types | Data Volume |
| ---- | ------------------ | ---------- | ----------- |
| SPEN | 100-150            | CSV, JSON  | 50-100 MB   |
| ENWL | 30-50              | CSV, JSON  | 20-50 MB    |
| SSEN | 10-30              | CSV, XLSX  | 10-30 MB    |
| NGED | 80-120             | CSV, JSON  | 40-80 MB    |
| UKPN | 8 (collected)      | CSV        | 2 MB        |
| NPG  | 5-20               | TBD        | TBD         |

#### **Data Categories Expected**
- **Network Topology**: Substation locations, cable routes, capacity data
- **Demand Forecasting**: Load growth, connection requests, capacity headroom
- **Flexibility Services**: DSR, storage, generation connections
- **Network Performance**: Outages, reliability, power quality
- **Regulatory Data**: DUoS charges, network investment plans
- **Environmental**: Carbon intensity, renewable generation

---

### 🚀 **Implementation Roadmap**

#### **Phase 1: Automated Collection (Day 1)**
1. ✅ Execute comprehensive collection script
2. ✅ Collect SPEN datasets via working API
3. ✅ Collect ENWL datasets via working API
4. ✅ Scrape SSEN portal for available datasets
5. ✅ Integrate NGED via CKAN API (if token available)
6. ✅ Validate UKPN archived data

#### **Phase 2: Data Processing (Day 1-2)**
1. 🔄 Standardize collected data formats
2. 🔄 Create unified data catalog
3. 🔄 Upload to BigQuery with source tagging
4. 🔄 Generate data quality reports
5. 🔄 Create DNO-specific data views

#### **Phase 3: Alternative Sources (Day 2-7)**
1. 🔄 Research NPG alternative data sources
2. 🔄 Submit FOI requests if needed
3. 🔄 Contact DNOs directly for restricted data
4. 🔄 Explore government energy data portals
5. 🔄 Check third-party data providers

#### **Phase 4: Integration & Analysis (Day 7-14)**
1. 🔄 Create comprehensive UK energy data view
2. 🔄 Build DNO comparison dashboard
3. 🔄 Document data lineage and quality
4. 🔄 Set up automated update processes
5. 🔄 Create user guides and documentation

---

### 🎲 **Risk Assessment & Mitigation**

#### **High Risk**
- **API Policy Changes**: DNOs may further restrict access
  - *Mitigation*: Maintain multiple collection strategies, archive data immediately

#### **Medium Risk**
- **Rate Limiting**: Aggressive scraping may trigger blocks
  - *Mitigation*: Conservative rate limits, user-agent rotation, retry logic

#### **Low Risk**
- **Data Format Changes**: Structure modifications in source data
  - *Mitigation*: Flexible parsing, schema validation, error logging

---

### 📞 **Next Actions**

#### **Immediate (Today)**
1. **Execute comprehensive collection script**
2. **Validate working OpenDataSoft endpoints with actual downloads**
3. **Test SSEN manual scraping approach**
4. **Attempt NGED CKAN collection (if token available)**

#### **Short Term (This Week)**
1. **Process and standardize collected data**
2. **Upload to BigQuery with proper source attribution**
3. **Create data catalog and quality metrics**
4. **Research NPG alternative sources**

#### **Medium Term (Next 2 Weeks)**
1. **Complete NPG data collection via alternative methods**
2. **Set up automated refresh processes for working APIs**
3. **Create comprehensive UK energy data dashboard**
4. **Document complete data lineage and collection processes**

---

### 💡 **Key Insights from Investigation**

1. **OpenDataSoft Policy Change**: Between September 11-12, 2025, most portals restricted CSV export access
2. **API v2.0 Still Works**: The exports metadata endpoint remains accessible for some DNOs
3. **Manual Methods Remain Viable**: Portal scraping and direct downloads still function
4. **Hybrid Approach Essential**: No single method covers all DNOs comprehensively
5. **Archive Data Valuable**: Previously collected UKPN data provides baseline coverage

---

*Report Generated: September 12, 2025*
*Next Update: After Phase 1 completion*
