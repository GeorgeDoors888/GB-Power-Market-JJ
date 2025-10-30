# Missing BMRS Datasets - API Mapping

Based on the BMRS API documentation and your requirements, here's the mapping for the missing datasets:

## Available through Standard BMRS API (should work with current script):

### ✅ Already in your script but may need to be enabled:
- **NETBSAD** → `bmrs_netbsad` (Net Balancing Services Adjustment Data)
- **COSTS** → `bmrs_costs` (System Buy/Sell Prices)
- **STOR** → `bmrs_stor` (Short Term Operating Reserve) - ADDED to script
- **NDF** → `bmrs_ndf` (National Demand Forecast)
- **TSDF** → `bmrs_tsdf` (Transmission System Demand Forecast)

### 🔍 Need to check if available in BMRS:
- **NDFD** → Day-ahead National Demand Forecast
- **NDFW** → Week-ahead National Demand Forecast
- **TSDFD** → Day-ahead Transmission System Demand Forecast
- **TSDFW** → Week-ahead Transmission System Demand Forecast

## Available through Insights API (need different approach):

### 📊 Demand and Generation Data:
- **Restoration region demand** → Insights API endpoint
- **Triad peaks** → Insights API endpoint
- **Surplus/Margin forecasts** → Insights API endpoint
- **Total Load forecasts** → Insights API endpoint

## Current Ingestion Status:

The ingestion script is currently running with:
```bash
python ingest_elexon_fixed.py --start 2024-01-01 --end 2025-09-20 --only NETBSAD,COSTS,STOR,NDF,TSDF --log-level INFO
```

This should add the following tables to your BigQuery dataset:
- `bmrs_netbsad`
- `bmrs_costs`
- `bmrs_stor`
- `bmrs_ndf`
- `bmrs_tsdf`

## Next Steps:

1. **Wait for current ingestion to complete** (running now)
2. **Validate the new tables** are created
3. **Add additional forecast datasets** (NDFD, NDFW, TSDFD, TSDFW) if available
4. **Implement Insights API integration** for Restoration/Triad data if needed

## Key Insights API Endpoints (for future implementation):

- `/demand/peak/triad` - Triad peak demand data
- `/forecast/margin/daily` - Daily margin forecasts
- `/forecast/surplus/daily` - Daily surplus forecasts
- `/demand/outturn` - Demand outturn data
- `/restoration/region/demand` - Restoration region data (if available)
