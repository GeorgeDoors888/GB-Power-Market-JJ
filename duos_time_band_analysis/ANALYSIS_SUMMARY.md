# DUoS Time Band Analysis Results

This analysis has successfully extracted DUoS (Distribution Use of System) time band information and rates from Excel files across multiple Distribution Network Operators (DNOs). The analysis provides a comprehensive view of how each DNO structures their Red, Amber, and Green time bands, and the associated rates for each band.

## Key Findings

1. **DNO Coverage**:
   - The analysis identified data for 3 DNOs: SP Manweb (MPAN 13), SSEN Hydro (MPAN 17), and SSEN Southern (MPAN 20)
   - SP Manweb files were found for years 2020-2026, but rate data could not be extracted
   - SSEN Hydro data was available for 2025-2026 with complete rate information
   - SSEN Southern data was available for 2025 with complete rate information

2. **Time Band Definitions**:
   - Most DNOs follow similar time period patterns:
     - RED bands: Typically weekday peak hours (4-7pm)
     - AMBER bands: Typically weekdays 07:00-16:00 and 19:00-23:00 (shoulder hours)
     - GREEN bands: Typically weekdays 23:00-07:00 and all weekend (off-peak hours)

3. **Rate Analysis**:
   - RED band rates are highest, ranging from -8.40 to 32.20 p/kWh (avg ~4.0 p/kWh)
   - AMBER band rates are medium, ranging from -2.93 to 8.97 p/kWh (avg ~1.0 p/kWh)
   - GREEN band rates are lowest, ranging from -0.63 to 6.85 p/kWh (avg ~0.3 p/kWh)
   - Negative rates represent cases where customers are paid for using electricity during certain periods

4. **Year-to-Year Trends**:
   - SSEN Hydro shows a slight decrease in AMBER and GREEN rates from 2025 to 2026
   - RED rates remain relatively stable across years

## Data Limitations

1. Unable to extract actual time period definitions for SP Manweb - the Excel files don't contain this information in a standard format
2. Could not extract rate data for SP Manweb files despite them being present
3. Limited year coverage for SSEN files (only 2025-2026)

## Next Steps

To enhance this analysis, we recommend:

1. Manually extracting time period definitions from SP Manweb documentation
2. Developing a specialized parser for SP Manweb rate sheets
3. Collecting data for additional years for SSEN
4. Expanding to other DNOs like UK Power Networks, Northern Powergrid, etc.
5. Creating a comprehensive visualization showing how time bands vary across DNOs throughout the day

## Visualization Insights

The visualizations in the `duos_time_band_analysis/plots` directory show:

1. **Band Rates Comparison**: Comparative view of RED, AMBER, and GREEN rates across DNOs
2. **DNO Comparison**: How rates vary between different DNOs
3. **Year Trend**: How rates are changing over time (limited to 2025-2026 for now)

This analysis provides valuable insights for energy consumers and businesses looking to optimize their electricity usage patterns to minimize DUoS charges.
