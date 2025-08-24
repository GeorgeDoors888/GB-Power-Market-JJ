# Elexon Insights API Smoke Test Suite

## Overview
This smoke test suite extracts and tests endpoints from the complete Elexon Insights API OpenAPI specification. It provides comprehensive testing capabilities for the Elexon BMRS and Insights APIs.

## Files Created

### 1. Configuration Files
- `config:comprehensive_endpoints.yml` - All 294 endpoints from 29 categories
- `config:sample_endpoints.yml` - Sample endpoints for quick testing
- `config:focused_test.yml` - Curated key endpoints from major categories

### 2. Testing Scripts
- `extract_api_endpoints.py` - Extracts endpoints from OpenAPI JSON specification
- `enhanced_smoke_test.py` - Basic smoke testing with categorization
- `comprehensive_smoke_test.py` - Advanced testing with multiple parameter strategies

## Test Results Summary

### Latest Comprehensive Test Results
- **Total Endpoints Tested:** 14 (curated selection)
- **Success Rate:** 71.4% (10/14 successful)
- **Total Data Rows Retrieved:** 50,008 rows
- **Data Coverage:** 1 week (2025-08-01 to 2025-08-08)

### Category Performance
| Category | Success Rate | Rows Retrieved | Status |
|----------|-------------|----------------|---------|
| Demand | 100% (2/2) | 3,398 | ✅ Excellent |
| Generation Forecast | 100% (2/2) | 3,192 | ✅ Excellent |
| System | 100% (2/2) | 39,986 | ✅ Excellent |
| Market Pricing | 100% (1/1) | 674 | ✅ Excellent |
| Generation Actual | 50% (1/2) | 2,017 | ⚠️ Partial |
| BMRS Key Datasets | 67% (2/3) | 741 | ⚠️ Partial |
| Balancing Mechanism | 0% (0/2) | 0 | ❌ Failed |

### Successful Endpoints
1. **Demand**
   - `/demand` - Real demand data (1,381 rows)
   - `/demand/rollingSystemDemand` - Rolling system demand (2,017 rows)

2. **Generation Forecast**
   - `/forecast/availability/daily` - Daily generation forecasts (247 rows)
   - `/forecast/availability/weekly` - Weekly generation forecasts (2,945 rows)

3. **System**
   - `/system/frequency` - System frequency data (39,985 rows - highest volume!)
   - `/system/warnings` - System warnings (1 row)

4. **Generation Actual**
   - `/generation/outturn` - Generation outturn data (2,017 rows)

5. **BMRS Datasets**
   - `/datasets/FUELHH` - Fuel generation half-hourly (740 rows)
   - `/datasets/INDO` - Initial demand outturn (1 row)

6. **Market Pricing**
   - `/balancing/pricing/market-index` - Market index pricing (674 rows)

### Failed Endpoints (404 Not Found)
- `/generation/actual/streams`
- `/balancing/bid-offer`
- `/balancing/acceptances`
- `/datasets/B1610`

## API Insights

### Data Volume by Category
1. **System Frequency** - 39,985 rows (79.9% of all data)
2. **Demand** - 3,398 rows (6.8%)
3. **Generation Forecast** - 3,192 rows (6.4%)
4. **Generation Actual** - 2,017 rows (4.0%)
5. **BMRS Datasets** - 741 rows (1.5%)
6. **Market Pricing** - 674 rows (1.3%)

### Parameter Strategies
The test suite uses multiple parameter combinations:
1. Standard: `from`, `to`, `apiKey`, `format`
2. No dates: `apiKey`, `format`
3. Settlement date: `settlementDate`, `apiKey`, `format`
4. Minimal: `apiKey` only

### Response Formats
- Most endpoints return JSON with `data` array
- Some return direct arrays
- All successful endpoints provide structured data suitable for pandas DataFrames

## Usage Instructions

### Quick Test (Sample Endpoints)
```bash
cd "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber"
source venv/bin/activate
python enhanced_smoke_test.py
```

### Comprehensive Test (Curated Key Endpoints)
```bash
cd "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber"
source venv/bin/activate
python comprehensive_smoke_test.py
```

### Extract New Endpoints from Updated API Spec
```bash
cd "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber"
source venv/bin/activate
python extract_api_endpoints.py
```

## API Key Configuration
Set your BMRS API key in the `api.env` file:
```
BMRS_API_KEY=your_32_character_api_key_here
```

## Dependencies
- requests
- pandas
- pyyaml
- python-dotenv

## Data Quality Assessment
- **High Quality Categories:** Demand, Generation Forecast, System, Market Pricing
- **Medium Quality Categories:** Generation Actual, BMRS Datasets  
- **Low Quality Categories:** Balancing Mechanism (endpoints may be deprecated or require special access)

## Recommendations
1. Focus on the high-success categories for production use
2. Investigate 404 errors for balancing mechanism endpoints
3. Consider the system frequency endpoint for high-volume data needs
4. Use the sample configuration for quick API health checks
5. Use the comprehensive configuration for full API coverage testing

## Next Steps
1. Set up automated daily/weekly smoke tests using cron or Airflow
2. Add data quality checks (e.g., expected data ranges, required fields)
3. Implement alerting for API degradation
4. Create dashboards showing API health metrics over time
5. Investigate authentication requirements for failed endpoints
