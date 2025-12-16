#!/usr/bin/env python3
"""
BM Accepted Offers Analysis - 24 Months (Using BOD Data)
=========================================================
Analyzes Balancing Mechanism bid-offer DATA over last 24 months.

REALITY CHECK:
- bmrs_boalf/bmrs_boalf_iris: Only has acceptanceNumber/Time (NO price/volume in YOUR BigQuery)
- bmrs_bod/bmrs_bod_iris: Has offer/bid PRICES and pair data
- bmrs_disbsad: Has ACCEPTED action costs and volumes (disaggregated settlement data)

This script uses bmrs_bod which contains:
- offer: Offer price (£/MWh)
- bid: Bid price (£/MWh)  
- bmUnit: BM Unit ID
- settlementDate, settlementPeriod
- pairId: Bid-offer pair identifier

Note: bmrs_bod is BID-OFFER SUBMISSIONS, not necessarily accepted actions.
For ACTUAL acceptances, use bmrs_disbsad (settlement data).

Metrics per month:
- Min/Average/Max offer prices (£/MWh)
- Min/Average/Max bid prices (£/MWh)
- Pair counts and unique BM units

Output: Google Sheets report with 24-month statistics
"""

import sys
from datetime import datetime, date, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import gspread

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
WORKSHEET_NAME = "BM Bid-Offer Data - 24M"
CREDENTIALS_FILE = "/home/george/inner-cinema-credentials.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def analyze_bod_24months():
    """
    Analyze BM bid-offer DATA (bmrs_bod) for last 24 months.
    Returns monthly aggregates with min/avg/max prices for offers and bids.
    """
    
    print("=" * 80)
    print("📊 BM BID-OFFER DATA ANALYSIS - LAST 24 MONTHS")
    print("=" * 80)
    
    # Calculate date range (last 24 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # ~24 months
    
    print(f"\n📅 Date Range: {start_date} to {end_date}")
    print(f"   (24 months of data)")
    print(f"\n📋 Data Source: bmrs_bod + bmrs_bod_iris (Bid-Offer Data)")
    print(f"   ✅ Contains: offer (£/MWh), bid (£/MWh), bmUnit, pairId")
    print(f"   ⚠️  This is SUBMISSION data, not acceptance data")
    print(f"   💡 For accepted actions, see bmrs_disbsad table instead")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Comprehensive monthly analysis query
    query = f"""
    WITH combined_bod AS (
        -- Historical bid-offer data
        SELECT 
            settlementDate,
            settlementPeriod,
            bmUnit,
            pairId,
            offer,
            bid
        FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
        WHERE DATE(settlementDate) >= '{start_date}'
          AND DATE(settlementDate) < '2025-10-28'  -- Historical cutoff
        
        UNION ALL
        
        -- Real-time bid-offer data (IRIS)
        SELECT 
            settlementDate,
            settlementPeriod,
            bmUnit,
            pairId,
            offer,
            bid
        FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
        WHERE DATE(settlementDate) >= '2025-10-28'  -- IRIS starts here
          AND DATE(settlementDate) <= '{end_date}'
    ),
    
    monthly_stats AS (
        SELECT
            FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
            
            -- Offer price statistics (£/MWh)
            MIN(offer) as min_offer_price,
            AVG(offer) as avg_offer_price,
            MAX(offer) as max_offer_price,
            APPROX_QUANTILES(offer, 100)[OFFSET(50)] as median_offer_price,
            
            -- Bid price statistics (£/MWh) - use absolute values
            MIN(ABS(bid)) as min_bid_price,
            AVG(ABS(bid)) as avg_bid_price,
            MAX(ABS(bid)) as max_bid_price,
            APPROX_QUANTILES(ABS(bid), 100)[OFFSET(50)] as median_bid_price,
            
            -- Spread statistics (offer - bid)
            AVG(offer - bid) as avg_spread,
            
            -- Pair counts
            COUNT(DISTINCT pairId) as unique_pairs,
            COUNT(DISTINCT bmUnit) as unique_units,
            COUNT(*) as total_records,
            
            -- Records by type
            COUNT(CASE WHEN offer > 0 THEN 1 END) as offer_records,
            COUNT(CASE WHEN bid < 0 THEN 1 END) as bid_records
            
        FROM combined_bod
        WHERE offer IS NOT NULL OR bid IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
    ),
    
    overall_avg AS (
        -- Calculate 24-month averages
        SELECT 
            'OVERALL 24M AVG' as month,
            AVG(avg_offer_price) as min_offer_price,
            AVG(avg_offer_price) as avg_offer_price,
            MAX(max_offer_price) as max_offer_price,
            AVG(median_offer_price) as median_offer_price,
            AVG(avg_bid_price) as min_bid_price,
            AVG(avg_bid_price) as avg_bid_price,
            MAX(max_bid_price) as max_bid_price,
            AVG(median_bid_price) as median_bid_price,
            AVG(avg_spread) as avg_spread,
            AVG(unique_pairs) as unique_pairs,
            AVG(unique_units) as unique_units,
            SUM(total_records) / 24 as total_records,
            SUM(offer_records) / 24 as offer_records,
            SUM(bid_records) / 24 as bid_records
        FROM monthly_stats
    )
    
    SELECT * FROM monthly_stats
    UNION ALL
    SELECT * FROM overall_avg
    ORDER BY 
        CASE WHEN month = 'OVERALL 24M AVG' THEN 1 ELSE 0 END,
        month DESC
    """
    
    print("\n⏳ Querying BigQuery...")
    print(f"   Combining bmrs_bod (historical) + bmrs_bod_iris (real-time)")
    
    try:
        df = client.query(query).to_dataframe()
        
        if df.empty:
            print("\n⚠️  No bid-offer data found for the specified period")
            return None
        
        print(f"\n✅ Retrieved {len(df)} monthly records")
        
        return df
        
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        return None


def print_summary(df):
    """Print summary statistics to console."""
    
    if df is None or df.empty:
        return
    
    print("\n" + "=" * 80)
    print("📈 SUMMARY STATISTICS")
    print("=" * 80)
    
    # Get overall average row
    overall = df[df['month'] == 'OVERALL 24M AVG']
    
    if not overall.empty:
        row = overall.iloc[0]
        
        print(f"\n💰 AVERAGE OFFER PRICES (24 months):")
        print(f"   Min:     £{row['min_offer_price']:,.2f}/MWh")
        print(f"   Average: £{row['avg_offer_price']:,.2f}/MWh")
        print(f"   Median:  £{row['median_offer_price']:,.2f}/MWh")
        print(f"   Max:     £{row['max_offer_price']:,.2f}/MWh")
        
        print(f"\n💰 AVERAGE BID PRICES (24 months):")
        print(f"   Min:     £{row['min_bid_price']:,.2f}/MWh")
        print(f"   Average: £{row['avg_bid_price']:,.2f}/MWh")
        print(f"   Median:  £{row['median_bid_price']:,.2f}/MWh")
        print(f"   Max:     £{row['max_bid_price']:,.2f}/MWh")
        
        print(f"\n📊 MARKET ACTIVITY (monthly averages):")
        print(f"   Bid-Offer Pairs: {row['unique_pairs']:,.0f}")
        print(f"   Unique Units:    {row['unique_units']:,.0f}")
        print(f"   Total Records:   {row['total_records']:,.0f}")
        print(f"   Offer Records:   {row['offer_records']:,.0f}")
        print(f"   Bid Records:     {row['bid_records']:,.0f}")
        print(f"   Avg Spread:      £{row['avg_spread']:,.2f}/MWh")
    
    # Top 5 months by offer price
    monthly = df[df['month'] != 'OVERALL 24M AVG'].copy()
    if not monthly.empty:
        print("\n" + "=" * 80)
        print("📊 TOP 5 MONTHS BY AVERAGE OFFER PRICE")
        print("=" * 80)
        
        top5 = monthly.nlargest(5, 'avg_offer_price')
        for _, row in top5.iterrows():
            print(f"\n{row['month']}:")
            print(f"   Avg Offer: £{row['avg_offer_price']:,.2f}/MWh")
            print(f"   Max Offer: £{row['max_offer_price']:,.2f}/MWh")
            print(f"   Pairs:     {row['unique_pairs']:,.0f}")


def update_google_sheet(df):
    """Update Google Sheets with analysis results."""
    
    if df is None or df.empty:
        print("\n⚠️  No data to write to Google Sheets")
        return
    
    print("\n" + "=" * 80)
    print("📝 UPDATING GOOGLE SHEETS")
    print("=" * 80)
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES
        )
        gc = gspread.authorize(creds)
        
        sh = gc.open_by_key(SPREADSHEET_ID)
        
        try:
            worksheet = sh.worksheet(WORKSHEET_NAME)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=20)
        
        # Format dataframe
        df_output = df.copy()
        numeric_cols = df_output.select_dtypes(include=['float64', 'float32']).columns
        for col in numeric_cols:
            df_output[col] = df_output[col].round(2)
        
        # Write to sheets
        data = [df_output.columns.tolist()] + df_output.values.tolist()
        worksheet.update('A1', data)
        
        # Format header
        worksheet.format('A1:Z1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Highlight overall row
        overall_idx = df_output[df_output['month'] == 'OVERALL 24M AVG'].index[0] + 2
        worksheet.format(f'A{overall_idx}:Z{overall_idx}', {
            'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.6},
            'textFormat': {'bold': True}
        })
        
        print(f"\n✅ Updated worksheet: {WORKSHEET_NAME}")
        print(f"🔗 https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        
    except Exception as e:
        print(f"\n❌ Failed to update Google Sheets: {e}")


def main():
    """Main execution."""
    
    print("\n🚀 Starting BM Bid-Offer Data Analysis...")
    print("\n⚠️  IMPORTANT:")
    print("   This analyzes BID-OFFER SUBMISSIONS (bmrs_bod), not acceptances")
    print("   For ACTUAL ACCEPTED actions with settlement costs, see bmrs_disbsad")
    
    df = analyze_bod_24months()
    
    if df is None:
        print("\n❌ Analysis failed")
        sys.exit(1)
    
    print_summary(df)
    update_google_sheet(df)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n📊 View results: {WORKSHEET_NAME}")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}\n")


if __name__ == "__main__":
    main()
