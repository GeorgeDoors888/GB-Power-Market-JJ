#!/usr/bin/env python3
"""
Create detailed BOD (Bid-Offer Data) and BOALF (Balancing Actions) analysis sheets

Creates two new sheets:
1. BOD_Analysis - Submitted bid/offer statistics by fuel type and unit
2. BOALF_Analysis - Accepted balancing actions analysis
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = 'inner-cinema-credentials.json'


def get_clients():
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/bigquery'
        ]
    )
    sheets = build('sheets', 'v4', credentials=creds)
    bq = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    return sheets, bq


def ensure_sheet(sheets_service, sheet_name):
    """Create sheet if it doesn't exist"""
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
        
        if sheet_name not in sheet_names:
            print(f"   Creating sheet: {sheet_name}")
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
            ).execute()
    except Exception as e:
        print(f"   ⚠️ Error ensuring sheet {sheet_name}: {e}")


def create_boalf_analysis(sheets_service, bq_client):
    """
    BOALF Analysis: Accepted balancing actions
    - Daily accepted actions
    - Top 10 most active units
    - Actions by fuel type
    - Note: BOALF has volumes only, not prices (prices in BOD)
    """
    print("1️⃣  Creating BOALF Analysis (Accepted Balancing Actions)...")
    
    ensure_sheet(sheets_service, "BOALF_Analysis")
    
    # Query 1: Daily summary (last 30 days)
    daily_query = f"""
    SELECT
        DATE(settlementDate) as date,
        COUNT(DISTINCT acceptanceNumber) as total_actions,
        COUNT(DISTINCT bmUnit) as active_units,
        SUM(CASE WHEN levelTo > 0 THEN ABS(levelTo - levelFrom) ELSE 0 END) as increase_mw,
        SUM(CASE WHEN levelTo < 0 THEN ABS(levelTo - levelFrom) ELSE 0 END) as decrease_mw,
        SUM(ABS(levelTo - levelFrom)) as total_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 30 DAY)
    GROUP BY DATE(settlementDate)
    ORDER BY date DESC
    LIMIT 30
    """
    
    # Query 2: Top 10 most active units
    top_units_query = f"""
    SELECT
        bmUnit,
        COUNT(DISTINCT acceptanceNumber) as action_count,
        SUM(CASE WHEN levelTo > 0 THEN 1 ELSE 0 END) as increase_actions,
        SUM(CASE WHEN levelTo < 0 THEN 1 ELSE 0 END) as decrease_actions,
        SUM(ABS(levelTo - levelFrom)) as total_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 7 DAY)
    GROUP BY bmUnit
    ORDER BY action_count DESC
    LIMIT 10
    """
    
    # Query 3: Actions by fuel type (join with registration data)
    fuel_query = f"""
    SELECT
        COALESCE(reg.fueltype, 'Unknown') as fuel_type,
        COUNT(DISTINCT boalf.acceptanceNumber) as action_count,
        COUNT(DISTINCT boalf.bmUnit) as unit_count,
        SUM(ABS(boalf.levelTo - boalf.levelFrom)) as total_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf` boalf
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` reg
        ON boalf.bmUnit = reg.elexonbmunit OR boalf.bmUnit = reg.nationalgridbmunit
    WHERE boalf.settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 7 DAY)
    GROUP BY fuel_type
    ORDER BY action_count DESC
    LIMIT 15
    """
    
    try:
        # Execute queries
        daily_df = bq_client.query(daily_query).to_dataframe()
        top_units_df = bq_client.query(top_units_query).to_dataframe()
        fuel_df = bq_client.query(fuel_query).to_dataframe()
        
        # Build sheet data
        rows = []
        
        # Header
        rows.append(['⚡ BALANCING ACTIONS ANALYSIS (BOALF)', '', '', '', '', '', ''])
        rows.append([f'Data as of: 2025-10-28 (Last available)', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])
        
        # Section 1: Daily Summary
        rows.append(['📊 DAILY ACCEPTED ACTIONS (Last 30 Days)', '', '', '', '', '', ''])
        rows.append(['Date', 'Total Actions', 'Active Units', 'Increase MW', 'Decrease MW', 'Total MW', ''])
        
        for _, row in daily_df.iterrows():
            rows.append([
                str(row['date']),
                int(row['total_actions']),
                int(row['active_units']),
                int(row['increase_mw']),
                int(row['decrease_mw']),
                int(row['total_mw']),
                ''
            ])
        
        # Add spacing
        rows.append(['', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])
        
        # Section 2: Top 10 Units
        rows.append(['🏆 TOP 10 MOST ACTIVE UNITS (Last 7 Days)', '', '', '', '', '', ''])
        rows.append(['BM Unit', 'Total Actions', 'Increase Actions', 'Decrease Actions', 'Total MW', '', ''])
        
        for _, row in top_units_df.iterrows():
            rows.append([
                row['bmUnit'],
                int(row['action_count']),
                int(row['increase_actions']),
                int(row['decrease_actions']),
                int(row['total_mw']),
                '',
                ''
            ])
        
        # Add spacing
        rows.append(['', '', '', '', '', '', ''])
        rows.append(['', '', '', '', '', '', ''])
        
        # Section 3: By Fuel Type
        rows.append(['🔥 ACTIONS BY FUEL TYPE (Last 7 Days)', '', '', '', '', '', ''])
        rows.append(['Fuel Type', 'Actions', 'Units', 'Total MW', '', '', ''])
        
        for _, row in fuel_df.iterrows():
            rows.append([
                row['fuel_type'],
                int(row['action_count']),
                int(row['unit_count']),
                int(row['total_mw']),
                '',
                '',
                ''
            ])
        
        # Write to sheet
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='BOALF_Analysis!A1',
            valueInputOption='USER_ENTERED',
            body={'values': rows}
        ).execute()
        
        print(f"   ✅ BOALF_Analysis created with {len(daily_df)} days, {len(top_units_df)} top units, {len(fuel_df)} fuel types")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_bod_analysis(sheets_service, bq_client):
    """
    BOD Analysis: Submitted bid-offer data
    - Daily bid/offer statistics
    - Bid-offer spreads by fuel type
    - Price distribution
    """
    print("2️⃣  Creating BOD Analysis (Submitted Bids & Offers)...")
    
    ensure_sheet(sheets_service, "BOD_Analysis")
    
    # Query 1: Daily bid/offer statistics
    daily_query = f"""
    SELECT
        DATE(settlementDate) as date,
        COUNT(DISTINCT bmUnit) as active_units,
        COUNT(DISTINCT pairId) as bid_offer_pairs,
        AVG(CASE WHEN bid > 0 THEN bid END) as avg_bid_price,
        AVG(CASE WHEN offer > 0 THEN offer END) as avg_offer_price,
        AVG(CASE WHEN bid > 0 AND offer > 0 THEN offer - bid END) as avg_spread
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
    WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 30 DAY)
    GROUP BY DATE(settlementDate)
    ORDER BY date DESC
    LIMIT 30
    """
    
    # Query 2: Bid/offer spreads by fuel type
    fuel_query = f"""
    SELECT
        COALESCE(reg.fueltype, 'Unknown') as fuel_type,
        COUNT(DISTINCT bod.bmUnit) as unit_count,
        AVG(CASE WHEN bod.bid > 0 THEN bod.bid END) as avg_bid,
        AVG(CASE WHEN bod.offer > 0 THEN bod.offer END) as avg_offer,
        AVG(CASE WHEN bod.bid > 0 AND bod.offer > 0 THEN bod.offer - bod.bid END) as avg_spread,
        COUNT(*) as total_submissions
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod` bod
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` reg
        ON bod.bmUnit = reg.elexonbmunit OR bod.bmUnit = reg.nationalgridbmunit
    WHERE bod.settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 7 DAY)
    GROUP BY fuel_type
    ORDER BY total_submissions DESC
    LIMIT 15
    """
    
    # Query 3: Top units by submission volume
    top_units_query = f"""
    SELECT
        bmUnit,
        COUNT(DISTINCT pairId) as pairs_submitted,
        AVG(CASE WHEN bid > 0 THEN bid END) as avg_bid,
        AVG(CASE WHEN offer > 0 THEN offer END) as avg_offer,
        COUNT(*) as total_rows
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
    WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 7 DAY)
    GROUP BY bmUnit
    ORDER BY pairs_submitted DESC
    LIMIT 10
    """
    
    try:
        # Execute queries
        daily_df = bq_client.query(daily_query).to_dataframe()
        fuel_df = bq_client.query(fuel_query).to_dataframe()
        top_units_df = bq_client.query(top_units_query).to_dataframe()
        
        # Build sheet data
        rows = []
        
        # Header
        rows.append(['📝 BID-OFFER DATA ANALYSIS (BOD)', '', '', '', '', ''])
        rows.append([f'Data as of: 2025-10-28 (Last available)', '', '', '', '', ''])
        rows.append(['', '', '', '', '', ''])
        
        # Section 1: Daily Summary
        rows.append(['📊 DAILY BID-OFFER STATISTICS (Last 30 Days)', '', '', '', '', ''])
        rows.append(['Date', 'Active Units', 'Bid-Offer Pairs', 'Avg Bid (£/MWh)', 'Avg Offer (£/MWh)', 'Avg Spread (£/MWh)'])
        
        for _, row in daily_df.iterrows():
            rows.append([
                str(row['date']),
                int(row['active_units']),
                int(row['bid_offer_pairs']),
                f"£{row['avg_bid_price']:.2f}" if pd.notna(row['avg_bid_price']) else 'N/A',
                f"£{row['avg_offer_price']:.2f}" if pd.notna(row['avg_offer_price']) else 'N/A',
                f"£{row['avg_spread']:.2f}" if pd.notna(row['avg_spread']) else 'N/A'
            ])
        
        # Add spacing
        rows.append(['', '', '', '', '', ''])
        rows.append(['', '', '', '', '', ''])
        
        # Section 2: By Fuel Type
        rows.append(['🔥 BID-OFFER SPREADS BY FUEL TYPE (Last 7 Days)', '', '', '', '', ''])
        rows.append(['Fuel Type', 'Units', 'Avg Bid (£/MWh)', 'Avg Offer (£/MWh)', 'Avg Spread (£/MWh)', 'Total Submissions'])
        
        for _, row in fuel_df.iterrows():
            rows.append([
                row['fuel_type'],
                int(row['unit_count']),
                f"£{row['avg_bid']:.2f}" if pd.notna(row['avg_bid']) else 'N/A',
                f"£{row['avg_offer']:.2f}" if pd.notna(row['avg_offer']) else 'N/A',
                f"£{row['avg_spread']:.2f}" if pd.notna(row['avg_spread']) else 'N/A',
                int(row['total_submissions'])
            ])
        
        # Add spacing
        rows.append(['', '', '', '', '', ''])
        rows.append(['', '', '', '', '', ''])
        
        # Section 3: Top Units
        rows.append(['🏆 TOP 10 UNITS BY SUBMISSION VOLUME (Last 7 Days)', '', '', '', '', ''])
        rows.append(['BM Unit', 'Pairs Submitted', 'Avg Bid (£/MWh)', 'Avg Offer (£/MWh)', 'Total Rows', ''])
        
        for _, row in top_units_df.iterrows():
            rows.append([
                row['bmUnit'],
                int(row['pairs_submitted']),
                f"£{row['avg_bid']:.2f}" if pd.notna(row['avg_bid']) else 'N/A',
                f"£{row['avg_offer']:.2f}" if pd.notna(row['avg_offer']) else 'N/A',
                int(row['total_rows']),
                ''
            ])
        
        # Write to sheet
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='BOD_Analysis!A1',
            valueInputOption='USER_ENTERED',
            body={'values': rows}
        ).execute()
        
        print(f"   ✅ BOD_Analysis created with {len(daily_df)} days, {len(fuel_df)} fuel types, {len(top_units_df)} top units")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🔧 Creating BOD & BOALF Analysis Sheets")
    print("="*80)
    
    sheets_service, bq_client = get_clients()
    
    success = True
    success &= create_boalf_analysis(sheets_service, bq_client)
    success &= create_bod_analysis(sheets_service, bq_client)
    
    print("="*80)
    if success:
        print("✅ Analysis sheets created successfully!")
        print("\n📋 New Sheets:")
        print("  • BOALF_Analysis - Accepted balancing actions breakdown")
        print("  • BOD_Analysis - Submitted bid-offer data statistics")
    else:
        print("⚠️  Some sheets had errors - check output above")
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
