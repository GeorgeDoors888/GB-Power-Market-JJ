# Interactive Analysis Dashboard - Quick Guide

## Overview

`interactive_analysis_dashboard.py` provides an interactive command-line interface for filtering OFR pricing and constraint geography analyses by custom date ranges.

## Features

✅ **Date Range Selection**
- Interactive prompts for "From" and "To" dates
- Default: Last 30 days
- Format: YYYY-MM-DD

✅ **Multiple Analysis Types**
1. OFR Pricing Analysis (DISBSAD)
2. Constraint Geography Analysis (BOALF)
3. Both analyses together

✅ **Automatic CSV Export**
- Optional export to timestamped CSV files
- Format: `ofr_pricing_YYYY-MM-DD_YYYY-MM-DD.csv`
- Format: `constraints_YYYY-MM-DD_YYYY-MM-DD.csv`

## Usage

### Basic Usage (Interactive Prompts)
```bash
python3 interactive_analysis_dashboard.py
```

### Example Session
```
╔══════════════════════════════════════════════════════════════╗
║     INTERACTIVE ANALYSIS DASHBOARD                          ║
║     OFR Pricing & Constraint Geography                      ║
╚══════════════════════════════════════════════════════════════╝

============================================================
DATE RANGE SELECTION
============================================================
From date (YYYY-MM-DD) [default: 2025-11-09]: 2025-11-01
To date (YYYY-MM-DD) [default: 2025-12-09]: 2025-12-09

✓ Date range: 2025-11-01 to 2025-12-09 (38 days)

============================================================
ANALYSIS OPTIONS
============================================================
1. OFR Pricing Analysis (DISBSAD)
2. Constraint Geography Analysis (BOALF)
3. Both Analyses
============================================================
Select analysis (1/2/3): 3

Export results to CSV? (y/n) [y]: y

🔄 Running OFR pricing analysis (2025-11-01 to 2025-12-09)...

============================================================
OFR PRICING RESULTS
============================================================
Actions:       4,235
Total cost:    £6,123,456.78
Total volume:  55,678.90 MWh
Avg price:     £109.98/MWh
Price range:   £68.50 - £205.00/MWh
Median:        £106.50/MWh
============================================================
✓ Exported to: ofr_pricing_2025-11-01_2025-12-09.csv

🔄 Running constraint analysis (2025-11-01 to 2025-12-09)...

============================================================
CONSTRAINT GEOGRAPHY RESULTS
============================================================
Total actions:  89,234
Total MW adj:   2,987,654.0 MW

Top 5 Categories:
------------------------------------------------------------
Transmission (National Grid) Wind              45,678 actions  1,789,234.0 MW ( 59.9%)
Transmission (National Grid) CCGT / Gas         6,890 actions    523,456.0 MW ( 17.5%)
Transmission (National Grid) PS                 4,123 actions    187,654.0 MW (  6.3%)
England & Wales          OTHER              5,234 actions     48,765.0 MW (  1.6%)
England & Wales          Wind               1,987 actions     29,876.0 MW (  1.0%)
============================================================
✓ Exported to: constraints_2025-11-01_2025-12-09.csv

✅ Analysis complete!
```

## Date Range Examples

### Last 7 Days
```
From date: 2025-12-02
To date:   2025-12-09
```

### Last 30 Days (Default)
```
From date: [press Enter]
To date:   [press Enter]
```

### Custom Period (e.g., October 2025)
```
From date: 2025-10-01
To date:   2025-10-31
```

### Year-to-Date
```
From date: 2025-01-01
To date:   2025-12-09
```

## Output Files

### OFR Pricing CSV
```csv
n_actions,total_cost_gbp,total_volume_mwh,avg_price_per_mwh,min_price,max_price,median_price
4235,6123456.78,55678.90,109.98,68.50,205.00,106.50
```

### Constraint Geography CSV
```csv
region,fuel_group,n_actions,total_mw_adjusted,share_pct
Transmission (National Grid),Wind,45678,1789234.0,59.9
Transmission (National Grid),CCGT / Gas,6890,523456.0,17.5
...
```

## Integration with Other Scripts

### Compare with Standard Analysis
```bash
# Interactive (custom dates)
python3 interactive_analysis_dashboard.py

# Standard 30-day analysis
python3 ofr_pricing_analysis.py --days 30 --compare-non-ofr
```

### Batch Processing Multiple Periods
```bash
# Create a loop for monthly analysis
for month in {01..12}; do
  python3 interactive_analysis_dashboard.py << EOF
2025-${month}-01
2025-${month}-28
1
y
EOF
done
```

## Troubleshooting

### "Failed to connect to BigQuery"
- Check credentials: `export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"`
- Verify project access: `gcloud auth list`

### "No actions found in date range"
- Check date format (YYYY-MM-DD)
- Verify data availability for period
- Historical data: bmrs_boalf (2023+)
- Real-time data: bmrs_boalf_iris (last 48h)

### "Invalid date format"
- Must use YYYY-MM-DD format
- Example: 2025-12-09 (not 09/12/2025 or 12-09-2025)

## Advanced Usage

### Programmatic Integration
```python
from interactive_analysis_dashboard import run_ofr_analysis, run_constraint_analysis
from google.cloud import bigquery
from datetime import date

client = bigquery.Client(project="inner-cinema-476211-u9")
start = date(2025, 11, 1)
end = date(2025, 12, 9)

# Run analyses programmatically
ofr_df = run_ofr_analysis(client, start, end, export_csv=True)
constraint_df = run_constraint_analysis(client, start, end, export_csv=True)

# Further processing...
```

## Performance Notes

- **OFR Analysis**: ~1-2 seconds per 30 days
- **Constraint Analysis**: ~3-5 seconds per 30 days
- **Both**: ~5-7 seconds total
- Longer periods (90+ days) may take 10-20 seconds

## Related Documentation

- [OFR Pricing Methodology](docs/OFR_PRICING_METHODOLOGY.md)
- [Constraint Analysis Guide](docs/WHY_CONSTRAINT_COSTS_ARE_NA.md)
- [Standard Analysis Scripts](README.md#common-tasks)

## Support

For issues or questions:
- Email: george@upowerenergy.uk
- Check: [DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)
