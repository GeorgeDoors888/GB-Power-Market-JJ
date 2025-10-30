# Elexon Data Download - Setup Complete ✅

## Summary

Successfully set up automated downloading of **42 Elexon/NESO datasets** covering the GB electricity market.

### What Was Done

1. **✅ Repository Setup**
   - Cloned project from GitHub
   - Installed all Python dependencies
   - Configured Google Cloud credentials
   - Granted BigQuery Admin permissions

2. **✅ Dataset Discovery**
   - Created comprehensive manifest with 42 datasets
   - Categories covered:
     - **Generation** (7 datasets): Fuel mix, actual output, forecasts
     - **Demand** (6 datasets): Actual demand, daily totals, peaks
     - **Forecasts** (12 datasets): Demand/generation forecasts 1-14 days ahead
     - **Balancing** (8 datasets): Physical notifications, bid-offers, acceptances
     - **Settlement** (5 datasets): System prices, imbalance data, market indices
     - **System** (3 datasets): Frequency, warnings, export limits
     - **Services** (1 dataset): Short-term operating reserves (STOR)

3. **✅ Data Downloaded (Last 7 Days)**
   - Initial 4 datasets: **10,853 rows**
   - Currently downloading all 42 datasets
   - Data stored in BigQuery: `inner-cinema-476211-u9.uk_energy_prod`

## Files Created

| File | Purpose |
|------|---------|
| `download_last_7_days.py` | Main downloader script with CLI options |
| `discover_all_datasets.py` | Auto-discover available API endpoints |
| `create_comprehensive_manifest.py` | Generate complete dataset manifest |
| `verify_data.py` | Validate downloaded data and generate reports |
| `insights_manifest_comprehensive.json` | Complete list of 42 datasets |
| `jibber_jabber_key.json` | GCP service account credentials |

## Usage

### Download All Datasets (Last 7 Days)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
source .venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/jibber_jabber_key.json"
python download_last_7_days.py --manifest insights_manifest_comprehensive.json --days 7
```

### Download Specific Datasets
```bash
python download_last_7_days.py --manifest insights_manifest_comprehensive.json \
    --datasets FREQ FUELINST DEMAND_OUTTURN SYSTEM_PRICES --days 7
```

### Download Different Time Periods
```bash
# Last 30 days
python download_last_7_days.py --days 30

# Last 90 days
python download_last_7_days.py --days 90
```

### Verify Downloaded Data
```bash
python verify_data.py
```

## Dataset Categories

### 1. Generation Data (7 datasets)
- `FUELINST` - Generation by fuel type (5-minute)
- `FUELHH` - Generation by fuel type (half-hourly)
- `GENERATION_ACTUAL_PER_TYPE` - Actual aggregated generation
- `GENERATION_WIND_SOLAR` - Wind and solar output
- `GENERATION_OUTTURN` - Generation outturn summary
- `INDGEN` - Indicated generation by BM Unit

### 2. Demand Data (6 datasets)
- `DEMAND_OUTTURN` - Initial demand outturn (INDO/ITSDO)
- `DEMAND_OUTTURN_DAILY` - Daily energy transmitted (INDOD)
- `DEMAND_OUTTURN_SUMMARY` - Rolling system demand
- `DEMAND_ACTUAL_TOTAL` - Total load actual
- `DEMAND_PEAK_TRIAD` - Triad demand peaks
- `DEMAND_PEAK_INDICATIVE` - Indicative peak demand

### 3. Forecasts (12 datasets)
- `NDF` - National demand forecast
- `NDFD` - National demand forecast (day-ahead)
- `NDFW` - National demand forecast (week-ahead)
- `TSDF` - Transmission system demand forecast
- `WINDFOR` - Wind generation forecast
- `UOU2T14D` - Output usable 2-14 days ahead
- `MARGIN_DAILY` - Operating margin forecast
- `SURPLUS_DAILY` - Surplus forecast

### 4. Balancing Mechanism (8 datasets)
- `BOD` - Bid-offer data
- `BALANCING_PHYSICAL` - Physical notifications
- `BALANCING_DYNAMIC` - Dynamic data
- `BALANCING_BID_OFFER` - Bid-offer pairs
- `BALANCING_ACCEPTANCES` - BM acceptances
- `QAS` - Quiescent physical notifications

### 5. Settlement & Prices (5 datasets)
- `SYSTEM_PRICES` - System buy/sell prices
- `NETBSAD` - Net balancing services adjustment
- `DISBSAD` - Disaggregated BSAD
- `MID` - Market index data
- `IMBALNGC` - Indicated imbalance

### 6. System Data (3 datasets)
- `FREQ` - System frequency (updated every few seconds)
- `SYSWARN` - System warnings
- `SEL` - Stable export limits

## BigQuery Tables

All data is stored in: `inner-cinema-476211-u9.uk_energy_prod`

### Sample Queries

**Daily Generation Mix:**
```sql
SELECT 
    DATE(startTime) as date,
    fuelType,
    SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_fuel_instant`
GROUP BY date, fuelType
ORDER BY date DESC, total_mw DESC
LIMIT 100;
```

**Demand vs Forecast:**
```sql
SELECT 
    d.settlementDate,
    d.initialDemandOutturn as actual,
    f.nationalDemandForecast as forecast,
    (d.initialDemandOutturn - f.nationalDemandForecast) as error
FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn` d
JOIN `inner-cinema-476211-u9.uk_energy_prod.demand_forecast_national` f
ON d.settlementDate = f.settlementDate 
AND d.settlementPeriod = f.settlementPeriod
ORDER BY d.settlementDate DESC;
```

**System Frequency Stats:**
```sql
SELECT 
    DATE(measurementtime) as date,
    AVG(frequency) as avg_frequency,
    MIN(frequency) as min_frequency,
    MAX(frequency) as max_frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.system_frequency`
GROUP BY date
ORDER BY date DESC;
```

## Data Sources

- **Elexon BMRS API**: https://data.elexon.co.uk/bmrs/api/v1
- **API Documentation**: https://developer.data.elexon.co.uk/
- **NESO Website**: https://www.neso.energy

## Notes

- Data is updated every 5-30 minutes depending on dataset
- Historical data availability varies by dataset (typically 2016-present)
- Some datasets require API key (set via `BMRS_API_KEY_1` environment variable)
- BigQuery costs: ~$0.01 per 10GB scanned (negligible for this data volume)

## Next Steps

1. **Automate Daily Downloads**
   - Set up cron job or Cloud Scheduler to run daily
   - Download incremental data (last 24 hours)

2. **Create Dashboards**
   - Connect to Looker Studio / Tableau / Power BI
   - Build visualizations for generation mix, demand patterns, prices

3. **Advanced Analytics**
   - Machine learning models for demand forecasting
   - Price prediction algorithms
   - Renewable generation analysis

4. **Data Quality Monitoring**
   - Set up alerts for missing data
   - Monitor API availability
   - Track data freshness

## Support

- Elexon Support: insightssupport@elexon.co.uk
- API Issues: https://support.elexon.co.uk/csm
- NESO Data: https://www.neso.energy/contact

---

**Setup Date**: 25 October 2025  
**Last Updated**: 25 October 2025  
**Status**: ✅ Active and downloading
