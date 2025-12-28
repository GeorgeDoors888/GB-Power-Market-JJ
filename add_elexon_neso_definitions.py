#!/usr/bin/env python3
"""
Add Elexon BSC and NESO official glossary definitions to DATA DICTIONARY sheet
"""

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Initialize gspread
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Get DATA DICTIONARY sheet
worksheet = spreadsheet.worksheet('DATA DICTIONARY')

# ============================================================================
# ELEXON BSC GLOSSARY DEFINITIONS (Official)
# ============================================================================
elexon_definitions = [
    [''],
    ['═══════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', ''],
    ['⚡ ELEXON BSC (BALANCING AND SETTLEMENT CODE) GLOSSARY', '', '', '', '', '', '', ''],
    ['Source: https://www.elexon.co.uk/bsc/glossary/ | Official Elexon definitions', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', ''],
    [''],
    ['Term', 'Official Definition (Elexon)', 'Units', 'Context', 'Update Freq', 'Data Source', 'Related Terms', 'Example'],

    # Core market terms
    ['Settlement Period (SP)', 'A 30-minute trading and settlement interval. Settlement Periods are numbered 1-48 (or 1-46/1-50 on clock change days) and are in local time (GMT/BST). The BSC settlement system compares contracted volumes with metered volumes for each SP.', '30 min', 'Fundamental time unit for all GB electricity trading and settlement', 'Fixed', 'BSC', 'Half-Hourly Period, Settlement Date', 'SP 17 = 08:00-08:30'],

    ['Balancing Mechanism Unit (BMU)', 'The smallest grouping of plant and/or demand that can be independently controlled and metered. BMUs are the "units of trade" in the Balancing Mechanism. Each BMU has a unique ID (e.g., DIDCB6, FFSEN005).', 'N/A', 'Generators, interconnectors, and demand can all be BMUs', 'Static/Updated', 'Elexon', 'BM Unit ID, Lead Party', 'FFSEN005 = Battery VLP'],

    ['Imbalance / Cash-out', 'The difference between a party\'s contracted (traded) energy volumes and their metered energy volumes in a Settlement Period. Parties are "cashed out" at the imbalance price (SBP/SSP) for any imbalance.', 'MWh', 'Financial settlement for energy imbalances', 'Every SP', 'Elexon Settlement', 'NIV, Imbalance Price', '10 MWh imbalance @ £100/MWh = £1,000'],

    ['SBP (System Buy Price)', 'The price (£/MWh) at which the system "buys" energy from parties that are net long (generated/contracted more than they metered). Since BSC Modification P305 (Nov 2015), SBP = SSP (single imbalance price).', '£/MWh', 'Imbalance settlement price for long parties', 'Every SP', 'bmrs_costs', 'SSP, Imbalance Price', '£65.11/MWh'],

    ['SSP (System Sell Price)', 'The price (£/MWh) at which the system "sells" energy to parties that are net short (generated/contracted less than they metered). Since BSC Modification P305 (Nov 2015), SSP = SBP (single imbalance price).', '£/MWh', 'Imbalance settlement price for short parties', 'Every SP', 'bmrs_costs', 'SBP, Imbalance Price', '£65.11/MWh'],

    ['NIV (Net Imbalance Volume)', 'The system-level net imbalance (MWh) for a Settlement Period. Positive NIV = system short (demand > supply), Negative NIV = system long (supply > demand). NIV determines whether SBP or SSP applies (though they\'re equal since P305).', 'MWh', 'System-level supply/demand balance', 'Every SP', 'bmrs_imbalngc', 'SBP, SSP, Imbalance', '+250 MWh = short system'],

    # BMRS datasets
    ['FREQ', 'System frequency dataset. Real-time measurements of GB grid frequency (nominal 50 Hz). Frequency deviations indicate supply/demand imbalances: <50 Hz = insufficient generation, >50 Hz = excess generation.', 'Hz', 'Grid stability indicator, frequency response trading', '~10 seconds', 'bmrs_freq, bmrs_freq_iris', 'Grid Frequency, Stability', '49.95 Hz = slight deficit'],

    ['FUELHH', 'Fuel Type Half-Hourly generation dataset. Outturn generation volumes by fuel type (CCGT, wind, nuclear, coal, etc.) aggregated to half-hourly resolution.', 'MW', 'Fuel mix analysis, renewables tracking', '30 minutes', 'bmrs_fuelinst', 'Generation Mix, Fuel Type', 'Wind: 12,500 MW'],

    ['MID (Market Index Data)', 'Market Index prices (£/MWh) representing wholesale day-ahead and within-day traded prices. Used for BM-MID spread analysis (balancing vs wholesale price differential).', '£/MWh', 'Wholesale price reference', 'Real-time', 'bmrs_mid', 'Wholesale Price, BM-MID Spread', '£40.41/MWh'],

    ['BOAL (Bid-Offer Acceptance Levels)', 'Balancing Mechanism acceptance volumes and times. Shows which BMU bids/offers National Grid accepted to balance the system. NOTE: Standard BOAL data lacks acceptance prices (must be matched with BOD).', 'MWh', 'Balancing actions, dispatch analysis', '~2-4 hours', 'bmrs_boalf', 'BOD, Acceptances, Dispatch', 'FFSEN005: 50 MWh accepted'],

    ['BOD (Bid-Offer Data)', 'All bid and offer price/volume pairs submitted by BMUs for each Settlement Period. Contains the "menu" of prices generators offer to increase (offer) or decrease (bid) output.', '£/MWh, MW', 'Price discovery, revenue analysis', '~30-60 min', 'bmrs_bod', 'BOAL, Offers, Bids', '£85/MWh offer, 100 MW'],

    ['PN (Physical Notifications)', 'Physical Notification levels (MW) submitted by BMUs indicating their expected generation/demand levels. Updated throughout the day as plans change.', 'MW', 'Generation schedules, unit commitment', '~30-60 min', 'bmrs_pn', 'FPN, Final Physical Notification', '485 MW expected output'],

    ['NETBSAD (Net Balancing System Adjustment Data)', 'Settlement data showing balancing costs and volumes. Used to calculate the system adjustment cost passed through to all parties. Includes buy/sell volumes and energy/system flags.', 'MWh, £', 'Settlement calculations, cost allocation', '~2-4 hours', 'bmrs_disbsad', 'Balancing Costs, Settlement', '£1.2M system cost'],

    # Market processes
    ['Gate Closure', 'The deadline (1 hour before real-time in GB) after which parties cannot change their notified positions. After Gate Closure, only the Balancing Mechanism can adjust positions.', 'Timestamp', 'Trading deadline, BM activation point', 'Every hour', 'BSC Procedures', 'BM Window, Trading Window', '13:00 Gate Closure for 14:00-14:30 SP'],

    ['Balancing Mechanism (BM)', 'The mechanism by which National Grid ESO (now NESO) balances supply and demand in real-time. BMUs submit bids/offers (BOD), and the ESO accepts (BOAL) the most economic actions to maintain system balance.', 'N/A', 'Real-time system balancing', 'Continuous', 'NESO Operations', 'BOD, BOAL, Dispatch', 'Accept 50 MWh @ £85/MWh'],

    ['Lead Party', 'The BSC party responsible for a BMU. Submits Physical Notifications, Bid-Offer Data, and receives settlement payments/charges. Often a trading company or aggregator (e.g., Flexitricity, Limejump).', 'N/A', 'Commercial responsibility for BMUs', 'Static/Updated', 'Elexon', 'BMU, VLP, Trading Party', 'Flexitricity leads FFSEN005'],

    ['Virtual Lead Party (VLP)', 'Unofficial term for batteries and demand-side response assets that actively trade in the Balancing Mechanism. VLPs submit dynamic bid-offer pairs and earn revenue from BM acceptances.', 'N/A', 'Battery arbitrage, DSR revenue', 'N/A', 'Industry Term', 'Lead Party, BMU, Battery', 'FFSEN005, FBPGM002'],

    # Settlement and pricing
    ['Energy Weighted Average Price (EWAP)', 'Calculated by dividing total cashflow (£) by total volume (MWh). Used to summarize average BM prices. EWAP Offer = Σ(offer cashflow)/Σ(offer MWh), EWAP Bid = Σ(bid cashflow)/Σ(bid MWh).', '£/MWh', 'Average BM price summary metric', 'Dashboard calc', 'bmrs_boav, bmrs_ebocf', 'BM Cashflow, Average Price', 'EWAP Offer: £85.50/MWh'],

    ['BM Cashflow', 'Total financial value of Balancing Mechanism actions. Calculated as Σ(acceptance volume × acceptance price). Includes both offers (positive cashflow) and bids (negative cashflow).', '£', 'Total BM market activity', 'Every SP', 'bmrs_ebocf, bmrs_boalf_complete', 'EWAP, Revenue', '£232.3k/day'],

    ['Dispatch Intensity', 'The number of BM acceptances per hour. High dispatch intensity indicates an active balancing period with frequent system adjustments. Typical range: 5-30 actions/hour.', 'Actions/hr', 'System activity level', 'Dashboard calc', 'bmrs_boalf', 'Workhorse Index, BM Activity', '68.2 actions/hr'],

    ['Workhorse Index', 'The percentage of Settlement Periods in which a BMU had BM activity. Calculated as (active SPs / 48) × 100. High workhorse index = frequent dispatch.', '%', 'Unit utilization metric', 'Dashboard calc', 'bmrs_boalf', 'Dispatch Intensity, Utilization', '95% = 46/48 SPs active'],

    ['']
]

# ============================================================================
# NESO GLOSSARY DEFINITIONS (Official)
# ============================================================================
neso_definitions = [
    [''],
    ['═══════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', ''],
    ['⚡ NESO (NATIONAL ENERGY SYSTEM OPERATOR) GLOSSARY', '', '', '', '', '', '', ''],
    ['Source: https://www.neso.energy/industry-information/connections/help-and-support/glossary-terms', '', '', '', '', '', '', ''],
    ['Formerly National Grid ESO | Operates GB transmission system and Balancing Mechanism', '', '', '', '', '', '', ''],
    ['═══════════════════════════════════════════════════════════════════════════════', '', '', '', '', '', '', ''],
    [''],
    ['Term', 'Official Definition (NESO)', 'Units', 'Context', 'Update Freq', 'Data Source', 'Related Terms', 'Example'],

    ['National Energy System Operator (NESO)', 'The independent public corporation responsible for operating the GB electricity and gas transmission systems. Formed in 2024, taking over from National Grid ESO. Runs the Balancing Mechanism and ensures system security.', 'N/A', 'System operator for GB energy', 'N/A', 'NESO', 'ESO, System Operator', 'NESO Control Room'],

    ['Balancing Mechanism (BM)', 'The market mechanism through which NESO balances electricity supply and demand in real-time. Participants submit bid-offer prices, and NESO accepts the most economic actions after Gate Closure to maintain system balance at 50 Hz.', 'N/A', 'Real-time balancing process', 'Continuous', 'NESO Operations', 'BOD, BOAL, Gate Closure', 'Accept cheapest offers first'],

    ['System Frequency', 'The frequency of the AC electricity on the GB transmission system. Nominally 50 Hz. Frequency rises when generation > demand (system long), falls when generation < demand (system short). NESO must maintain 49.5-50.5 Hz.', 'Hz', 'Primary stability indicator', '~10 seconds', 'bmrs_freq', 'Grid Stability, Frequency Response', '50.02 Hz = balanced system'],

    ['Gate Closure', 'The point in time (1 hour before real-time) after which contract notifications are "locked in" and only BM actions can change positions. For a 14:00-14:30 Settlement Period, Gate Closure is at 13:00.', 'Timestamp', 'Trading deadline', 'Every hour', 'BSC Procedures', 'BM Window, Notification Deadline', '13:00 for 14:00 SP'],

    ['Balancing Services', 'Ancillary services procured by NESO to maintain system stability and security. Includes frequency response, reserve, reactive power, and black start. Separate from the energy Balancing Mechanism.', 'Various', 'System security services', 'Continuous', 'NESO Procurement', 'Frequency Response, Reserve', 'Dynamic Containment'],

    ['Demand Turn-Up (DTU)', 'A demand-side service where large consumers increase electricity consumption when requested by NESO. Used to absorb excess generation (e.g., high wind output). Paid for availability + utilization.', 'MW', 'Demand-side balancing', 'Event-based', 'NESO', 'DSR, Balancing Services', 'Industrial consumer increases load'],

    ['Distribution Network Operator (DNO)', 'Companies that own and operate the local electricity distribution networks (11 kV to 132 kV). There are 14 DNO license areas in GB. DNOs manage connections and charge Distribution Use of System (DUoS) charges.', 'N/A', 'Local network operators', 'Static', 'Ofgem', 'DUoS, MPAN, Connection', 'UKPN, SSEN, NGED'],

    ['MPAN (Metering Point Administration Number)', 'A unique 13-digit identifier for each electricity supply point. The first 2 digits indicate the DNO region (e.g., "10" = UKPN Eastern, "14" = NGED West Midlands). Used for DUoS charge allocation.', '13 digits', 'Supply point identifier', 'Static', 'DNO', 'DNO, DUoS, Metering', '1405566778899'],

    ['DUoS (Distribution Use of System)', 'Charges levied by DNOs for use of the local distribution network. Vary by DNO, voltage level, and time of day (Red/Amber/Green bands). Critical cost component for battery storage.', 'p/kWh', 'Distribution network charges', 'Annual review', 'DNO Tariffs', 'DNO, MPAN, Time Bands', 'Red: 4.837 p/kWh'],

    ['Grid Code', 'The technical code governing the connection and operation of generation and demand on the GB transmission system. Contains technical definitions, compliance obligations, and operating standards.', 'N/A', 'Technical compliance code', 'Periodic updates', 'NESO', 'Connection Requirements', 'Grid Code OC6 (frequency)'],

    ['Transmission Constraint', 'A limit on power flow across the transmission network due to thermal, voltage, or stability limits. NESO must constrain (pay generators to turn down in one area and turn up in another) to manage constraints. Major cost driver.', 'MW', 'Network capacity limit', 'Real-time', 'NESO', 'Constraint Costs, BOAs', 'Scotland → England limit'],

    ['Balancing Mechanism Start-Up (BMSU)', 'The action of starting a generation unit specifically for Balancing Mechanism purposes (not pre-synchronized). Paid a fixed £ fee plus energy costs. Common for gas turbines.', '£', 'Unit start-up payment', 'Event-based', 'BM Payments', 'BOAs, Start-up Costs', '£5,000 start-up fee'],

    ['Final Physical Notification (FPN)', 'The last Physical Notification submitted by a BMU before Gate Closure. Represents the BMU\'s expected generation/demand position and is used as the baseline for BM actions.', 'MW', 'Pre-Gate Closure position', 'Hourly', 'bmrs_pn', 'PN, Gate Closure', '485 MW FPN'],

    ['']
]

# ============================================================================
# FIND INSERT POSITION (after existing definitions)
# ============================================================================
print("📍 Finding insertion point...")
all_data = worksheet.get_all_values()
insert_row = len(all_data) + 1  # Append at end

# Combine all new definitions
all_new_defs = elexon_definitions + neso_definitions

# Normalize to 8 columns (matching DATA DICTIONARY structure)
for row in all_new_defs:
    while len(row) < 8:
        row.append('')
    row[:] = row[:8]

# ============================================================================
# INSERT DEFINITIONS
# ============================================================================
print(f"📝 Adding {len(all_new_defs)} rows of Elexon + NESO definitions...")

start_cell = f'A{insert_row}'
end_cell = f'H{insert_row + len(all_new_defs) - 1}'
range_name = f'{start_cell}:{end_cell}'

worksheet.update(values=all_new_defs, range_name=range_name)

# ============================================================================
# FORMAT NEW SECTIONS
# ============================================================================
print("🎨 Applying formatting...")

# Black background for section headers
section_header_rows = []
for idx, row in enumerate(all_new_defs):
    if '═══════' in row[0]:
        section_header_rows.append(insert_row + idx)

if section_header_rows:
    requests = []
    for row_num in section_header_rows:
        requests.append({
            'repeatCell': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex': row_num - 1,
                    'endRowIndex': row_num,
                    'startColumnIndex': 0,
                    'endColumnIndex': 8
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0, 'green': 0, 'blue': 0},
                        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'bold': True}
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })

    spreadsheet.batch_update({'requests': requests})

print(f"✅ DATA DICTIONARY updated! 📚")
print(f"   • Added {len(elexon_definitions)} Elexon BSC definitions")
print(f"   • Added {len(neso_definitions)} NESO definitions")
print(f"   • Total new glossary entries: {len(all_new_defs)}")
