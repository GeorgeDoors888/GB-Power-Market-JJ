# UK Energy BigQuery Dataset Analysis Report

## Dataset Overview

The UK Energy dataset in BigQuery (`jibber-jabber-knowledge.uk_energy_prod`) contains the following tables:

| Table Name | Rows | Size (MB) | Description |
|------------|------|-----------|-------------|
| neso_interconnector_flows | 210,528 | 21.35 | Data on interconnector flows between UK and connected countries |
| neso_wind_forecasts | 175,440 | 15.09 | Wind generation forecasts and actuals |
| neso_carbon_intensity | 157,896 | 41.90 | Carbon intensity measurements and forecasts |
| neso_balancing_services | 35,088 | 2.41 | Cost and volume data for balancing services |
| neso_demand_forecasts | 35,088 | 2.14 | Demand forecasts including temperature data |
| elexon_system_warnings | 48 | 0.01 | System warnings and events |
| elexon_demand_outturn | 0 | 0.00 | Demand outturn data (empty) |
| elexon_generation_outturn | 0 | 0.00 | Generation outturn data (empty) |

The data spans from January 1, 2023 to December 31, 2024, with this analysis focusing on December 2024.

## Key Findings

### 1. Correlation Analysis

The strongest correlations identified in the December 2024 data:

- **Balancing Volume and Balancing Cost** (0.73, positive): As expected, the total volume of balancing services (MWh) strongly correlates with the total cost of balancing services (£). This indicates that higher volumes of balancing actions lead to higher costs in a somewhat linear fashion.

- **Balancing Cost and Cost per MWh** (0.63, positive): Total balancing costs correlate strongly with the unit cost (£/MWh), suggesting that periods of high balancing needs not only involve more volume but also tend to be more expensive per unit.

- **Settlement Period and Carbon Intensity** (0.52, positive): Carbon intensity tends to increase throughout the day, with higher values in later settlement periods. This likely reflects the daily pattern of electricity demand and the corresponding generation mix changes.

- **System Warnings and Day of Week** (-0.27, negative): System warnings appear to have a weak negative correlation with the day of the week, potentially indicating fewer warnings on weekends.

- **Interconnector Flow and Utilization** (-0.21, negative): Surprisingly, there's a weak negative correlation between total flow and average utilization percentage across interconnectors.

### 2. Regression Analysis

#### Carbon Intensity Model

The regression model for carbon intensity using wind generation and temperature as predictors:

- **R-squared: 0.002** - The model explains only 0.2% of the variation in carbon intensity, indicating these factors alone are not good predictors for December 2024 data.

- **Wind Generation coefficient: 0.012 (p=0.594)** - The effect of wind generation on carbon intensity is not statistically significant.

- **Temperature coefficient: 0.137 (p=0.348)** - Temperature also does not show a statistically significant relationship with carbon intensity.

#### Balancing Cost Model

The regression model for balancing costs (£/MWh) using wind generation, temperature, and carbon intensity:

- **R-squared: 0.007** - The model explains only 0.7% of the variation in balancing costs.

- **Wind Generation coefficient: -0.002 (p=0.030)** - Wind generation has a small but statistically significant negative effect on balancing costs, suggesting slightly lower balancing costs with higher wind generation.

- **Temperature coefficient: -0.001 (p=0.765)** - Not statistically significant.

- **Carbon Intensity coefficient: -0.001 (p=0.659)** - Not statistically significant.

### 3. Seasonal Analysis

For December 2024 (Winter):

- **Wind Generation**: Average of 211.43 MW with a standard deviation of 45.00 MW.

- **Carbon Intensity**: Average of 158.24 gCO2/kWh with a standard deviation of 25.77 gCO2/kWh.

These values represent the winter season patterns, which is the only season in our analyzed period.

## Time Series Analysis

Time series decomposition was performed for both wind generation and carbon intensity, with the resulting plots saved in the output directory:

- `wind_generation_decomposition.png`
- `carbon_intensity_decomposition.png`

The analysis separated the data into trend, seasonal, and residual components to better understand the patterns and variations over time.

## Conclusions

1. **Balancing Mechanism Insights**: The strong correlation between balancing volumes and costs confirms expected market behavior, while the correlation with cost per MWh suggests potential market inefficiencies during high-demand periods.

2. **Limited Predictive Power**: The regression models showed very limited explanatory power (low R-squared values), indicating that the selected variables (wind generation, temperature, carbon intensity) don't effectively predict the target variables in December 2024.

3. **Wind Generation Impact**: Despite the low R-squared, wind generation showed a statistically significant (though small) negative effect on balancing costs, suggesting a potential cost-saving effect.

4. **Daily Carbon Intensity Pattern**: The correlation between settlement period and carbon intensity points to a clear daily pattern in the carbon intensity of electricity generation.

5. **Data Quality Note**: Some tables (elexon_demand_outturn, elexon_generation_outturn) were empty, limiting the scope of analysis.

## Recommendations

1. **Expand the Analysis Timeframe**: Analyzing a full year would provide better insights into seasonal patterns and allow for more robust time series modeling.

2. **Add More Predictors**: Include additional variables such as demand forecast errors, outage data, and market prices to improve the predictive power of regression models.

3. **Explore Grid Stress Events**: Further investigate the relationship between system warnings, balancing costs, and grid conditions.

4. **Interconnector Analysis**: Conduct a more detailed analysis of interconnector flows by country and direction.

5. **Seasonal Model Comparison**: Develop separate models for different seasons to capture varying relationships between variables throughout the year.

This report provides an initial analysis of the UK Energy dataset for December 2024. Further analysis with expanded data and more sophisticated models would yield deeper insights into the UK energy system dynamics.
