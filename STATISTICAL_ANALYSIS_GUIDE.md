# 📊 Advanced Statistical Analysis Guide for GB Power Market

**Date:** October 31, 2025  
**Purpose:** Comprehensive guide to interpreting statistical outputs for battery optimization, solar PV, market modeling, and transmission charging (DUoS/BSUoS/TNUoS)  
**Dataset:** `inner-cinema-476211-u9.uk_energy_prod` & `jibber-jabber-knowledge.uk_energy`

---

## 🎯 Executive Summary

This guide explains each output from the Advanced Statistical Analysis Suite and how to apply it to GB power market operations. All analyses are designed for operational decision-making in:

- **Battery Storage**: Charge/discharge scheduling, arbitrage windows
- **Solar PV**: Generation forecasting, curtailment risk
- **Market Modeling**: Price elasticity, supply-demand dynamics
- **Transmission Costs**: DUoS/BSUoS/TNUoS optimization

**Key Principle:** All timestamps align to **Elexon Settlement Periods** (30-min UTC). This ensures compatibility with settlement, balancing mechanisms, and transmission charging.

---

## 📈 Analysis Outputs Explained

### 1️⃣ **ttest_results** — SSP vs SBP Comparison

#### What It Is
Welch's t-test comparing mean System Sell Price (SSP) vs System Buy Price (SBP).

#### Why It Matters
**For Batteries:** The SBP–SSP spread is your **monetizable arbitrage window**:
- **Charge on SSP** (when system is long, prices lower)
- **Discharge on SBP** (when system is short, prices higher)

A statistically significant difference indicates **persistent market asymmetry** — this is the foundation of imbalance revenue.

**For Solar PV:** When SSP drops (high generation periods), understand whether it's systematically lower than SBP to plan curtailment strategies.

#### How to Read

```python
# Example output:
{
  "t_stat": 15.23,
  "p_value": 0.0001,
  "mean_SSP": 45.32,
  "mean_SBP": 52.18,
  "mean_diff": 6.86,      # Positive = SBP typically > SSP
  "ci_95_lo": 5.92,       # 95% confidence interval
  "ci_95_hi": 7.80,
  "n_SSP": 48520,
  "n_SBP": 48520
}
```

**Interpretation:**
- **mean_diff = +6.86**: SBP averages £6.86/MWh higher than SSP
- **p_value < 0.05**: Difference is statistically significant (not random)
- **CI [5.92, 7.80]**: 95% confident true difference is in this range
- **Wider CI = higher volatility** (more risk but also opportunity)

#### Pitfalls & Considerations
⚠️ **Non-normal tails**: Extreme event days (e.g., tight margin warnings) inflate variance  
⚠️ **Regime changes**: Coal phase-out, wind capacity additions change distributions  
⚠️ **Solution**: Run analysis by season or regime (pre/post-2023) for stability

#### Operational Use Cases
1. **Battery Revenue Estimation**: £6.86/MWh × round-trip efficiency × cycles/day
2. **Risk Assessment**: Wider CI = more volatile, size position accordingly
3. **Hedging Strategy**: If spread narrows over time (trend analysis), adjust commercial assumptions

---

### 2️⃣ **regression_temperature_ssp** — Weather Impact on SSP

#### What It Is
Ordinary Least Squares (OLS) regression: SSP = β₀ + β₁ × Temperature + ε

#### Why It Matters
**For Batteries:** Temperature drives heating/cooling demand:
- **Cold snaps** (< 5°C): Heating demand surges → SSP rises → charge earlier
- **Heat waves** (> 25°C): Cooling demand peaks → SSP rises → discharge opportunity

**For Solar PV:** Temperature affects both demand and solar efficiency (panels less efficient at high temps).

**For Cost Forecasting:** Temperature is a proxy for BSUoS volatility (NESO actions during extreme weather).

#### How to Read

```python
{
  "model": "OLS_SSP_on_Temperature",
  "n_obs": 45230,
  "r_squared": 0.12,           # 12% of SSP variance explained
  "adj_r_squared": 0.119,
  "intercept": 65.40,
  "slope_temperature": -1.23,  # Negative = milder temps → lower SSP
  "p_intercept": 0.0000,
  "p_temperature": 0.0001,     # Significant
  "plot_path": "output/reg_temperature_ssp.png"
}
```

**Interpretation:**
- **slope_temperature = -1.23**: Every 1°C increase → SSP drops £1.23/MWh
- **Negative slope typical**: Milder temps reduce heating demand → less generation needed
- **r_squared = 0.12**: Low, but normal for noisy prices (many factors at play)
- **p_temperature < 0.05**: Relationship is statistically significant

#### Pitfalls & Considerations
⚠️ **Temperature is a proxy**: Wind/solar generation, fuel prices also drive SSP  
⚠️ **Seasonal variation**: Heating vs cooling seasons have different dynamics  
⚠️ **Solution**: Use multi-factor regression (see #3) for complete picture

#### Operational Use Cases
1. **Day-Ahead Planning**: Met Office forecast shows -2°C overnight → expect SSP surge, pre-charge battery
2. **Seasonal Budgets**: Winter months budget +£10/MWh average SSP vs summer
3. **Solar Curtailment**: Cold + high wind = high SSP despite sunny day, don't curtail

---

### 3️⃣ **regression_volume_price** — Load, Wind, Temp → SSP

#### What It Is
Multi-factor OLS: SSP = β₀ + β₁×log(volume) + β₂×wind + β₃×temp + ε

Core **price elasticity model** incorporating:
- **Volume** (demand): Higher load → tighter system → higher prices
- **Wind**: Merit order effect (zero marginal cost displaces gas)
- **Temperature**: Demand proxy (heating/cooling)

#### Why It Matters
**For Batteries:** Forecast SSP for scheduling decisions:
- "If wind is +3 GW and demand +5%, what's expected SSP?"
- Quantify **demand response** opportunities

**For Market Modeling:** Understand which drivers have biggest impact (beta coefficients).

**For Solar PV:** See how your generation (via wind proxy) affects your own revenue.

#### How to Read

```python
{
  "model": "OLS_SSP_on_logVolume_controls",
  "n_obs": 42150,
  "r_squared": 0.38,              # 38% explained variance
  "adj_r_squared": 0.377,
  "intercept": -125.50,
  "beta_log_volume": 45.23,       # Higher demand → higher SSP
  "p_log_volume": 0.0000,
  "beta_wind": -0.012,            # More wind → lower SSP (merit order)
  "p_wind": 0.0003,
  "beta_temp": -0.85,             # Milder temps → lower SSP
  "p_temp": 0.0421
}
```

**Interpretation:**
- **beta_log_volume = +45.23**: 10% demand increase → +4.52 £/MWh SSP (log scale)
- **beta_wind = -0.012**: +1 GW wind → -£0.012/MWh (merit order suppression)
- **beta_temp = -0.85**: +1°C → -£0.85/MWh
- **r_squared = 0.38**: Much better than single-factor models

#### Pitfalls & Considerations
⚠️ **Endogeneity**: Prices influence volume via demand response (two-way causation)  
⚠️ **Treat as reduced-form**: Coefficients show associations, not pure causation  
⚠️ **Solution**: For policy analysis, use instrumental variables or structural models

#### Operational Use Cases
1. **Scenario Planning**: "What if winter evening peak with low wind?"
   - High volume (+10%) + low wind (-5 GW) = SSP +£4.52 -£0.06 = +£4.46/MWh
2. **Real-Time Adjustments**: Live wind forecast drops 2 GW → revise SSP up £0.024/MWh
3. **Solar Revenue Forecast**: High solar day = proxy high wind = lower SSP

---

### 4️⃣ **correlation_matrix** + **heatmap** — Variable Relationships

#### What It Is
Pearson correlation coefficients between all key variables:
- SSP, SBP, spread, volume, temperature, wind, balancing costs

Plus a color-coded heatmap for visual inspection.

#### Why It Matters
**For Dashboard Design:** Know which metrics to display together (high correlation = redundant).

**For Model Building:** Identify multicollinearity (don't use highly correlated features together).

**For Sanity Checks:** Verify expected relationships (e.g., wind ↔ SSP should be negative).

#### How to Read

```python
# Example correlations:
{
  "SSP vs volume": 0.42,           # Moderate positive (demand drives price)
  "SSP vs wind": -0.28,            # Negative (wind suppresses price)
  "spread vs balancing_cost": 0.51 # Strong positive (NESO actions widen spreads)
}
```

**Interpretation:**
- **|corr| > 0.4**: Strong relationship, use in forecasting
- **corr near 0**: Variables independent
- **Negative corr**: Inverse relationship (wind ↓ → SSP ↑)

**Heatmap Colors:**
- 🔴 Dark red: Strong positive correlation (+0.7 to +1.0)
- ⚪ White: No correlation (0)
- 🔵 Dark blue: Strong negative correlation (-1.0 to -0.7)

#### Pitfalls & Considerations
⚠️ **Correlation ≠ Causation**: High correlation doesn't mean one causes the other  
⚠️ **Outliers dominate**: One extreme event can skew correlations  
⚠️ **Solution**: Check by season or time of day for robustness

#### Operational Use Cases
1. **Feature Selection**: For ML models, drop variables with |corr| > 0.8 (redundant)
2. **Risk Hedging**: If spread and balancing cost highly correlated, hedge together
3. **Dashboard Design**: Don't show SSP and SBP separately if corr > 0.95 (use spread instead)

---

### 5️⃣ **arima_forecast_ssp** — Short-Term SSP Forecast

#### What It Is
SARIMAX (Seasonal AutoRegressive Integrated Moving Average with eXogenous variables):
- **Autoregressive**: Price depends on past prices
- **Seasonal**: Weekly patterns (weekday vs weekend)
- **Forecast horizon**: Next 24 hours (48 settlement periods)

Produces point forecast + 95% confidence interval.

#### Why It Matters
**For Battery Scheduling:** Operational planning for next-day charge/discharge windows:
- "Forecast shows SSP spike at 18:00 → pre-charge by 17:30"
- Overlay with DUoS red band (16:00-19:00) to optimize costs

**For Solar PV:** Forecast low SSP tomorrow afternoon → plan curtailment if needed.

**For Trading:** Day-ahead market bidding strategy.

#### How to Read

```python
# Example forecast output (next 48 periods):
{
  "ts": "2025-11-01 00:00:00",
  "forecast_ssp": 52.3,    # Point forecast
  "ci_lo": 48.1,           # Lower bound (95% CI)
  "ci_hi": 56.5,           # Upper bound (95% CI)
  "aic": 12543.2,          # Model fit metric (lower = better)
  "bic": 12589.7,
  "order": "(1,1,1)",
  "seasonal_order": "(1,1,1,336)",  # 48 SPs/day × 7 days
  "plot_path": "output/arima_ssp_forecast.png"
}
```

**Interpretation:**
- **forecast_ssp = 52.3**: Expected SSP is £52.30/MWh
- **CI [48.1, 56.5]**: 95% confident actual SSP will be in this range
- **Wide band = high uncertainty** (e.g., weather forecast uncertain)
- **AIC/BIC**: Use to compare model variants (lower is better fit)

#### Pitfalls & Considerations
⚠️ **Purely univariate**: Doesn't consider wind/demand/temperature forecasts  
⚠️ **Regime shifts**: Coal phase-out, new interconnectors change dynamics  
⚠️ **Solution**: Add exogenous variables (wind, demand forecasts) via `SARIMAX(..., exog=X)` for better accuracy

#### Operational Use Cases
1. **Battery Scheduling**: Forecast shows evening peak at £65/MWh → discharge 18:00-19:00
2. **DUoS Optimization**: Forecast high SSP during red band → shift load to green band if possible
3. **Solar Curtailment**: Forecast SSP < £30/MWh tomorrow → negotiate curtailment contract
4. **Refit Regularly**: Update model every 6 hours with latest data to avoid drift

---

### 6️⃣ **seasonal_decomposition_stats** — Trend vs Seasonality vs Noise

#### What It Is
Additive decomposition: SSP = Trend + Seasonal + Residual
- **Trend**: Long-term direction (e.g., coal phase-out → rising baseload price)
- **Seasonal**: Weekly pattern (weekday/weekend, time-of-day)
- **Residual**: Random noise + shocks (e.g., interconnector trip)

Produces 4-panel plot + variance statistics.

#### Why It Matters
**For Anomaly Detection:** Large residual = unusual event (investigate cause).

**For Forecasting Horizon:** High seasonal variance = weekly pattern dominates (short horizon OK). High trend variance = structural shifts (need longer window).

**For Contract Design:** If strong seasonality, negotiate time-of-day tariffs rather than flat rates.

#### How to Read

```python
{
  "period": 336,                # 48 SPs/day × 7 days (weekly)
  "obs_count": 52560,           # ~1 year of data
  "trend_var": 45.2,            # Long-term variance
  "seasonal_var": 123.8,        # Weekly pattern variance (larger = stronger)
  "resid_var": 89.5,            # Noise variance
  "plot_path": "output/seasonal_decomposition_ssp.png"
}
```

**Interpretation:**
- **seasonal_var > resid_var**: Strong weekly pattern, use in forecasting
- **Large resid_var**: Noisy regime (many shocks), wider CI needed
- **Rising trend**: Structural shift happening (e.g., gas price surge 2022)

**Plot Panels:**
1. **Observed**: Raw SSP time series
2. **Trend**: Smooth long-term movement (remove seasonality)
3. **Seasonal**: Repeating weekly pattern (detrended)
4. **Residual**: What's left (shocks + noise)

#### Pitfalls & Considerations
⚠️ **Assumes stable seasonality**: Holiday periods distort weekly patterns  
⚠️ **Additive assumption**: May need multiplicative if variance grows with level  
⚠️ **Solution**: Exclude major holidays, or use STL decomposition (more robust)

#### Operational Use Cases
1. **Anomaly Detection**: Residual > 3σ = investigate (interconnector fault? NESO action?)
2. **Forecasting Calibration**: High seasonal_var → focus on weekly patterns
3. **Contract Negotiations**: Show seasonal plot to justify time-of-day pricing
4. **Regime Detection**: If trend variance spikes, market structure changing (update models)

---

### 7️⃣ **outage_impact_results** — Event-Day Stress Test

#### What It Is
Welch's t-test comparing spread during **system warning periods** vs normal operation.

Uses `elexon_system_warnings` table to flag events:
- Tight margins
- Frequency deviations
- Loss of generation/interconnector

#### Why It Matters
**For Risk Management:** Quantify how much spreads widen during stress events:
- Size **reserve capacity** for batteries (what if your discharge window coincides with event?)
- Negotiate **premium pricing** for availability contracts

**For BSUoS Forecasting:** System events drive NESO balancing actions → higher BSUoS.

**For Solar PV:** Events often coincide with low wind (system stress) → solar can be premium asset.

#### How to Read

```python
{
  "metric": "spread_during_system_events",
  "mean_with_event": 15.8,       # Spread during events
  "mean_without_event": 6.2,     # Spread normally
  "mean_diff": 9.6,              # +£9.60/MWh during events
  "t_stat": 8.42,
  "p_value": 0.0001,             # Highly significant
  "n_with": 342,                 # Event periods
  "n_without": 48178             # Normal periods
}
```

**Interpretation:**
- **mean_diff = +9.6**: Spreads widen by £9.60/MWh during system events
- **Significant p-value**: Not random, systematic pattern
- **n_with = 342**: ~7 events (342 SPs ÷ 48 SPs/day)

#### Pitfalls & Considerations
⚠️ **Event windows overlap**: Multiple events can cascade (interconnector + low wind)  
⚠️ **Time-of-day bias**: Events often occur at peak times (confounding)  
⚠️ **Solution**: Robustness checks by event type or hour-of-day

#### Operational Use Cases
1. **Battery Reserve Pricing**: "During events, spread is 2.5× normal → charge premium for availability"
2. **Risk Buffers**: If cycling battery during event, add £9.60/MWh to assumed spread
3. **Solar Availability**: System events = premium for dispatchable generation (storage + solar)
4. **BSUoS Hedge**: Events drive BSUoS spikes, hedge with imbalance exposure

---

### 8️⃣ **neso_behavior_results** — BSUoS Linkage

#### What It Is
OLS regression: Spread ~ Balancing Cost + Cost per MWh

Connects **NESO balancing actions** (from `neso_balancing_services`) to **price formation** (spread).

#### Why It Matters
**For Cost Forecasting:** Unified view of DUoS/BSUoS/TNUoS:
- High balancing costs → wider spreads → higher imbalance exposure
- Inform **forward cost scenarios** for solar PV / battery business cases

**For Market Understanding:** See how NESO interventions affect your revenue (spread is your income).

**For Hedging:** If balancing cost and spread highly correlated, hedge balancing exposure with imbalance position.

#### How to Read

```python
{
  "model": "Spread_on_BalancingCosts",
  "n_obs": 45200,
  "r_squared": 0.28,
  "adj_r_squared": 0.279,
  "beta_balancing_cost": 0.0045,      # £1M balancing → +£4.50/MWh spread
  "p_balancing_cost": 0.0001,
  "beta_cost_per_mwh": 0.23,          # £1/MWh balancing rate → +£0.23 spread
  "p_cost_per_mwh": 0.0023
}
```

**Interpretation:**
- **beta_balancing_cost = 0.0045**: £1M total balancing cost → spread widens £4.50/MWh
- **beta_cost_per_mwh = 0.23**: £1/MWh balancing rate → £0.23/MWh wider spread
- **r_squared = 0.28**: Balancing explains 28% of spread variance

#### Pitfalls & Considerations
⚠️ **Joint determination**: Balancing cost and spread are both outcomes of system stress (not pure causation)  
⚠️ **Treat as associations**: Don't assume NESO "sets" spreads, but actions correlated  
⚠️ **Solution**: Use as descriptive tool, not for counterfactual policy analysis

#### Operational Use Cases
1. **BSUoS Forecasting**: NESO forecast shows £50M balancing today → expect £225/MWh wider spread
2. **Unified Cost View**: Combine DUoS (time-of-use) + BSUoS (volume-based) + spread impact
3. **Solar Business Case**: Show investors: "High balancing costs increase our imbalance revenue"
4. **Battery Scheduling**: If high balancing forecast, expect wider arbitrage window

---

### 9️⃣ **anova_results** — Seasonal Pricing Regimes

#### What It Is
One-way ANOVA (Analysis of Variance) testing if mean SSP (and SBP) differs across seasons:
- Winter (Dec, Jan, Feb)
- Spring (Mar, Apr, May)
- Summer (Jun, Jul, Aug)
- Autumn (Sep, Oct, Nov)

#### Why It Matters
**For Tariff Planning:** Quick check that Winter ≠ Summer pricing → justify seasonal tariffs.

**For Budgeting:** Solar PV projects need seasonal revenue profiles (summer higher generation, but lower prices?).

**For Scenario UX:** Dashboards should let users filter by season for meaningful comparisons.

#### How to Read

```python
{
  "price_col": "SSP",
  "f_stat": 342.5,                # F-statistic (higher = more different)
  "p_value": 0.0000,              # Highly significant
  "n_groups": 4,                  # 4 seasons
  "group_names": ["Winter", "Spring", "Summer", "Autumn"],
  "group_sizes": [12096, 12144, 12192, 12096],  # ~3 months each
  "group_means": [58.3, 45.2, 38.7, 49.1]       # £/MWh
}
```

**Interpretation:**
- **Significant p-value**: Seasons have different mean SSP
- **Winter highest (£58.30)**: Heating demand drives prices
- **Summer lowest (£38.70)**: Lower baseload, high solar/wind
- **F-stat = 342.5**: Very strong seasonal effect

**Follow-up:** ANOVA doesn't tell you *which* seasons differ. For pairwise comparisons (e.g., Winter vs Summer only), use Tukey's HSD test.

#### Pitfalls & Considerations
⚠️ **Doesn't show which pairs differ**: Need post-hoc tests  
⚠️ **Assumes normal distributions**: Robust to violations if large samples  
⚠️ **Solution**: If needed, run pairwise t-tests with Bonferroni correction

#### Operational Use Cases
1. **Tariff Design**: Justify 3-tier pricing (Winter/Shoulder/Summer)
2. **Solar Business Case**: Show investors seasonal revenue variation (model explicitly)
3. **Battery Strategy**: Winter = higher revenues (more arbitrage), size capacity accordingly
4. **Dashboard Filters**: Let users select season for scenario analysis

---

## 🔧 Implementation Best Practices

### Data Quality
✅ **Continuous 30-min series**: Ensure no gaps; interpolate short gaps cautiously (<2 hours)  
✅ **BigQuery optimization**: Partition by `DATE(ts)`, cluster by `settlement_period`  
✅ **Outlier handling**: Cap SSP/SBP at 99th percentile for regressions (avoid extreme events dominating)

### Scheduling
✅ **Nightly runs**: Schedule at 02:00 UTC (after settlement data finalized)  
✅ **6-hourly ARIMA**: Update forecasts 4× daily for operational use  
✅ **Weekly trend review**: Detect regime shifts early

### Output Storage
✅ **Persist to BigQuery**: Write all outputs to `uk_energy_analysis.*` for dashboard queries  
✅ **Version control**: Tag outputs with `run_timestamp` for auditability  
✅ **Plot archival**: If using GCS, organize by `output/YYYY/MM/plot_name.png`

### Integration
✅ **Dashboard consumption**: Query `*_results` tables via Data Studio / Looker  
✅ **API exposure**: Serve forecasts via Cloud Functions for real-time scheduling systems  
✅ **Alert thresholds**: Trigger alerts if spread > 95th percentile or residual > 3σ

---

## 📚 Related Documentation

- **`UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`** - Data pipeline design
- **`SCHEMA_FIX_SUMMARY.md`** - BigQuery table schemas
- **`ENHANCED_BI_ANALYSIS_README.md`** - Dashboard implementation
- **Elexon Settlement Guide**: https://www.elexon.co.uk/documents/training-guidance/

---

## 🎯 Quick Reference Card

| Output | Key Metric | Operational Use | Update Frequency |
|--------|-----------|-----------------|------------------|
| **ttest_results** | mean_diff | Battery arbitrage revenue | Weekly |
| **regression_temperature_ssp** | slope_temperature | Weather-driven scheduling | Weekly |
| **regression_volume_price** | beta_log_volume, beta_wind | Scenario forecasting | Weekly |
| **correlation_matrix** | |corr| | Feature selection, risk hedging | Monthly |
| **arima_forecast_ssp** | forecast_ssp, CI | Day-ahead scheduling | 6-hourly |
| **seasonal_decomposition** | resid_var | Anomaly detection | Daily |
| **outage_impact** | mean_diff | Reserve pricing, risk buffers | Monthly |
| **neso_behavior** | beta_balancing_cost | BSUoS forecasting | Weekly |
| **anova_results** | group_means | Seasonal tariff design | Quarterly |

---

**Last Updated:** October 31, 2025  
**Maintained by:** GB Power Market Analytics Team  
**Repository:** https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop  
**Contact:** For questions on statistical interpretation, see `advanced_statistical_analysis.py` docstrings
