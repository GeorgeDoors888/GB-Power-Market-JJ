# Actual BigQuery Data Inventory

**Generated:** 2025-11-09  
**Total Tables Found:** 198

## ✅ VERIFIED: Key VLP Analysis Tables

### 1. bmrs_mid - Market Index Data (System Prices) ⭐⭐⭐⭐⭐
- **Rows:** 155,405
- **Date Range:** 2022-01-01 to 2025-10-30 (3+ years)
- **Key Columns:** settlementDate, settlementPeriod, price
- **VLP Use Case:** Primary arbitrage signals - system buy/sell prices
- **Status:** ✅ EXCELLENT - Full historical data available

### 2. bmrs_bod - Bid-Offer Data ⭐⭐⭐⭐⭐
- **Rows:** 391,287,533 (391 million!)
- **Date Range:** 2022-01-01 to 2025-10-28
- **Key Columns:** timeFrom, timeTo, bmUnitId, offerPrice, bidPrice, offerVolume, bidVolume
- **VLP Use Case:** Asset-level dispatch signals, unit-specific arbitrage opportunities
- **Status:** ✅ EXCELLENT - Massive dataset with detailed bid/offer data

### 3. bmrs_netbsad - Net Balancing Services Adjustment Data ⭐⭐⭐⭐
- **Rows:** 82,026
- **Date Range:** 2022-01-01 to 2025-10-28
- **Key Columns:** settlementDate, settlementPeriod, volume
- **VLP Use Case:** System imbalance volumes - indicates when system needs balancing
- **Status:** ✅ GOOD - Consistent historical data

### 4. bmrs_indgen_iris - Indicated Generation by Unit ⭐⭐⭐⭐
- **Rows:** 468,306
- **Date Range:** 2025-10-30 to 2025-11-10 (RECENT ONLY)
- **Key Columns:** settlementDate, settlementPeriod, bmUnitId, quantity, fuelType
- **VLP Use Case:** Unit-level dispatch signals, verify actual generation vs bids
- **Status:** ⚠️ LIMITED - Only 10 days of data, but very detailed

### 5. fuelinst - Fuel Mix (Instantaneous) ⭐⭐⭐
- **Rows:** 7,280
- **Date Range:** 2025-10-25 only (SINGLE DAY)
- **Key Columns:** settlementDate, ccgt, wind, solar, nuclear, coal, etc.
- **VLP Use Case:** System-level fuel mix for understanding dispatch patterns
- **Status:** ⚠️ VERY LIMITED - Only 1 day of data

## 📊 Complete Table List (198 Tables)

### Balancing & Market Data (High Priority for VLP)
- ✅ **balancing_acceptances** - Accepted balancing actions
- ✅ **balancing_dynamic_sel** - Stable Export Limits (dynamic)
- ✅ **balancing_nonbm_volumes** - Non-BM balancing volumes
- ✅ **balancing_physical_mels** - Maximum Export Limits (physical)
- ✅ **balancing_physical_mils** - Maximum Import Limits (physical)
- ✅ **bid_offer_data** - Alternative BOD table
- ✅ **bmrs_boalf** - Bid-Offer Acceptance Level Flagged
- ✅ **bmrs_disbsad** - Disaggregated Balancing Services Adjustment Data

### Generation & Demand Forecasts
- ✅ **demand_forecast_day_ahead** - Day-ahead demand forecasts
- ✅ **demand_forecast_national** - National demand forecasts
- ✅ **demand_forecast_transmission** - Transmission-level demand forecasts
- ✅ **demand_outturn** - Actual demand outturn
- ✅ **generation_forecast_day_ahead** - Day-ahead generation forecasts
- ✅ **generation_forecast_wind** - Wind generation forecasts
- ✅ **generation_forecast_wind_solar_peak** - Wind/solar peak forecasts
- ✅ **generation_outturn** - Actual generation outturn

### System Frequency & Warnings
- ✅ **bmrs_freq** - System frequency data
- ✅ **system_frequency** - Alternative frequency table
- ✅ **system_warnings** - System warning notifications
- ✅ **margin_daily** - Daily margin forecast

### Asset & Network Data
- ✅ **cva_plants** - CVA (Central Volume Allocation) plants
- ✅ **sva_generators** - SVA (Supplier Volume Allocation) generators
- ✅ **sva_generators_with_coords** - SVA generators with coordinates
- ✅ **offshore_wind_farms** - Offshore wind farm reference data
- ✅ **neso_gsp_groups** - Grid Supply Point groups
- ✅ **neso_gsp_boundaries** - GSP boundary data
- ✅ **neso_dno_boundaries** - Distribution Network Operator boundaries
- ✅ **dno_license_areas** - DNO license area data

### REMIT Outage Data
- ✅ **bmrs_remit_iris** - REMIT unavailability messages
- ✅ **bmrs_remit_unavailability** - REMIT unavailability data

### Reserve & Response Data
- ✅ **bmrs_rdre** - Run Down Rate Export
- ✅ **bmrs_rdri** - Run Down Rate Import
- ✅ **bmrs_rure** - Run Up Rate Export
- ✅ **bmrs_ruri** - Run Up Rate Import
- ✅ **bmrs_qas** - Quiescent Accepted Settlement
- ✅ **bmrs_qpn** - Quiescent Physical Notification
- ✅ **quiescent_physical** - Quiescent physical data

### Limits & Constraints
- ✅ **bmrs_sel** - Stable Export Limit
- ✅ **bmrs_sil** - Stable Import Limit
- ✅ **stable_export_limit** - Alternative SEL table
- ✅ **bmrs_pn** - Physical Notifications
- ✅ **bmrs_mdp** - Maximum Delivery Period
- ✅ **bmrs_mdv** - Maximum Delivery Volume

### Temperature & Weather
- ✅ **bmrs_temp** - Temperature data
- ✅ **bmrs_windfor** - Wind forecast data

### Interconnector Data
- ✅ **bmrs_indo** - Interconnector data
- ✅ **bmrs_itsdo** - Interconnector transfer schedule data

### Transmission Constraints
- ✅ **bmrs_mnzt** - Minimum Non-Zero Time
- ✅ **bmrs_mzt** - Minimum Zero Time
- ✅ **bmrs_ndz** - Notice to Deviate from Zero
- ✅ **bmrs_ntb** - Notice to Bid
- ✅ **bmrs_nto** - Notice to Offer

### Surplus & Margin Data
- ✅ **bmrs_surplus_margin** - Surplus margin forecast
- ✅ **surplus_daily** - Daily surplus forecast
- ✅ **output_usable_2_14d** - Usable output 2-14 days ahead

### Time-Stamped Data (2025 Snapshots)
Many tables have "_2025" or "_sep_oct_2025" variants:
- freq_2025, fuelinst_2025, imbalngc_2025, indgen_2025, inddem_2025
- bod_sep_oct_2025, disbsad_sep_oct_2025, freq_sep_oct_2025
- fuelhh_sep_oct_2025, fuelinst_sep_oct_2025, imbalngc_sep_oct_2025
- And ~60 more similar tables

### Sample Data Tables (For Testing)
- demand_outturn_sample_january_2025
- demand_outturn_sample_february_2025
- demand_outturn_sample_march_2025
- demand_outturn_sample_april_2025
- demand_outturn_sample_may_2025
- demand_outturn_sample_june_2025
- generation_actual_sample_january_2025 through june_2025

## 🎯 VLP Priority Recommendations

### Immediate Use (Excellent Data)
1. **bmrs_mid** (155K rows, 3+ years) - System prices for arbitrage signals
2. **bmrs_bod** (391M rows, 3+ years) - Unit-level bid/offer data for asset-specific strategies
3. **bmrs_netbsad** (82K rows, 3+ years) - System imbalance for timing decisions

### Worth Investigating (Need Row Count Verification)
4. **bmrs_boalf** - Bid-Offer Acceptance Level (BOA volumes)
5. **bmrs_disbsad** - Disaggregated balancing costs by action
6. **balancing_acceptances** - Accepted balancing actions
7. **bmrs_freq** - System frequency (indicates system stress)
8. **system_warnings** - Official system warning notifications

### Limited Use (Incomplete Data)
- **bmrs_indgen_iris** (10 days only) - Wait for more historical data
- **fuelinst** (1 day only) - Use bmrs_fuelinst_dedup or generation_fuel_instant instead

## ⚠️ Tables That DON'T Exist
- ❌ **bmrs_b1610** - This was listed in theoretical guides but doesn't exist
- (Other assumed tables not verified)

## 📝 Next Steps for VLP Analysis

1. **Query bmrs_mid for Price Spreads:**
   ```sql
   SELECT 
     settlementDate,
     settlementPeriod,
     MAX(price) - MIN(price) as price_spread,
     MAX(price) as max_price,
     MIN(price) as min_price
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
   WHERE settlementDate >= '2025-01-01'
   GROUP BY settlementDate, settlementPeriod
   ORDER BY price_spread DESC
   LIMIT 100;
   ```

2. **Check Unit-Level Arbitrage in bmrs_bod:**
   ```sql
   SELECT 
     bmUnitId,
     COUNT(*) as num_offers,
     AVG(offerPrice) as avg_offer_price,
     AVG(bidPrice) as avg_bid_price,
     AVG(offerPrice - bidPrice) as avg_spread
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
   WHERE timeFrom >= '2025-01-01'
   GROUP BY bmUnitId
   HAVING avg_spread > 10
   ORDER BY avg_spread DESC
   LIMIT 100;
   ```

3. **Verify Other High-Priority Tables:**
   - Get row counts for bmrs_boalf, bmrs_disbsad, balancing_acceptances
   - Check date ranges for system_warnings, bmrs_freq
   - Verify which "_2025" tables have substantial data

## 🔍 Data Quality Notes

- ✅ **bmrs_mid**: Excellent - 3+ years of complete system price data
- ✅ **bmrs_bod**: Excellent - 391M rows over 3+ years (massive dataset)
- ✅ **bmrs_netbsad**: Good - 3+ years of imbalance data
- ⚠️ **bmrs_indgen_iris**: Limited to 10 recent days
- ⚠️ **fuelinst**: Only 1 day of data
- ⚠️ Many "_iris" tables may have limited data (need verification)
- ⚠️ "_sep_oct_2025" tables are likely recent snapshots only

**This is ACTUAL data you have, not theoretical!**
