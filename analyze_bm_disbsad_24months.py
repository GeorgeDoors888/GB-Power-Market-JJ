#!/usr/bin/env python3
"""
BM Accepted Actions Analysis - Last 24 Months (CORRECTED)
==========================================================
Analyzes Balancing Mechanism accepted actions using DISBSAD data (the actual settlement table).

IMPORTANT: 
- bmrs_boalf does NOT have price/volume columns (only acceptanceNumber/Time)
- bmrs_disbsad contains the ACTUAL accepted action prices and volumes
- This is the Disaggregated Balancing Services Adjustment Data table

Metrics per month:
- Min/Average/Max price (£/MWh) calculated as cost/volume
- Total volume (MWh) 
- Settlement cashflow (£ cost)
- SO constraint actions vs other BM actions

Data source:
- bmrs_disbsad: Disaggregated Balancing Services Adjustment Data (2020-present)
  - cost: £ settlement cost
  - volume: MWh delivered
  - so_flag: System Operator constraint action flag
  - assetId: Asset identifier

Author: GitHub Copilot (Corrected)
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
WORKSHEET_NAME = "BM Actions Analysis - 24M"
CREDENTIALS_FILE = "/home/george/inner-cinema-credentials.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def analyze_bm_disbsad_24months():
    """
    Analyze BM accepted actions from bmrs_disbsad for last 24 months.
    Returns monthly aggregates with min/avg/max prices, volumes, and costs.
    """
    
    print("=" * 80)
    print("📊 BM ACCEPTED ACTIONS ANALYSIS (DISBSAD) - LAST 24 MONTHS")
    print("=" * 80)
    
    # Calculate date range (last 24 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # ~24 months
    
    print(f"\n📅 Date Range: {start_date} to {end_date}")
    print(f"   (24 months of data)")
    print(f"\n📋 Data Source: bmrs_disbsad (Disaggregated Balancing Services Adjustment Data)")
    print(f"   ✅ Contains: cost (£), volume (MWh), so_flag, assetId")
    print(f"   ❌ NOT using bmrs_boalf (only has acceptanceNumber/Time, no price/volume)")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Comprehensive monthly analysis query
    query = f"""
    WITH disbsad_data AS (
        SELECT 
            settlementDate,
            assetId,
            cost,
            volume,
            so_flag,
            -- Calculate price per MWh (cost / volume)
            CASE 
                WHEN volume > 0 THEN cost / volume
                WHEN volume < 0 THEN cost / ABS(volume)
                ELSE NULL
            END as price_per_mwh,
            -- Classify as upward/downward based on cost sign
            CASE 
                WHEN cost > 0 THEN 'Upward Action (Provider Paid)'
                WHEN cost < 0 THEN 'Downward Action (Provider Pays)'
                ELSE 'Zero Cost'
            END as action_direction
        FROM `{PROJECT_ID}.{DATASET}.bmrs_disbsad`
        WHERE DATE(settlementDate) >= '{start_date}'
          AND DATE(settlementDate) <= '{end_date}'
          AND volume != 0  -- Exclude zero volume records
    ),
    
    monthly_stats AS (
        SELECT
            FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
            
            -- SO constraint vs other actions
            CASE WHEN so_flag THEN 'SO Constraint' ELSE 'Other BM Action' END as action_type,
            
            -- Price statistics (£/MWh)
            MIN(ABS(price_per_mwh)) as min_price_mwh,
            AVG(ABS(price_per_mwh)) as avg_price_mwh,
            MAX(ABS(price_per_mwh)) as max_price_mwh,
            
            -- Volume statistics (MWh, absolute values)
            SUM(ABS(volume)) as total_volume_mwh,
            MIN(ABS(volume)) as min_volume_mwh,
            AVG(ABS(volume)) as avg_volume_mwh,
            MAX(ABS(volume)) as max_volume_mwh,
            
            -- Cost statistics (£, absolute values for easier reading)
            SUM(ABS(cost)) as total_cost_gbp,
            MIN(ABS(cost)) as min_cost_gbp,
            AVG(ABS(cost)) as avg_cost_gbp,
            MAX(ABS(cost)) as max_cost_gbp,
            
            -- Calculated settlement cashflow (price × volume)
            SUM(ABS(price_per_mwh * volume)) as settlement_cashflow_gbp,
            
            -- Action counts
            COUNT(*) as action_count,
            COUNT(DISTINCT assetId) as unique_assets,
            
            -- Upward vs Downward breakdown
            COUNT(CASE WHEN cost > 0 THEN 1 END) as upward_actions,
            COUNT(CASE WHEN cost < 0 THEN 1 END) as downward_actions
            
        FROM disbsad_data
        WHERE price_per_mwh IS NOT NULL  -- Exclude division by zero
        GROUP BY month, action_type
        ORDER BY month DESC, action_type
    ),
    
    overall_avg AS (
        -- Calculate 24-month averages for comparison
        SELECT 
            'OVERALL 24M AVG' as month,
            'All Actions' as action_type,
            AVG(avg_price_mwh) as min_price_mwh,
            AVG(avg_price_mwh) as avg_price_mwh,
            MAX(max_price_mwh) as max_price_mwh,
            SUM(total_volume_mwh) / 24 as total_volume_mwh,
            AVG(avg_volume_mwh) as min_volume_mwh,
            AVG(avg_volume_mwh) as avg_volume_mwh,
            MAX(max_volume_mwh) as max_volume_mwh,
            SUM(total_cost_gbp) / 24 as total_cost_gbp,
            AVG(avg_cost_gbp) as min_cost_gbp,
            AVG(avg_cost_gbp) as avg_cost_gbp,
            MAX(max_cost_gbp) as max_cost_gbp,
            SUM(settlement_cashflow_gbp) / 24 as settlement_cashflow_gbp,
            SUM(action_count) / 24 as action_count,
            AVG(unique_assets) as unique_assets,
            SUM(upward_actions) / 24 as upward_actions,
            SUM(downward_actions) / 24 as downward_actions
        FROM monthly_stats
    )
    
    SELECT * FROM monthly_stats
    UNION ALL
    SELECT * FROM overall_avg
    ORDER BY 
        CASE WHEN month = 'OVERALL 24M AVG' THEN 1 ELSE 0 END,
        month DESC, 
        action_type
    """
    
    print("\n⏳ Querying BigQuery...")
    print(f"   Table: {PROJECT_ID}.{DATASET}.bmrs_disbsad")
    
    try:
        df = client.query(query).to_dataframe()
        
        if df.empty:
            print("\n⚠️  No data found in bmrs_disbsad for the specified period")
            return None
        
        print(f"\n✅ Retrieved {len(df)} monthly records")
        print(f"   Records include SO constraints and other BM actions")
        
        return df
        
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        return None


def calculate_summary_stats(df):
    """Calculate and print summary statistics."""
    
    if df is None or df.empty:
        return
    
    print("\n" + "=" * 80)
    print("📈 SUMMARY STATISTICS (24 MONTHS)")
    print("=" * 80)
    
    # Filter for overall average row
    overall = df[df['month'] == 'OVERALL 24M AVG']
    
    if not overall.empty:
        overall_row = overall.iloc[0]
        
        print(f"\n💰 AVERAGE PRICE PER MWH:")
        print(f"   Min:     £{overall_row['min_price_mwh']:,.2f}/MWh")
        print(f"   Average: £{overall_row['avg_price_mwh']:,.2f}/MWh")
        print(f"   Max:     £{overall_row['max_price_mwh']:,.2f}/MWh")
        
        print(f"\n📦 AVERAGE MONTHLY VOLUME:")
        print(f"   Total:   {overall_row['total_volume_mwh']:,.0f} MWh/month")
        print(f"   Average: {overall_row['avg_volume_mwh']:,.2f} MWh/action")
        
        print(f"\n💷 AVERAGE MONTHLY COST:")
        print(f"   Total:   £{overall_row['total_cost_gbp']:,.0f}/month")
        print(f"   Average: £{overall_row['avg_cost_gbp']:,.2f}/action")
        
        print(f"\n🔄 AVERAGE MONTHLY ACTIONS:")
        print(f"   Total actions:   {overall_row['action_count']:,.0f}/month")
        print(f"   Unique assets:   {overall_row['unique_assets']:,.0f}")
        print(f"   Upward actions:  {overall_row['upward_actions']:,.0f}/month")
        print(f"   Downward actions: {overall_row['downward_actions']:,.0f}/month")
    
    # Show monthly breakdown by action type
    monthly_data = df[df['month'] != 'OVERALL 24M AVG'].copy()
    
    if not monthly_data.empty:
        print("\n" + "=" * 80)
        print("📊 TOP 5 MONTHS BY VOLUME")
        print("=" * 80)
        
        top_months = monthly_data.nlargest(5, 'total_volume_mwh')
        for idx, row in top_months.iterrows():
            print(f"\n{row['month']} ({row['action_type']}):")
            print(f"   Volume:    {row['total_volume_mwh']:,.0f} MWh")
            print(f"   Avg Price: £{row['avg_price_mwh']:,.2f}/MWh")
            print(f"   Total Cost: £{row['total_cost_gbp']:,.0f}")
            print(f"   Actions:   {row['action_count']:,.0f}")


def update_google_sheet(df):
    """Update Google Sheets with the analysis results."""
    
    if df is None or df.empty:
        print("\n⚠️  No data to write to Google Sheets")
        return
    
    print("\n" + "=" * 80)
    print("📝 UPDATING GOOGLE SHEETS")
    print("=" * 80)
    
    try:
        # Authenticate with Google Sheets
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, 
            scopes=SCOPES
        )
        gc = gspread.authorize(creds)
        
        print(f"\n📊 Opening spreadsheet: {SPREADSHEET_ID}")
        sh = gc.open_by_key(SPREADSHEET_ID)
        
        # Try to open existing worksheet, create if doesn't exist
        try:
            worksheet = sh.worksheet(WORKSHEET_NAME)
            print(f"   ✅ Found existing worksheet: {WORKSHEET_NAME}")
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            print(f"   📄 Creating new worksheet: {WORKSHEET_NAME}")
            worksheet = sh.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=20)
        
        # Format dataframe for sheets
        df_output = df.copy()
        
        # Round numeric columns
        numeric_cols = df_output.select_dtypes(include=['float64', 'float32']).columns
        for col in numeric_cols:
            df_output[col] = df_output[col].round(2)
        
        # Convert to list of lists for gspread
        data = [df_output.columns.tolist()] + df_output.values.tolist()
        
        print(f"\n📤 Writing {len(data)} rows to Google Sheets...")
        worksheet.update('A1', data)
        
        # Format header row
        worksheet.format('A1:Z1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
            'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Highlight overall average row
        overall_row_idx = df_output[df_output['month'] == 'OVERALL 24M AVG'].index[0] + 2  # +2 for header and 1-based
        worksheet.format(f'A{overall_row_idx}:Z{overall_row_idx}', {
            'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.6},
            'textFormat': {'bold': True}
        })
        
        print(f"   ✅ Data written successfully")
        print(f"   🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        
    except Exception as e:
        print(f"\n❌ Failed to update Google Sheets: {e}")


def main():
    """Main execution function."""
    
    print("\n🚀 Starting BM Accepted Actions Analysis...")
    print(f"   Using CORRECTED table: bmrs_disbsad")
    print(f"   (Not bmrs_boalf - that table lacks price/volume columns)")
    
    # Step 1: Query data
    df = analyze_bm_disbsad_24months()
    
    if df is None:
        print("\n❌ Analysis failed - no data retrieved")
        sys.exit(1)
    
    # Step 2: Print summary statistics
    calculate_summary_stats(df)
    
    # Step 3: Update Google Sheets
    update_google_sheet(df)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n📊 Results available in Google Sheets worksheet: '{WORKSHEET_NAME}'")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("\n")


if __name__ == "__main__":
    main()
