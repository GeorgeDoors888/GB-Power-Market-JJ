#!/usr/bin/env python3
"""
Add Bid vs Offer Definitions to Google Sheets
Adds a comprehensive definitions sheet explaining the difference between BIDs and OFFERs
"""

import gspread
from google.oauth2.service_account import Credentials
import time

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def main():
    print("=" * 100)
    print("📖 Adding Bid vs Offer Definitions to Google Sheets")
    print("=" * 100)
    
    # Authenticate
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID)
    
    # Create new worksheet
    try:
        worksheet = sheet.worksheet("BID_OFFER_Definitions")
        print("⚠️  Worksheet 'BID_OFFER_Definitions' already exists - will clear and update")
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print("✅ Creating new worksheet 'BID_OFFER_Definitions'")
        worksheet = sheet.add_worksheet(title="BID_OFFER_Definitions", rows=100, cols=10)
    
    # Header
    data = [
        ["⚡ DEFINITIONS — BID vs OFFER", "", "", "", "", ""],
        ["Critical Understanding: Opposite Market Actions", "", "", "", "", ""],
        [""],
        ["📊 CORE DEFINITIONS", "", "", "", "", ""],
        ["Term", "Direction", "What Participant Does", "Financial Flow", "Typical Tech", "Price Sign"],
        [
            "OFFER",
            "↑ Increase generation",
            "Generates or exports MORE power",
            "ESO PAYS participant",
            "Gas, battery discharge, interconnector",
            "POSITIVE (£/MWh)"
        ],
        [
            "BID",
            "↓ Reduce generation",
            "Generates or exports LESS power (or consumes more)",
            "Participant PAYS ESO",
            "Wind, battery charge, demand response",
            "NEGATIVE (£/MWh)"
        ],
        [""],
        ["💡 REAL-WORLD EXAMPLES", "", "", "", "", ""],
        [""],
        ["Example 1: Gas Generator OFFER", "", "", "", "", ""],
        ["• Gas generator offers to INCREASE generation at £80/MWh", "", "", "", "", ""],
        ["• ESO buys that energy to fill supply shortfall", "", "", "", "", ""],
        ["• Generator RECEIVES £80/MWh from ESO", "", "", "", "", ""],
        ["• Result: Positive price, ESO pays generator", "", "", "", "", ""],
        [""],
        ["Example 2: Wind Farm BID", "", "", "", "", ""],
        ["• Wind farm bids to REDUCE generation at –£100/MWh", "", "", "", "", ""],
        ["• ESO accepts bid to reduce excess supply", "", "", "", "", ""],
        ["• Wind farm PAYS ESO £100/MWh to be turned down", "", "", "", "", ""],
        ["• Why? Wind farm still receives CfD subsidy, so paying to curtail is profitable", "", "", "", "", ""],
        ["• Result: Negative price, generator pays ESO", "", "", "", "", ""],
        [""],
        ["📖 EXAMPLES BY TECHNOLOGY", "", "", "", "", ""],
        ["Technology", "Typical Action", "Behaviour", "Example Price (£/MWh)", "Reason", ""],
        [
            "Gas CCGT",
            "Offer (up)",
            "Generate more",
            "+70 → +150",
            "Fuel + profit margin",
            ""
        ],
        [
            "Battery",
            "Bid (charge) / Offer (discharge)",
            "Arbitrage",
            "–20 (charge) / +90 (discharge)",
            "Exploiting price spread",
            ""
        ],
        [
            "Wind Farm (CfD)",
            "Bid (down)",
            "Pay to curtail",
            "–100 → –1000",
            "Keeps subsidy income",
            ""
        ],
        [
            "Interconnector",
            "Offer (import)",
            "Bring power from abroad",
            "+100 → +500",
            "Scarcity periods",
            ""
        ],
        [
            "Demand Response",
            "Bid (up consumption)",
            "Increase usage",
            "–10 → –50",
            "Paid to consume excess",
            ""
        ],
        [""],
        ["🧾 HOW BALANCING MECHANISM PRICES ARE RECORDED", "", "", "", "", ""],
        [""],
        ["When National Grid ESO accepts a bid or offer, it becomes an Accepted Balancing Action", "", "", "", "", ""],
        ["Published by Elexon in BOALF (Bid Offer Acceptance Log Final) tables", "", "", "", "", ""],
        [""],
        ["Field", "Description", "Units", "", "", ""],
        ["acceptanceId", "Unique ID for the balancing action", "—", "", "", ""],
        ["bmUnitID", "Unit that delivered the action", "—", "", "", ""],
        ["acceptanceType", "BID or OFFER", "—", "", "", ""],
        ["acceptancePrice", "Price accepted for the action", "£/MWh", "", "", ""],
        ["acceptanceVolume", "MWh accepted", "MWh", "", "", ""],
        ["timeFrom / timeTo", "Start and end of acceptance", "datetime", "", "", ""],
        [""],
        ["🔢 PRICE INTERPRETATION GUIDE", "", "", "", "", ""],
        ["Situation", "Typical £/MWh", "Explanation", "", "", ""],
        [
            "Positive Offer",
            "+£20 → +£300",
            "ESO buying extra power during tight periods (generators paid)",
            "", "", ""
        ],
        [
            "Negative Bid",
            "–£5 → –£1000",
            "Generators paying ESO to curtail (common for wind)",
            "", "", ""
        ],
        [
            "Zero Bid/Offer",
            "£0",
            "Non-commercial actions (system tests, constraint management)",
            "", "", ""
        ],
        [""],
        ["🧠 ECONOMIC IMPACT BY ACTOR", "", "", "", "", ""],
        ["Actor", "Action", "Financial Effect", "", "", ""],
        ["ESO", "Buys Offers", "Pays generators to increase output (cost)", "", "", ""],
        ["ESO", "Accepts Bids", "Receives payment from generators who reduce output (revenue)", "", "", ""],
        ["Generator", "Offers", "Earns extra revenue", "", "", ""],
        ["Generator", "Bids", "Pays ESO but may still profit via subsidies", "", "", ""],
        ["Battery / VLP", "Both", "Arbitrages difference between BOALF and MID", "", "", ""],
        [""],
        ["📊 HOW AVERAGES ARE CALCULATED", "", "", "", "", ""],
        [""],
        ["Weighted Average Formula:", "", "", "", "", ""],
        ["SUM(acceptancePrice × acceptanceVolume) / SUM(acceptanceVolume)", "", "", "", "", ""],
        [""],
        ["In 2025 data:", "", "", "", "", ""],
        ["• Negative bids (–£100 to –£20/MWh) occur frequently (wind, storage)", "", "", "", "", ""],
        ["• Positive offers (£60–£200/MWh) occur during scarcity", "", "", "", "", ""],
        ["• Because bids outnumber offers (440K vs 354K), negative prices drag average down", "", "", "", "", ""],
        ["• This explains why BOALF average can be lower than MID wholesale price", "", "", "", "", ""],
        [""],
        ["⚠️ CRITICAL WARNINGS", "", "", "", "", ""],
        [""],
        ["1. NEVER average BIDs and OFFERs together without context — they are opposite actions", "", "", "", "", ""],
        ["2. Separate analysis required — BIDs and OFFERs have different price dynamics", "", "", "", "", ""],
        ["3. Volume-weighted averages — High-volume low-price events can dominate the mean", "", "", "", "", ""],
        ["4. Extreme prices are rare — ±£1000/MWh appears during stress events but <1% of actions", "", "", "", "", ""],
        [""],
        ["📈 2025 ACTUAL DATA (24 MONTHS)", "", "", "", "", ""],
        [""],
        ["OFFERS (Increase Output):", "", "", "", "", ""],
        ["• Average Price: £88.58/MWh", "", "", "", "", ""],
        ["• Count: 353,828 acceptances", "", "", "", "", ""],
        ["• Premium over MID wholesale: +£16.95/MWh", "", "", "", "", ""],
        ["• October 2025: £111.12/MWh (23,970 acceptances)", "", "", "", "", ""],
        [""],
        ["BIDS (Decrease Output):", "", "", "", "", ""],
        ["• Average Price: -£1.63/MWh (NEGATIVE!)", "", "", "", "", ""],
        ["• Count: 440,306 acceptances (MORE than offers)", "", "", "", "", ""],
        ["• Discount vs MID wholesale: -£78.63/MWh", "", "", "", "", ""],
        ["• October 2025: -£8.71/MWh (48,273 acceptances)", "", "", "", "", ""],
        [""],
        ["KEY INSIGHT: More BIDs than OFFERs = UK grid dominated by renewable excess, not scarcity", "", "", "", "", ""],
        [""],
        [""],
        ["Last Updated: 2025-12-16", "", "", "", "", ""],
        ["Source: inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete", "", "", "", "", ""],
    ]
    
    # Write data
    print(f"✍️  Writing {len(data)} rows to worksheet...")
    worksheet.update(values=data, range_name='A1')
    time.sleep(2)
    
    # Format header
    print("🎨 Applying formatting...")
    worksheet.format('A1:F1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    time.sleep(1)
    
    # Format section headers
    section_rows = [4, 9, 23, 33, 46, 58, 65, 72, 80]
    for row in section_rows:
        worksheet.format(f'A{row}:F{row}', {
            'backgroundColor': {'red': 1, 'green': 0.9, 'blue': 0.6},
            'textFormat': {'bold': True, 'fontSize': 11}
        })
        time.sleep(0.5)
    
    # Format definition table
    worksheet.format('A5:F7', {
        'borders': {
            'top': {'style': 'SOLID'},
            'bottom': {'style': 'SOLID'},
            'left': {'style': 'SOLID'},
            'right': {'style': 'SOLID'}
        }
    })
    time.sleep(1)
    
    # Bold first column (labels)
    worksheet.format('A:A', {'textFormat': {'bold': True}})
    time.sleep(1)
    
    # Set column widths using resize_columns
    worksheet.columns_auto_resize(0, 5)
    
    print("=" * 100)
    print("✅ Bid vs Offer Definitions added successfully!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}")
    print("=" * 100)

if __name__ == "__main__":
    main()
