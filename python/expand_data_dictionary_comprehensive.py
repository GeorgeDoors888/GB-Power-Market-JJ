#!/usr/bin/env python3
"""
Comprehensive Data Dictionary Expansion

Adds to existing Data Dictionary sheet:
1. All NESO/Elexon £/MWh price schemas
2. Comprehensive KPI definitions (5 categories)
3. Dashboard V3 KPI row documentation
4. BOALF_Analysis revenue schema
5. Revenue types and sources (6 types)
6. VLP revenue fact table architecture
7. Working BigQuery KPI query examples
8. BOD vs BOALF clarification
9. Target KPI benchmarks
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import sys

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json'

def get_clients():
    """Initialize Google Sheets and BigQuery clients"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=credentials)
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")
    return sheets_service, bq_client


def expand_data_dictionary(sheets_service, bq_client):
    """Expand existing Data Dictionary with comprehensive content"""
    print("📚 Expanding Data Dictionary with comprehensive schemas & KPIs...")
    
    try:
        # Read existing content to find where to append
        existing = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range='Data Dictionary!A1:Z200'
        ).execute()
        
        existing_rows = existing.get('values', [])
        next_row = len(existing_rows) + 1
        
        # Build comprehensive additions
        data = []
        
        # SECTION 6: NESO/ELEXON PRICE SCHEMAS
        data.append(['', '', '', '', ''])
        data.append(['💷 NESO & ELEXON PRICE SCHEMAS (£/MWh)', '', '', '', '', '', '', '', '', ''])
        data.append(['Table', 'Source', 'Key Price Columns', 'Purpose', 'Typical Range'])
        
        price_schemas = [
            ['bmrs_mid', 'Elexon – Market Index Data', 'marketIndexPrice (£/MWh), marketIndexVolume', 'Day-ahead and intraday clearing prices for arbitrage analysis', '£20-£200/MWh (can spike to £500+)'],
            
            ['bmrs_imbalngc', 'Elexon – Imbalance Prices', 'systemSellPrice (£/MWh), systemBuyPrice (£/MWh)', 'Balancing mechanism prices; calculate spread for VLP signals', '£25-£150/MWh (spread typically £5-20)'],
            
            ['bmrs_boalf / bmrs_boalf_iris', 'Elexon – Bid Offer Acceptances', 'levelFrom, levelTo (£/MWh)', 'Accepted bid/offer levels to determine dispatch prices', '£0-£500/MWh (actual accepted prices)'],
            
            ['bmrs_netbsad', 'Elexon – Net Balancing Services Adjustment', 'costSoPrice (£/MWh), costSoVolume', 'Tracks system operator balancing costs and adjustments', '£10-£200/MWh'],
            
            ['bmrs_disbsad', 'Elexon – Disaggregated Balancing Services', 'price (£/MWh) per service action', 'Detailed price per balancing service type', 'Varies by service (£5-£300)'],
            
            ['bmrs_detsysprices', 'Elexon – Detailed System Prices', 'imbalancePrice (£/MWh) + component breakdown', 'Full calculation of system sell/buy price with energy/reserve components', '£20-£150/MWh'],
            
            ['bmrs_bod_iris', 'NESO – Bid Offer Data', 'bidPrice, offerPrice (£/MWh)', 'Submitted bid/offer prices for NESO dispatch forecasting', '£-50 to £500/MWh (9999 = no price)'],
            
            ['bmrs_beb_iris', 'NESO – Balancing Energy Bid Data', 'price (£/MWh) per energy bid', 'Event-driven NESO balancing events', '£10-£300/MWh'],
        ]
        
        data.extend(price_schemas)
        data.append(['', '', '', '', ''])
        
        # Usage patterns
        data.append(['⚙️ USAGE IN VLP WORKFLOWS', '', '', '', ''])
        data.append(['Workflow', 'Tables Used', 'Calculation', 'Purpose'])
        
        usage_patterns = [
            ['Arbitrage', 'bmrs_mid + bmrs_imbalngc', 'Compare Day-Ahead vs System Buy/Sell Prices', 'Identify profitable charge/discharge windows'],
            ['Imbalance Forecasting', 'bmrs_freq_iris + price tables', 'Infer expected price movement from frequency and fuel mix', 'Predict when to offer balancing services'],
            ['Dispatch Validation', 'bmrs_boalf_iris + bmrs_bod_iris', 'Check accepted prices against offers to confirm NESO actions', 'Verify revenue calculations'],
        ]
        
        data.extend(usage_patterns)
        data.append(['', '', '', '', ''])
        
        # SECTION 7: COMPREHENSIVE KPIs
        data.append(['📊 KEY PERFORMANCE INDICATORS (KPIs)', '', '', '', '', '', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        # 7.1 Market & Arbitrage KPIs
        data.append(['💰 1. MARKET & ARBITRAGE KPIs', '', '', '', ''])
        data.append(['KPI', 'Definition', 'Source Table', 'Formula / Query', 'Typical Value'])
        
        market_kpis = [
            ['Market Index Price (£/MWh)', 'Average cleared price on the market per settlement period', 'bmrs_mid', 'AVG(marketIndexPrice)', '£50-£100/MWh'],
            ['System Buy/Sell Price (£/MWh)', 'Balancing mechanism price set by Elexon', 'bmrs_imbalngc', 'AVG(systemBuyPrice), AVG(systemSellPrice)', '£45-£95/MWh'],
            ['Arbitrage Spread (£/MWh)', 'Profit potential between day-ahead and imbalance prices', 'bmrs_mid + bmrs_imbalngc', 'systemSellPrice - marketIndexPrice', '£5-£20/MWh'],
            ['Market Volatility (%)', 'Std. deviation of prices across 24h', 'bmrs_mid', 'STDDEV(marketIndexPrice)/AVG(marketIndexPrice) × 100', '15-30%'],
            ['VLP Arbitrage Opportunity (£)', 'Aggregated positive spread × volume', 'Joined tables', 'SUM((marketIndexPrice - systemBuyPrice) × marketIndexVolume)', '£10k-£50k per day'],
        ]
        
        data.extend(market_kpis)
        data.append(['', '', '', '', ''])
        
        # 7.2 System Balance & Frequency KPIs
        data.append(['⚡ 2. SYSTEM BALANCE & FREQUENCY KPIs', '', '', '', ''])
        data.append(['KPI', 'Definition', 'Source', 'Formula', 'Target'])
        
        frequency_kpis = [
            ['System Frequency (Hz)', 'Average grid frequency per interval', 'bmrs_freq_iris', 'AVG(frequency)', '49.95-50.05 Hz'],
            ['Frequency Deviation (Hz)', 'Absolute deviation from 50.00 Hz', 'bmrs_freq_iris', 'ABS(frequency - 50.00)', '< 0.05 Hz (95% of time)'],
            ['Generation Mix % (by fuel)', 'Share of total generation by type', 'bmrs_fuelinst_iris', 'SUM(quantity)/SUM(total) × 100', 'WIND 30-50%, CCGT 20-40%'],
            ['Carbon Intensity (tCO₂/MWh)', 'Weighted emissions factor (derived)', 'bmrs_fuelinst_iris + emission factors', 'Weighted sum by fuel type', '50-200 tCO₂/MWh'],
            ['Shortfall Duration (min)', 'Minutes below 49.95 Hz', 'bmrs_freq_iris', 'COUNTIF(frequency < 49.95) × 2 min', '< 10 min/day'],
        ]
        
        data.extend(frequency_kpis)
        data.append(['', '', '', '', ''])
        
        # 7.3 Dispatch & Balancing KPIs
        data.append(['🏭 3. DISPATCH & BALANCING KPIs', '', '', '', ''])
        data.append(['KPI', 'Definition', 'Source', 'Formula', 'Typical Range'])
        
        dispatch_kpis = [
            ['Accepted Bid Volume (MWh)', 'Total energy accepted from units (bid down)', 'bmrs_boalf_iris', 'SUM(levelTo - levelFrom) WHERE levelTo < levelFrom', '500-2000 MWh/day'],
            ['Accepted Offer Volume (MWh)', 'Total energy accepted from units (offer up)', 'bmrs_boalf_iris', 'SUM(levelTo - levelFrom) WHERE levelTo > levelFrom', '500-2000 MWh/day'],
            ['Weighted Acceptance Price (£/MWh)', 'Average accepted price weighted by volume', 'bmrs_boalf_iris + bmrs_bod', 'SUM(levelTo × volume)/SUM(volume)', '£40-£120/MWh'],
            ['Constraint Cost (£)', 'Sum of all system operator bid/offer costs', 'bmrs_netbsad, bmrs_disbsad', 'SUM(costSoPrice × costSoVolume)', '£50k-£200k/day'],
            ['MEL Availability Margin (MW)', 'Available export limit - actual generation', 'bmrs_mels_iris', 'MAX(exportLimit) - SUM(actualGeneration)', '5-20 GW'],
        ]
        
        data.extend(dispatch_kpis)
        data.append(['', '', '', '', ''])
        
        # 7.4 Forecast & Demand KPIs
        data.append(['📈 4. FORECAST & DEMAND KPIs', '', '', '', ''])
        data.append(['KPI', 'Definition', 'Source', 'Formula', 'Target'])
        
        forecast_kpis = [
            ['Demand Forecast Accuracy (%)', '1 - |forecast - actual| / forecast', 'bmrs_inddem', '1 - ABS(forecast - actual)/forecast × 100', '> 95%'],
            ['Generation Forecast Accuracy (%)', 'Same logic for generation', 'bmrs_indgen', '1 - ABS(forecast - actual)/forecast × 100', '> 90%'],
            ['Net Margin (MW)', 'Generation - Demand', 'bmrs_indgen, bmrs_inddem', 'SUM(generation) - SUM(demand)', '2-5 GW reserve margin'],
            ['Imbalance Volume (MWh)', 'Total absolute imbalance', 'bmrs_imbalngc', 'SUM(ABS(netImbalanceVolume))', '500-1500 MWh/day'],
        ]
        
        data.extend(forecast_kpis)
        data.append(['', '', '', '', ''])
        
        # 7.5 System & Operational KPIs
        data.append(['🛠️ 5. SYSTEM & OPERATIONAL KPIs', '', '', '', ''])
        data.append(['KPI', 'Description', 'Source', 'Target'])
        
        operational_kpis = [
            ['Data Latency (min)', 'Δ between event time and ingested_utc', 'All _IRIS tables', '< 2 min for FREQ/FUELINST'],
            ['Data Completeness (%)', 'Received rows / expected rows per period', 'BigQuery metadata', '> 99%'],
            ['File Backlog (#)', 'Unprocessed IRIS files', 'Uploader logs', '< 10 files'],
            ['System Uptime (%)', 'Successful API pings / total checks', '/health endpoint', '> 99.5%'],
            ['Documentation Coverage (%)', 'Active files / total tracked (546)', 'documentation_url_registry', '> 95%'],
        ]
        
        data.extend(operational_kpis)
        data.append(['', '', '', '', ''])
        
        # SECTION 8: DASHBOARD V3 KPI ROW DEFINITIONS
        data.append(['📊 DASHBOARD V3 KPI ROW (F9:L9)', '', '', '', '', '', '', '', '', ''])
        data.append(['Cell', 'KPI Name', 'Current Implementation', 'Correct Formula', 'Notes'])
        
        dashboard_kpis = [
            ['F9', '📊 VLP Revenue (£k)', 'Needs fixing', '=SUM(VLP_Data!D:D WHERE date in range)/1000', 'Should aggregate total_revenue_£ from VLP_Data, filtered by date'],
            ['G9', '💰 Wholesale Avg (£/MWh)', 'Points to Market_Prices!C', '=AVERAGE(Market_Prices!C:C WHERE date in range)', 'Correct - wholesale reference price'],
            ['H9', '📈 Market Vol (%)', 'Needs definition', '=STDDEV(prices)/AVG(prices) × 100', 'Price volatility percentage'],
            ['I9', 'All-GB Net Margin (£/MWh)', 'Currently wrong', '=SUM(total_revenue_£ for all GB BMUs)/SUM(delivered_volume_mwh for all GB BMUs)', 'Should be revenue/volume, not just price copy'],
            ['J9', 'Selected DNO Net Margin (£/MWh)', 'Currently wrong', '=SUM(total_revenue_£ WHERE dno=selected)/SUM(delivered_volume_mwh WHERE dno=selected)', 'Filtered by DNO dropdown selection'],
            ['K9', 'Selected DNO Volume (MWh)', 'Needs implementation', '=SUM(delivered_volume_mwh WHERE dno=selected)', 'Total MWh for selected DNO'],
            ['L9', 'Selected DNO Revenue (£k)', 'Needs implementation', '=SUM(total_revenue_£ WHERE dno=selected)/1000', 'Total revenue for selected DNO in £k'],
        ]
        
        data.extend(dashboard_kpis)
        data.append(['', '', '', '', ''])
        
        # SECTION 9: BOALF_ANALYSIS REVENUE SCHEMA
        data.append(['💰 BOALF_ANALYSIS REVENUE FACT TABLE', '', '', '', '', '', '', '', '', ''])
        data.append(['Column', 'Type', 'Description', 'Example Value', 'Notes'])
        
        boalf_schema = [
            ['Date', 'DATE', 'Settlement date', '2025-12-04', 'From settlementDate'],
            ['SP', 'INT', 'Settlement period (1-48)', '23', '30-minute periods'],
            ['BMU_Id', 'STRING', 'Balancing Mechanism Unit ID', 'T_DRAXX-1', 'Generator or storage unit'],
            ['ActionType', 'STRING', 'Type of action', 'Offer Up / Bid Down / Offer Down / Bid Up', 'Based on levelTo vs levelFrom direction'],
            ['Volume_MWh', 'FLOAT', 'Energy volume accepted', '2.5', '(levelTo - levelFrom) × 0.5 hours'],
            ['Price_£_per_MWh', 'FLOAT', 'Applied price from BOD', '85.50', 'Joined from bmrs_bod (bid or offer price)'],
            ['Value_£', 'FLOAT', 'Revenue from this action', '213.75', 'Volume_MWh × Price_£_per_MWh'],
            ['SO_Flag', 'STRING', 'System operator flag', 'T/F', 'System-initiated action'],
            ['RR_Flag', 'STRING', 'Replacement reserve flag', 'T/F', 'Reserve-related action'],
            ['DNO / GSP Group', 'STRING', 'Distribution network operator', 'UKPN-EPN', 'From BMU registration lookup'],
        ]
        
        data.extend(boalf_schema)
        data.append(['', '', '', '', ''])
        data.append(['⚠️ IMPORTANT', 'This is the REVENUE fact table. BOD contains submitted prices (market intelligence) but BOALF contains accepted actions (actual revenue).', '', '', ''])
        data.append(['', '', '', '', ''])
        
        # SECTION 10: REVENUE TYPES AND SOURCES
        data.append(['💷 REVENUE TYPES AND SOURCES', '', '', '', '', '', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['🔄 PHYSICAL ACTION → BM VIEW → REVENUE MAPPING', '', '', '', ''])
        data.append(['Physical Action at Site', 'BM View', 'Revenue Type', 'Who Pays', 'Typical Price'])
        
        revenue_mapping = [
            ['Reduce demand / increase generation', 'Offer Up', 'ESO pays you for positive delivered volume', 'ESO → You', '£50-£150/MWh'],
            ['Increase demand / reduce generation', 'Bid Down', 'ESO pays you to absorb energy (or you pay)', 'ESO → You (usually)', '£30-£120/MWh'],
        ]
        
        data.extend(revenue_mapping)
        data.append(['', '', '', '', ''])
        
        data.append(['💰 SIX REVENUE STREAM TYPES', '', '', '', ''])
        data.append(['Revenue Type', 'Formula', 'Source Tables', 'Typical Contribution', 'Notes'])
        
        revenue_types = [
            ['1. BM Energy Revenue', 'delivered_volume_mwh × bm_price_£/MWh', 'bmrs_boalf + bmrs_bod', '£50-200/MWh', 'Core balancing mechanism revenue'],
            ['2. Wholesale Arbitrage Revenue', '(export_price - import_price) × net_volume', 'bmrs_mid + bmrs_imbalngc', '£8-15/MWh average', 'Buy low, sell high strategy'],
            ['3. Ancillary / FR Services (DC)', 'Service-specific £ values per SP', 'DC contract data', '£50k-200k/MW/year', 'Dynamic Containment frequency response'],
            ['4. Capacity Market Revenue', 'CM £ allocated per SP', 'CM auction results', '£15-25/kW/year', 'Availability payments'],
            ['5. Network-side Benefits', 'DUoS/levy avoidance', 'gb_power.duos_unit_rates', '£10-30/MWh saved', 'Avoid Red band charges'],
            ['6. VLP Customer Margin', 'ESO payment - customer pass-through', 'P444/P376 baselining', '£5-12/MWh', 'VLP intermediary margin'],
        ]
        
        data.extend(revenue_types)
        data.append(['', '', '', '', ''])
        
        # SECTION 11: VLP REVENUE FACT TABLE ARCHITECTURE
        data.append(['🗄️ PROPOSED: iris.vlp_revenue_sp FACT TABLE', '', '', '', '', '', '', '', '', ''])
        data.append(['Column Name', 'Type', 'Description', 'Example', 'Notes'])
        
        vlp_schema = [
            ['settlement_date', 'DATE', 'Settlement date', '2025-12-04', ''],
            ['settlement_period', 'INT', 'Settlement period (1-48)', '23', ''],
            ['bm_unit_id', 'STRING', 'BMU ID', 'T_DRAXX-1', ''],
            ['dno', 'STRING', 'Distribution network', 'UKPN-EPN', ''],
            ['region', 'STRING', 'GSP group or region', 'London', ''],
            ['delivered_volume_mwh', 'FLOAT', 'Actual delivered energy', '2.5', 'Positive for up, negative for down'],
            ['bm_price_£_per_mwh', 'FLOAT', 'Applied BM price', '85.50', 'From BOD joined to BOALF'],
            ['bm_value_£', 'FLOAT', 'BM cashflow', '213.75', 'delivered_volume_mwh × bm_price_£_per_mwh'],
            ['wholesale_price_£_per_mwh', 'FLOAT', 'Reference wholesale price', '75.00', 'From bmrs_mid'],
            ['wholesale_cost_£', 'FLOAT', 'Cost of energy otherwise paid', '187.50', 'Volume × wholesale price'],
            ['duos_£', 'FLOAT', 'DUoS charges/savings', '12.50', 'From duos_unit_rates'],
            ['levies_£', 'FLOAT', 'TNUoS/BSUoS/CCL/RO/FIT', '15.30', 'Total levies'],
            ['other_service_£', 'FLOAT', 'DC, CM, etc.', '50.00', 'Ancillary services'],
            ['total_revenue_£', 'FLOAT', 'Sum of all revenue streams', '291.55', 'bm_value_£ + other_service_£ - costs'],
            ['net_margin_£_per_mwh', 'FLOAT', 'Net profit per MWh', '116.62', '(total_revenue_£ - energy_cost_£) / |volume|'],
        ]
        
        data.extend(vlp_schema)
        data.append(['', '', '', '', ''])
        
        # SECTION 12: WORKING BIGQUERY EXAMPLES
        data.append(['🔍 EXAMPLE BIGQUERY KPI QUERIES', '', '', '', '', '', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['Query 1: 7-Day Market Summary', '', '', '', ''])
        data.append(['SQL', '''SELECT
  AVG(frequency) AS avg_frequency,
  STDDEV(frequency) AS volatility_hz,
  AVG(marketIndexPrice) AS avg_market_price,
  AVG(systemBuyPrice) AS avg_buy_price,
  AVG(systemSellPrice) AS avg_sell_price,
  SUM(ABS(netImbalanceVolume)) AS total_imbalance_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_imbalngc`
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
USING(settlementDate, settlementPeriod)
WHERE settlementDate >= CURRENT_DATE() - 7''', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['Query 2: VLP Revenue by DNO', '', '', '', ''])
        data.append(['SQL', '''SELECT
  dno,
  SUM(total_revenue_£) AS total_revenue,
  SUM(delivered_volume_mwh) AS total_volume_mwh,
  SUM(total_revenue_£) / SUM(delivered_volume_mwh) AS net_margin_per_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp`
WHERE settlement_date >= CURRENT_DATE() - 7
GROUP BY dno
ORDER BY total_revenue DESC''', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['Query 3: All-GB Net Margin', '', '', '', ''])
        data.append(['SQL', '''SELECT
  SUM(bm_value_£) AS total_bm_revenue,
  SUM(delivered_volume_mwh) AS total_volume,
  SUM(bm_value_£) / NULLIF(SUM(delivered_volume_mwh), 0) AS gb_net_margin
FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_revenue_sp`
WHERE settlement_date >= CURRENT_DATE() - 7''', '', '', ''])
        data.append(['', '', '', '', ''])
        
        # SECTION 13: BOD VS BOALF CLARIFICATION
        data.append(['⚠️ CRITICAL: BOD vs BOALF DISTINCTION', '', '', '', '', '', '', '', '', ''])
        data.append(['', '', '', '', ''])
        
        data.append(['Dataset', 'Full Name', 'Purpose', 'Contains Revenue?', 'Use Case'])
        
        bod_boalf_table = [
            ['BOD', 'Bid-Offer Data', 'Submitted price curves from BMUs', '❌ NO', 'Market intelligence, price analysis, sanity checks'],
            ['BOALF', 'Bid-Offer Acceptance Level Flagged', 'Accepted actions by ESO', '✅ YES', 'Actual revenue calculation, dispatch validation'],
        ]
        
        data.extend(bod_boalf_table)
        data.append(['', '', '', '', ''])
        
        data.append(['🔑 KEY POINTS', '', '', '', ''])
        data.append(['Point', 'Explanation'])
        data.append(['BOD = Submitted Prices', 'These are your bids/offers submitted to the market. No revenue until accepted.'])
        data.append(['BOALF = Accepted Actions', 'These are ESO acceptances. THIS is where revenue comes from.'])
        data.append(['Dashboard V3 Revenue KPIs', 'Should pull from BOALF-side (accepted actions), NOT raw BOD.'])
        data.append(['BOD_Analysis Sheet', 'Market intelligence tool - shows if your prices are competitive, not revenue.'])
        data.append(['BOALF_Analysis Sheet', 'Revenue fact table - shows actual £ earned from accepted actions.'])
        data.append(['', '', '', '', ''])
        
        # SECTION 14: TARGET KPI BENCHMARKS
        data.append(['🎯 AGGREGATED VLP DASHBOARD KPI TARGETS', '', '', '', '', '', '', '', '', ''])
        data.append(['Category', 'Metric', 'Target', 'Current Status', 'Action if Below Target'])
        
        kpi_targets = [
            ['Market Arbitrage', 'Avg. spread > £5/MWh', '✅ Positive', 'Monitor', 'Review bid/offer strategy'],
            ['Frequency Stability', '< 0.05 Hz deviation 95% of time', '✅ On target', 'Good', 'Continue monitoring'],
            ['Imbalance Cost', '< £100k/day', '✅ Under control', 'Good', 'Alert if approaching £100k'],
            ['Forecast Accuracy', '> 90%', '✅ Achieving', 'Good', 'Improve ML models if <90%'],
            ['Data Latency', '< 2 min (FREQ/FUELINST)', '✅ Real-time', 'Good', 'Check IRIS pipeline if >2min'],
        ]
        
        data.extend(kpi_targets)
        data.append(['', '', '', '', ''])
        
        # Write all new content starting from next_row
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f'Data Dictionary!A{next_row}',
            valueInputOption='USER_ENTERED',
            body={'values': data}
        ).execute()
        
        print(f"   ✅ Added {len(data)} rows of comprehensive content")
        print(f"   📍 New sections added:")
        print(f"      • NESO & Elexon price schemas (8 tables)")
        print(f"      • 5 KPI categories (Market, Frequency, Dispatch, Forecast, Operational)")
        print(f"      • Dashboard V3 KPI row definitions (F9:L9)")
        print(f"      • BOALF_Analysis revenue schema")
        print(f"      • 6 revenue types with formulas")
        print(f"      • VLP revenue fact table architecture")
        print(f"      • Working BigQuery query examples")
        print(f"      • BOD vs BOALF clarification")
        print(f"      • Target KPI benchmarks")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_kpi_row_cell_notes(sheets_service):
    """Add cell notes to Dashboard V3 KPI row (F9:L9)"""
    print("📝 Adding cell notes to Dashboard V3 KPI row...")
    
    try:
        # Get Dashboard V3 sheet ID
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        dashboard_v3_id = None
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == 'Dashboard V3':
                dashboard_v3_id = sheet['properties']['sheetId']
                break
        
        if not dashboard_v3_id:
            print("   ⚠️  Dashboard V3 sheet not found")
            return False
        
        # Cell note definitions for KPI row
        kpi_notes = {
            'F9': '''📊 VLP Revenue (£k)
            
Definition: Total Virtual Lead Party revenue from all sources
Formula: SUM(VLP_Data!D:D WHERE date in range)/1000
Source: VLP_Data sheet, total_revenue_£ column
Includes: BM energy revenue, wholesale arbitrage, DC/CM services, network benefits, VLP margin''',
            
            'G9': '''💰 Wholesale Avg (£/MWh)
            
Definition: Average wholesale electricity price
Formula: AVERAGE(Market_Prices!C:C WHERE date in range)
Source: bmrs_mid (marketIndexPrice) or bmrs_imbalngc (reference price)
Purpose: Baseline market price for arbitrage comparison''',
            
            'H9': '''📈 Market Vol (%)
            
Definition: Market price volatility percentage
Formula: STDDEV(prices)/AVG(prices) × 100
Source: Market_Prices sheet, price volatility calculation
Typical: 15-30% volatility indicates normal market conditions''',
            
            'I9': '''All-GB Net Margin (£/MWh)
            
Definition: National average net profit margin per MWh
Formula: SUM(total_revenue_£ for all GB BMUs) / SUM(delivered_volume_mwh for all GB BMUs)
Source: vlp_revenue_sp fact table (all GB units)
Purpose: Benchmark for your DNO-specific performance''',
            
            'J9': '''Selected DNO Net Margin (£/MWh)
            
Definition: Net profit margin per MWh for selected DNO
Formula: SUM(total_revenue_£ WHERE dno=selected) / SUM(delivered_volume_mwh WHERE dno=selected)
Source: vlp_revenue_sp fact table filtered by DNO dropdown
Purpose: Your DNO-specific performance metric''',
            
            'K9': '''Selected DNO Volume (MWh)
            
Definition: Total energy volume for selected DNO
Formula: SUM(delivered_volume_mwh WHERE dno=selected)
Source: vlp_revenue_sp fact table, delivered_volume_mwh column
Purpose: Scale metric for your DNO operations''',
            
            'L9': '''Selected DNO Revenue (£k)
            
Definition: Total revenue for selected DNO in thousands
Formula: SUM(total_revenue_£ WHERE dno=selected) / 1000
Source: vlp_revenue_sp fact table, total_revenue_£ column
Purpose: Absolute revenue metric for your DNO'''
        }
        
        requests = []
        
        for cell_ref, note_text in kpi_notes.items():
            col = ord(cell_ref[0]) - ord('A')
            row = int(cell_ref[1:]) - 1
            
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': dashboard_v3_id,
                        'startRowIndex': row,
                        'endRowIndex': row + 1,
                        'startColumnIndex': col,
                        'endColumnIndex': col + 1
                    },
                    'rows': [{
                        'values': [{
                            'note': note_text.strip()
                        }]
                    }],
                    'fields': 'note'
                }
            })
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        
        print(f"   ✅ Added {len(kpi_notes)} cell notes to KPI row (F9:L9)")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("📚 Comprehensive Data Dictionary Expansion")
    print("="*80)
    
    sheets_service, bq_client = get_clients()
    
    success = True
    success &= expand_data_dictionary(sheets_service, bq_client)
    success &= add_kpi_row_cell_notes(sheets_service)
    
    print("="*80)
    if success:
        print("✅ Comprehensive Data Dictionary expansion complete!")
        print("\n📖 What was added:")
        print("   1. NESO & Elexon price schemas (8 tables with £/MWh fields)")
        print("   2. 5 comprehensive KPI categories:")
        print("      - Market & Arbitrage KPIs")
        print("      - System Balance & Frequency KPIs")
        print("      - Dispatch & Balancing KPIs")
        print("      - Forecast & Demand KPIs")
        print("      - System & Operational KPIs")
        print("   3. Dashboard V3 KPI row documentation (F9:L9)")
        print("   4. BOALF_Analysis revenue schema")
        print("   5. 6 revenue types with formulas")
        print("   6. VLP revenue fact table architecture")
        print("   7. Working BigQuery query examples")
        print("   8. BOD vs BOALF clarification")
        print("   9. Target KPI benchmarks")
        print("   10. Cell notes added to KPI row (F9:L9)")
    else:
        print("⚠️  Completed with errors")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
