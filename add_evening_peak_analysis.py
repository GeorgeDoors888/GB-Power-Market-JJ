#!/usr/bin/env python3
"""
Add Evening Peak Analysis (4-8 PM Weekdays) to Google Sheets
Shows BOALF acceptance statistics during evening demand peak
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
    print("🌆 Adding Evening Peak Analysis (4-8 PM Weekdays) to Google Sheets")
    print("=" * 100)
    
    # Connect to BigQuery
    bq_client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
    
    # Query 1: Evening peak overall statistics (Settlement Periods 33-40 = 16:00-20:00)
    print("\n1️⃣ Fetching evening peak overall statistics...")
    query_evening = """
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
      AND settlementPeriod BETWEEN 33 AND 40
      AND EXTRACT(DAYOFWEEK FROM DATE(settlementDate)) BETWEEN 2 AND 6
    GROUP BY acceptanceType
    ORDER BY acceptanceType
    """
    
    df_evening = bq_client.query(query_evening).to_dataframe()
    print(f"✅ Retrieved {len(df_evening)} rows")
    
    # Query 2: All-day statistics for comparison
    print("\n2️⃣ Fetching all-day statistics for comparison...")
    query_allday = """
    SELECT 
      acceptanceType,
      COUNT(*) as num_acceptances,
      ROUND(SUM(acceptanceVolume), 0) as total_volume_mwh,
      ROUND(SUM(acceptancePrice * acceptanceVolume) / SUM(acceptanceVolume), 2) as volume_weighted_avg
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE validation_flag = 'Valid'
      AND acceptancePrice IS NOT NULL
      AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
    GROUP BY acceptanceType
    ORDER BY acceptanceType
    """
    
    df_allday = bq_client.query(query_allday).to_dataframe()
    print(f"✅ Retrieved {len(df_allday)} rows")
    
    # Query 3: Morning peak for comparison
    print("\n3️⃣ Fetching morning peak statistics for comparison...")
    query_morning = """
    SELECT 
      acceptanceType,
      ROUND(SUM(acceptancePrice * acceptanceVolume) / SUM(acceptanceVolume), 2) as volume_weighted_avg
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE validation_flag = 'Valid'
      AND acceptancePrice IS NOT NULL
      AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH)
      AND settlementPeriod BETWEEN 11 AND 22
      AND EXTRACT(DAYOFWEEK FROM DATE(settlementDate)) BETWEEN 2 AND 6
    GROUP BY acceptanceType
    ORDER BY acceptanceType
    """
    
    df_morning = bq_client.query(query_morning).to_dataframe()
    print(f"✅ Retrieved {len(df_morning)} rows")
    
    # Query 4: Monthly breakdown
    print("\n4️⃣ Fetching monthly breakdown...")
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
      AND settlementPeriod BETWEEN 33 AND 40
      AND EXTRACT(DAYOFWEEK FROM DATE(settlementDate)) BETWEEN 2 AND 6
    GROUP BY month, acceptanceType
    ORDER BY month DESC, acceptanceType
    """
    
    df_monthly = bq_client.query(query_monthly).to_dataframe()
    print(f"✅ Retrieved {len(df_monthly)} rows")
    
    # Authenticate with Google Sheets
    print("\n5️⃣ Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID)
    
    # Create new worksheet
    print("\n6️⃣ Creating new worksheet 'Evening_Peak_Analysis'...")
    try:
        worksheet = sheet.add_worksheet(title="Evening_Peak_Analysis", rows=150, cols=10)
    except Exception as e:
        print(f"⚠️  Worksheet may already exist: {e}")
        worksheet = sheet.worksheet("Evening_Peak_Analysis")
        worksheet.clear()
    
    time.sleep(1)
    
    # Build data structure
    print("\n7️⃣ Building data structure...")
    
    data = []
    
    # Header
    data.append(["📊 EVENING PEAK ANALYSIS: 4-8 PM WEEKDAYS"])
    data.append(["24-Month Period: 2025-12-16 to 2023-12-16"])
    data.append(["Time Range: Settlement Periods 33-40 (16:00-20:00)"])
    data.append(["Days: Monday-Friday only"])
    data.append(["Source: inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete"])
    data.append(["Last Updated: 2025-12-16"])
    data.append([])
    
    # Section 1: Overall Evening Peak Statistics
    data.append(["═" * 80])
    data.append(["1️⃣ EVENING PEAK STATISTICS (4-8 PM Weekdays)"])
    data.append(["═" * 80])
    data.append([])
    
    data.append(["Metric", "BIDS (Reduce Output)", "OFFERS (Increase Output)", "Difference"])
    
    bid_row = df_evening[df_evening['acceptanceType']=='BID'].iloc[0]
    offer_row = df_evening[df_evening['acceptanceType']=='OFFER'].iloc[0]
    
    data.append(["Count", f"{int(bid_row['num_acceptances']):,}", f"{int(offer_row['num_acceptances']):,}", 
                 f"{int(bid_row['num_acceptances'] - offer_row['num_acceptances']):,}"])
    data.append(["Simple Average (£/MWh)", f"£{bid_row['avg_price']:.2f}", f"£{offer_row['avg_price']:.2f}", 
                 f"£{bid_row['avg_price'] - offer_row['avg_price']:.2f}"])
    data.append(["Volume-Weighted Avg (£/MWh) ⭐", f"£{bid_row['volume_weighted_avg']:.2f}", 
                 f"£{offer_row['volume_weighted_avg']:.2f}", f"£{bid_row['volume_weighted_avg'] - offer_row['volume_weighted_avg']:.2f}"])
    data.append(["Min Price (£/MWh)", f"£{bid_row['min_price']:.2f}", f"£{offer_row['min_price']:.2f}", ""])
    data.append(["Max Price (£/MWh)", f"£{bid_row['max_price']:.2f}", f"£{offer_row['max_price']:.2f}", ""])
    data.append(["Std Deviation", f"{bid_row['std_dev']:.2f}", f"{offer_row['std_dev']:.2f}", ""])
    data.append(["Avg Volume per Action (MW)", f"{bid_row['avg_volume_mw']:.1f} MW", f"{offer_row['avg_volume_mw']:.1f} MW", ""])
    data.append(["Total Volume (MWh)", f"{int(bid_row['total_volume_mwh']):,}", f"{int(offer_row['total_volume_mwh']):,}", ""])
    data.append(["Total Volume (TWh)", f"{bid_row['total_volume_mwh']/1e6:.2f}", f"{offer_row['total_volume_mwh']/1e6:.2f}", ""])
    
    # Calculate percentages of total
    allday_bid = df_allday[df_allday['acceptanceType']=='BID'].iloc[0]
    allday_offer = df_allday[df_allday['acceptanceType']=='OFFER'].iloc[0]
    
    data.append(["% of All-Day Count", 
                 f"{100*bid_row['num_acceptances']/allday_bid['num_acceptances']:.1f}%",
                 f"{100*offer_row['num_acceptances']/allday_offer['num_acceptances']:.1f}%", ""])
    data.append(["% of All-Day Volume", 
                 f"{100*bid_row['total_volume_mwh']/allday_bid['total_volume_mwh']:.1f}%",
                 f"{100*offer_row['total_volume_mwh']/allday_offer['total_volume_mwh']:.1f}%", ""])
    
    data.append([])
    data.append([])
    
    # Section 2: Price Comparison
    data.append(["═" * 80])
    data.append(["2️⃣ PRICE COMPARISON: Evening vs Morning vs All-Day"])
    data.append(["═" * 80])
    data.append([])
    
    morning_bid = df_morning[df_morning['acceptanceType']=='BID'].iloc[0]['volume_weighted_avg']
    morning_offer = df_morning[df_morning['acceptanceType']=='OFFER'].iloc[0]['volume_weighted_avg']
    
    data.append(["Period", "BIDs (£/MWh)", "OFFERs (£/MWh)"])
    data.append(["Evening Peak (4-8 PM)", f"£{bid_row['volume_weighted_avg']:.2f}", f"£{offer_row['volume_weighted_avg']:.2f}"])
    data.append(["Morning Peak (5-11 AM)", f"£{morning_bid:.2f}", f"£{morning_offer:.2f}"])
    data.append(["All-Day Average", f"£{allday_bid['volume_weighted_avg']:.2f}", f"£{allday_offer['volume_weighted_avg']:.2f}"])
    data.append([])
    data.append(["Evening Premium vs Morning", 
                 f"{bid_row['volume_weighted_avg'] - morning_bid:+.2f}",
                 f"{offer_row['volume_weighted_avg'] - morning_offer:+.2f}"])
    data.append(["Evening Premium vs All-Day", 
                 f"{bid_row['volume_weighted_avg'] - allday_bid['volume_weighted_avg']:+.2f}",
                 f"{offer_row['volume_weighted_avg'] - allday_offer['volume_weighted_avg']:+.2f}"])
    
    data.append([])
    data.append([])
    
    # Section 3: Monthly Breakdown - BIDs
    data.append(["═" * 80])
    data.append(["3️⃣ MONTHLY BREAKDOWN - BIDS (Evening Peak)"])
    data.append(["═" * 80])
    data.append([])
    
    data.append(["Month", "Count", "Simple Avg (£/MWh)", "Volume-Wtd Avg (£/MWh)", 
                 "Min (£/MWh)", "Max (£/MWh)", "Total Vol (MWh)"])
    
    for _, row in df_monthly[df_monthly['acceptanceType']=='BID'].iterrows():
        data.append([
            row['month'],
            f"{int(row['num_acceptances']):,}",
            f"£{row['avg_price']:.2f}",
            f"£{row['volume_weighted_avg']:.2f}",
            f"£{row['min_price']:.2f}",
            f"£{row['max_price']:.2f}",
            f"{int(row['total_volume_mwh']):,}"
        ])
    
    data.append([])
    data.append([])
    
    # Section 4: Monthly Breakdown - OFFERs
    data.append(["═" * 80])
    data.append(["4️⃣ MONTHLY BREAKDOWN - OFFERS (Evening Peak)"])
    data.append(["═" * 80])
    data.append([])
    
    data.append(["Month", "Count", "Simple Avg (£/MWh)", "Volume-Wtd Avg (£/MWh)", 
                 "Min (£/MWh)", "Max (£/MWh)", "Total Vol (MWh)"])
    
    for _, row in df_monthly[df_monthly['acceptanceType']=='OFFER'].iterrows():
        data.append([
            row['month'],
            f"{int(row['num_acceptances']):,}",
            f"£{row['avg_price']:.2f}",
            f"£{row['volume_weighted_avg']:.2f}",
            f"£{row['min_price']:.2f}",
            f"£{row['max_price']:.2f}",
            f"{int(row['total_volume_mwh']):,}"
        ])
    
    data.append([])
    data.append([])
    
    # Section 5: Key Insights
    data.append(["═" * 80])
    data.append(["🔑 KEY INSIGHTS"])
    data.append(["═" * 80])
    data.append([])
    
    data.append(["1. Evening Peak is HIGHEST VALUE Period for VLP Batteries"])
    data.append([f"   - OFFER prices: £{offer_row['volume_weighted_avg']:.2f}/MWh (evening) vs £{morning_offer:.2f}/MWh (morning) = "
                 f"+£{offer_row['volume_weighted_avg'] - morning_offer:.2f} premium 🔥"])
    data.append([f"   - BID prices: £{bid_row['volume_weighted_avg']:.2f}/MWh (evening) vs £{morning_bid:.2f}/MWh (morning) = "
                 f"+£{bid_row['volume_weighted_avg'] - morning_bid:.2f} premium"])
    data.append([])
    
    data.append(["2. Evening Peak Represents ~13% of Daily Balancing Activity"])
    data.append([f"   - BIDs: {100*bid_row['num_acceptances']/allday_bid['num_acceptances']:.1f}% of daily count, "
                 f"{100*bid_row['total_volume_mwh']/allday_bid['total_volume_mwh']:.1f}% of daily volume"])
    data.append([f"   - OFFERs: {100*offer_row['num_acceptances']/allday_offer['num_acceptances']:.1f}% of daily count, "
                 f"{100*offer_row['total_volume_mwh']/allday_offer['total_volume_mwh']:.1f}% of daily volume"])
    data.append([])
    
    data.append(["3. Evening Demand Peak Creates Premium Pricing"])
    data.append(["   - 4-8 PM: Peak residential demand + business still operating"])
    data.append(["   - Higher OFFER prices = better revenue for VLP discharge"])
    data.append(["   - Charge during low-price periods (overnight/morning), discharge at evening peak"])
    data.append([])
    
    data.append(["4. Time Period Details"])
    data.append(["   - Settlement Periods 33-40 = 16:00-20:00 (8 periods × 30 min = 4 hours)"])
    data.append(["   - Weekdays only (Monday-Friday) to focus on business + residential overlap"])
    data.append(["   - Weekend excluded due to different demand profiles"])
    
    # Write to sheet
    print(f"\n✍️  Writing {len(data)} rows to worksheet...")
    worksheet.update(values=data, range_name='A1')
    time.sleep(2)
    
    # Apply formatting
    print("\n🎨 Applying formatting...")
    
    # Title row - blue background
    worksheet.format('A1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True, 'fontSize': 12},
        'horizontalAlignment': 'CENTER'
    })
    
    # Section headers - yellow background
    for row_num in [8, 9, 26, 27]:
        worksheet.format(f'A{row_num}:J{row_num}', {
            'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.4},
            'textFormat': {'bold': True}
        })
    
    # Column headers - gray background
    for row_num in [12, 29, 46]:
        worksheet.format(f'A{row_num}:J{row_num}', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True}
        })
    
    # Auto-resize columns
    worksheet.columns_auto_resize(0, 9)
    
    print("\n" + "=" * 100)
    print("✅ Evening Peak Analysis added successfully to Google Sheets!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
    print("\nSummary:")
    print(f"  - Evening peak (4-8 PM weekdays) acceptances: {int(bid_row['num_acceptances'] + offer_row['num_acceptances']):,}")
    print(f"  - BIDs: {int(bid_row['num_acceptances']):,} count, {bid_row['total_volume_mwh']/1e6:.2f} TWh")
    print(f"  - OFFERs: {int(offer_row['num_acceptances']):,} count, {offer_row['total_volume_mwh']/1e6:.2f} TWh")
    print(f"  - OFFER premium vs morning: +£{offer_row['volume_weighted_avg'] - morning_offer:.2f}/MWh 🔥")
    print("=" * 100)

if __name__ == "__main__":
    main()
