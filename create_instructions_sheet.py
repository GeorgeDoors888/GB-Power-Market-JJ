#!/usr/bin/env python3
"""
Create INSTRUCTIONS sheet - Complete user guide for all sheets and capabilities
Combines: Usage guides, data collection methods, architecture diagram, troubleshooting
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Initialize gspread
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Try to get existing sheet or create new one
try:
    worksheet = spreadsheet.worksheet('INSTRUCTIONS')
    print("📝 Found existing INSTRUCTIONS sheet, clearing...")
    worksheet.clear()
except gspread.WorksheetNotFound:
    print("📝 Creating new INSTRUCTIONS sheet...")
    worksheet = spreadsheet.add_worksheet(title='INSTRUCTIONS', rows=600, cols=10)

# ============================================================================
# BUILD INSTRUCTIONS CONTENT
# ============================================================================

data = [
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['GB POWER MARKET JJ - COMPREHENSIVE INSTRUCTIONS', '', '', '', '', '', '', '', ''],
    ['Complete guide to all sheets, data sources, and system capabilities', '', '', '', '', '', '', '', ''],
    ['Last Updated: December 23, 2025', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # TABLE OF CONTENTS
    # ========================================================================
    ['📋 TABLE OF CONTENTS', '', '', '', '', '', '', '', ''],
    [''],
    ['Section 1: Sheet Purpose Overview', '', '', '', '', '', '', '', ''],
    ['Section 2: Live Dashboard v2 Usage Guide', '', '', '', '', '', '', '', ''],
    ['Section 3: VLP Revenue Analysis', '', '', '', '', '', '', '', ''],
    ['Section 4: BESS Calculator', '', '', '', '', '', '', '', ''],
    ['Section 5: DATA & DATA DICTIONARY Navigation', '', '', '', '', '', '', '', ''],
    ['Section 6: Python Query Examples', '', '', '', '', '', '', '', ''],
    ['Section 7: ChatGPT Integration', '', '', '', '', '', '', '', ''],
    ['Section 8: Data Collection Architecture', '', '', '', '', '', '', '', ''],
    ['Section 9: System Architecture Diagram', '', '', '', '', '', '', '', ''],
    ['Section 10: Troubleshooting Guide', '', '', '', '', '', '', '', ''],
    ['Section 11: Update Schedules & Monitoring', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 1: SHEET PURPOSE OVERVIEW
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 1: SHEET PURPOSE OVERVIEW', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['Sheet Name', 'Purpose', 'Update Frequency', 'Primary Users', 'Key Features'],
    ['Live Dashboard v2', 'Real-time GB electricity market monitoring', 'Every 5 minutes (automated)', 'Traders, analysts, operators', 'System prices, BM KPIs, VLP revenue, outages, interconnectors, sparklines'],
    ['Data_Hidden', 'Raw data storage for dashboard calculations', 'Every 5 minutes (automated)', 'System (internal)', '48 settlement periods × fuel types, interconnectors, market metrics'],
    ['VLP_Data', 'Battery operator revenue analysis', 'On-demand (manual refresh)', 'Battery traders, VLP operators', 'Detailed revenue, margin, dispatch patterns for individual units'],
    ['BtM Calculator', 'Behind-the-meter savings calculator', 'Manual input', 'Commercial sites, solar+storage', 'ROI calculation, import/export tariffs, generation offsets'],
    ['BESS', 'Battery system DUoS calculator', 'On-demand (button trigger)', 'Battery operators, DNOs', 'Postcode → DNO region, DUoS rates by time band (Red/Amber/Green)'],
    ['DATA', 'Platform documentation & data catalog', 'Static reference', 'Developers, data analysts', 'BigQuery tables, Python scripts, SQL examples, sophistication metrics'],
    ['DATA DICTIONARY', 'Complete KPI glossary', 'Static reference', 'All users', 'Every column/metric definition with units, sources, calculations'],
    ['INSTRUCTIONS', 'User guide (this sheet)', 'Static reference', 'New users, troubleshooting', 'How to use all features, system architecture, troubleshooting'],
    ['publication_dashboard_live', 'Wind forecast data', 'Every 15 minutes (automated)', 'Wind traders, forecasters', 'Elexon WINDFOR 14-day ahead forecasts'],
    [''],

    # ========================================================================
    # SECTION 2: LIVE DASHBOARD V2 USAGE GUIDE
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 2: LIVE DASHBOARD V2 USAGE GUIDE', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['🎯 KEY SECTIONS & HOW TO READ THEM', '', '', '', '', '', '', '', ''],
    [''],
    ['IRIS Freshness Indicator (A2-A3)', '', '', '', '', '', '', '', ''],
    ['→ Green text = Data fresh (<10 min old)', '', '', '', '', '', '', '', ''],
    ['→ Yellow/Orange = Stale data (10-30 min)', '', '', '', '', '', '', '', ''],
    ['→ Red = Very stale (>30 min) - check IRIS pipeline', '', '', '', '', '', '', '', ''],
    ['→ Location: Top-left corner, updates every 5 min', '', '', '', '', '', '', '', ''],
    [''],
    ['Market Metrics (A5-B9)', '', '', '', '', '', '', '', ''],
    ['→ BM-MID Spread (A5): Balancing premium over wholesale', '', '', '', '', '', '', '', ''],
    ['→ Typical: £15-40/MWh | High stress: £50+/MWh', '', '', '', '', '', '', '', ''],
    ['→ Market Index (C5): Wholesale day-ahead price', '', '', '', '', '', '', '', ''],
    ['→ Sparkline (A7-B9): 48-period trend (merged cell)', '', '', '', '', '', '', '', ''],
    ['→ HOVER over cells for detailed tooltips!', '', '', '', '', '', '', '', ''],
    [''],
    ['Combined KPIs (K12:S22) - MAIN DASHBOARD SECTION', '', '', '', '', '', '', '', ''],
    ['→ K12 Header: "📊 Bar MARKET DYNAMICS - 24 HOUR VIEW"', '', '', '', '', '', '', '', ''],
    ['→ Row Heights: 50px header, 38px data rows (increased for readability)', '', '', '', '', '', '', '', ''],
    ['→ Sparklines: 6 columns wide (N-S merged) for large visualizations', '', '', '', '', '', '', '', ''],
    ['→ K13-K18: System Price KPIs (current, averages, deviation, highs/lows)', '', '', '', '', '', '', '', ''],
    ['→ K19-K22: BM Financial KPIs (cashflow, EWAP, dispatch intensity)', '', '', '', '', '', '', '', ''],
    ['→ HOVER over K13-K22 for detailed explanations of each KPI!', '', '', '', '', '', '', '', ''],
    [''],
    ['Reading KPI Rows:', '', '', '', '', '', '', '', ''],
    ['  Column K = KPI Name (e.g., "Real-time imbalance price")', '', '', '', '', '', '', '', ''],
    ['  Column L = Current Value (e.g., "£65.11/MWh")', '', '', '', '', '', '', '', ''],
    ['  Column M = Description (e.g., "SSP=SBP")', '', '', '', '', '', '', '', ''],
    ['  Columns N-S = 6-column wide sparkline (merged for size)', '', '', '', '', '', '', '', ''],
    ['  Column S = Notes/Conditions (e.g., "⚖ Balanced" or "10.4% active")', '', '', '', '', '', '', '', ''],
    [''],
    ['VLP Revenue Analysis (L54-R67)', '', '', '', '', '', '', '', ''],
    ['→ Top 10 battery operators by 28-day MWh', '', '', '', '', '', '', '', ''],
    ['→ M = Operator (e.g., FFSEN005, FBPGM002)', '', '', '', '', '', '', '', ''],
    ['→ N = Total MWh dispatched', '', '', '', '', '', '', '', ''],
    ['→ O = Revenue (£k) - gross revenue from BM actions', '', '', '', '', '', '', '', ''],
    ['→ P = Margin (£/MWh) - KEY PROFITABILITY METRIC', '', '', '', '', '', '', '', ''],
    ['→ Q = BM Price (avg imbalance price received)', '', '', '', '', '', '', '', ''],
    ['→ R = Wholesale (avg MID price for comparison)', '', '', '', '', '', '', '', ''],
    ['→ Row 67 = Totals (sum of all operators)', '', '', '', '', '', '', '', ''],
    [''],
    ['Active Outages (G25-K41)', '', '', '', '', '', '', '', ''],
    ['→ G25 Header shows totals: "15 units | 6,524 MW offline"', '', '', '', '', '', '', '', ''],
    ['→ Top 15 generators by unavailable capacity', '', '', '', '', '', '', '', ''],
    ['→ Fuel type emojis: 🏭 CCGT, ⚛️ Nuclear, 🌬️ Wind, 🔋 PS, 🇫🇷 IFA', '', '', '', '', '', '', '', ''],
    ['→ Updates from REMIT (EU market transparency messages)', '', '', '', '', '', '', '', ''],
    [''],
    ['Interconnectors (G13-H22)', '', '', '', '', '', '', '', ''],
    ['→ 10 cross-border electricity links', '', '', '', '', '', '', '', ''],
    ['→ Positive MW = Import to GB | Negative = Export from GB', '', '', '', '', '', '', '', ''],
    ['→ Real-time data from IRIS stream', '', '', '', '', '', '', '', ''],
    ['→ Sparklines show 48-period flow trends', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 3: VLP REVENUE ANALYSIS
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 3: VLP REVENUE ANALYSIS - BATTERY TRADING INSIGHTS', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['🔋 WHAT IS VLP?', '', '', '', '', '', '', '', ''],
    ['Virtual Lead Party = Battery operators submitting bids/offers to National Grid balancing mechanism', '', '', '', '', '', '', '', ''],
    ['Revenue model: Charge when prices low → Discharge when prices high', '', '', '', '', '', '', '', ''],
    ['Profit from system imbalance volatility', '', '', '', '', '', '', '', ''],
    [''],
    ['📊 KEY METRICS EXPLAINED', '', '', '', '', '', '', '', ''],
    [''],
    ['Total MWh (Column N):', '', '', '', '', '', '', '', ''],
    ['→ Sum of all discharge volumes (MWh) over 28-day period', '', '', '', '', '', '', '', ''],
    ['→ Typical: 5,000-20,000 MWh/month per unit', '', '', '', '', '', '', ''],
    ['→ High activity: >20,000 MWh (unit running frequently)', '', '', '', '', '', '', '', ''],
    [''],
    ['Revenue (Column O):', '', '', '', '', '', '', '', ''],
    ['→ Σ(Volume × acceptancePrice) - gross revenue before costs', '', '', '', '', '', '', '', ''],
    ['→ Typical: £500k-5,000k/month', '', '', '', '', '', '', ''],
    ['→ High-value events (Oct 17-23, 2025): £80k/day per unit', '', '', '', '', '', '', '', ''],
    ['→ Source: bmrs_boalf_complete (prices matched from BOD)', '', '', '', '', '', '', '', ''],
    [''],
    ['Margin (Column P) - MOST IMPORTANT:', '', '', '', '', '', '', '', ''],
    ['→ Revenue / Total MWh = average £/MWh earned', '', '', '', '', '', '', '', ''],
    ['→ Typical: £20-150/MWh', '', '', '', '', '', '', '', ''],
    ['→ Good: >£100/MWh (premium arbitrage)', '', '', '', '', '', '', '', ''],
    ['→ Excellent: >£500/MWh (extreme stress events)', '', '', '', '', '', '', '', ''],
    ['→ Break-even: ~£10-20/MWh (covers cycling costs)', '', '', '', '', '', '', '', ''],
    [''],
    ['BM Price vs Wholesale:', '', '', '', '', '', '', '', ''],
    ['→ BM Price (Q): Average imbalance price when dispatching', '', '', '', '', '', '', '', ''],
    ['→ Wholesale (R): Average MID price (opportunity cost)', '', '', '', '', '', '', '', ''],
    ['→ Spread = Q - R = balancing premium earned', '', '', '', '', '', '', '', ''],
    [''],
    ['💡 TRADING SIGNALS (Based on Historical Analysis)', '', '', '', '', '', '', '', ''],
    [''],
    ['EWAP Offer (Live Dashboard K20) | Strategy:', '', '', '', '', '', '', '', ''],
    ['>£70/MWh    → AGGRESSIVE DISCHARGE (high revenue opportunity)', '', '', '', '', '', '', '', ''],
    ['£40-70/MWh  → MODERATE DISCHARGE (reasonable margins)', '', '', '', '', '', '', '', ''],
    ['£25-40/MWh  → PRESERVE CYCLES (low margins, wait for better prices)', '', '', '', '', '', '', '', ''],
    ['<£25/MWh    → CHARGE (if EWAP Bid >£50, otherwise hold)', '', '', '', '', '', '', '', ''],
    [''],
    ['Historical High-Value Event: Oct 17-23, 2025', '', '', '', '', '', '', '', ''],
    ['→ Avg system price: £79.83/MWh', '', '', '', '', '', '', '', ''],
    ['→ EWAP Offer: £110/MWh', '', '', '', '', '', '', '', ''],
    ['→ VLP revenue: £80k/day (FFSEN005)', '', '', '', '', '', '', '', ''],
    ['→ 80%+ of monthly revenue earned in 6 days', '', '', '', '', '', '', '', ''],
    ['→ Strategy: Aggressive dispatch at every opportunity, 100% workhorse index', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 4: BESS CALCULATOR
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 4: BESS CALCULATOR - DNO CHARGES & TIME BANDS', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['🔌 PURPOSE: Calculate Distribution Use of System (DUoS) charges for battery sites', '', '', '', '', '', '', '', ''],
    [''],
    ['📍 HOW TO USE:', '', '', '', '', '', '', '', ''],
    [''],
    ['1. ENTER POSTCODE (A6):', '', '', '', '', '', '', '', ''],
    ['   → UK postcode format: SW1A 1AA', '', '', '', '', '', '', '', ''],
    ['   → Used to determine DNO region via postcodes.io API', '', '', '', '', '', '', '', ''],
    [''],
    ['2. ENTER MPAN (B6):', '', '', '', '', '', '', '', ''],
    ['   → 13-digit Meter Point Administration Number', '', '', '', '', '', '', '', ''],
    ['   → Example: 1405566778899', '', '', '', '', '', '', '', ''],
    ['   → First 2 digits of MPAN core = distributor ID (14 = NGED West Midlands)', '', '', '', '', '', '', '', ''],
    [''],
    ['3. SELECT VOLTAGE (A9 DROPDOWN):', '', '', '', '', '', '', '', ''],
    ['   → LV (Low Voltage): <1kV, small commercial', '', '', '', '', '', '', '', ''],
    ['   → HV (High Voltage): 1-20kV, large industrial', '', '', '', '', '', '', ''],
    ['   → EHV (Extra High Voltage): >20kV, very large sites', '', '', '', '', '', '', ''],
    [''],
    ['4. CLICK "REFRESH DNO INFO" BUTTON:', '', '', '', '', '', '', '', ''],
    ['   → Triggers webhook → Python script → BigQuery lookups', '', '', '', '', '', '', '', ''],
    ['   → Populates C6-H6 with DNO details', '', '', '', '', '', '', '', ''],
    ['   → Populates B9-D9 with DUoS rates (Red/Amber/Green)', '', '', '', '', '', '', '', ''],
    ['   → Populates A11-C13 with time band definitions', '', '', '', '', '', '', '', ''],
    [''],
    ['📊 READING THE RESULTS:', '', '', '', '', '', '', '', ''],
    [''],
    ['DNO Region (C6-H6):', '', '', '', '', '', '', '', ''],
    ['→ Example: "NGED West Midlands (WMID)"', '', '', '', '', '', '', '', ''],
    ['→ Shows which network operator charges apply', '', '', '', '', '', '', '', ''],
    [''],
    ['DUoS Rates (B9-D9):', '', '', '', '', '', '', '', ''],
    ['→ Red: Highest rate (peak demand periods)', '', '', '', '', '', '', '', ''],
    ['   Example: 1.764 p/kWh (HV, NGED West Midlands)', '', '', '', '', '', '', '', ''],
    ['→ Amber: Medium rate (shoulder periods)', '', '', '', '', '', '', '', ''],
    ['   Example: 0.118 p/kWh', '', '', '', '', '', '', '', ''],
    ['→ Green: Lowest rate (off-peak)', '', '', '', '', '', '', '', ''],
    ['   Example: 0.038 p/kWh', '', '', '', '', '', '', '', ''],
    [''],
    ['Time Bands (A11-C13):', '', '', '', '', '', '', '', ''],
    ['→ Shows WHEN each rate applies', '', '', '', '', '', '', '', ''],
    ['→ Red example: "16:00-19:30 weekdays" (peak demand)', '', '', '', '', '', '', '', ''],
    ['→ Amber example: "08:00-16:00, 19:30-22:00 weekdays"', '', '', '', '', '', '', '', ''],
    ['→ Green example: "00:00-08:00, 22:00-23:59 weekdays + all weekend"', '', '', '', '', '', '', '', ''],
    [''],
    ['💡 BATTERY STRATEGY:', '', '', '', '', '', '', '', ''],
    ['→ AVOID discharging during Red periods (high network charges)', '', '', '', '', '', '', '', ''],
    ['→ PREFER discharging during Green periods (low network charges)', '', '', '', '', '', '', '', ''],
    ['→ Balance against imbalance prices (from Live Dashboard K13)', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 5: DATA & DATA DICTIONARY
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 5: DATA & DATA DICTIONARY NAVIGATION', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['📊 DATA SHEET - Platform Documentation', '', '', '', '', '', '', '', ''],
    ['→ Section 1: Platform sophistication metrics (174+ tables, 391M+ rows, etc)', '', '', '', '', '', '', '', ''],
    ['→ Section 2: BigQuery tables with row counts, sizes, date ranges', '', '', '', '', '', '', '', ''],
    ['→ Section 3: Python scripts with purposes, schedules', '', '', '', '', '', '', '', ''],
    ['→ Section 4: Data collection methods (IRIS, Elexon API, etc)', '', '', '', '', '', '', '', ''],
    ['→ Section 5: Update schedules & monitoring', '', '', '', '', '', '', '', ''],
    ['→ INCLUDES: Example SQL queries you can run', '', '', '', '', '', '', '', ''],
    [''],
    ['📚 DATA DICTIONARY SHEET - Complete KPI Glossary', '', '', '', '', '', '', '', ''],
    ['→ 102 entries covering ALL metrics across ALL sheets', '', '', '', '', '', '', '', ''],
    ['→ Columns: Sheet, Column/KPI, Description, Units, Source, Update Freq, Calculation, Examples', '', '', '', '', '', '', '', ''],
    ['→ Covers: Live Dashboard v2, VLP_Data, BESS, BtM Calculator, BigQuery tables', '', '', '', '', '', '', '', ''],
    ['→ Use Ctrl+F to search for any metric', '', '', '', '', '', '', '', ''],
    [''],
    ['🔍 HOW TO FIND INFORMATION:', '', '', '', '', '', '', '', ''],
    ['1. Know the metric name? → Search DATA DICTIONARY', '', '', '', '', '', '', '', ''],
    ['2. Want to query data? → Check DATA sheet Section 3 for Python scripts', '', '', '', '', '', '', '', ''],
    ['3. Need SQL examples? → Check DATA sheet bottom for query templates', '', '', '', '', '', '', '', ''],
    ['4. System architecture? → This sheet (INSTRUCTIONS) Section 8-9', '', '', '', '', '', '', '', ''],
    ['5. Troubleshooting? → This sheet Section 10', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 6: PYTHON QUERY EXAMPLES
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 6: PYTHON QUERY EXAMPLES', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['🐍 RUNNING QUERIES FROM TERMINAL:', '', '', '', '', '', '', '', ''],
    [''],
    ['Setup (one-time):', '', '', '', '', '', '', '', ''],
    ['$ export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"', '', '', '', '', '', '', '', ''],
    ['$ pip3 install --user google-cloud-bigquery pandas pyarrow', '', '', '', '', '', '', '', ''],
    [''],
    ['Basic Query Template:', '', '', '', '', '', '', '', ''],
    ['```python', '', '', '', '', '', '', '', ''],
    ['from google.cloud import bigquery', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['PROJECT_ID = "inner-cinema-476211-u9"', '', '', '', '', '', '', '', ''],
    ['client = bigquery.Client(project=PROJECT_ID, location="US")', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['query = """', '', '', '', '', '', '', '', ''],
    ['SELECT settlementDate, AVG(systemSellPrice) as avg_price', '', '', '', '', '', '', '', ''],
    ['FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`', '', '', '', '', '', '', '', ''],
    ['WHERE settlementDate >= CURRENT_DATE() - 7', '', '', '', '', '', '', '', ''],
    ['GROUP BY settlementDate ORDER BY settlementDate', '', '', '', '', '', '', '', ''],
    ['LIMIT 100', '', '', '', '', '', '', '', ''],
    ['"""', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['df = client.query(query).to_dataframe()', '', '', '', '', '', '', '', ''],
    ['print(df)', '', '', '', '', '', '', '', ''],
    ['```', '', '', '', '', '', '', '', ''],
    [''],
    ['🔥 USEFUL PRE-BUILT SCRIPTS:', '', '', '', '', '', '', '', ''],
    ['→ update_live_metrics.py: See current dashboard code', '', '', '', '', '', '', '', ''],
    ['→ check_table_coverage.sh: Check any table date range/row count', '', '', '', '', '', '', '', ''],
    ['   Usage: ./check_table_coverage.sh bmrs_bod', '', '', '', '', '', '', '', ''],
    ['→ add_vlp_correct_calculation.py: VLP revenue with prices', '', '', '', '', '', '', '', ''],
    ['→ advanced_statistical_analysis_enhanced.py: Stats suite (correlation, regression)', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 7: CHATGPT INTEGRATION
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 7: CHATGPT INTEGRATION - NATURAL LANGUAGE QUERIES', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['🤖 WHAT YOU CAN ASK:', '', '', '', '', '', '', '', ''],
    ['→ "What was the average system price last week?"', '', '', '', '', '', '', '', ''],
    ['→ "Show me VLP revenue for FFSEN005 in October"', '', '', '', '', '', '', '', ''],
    ['→ "How many MWh did batteries dispatch yesterday?"', '', '', '', '', '', '', '', ''],
    ['→ "What are the current interconnector flows?"', '', '', '', '', '', '', '', ''],
    ['→ "Calculate BM-MID spread for the last 48 periods"', '', '', '', '', '', '', '', ''],
    [''],
    ['🔧 HOW IT WORKS:', '', '', '', '', '', '', '', ''],
    ['1. You ask question in plain English', '', '', '', '', '', '', '', ''],
    ['2. ChatGPT converts to SQL query', '', '', '', '', '', '', '', ''],
    ['3. Vercel Edge Function validates SQL', '', '', '', '', '', '', '', ''],
    ['4. BigQuery executes query', '', '', '', '', '', '', '', '', ''],
    ['5. JSON results returned to ChatGPT', '', '', '', '', '', '', '', ''],
    ['6. ChatGPT formats answer in natural language', '', '', '', '', '', '', '', '', ''],
    [''],
    ['🌐 ENDPOINT:', '', '', '', '', '', '', '', '', ''],
    ['→ https://gb-power-market-jj.vercel.app/api/proxy-v2', '', '', '', '', '', '', '', ''],
    ['→ Secured with SQL validation, project whitelist, rate limiting', '', '', '', '', '', '', '', ''],
    ['→ Free tier (Vercel Edge Functions)', '', '', '', '', '', '', '', ''],
    [''],
    ['🔐 SECURITY:', '', '', '', '', '', '', '', '', ''],
    ['→ Read-only access (SELECT queries only)', '', '', '', '', '', '', '', ''],
    ['→ SQL injection prevention', '', '', '', '', '', '', '', '', ''],
    ['→ Project whitelist (only inner-cinema-476211-u9 allowed)', '', '', '', '', '', '', '', ''],
    ['→ Rate limiting: 100 requests/minute', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 8: DATA COLLECTION ARCHITECTURE
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 8: DATA COLLECTION ARCHITECTURE - HOW DATA FLOWS', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['🔄 DUAL-PIPELINE SYSTEM:', '', '', '', '', '', '', '', ''],
    [''],
    ['PIPELINE 1: HISTORICAL BATCH (2020-present)', '', '', '', '', '', '', '', ''],
    ['┌─────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│ Elexon BMRS REST API                                       │', '', '', '', '', '', '', '', ''],
    ['│   https://api.bmreports.com/BMRS/...                       │', '', '', '', '', '', '', '', ''],
    ['└────────────────┬────────────────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    ['                 │ HTTP GET requests every 15 minutes', '', '', '', '', '', '', '', ''],
    ['                 ▼', '', '', '', '', '', '', '', ''],
    ['┌─────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│ ingest_elexon_fixed.py                                      │', '', '', '', '', '', '', '', ''],
    ['│   - Downloads 174+ BMRS tables                             │', '', '', '', '', '', '', '', ''],
    ['│   - Handles pagination, retries, rate limiting             │', '', '', '', '', '', '', '', ''],
    ['│   - Deduplicates existing data                             │', '', '', '', '', '', '', '', ''],
    ['│   - Cron: */15 * * * * (every 15 minutes)                  │', '', '', '', '', '', '', '', ''],
    ['└────────────────┬────────────────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    ['                 │ INSERT INTO BigQuery', '', '', '', '', '', '', '', ''],
    ['                 ▼', '', '', '', '', '', '', '', ''],
    ['┌─────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│ BigQuery: inner-cinema-476211-u9.uk_energy_prod            │', '', '', '', '', '', '', '', ''],
    ['│   - bmrs_bod (391M rows), bmrs_costs (50M), etc            │', '', '', '', '', '', '', '', ''],
    ['│   - Historical data: 2020-present                          │', '', '', '', '', '', '', '', ''],
    ['│   - Location: US region                                    │', '', '', '', '', '', '', '', ''],
    ['└─────────────────────────────────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    [''],
    ['PIPELINE 2: REAL-TIME IRIS (24-48h rolling)', '', '', '', '', '', '', '', ''],
    ['┌─────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│ Azure Service Bus (IRIS Topics)                            │', '', '', '', '', '', '', '', ''],
    ['│   - FUELINST, INDGEN, FREQ, COSTS, etc                     │', '', '', '', '', '', '', '', ''],
    ['│   - Messages published every 5 minutes                     │', '', '', '', '', '', '', '', ''],
    ['└────────────────┬────────────────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    ['                 │ Subscribe to topics', '', '', '', '', '', '', '', ''],
    ['                 ▼', '', '', '', '', '', '', '', ''],
    ['┌─────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│ AlmaLinux VPS: 94.237.55.234                                │', '', '', '', '', '', '', '', ''],
    ['│   - iris-clients/python/client.py                          │', '', '', '', '', '', '', '', ''],
    ['│     → Downloads messages to JSON files                     │', '', '', '', '', '', '', '', ''],
    ['│     → systemd service: iris-client.service                 │', '', '', '', '', '', '', '', ''],
    ['│   - iris_to_bigquery_unified.py                            │', '', '', '', '', '', '', '', ''],
    ['│     → Parses JSON → BigQuery upload                        │', '', '', '', '', '', '', '', ''],
    ['│     → systemd service: iris-uploader.service               │', '', '', '', '', '', '', '', ''],
    ['│     → Runs every 5 minutes                                 │', '', '', '', '', '', '', '', ''],
    ['└────────────────┬────────────────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    ['                 │ INSERT INTO BigQuery', '', '', '', '', '', '', '', ''],
    ['                 ▼', '', '', '', '', '', '', '', ''],
    ['┌─────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│ BigQuery: inner-cinema-476211-u9.uk_energy_prod            │', '', '', '', '', '', '', '', ''],
    ['│   - bmrs_costs_iris, bmrs_fuelinst_iris, etc               │', '', '', '', '', '', '', '', ''],
    ['│   - Real-time data: 24-48h rolling window                  │', '', '', '', '', '', '', '', ''],
    ['│   - Automatically cleaned up (old data deleted)            │', '', '', '', '', '', '', '', ''],
    ['└─────────────────────────────────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    [''],
    ['UNIFIED QUERY PATTERN:', '', '', '', '', '', '', '', ''],
    ['```sql', '', '', '', '', '', '', '', ''],
    ['-- Combine historical + real-time seamlessly', '', '', '', '', '', '', '', ''],
    ['WITH combined AS (', '', '', '', '', '', '', '', ''],
    ['  SELECT * FROM `uk_energy_prod.bmrs_costs`', '', '', '', '', '', '', '', ''],
    ['  WHERE settlementDate < CURRENT_DATE() - 1', '', '', '', '', '', '', '', ''],
    ['  UNION ALL', '', '', '', '', '', '', '', ''],
    ['  SELECT * FROM `uk_energy_prod.bmrs_costs_iris`', '', '', '', '', '', '', '', ''],
    ['  WHERE settlementDate >= CURRENT_DATE() - 1', '', '', '', '', '', '', '', ''],
    [')', '', '', '', '', '', '', '', ''],
    ['SELECT * FROM combined ORDER BY settlementDate DESC;', '', '', '', '', '', '', '', ''],
    ['```', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 9: SYSTEM ARCHITECTURE DIAGRAM
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 9: COMPLETE SYSTEM ARCHITECTURE DIAGRAM', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['┌────────────────────────────────────────────────────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['│                          DATA SOURCES (EXTERNAL)                               │', '', '', '', '', '', '', '', ''],
    ['└──────────────────┬────────────────────────────┬────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    ['                   │                            │', '', '', '', '', '', '', '', ''],
    ['         ┌─────────▼─────────┐       ┌──────────▼──────────┐', '', '', '', '', '', '', '', ''],
    ['         │  Elexon BMRS API  │       │  Azure IRIS Stream  │', '', '', '', '', '', '', '', ''],
    ['         │  (Historical)     │       │  (Real-time)        │', '', '', '', '', '', '', '', ''],
    ['         │  174+ tables      │       │  10+ topics         │', '', '', '', '', '', '', '', ''],
    ['         │  2020-present     │       │  5-min messages     │', '', '', '', '', '', '', '', ''],
    ['         └─────────┬─────────┘       └──────────┬──────────┘', '', '', '', '', '', '', '', ''],
    ['                   │                            │', '', '', '', '', '', '', '', ''],
    ['        ┌──────────▼──────────┐      ┌──────────▼──────────────┐', '', '', '', '', '', '', '', ''],
    ['        │ ingest_elexon_fixed │      │  AlmaLinux VPS          │', '', '', '', '', '', '', '', ''],
    ['        │ Every 15 min (cron) │      │  94.237.55.234          │', '', '', '', '', '', '', '', ''],
    ['        │ Ubuntu local        │      │  iris-client.service    │', '', '', '', '', '', '', '', ''],
    ['        └──────────┬──────────┘      │  iris-uploader.service  │', '', '', '', '', '', '', '', ''],
    ['                   │                 └──────────┬──────────────┘', '', '', '', '', '', '', '', ''],
    ['                   │                            │', '', '', '', '', '', '', '', ''],
    ['                   └────────────┬───────────────┘', '', '', '', '', '', '', '', ''],
    ['                                │', '', '', '', '', '', '', '', ''],
    ['                    ┌───────────▼───────────────────────────────────┐', '', '', '', '', '', '', '', ''],
    ['                    │      GOOGLE CLOUD BIGQUERY                    │', '', '', '', '', '', '', '', ''],
    ['                    │  inner-cinema-476211-u9.uk_energy_prod        │', '', '', '', '', '', '', '', ''],
    ['                    │  - Historical: bmrs_bod, bmrs_costs, etc      │', '', '', '', '', '', '', '', ''],
    ['                    │  - Real-time: *_iris tables                   │', '', '', '', '', '', '', '', ''],
    ['                    │  - 500M+ rows, ~50-100 GB                     │', '', '', '', '', '', '', '', ''],
    ['                    │  - Location: US region                        │', '', '', '', '', '', '', '', ''],
    ['                    └───────────┬───────────────────────────────────┘', '', '', '', '', '', '', '', ''],
    ['                                │', '', '', '', '', '', '', '', ''],
    ['                ┌───────────────┼───────────────┐', '', '', '', '', '', '', '', ''],
    ['                │               │               │', '', '', '', '', '', '', '', ''],
    ['     ┌──────────▼─────────┐   │   ┌──────────▼──────────┐', '', '', '', '', '', '', '', ''],
    ['     │ update_live_metrics│   │   │  Vercel Edge Proxy  │', '', '', '', '', '', '', '', ''],
    ['     │ Every 5 min (cron) │   │   │  /api/proxy-v2      │', '', '', '', '', '', '', '', ''],
    ['     │ Ubuntu local       │   │   │  SQL validation     │', '', '', '', '', '', '', '', ''],
    ['     └──────────┬─────────┘   │   └──────────┬──────────┘', '', '', '', '', '', '', '', ''],
    ['                │             │              │', '', '', '', '', '', '', '', ''],
    ['                │             │              │', '', '', '', '', '', '', '', ''],
    ['     ┌──────────▼─────────────▼────┐        │', '', '', '', '', '', '', '', ''],
    ['     │  GOOGLE SHEETS               │        │', '', '', '', '', '', '', '', ''],
    ['     │  1-u794iGngn5_Ql_Xo...       │        │', '', '', '', '', '', '', '', ''],
    ['     │  - Live Dashboard v2         │        │', '', '', '', '', '', '', '', ''],
    ['     │  - VLP_Data                  │        │', '', '', '', '', '', '', '', ''],
    ['     │  - BESS Calculator           │        │', '', '', '', '', '', '', '', ''],
    ['     │  - DATA, DATA DICTIONARY     │        │', '', '', '', '', '', '', '', ''],
    ['     │  - INSTRUCTIONS (this)       │        │', '', '', '', '', '', '', '', ''],
    ['     │  Updates via Google API      │        │', '', '', '', '', '', '', '', ''],
    ['     │  5 service accounts          │        │', '', '', '', '', '', '', '', ''],
    ['     └──────────────────────────────┘        │', '', '', '', '', '', '', '', ''],
    ['                                              │', '', '', '', '', '', '', '', ''],
    ['                                   ┌──────────▼──────────┐', '', '', '', '', '', '', '', ''],
    ['                                   │      CHATGPT         │', '', '', '', '', '', '', '', ''],
    ['                                   │  Natural language    │', '', '', '', '', '', '', '', ''],
    ['                                   │  → SQL → Results     │', '', '', '', '', '', '', '', ''],
    ['                                   └─────────────────────┘', '', '', '', '', '', '', '', ''],
    [''],
    ['📊 DATA FLOW SUMMARY:', '', '', '', '', '', '', '', ''],
    ['1. Elexon API → ingest_elexon_fixed.py → BigQuery (historical)', '', '', '', '', '', '', '', ''],
    ['2. Azure IRIS → AlmaLinux VPS → BigQuery (real-time)', '', '', '', '', '', '', '', ''],
    ['3. BigQuery → update_live_metrics.py → Google Sheets (dashboard)', '', '', '', '', '', '', '', ''],
    ['4. BigQuery → Vercel proxy → ChatGPT (queries)', '', '', '', '', '', '', '', ''],
    [''],
    ['⏱️ UPDATE FREQUENCIES:', '', '', '', '', '', '', '', ''],
    ['→ IRIS upload: Continuous (new data every 5-10 min)', '', '', '', '', '', '', '', ''],
    ['→ Historical ingest: Every 15 min', '', '', '', '', '', '', '', ''],
    ['→ Dashboard refresh: Every 5 min', '', '', '', '', '', '', '', ''],
    ['→ Data lag: 5-120 min (varies by source)', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 10: TROUBLESHOOTING
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 10: TROUBLESHOOTING GUIDE', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: Dashboard not updating (AA1 timestamp frozen)', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ Check cron job running: crontab -l | grep update_live_metrics', '', '', '', '', '', '', '', ''],
    ['→ Check for errors: tail ~/GB-Power-Market-JJ/logs/dashboard_updater.log', '', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ Restart cron: crontab -e (verify entries exist)', '', '', '', '', '', '', '', ''],
    ['→ Run manually: cd ~/GB-Power-Market-JJ && python3 update_live_metrics.py', '', '', '', '', '', '', '', ''],
    ['→ Check credentials: ls -la inner-cinema-credentials.json', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: BM KPIs (K19-K22) showing zeros', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ EBOCF/BOAV data lags 2-4 hours behind real-time', '', '', '', '', '', '', '', ''],
    ['→ Check table: python3 check_table_coverage.sh bmrs_ebocf', '', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ WAIT 2-4 hours if recent settlement period', '', '', '', '', '', '', '', ''],
    ['→ Check Elexon API status: https://www.bmreports.com', '', '', '', '', '', '', '', ''],
    ['→ If prolonged: Verify ingest scripts running', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: IRIS data stale (red freshness indicator)', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ Check AlmaLinux services: ssh root@94.237.55.234', '', '', '', '', '', '', '', ''],
    ['→ systemctl status iris-client.service', '', '', '', '', '', '', '', ''],
    ['→ systemctl status iris-uploader.service', '', '', '', '', '', '', '', ''],
    ['→ Check logs: tail -f /opt/iris-pipeline/logs/iris_uploader.log', '', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ Restart services: systemctl restart iris-client iris-uploader', '', '', '', '', '', '', '', ''],
    ['→ Check Azure Service Bus connection', '', '', '', '', '', '', '', ''],
    ['→ Verify credentials in /opt/iris-pipeline/config/', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: Sparklines not showing', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ Check Data_Hidden sheet has data (should have 48 cols of numbers)', '', '', '', '', '', '', '', ''],
    ['→ Inspect sparkline formula in cell (should be SPARKLINE function)', '', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ Re-run dashboard update: python3 update_live_metrics.py', '', '', '', '', '', '', '', ''],
    ['→ If formulas missing: Check script line ~1062-1156 (KPI section)', '', '', '', '', '', '', '', ''],
    ['→ Manual fix: Extensions → Apps Script → paste dashboard_charts.gs', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: VLP revenue shows £0 or very low', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ Check bmrs_boalf_complete table coverage', '', '', '', '', '', '', '', ''],
    ['→ Query: SELECT COUNT(*), MAX(settlementDate) FROM bmrs_boalf_complete', '', '', '', '', '', '', '', ''],
    ['→ Only 42.8% of records have valid prices (Elexon B1610 filters)', '', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ Run backfill: python3 backfill_boalf_gap.py', '', '', '', '', '', '', '', ''],
    ['→ Check BOD table coverage (needed for price matching)', '', '', '', '', '', '', '', ''],
    ['→ Wait 24h (bmrs_boalf_complete updates daily)', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: BESS DNO lookup not working', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ Check webhook server: ps aux | grep dno_webhook', '', '', '', '', '', '', '', ''],
    ['→ Check ngrok tunnel: ngrok http 5001', '', '', '', '', '', '', '', ''],
    ['→ Verify webhook URL in Apps Script matches ngrok URL', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ Start webhook server: python3 dno_webhook_server.py &', '', '', '', '', '', '', '', ''],
    ['→ Start ngrok: ngrok http 5001', '', '', '', '', '', '', '', ''],
    ['→ Update Apps Script: bess_auto_trigger.gs line ~10 with new ngrok URL', '', '', '', '', '', '', '', ''],
    ['→ Test manually: python3 dno_lookup_python.py 14 HV', '', '', '', '', '', '', '', ''],
    [''],
    ['❌ PROBLEM: ChatGPT queries failing', '', '', '', '', '', '', '', ''],
    ['DIAGNOSIS:', '', '', '', '', '', '', '', ''],
    ['→ Check Vercel deployment: curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health', '', '', '', '', '', '', '', ''],
    ['→ Check BigQuery permissions: gcloud auth list', '', '', '', '', '', '', '', ''],
    ['FIX:', '', '', '', '', '', '', '', ''],
    ['→ Redeploy Vercel: cd vercel-proxy && vercel --prod', '', '', '', '', '', '', '', ''],
    ['→ Check environment variables in Vercel dashboard', '', '', '', '', '', '', '', ''],
    ['→ Verify SQL syntax (must be SELECT only, no INSERT/UPDATE/DELETE)', '', '', '', '', '', '', '', ''],
    [''],

    # ========================================================================
    # SECTION 11: UPDATE SCHEDULES
    # ========================================================================
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['SECTION 11: UPDATE SCHEDULES & MONITORING', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    [''],
    ['⏰ AUTOMATED UPDATE SCHEDULE:', '', '', '', '', '', '', '', ''],
    [''],
    ['Component             | Schedule        | Script/Service                    | Check Command', '', '', '', '', '', '', '', ''],
    ['──────────────────────|─────────────────|───────────────────────────────────|──────────────────────', '', '', '', '', '', '', '', ''],
    ['Live Dashboard v2     | Every 5 min     | update_live_metrics.py (cron)     | Check AA1 cell', '', '', '', '', '', '', '', ''],
    ['IRIS Upload           | Continuous      | iris-uploader.service (systemd)   | python3 check_iris_data.py', '', '', '', '', '', '', '', ''],
    ['Historical Ingest     | Every 15 min    | ingest_elexon_fixed.py (cron)     | ./check_table_coverage.sh', '', '', '', '', '', '', '', ''],
    ['Wind Forecast         | Every 15 min    | build_publication_table_current   | Query publication_dashboard_live', '', '', '', '', '', '', '', ''],
    ['Costs Backfill        | Daily 03:00     | auto_backfill_costs_daily.py      | Check bmrs_costs gaps', '', '', '', '', '', '', '', ''],
    ['Disbsad Backfill      | Daily 03:00     | auto_backfill_disbsad_daily.py    | Check bmrs_disbsad gaps', '', '', '', '', '', '', '', ''],
    ['BOALF Complete        | Daily 04:00     | BOD matching logic                | Check bmrs_boalf_complete', '', '', '', '', '', '', '', ''],
    [''],
    ['📊 MONITORING COMMANDS:', '', '', '', '', '', '', '', ''],
    [''],
    ['Check dashboard freshness:', '', '', '', '', '', '', '', ''],
    ['→ Open Live Dashboard v2, check AA1 timestamp (should be <5 min old)', '', '', '', '', '', '', '', ''],
    [''],
    ['Check IRIS pipeline:', '', '', '', '', '', '', '', ''],
    ['→ ssh root@94.237.55.234', '', '', '', '', '', '', '', ''],
    ['→ systemctl status iris-client iris-uploader', '', '', '', '', '', '', '', ''],
    ['→ tail -f /opt/iris-pipeline/logs/iris_uploader.log', '', '', '', '', '', '', '', ''],
    [''],
    ['Check historical ingestion:', '', '', '', '', '', '', '', ''],
    ['→ tail ~/GB-Power-Market-JJ/logs/ingest*.log', '', '', '', '', '', '', '', ''],
    ['→ ./check_table_coverage.sh bmrs_costs', '', '', '', '', '', '', '', ''],
    [''],
    ['Check BigQuery table stats:', '', '', '', '', '', '', '', ''],
    ['→ python3 -c "from google.cloud import bigquery; ..." (see DATA sheet for queries)', '', '', '', '', '', '', '', ''],
    [''],
    ['Check cron jobs:', '', '', '', '', '', '', '', ''],
    ['→ crontab -l', '', '', '', '', '', '', '', ''],
    ['→ Should see: update_live_metrics.py (*/5), ingest_elexon_fixed.py (*/15)', '', '', '', '', '', '', '', ''],
    [''],
    ['🏥 HEALTH CHECK TARGETS:', '', '', '', '', '', '', '', ''],
    [''],
    ['Metric                | Healthy         | Warning         | Critical         | Action', '', '', '', '', '', '', '', ''],
    ['──────────────────────|─────────────────|─────────────────|──────────────────|────────────────', '', '', '', '', '', '', '', ''],
    ['AA1 Timestamp Age     | <5 min          | 5-10 min        | >10 min          | Restart cron', '', '', '', '', '', '', '', ''],
    ['IRIS Data Age (A2)    | <10 min         | 10-30 min       | >30 min          | Restart systemd', '', '', '', '', '', '', '', ''],
    ['BM Cashflow (K19)     | >£50k           | £10k-50k        | £0               | Wait 2-4h (lag)', '', '', '', '', '', '', '', ''],
    ['VLP Revenue (O67)     | >£100k (28d)    | £50k-100k       | <£50k            | Check boalf_complete', '', '', '', '', '', '', '', ''],
    ['Sparklines            | All visible     | Some missing    | All blank        | Re-run update script', '', '', '', '', '', '', '', ''],
    ['Interconnector Flows  | Real numbers    | Zeros           | All blank        | Check IRIS pipeline', '', '', '', '', '', '', '', ''],
    [''],
    [''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
    ['END OF INSTRUCTIONS', '', '', '', '', '', '', '', ''],
    ['For additional help, see DATA DICTIONARY sheet or contact: george@upowerenergy.uk', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', ''],
]

print(f"📝 Writing {len(data)} rows to INSTRUCTIONS sheet...")

# Ensure all rows have exactly 9 columns (pad or truncate)
for i, row in enumerate(data):
    if len(row) < 9:
        data[i] = row + [''] * (9 - len(row))  # Pad with empty strings
    elif len(row) > 9:
        data[i] = row[:9]  # Truncate to 9 columns

# Write data in batches
batch_size = 100
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    start_row = i + 1
    end_row = start_row + len(batch) - 1
    range_name = f'A{start_row}:I{end_row}'
    worksheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
    print(f"  ✅ Wrote rows {start_row}-{end_row}")

# Format sheet
print("🎨 Applying formatting...")

# Header rows
worksheet.format('A1:I5', {
    'textFormat': {'bold': True, 'fontSize': 14},
    'horizontalAlignment': 'CENTER',
    'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
})

# Section headers (rows with ═══)
for i, row in enumerate(data, start=1):
    if row and len(row[0]) > 0 and '═══' in row[0]:
        worksheet.format(f'A{i}:I{i}', {
            'textFormat': {'bold': True, 'fontSize': 11},
            'backgroundColor': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    elif row and len(row[0]) > 0 and row[0].startswith('SECTION'):
        worksheet.format(f'A{i}:I{i}', {
            'textFormat': {'bold': True, 'fontSize': 13},
            'backgroundColor': {'red': 0.3, 'green': 0.3, 'blue': 0.9},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })

# Set column widths
column_widths = [
    {'startIndex': 0, 'endIndex': 1, 'pixelSize': 700},   # A - Main content
    {'startIndex': 1, 'endIndex': 2, 'pixelSize': 150},   # B
    {'startIndex': 2, 'endIndex': 3, 'pixelSize': 150},   # C
    {'startIndex': 3, 'endIndex': 4, 'pixelSize': 150},   # D
    {'startIndex': 4, 'endIndex': 5, 'pixelSize': 150},   # E
    {'startIndex': 5, 'endIndex': 6, 'pixelSize': 150},   # F
    {'startIndex': 6, 'endIndex': 7, 'pixelSize': 150},   # G
    {'startIndex': 7, 'endIndex': 8, 'pixelSize': 150},   # H
    {'startIndex': 8, 'endIndex': 9, 'pixelSize': 150},   # I
]

requests = []
for col_width in column_widths:
    requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': worksheet.id,
                'dimension': 'COLUMNS',
                'startIndex': col_width['startIndex'],
                'endIndex': col_width['endIndex']
            },
            'properties': {'pixelSize': col_width['pixelSize']},
            'fields': 'pixelSize'
        }
    })

worksheet.spreadsheet.batch_update({'requests': requests})

# Freeze header rows
worksheet.freeze(rows=6, cols=1)

print("✅ INSTRUCTIONS sheet created successfully!")
print(f"📊 Total entries: {len(data)}")
print(f"🔗 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
