#!/usr/bin/env python3
"""
BM Accepted Actions Analysis - 24 Months (DISBSAD Settlement Data)
===================================================================
Analyzes actual BM accepted actions using DISBSAD settlement data.

THIS IS THE CORRECT TABLE for BM acceptance analysis:
- bmrs_disbsad: Disaggregated Balancing Services Adjustment Data
- Contains ACTUAL settlement costs and volumes for accepted BM actions
- Updated daily via auto_backfill_disbsad_daily.py cron job
- Data available: 2022-01-01 to present

Fields:
- cost: £ settlement cost (positive = payment to provider, negative = from provider)
- volume: MWh delivered 
- Price calculated as: cost / volume (£/MWh)
- soFlag: System Operator constraint action

Metrics per month:
- Min/Average/Max accepted price (£/MWh)
- Total accepted volume (MWh)
- Settlement cashflow (£)
- SO constraint actions vs other BM actions
- Upward vs downward actions

Output: Google Sheets with 24-month monthly statistics + overall averages

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
WORKSHEET_NAME = "BM Acceptances 24M"
CREDENTIALS_FILE = "/home/george/inner-cinema-credentials.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def analyze_bm_acceptances_24m():
    """
    Analyze BM accepted actions from bmrs_disbsad for last 24 months.
    Returns monthly aggregates with min/avg/max prices, volumes, and costs.
    """
    
    print("=" * 80)
    print("📊 BM ACCEPTED ACTIONS ANALYSIS - LAST 24 MONTHS (DISBSAD)")
    print("=" * 80)
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # ~24 months
    
    print(f"\n📅 Date Range: {start_date} to {end_date}")
    print(f"   (24 months of actual BM settlement data)")
    print(f"\n📋 Data Source: bmrs_disbsad (Disaggregated Balancing Services)")
    print(f"   ✅ Updated daily via cron (auto_backfill_disbsad_daily.py)")
    print(f"   ✅ Contains: cost (£), volume (MWh), soFlag")
    print(f"   ✅ This is ACTUAL accepted action settlement data")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH disbsad_clean AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            assetId,
            cost,
            volume,
            soFlag,
            -- Calculate price per MWh
            SAFE_DIVIDE(cost, volume) as price_per_mwh,
            -- Classify direction
            CASE 
                WHEN cost > 0 AND volume > 0 THEN 'Upward (Gen↑ or Demand↓)'
                WHEN cost > 0 AND volume < 0 THEN 'Downward (Gen↓ or Demand↑)'
                WHEN cost < 0 AND volume > 0 THEN 'Downward (Provider Pays)'
                WHEN cost < 0 AND volume < 0 THEN 'Upward (Provider Pays)'
                ELSE 'Zero/Unknown'
            END as action_direction,
            -- Action type
            CASE WHEN soFlag THEN 'SO Constraint' ELSE 'Energy Balancing' END as action_type
        FROM `{PROJECT_ID}.{DATASET}.bmrs_disbsad`
        WHERE DATE(settlementDate) >= '{start_date}'
          AND DATE(settlementDate) <= '{end_date}'
          AND volume IS NOT NULL
          AND volume != 0  -- Exclude zero volume
    ),
    
    monthly_stats AS (
        SELECT
            FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
            action_type,
            
            -- Price statistics (£/MWh) - use absolute values
            MIN(ABS(price_per_mwh)) as min_price_mwh,
            AVG(ABS(price_per_mwh)) as avg_price_mwh,
            MAX(ABS(price_per_mwh)) as max_price_mwh,
            APPROX_QUANTILES(ABS(price_per_mwh), 100)[OFFSET(50)] as median_price_mwh,
            
            -- Volume statistics (MWh) - absolute values
            SUM(ABS(volume)) as total_volume_mwh,
            MIN(ABS(volume)) as min_volume_mwh,
            AVG(ABS(volume)) as avg_volume_mwh,
            MAX(ABS(volume)) as max_volume_mwh,
            
            -- Cost statistics (£) - absolute values  
            SUM(ABS(cost)) as total_cost_gbp,
            MIN(ABS(cost)) as min_cost_gbp,
            AVG(ABS(cost)) as avg_cost_gbp,
            MAX(ABS(cost)) as max_cost_gbp,
            
            -- Calculated settlement cashflow
            SUM(ABS(price_per_mwh * volume)) as settlement_cashflow_gbp,
            
            -- Action counts
            COUNT(*) as action_count,
            COUNT(DISTINCT assetId) as unique_assets,
            
            -- Direction breakdown
            COUNTIF(action_direction LIKE 'Upward%') as upward_actions,
            COUNTIF(action_direction LIKE 'Downward%') as downward_actions
            
        FROM disbsad_clean
        WHERE price_per_mwh IS NOT NULL
        GROUP BY month, action_type
        ORDER BY month DESC, action_type
    ),
    
    overall_avg AS (
        -- 24-month overall averages
        SELECT 
            'OVERALL 24M AVG' as month,
            'All Actions' as action_type,
            AVG(avg_price_mwh) as min_price_mwh,
            AVG(avg_price_mwh) as avg_price_mwh,
            MAX(max_price_mwh) as max_price_mwh,
            AVG(median_price_mwh) as median_price_mwh,
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
            print("\n⚠️  No data found in bmrs_disbsad for specified period")
            return None
        
        print(f"\n✅ Retrieved {len(df)} monthly records")
        return df
        
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_summary(df):
    """Print summary statistics."""
    
    if df is None or df.empty:
        return
    
    print("\n" + "=" * 80)
    print("📈 SUMMARY STATISTICS (24 MONTHS)")
    print("=" * 80)
    
    overall = df[df['month'] == 'OVERALL 24M AVG']
    
    if not overall.empty:
        row = overall.iloc[0]
        
        print(f"\n💰 AVERAGE ACCEPTED PRICE (£/MWh):")
        print(f"   Min:     £{row['min_price_mwh']:,.2f}/MWh")
        print(f"   Average: £{row['avg_price_mwh']:,.2f}/MWh")
        print(f"   Median:  £{row['median_price_mwh']:,.2f}/MWh")
        print(f"   Max:     £{row['max_price_mwh']:,.2f}/MWh")
        
        print(f"\n📦 AVERAGE MONTHLY VOLUME:")
        print(f"   Total:   {row['total_volume_mwh']:,.0f} MWh/month")
        print(f"   Average: {row['avg_volume_mwh']:,.2f} MWh/action")
        
        print(f"\n💷 AVERAGE MONTHLY SETTLEMENT COST:")
        print(f"   Total:   £{row['total_cost_gbp']:,.0f}/month")
        print(f"   Average: £{row['avg_cost_gbp']:,.2f}/action")
        print(f"   Cashflow: £{row['settlement_cashflow_gbp']:,.0f}/month")
        
        print(f"\n🔄 AVERAGE MONTHLY ACTIONS:")
        print(f"   Total actions:    {row['action_count']:,.0f}/month")
        print(f"   Unique assets:    {row['unique_assets']:,.0f}")
        print(f"   Upward actions:   {row['upward_actions']:,.0f}/month")
        print(f"   Downward actions: {row['downward_actions']:,.0f}/month")
    
    # Top 5 months by price
    monthly = df[df['month'] != 'OVERALL 24M AVG'].copy()
    if not monthly.empty:
        print("\n" + "=" * 80)
        print("📊 TOP 5 MONTHS BY AVERAGE ACCEPTED PRICE")
        print("=" * 80)
        
        top5 = monthly.nlargest(5, 'avg_price_mwh')
        for _, row in top5.iterrows():
            print(f"\n{row['month']} ({row['action_type']}):")
            print(f"   Avg Price: £{row['avg_price_mwh']:,.2f}/MWh")
            print(f"   Max Price: £{row['max_price_mwh']:,.2f}/MWh")
            print(f"   Volume:    {row['total_volume_mwh']:,.0f} MWh")
            print(f"   Cost:      £{row['total_cost_gbp']:,.0f}")
            print(f"   Actions:   {row['action_count']:,.0f}")


def update_google_sheet(df):
    """Update Google Sheets with results."""
    
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
        worksheet.update(range_name='A1', values=data)
        
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
    
    print("\n🚀 Starting BM Accepted Actions Analysis (24 months)...")
    print("\n📋 Using CORRECT data source:")
    print("   ✅ bmrs_disbsad = Actual BM settlement data")
    print("   ✅ Updated daily via cron job")
    print("   ✅ Contains cost, volume, and soFlag")
    print("   ⚠️  NOT using bmrs_boalf (metadata only, no prices/volumes)")
    
    df = analyze_bm_acceptances_24m()
    
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
