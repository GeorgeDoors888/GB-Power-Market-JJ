# 📊 Analysis Sheet Design: Unified Historical + Real-Time Data

**Date:** October 30, 2025  
**Sheet Name:** Analysis  
**Dashboard ID:** 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8  
**Purpose:** Unified analysis interface combining historical (Elexon API) and real-time (IRIS) data

---

## 🎯 Design Overview

### User Experience Goals
1. **Simple Date Selection** - Drop-downs for quick date range selection
2. **Preset Time Ranges** - Common periods (24hrs, 1 week, 1 month, etc.)
3. **Data Grouping** - Logical organization by data type
4. **Visual Clarity** - Easy-on-the-eye layout with clear sections
5. **Unified Data** - Seamlessly combines historical and real-time sources

---

## 🎨 Sheet Layout Design

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          ANALYSIS DASHBOARD                                 │
│                     Historical + Real-Time Data Analysis                    │
└────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  📅 DATE RANGE SELECTION                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Quick Select:  [⏱️ 24 Hours ▼]    OR    Custom Range:                     │
│                                                                              │
│                                           From: [📅 DD/MM/YYYY ▼]           │
│  Options:                                 To:   [📅 DD/MM/YYYY ▼]           │
│    • 24 Hours                                                               │
│    • 1 Week                               [🔄 Refresh Data]                 │
│    • 1 Month                                                                │
│    • 6 Months                                                               │
│    • 12 Months                                                              │
│    • 24 Months                                                              │
│    • 3 Years                                                                │
│    • 4 Years                                                                │
│    • All Time                                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 DATA GROUP SELECTION                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [✓] System Frequency      [✓] Market Prices       [✓] Generation          │
│  [✓] Balancing Services    [ ] Demand Data         [ ] Weather Correlation │
│  [✓] Bid-Offer Data        [ ] Forecast vs Actual  [ ] Grid Stability      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  📈 SYSTEM FREQUENCY ANALYSIS                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Data Source: Historical (bmrs_freq) + Real-Time (bmrs_freq_iris)          │
│  Records: 45,234 | Time Range: 01/10/2025 - 30/10/2025                     │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │               Frequency Trend (50.0 Hz target)                │           │
│  │  50.2 ┼─────────╮                              ╭──────        │           │
│  │  50.1 ┤         ╰──╮  ╭──────╮  ╭──────────╮  │              │           │
│  │  50.0 ┤            ╰──╯      ╰──╯          ╰──╯              │           │
│  │  49.9 ┤                                                       │           │
│  │  49.8 ┤                                                       │           │
│  │       └──────────────────────────────────────────────────────┤           │
│  │         01/10   05/10   10/10   15/10   20/10   25/10  30/10│           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  Key Metrics:                                                               │
│  • Average Frequency: 50.01 Hz                                              │
│  • Min Frequency: 49.76 Hz (⚠️ Low Event on 15/10/2025 14:23)             │
│  • Max Frequency: 50.18 Hz                                                  │
│  • Standard Deviation: 0.087 Hz                                             │
│  • Time Below 49.8 Hz: 0.3% (Critical Alert Threshold)                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  💰 MARKET PRICES ANALYSIS                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Data Source: Historical (bmrs_mid) + Real-Time (bmrs_mid_iris)            │
│  Records: 2,304 | Settlement Periods Analyzed                              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │            System Sell Price vs System Buy Price              │           │
│  │  £150 ┼      ╭╮                                    ╭╮         │           │
│  │  £100 ┼──────╯╰────────────────────────────────────╯╰────     │           │
│  │   £50 ┼────────────────────────────────────────────────────   │           │
│  │    £0 ┼────────────────────────────────────────────────────   │           │
│  │  -£50 ┤                                                       │           │
│  │       └──────────────────────────────────────────────────────┤           │
│  │         01/10   05/10   10/10   15/10   20/10   25/10  30/10│           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  Key Metrics:                                                               │
│  • Avg System Sell Price: £78.34/MWh                                        │
│  • Avg System Buy Price: £72.18/MWh                                         │
│  • Max Price Spike: £245.00/MWh (15/10/2025 SP29)                          │
│  • Price Volatility: 12.3% (std dev / mean)                                │
│  • Settlement Periods with Negative Prices: 0                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚡ GENERATION MIX ANALYSIS                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Data Source: Historical (bmrs_fuelinst) + Real-Time (bmrs_fuelinst_iris)  │
│  Records: 145,234 | Generation Units Tracked                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │                  Generation by Fuel Type                      │           │
│  │  40GW ┼  ■■■ Wind                                             │           │
│  │  35GW ┼  ■■■■■ Solar                                          │           │
│  │  30GW ┼  ████ Gas (CCGT)                                      │           │
│  │  25GW ┼  ████████ Nuclear                                     │           │
│  │  20GW ┼  ██ Hydro                                             │           │
│  │  15GW ┼  ██ Biomass                                           │           │
│  │  10GW ┼  █ Coal                                               │           │
│  │   5GW ┼  ████ Interconnectors                                 │           │
│  │       └──────────────────────────────────────────────────────┤           │
│  │         Wind Solar Gas  Nuc  Hydro Bio  Coal Inter  Other    │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  Key Metrics:                                                               │
│  • Total Generation: 34,567 GWh                                             │
│  • Renewable Percentage: 42.3% (Wind + Solar + Hydro)                      │
│  • Carbon Intensity: 145 gCO2/kWh                                           │
│  • Gas Contribution: 38.2%                                                  │
│  • Nuclear Baseload: 18.9%                                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚖️ BALANCING SERVICES ANALYSIS                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Data Source: BOD (bmrs_bod + bmrs_bod_iris) + BOALF (bmrs_boalf + _iris)  │
│  Records: 89,234 | Balancing Actions Analyzed                              │
│                                                                              │
│  Summary Statistics:                                                        │
│  • Total Balancing Actions: 1,234                                           │
│  • Avg Cost per Action: £45,678                                             │
│  • Total Balancing Cost: £56.4M                                             │
│  • Most Active Unit: 2__DIDCR003 (145 actions)                             │
│  • Largest Single Action: 450 MW (15/10/2025 14:23)                        │
│                                                                              │
│  Bid-Offer Acceptance Rates:                                               │
│  • Offers Accepted: 67% (system short)                                     │
│  • Bids Accepted: 33% (system long)                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  📊 RAW DATA TABLE                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [Export to CSV] [Export to Excel] [Copy to Clipboard]                     │
│                                                                              │
│  Showing 1-50 of 145,234 records | Page [1] of 2,905                       │
│                                                                              │
│  ┌─────────────────┬──────────┬──────────┬──────────┬──────────┬─────────┐ │
│  │ Timestamp       │ Freq (Hz)│ SSP (£)  │ SBP (£)  │ Gen (MW) │ Source  │ │
│  ├─────────────────┼──────────┼──────────┼──────────┼──────────┼─────────┤ │
│  │ 30/10/25 23:45  │ 50.02    │ 78.45    │ 72.30    │ 34,567   │ IRIS    │ │
│  │ 30/10/25 23:44  │ 50.01    │ 78.42    │ 72.28    │ 34,545   │ IRIS    │ │
│  │ 30/10/25 23:43  │ 50.03    │ 78.50    │ 72.35    │ 34,589   │ IRIS    │ │
│  │ 30/10/25 23:42  │ 50.02    │ 78.48    │ 72.33    │ 34,578   │ IRIS    │ │
│  │ ...             │ ...      │ ...      │ ...      │ ...      │ ...     │ │
│  │ 01/10/25 00:01  │ 50.00    │ 65.23    │ 62.15    │ 32,123   │ Hist    │ │
│  │ 01/10/25 00:00  │ 50.01    │ 65.20    │ 62.12    │ 32,098   │ Hist    │ │
│  └─────────────────┴──────────┴──────────┴──────────┴──────────┴─────────┘ │
│                                                                              │
│  [◀ Previous] [Next ▶]                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ℹ️ DATA SOURCES & QUALITY                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Historical Data (Elexon API):                                              │
│  • Tables: bmrs_freq, bmrs_mid, bmrs_fuelinst, bmrs_bod, bmrs_boalf        │
│  • Coverage: 2020-01-01 to 2025-10-30 14:00                                │
│  • Records: 5.66M (FUELINST), 174 tables total                             │
│  • Update Frequency: Every 15 minutes                                       │
│  • Data Quality: ✅ 99.7% complete                                          │
│                                                                              │
│  Real-Time Data (IRIS Streaming):                                           │
│  • Tables: bmrs_freq_iris, bmrs_mid_iris, bmrs_fuelinst_iris, etc.         │
│  • Coverage: Last 48 hours (rolling window)                                 │
│  • Records: 100K+ (first 4 hours of operation)                             │
│  • Update Frequency: Continuous (30-60 second latency)                      │
│  • Data Quality: ✅ 98.3% complete (new system, monitoring)                │
│                                                                              │
│  Data Fusion Strategy:                                                      │
│  • Queries automatically UNION historical + real-time tables                │
│  • Deduplication: Real-time data takes precedence for overlapping periods   │
│  • Transition Point: Real-time data used for last 24 hours by default      │
│                                                                              │
│  Last Updated: 30/10/2025 23:45:32 | Auto-refresh: Every 5 minutes         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Technical Implementation

### BigQuery Unified Views

#### 1. System Frequency Unified View
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_unified` AS
WITH historical AS (
  SELECT 
    measurementTime as timestamp,
    frequency,
    'historical' as source,
    recordType
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
  WHERE measurementTime < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
),
realtime AS (
  SELECT 
    measurementTime as timestamp,
    frequency,
    'real-time' as source,
    recordType
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
  WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
)
SELECT * FROM historical
UNION ALL
SELECT * FROM realtime
ORDER BY timestamp DESC;
```

#### 2. Market Index Data Unified View
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_unified` AS
WITH historical AS (
  SELECT 
    settlementDate as timestamp,
    settlementPeriod,
    systemSellPrice,
    systemBuyPrice,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate < DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
),
realtime AS (
  SELECT 
    settlementDate as timestamp,
    settlementPeriod,
    price as systemSellPrice,
    volume as systemBuyPrice,  -- Note: May need adjustment based on IRIS schema
    'real-time' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
)
SELECT * FROM historical
UNION ALL
SELECT * FROM realtime
ORDER BY timestamp DESC, settlementPeriod DESC;
```

#### 3. Fuel Generation Unified View
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_unified` AS
WITH historical AS (
  SELECT 
    publishTime as timestamp,
    settlementDate,
    settlementPeriod,
    fuelType,
    generation,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE publishTime < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
),
realtime AS (
  SELECT 
    publishTime as timestamp,
    settlementDate,
    settlementPeriod,
    fuelType,
    generation,
    'real-time' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
)
SELECT * FROM historical
UNION ALL
SELECT * FROM realtime
ORDER BY timestamp DESC;
```

#### 4. Bid-Offer Data Unified View
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_unified` AS
WITH historical AS (
  SELECT 
    timeFrom as timestamp,
    bmUnit,
    bidOfferLevel,
    bidOfferPair,
    offerPrice,
    bidPrice,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE timeFrom < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
),
realtime AS (
  SELECT 
    timeFrom as timestamp,
    bmUnit,
    bidOfferLevel,
    bidOfferPair,
    offerPrice,
    bidPrice,
    'real-time' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
  WHERE timeFrom >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
)
SELECT * FROM historical
UNION ALL
SELECT * FROM realtime
ORDER BY timestamp DESC;
```

#### 5. BOA Lift Forecast Unified View
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_unified` AS
WITH historical AS (
  SELECT 
    publishTime as timestamp,
    bmUnit,
    acceptanceTime,
    deemedBidOfferFlag,
    soFlag,
    volume,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE publishTime < DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
),
realtime AS (
  SELECT 
    publishTime as timestamp,
    bmUnit,
    acceptanceTime,
    deemedBidOfferFlag,
    soFlag,
    volume,
    'real-time' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
  WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 48 HOUR)
)
SELECT * FROM historical
UNION ALL
SELECT * FROM realtime
ORDER BY timestamp DESC;
```

---

## 📋 Google Sheets Structure

### Cell Layout (Analysis Sheet)

```
Row 1:  [Merged A1:K1] ANALYSIS DASHBOARD - Historical + Real-Time Data
Row 2:  [Empty - spacing]
Row 3:  [Merged A3:K3] 📅 DATE RANGE SELECTION
Row 4:  [Empty - border]
Row 5:  A5: "Quick Select:" | C5: [Dropdown] | F5: "Custom Range:"
Row 6:  A6: "" | C6: "" | F6: "From:" | H6: [Date Picker]
Row 7:  A7: "" | C7: "" | F7: "To:" | H7: [Date Picker]
Row 8:  A8: "" | C8: "" | F8: [Refresh Button]
Row 9:  [Empty - spacing]
Row 10: [Merged A10:K10] 📊 DATA GROUP SELECTION
Row 11: [Empty - border]
Row 12: A12: [Checkbox] "System Frequency" | D12: [Checkbox] "Market Prices" | G12: [Checkbox] "Generation"
Row 13: A13: [Checkbox] "Balancing Services" | D13: [Checkbox] "Demand Data" | G13: [Checkbox] "Weather"
Row 14: A14: [Checkbox] "Bid-Offer Data" | D14: [Checkbox] "Forecast vs Actual" | G14: [Checkbox] "Grid Stability"
Row 15: [Empty - spacing]
Row 16: [Merged A16:K16] 📈 SYSTEM FREQUENCY ANALYSIS
Row 17-35: [Charts and metrics]
Row 36: [Empty - spacing]
Row 37: [Merged A37:K37] 💰 MARKET PRICES ANALYSIS
Row 38-55: [Charts and metrics]
Row 56: [Empty - spacing]
Row 57: [Merged A57:K57] ⚡ GENERATION MIX ANALYSIS
Row 58-75: [Charts and metrics]
Row 76: [Empty - spacing]
Row 77: [Merged A77:K77] ⚖️ BALANCING SERVICES ANALYSIS
Row 78-95: [Charts and metrics]
Row 96: [Empty - spacing]
Row 97: [Merged A97:K97] 📊 RAW DATA TABLE
Row 98: [Export buttons]
Row 99: [Table headers]
Row 100+: [Data rows - dynamic]
```

### Named Ranges
- `DateRangeQuickSelect`: C5
- `DateRangeFrom`: H6
- `DateRangeTo`: H7
- `CheckboxFrequency`: A12
- `CheckboxMarketPrices`: D12
- `CheckboxGeneration`: G12
- `CheckboxBalancing`: A13
- `CheckboxDemand`: D13
- `CheckboxWeather`: G13
- `DataTableStart`: A99

---

## 🎨 Color Scheme & Styling

### Color Palette (Easy on the Eye)
```
Primary Colors:
- Header Background: #1a237e (Deep Blue)
- Header Text: #ffffff (White)
- Section Headers: #283593 (Indigo)
- Section Text: #ffffff (White)

Data Colors:
- Historical Data: #2196f3 (Blue)
- Real-Time Data: #4caf50 (Green)
- Warning/Low: #ff9800 (Orange)
- Critical/Alert: #f44336 (Red)
- Success/High: #8bc34a (Light Green)

Background Colors:
- Main Background: #fafafa (Light Gray)
- Data Sections: #ffffff (White)
- Alternate Rows: #f5f5f5 (Very Light Gray)
- Borders: #e0e0e0 (Gray)

Chart Colors:
- Line 1 (Frequency): #2196f3 (Blue)
- Line 2 (Target): #4caf50 (Green)
- Bar 1 (Sell Price): #ff9800 (Orange)
- Bar 2 (Buy Price): #ffeb3b (Yellow)
- Stacked (Generation): Varied palette
```

### Font Styling
```
Headers:
- Font: Roboto or Arial
- Size: 14pt
- Weight: Bold
- Color: White on colored background

Section Titles:
- Font: Roboto or Arial
- Size: 12pt
- Weight: Bold
- Color: #1a237e (Deep Blue)

Data:
- Font: Roboto Mono or Courier
- Size: 10pt
- Weight: Normal
- Color: #212121 (Dark Gray)

Metrics:
- Font: Roboto or Arial
- Size: 11pt
- Weight: Semi-bold
- Color: #424242 (Medium Gray)
```

---

## 🔧 Data Refresh Logic

### Python Script: `update_analysis_sheet.py`

```python
#!/usr/bin/env python3
"""
Update the Analysis sheet with unified historical + real-time data
"""

import pickle
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Analysis'
PROJECT_ID = 'inner-cinema-476211-u9'

def get_date_range_from_sheet(sheet):
    """Get date range from user selection"""
    quick_select = sheet.acell('C5').value
    
    if quick_select and quick_select != "Custom":
        # Calculate based on quick select
        end_date = datetime.now()
        
        ranges = {
            "24 Hours": timedelta(hours=24),
            "1 Week": timedelta(days=7),
            "1 Month": timedelta(days=30),
            "6 Months": timedelta(days=180),
            "12 Months": timedelta(days=365),
            "24 Months": timedelta(days=730),
            "3 Years": timedelta(days=1095),
            "4 Years": timedelta(days=1460),
            "All Time": timedelta(days=365*10)  # 10 years max
        }
        
        start_date = end_date - ranges.get(quick_select, timedelta(days=30))
    else:
        # Use custom range
        from_date = sheet.acell('H6').value
        to_date = sheet.acell('H7').value
        start_date = datetime.strptime(from_date, '%d/%m/%Y')
        end_date = datetime.strptime(to_date, '%d/%m/%Y')
    
    return start_date, end_date

def query_unified_frequency(bq_client, start_date, end_date):
    """Query unified frequency data"""
    query = f"""
    SELECT 
        timestamp,
        frequency,
        source
    FROM `{PROJECT_ID}.uk_energy_prod.bmrs_freq_unified`
    WHERE timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
    ORDER BY timestamp DESC
    LIMIT 10000
    """
    return list(bq_client.query(query).result())

def query_unified_market_prices(bq_client, start_date, end_date):
    """Query unified market index data"""
    query = f"""
    SELECT 
        timestamp,
        settlementPeriod,
        systemSellPrice,
        systemBuyPrice,
        source
    FROM `{PROJECT_ID}.uk_energy_prod.bmrs_mid_unified`
    WHERE timestamp BETWEEN '{start_date.date().isoformat()}' 
          AND '{end_date.date().isoformat()}'
    ORDER BY timestamp DESC, settlementPeriod DESC
    LIMIT 5000
    """
    return list(bq_client.query(query).result())

def query_unified_generation(bq_client, start_date, end_date):
    """Query unified generation data"""
    query = f"""
    SELECT 
        timestamp,
        fuelType,
        SUM(generation) as total_generation,
        source
    FROM `{PROJECT_ID}.uk_energy_prod.bmrs_fuelinst_unified`
    WHERE timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
    GROUP BY timestamp, fuelType, source
    ORDER BY timestamp DESC
    LIMIT 10000
    """
    return list(bq_client.query(query).result())

def calculate_frequency_metrics(data):
    """Calculate frequency statistics"""
    frequencies = [row.frequency for row in data]
    
    return {
        'avg': sum(frequencies) / len(frequencies),
        'min': min(frequencies),
        'max': max(frequencies),
        'std_dev': calculate_std_dev(frequencies),
        'below_threshold': sum(1 for f in frequencies if f < 49.8) / len(frequencies) * 100
    }

def calculate_std_dev(values):
    """Calculate standard deviation"""
    import statistics
    return statistics.stdev(values) if len(values) > 1 else 0

def update_sheet(sheet, freq_data, price_data, gen_data, start_date, end_date):
    """Update the Analysis sheet with data"""
    
    # Update date range display
    sheet.update_acell('H6', start_date.strftime('%d/%m/%Y'))
    sheet.update_acell('H7', end_date.strftime('%d/%m/%Y'))
    
    # Calculate metrics
    freq_metrics = calculate_frequency_metrics(freq_data)
    
    # Update frequency metrics (example cells - adjust as needed)
    sheet.update_acell('B20', f"{freq_metrics['avg']:.2f} Hz")
    sheet.update_acell('B21', f"{freq_metrics['min']:.2f} Hz")
    sheet.update_acell('B22', f"{freq_metrics['max']:.2f} Hz")
    sheet.update_acell('B23', f"{freq_metrics['std_dev']:.3f} Hz")
    sheet.update_acell('B24', f"{freq_metrics['below_threshold']:.1f}%")
    
    # Update raw data table (starting at row 100)
    table_data = []
    table_data.append(['Timestamp', 'Freq (Hz)', 'SSP (£)', 'SBP (£)', 'Gen (MW)', 'Source'])
    
    # Combine and sort data (simplified example)
    for i, row in enumerate(freq_data[:50]):  # Limit to 50 rows
        table_data.append([
            row.timestamp.strftime('%d/%m/%y %H:%M'),
            f"{row.frequency:.2f}" if row.frequency else '',
            '',  # Price data would be matched here
            '',
            '',  # Generation data would be matched here
            row.source
        ])
    
    # Update table
    sheet.update(f'A99:F{99 + len(table_data)}', table_data)
    
    # Update last refresh time
    sheet.update_acell('B200', f"Last Updated: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

def main():
    """Main execution"""
    print("📊 Updating Analysis Sheet...")
    
    # Initialize BigQuery
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Initialize Google Sheets (using existing auth)
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create Analysis sheet
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Creating new sheet: {SHEET_NAME}")
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=200, cols=15)
    
    # Get date range
    start_date, end_date = get_date_range_from_sheet(sheet)
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    
    # Query unified views
    print("Querying frequency data...")
    freq_data = query_unified_frequency(bq_client, start_date, end_date)
    
    print("Querying market price data...")
    price_data = query_unified_market_prices(bq_client, start_date, end_date)
    
    print("Querying generation data...")
    gen_data = query_unified_generation(bq_client, start_date, end_date)
    
    # Update sheet
    print("Updating sheet...")
    update_sheet(sheet, freq_data, price_data, gen_data, start_date, end_date)
    
    print("✅ Analysis sheet updated successfully!")

if __name__ == '__main__':
    main()
```

---

## 📊 Dropdown Configuration

### Quick Select Dropdown (Cell C5)
```
Data Validation > List from range:
- 24 Hours
- 1 Week
- 1 Month
- 6 Months
- 12 Months
- 24 Months
- 3 Years
- 4 Years
- All Time
- Custom
```

### Data Group Checkboxes
```
Insert > Checkbox in cells:
- A12: System Frequency
- D12: Market Prices
- G12: Generation
- A13: Balancing Services
- D13: Demand Data
- G13: Weather Correlation
- A14: Bid-Offer Data
- D14: Forecast vs Actual
- G14: Grid Stability
```

---

## 🚀 Implementation Steps

### Phase 1: Create Unified Views (BigQuery)
1. Run SQL scripts to create unified views
2. Test each view with sample queries
3. Verify data quality and completeness

### Phase 2: Create Analysis Sheet (Google Sheets)
1. Add new sheet named "Analysis"
2. Set up header and section structure
3. Add dropdowns and checkboxes
4. Configure named ranges
5. Apply color scheme and styling

### Phase 3: Create Update Script (Python)
1. Develop `update_analysis_sheet.py`
2. Test with different date ranges
3. Verify data accuracy
4. Add error handling

### Phase 4: Deploy Automation
1. Test manual updates
2. Set up cron job for automatic updates
3. Monitor performance
4. Document usage

---

## 🎯 Success Criteria

- [ ] All 5 unified views created in BigQuery
- [ ] Analysis sheet created with full layout
- [ ] Dropdowns functional (date ranges)
- [ ] Checkboxes functional (data groups)
- [ ] Python script updates all sections
- [ ] Charts render correctly
- [ ] Data accuracy validated
- [ ] Refresh < 30 seconds
- [ ] User-friendly interface
- [ ] Documentation complete

---

## 📚 Related Documentation

- **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)** - Architecture overview
- **[IRIS_AUTOMATED_DASHBOARD_STATUS.md](IRIS_AUTOMATED_DASHBOARD_STATUS.md)** - IRIS system status
- **[AUTHENTICATION_AND_CREDENTIALS_GUIDE.md](AUTHENTICATION_AND_CREDENTIALS_GUIDE.md)** - Auth setup

---

**Last Updated:** October 30, 2025  
**Status:** 📝 Design Complete - Ready for Implementation  
**Next Step:** Create BigQuery unified views
