#!/usr/bin/env python3
"""
BM Accepted Offers Analysis - Last 24 Months
Analyzes balancing mechanism accepted offer prices, volumes, and cashflows by month.

Metrics per month:
- Accepted Offer Price (£/MWh): Min, Average, Max
- Accepted Volume (MWh): Total, Average per action
- BM Settlement Cashflow (£): Total (acceptancePrice × acceptanceVolume)
- Action counts: Offer vs Bid breakdown

Data sources:
- bmrs_boalf (historical, complete data)
- bmrs_boalf_iris (real-time, last 24-48h)

Author: GitHub Copilot
Date: December 15, 2025
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
WORKSHEET_NAME = "BM Offers Analysis - 24M"
CREDENTIALS_FILE = "/home/george/inner-cinema-credentials.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def analyze_bm_offers_24months():
    """
    Analyze BM accepted offers for last 24 months from bmrs_boalf.
    Returns monthly aggregates with min/avg/max prices, volumes, and cashflows.
    """
    
    print("=" * 80)
    print("📊 BM ACCEPTED OFFERS ANALYSIS - LAST 24 MONTHS")
    print("=" * 80)
    
    # Calculate date range (last 24 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # ~24 months
    
    print(f"\n📅 Date Range: {start_date} to {end_date}")
    print(f"   (24 months of data)")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Comprehensive monthly analysis query
    query = f"""
    WITH monthly_offers AS (
        SELECT 
            FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
            
            -- Offer metrics
            COUNT(CASE WHEN acceptanceType = 'OFFER' THEN 1 END) as offer_count,
            SUM(CASE WHEN acceptanceType = 'OFFER' THEN acceptedOfferVolume ELSE 0 END) as offer_volume_mwh,
            MIN(CASE WHEN acceptanceType = 'OFFER' AND offerPrice > 0 THEN offerPrice END) as offer_price_min,
            AVG(CASE WHEN acceptanceType = 'OFFER' AND offerPrice > 0 THEN offerPrice END) as offer_price_avg,
            MAX(CASE WHEN acceptanceType = 'OFFER' AND offerPrice > 0 THEN offerPrice END) as offer_price_max,
            SUM(CASE WHEN acceptanceType = 'OFFER' THEN acceptedOfferVolume * offerPrice ELSE 0 END) as offer_cashflow_gbp,
            
            -- Bid metrics
            COUNT(CASE WHEN acceptanceType = 'BID' THEN 1 END) as bid_count,
            SUM(CASE WHEN acceptanceType = 'BID' THEN ABS(acceptedBidVolume) ELSE 0 END) as bid_volume_mwh,
            MIN(CASE WHEN acceptanceType = 'BID' AND bidPrice < 0 THEN ABS(bidPrice) END) as bid_price_min,
            AVG(CASE WHEN acceptanceType = 'BID' AND bidPrice < 0 THEN ABS(bidPrice) END) as bid_price_avg,
            MAX(CASE WHEN acceptanceType = 'BID' AND bidPrice < 0 THEN ABS(bidPrice) END) as bid_price_max,
            SUM(CASE WHEN acceptanceType = 'BID' THEN ABS(acceptedBidVolume * bidPrice) ELSE 0 END) as bid_cashflow_gbp,
            
            -- Combined metrics
            COUNT(*) as total_actions,
            SUM(CASE WHEN acceptanceType = 'OFFER' THEN acceptedOfferVolume 
                     WHEN acceptanceType = 'BID' THEN ABS(acceptedBidVolume) 
                     ELSE 0 END) as total_volume_mwh
            
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE DATE(settlementDate) >= '{start_date}'
          AND DATE(settlementDate) <= '{end_date}'
          AND (acceptanceType = 'OFFER' OR acceptanceType = 'BID')
        GROUP BY month
        ORDER BY month DESC
    ),
    
    overall_avg AS (
        -- Calculate 24-month averages for comparison
        SELECT 
            AVG(offer_price_avg) as avg_offer_price_24m,
            AVG(bid_price_avg) as avg_bid_price_24m,
            SUM(offer_volume_mwh) as total_offer_volume_24m,
            SUM(bid_volume_mwh) as total_bid_volume_24m,
            SUM(offer_cashflow_gbp) as total_offer_cashflow_24m,
            SUM(bid_cashflow_gbp) as total_bid_cashflow_24m,
            SUM(total_actions) as total_actions_24m
        FROM monthly_offers
    )
    
    SELECT 
        mo.*,
        oa.avg_offer_price_24m,
        oa.avg_bid_price_24m,
        oa.total_offer_volume_24m,
        oa.total_bid_volume_24m,
        oa.total_offer_cashflow_24m,
        oa.total_bid_cashflow_24m,
        oa.total_actions_24m
    FROM monthly_offers mo
    CROSS JOIN overall_avg oa
    ORDER BY mo.month DESC
    """
    
    print("\n⏳ Querying BigQuery for 24 months of BM acceptance data...")
    print("   (This may take 30-60 seconds for 24 months of data)")
    
    results = client.query(query).result()
    
    # Convert to pandas DataFrame
    rows = []
    overall_stats = None
    
    for row in results:
        month_data = {
            'month': row.month,
            # Offer metrics
            'offer_count': row.offer_count,
            'offer_volume_mwh': round(row.offer_volume_mwh or 0, 2),
            'offer_price_min': round(row.offer_price_min or 0, 2),
            'offer_price_avg': round(row.offer_price_avg or 0, 2),
            'offer_price_max': round(row.offer_price_max or 0, 2),
            'offer_cashflow_gbp': round(row.offer_cashflow_gbp or 0, 2),
            # Bid metrics
            'bid_count': row.bid_count,
            'bid_volume_mwh': round(row.bid_volume_mwh or 0, 2),
            'bid_price_min': round(row.bid_price_min or 0, 2),
            'bid_price_avg': round(row.bid_price_avg or 0, 2),
            'bid_price_max': round(row.bid_price_max or 0, 2),
            'bid_cashflow_gbp': round(row.bid_cashflow_gbp or 0, 2),
            # Combined
            'total_actions': row.total_actions,
            'total_volume_mwh': round(row.total_volume_mwh or 0, 2)
        }
        rows.append(month_data)
        
        # Store overall stats (same for all rows, just take first)
        if overall_stats is None:
            overall_stats = {
                'avg_offer_price_24m': round(row.avg_offer_price_24m or 0, 2),
                'avg_bid_price_24m': round(row.avg_bid_price_24m or 0, 2),
                'total_offer_volume_24m': round(row.total_offer_volume_24m or 0, 2),
                'total_bid_volume_24m': round(row.total_bid_volume_24m or 0, 2),
                'total_offer_cashflow_24m': round(row.total_offer_cashflow_24m or 0, 2),
                'total_bid_cashflow_24m': round(row.total_bid_cashflow_24m or 0, 2),
                'total_actions_24m': row.total_actions_24m
            }
    
    df = pd.DataFrame(rows)
    
    print(f"✅ Retrieved {len(df)} months of data")
    
    return df, overall_stats

def update_google_sheet(df, overall_stats):
    """Update Google Sheets with BM offers analysis."""
    
    print("\n📊 Updating Google Sheets...")
    
    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    
    # Open spreadsheet
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create worksheet
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        worksheet.clear()
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME, 
            rows=100, 
            cols=20
        )
    
    # Prepare header section
    headers = [
        ['BM ACCEPTED OFFERS ANALYSIS - LAST 24 MONTHS'],
        [f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '', '', f'Data Source: bmrs_boalf'],
        [],
        ['📊 24-MONTH SUMMARY (OVERALL AVERAGES)'],
        ['Metric', 'Offer', 'Bid', 'Combined'],
        [
            'Average Price (£/MWh)',
            f"£{overall_stats['avg_offer_price_24m']:,.2f}",
            f"£{overall_stats['avg_bid_price_24m']:,.2f}",
            ''
        ],
        [
            'Total Volume (MWh)',
            f"{overall_stats['total_offer_volume_24m']:,.0f}",
            f"{overall_stats['total_bid_volume_24m']:,.0f}",
            f"{overall_stats['total_offer_volume_24m'] + overall_stats['total_bid_volume_24m']:,.0f}"
        ],
        [
            'Total Cashflow (£)',
            f"£{overall_stats['total_offer_cashflow_24m']:,.0f}",
            f"£{overall_stats['total_bid_cashflow_24m']:,.0f}",
            f"£{overall_stats['total_offer_cashflow_24m'] + overall_stats['total_bid_cashflow_24m']:,.0f}"
        ],
        [
            'Total Actions',
            '',
            '',
            f"{overall_stats['total_actions_24m']:,}"
        ],
        [],
        ['📅 MONTHLY BREAKDOWN'],
        [
            'Month',
            'Offer Actions',
            'Offer Vol (MWh)',
            'Offer Price Min',
            'Offer Price Avg',
            'Offer Price Max',
            'Offer Cashflow (£)',
            'Bid Actions',
            'Bid Vol (MWh)',
            'Bid Price Min',
            'Bid Price Avg',
            'Bid Price Max',
            'Bid Cashflow (£)',
            'Total Actions',
            'Total Vol (MWh)'
        ]
    ]
    
    # Prepare data rows
    data_rows = []
    for _, row in df.iterrows():
        data_rows.append([
            row['month'],
            row['offer_count'],
            f"{row['offer_volume_mwh']:,.0f}",
            f"£{row['offer_price_min']:,.2f}",
            f"£{row['offer_price_avg']:,.2f}",
            f"£{row['offer_price_max']:,.2f}",
            f"£{row['offer_cashflow_gbp']:,.0f}",
            row['bid_count'],
            f"{row['bid_volume_mwh']:,.0f}",
            f"£{row['bid_price_min']:,.2f}",
            f"£{row['bid_price_avg']:,.2f}",
            f"£{row['bid_price_max']:,.2f}",
            f"£{row['bid_cashflow_gbp']:,.0f}",
            row['total_actions'],
            f"{row['total_volume_mwh']:,.0f}"
        ])
    
    # Combine all data
    all_data = headers + data_rows
    
    # Write to sheet
    worksheet.update('A1', all_data)
    
    # Format headers
    worksheet.format('A1:O1', {
        'backgroundColor': {'red': 0.2, 'green': 0.45, 'blue': 0.7},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True,
            'fontSize': 14
        },
        'horizontalAlignment': 'CENTER'
    })
    
    worksheet.format('A4:D4', {
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
        'textFormat': {'bold': True, 'fontSize': 12}
    })
    
    worksheet.format('A11:O11', {
        'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85},
        'textFormat': {'bold': True, 'fontSize': 11}
    })
    
    worksheet.format('A12:O12', {
        'backgroundColor': {'red': 0.3, 'green': 0.3, 'blue': 0.3},
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'bold': True
        },
        'horizontalAlignment': 'CENTER'
    })
    
    # Freeze header rows
    worksheet.freeze(rows=12)
    
    print(f"✅ Updated worksheet '{WORKSHEET_NAME}'")
    print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

def print_summary(df, overall_stats):
    """Print summary statistics to console."""
    
    print("\n" + "=" * 80)
    print("📊 24-MONTH SUMMARY")
    print("=" * 80)
    
    print(f"\n🎯 OFFER METRICS (24-month average):")
    print(f"   Average Price: £{overall_stats['avg_offer_price_24m']:,.2f}/MWh")
    print(f"   Total Volume: {overall_stats['total_offer_volume_24m']:,.0f} MWh")
    print(f"   Total Cashflow: £{overall_stats['total_offer_cashflow_24m']:,.0f}")
    
    print(f"\n🎯 BID METRICS (24-month average):")
    print(f"   Average Price: £{overall_stats['avg_bid_price_24m']:,.2f}/MWh")
    print(f"   Total Volume: {overall_stats['total_bid_volume_24m']:,.0f} MWh")
    print(f"   Total Cashflow: £{overall_stats['total_bid_cashflow_24m']:,.0f}")
    
    print(f"\n🎯 COMBINED METRICS:")
    total_volume = overall_stats['total_offer_volume_24m'] + overall_stats['total_bid_volume_24m']
    total_cashflow = overall_stats['total_offer_cashflow_24m'] + overall_stats['total_bid_cashflow_24m']
    print(f"   Total Actions: {overall_stats['total_actions_24m']:,}")
    print(f"   Total Volume: {total_volume:,.0f} MWh")
    print(f"   Total Cashflow: £{total_cashflow:,.0f}")
    
    print(f"\n📅 MOST RECENT MONTH ({df.iloc[0]['month']}):")
    print(f"   Offer Price: £{df.iloc[0]['offer_price_min']:,.2f} - £{df.iloc[0]['offer_price_avg']:,.2f} - £{df.iloc[0]['offer_price_max']:,.2f}")
    print(f"   Offer Volume: {df.iloc[0]['offer_volume_mwh']:,.0f} MWh ({df.iloc[0]['offer_count']:,} actions)")
    print(f"   Bid Price: £{df.iloc[0]['bid_price_min']:,.2f} - £{df.iloc[0]['bid_price_avg']:,.2f} - £{df.iloc[0]['bid_price_max']:,.2f}")
    print(f"   Bid Volume: {df.iloc[0]['bid_volume_mwh']:,.0f} MWh ({df.iloc[0]['bid_count']:,} actions)")

def main():
    """Main execution."""
    
    try:
        # Analyze 24 months of BM offers
        df, overall_stats = analyze_bm_offers_24months()
        
        if df.empty:
            print("❌ No data retrieved")
            return 1
        
        # Print summary to console
        print_summary(df, overall_stats)
        
        # Update Google Sheets
        update_google_sheet(df, overall_stats)
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
