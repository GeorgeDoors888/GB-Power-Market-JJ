#!/usr/bin/env python3
"""
PPA 24-Month Analysis with Rate Limiting & Caching
Updates BESS sheet rows 44-45 with comprehensive PPA profitability data
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from gspread.exceptions import APIError
import time
import json
import os
from datetime import datetime

# Configuration
CREDENTIALS_FILE = '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json'
MAIN_DASHBOARD_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CACHE_FILE = '/tmp/ppa_analysis_cache.json'
CACHE_DURATION = 3600  # 1 hour

# PPA Configuration
PPA_PRICE = 150.0  # £/MWh
DUOS_RED = 17.64
DUOS_AMBER = 2.05
DUOS_GREEN = 0.11
FIXED_COSTS = 98.15  # TNUoS + BSUoS + CCL + RO + FiT

print("=" * 80)
print("PPA 24-MONTH ANALYSIS WITH RATE LIMITING")
print("=" * 80)

# ============================================================================
# SOLUTION 1: EXPONENTIAL BACKOFF
# ============================================================================

def with_retry(func, retries=5):
    """Retry function with exponential backoff on rate limit errors"""
    for i in range(retries):
        try:
            return func()
        except APIError as e:
            if '429' in str(e):
                wait_time = 2 ** i
                print(f"⏰ Rate limited. Waiting {wait_time}s before retry {i+1}/{retries}...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")

# ============================================================================
# SOLUTION 2: BATCH OPERATIONS
# ============================================================================

def batch_read_sheet(sheet, ranges):
    """Read multiple ranges in a single API call"""
    def _read():
        return sheet.batch_get(ranges)
    return with_retry(_read)

def batch_write_sheet(sheet, data_dict):
    """Write multiple ranges in a single API call"""
    def _write():
        # Convert dict to list of dicts for batch_update
        data = [{'range': k, 'values': v} for k, v in data_dict.items()]
        return sheet.batch_update(data)
    return with_retry(_write)

# ============================================================================
# SOLUTION 3: CACHING
# ============================================================================

def load_cache():
    """Load cached analysis results"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                cache_age = time.time() - cache.get('timestamp', 0)
                if cache_age < CACHE_DURATION:
                    print(f"✅ Using cached data ({cache_age/60:.1f} minutes old)")
                    return cache.get('data')
        except:
            pass
    return None

def save_cache(data):
    """Save analysis results to cache"""
    cache = {
        'timestamp': time.time(),
        'data': data
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    print(f"💾 Cached analysis results")

# ============================================================================
# BIGQUERY ANALYSIS
# ============================================================================

def run_24_month_analysis():
    """Run comprehensive 24-month PPA profitability analysis"""
    
    # Check cache first
    cached = load_cache()
    if cached:
        return cached
    
    print("\n🔍 Running fresh 24-month analysis...")
    
    client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)
    
    # Query 24 months of data with profitability calculations
    query = """
    WITH period_data AS (
      SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        MAX(systemBuyPrice) as system_buy_price
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
      WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
        AND systemBuyPrice IS NOT NULL
      GROUP BY date, settlementPeriod
    ),
    profitable AS (
      SELECT 
        *,
        CASE 
          WHEN settlementPeriod BETWEEN 33 AND 39 THEN 17.64
          WHEN settlementPeriod BETWEEN 17 AND 32 OR settlementPeriod BETWEEN 40 AND 44 THEN 2.05
          ELSE 0.11
        END as duos,
        150.0 - (system_buy_price + 98.15 + 
          CASE 
            WHEN settlementPeriod BETWEEN 33 AND 39 THEN 17.64
            WHEN settlementPeriod BETWEEN 17 AND 32 OR settlementPeriod BETWEEN 40 AND 44 THEN 2.05
            ELSE 0.11
          END) as profit
      FROM period_data
    )
    SELECT 
      COUNT(*) as total_periods,
      COUNTIF(profit > 0) as profitable_periods,
      SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) as total_profit,
      AVG(CASE WHEN profit > 0 THEN profit ELSE NULL END) as avg_profit,
      MAX(profit) as max_profit,
      MIN(profit) as min_profit,
      COUNT(DISTINCT date) as total_days,
      AVG(system_buy_price) as avg_system_buy,
      MIN(system_buy_price) as min_system_buy,
      MAX(system_buy_price) as max_system_buy
    FROM profitable
    """
    
    results = client.query(query).result()
    
    for row in results:
        # Calculate metrics
        profitable_pct = (row.profitable_periods / row.total_periods) * 100
        total_revenue_ppa = row.profitable_periods * PPA_PRICE
        profit_per_day = row.total_profit / row.total_days if row.total_days > 0 else 0
        annual_profit = row.total_profit / 2  # 24 months = 2 years
        
        analysis = {
            'total_periods': row.total_periods,
            'profitable_periods': row.profitable_periods,
            'profitable_pct': profitable_pct,
            'total_days': row.total_days,
            'total_revenue_ppa': total_revenue_ppa,
            'total_profit': row.total_profit,
            'profit_per_day': profit_per_day,
            'avg_profit': row.avg_profit,
            'max_profit': row.max_profit,
            'min_profit': row.min_profit,
            'annual_profit': annual_profit,
            'avg_system_buy': row.avg_system_buy,
            'min_system_buy': row.min_system_buy,
            'max_system_buy': row.max_system_buy,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to cache
        save_cache(analysis)
        
        return analysis
    
    return None

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    # Run analysis
    analysis = run_24_month_analysis()
    
    if not analysis:
        print("❌ No data returned from analysis")
        return
    
    print("\n" + "=" * 80)
    print("24-MONTH ANALYSIS RESULTS")
    print("=" * 80)
    print(f"\nTotal Periods Analyzed: {analysis['total_periods']:,}")
    print(f"Profitable Periods: {analysis['profitable_periods']:,} ({analysis['profitable_pct']:.1f}%)")
    print(f"Total Days: {analysis['total_days']}")
    print(f"\n💰 REVENUE & PROFIT:")
    print(f"   Total Revenue PPA: £{analysis['total_revenue_ppa']:,.2f}")
    print(f"   Total Profit PPA: £{analysis['total_profit']:,.2f}")
    print(f"   Total Profit PPA/day: £{analysis['profit_per_day']:.2f}")
    print(f"\n   Average Profit (when profitable): £{analysis['avg_profit']:.2f}/MWh")
    print(f"   Best Period Profit: £{analysis['max_profit']:.2f}/MWh")
    print(f"   Worst Period Loss: £{analysis['min_profit']:.2f}/MWh")
    print(f"   Expected Annual Profit: £{analysis['annual_profit']:,.2f}")
    print(f"\n📊 MARKET PRICES:")
    print(f"   Average System Buy: £{analysis['avg_system_buy']:.2f}/MWh")
    print(f"   Range: £{analysis['min_system_buy']:.2f} - £{analysis['max_system_buy']:.2f}/MWh")
    
    # Connect to Google Sheets with rate limiting
    print("\n" + "=" * 80)
    print("UPDATING GOOGLE SHEETS")
    print("=" * 80)
    
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    
    # Open workbook and sheet with retry
    def _open_sheet():
        wb = gc.open_by_key(MAIN_DASHBOARD_ID)
        return wb.worksheet('BESS')
    
    bess_sheet = with_retry(_open_sheet)
    
    # Prepare data for batch update (SOLUTION 2: BATCH OPERATIONS)
    update_data = {
        'A44:C44': [['Total Revenue PPA', 'Total Profit PPA B', 'Total Profit PPA B/day']],
        'A45:C45': [[
            f"£{analysis['total_revenue_ppa']:,.2f}",
            f"£{analysis['total_profit']:,.2f}",
            f"£{analysis['profit_per_day']:.2f}"
        ]]
    }
    
    # Batch write to sheet
    print("\n📝 Writing to BESS sheet (batch operation)...")
    batch_write_sheet(bess_sheet, update_data)
    
    print("\n✅ Update complete!")
    
    # Verify with batch read (SOLUTION 2: BATCH OPERATIONS)
    print("\n🔍 Verifying update...")
    result = batch_read_sheet(bess_sheet, ['A44:C45'])
    
    if result and result[0]:
        print(f"\n📊 VERIFIED - Sheet now contains:")
        print(f"   Row 44: {result[0][0]}")
        print(f"   Row 45: {result[0][1] if len(result[0]) > 1 else 'empty'}")
    
    print("\n" + "=" * 80)
    print("✅ ALL DONE - Rate Limiting Solutions Applied:")
    print("=" * 80)
    print("1️⃣  Exponential Backoff: Auto-retry with delays on rate limits")
    print("2️⃣  Batch Operations: Single API call for multiple ranges")
    print("3️⃣  Caching: 1-hour cache to avoid redundant BigQuery queries")
    print(f"\n💾 Cache location: {CACHE_FILE}")
    print(f"🔄 Cache expires: {CACHE_DURATION/60:.0f} minutes after creation")

if __name__ == '__main__':
    main()
