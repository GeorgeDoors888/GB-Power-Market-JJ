#!/usr/bin/env python3
"""
Update Google Sheets with BOALF Acceptance Price Analysis
Creates a new sheet with monthly min/avg/max for last 24 months
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "BOALF Price Analysis"

# Google Sheets authentication
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

# BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

print("=" * 100)
print("📊 BOALF ACCEPTANCE PRICE ANALYSIS - Last 24 Months")
print("=" * 100)

# Calculate date range (last 24 months)
end_date = datetime.now()
start_date = end_date - timedelta(days=730)  # ~24 months

print(f"\nDate Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

# Query for monthly statistics
query = f"""
WITH monthly_stats AS (
  SELECT 
    EXTRACT(YEAR FROM settlementDate) as year,
    EXTRACT(MONTH FROM settlementDate) as month,
    DATE_TRUNC(DATE(settlementDate), MONTH) as month_start,
    
    -- All Valid acceptances
    COUNT(*) as total_valid,
    
    -- OFFER statistics (discharge, positive revenue)
    COUNTIF(acceptanceType = 'OFFER' AND acceptancePrice > 0) as offer_count,
    ROUND(MIN(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0 
                   THEN acceptancePrice END), 2) as offer_min,
    ROUND(AVG(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0 
                   THEN acceptancePrice END), 2) as offer_avg,
    ROUND(MAX(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0 
                   THEN acceptancePrice END), 2) as offer_max,
    ROUND(SUM(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0
                   THEN ABS(levelTo - levelFrom) END), 1) as offer_volume_mw,
    
    -- BID statistics (charge, negative cost)
    COUNTIF(acceptanceType = 'BID' AND acceptancePrice < 0) as bid_count,
    ROUND(MAX(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0 
                   THEN acceptancePrice END), 2) as bid_min,  -- Least negative
    ROUND(AVG(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0 
                   THEN acceptancePrice END), 2) as bid_avg,
    ROUND(MIN(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0 
                   THEN acceptancePrice END), 2) as bid_max,  -- Most negative
    ROUND(SUM(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0
                   THEN ABS(levelTo - levelFrom) END), 1) as bid_volume_mw
    
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
  WHERE validation_flag = 'Valid'
    AND DATE(settlementDate) >= '{start_date.strftime('%Y-%m-%d')}'
    AND DATE(settlementDate) <= '{end_date.strftime('%Y-%m-%d')}'
  GROUP BY year, month, month_start
)

SELECT 
  FORMAT_DATE('%Y-%m', month_start) as month_label,
  year,
  month,
  total_valid,
  
  -- OFFER (Discharge/Sell)
  offer_count,
  offer_min,
  offer_avg,
  offer_max,
  offer_volume_mw,
  
  -- BID (Charge/Buy)
  bid_count,
  bid_min,
  bid_avg,
  bid_max,
  bid_volume_mw

FROM monthly_stats
ORDER BY year, month
"""

print("\n⏳ Querying BigQuery...")
df = bq_client.query(query).to_dataframe()
print(f"✅ Retrieved {len(df)} months of data")

# Add VLP battery-specific analysis
print("\n⏳ Querying VLP Battery data...")
vlp_query = f"""
WITH monthly_vlp AS (
  SELECT 
    FORMAT_DATE('%Y-%m', DATE_TRUNC(DATE(settlementDate), MONTH)) as month_label,
    
    -- OFFER statistics (discharge)
    COUNTIF(acceptanceType = 'OFFER' AND acceptancePrice > 0) as vlp_offer_count,
    ROUND(AVG(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0 
                   THEN acceptancePrice END), 2) as vlp_offer_avg,
    ROUND(MAX(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0 
                   THEN acceptancePrice END), 2) as vlp_offer_max,
    ROUND(SUM(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0
                   THEN (ABS(levelTo - levelFrom) / 2) * acceptancePrice END), 0) as vlp_offer_revenue,
    
    -- BID statistics (charge)
    COUNTIF(acceptanceType = 'BID' AND acceptancePrice < 0) as vlp_bid_count,
    ROUND(AVG(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0 
                   THEN acceptancePrice END), 2) as vlp_bid_avg,
    ROUND(MIN(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0 
                   THEN acceptancePrice END), 2) as vlp_bid_max,
    ROUND(SUM(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0
                   THEN (ABS(levelTo - levelFrom) / 2) * acceptancePrice END), 0) as vlp_bid_cost,
    
    -- Net revenue
    ROUND(
      COALESCE(SUM(CASE WHEN acceptanceType = 'OFFER' AND acceptancePrice > 0
                   THEN (ABS(levelTo - levelFrom) / 2) * acceptancePrice END), 0) +
      COALESCE(SUM(CASE WHEN acceptanceType = 'BID' AND acceptancePrice < 0
                   THEN (ABS(levelTo - levelFrom) / 2) * acceptancePrice END), 0)
    , 0) as vlp_net_revenue
    
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
  WHERE validation_flag = 'Valid'
    AND (bmUnit LIKE '2__%' OR bmUnit LIKE 'V__%')
    AND DATE(settlementDate) >= '{start_date.strftime('%Y-%m-%d')}'
    AND DATE(settlementDate) <= '{end_date.strftime('%Y-%m-%d')}'
  GROUP BY month_label
)

SELECT * FROM monthly_vlp
ORDER BY month_label
"""

df_vlp = bq_client.query(vlp_query).to_dataframe()
print(f"✅ Retrieved VLP data for {len(df_vlp)} months")

# Merge dataframes
df = df.merge(df_vlp, on='month_label', how='left')

print("\n📝 Creating/updating Google Sheet...")

# Open spreadsheet and create new sheet
try:
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Try to delete existing sheet if it exists
    try:
        existing_sheet = spreadsheet.worksheet(SHEET_NAME)
        spreadsheet.del_worksheet(existing_sheet)
        print(f"   Deleted existing '{SHEET_NAME}' sheet")
    except:
        pass
    
    # Create new sheet
    sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=200, cols=30)
    print(f"   Created new sheet: '{SHEET_NAME}'")
    
    # Write header with clarification
    header = [
        "Month", "Year", "Month #", "Total Valid",
        "", "--- OFFERS (Discharge/Sell) - ACTUAL ACCEPTED PRICES ---", "", "", "",
        "Count", "Min £/MWh", "Avg £/MWh", "Max £/MWh", "Volume MW",
        "", "--- BIDS (Charge/Buy) - ACTUAL ACCEPTED PRICES ---", "", "", "",
        "Count", "Min £/MWh", "Avg £/MWh", "Max £/MWh", "Volume MW",
        "", "--- VLP BATTERIES (2__ / V__ units) ---", "", "", "", "",
        "Offers", "Avg Offer", "Max Offer", "Revenue £", "Bids", "Avg Bid", "Max Bid", "Cost £", "Net Revenue £"
    ]
    
    # Add explanation row
    explanation = [
        "NOTE: These are ACTUAL ACCEPTED prices paid by ESO, not submitted bids.",
        "High prices (£999-1000/MWh) are real emergency payments during grid stress.",
        "",
        "",
        "",
        "OFFERs = Generator increases output (ESO pays positive £/MWh)",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "BIDs = Generator decreases output (negative = ESO pays to reduce, positive = generator pays)",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "VLP batteries do arbitrage: charge at negative BIDs, discharge at high OFFERs",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    ]
    
    # Prepare data for upload
    data = [header, explanation]
    
    for _, row in df.iterrows():
        data.append([
            row['month_label'],
            int(row['year']),
            int(row['month']),
            int(row['total_valid']),
            "",
            "",  # OFFERS header spacer
            "",
            "",
            "",
            int(row['offer_count']) if pd.notna(row['offer_count']) else 0,
            float(row['offer_min']) if pd.notna(row['offer_min']) else 0,
            float(row['offer_avg']) if pd.notna(row['offer_avg']) else 0,
            float(row['offer_max']) if pd.notna(row['offer_max']) else 0,
            float(row['offer_volume_mw']) if pd.notna(row['offer_volume_mw']) else 0,
            "",
            "",  # BIDS header spacer
            "",
            "",
            "",
            int(row['bid_count']) if pd.notna(row['bid_count']) else 0,
            float(row['bid_min']) if pd.notna(row['bid_min']) else 0,
            float(row['bid_avg']) if pd.notna(row['bid_avg']) else 0,
            float(row['bid_max']) if pd.notna(row['bid_max']) else 0,
            float(row['bid_volume_mw']) if pd.notna(row['bid_volume_mw']) else 0,
            "",
            "",  # VLP header spacer
            "",
            "",
            "",
            "",
            int(row['vlp_offer_count']) if pd.notna(row['vlp_offer_count']) else 0,
            float(row['vlp_offer_avg']) if pd.notna(row['vlp_offer_avg']) else 0,
            float(row['vlp_offer_max']) if pd.notna(row['vlp_offer_max']) else 0,
            float(row['vlp_offer_revenue']) if pd.notna(row['vlp_offer_revenue']) else 0,
            int(row['vlp_bid_count']) if pd.notna(row['vlp_bid_count']) else 0,
            float(row['vlp_bid_avg']) if pd.notna(row['vlp_bid_avg']) else 0,
            float(row['vlp_bid_max']) if pd.notna(row['vlp_bid_max']) else 0,
            float(row['vlp_bid_cost']) if pd.notna(row['vlp_bid_cost']) else 0,
            float(row['vlp_net_revenue']) if pd.notna(row['vlp_net_revenue']) else 0,
        ])
    
    # Upload to sheet
    sheet.update(range_name='A1', values=data)
    
    # Format header row
    sheet.format('A1:AH1', {
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER"
    })
    
    # Format explanation row
    sheet.format('A2:AH2', {
        "backgroundColor": {"red": 1, "green": 0.95, "blue": 0.8},
        "textFormat": {"italic": True, "fontSize": 9},
        "horizontalAlignment": "LEFT"
    })
    
    # Format OFFER section header
    sheet.format('F1:N1', {
        "backgroundColor": {"red": 0.0, "green": 0.6, "blue": 0.3}
    })
    
    # Format BID section header
    sheet.format('P1:X1', {
        "backgroundColor": {"red": 0.8, "green": 0.3, "blue": 0.0}
    })
    
    # Format VLP section header
    sheet.format('Z1:AH1', {
        "backgroundColor": {"red": 0.6, "green": 0.0, "blue": 0.8}
    })
    
    # Freeze header + explanation rows
    sheet.freeze(rows=2)
    
    # Auto-resize columns
    sheet.columns_auto_resize(0, 33)
    
    print(f"✅ Uploaded {len(data)-1} rows to Google Sheets")
    print(f"\n🔗 View sheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet.id}")

except Exception as e:
    print(f"❌ Error updating Google Sheets: {e}")
    raise

print("\n" + "=" * 100)
print("✅ BOALF Price Analysis Complete")
print("=" * 100)
print(f"\nSummary:")
print(f"  - Date Range: {df['month_label'].min()} to {df['month_label'].max()}")
print(f"  - Months Analyzed: {len(df)}")
print(f"  - Total Valid Acceptances: {df['total_valid'].sum():,.0f}")
print(f"  - VLP Net Revenue (24mo): £{df['vlp_net_revenue'].sum():,.0f}")
print("=" * 100)
