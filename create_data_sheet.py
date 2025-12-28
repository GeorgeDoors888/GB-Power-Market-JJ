#!/usr/bin/env python3
"""
Create DATA sheet - Comprehensive data platform summary
Combines: BigQuery tables, Python scripts, sophistication metrics, size statistics
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
    worksheet = spreadsheet.worksheet('DATA')
    print("📝 Found existing DATA sheet, clearing...")
    worksheet.clear()
except gspread.WorksheetNotFound:
    print("📝 Creating new DATA sheet...")
    worksheet = spreadsheet.add_worksheet(title='DATA', rows=500, cols=12)

# ============================================================================
# HEADER & OVERVIEW
# ============================================================================
header = [
    ['GB POWER MARKET JJ - DATA PLATFORM SUMMARY', '', '', '', '', '', '', '', '', '', ''],
    ['Complete reference for data sources, Python capabilities, and system architecture', '', '', '', '', '', '', '', '', '', ''],
    ['Last Updated: December 23, 2025 | Project: inner-cinema-476211-u9.uk_energy_prod', '', '', '', '', '', '', '', '', '', ''],
    ['']
]

# ============================================================================
# SECTION 1: PLATFORM SOPHISTICATION METRICS
# ============================================================================
sophistication = [
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['📊 PLATFORM SOPHISTICATION & SCALE', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['Metric', 'Value', 'Description', 'Context'],
    ['Total BMRS Tables', '174+', 'Complete Elexon BMRS data catalog', 'Covers all market operations: generation, balancing, prices, outages, forecasts'],
    ['Largest Table (bmrs_bod)', '391,000,000+ rows', 'Bid-Offer Data since 2020', 'Every generator offer/bid submitted to National Grid (~200k rows/day)'],
    ['Total Dataset Size', '~50-100 GB', 'Complete uk_energy_prod dataset', 'Compressed BigQuery storage, ~500M+ total rows across all tables'],
    ['Historical Coverage', '2020-present (5+ years)', 'Batch ingestion from Elexon API', 'Complete market history for analysis and backtesting'],
    ['Real-Time Coverage', '24-48 hours rolling', 'IRIS Azure Service Bus stream', 'Live data for current market conditions and real-time trading'],
    ['Dual-Pipeline Architecture', '2 ingestion streams', 'Historical batch + real-time streaming', 'Seamless UNION queries combining 5 years history with live 24h data'],
    ['Dashboard Refresh Rate', 'Every 5 minutes', 'Automated cron job', 'update_live_metrics.py runs at :01, :06, :11, :16, etc. (12 times/hour)'],
    ['Data Latency', '5-120 minutes', 'Variable by source', 'IRIS: 5-10 min | System prices: 30-60 min | BM cashflow: 2-4 hours'],
    ['API Integrations', '4 external APIs', 'Multi-source data fusion', 'Elexon BMRS, Azure IRIS, postcodes.io, Google Sheets API'],
    ['ChatGPT Integration', 'Natural language queries', 'Vercel proxy endpoint', 'Ask questions in plain English, get SQL-powered answers from BigQuery'],
    ['Query Performance', 'Sub-second response', 'BigQuery columnar storage', 'Scan 391M rows in <2s for typical queries'],
    ['Cost Optimization', 'Free tier sufficient', '<1TB queries/month', 'BigQuery free tier: 1TB/month, Vercel: free Edge Functions'],
    ['']
]

# ============================================================================
# SECTION 2: BIGQUERY TABLES - KEY DATA SOURCES
# ============================================================================
tables_header = [
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['📊 BIGQUERY TABLES - PRIMARY DATA SOURCES', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['Table Name', 'Row Count (Est.)', 'Size (GB)', 'Date Range', 'Update Freq', 'Data Lag', 'Description', 'Primary Use Case']
]

tables_data = [
    ['bmrs_bod', '391,000,000+', '~20-30 GB', '2020-present', '15 min', '30-60 min', 'Bid-Offer Data: All generator price submissions', 'VLP revenue analysis, price discovery, BOD-BOALF matching'],
    ['bmrs_costs', '50,000,000+', '~3-5 GB', '2020-present', '5 min', '30-60 min', 'System imbalance prices (SSP/SBP)', 'Dashboard KPIs, price analysis, battery arbitrage signals'],
    ['bmrs_costs_iris', '20,000+', '<0.1 GB', '24-48h rolling', '5 min', '5-10 min', 'Real-time imbalance prices', 'Live dashboard current price'],
    ['bmrs_mid', '40,000,000+', '~2-4 GB', '2020-present', '5 min', 'Real-time', 'Market Index Data (wholesale prices)', 'BM-MID spread calculation, wholesale vs balancing comparison'],
    ['bmrs_fuelinst', '80,000,000+', '~5-8 GB', '2020-present', '5 min', '30-60 min', 'Generation by fuel type (wind, gas, nuclear, etc)', 'Fuel mix analysis, renewables tracking'],
    ['bmrs_fuelinst_iris', '30,000+', '<0.1 GB', '24-48h rolling', '5 min', '5-10 min', 'Real-time fuel generation', 'Live dashboard fuel sparklines'],
    ['bmrs_boalf', '40,000,000+', '~3-5 GB', '2020-present', '5 min', '2-4 hours', 'Balancing acceptance volumes (no prices)', 'Dispatch intensity, workhorse index, volume analysis'],
    ['bmrs_boalf_complete', '11,000,000+', '~2-3 GB', '2022-2025', 'Daily', '24 hours', 'Acceptances WITH prices (BOD matched)', 'VLP revenue calculation, EWAP analysis (42.8% valid records)'],
    ['bmrs_ebocf', '30,000,000+', '~2-3 GB', '2020-present', '5 min', '2-4 hours', 'BM cashflow data', 'Total BM cashflow KPI, financial analysis'],
    ['bmrs_boav', '35,000,000+', '~2-3 GB', '2020-present', '5 min', '2-4 hours', 'BM acceptance volumes', 'EWAP calculation (volume-weighted prices)'],
    ['bmrs_freq', '15,000,000+', '~1-2 GB', '2020-present', '5 min', '5-10 min', 'Grid frequency measurements (Hz)', 'Stability analysis, frequency response events'],
    ['bmrs_indgen_iris', '50,000+', '<0.1 GB', '24-48h rolling', '5 min', '5-10 min', 'Real-time unit generation + interconnectors', 'Live interconnector flows, individual unit dispatch'],
    ['bmrs_remit_unavailability', '5,000,000+', '~1-2 GB', '2020-present', '5 min', '30-60 min', 'Generation outages (REMIT messages)', 'Active outages dashboard section'],
    ['bmrs_disbsad', '25,000,000+', '~2-3 GB', '2020-present', '5 min', '2-4 hours', 'Balancing settlement proxy', 'Volume-weighted settlement prices (validation vs bmrs_costs)'],
    ['neso_dno_reference', '14 rows', '<0.01 GB', 'Static', 'Manual', 'N/A', 'DNO operator details (14 UK regions)', 'BESS postcode → DNO lookup'],
    ['duos_unit_rates', '~200 rows', '<0.01 GB', 'Annual', 'Manual', 'N/A', 'DUoS charges by DNO/voltage/time', 'BESS calculator DUoS rate lookup'],
    ['duos_time_bands', '~50 rows', '<0.01 GB', 'Annual', 'Manual', 'N/A', 'Red/Amber/Green time periods', 'BESS calculator time band display'],
    [''],
    ['TOTAL DATASET', '~500,000,000+ rows', '~50-100 GB', '2020-present + 24-48h IRIS', 'Mixed', 'Variable', '174+ tables total', 'Complete GB electricity market data platform']
]

tables = tables_header + tables_data + [['']]

# ============================================================================
# SECTION 3: PYTHON SCRIPTS - QUERY & ANALYSIS CAPABILITIES
# ============================================================================
python_scripts = [
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['🐍 PYTHON SCRIPTS - DATA QUERY & ANALYSIS TOOLS', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['Script Name', 'Purpose', 'Schedule', 'Target', 'Key Features'],
    ['update_live_metrics.py', 'Main dashboard updater', 'Every 5 min (cron)', 'Live Dashboard v2', 'KPIs, sparklines, VLP revenue, outages, interconnectors. 1,400+ lines.'],
    ['build_publication_table_current.py', 'Wind forecast ingestion', 'Every 15 min', 'publication_dashboard_live', 'Elexon WINDFOR data → BigQuery → dashboard'],
    ['add_vlp_correct_calculation.py', 'VLP revenue calculator', 'On-demand', 'VLP_Data sheet', 'Uses bmrs_boalf_complete for accurate revenue (with prices)'],
    ['check_table_coverage.sh', 'Data audit tool', 'On-demand', 'Terminal output', 'Check date ranges, row counts, data gaps for any table'],
    ['auto_backfill_costs_daily.py', 'System price backfill', 'Daily 03:00', 'bmrs_costs', 'Fill gaps in historical imbalance price data'],
    ['auto_backfill_disbsad_daily.py', 'Settlement proxy backfill', 'Daily 03:00', 'bmrs_disbsad', 'Volume-weighted settlement data'],
    ['iris_to_bigquery_unified.py', 'IRIS real-time uploader', 'Continuous', 'All *_iris tables', 'Azure Service Bus → BigQuery streaming pipeline'],
    ['ingest_elexon_fixed.py', 'Batch data ingestion', 'Every 15 min', 'All historical tables', 'Elexon BMRS REST API → BigQuery (174+ tables)'],
    ['dno_lookup_python.py', 'BESS DNO calculator', 'On-demand (webhook)', 'BESS sheet', 'MPAN → DNO region + DUoS rates + time bands'],
    ['advanced_statistical_analysis_enhanced.py', 'Statistical analysis suite', 'On-demand', 'Analysis outputs', 'Correlation, regression, volatility, trend analysis'],
    [''],
    ['EXAMPLE SQL QUERIES (run via Python or ChatGPT)', '', '', '', ''],
    [''],
    ['-- Get VLP revenue for last 28 days', '', '', '', ''],
    ['SELECT bmUnitId, SUM(acceptanceVolume * acceptancePrice)/1000 as revenue_k', '', '', '', ''],
    ['FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`', '', '', '', ''],
    ['WHERE validation_flag = "Valid" AND settlementDate >= CURRENT_DATE() - 28', '', '', '', ''],
    ['GROUP BY bmUnitId ORDER BY revenue_k DESC LIMIT 10;', '', '', '', ''],
    [''],
    ['-- Get system price stats for current month', '', '', '', ''],
    ['SELECT DATE(settlementDate) as date,', '', '', '', ''],
    ['  AVG(systemSellPrice) as avg_price, MAX(systemSellPrice) as max_price,', '', '', '', ''],
    ['  MIN(systemSellPrice) as min_price, STDDEV(systemSellPrice) as volatility', '', '', '', ''],
    ['FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`', '', '', '', ''],
    ['WHERE settlementDate >= DATE_TRUNC(CURRENT_DATE(), MONTH)', '', '', '', ''],
    ['GROUP BY date ORDER BY date;', '', '', '', ''],
    [''],
    ['-- Get BM-MID spread for last 48 periods', '', '', '', ''],
    ['SELECT c.settlementDate, c.settlementPeriod,', '', '', '', ''],
    ['  c.systemSellPrice - m.price as spread', '', '', '', ''],
    ['FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c', '', '', '', ''],
    ['JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` m', '', '', '', ''],
    ['  ON c.settlementDate = m.settlementDate AND c.settlementPeriod = m.settlementPeriod', '', '', '', ''],
    ['WHERE c.settlementDate >= CURRENT_DATE() - 1', '', '', '', ''],
    ['ORDER BY c.settlementDate DESC, c.settlementPeriod DESC LIMIT 48;', '', '', '', ''],
    ['']
]

# ============================================================================
# SECTION 4: DATA COLLECTION METHODS
# ============================================================================
collection_methods = [
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['📡 DATA COLLECTION METHODS & PIPELINES', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['Pipeline', 'Source', 'Method', 'Frequency', 'Scripts', 'Description'],
    ['Historical Batch', 'Elexon BMRS REST API', 'HTTP polling', 'Every 15 min', 'ingest_elexon_fixed.py, auto_ingest_*.py', 'Downloads historical data for 174+ tables. Cron: */15 * * * *. Handles rate limiting, retries, deduplication.'],
    ['Real-Time IRIS', 'Azure Service Bus', 'Message streaming', 'Continuous', 'iris_to_bigquery_unified.py, client.py', 'Deployed on AlmaLinux VPS (94.237.55.234). Subscribes to IRIS topics: FUELINST, INDGEN, FREQ, etc. Pushes to *_iris tables.'],
    ['DNO Lookup', 'postcodes.io API', 'REST API', 'On-demand', 'dno_lookup_python.py', 'Webhook server (Flask port 5001 + ngrok). Postcode → lat/lon → DNO region. MPAN core parsing via mpan_generator_validator.'],
    ['Google Sheets', 'Google Sheets API', 'OAuth2 service account', 'Every 5 min', 'update_live_metrics.py, CacheManager', 'Batch updates via google-cloud-storage. Credentials: inner-cinema-credentials.json. 5 service accounts for parallelization.'],
    [''],
    ['DEPLOYMENT DETAILS', '', '', '', '', ''],
    ['Server', 'AlmaLinux VPS', '94.237.55.234', 'Root access', 'IRIS pipeline', 'systemd services: iris-client.service, iris-uploader.service. Logs: /opt/iris-pipeline/logs/'],
    ['Cron Jobs', 'Local Ubuntu machine', 'crontab -l', 'george user', 'Dashboard updates', '*/5 * * * * update_live_metrics.py, */15 * * * * ingest_elexon_fixed.py'],
    ['Vercel Edge', 'Vercel serverless', 'gb-power-market-jj.vercel.app', 'Production', 'ChatGPT proxy', '/api/proxy-v2 endpoint. SQL validation, rate limiting, BigQuery execution.'],
    ['BigQuery', 'Google Cloud Platform', 'inner-cinema-476211-u9', 'US region', 'Data warehouse', 'Location: US (NOT europe-west2). Free tier: 10GB storage, 1TB queries/month.'],
    ['Credentials', 'Service account JSON', 'inner-cinema-credentials.json', 'OAuth2', 'All scripts', 'Scopes: BigQuery, Sheets. Never commit to git (in .gitignore).'],
    ['']
]

# ============================================================================
# SECTION 5: UPDATE SCHEDULES & MONITORING
# ============================================================================
schedules = [
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    ['⏰ UPDATE SCHEDULES & MONITORING', '', '', '', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', '', '', '', ''],
    [''],
    ['Component', 'Schedule', 'Expected Result', 'Check Command', 'Troubleshooting'],
    ['Live Dashboard v2', 'Every 5 min', 'AA1 timestamp updates', 'Check AA1 cell', 'crontab -l | grep update_live_metrics; tail logs/*.log'],
    ['IRIS Pipeline', 'Continuous', 'New rows in *_iris tables every 5-10 min', 'python3 check_iris_data.py', 'ssh root@94.237.55.234 systemctl status iris-uploader.service'],
    ['Historical Ingest', 'Every 15 min', 'Row counts increase for historical tables', './check_table_coverage.sh bmrs_costs', 'tail logs/ingest*.log; check Elexon API status'],
    ['Wind Forecast', 'Every 15 min', 'publication_dashboard_live updates', 'Check BigQuery table', 'python3 build_publication_table_current.py manually'],
    ['ChatGPT Proxy', 'Real-time', 'API responds to queries', 'curl https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health', 'Check Vercel logs; verify BigQuery permissions'],
    ['BESS DNO Lookup', 'On-demand', 'C6-H6 populates when button clicked', 'Check BESS sheet after manual refresh', 'python3 dno_webhook_server.py; check ngrok tunnel; verify webhook URL in Apps Script'],
    [''],
    ['HEALTH CHECK INDICATORS', '', '', '', ''],
    ['Metric', 'Healthy', 'Warning', 'Critical', 'Action'],
    ['AA1 Timestamp', '<5 min old', '5-10 min old', '>10 min old', 'Restart cron job; check script errors'],
    ['IRIS Data Age', '<10 min', '10-30 min', '>30 min', 'Check AlmaLinux systemd services; verify Azure Service Bus connection'],
    ['BM KPIs (K19-K22)', 'Non-zero values', 'Zeros during active hours', 'All zeros for 4+ hours', 'EBOCF/BOAV lag 2-4 hours; wait or check Elexon API'],
    ['VLP Revenue (O67)', '>£100k (28-day)', '£50k-100k', '<£50k', 'Check bmrs_boalf_complete table coverage; verify price matching logic'],
    ['Sparklines', 'Charts visible', 'Some missing', 'All blank', 'Check Data_Hidden sheet; verify SPARKLINE formulas; run update_live_metrics.py'],
    ['']
]

# ============================================================================
# COMBINE ALL SECTIONS
# ============================================================================
all_data = header + sophistication + tables + python_scripts + collection_methods + schedules

print(f"📝 Writing {len(all_data)} rows to DATA sheet...")

# Write data in batches
batch_size = 100
for i in range(0, len(all_data), batch_size):
    batch = all_data[i:i+batch_size]
    start_row = i + 1
    end_row = start_row + len(batch) - 1
    range_name = f'A{start_row}:K{end_row}'
    worksheet.update(values=batch, range_name=range_name, value_input_option='USER_ENTERED')
    print(f"  ✅ Wrote rows {start_row}-{end_row}")

# Format sheet
print("🎨 Applying formatting...")

# Header rows (1-3)
worksheet.format('A1:K3', {
    'textFormat': {'bold': True, 'fontSize': 14},
    'horizontalAlignment': 'CENTER',
    'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
    'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
})

# Section headers (rows with ═══)
for i, row in enumerate(all_data, start=1):
    if row and len(row[0]) > 0 and '═══' in row[0]:
        worksheet.format(f'A{i}:K{i}', {
            'textFormat': {'bold': True, 'fontSize': 12},
            'backgroundColor': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    elif row and len(row[0]) > 0 and row[0].startswith('📊'):
        worksheet.format(f'A{i}:K{i}', {
            'textFormat': {'bold': True, 'fontSize': 13},
            'backgroundColor': {'red': 0.3, 'green': 0.3, 'blue': 0.9},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })

# Set column widths
column_widths = [
    {'startIndex': 0, 'endIndex': 1, 'pixelSize': 250},   # A - Names
    {'startIndex': 1, 'endIndex': 2, 'pixelSize': 150},   # B - Values
    {'startIndex': 2, 'endIndex': 3, 'pixelSize': 120},   # C - Sizes/Types
    {'startIndex': 3, 'endIndex': 4, 'pixelSize': 150},   # D - Ranges/Dates
    {'startIndex': 4, 'endIndex': 5, 'pixelSize': 120},   # E - Frequencies
    {'startIndex': 5, 'endIndex': 6, 'pixelSize': 120},   # F - Lags
    {'startIndex': 6, 'endIndex': 7, 'pixelSize': 350},   # G - Descriptions
    {'startIndex': 7, 'endIndex': 8, 'pixelSize': 250},   # H - Use cases
    {'startIndex': 8, 'endIndex': 9, 'pixelSize': 150},   # I
    {'startIndex': 9, 'endIndex': 10, 'pixelSize': 150},  # J
    {'startIndex': 10, 'endIndex': 11, 'pixelSize': 150}, # K
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
worksheet.freeze(rows=4, cols=1)

print("✅ DATA sheet created successfully!")
print(f"📊 Total entries: {len(all_data)}")
print(f"🔗 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
