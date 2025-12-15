# VLP Dashboard System - Complete Guide

## Overview
Automated VLP (Virtual Lead Party) revenue dashboard for battery BESS unit 2__FBPGM002 (Flexgen). Analyzes balancing mechanism (BM) revenue, capacity market (CM) payments, PPA export, and avoided import costs.

**Live Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

## Architecture

### Data Pipeline
1. **Data Sources**
   - **Historical**: Elexon BMRS API (2020-present)
     - `bmrs_boalf`: BM acceptance volumes (11.3M rows)
     - `bmrs_costs`: System prices SSP/SBP (64k rows)
     - `bmrs_bod`: BM bid/offer prices (391M rows)
   - **Real-time**: IRIS streaming via Azure Service Bus
     - `bmrs_*_iris` tables (last 24-48h)

2. **Processing Pipeline**
   ```
   BigQuery (bmrs_boalf + bmrs_costs)
       ↓
   vlp_dashboard_simple.py (Python)
       ↓ Calculates 4 revenue streams
   Google Sheets (BESS_VLP + Dashboard)
       ↓
   format_vlp_dashboard.py (Formatting)
       ↓
   create_vlp_charts.py (Charts)
   ```

3. **Automation**
   - **Apps Script Menu**: Custom menu in Google Sheets
   - **Webhook Server**: Flask server for manual refresh
   - **CLASP**: Deploy Apps Script code via CLI

## Prerequisites Configuration

### Battery Specs (vlp_prerequisites.json)
- **BMU ID**: `2__FBPGM002` (Flexgen battery)
- **Power**: 2.5 MW
- **Capacity**: 5.0 MWh
- **Efficiency**: 85%
- **Site Share**: 70% (VLP gets 30%)

### Revenue Parameters
- **BM Revenue**: SSP (System Sell Price) × accepted MWh
  - Currently uses SSP as proxy
  - Can enhance with actual bid/offer prices from `bmrs_bod`
- **CM Revenue**: £9.04/MWh (from £15.08/kW/year clearing price)
- **PPA Export**: £150/MWh
- **Avoided Import**: (Wholesale + DUoS + Levies) × MWh
  - Levies: £98.15/MWh blended (RO, FiT, CfD, CCL, BSUoS, TNUoS)
  - DUoS bands:
    - RED: £17.64/MWh (SP 33-39, weekdays 16:00-19:30)
    - AMBER: £2.05/MWh (SP 17-44, weekdays 08:00-22:00)
    - GREEN: £0.11/MWh (weekends + off-peak)

## Installation

### 1. Python Environment
```bash
cd /home/george/GB-Power-Market-JJ

# Install dependencies
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread oauth2client flask

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="/home/george/inner-cinema-credentials.json"
```

### 2. Verify Prerequisites
```bash
# Check vlp_prerequisites.json exists
cat vlp_prerequisites.json

# Test BigQuery connection
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ BigQuery OK")'

# Test Sheets connection
python3 -c 'import gspread; from oauth2client.service_account import ServiceAccountCredentials; print("✅ Sheets OK")'
```

### 3. Apps Script Setup (via CLASP)
```bash
# Install CLASP (if not already installed)
npm install -g @google/clasp

# Login to Google account
clasp login

# Current CLASP config exists (.clasp.json)
# To deploy VLP menu:
# 1. Copy vlp_menu.gs to appsscript_v3/ folder
# 2. Push to Apps Script:
clasp push

# 3. Deploy as add-on:
clasp deploy --description "VLP Dashboard Menu v1.0"
```

### 4. Webhook Server (Optional - for Apps Script button)
```bash
# Run webhook server
python3 vlp_webhook_server.py

# In separate terminal, expose via ngrok
ngrok http 5002

# Copy ngrok URL and update vlp_menu.gs:
# Change 'YOUR_NGROK_URL_HERE' to your ngrok URL
```

## Running the Dashboard

### Manual Refresh (Complete Pipeline)
```bash
cd /home/george/GB-Power-Market-JJ

# 1. Fetch data and calculate revenues
python3 vlp_dashboard_simple.py

# 2. Apply formatting
python3 format_vlp_dashboard.py

# 3. Create charts
python3 create_vlp_charts.py

# Or run all at once:
python3 vlp_dashboard_simple.py && python3 format_vlp_dashboard.py && python3 create_vlp_charts.py
```

### Via Apps Script Menu (Once Deployed)
1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Click **🔋 VLP Dashboard** → **🔄 Refresh Data**
3. Wait 30-60 seconds for pipeline to complete

## Output Structure

### Google Sheets Worksheets

#### 1. Dashboard (Summary)
```
A1: VLP Site – BESS Revenue Dashboard

A3: Revenue Breakdown
A4-B10:
| Revenue Line       | Value (£)    |
|-------------------|--------------|
| BM revenue        | £447,777     |
| ESO services      | £0           |
| CM revenue        | £49,327      |
| DSO flex          | £0           |
| PPA export        | £818,475     |
| Avoided import    | £995,977     |

D4-E7: KPIs
| Total Gross Margin | £2,311,556  |
| Site Margin (70%)  | £1,609,756  |
| VLP Margin (30%)   | £693,467    |

A20: Last Updated: 2025-11-22 14:30:00
```

**Charts**:
- G4: Revenue Stack (stacked column)
- G15: State of Charge (line chart)
- M4: Battery Actions (column chart)
- M15: Gross Margin (line chart)

#### 2. BESS_VLP (Time Series)
Columns:
- `settlementDate`: Date
- `settlementPeriod`: 1-48
- `bm_accepted_mwh`: BM acceptance volume (MWh)
- `ssp_price`: System Sell Price (£/MWh)
- `duos_band`: RED/AMBER/GREEN
- `duos_rate`: DUoS charge (£/MWh)
- `r_bm_gbp`: BM revenue (£)
- `r_cm_gbp`: CM revenue (£)
- `r_ppa_gbp`: PPA revenue (£)
- `r_avoided_import_gbp`: Avoided import cost (£)
- `gross_margin_sp`: Gross margin per SP (£)
- `soc_start`: State of charge at start (MWh)
- `soc_end`: State of charge at end (MWh)

**336 rows** for Oct 17-23 week (7 days × 48 SPs)

## Test Results (Oct 17-23, 2025)

### Revenue Summary
- **BM Revenue**: £447,777 (5,457 MWh × avg SSP ~£82/MWh)
- **CM Revenue**: £49,327 (5,457 MWh × £9.04/MWh)
- **PPA Revenue**: £818,475 (5,457 MWh × £150/MWh)
- **Avoided Import**: £995,977 (5,457 MWh × avg import cost ~£182/MWh)
- **Total Gross**: £2,311,556

### Revenue Split
- **Site (70%)**: £1,609,756
- **VLP (30%)**: £693,467

### Context
Oct 17-23 was a **high-price event week** (avg £79.83/MWh vs normal £30-40/MWh). This represents exceptional performance, not typical revenue. For monthly average, test on 30-day periods including normal weeks.

## File Descriptions

### Core Scripts
1. **vlp_dashboard_simple.py** (~265 lines)
   - Fetches data from BigQuery (bmrs_boalf + bmrs_costs)
   - Calculates 4 revenue streams
   - Writes to Google Sheets (BESS_VLP + Dashboard)
   - Functions: `fetch_vlp_data()`, `calculate_revenues()`, `write_to_sheets()`

2. **format_vlp_dashboard.py** (~150 lines)
   - Applies currency formatting (£#,##0)
   - Conditional formatting (negatives in red)
   - Header styling (bold, light blue #CFE2F3)
   - Borders and alignment
   - Functions: `format_dashboard()`, `format_bess_vlp()`

3. **create_vlp_charts.py** (~360 lines)
   - Creates 4 charts via gspread API
   - Functions: `create_revenue_stack_chart()`, `create_soc_chart()`, `create_battery_actions_chart()`, `create_margin_chart()`

4. **vlp_webhook_server.py** (~120 lines)
   - Flask webhook for Apps Script integration
   - Endpoints: `/refresh-vlp`, `/run-full-pipeline`, `/health`

5. **vlp_menu.gs** (~120 lines)
   - Apps Script custom menu
   - Functions: `onOpen()`, `refreshVlpDashboard()`, `runFullPipeline()`, `showAbout()`

### Configuration
- **vlp_prerequisites.json**: BMU IDs, battery specs, spreadsheet ID
- **.clasp.json**: CLASP configuration for Apps Script deployment

## Data Sources & Schema

### bmrs_boalf (BM Acceptance Volumes)
```sql
SELECT 
  settlementDate,           -- DATETIME
  settlementPeriodFrom,     -- INTEGER (NOT settlementPeriod)
  settlementPeriodTo,       -- INTEGER
  bmUnit,                   -- STRING (e.g., '2__FBPGM002')
  levelFrom,                -- INTEGER (MW)
  levelTo,                  -- INTEGER (MW)
  acceptanceNumber,         -- STRING
  acceptanceTime            -- DATETIME
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnit = '2__FBPGM002'
```

### bmrs_costs (System Prices)
```sql
SELECT 
  settlementDate,           -- DATETIME
  settlementPeriod,         -- INTEGER (1-48)
  systemBuyPrice,           -- FLOAT (£/MWh) - SBP
  systemSellPrice           -- FLOAT (£/MWh) - SSP
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
-- Note: SSP = SBP since Nov 2015 (P305 single price)
```

### bmrs_bod (BM Bid/Offer Prices)
```sql
SELECT 
  settlementDate,           -- DATETIME
  settlementPeriod,         -- INTEGER
  bmUnit,                   -- STRING (NOT bmUnitId!)
  pairId,                   -- STRING
  offer,                    -- FLOAT (£/MWh)
  bid                       -- FLOAT (£/MWh)
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnit = '2__FBPGM002'
-- 391,287,533 rows total
```

## Troubleshooting

### "Access Denied: jibber-jabber-knowledge"
**Cause**: Using wrong GCP project  
**Fix**: Always use `inner-cinema-476211-u9`, location `US`

### "FileNotFoundError: inner-cinema-credentials.json"
**Cause**: Credentials not in working directory  
**Fix**: Use absolute path `/home/george/inner-cinema-credentials.json`

### "Object of type Timestamp is not JSON serializable"
**Cause**: pandas Timestamp not JSON compatible  
**Fix**: Convert to string: `df['settlementDate'] = df['settlementDate'].astype(str)`

### "Invalid value: 'NONE' for legendPosition"
**Cause**: Invalid gspread chart spec  
**Fix**: Use `'legendPosition': 'NO_LEGEND'` instead of `'NONE'`

### No Recent Data (last 24h missing)
**Cause**: Historical tables lag ~24h  
**Fix**: UNION with `*_iris` tables for real-time data
```sql
SELECT * FROM bmrs_costs WHERE settlementDate < '2025-10-30'
UNION ALL
SELECT * FROM bmrs_costs_iris WHERE settlementDate >= '2025-10-30'
```

## Enhancement Ideas

### 1. Improve BM Revenue Calculation
Current: Uses SSP as proxy for BM acceptance prices  
Better: Join with `bmrs_bod` to get actual bid/offer prices

```sql
LEFT JOIN bmrs_bod USING (bmUnit, settlementDate, settlementPeriod)
-- Use bod.offer for discharge, bod.bid for charge
```

### 2. Add Real-Time IRIS Data
Currently: Only uses historical `bmrs_boalf` + `bmrs_costs`  
Enhancement: UNION with `bmrs_*_iris` tables for last 24-48h

### 3. Automate via Cron
```bash
# Add to crontab
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 vlp_dashboard_simple.py >> logs/vlp_dashboard.log 2>&1
```

### 4. Add Forecasting
- Use historical patterns to forecast next-day revenue
- Integration with day-ahead market prices
- Optimize charge/discharge strategy

### 5. Multi-BMU Support
Extend to analyze multiple batteries:
- `2__FBPGM002` (Flexgen) - current
- `2__FFSEN005` (likely Gresham House/Harmony Energy)

## Contact & Support

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (Nov 2025)

---

*Last Updated: November 22, 2025*  
*Version: 1.0*
