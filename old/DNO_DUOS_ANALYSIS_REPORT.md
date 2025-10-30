# DNO DUoS Rate Analysis Report
*Generated on: 2025-09-15*

## Overview

This report presents an analysis of Distribution Network Operator (DNO) Distribution Use of System (DUoS) charges across different UK network operators and years. The analysis organizes and visualizes rate trends to identify patterns and variations between different DNOs.

## Data Sources

The analysis is based on the following primary data sources:

- **DNO_DUoS_All_Data.csv**: Comprehensive dataset with all DUoS rates across DNOs and years
- **DNO_Reference.csv**: Master reference table for mapping MPAN distributor IDs to DNO information

## Analysis Process

1. **Data Organization**:
   - Standardized year/date information
   - Grouped data by DNO and date
   - Calculated statistical measures for rates (min, max, mean, median)
   - Created a time-series friendly dataset in `Organised_DNO_By_Date.csv`

2. **Visualization**:
   - Created trend charts for rate changes over time
   - Generated comparative visualizations between DNOs
   - Produced heatmaps to identify patterns across years and DNOs

## Key Findings

### Rate Trends Over Time

The analysis shows a general upward trend in DUoS rates across most DNOs over the years, with significant acceleration after 2020. Some notable observations:

- National Grid's areas (formerly Western Power Distribution) show the steepest increases
- Electricity North West shows moderate increases with lower volatility
- Scottish networks (SSE-SHEPD and SSE-SEPD) exhibit more stable rates over time

### DNO Comparison

Based on the 2026 data (latest available):

- NGED-SW (National Grid Electricity Distribution - South West) has the highest median rates
- UKPN-LPN (UK Power Networks - London) shows elevated rates compared to other UKPN regions
- Northern regions generally have lower rates than southern regions

### Rate Volatility

The standard deviation of rates reveals:

- NGED regions show the highest volatility in rates
- SSE regions demonstrate the most stable rates
- The spread between minimum and maximum rates has widened significantly in recent years

## Files Generated

1. **Organised_DNO_By_Date.csv**: Time-series dataset of DUoS rates by DNO
2. **Visualization Plots**:
   - **mean_rates_by_dno_over_time.png**: Trend lines of mean rates by DNO
   - **min_max_rates_by_dno.png**: Range of rates for each DNO over time
   - **duos_rates_heatmap.png**: Heat map showing rate patterns by DNO and year
   - **median_rates_latest_year.png**: Bar chart comparing DNOs in the latest year
   - **dno_rate_statistics.csv**: Statistical summary of DNO rates

## Tools Used

- **organize_dno_by_date.py**: Script for data organization and time-series preparation
- **visualize_dno_rates.py**: Script for generating visualizations and statistics
- **mpan_dno_mapper.py**: Tool for mapping MPAN distributor IDs to DNO information

## Recommendations

1. **Rate Forecasting**: The consistent upward trend suggests potential for predictive modeling of future rates
2. **Consumer Impact Analysis**: Investigate how these rate differences affect consumer bills across regions
3. **Regulatory Analysis**: Examine the relationship between regulatory changes and rate increases
4. **Enhanced Visualization**: Consider interactive dashboards to explore the data dynamically

## Next Steps

1. **Incorporate Time Bands**: Analyze how rates vary by time of day (RED, AMBER, GREEN bands)
2. **Add Capacity Charges**: Extend the analysis to include fixed and capacity charges
3. **Regional Factors**: Correlate with regional factors (population density, infrastructure age)
4. **Consumer Impact**: Calculate typical bill impacts for different consumer profiles

---

*Report prepared using Python data analysis tools (pandas, matplotlib, seaborn)*
