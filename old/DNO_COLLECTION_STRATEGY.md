# UK DNO Data Collection Strategy

## Executive Summary

Currently we have comprehensive data from **1 out of 6 UK DNOs** (UKPN only, 17% coverage). To complete the UK electricity distribution network dataset, we need to collect data from the remaining **5 DNOs**.

## Current Status

### ✅ Collected (1/6 DNOs)
- **UKPN (UK Power Networks)**: 10 tables collected
  - Areas: LPN, SPN, EPN (London, South, Eastern England)
  - Data types: DUoS charges, network data, connections

### 🔄 Remaining DNOs (5/6)

| DNO      | Full Name                                | Areas                     | Priority | Status             |
| -------- | ---------------------------------------- | ------------------------- | -------- | ------------------ |
| **SSEN** | Scottish & Southern Electricity Networks | SSES, SHEPD               | High     | 🎯 Ready to collect |
| **NGED** | National Grid Electricity Distribution   | WMID, EMID, SWALES, SWEST | High     | 🔍 Research phase   |
| **ENWL** | Electricity North West                   | ENWL                      | Medium   | 🔍 Research phase   |
| **NPG**  | Northern Powergrid                       | NEEB, YOREB               | Medium   | 🔍 Research phase   |
| **SPD**  | SP Distribution                          | SPDS, SPMW                | Medium   | 🔍 Research phase   |

## Data Collection Strategy

### Phase 1: Research & Discovery (Week 1)
**Objective**: Identify actual data sources and availability for each DNO

#### Day 1-2: SSEN (Scottish & Southern)
- **Data Portal**: https://data.ssen.co.uk/
- **Charges**: https://www.ssen.co.uk/our-services/connections/charges-and-agreements/
- **Expected Data**:
  - DUoS charges for SSES/SHEPD areas
  - Network capacity information
  - Distributed generation connections
  - Network performance statistics

#### Day 3-4: NGED (National Grid Distribution)
- **Open Data**: https://connecteddata.westernpower.co.uk/
- **Charges**: https://www.nationalgrideso.com/connections-and-charges
- **Expected Data**:
  - DUoS charges for 4 license areas
  - Generation connection queue
  - Network utilization data
  - Innovation project data

#### Day 5-7: ENWL, NPG, SPD
- **ENWL**: https://www.enwl.co.uk/about-us/regulatory-and-governance/regulatory-reporting/
- **NPG**: https://www.northernpowergrid.com/network-information
- **SPD**: https://www.spenergynetworks.co.uk/pages/distribution_network_data.aspx

### Phase 2: Collector Development (Week 2)
**Objective**: Build DNO-specific data collection tools

#### Technical Requirements
```python
# Each DNO collector needs:
class DNOCollector:
    def discover_data_sources()     # Find CSV/API endpoints
    def collect_duos_charges()      # Priority: standardized charges
    def collect_network_data()      # Capacity, utilization
    def collect_generation_data()   # DG connections
    def map_to_bigquery_schema()    # Standardized output
```

#### Data Priorities
1. **DUoS Charges** (Highest) - Standardized across all DNOs
2. **Network Capacity** - Critical for planning
3. **Connection Queue** - Generation pipeline
4. **Performance Stats** - Network reliability
5. **Innovation Data** - Future technologies

### Phase 3: Integration & Testing (Week 3)
**Objective**: Ensure data quality and BigQuery compatibility

#### Schema Standardization
```sql
-- Standardized DNO table structure
CREATE TABLE `uk_energy_insights.dno_{area}_duos_charges` (
  dno_code STRING,          -- SSEN, NGED, etc.
  license_area STRING,      -- SSES, SHEPD, etc.
  voltage_level STRING,     -- LV, HV, EHV
  tariff_category STRING,   -- Capacity, Fixed, Unit
  charge_rate FLOAT64,      -- Rate in pence/kWh or £/kVA
  effective_date DATE,
  data_source STRING,
  collection_timestamp TIMESTAMP
);
```

## Implementation Roadmap

### Week 1: Discovery Phase
```bash
# Day 1-2: SSEN Research
python collect_ssen_data.py --mode=discover
python collect_ssen_data.py --mode=collect --dry-run

# Day 3-4: NGED Research
python collect_nged_data.py --mode=discover
python collect_nged_data.py --mode=collect --dry-run

# Day 5-7: Others
python collect_enwl_data.py --mode=discover
python collect_npg_data.py --mode=discover
python collect_spd_data.py --mode=discover
```

### Week 2: Collection Development
```bash
# Build collectors for each DNO
python collect_ssen_data.py --mode=collect --upload=false
python collect_nged_data.py --mode=collect --upload=false
python collect_enwl_data.py --mode=collect --upload=false
python collect_npg_data.py --mode=collect --upload=false
python collect_spd_data.py --mode=collect --upload=false
```

### Week 3: Integration & Upload
```bash
# Test BigQuery integration
python test_dno_bigquery_schemas.py
python validate_dno_data_quality.py

# Execute full collection
python collect_all_dno_data.py --execute --upload=true
```

## Expected Outcomes

### Data Volume Estimates
- **SSEN**: ~15-20 tables (charges, network, generation)
- **NGED**: ~20-25 tables (4 license areas)
- **ENWL**: ~10-15 tables (single area)
- **NPG**: ~15-20 tables (2 license areas)
- **SPD**: ~15-20 tables (2 license areas)

**Total**: ~75-100 additional tables

### Coverage Improvement
- **Current**: 1/6 DNOs (17% coverage)
- **After collection**: 6/6 DNOs (100% coverage)
- **Geographic coverage**: Complete UK electricity distribution network

### Data Types Available
1. **DUoS Charges**: All voltage levels, all tariff categories
2. **Network Capacity**: Available capacity by voltage level
3. **Generation Connections**: DG queue and connected capacity
4. **Network Performance**: Reliability statistics
5. **Innovation Projects**: Future network technologies
6. **Demand Data**: Distribution-level demand patterns

## Technical Challenges & Solutions

### Challenge 1: Varying Data Formats
**Solution**: Build format-specific parsers for each DNO
```python
class DataFormatHandler:
    def parse_csv(self, url)        # Standard CSV files
    def parse_excel(self, url)      # Excel spreadsheets
    def parse_api(self, endpoint)   # JSON APIs
    def parse_html(self, url)       # Web-scraped data
```

### Challenge 2: Schema Standardization
**Solution**: Common data model with DNO-specific mappings
```python
# Standardized field mapping
FIELD_MAPPINGS = {
    'SSEN': {'tariff_rate': 'rate_pence_kwh'},
    'NGED': {'tariff_rate': 'charge_rate'},
    'UKPN': {'tariff_rate': 'unit_rate'}
}
```

### Challenge 3: Data Quality & Validation
**Solution**: Comprehensive validation pipeline
```python
def validate_dno_data(df, dno_code):
    # Check required fields
    # Validate data types
    # Check for duplicates
    # Verify date ranges
    # Compare with known patterns
```

## Immediate Next Steps

### This Week
1. **Research SSEN data sources** - Identify CSV/API endpoints
2. **Build SSEN collector** - First working implementation
3. **Test BigQuery integration** - Ensure schema compatibility
4. **Document collection patterns** - Reusable for other DNOs

### Next Week
1. **Scale to NGED** - Second largest DNO
2. **Parallel development** - ENWL, NPG, SPD collectors
3. **Quality assurance** - Data validation and testing
4. **Integration testing** - End-to-end pipeline

### Week 3
1. **Full collection execution** - All 5 remaining DNOs
2. **Data validation** - Quality checks and corrections
3. **Documentation** - Complete collection documentation
4. **Monitoring setup** - Ongoing data collection monitoring

## Success Metrics

### Quantitative
- ✅ 6/6 DNOs collected (100% coverage)
- ✅ ~100 additional tables in BigQuery
- ✅ All major data types available
- ✅ Schema compliance across all DNOs

### Qualitative
- ✅ Complete UK electricity distribution network coverage
- ✅ Standardized data access across all DNOs
- ✅ Automated collection pipelines
- ✅ Comprehensive UK energy system dataset

---

**Next Action**: Begin SSEN data source research and collector development.
