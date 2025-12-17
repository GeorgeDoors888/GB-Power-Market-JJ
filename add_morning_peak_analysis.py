#!/usr/bin/env python3
"""
Add Morning Peak Analysis (5-11 AM Weekdays) to Google Sheets
Shows BOALF acceptance statistics during morning demand ramp-up
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
    print("🌅 Adding Morning Peak Analysis (5-11 AM Weekdays) to Google Sheets")
    print("=" * 100)
    
    # Connect to BigQuery
    bq_client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
    
    # Query 1: Morning peak overall statistics
    print("\n1️⃣ Fetching morning peak overall statistics...")
    query_morning = """
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
      AND settlementPeriod BETWEEN 11 AND 22
      AND EXTRACT(DAYOFWEEK FROM DATE(settlementDate)) BETWEEN 2 AND 6
    GROUP BY acceptanceType
    ORDER BY acceptanceType
    """
    
    df_morning = bq_client.query(query_morning).to_dataframe()
    print(f"✅ Retrieved {len(df_morning)} rows")
    
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
    
    # Query 3: Monthly breakdown
    print("\n3️⃣ Fetching monthly breakdown...")
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
      AND settlementPeriod BETWEEN 11 AND 22
      AND EXTRACT(DAYOFWEEK FROM DATE(settlementDate)) BETWEEN 2 AND 6
    GROUP BY month, acceptanceType
    ORDER BY month DESC, acceptanceType
    """
    
    df_monthly = bq_client.query(query_monthly).to_dataframe()
    print(f"✅ Retrieved {len(df_monthly)} rows")
    
    # Authenticate with Google Sheets
    print("\n4️⃣ Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID)
    
    # Create new worksheet
    print("\n5️⃣ Creating new worksheet 'Morning_Peak_Analysis'...")
    try:
        worksheet = sheet.add_worksheet(title="Morning_Peak_Analysis", rows=150, cols=10)
    except Exception as e:
        print(f"⚠️  Worksheet may already exist: {e}")
        worksheet = sheet.worksheet("Morning_Peak_Analysis")
        worksheet.clear()
    
    time.sleep(1)
    
    # Build data structure
    print("\n6️⃣ Building data structure...")
    
    data = []
    
    # Header
    data.append(["📊 MORNING PEAK ANALYSIS: 5-11 AM WEEKDAYS"])
    data.append(["24-Month Period: 2025-12-16 to 2023-12-16"])
    data.append(["Time Range: Settlement Periods 11-22 (05:00-11:00)"])
    data.append(["Days: Monday-Friday only"])
    data.append(["Source: inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete"])
    data.append(["Last Updated: 2025-12-16"])
    data.append([])
    
    # Section 1: Overall Morning Peak Statistics
    data.append(["═" * 80])
    data.append(["1️⃣ MORNING PEAK STATISTICS (5-11 AM Weekdays)"])
    data.append(["═" * 80])
    data.append([])
    
    data.append(["Metric", "BIDS (Reduce Output)", "OFFERS (Increase Output)", "Difference"])
    
    bid_row = df_morning[df_morning['acceptanceType']=='BID'].iloc[0]
    offer_row = df_morning[df_morning['acceptanceType']=='OFFER'].iloc[0]
    
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
    
    # Section 2: All-Day Comparison
    data.append(["═" * 80])
    data.append(["2️⃣ ALL-DAY STATISTICS (for comparison)"])
    data.append(["═" * 80])
    data.append([])
    
    data.append(["Metric", "BIDS (All Day)", "OFFERS (All Day)"])
    data.append(["Count", f"{int(allday_bid['num_acceptances']):,}", f"{int(allday_offer['num_acceptances']):,}"])
    data.append(["Total Volume (MWh)", f"{int(allday_bid['total_volume_mwh']):,}", f"{int(allday_offer['total_volume_mwh']):,}"])
    data.append(["Volume-Weighted Avg (£/MWh)", f"£{allday_bid['volume_weighted_avg']:.2f}", 
                 f"£{allday_offer['volume_weighted_avg']:.2f}"])
    
    data.append([])
    data.append([])
    
    # Section 3: Monthly Breakdown - BIDs
    data.append(["═" * 80])
    data.append(["3️⃣ MONTHLY BREAKDOWN - BIDS (Morning Peak)"])
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
    data.append(["4️⃣ MONTHLY BREAKDOWN - OFFERS (Morning Peak)"])
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
    
    data.append(["1. Morning Peak Represents ~20% of Daily Balancing Activity"])
    data.append([f"   - BIDs: {100*bid_row['num_acceptances']/allday_bid['num_acceptances']:.1f}% of daily count, "
                 f"{100*bid_row['total_volume_mwh']/allday_bid['total_volume_mwh']:.1f}% of daily volume"])
    data.append([f"   - OFFERs: {100*offer_row['num_acceptances']/allday_offer['num_acceptances']:.1f}% of daily count, "
                 f"{100*offer_row['total_volume_mwh']/allday_offer['total_volume_mwh']:.1f}% of daily volume"])
    data.append([])
    
    data.append(["2. Morning Peak Prices Higher Than All-Day Average"])
    data.append([f"   - BID volume-weighted: £{bid_row['volume_weighted_avg']:.2f}/MWh vs £{allday_bid['volume_weighted_avg']:.2f}/MWh all-day "
                 f"({bid_row['volume_weighted_avg'] - allday_bid['volume_weighted_avg']:+.2f})"])
    data.append([f"   - OFFER volume-weighted: £{offer_row['volume_weighted_avg']:.2f}/MWh vs £{allday_offer['volume_weighted_avg']:.2f}/MWh all-day "
                 f"({offer_row['volume_weighted_avg'] - allday_offer['volume_weighted_avg']:+.2f})"])
    data.append([])
    
    data.append(["3. Morning Demand Ramp Creates Balancing Opportunities"])
    data.append(["   - 5-11 AM: Households wake up, businesses open, demand increases"])
    data.append(["   - More balancing actions needed during demand transition period"])
    data.append(["   - VLP batteries can capitalize on higher morning OFFER prices"])
    data.append([])
    
    data.append(["4. Time Period Details"])
    data.append(["   - Settlement Periods 11-22 = 05:00-11:00 (12 periods × 30 min = 6 hours)"])
    data.append(["   - Weekdays only (Monday-Friday) to focus on business demand patterns"])
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
    for row_num in [8, 9, 28, 29]:
        worksheet.format(f'A{row_num}:J{row_num}', {
            'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.4},
            'textFormat': {'bold': True}
        })
    
    # Column headers - gray background
    for row_num in [12, 33, 50]:
        worksheet.format(f'A{row_num}:J{row_num}', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True}
        })
    
    # Auto-resize columns
    worksheet.columns_auto_resize(0, 9)
    
    print("\n" + "=" * 100)
    print("✅ Morning Peak Analysis added successfully to Google Sheets!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
    print("\nSummary:")
    print(f"  - Morning peak (5-11 AM weekdays) acceptances: {int(bid_row['num_acceptances'] + offer_row['num_acceptances']):,}")
    print(f"  - BIDs: {int(bid_row['num_acceptances']):,} count, {bid_row['total_volume_mwh']/1e6:.2f} TWh")
    print(f"  - OFFERs: {int(offer_row['num_acceptances']):,} count, {offer_row['total_volume_mwh']/1e6:.2f} TWh")
    print(f"  - Morning represents ~20% of daily balancing activity")
    print("=" * 100)

if __name__ == "__main__":
    main()
