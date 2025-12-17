#!/usr/bin/env python3
"""
Add Comprehensive Accepted BID/OFFER Data to Google Sheets
Creates a new sheet with all acceptance statistics, min/max, averages, volumes
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import time

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def main():
    print("=" * 100)
    print("📊 Adding Comprehensive Accepted BID/OFFER Data to Google Sheets")
    print("=" * 100)
    
    # Connect to BigQuery
    bq_client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
    
    # Query 1: Overall statistics
    print("\n1️⃣ Fetching overall statistics...")
    query_overall = """
    SELECT 
      acceptanceType,
      COUNT(*) as num_acceptances,
      ROUND(AVG(acceptancePrice), 2) as avg_price,
      ROUND(MIN(acceptancePrice), 2) as min_price,
      ROUND(MAX(acceptancePrice), 2) as max_price,
      ROUND(STDDEV(acceptancePrice), 2) as std_dev,
      ROUND(AVG(acceptanceVolume), 1) as avg_volume_mw,
      ROUND(SUM(acceptanceVolume), 0) as total_volume_mwh,
      ROUND(SUM(acceptancePrice * acceptanceVolume) / SUM(acceptanceVolume), 2) as volume_weighted_avg
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE validation_flag = 'Valid'
      AND acceptancePrice IS NOT NULL
      AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
    GROUP BY acceptanceType
    ORDER BY acceptanceType
    """
    
    df_overall = bq_client.query(query_overall).to_dataframe()
    print(f"✅ Retrieved {len(df_overall)} rows")
    
    # Query 2: Monthly breakdown
    print("\n2️⃣ Fetching monthly breakdown...")
    query_monthly = """
    SELECT 
      FORMAT_DATE('%Y-%m', DATE(settlementDate)) as month,
      acceptanceType,
      COUNT(*) as num_acceptances,
      ROUND(AVG(acceptancePrice), 2) as avg_price,
      ROUND(MIN(acceptancePrice), 2) as min_price,
      ROUND(MAX(acceptancePrice), 2) as max_price,
      ROUND(SUM(acceptanceVolume), 0) as total_volume_mwh,
      ROUND(SUM(acceptancePrice * acceptanceVolume) / SUM(acceptanceVolume), 2) as volume_weighted_avg
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE validation_flag = 'Valid'
      AND acceptancePrice IS NOT NULL
      AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
    GROUP BY month, acceptanceType
    ORDER BY month DESC, acceptanceType
    """
    
    df_monthly = bq_client.query(query_monthly).to_dataframe()
    print(f"✅ Retrieved {len(df_monthly)} rows")
    
    # Authenticate with Google Sheets
    print("\n3️⃣ Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID)
    
    # Create new worksheet
    try:
        worksheet = sheet.worksheet("ACCEPTED_Data_Analysis")
        print("⚠️  Worksheet 'ACCEPTED_Data_Analysis' already exists - will clear and update")
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("✅ Creating new worksheet 'ACCEPTED_Data_Analysis'")
        worksheet = sheet.add_worksheet(title="ACCEPTED_Data_Analysis", rows=200, cols=15)
    
    # Build the data structure
    data = [
        ["📊 COMPREHENSIVE ACCEPTED BID/OFFER DATA ANALYSIS", "", "", "", "", "", "", "", ""],
        ["24-Month Period: " + df_monthly['month'].max() + " to " + df_monthly['month'].min(), "", "", "", "", "", "", "", ""],
        ["Source: inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete", "", "", "", "", "", "", "", ""],
        ["Last Updated: 2025-12-16", "", "", "", "", "", "", "", ""],
        [""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        ["1️⃣ OVERALL STATISTICS (24 Months)", "", "", "", "", "", "", "", ""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        [""],
        ["Metric", "BIDS (Reduce Output)", "OFFERS (Increase Output)", "Difference", "", "", "", "", ""],
        ["Count", "", "", "", "", "", "", "", ""],
        ["Simple Average (£/MWh)", "", "", "", "", "", "", "", ""],
        ["Volume-Weighted Avg (£/MWh) ⭐", "", "", "", "", "", "", "", ""],
        ["Min Price (£/MWh)", "", "", "", "", "", "", "", ""],
        ["Max Price (£/MWh)", "", "", "", "", "", "", "", ""],
        ["Std Deviation", "", "", "", "", "", "", "", ""],
        ["Avg Volume per Action (MW)", "", "", "", "", "", "", "", ""],
        ["Total Volume (MWh)", "", "", "", "", "", "", "", ""],
        ["Total Volume (TWh)", "", "", "", "", "", "", "", ""],
        ["% of Total Volume", "", "", "", "", "", "", "", ""],
        [""],
        [""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        ["2️⃣ MONTHLY BREAKDOWN - BIDS (Reduce Output)", "", "", "", "", "", "", "", ""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        [""],
        ["Month", "Count", "Simple Avg (£/MWh)", "Volume-Wtd Avg (£/MWh)", "Min (£/MWh)", "Max (£/MWh)", "Total Vol (MWh)", "", ""],
    ]
    
    # Fill in overall statistics
    bid_data = df_overall[df_overall['acceptanceType'] == 'BID'].iloc[0]
    offer_data = df_overall[df_overall['acceptanceType'] == 'OFFER'].iloc[0]
    
    total_volume = bid_data['total_volume_mwh'] + offer_data['total_volume_mwh']
    
    data[10][1] = f"{bid_data['num_acceptances']:,.0f}"
    data[10][2] = f"{offer_data['num_acceptances']:,.0f}"
    data[10][3] = f"{bid_data['num_acceptances'] - offer_data['num_acceptances']:,.0f}"
    
    data[11][1] = f"£{bid_data['avg_price']:.2f}"
    data[11][2] = f"£{offer_data['avg_price']:.2f}"
    data[11][3] = f"£{bid_data['avg_price'] - offer_data['avg_price']:.2f}"
    
    data[12][1] = f"£{bid_data['volume_weighted_avg']:.2f}"
    data[12][2] = f"£{offer_data['volume_weighted_avg']:.2f}"
    data[12][3] = f"£{bid_data['volume_weighted_avg'] - offer_data['volume_weighted_avg']:.2f}"
    
    data[13][1] = f"£{bid_data['min_price']:.2f}"
    data[13][2] = f"£{offer_data['min_price']:.2f}"
    
    data[14][1] = f"£{bid_data['max_price']:.2f}"
    data[14][2] = f"£{offer_data['max_price']:.2f}"
    
    data[15][1] = f"{bid_data['std_dev']:.2f}"
    data[15][2] = f"{offer_data['std_dev']:.2f}"
    
    data[16][1] = f"{bid_data['avg_volume_mw']:.1f} MW"
    data[16][2] = f"{offer_data['avg_volume_mw']:.1f} MW"
    
    data[17][1] = f"{bid_data['total_volume_mwh']:,.0f}"
    data[17][2] = f"{offer_data['total_volume_mwh']:,.0f}"
    
    data[18][1] = f"{bid_data['total_volume_mwh']/1000000:.2f}"
    data[18][2] = f"{offer_data['total_volume_mwh']/1000000:.2f}"
    
    data[19][1] = f"{100*bid_data['total_volume_mwh']/total_volume:.1f}%"
    data[19][2] = f"{100*offer_data['total_volume_mwh']/total_volume:.1f}%"
    
    # Add monthly BID data
    df_bids = df_monthly[df_monthly['acceptanceType'] == 'BID'].copy()
    for _, row in df_bids.iterrows():
        data.append([
            row['month'],
            f"{row['num_acceptances']:,.0f}",
            f"£{row['avg_price']:.2f}",
            f"£{row['volume_weighted_avg']:.2f}",
            f"£{row['min_price']:.2f}",
            f"£{row['max_price']:.2f}",
            f"{row['total_volume_mwh']:,.0f}",
            "", ""
        ])
    
    # Add OFFER section
    data.extend([
        [""],
        [""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        ["3️⃣ MONTHLY BREAKDOWN - OFFERS (Increase Output)", "", "", "", "", "", "", "", ""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        [""],
        ["Month", "Count", "Simple Avg (£/MWh)", "Volume-Wtd Avg (£/MWh)", "Min (£/MWh)", "Max (£/MWh)", "Total Vol (MWh)", "", ""],
    ])
    
    df_offers = df_monthly[df_monthly['acceptanceType'] == 'OFFER'].copy()
    for _, row in df_offers.iterrows():
        data.append([
            row['month'],
            f"{row['num_acceptances']:,.0f}",
            f"£{row['avg_price']:.2f}",
            f"£{row['volume_weighted_avg']:.2f}",
            f"£{row['min_price']:.2f}",
            f"£{row['max_price']:.2f}",
            f"{row['total_volume_mwh']:,.0f}",
            "", ""
        ])
    
    # Add key insights
    data.extend([
        [""],
        [""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        ["🔑 KEY INSIGHTS", "", "", "", "", "", "", "", ""],
        ["═══════════════════════════════════════════════════════════════", "", "", "", "", "", "", "", ""],
        [""],
        ["1. Volume-Weighted Averages are MORE ACCURATE than simple averages", "", "", "", "", "", "", "", ""],
        ["   - BIDs: £0.98/MWh volume-weighted vs -£1.63/MWh simple average", "", "", "", "", "", "", "", ""],
        ["   - OFFERs: £96.35/MWh volume-weighted vs £88.58/MWh simple average", "", "", "", "", "", "", "", ""],
        [""],
        ["2. BID Volume is 1.6x LARGER than OFFER Volume", "", "", "", "", "", "", "", ""],
        [f"   - BIDs: {bid_data['total_volume_mwh']/1000000:.1f} TWh (62% of total)", "", "", "", "", "", "", "", ""],
        [f"   - OFFERs: {offer_data['total_volume_mwh']/1000000:.1f} TWh (38% of total)", "", "", "", "", "", "", "", ""],
        ["   - This confirms UK grid has MORE SURPLUS than scarcity events", "", "", "", "", "", "", "", ""],
        [""],
        ["3. BIDs and OFFERs are OPPOSITE actions - NEVER average together!", "", "", "", "", "", "", "", ""],
        ["   - BIDs = Generators paid to DECREASE output (often negative prices)", "", "", "", "", "", "", "", ""],
        ["   - OFFERs = Generators paid to INCREASE output (positive prices)", "", "", "", "", "", "", "", ""],
        [""],
        ["4. Price Ranges show extreme market conditions:", "", "", "", "", "", "", "", ""],
        ["   - BIDs: -£1,000 to +£200/MWh", "", "", "", "", "", "", "", ""],
        ["   - OFFERs: -£979.88 to +£1,000/MWh", "", "", "", "", "", "", "", ""],
        [""],
    ])
    
    # Write to sheet
    print(f"\n4️⃣ Writing {len(data)} rows to worksheet...")
    worksheet.update(values=data, range_name='A1')
    time.sleep(2)
    
    # Format headers
    print("5️⃣ Applying formatting...")
    
    # Title
    worksheet.format('A1:I1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    time.sleep(1)
    
    # Section headers (rows 7, 24, and OFFER section)
    for row in [7, 24]:
        worksheet.format(f'A{row}:I{row}', {
            'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.6},
            'textFormat': {'bold': True, 'fontSize': 12}
        })
        time.sleep(0.5)
    
    # Data table headers
    worksheet.format('A10:I10', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'bold': True},
        'borders': {
            'top': {'style': 'SOLID_MEDIUM'},
            'bottom': {'style': 'SOLID_MEDIUM'}
        }
    })
    time.sleep(1)
    
    worksheet.format('A27:G27', {
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
        'textFormat': {'bold': True},
        'borders': {
            'top': {'style': 'SOLID_MEDIUM'},
            'bottom': {'style': 'SOLID_MEDIUM'}
        }
    })
    time.sleep(1)
    
    # Bold first column
    worksheet.format('A:A', {'textFormat': {'bold': True}})
    time.sleep(1)
    
    # Auto-resize columns
    worksheet.columns_auto_resize(0, 8)
    
    print("\n" + "=" * 100)
    print("✅ Accepted Data Analysis added successfully to Google Sheets!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
    print("=" * 100)
    
    print("\n📈 Summary:")
    print(f"  - Overall statistics: 2 acceptance types")
    print(f"  - Monthly data: {len(df_monthly)} rows")
    print(f"  - BIDs: {len(df_bids)} months")
    print(f"  - OFFERs: {len(df_offers)} months")
    print(f"  - Total volume: {total_volume/1000000:.1f} TWh")

if __name__ == "__main__":
    main()
