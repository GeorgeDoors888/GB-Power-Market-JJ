#!/usr/bin/env python3
"""
Add data validation notes (tooltips) to header cells in Live Dashboard v2
Similar to BtM Calculator style - hover tooltips with definitions
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Initialize gspread
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
worksheet = spreadsheet.worksheet('Live Dashboard v2')

print("📝 Adding tooltips to header cells...")

# Define tooltips for each header/key cell
tooltips = {
    # Market Metrics section headers
    'A5': 'BM-MID SPREAD: Difference between Balancing Mechanism price and Market Index (wholesale) price. Positive spread indicates system stress. Source: bmrs_costs - bmrs_mid. Updates every 5 minutes.',
    'C5': 'MARKET INDEX PRICE: Wholesale electricity price from day-ahead and within-day markets. Also called MID (Market Index Data). Source: bmrs_mid table. Updates every 5 minutes.',

    # Combined KPI section header
    'K12': 'MARKET DYNAMICS - 24 HOUR VIEW: Real-time system prices, BM financial metrics, and grid balancing activity. All KPIs use 48 half-hourly settlement periods. Sparklines show 6-column wide trends. Updates every 5 minutes.',

    # Individual KPI rows (column K - KPI names)
    'K13': 'REAL-TIME IMBALANCE PRICE: Current electricity settlement price (£/MWh). SSP=SBP since Nov 2015 (single pricing). Typical: £40-100/MWh, Stress: £100-400/MWh. Source: bmrs_costs. This is the price batteries/generators receive for balancing actions.',
    'K14': '7-DAY AVERAGE: Rolling 7-day mean system price. Smooths out daily volatility. Used for deviation calculations. Source: bmrs_costs 7-day window.',
    'K15': '30-DAY AVERAGE: Rolling 30-day mean system price. Shows medium-term pricing trends. Source: bmrs_costs 30-day window.',
    'K16': 'DEVIATION FROM 7D: Percentage change vs 7-day average. Formula: (Current - 7d avg) / 7d avg × 100. Positive = above average (high price opportunity). Typical: -20% to +50%.',
    'K17': '30-DAY HIGH: Maximum system price in last 30 days. Indicates peak stress events. VLP units target £70+/MWh for aggressive discharge. Source: MAX(bmrs_costs).',
    'K18': '30-DAY LOW: Minimum system price in last 30 days. Can be negative during oversupply. Indicates charging opportunities. Source: MIN(bmrs_costs).',
    'K19': 'TOTAL BM CASHFLOW: Sum of all balancing mechanism cashflows (£k). Formula: Σ(Volume × Price) for all acceptances. Typical: £50k-500k/day. High stress days: £1M+. Source: bmrs_ebocf + bmrs_boav.',
    'K20': 'EWAP OFFER: Energy-Weighted Average Price for offers (£/MWh). Formula: Σ(Offer £) / Σ(Offer MWh). Shows average price generators receive for increasing output. Typical: £50-150/MWh. Source: bmrs_ebocf / bmrs_boav.',
    'K21': 'EWAP BID: Energy-Weighted Average Price for bids (£/MWh). Formula: Σ(Bid £) / Σ(Bid MWh). Shows average price for decreasing output. Typical: £30-80/MWh. Source: bmrs_ebocf / bmrs_boav.',
    'K22': 'DISPATCH INTENSITY: Balancing actions per hour (count/hr). Formula: Total Acceptances / Hours. Typical: 5-30/hr, Stress: 60+/hr. High intensity = volatile system requiring frequent interventions. Source: bmrs_boalf.',

    # VLP Revenue section header
    'L54': 'VLP REVENUE ANALYSIS: Virtual Lead Party (battery) operators. 28-day rolling revenue and margin analysis. Shows top 10 operators by total MWh dispatched. Updates every 5 minutes.',
    'M55': 'OPERATOR NAME: VLP unit identifier (bmUnitId). Examples: FFSEN005 (likely Gresham House/Harmony), FBPGM002 (Flexgen). Source: bmrs_boalf.',
    'N55': 'TOTAL MWH: Total energy dispatched in 28-day period. Sum of all acceptance volumes. Typical: 5,000-20,000 MWh/month. Source: Σ(bmrs_boalf.acceptanceVolume).',
    'O55': 'REVENUE (£k): Gross revenue from balancing actions. Formula: Σ(Volume × acceptancePrice). Typical: £500k-5,000k/month. High-value events (Oct 17-23): £80k/day. Source: bmrs_boalf_complete.',
    'P55': 'MARGIN (£/MWH): Average revenue per MWh dispatched. Formula: Revenue / Total MWh. Typical: £20-150/MWh. Premium events: £500+/MWh. Key profitability metric for battery arbitrage.',
    'Q55': 'BM PRICE: Average imbalance price received. Weighted average system price during dispatch periods. Source: bmrs_costs.',
    'R55': 'WHOLESALE: Average wholesale price (MID). Shows opportunity cost vs day-ahead market. Source: bmrs_mid.',

    # Active Outages section
    'G25': 'ACTIVE OUTAGES: Generation units offline due to planned/unplanned outages. Top 15 by unavailable capacity. REMIT (Regulation on Energy Market Integrity and Transparency) messages from Elexon. Updates every 5 minutes. Source: bmrs_remit_unavailability.',
    'G26': 'ASSET NAME: Generator/unit identifier (bmUnitId). Examples: DIDCB6 (Didcot CCGT), DRAXX8 (Drax coal). Source: bmrs_remit_unavailability.',
    'H26': 'FUEL TYPE: Generation technology. 🏭 CCGT (gas turbine), ⚛️ Nuclear, 🌬️ Wind, 🔋 Pumped Storage, 🇫🇷 IFA (France interconnector). Source: bmrs_remit_unavailability.fuelType.',
    'I26': 'UNAVAIL (MW): Offline capacity. Amount of MW currently unavailable. Source: bmrs_remit_unavailability.unavailableCapacity.',
    'J26': 'NORMAL (MW): Installed capacity. Total MW when operational. Source: bmrs_remit_unavailability.normalCapacity.',
    'K26': 'CAUSE: Outage reason. Examples: "Planned outage", "Unplanned technical", "Fuel shortage". Truncated to 30 chars. Source: bmrs_remit_unavailability.cause.',

    # Interconnectors section
    'G13': 'INTERCONNECTORS: Cross-border electricity links. Shows current power flow (MW). Positive = import to GB, Negative = export from GB. Updates every 5 minutes via IRIS real-time stream. Source: bmrs_indgen_iris.',

    # Data freshness indicator
    'A2': 'DATA FRESHNESS: IRIS real-time data status. Shows last update time and staleness warning. Green = fresh (<10 min), Yellow = stale (10-30 min), Red = very stale (>30 min). Updates every 5 minutes.',
    'AA1': 'LAST UPDATE TIMESTAMP: Script execution time. Format: DD/MM HH:MM. Should update every 5 minutes. If frozen, check cron job: crontab -l | grep update_live_metrics',
}

# Add notes to cells
print(f"📝 Adding {len(tooltips)} tooltips...")
requests = []

for cell, note_text in tooltips.items():
    # Get the sheet ID
    sheet_id = worksheet.id

    # Parse cell reference (e.g., 'K12' -> row 11, col 10 in 0-indexed)
    col_letter = ''.join(filter(str.isalpha, cell))
    row_num = int(''.join(filter(str.isdigit, cell)))

    # Convert column letter to index (A=0, B=1, ..., Z=25, AA=26, etc.)
    col_index = 0
    for i, char in enumerate(reversed(col_letter)):
        col_index += (ord(char) - ord('A') + 1) * (26 ** i)
    col_index -= 1  # Convert to 0-indexed

    # Create note request
    requests.append({
        'updateCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': row_num - 1,
                'endRowIndex': row_num,
                'startColumnIndex': col_index,
                'endColumnIndex': col_index + 1
            },
            'rows': [{
                'values': [{
                    'note': note_text
                }]
            }],
            'fields': 'note'
        }
    })

    print(f"  ✅ {cell}: {note_text[:50]}...")

# Execute batch update
print("\n⚡ Executing batch update...")
spreadsheet.batch_update({'requests': requests})

print("\n✅ Tooltips added successfully!")
print(f"📊 Total tooltips: {len(tooltips)}")
print(f"🔗 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print("\n💡 Hover over header cells to see definitions!")
