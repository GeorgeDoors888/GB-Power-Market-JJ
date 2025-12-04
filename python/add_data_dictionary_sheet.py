#!/usr/bin/env python3
"""
Add Data Dictionary Sheet to Dashboard V3

Creates comprehensive data dictionary with:
1. All BOD/BOALF definitions
2. All £ price/revenue schemas from the project
3. Adds cell notes to Dashboard V3 balancing summary
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import sys

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
CREDS_FILE = '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json'

# Cell note definitions for Dashboard V3
CELL_NOTES = {
    'E44': '''Units Submitting: The number of individual Balancing Mechanism Units (such as power generators or large consumers) for which bid-offer data has been submitted in a given time period.''',
    
    'E45': '''Bid-Offer Pairs: The number of bid and offer price pairs submitted for these units. Each pair typically includes a price in £/MWh and a quantity (level) in MW at which the participant is willing to increase (offer) or decrease (bid) their generation/consumption relative to their Final Physical Notification (FPN).''',
    
    'E46': '''Avg Bid Price: The average price across all submitted bids. A bid price is the price the System Operator pays the unit to reduce its output or increase its consumption.''',
    
    'E47': '''Avg Offer Price: The average price across all submitted offers. An offer price is the price the System Operator pays the unit to increase its output or decrease its consumption.''',
    
    'E48': '''Avg Spread: The average difference between the Offer Price and the Bid Price within each submitted pair, or the average difference across the market. The spread represents a potential cost or gain for the system operator when balancing supply and demand.'''
}

def get_clients():
    """Initialize Google Sheets and BigQuery clients"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=credentials)
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")
    return sheets_service, bq_client


def add_cell_notes(sheets_service):
    """Add notes to BOD/BOALF cells in Dashboard V3"""
    print("📝 Adding cell notes to Dashboard V3...")
    
    try:
        requests = []
        
        for cell_ref, note_text in CELL_NOTES.items():
            # Convert A1 notation to row/col (e.g., E44 → row 43, col 4)
            col = ord(cell_ref[0]) - ord('A')
            row = int(cell_ref[1:]) - 1
            
            requests.append({
                'updateCells': {
                    'range': {
                        'sheetId': 1471864390,  # Dashboard V3 sheet ID
                        'startRowIndex': row,
                        'endRowIndex': row + 1,
                        'startColumnIndex': col,
                        'endColumnIndex': col + 1
                    },
                    'rows': [{
                        'values': [{
                            'note': note_text
                        }]
                    }],
                    'fields': 'note'
                }
            })
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': requests}
        ).execute()
        
        print(f"   ✅ Added {len(CELL_NOTES)} cell notes")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def create_data_dictionary_sheet(sheets_service, bq_client):
    """Create comprehensive Data Dictionary sheet"""
    print("📚 Creating Data Dictionary sheet...")
    
    try:
        # Check if sheet exists, create if not
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        sheet_exists = any(s['properties']['title'] == 'Data Dictionary' 
                          for s in spreadsheet['sheets'])
        
        if not sheet_exists:
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': 'Data Dictionary',
                                'gridProperties': {
                                    'rowCount': 200,
                                    'columnCount': 10,
                                    'frozenRowCount': 1
                                }
                            }
                        }
                    }]
                }
            ).execute()
            print("   ✅ Created Data Dictionary sheet")
        else:
            print("   ℹ️  Data Dictionary sheet already exists")
        
        # Build data dictionary content
        data = []
        
        # Header
        data.append([
            '📚 GB POWER MARKET DATA DICTIONARY',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append([
            'Last Updated: 2025-12-04',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append(['', '', '', '', '', '', '', '', '', ''])
        
        # Section 1: BALANCING MECHANISM (BOD/BOALF)
        data.append([
            '⚡ BALANCING MECHANISM TERMS',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append([
            'Term', 'Definition', 'Unit', 'Source Table', 'Notes'
        ])
        
        bm_terms = [
            ['Units Submitting', 'The number of individual Balancing Mechanism Units (such as power generators or large consumers) for which bid-offer data has been submitted in a given time period.', 'Count', 'bmrs_bod', 'BMU can be generator, storage, or demand'],
            
            ['Bid-Offer Pairs', 'The number of bid and offer price pairs submitted for these units. Each pair typically includes a price in £/MWh and a quantity (level) in MW at which the participant is willing to increase (offer) or decrease (bid) their generation/consumption relative to their Final Physical Notification (FPN).', 'Count', 'bmrs_bod', 'Each unit can submit multiple pairs at different price levels'],
            
            ['Avg Bid Price', 'The average price across all submitted bids. A bid price is the price the System Operator pays the unit to reduce its output or increase its consumption.', '£/MWh', 'bmrs_bod', 'Sentinel value 9999 = no bid submitted'],
            
            ['Avg Offer Price', 'The average price across all submitted offers. An offer price is the price the System Operator pays the unit to increase its output or decrease its consumption.', '£/MWh', 'bmrs_bod', 'Sentinel value 9999 = no offer submitted'],
            
            ['Avg Spread', 'The average difference between the Offer Price and the Bid Price within each submitted pair, or the average difference across the market. The spread represents a potential cost or gain for the system operator when balancing supply and demand.', '£/MWh', 'bmrs_bod (calculated)', 'Spread = Offer Price - Bid Price'],
            
            ['Accepted Actions', 'Total number of bid or offer acceptances where the System Operator instructed a BMU to change output.', 'Count', 'bmrs_boalf', 'Each action has unique acceptanceNumber'],
            
            ['Active Units', 'Number of distinct BMUs that received at least one acceptance instruction.', 'Count', 'bmrs_boalf', 'Subset of all registered BMUs'],
            
            ['Increase MW', 'Total megawatts of generation increase instructions (levelTo > levelFrom).', 'MW', 'bmrs_boalf', 'Used when system needs more power'],
            
            ['Decrease MW', 'Total megawatts of generation decrease instructions (levelTo < levelFrom).', 'MW', 'bmrs_boalf', 'Used when system has excess power'],
            
            ['Avg Change', 'Average size of each acceptance instruction in megawatts.', 'MW', 'bmrs_boalf (calculated)', 'Typically small adjustments (±1 MW)'],
        ]
        
        data.extend(bm_terms)
        data.append(['', '', '', '', ''])
        
        # Section 2: PRICE & REVENUE SCHEMAS
        data.append([
            '💰 PRICE & REVENUE SCHEMAS',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append([
            'Schema/Field', 'Description', 'Unit', 'Source', 'Typical Range'
        ])
        
        price_schemas = [
            ['systemSellPrice (SSP)', 'Price at which the System Operator sells energy to the market (system long = excess generation).', '£/MWh', 'bmrs_mid, bmrs_mid_iris', '£20-£200/MWh (can go negative)'],
            
            ['systemBuyPrice (SBP)', 'Price at which the System Operator buys energy from the market (system short = deficit).', '£/MWh', 'bmrs_mid, bmrs_mid_iris', '£20-£200/MWh (typically higher than SSP)'],
            
            ['imbalancePrice', 'Price charged to parties out of balance (SSP if short, SBP if long).', '£/MWh', 'bmrs_mid (calculated)', 'Equals SSP or SBP depending on position'],
            
            ['DUoS Rates', 'Distribution Use of System charges for using local electricity networks. Varies by voltage level and time band (Red/Amber/Green).', 'p/kWh', 'gb_power.duos_unit_rates', 'HV Red: 1-5 p/kWh, Green: 0.01-0.1 p/kWh'],
            
            ['TNUoS', 'Transmission Network Use of System charges for using National Grid transmission network.', '£/MWh', 'Configuration', '£0-20/MWh (set to £0 from Dec 2025)'],
            
            ['BSUoS', 'Balancing Services Use of System - cost of balancing the grid.', '£/MWh', 'Configuration', '£3-8/MWh'],
            
            ['CCL', 'Climate Change Levy - tax on energy usage.', '£/MWh', 'Configuration', '£0.775/MWh'],
            
            ['RO', 'Renewables Obligation - support scheme for renewable generation.', '£/MWh', 'Configuration', '£6.83/MWh'],
            
            ['FIT', 'Feed-in Tariff - payment for renewable generation.', '£/MWh', 'Configuration', '£0.54/MWh'],
            
            ['PPA Price', 'Power Purchase Agreement price for behind-the-meter arrangements.', '£/MWh', 'Configuration', '£100-200/MWh'],
            
            ['VLP Revenue', 'Virtual Lead Party revenue from battery arbitrage and frequency response.', '£/MWh uplift', 'Analysis/bmrs_boalf', '£8-15/MWh average uplift'],
            
            ['DC Revenue', 'Dynamic Containment - frequency response service revenue.', '£/year', 'Analysis', '£50,000-200,000/MW/year'],
            
            ['Capacity Market', 'Payment for being available to generate during peak demand.', '£/kW/year', 'Analysis', '£15-25/kW/year'],
        ]
        
        data.extend(price_schemas)
        data.append(['', '', '', '', ''])
        
        # Section 3: FUEL MIX & GENERATION
        data.append([
            '🔋 GENERATION & FUEL MIX',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append([
            'Term', 'Description', 'Unit', 'Source', 'Notes'
        ])
        
        fuel_terms = [
            ['CCGT', 'Combined Cycle Gas Turbine - natural gas power plants.', 'MW', 'bmrs_fuelinst_iris', 'Flexible, fast-ramping'],
            ['WIND', 'Wind generation (onshore + offshore).', 'MW', 'bmrs_fuelinst_iris', 'Variable renewable'],
            ['NUCLEAR', 'Nuclear power stations.', 'MW', 'bmrs_fuelinst_iris', 'Baseload generation'],
            ['BIOMASS', 'Biomass power plants.', 'MW', 'bmrs_fuelinst_iris', 'Renewable baseload'],
            ['NPSHYD', 'Non-pumped storage hydro.', 'MW', 'bmrs_fuelinst_iris', 'Run-of-river hydro'],
            ['COAL', 'Coal-fired power stations.', 'MW', 'bmrs_fuelinst_iris', 'Being phased out'],
            ['OCGT', 'Open Cycle Gas Turbine - peaking plants.', 'MW', 'bmrs_fuelinst_iris', 'Emergency/peak generation'],
            ['Interconnectors', 'Cross-border electricity flows (FR, BE, NL, NO, DK, IE).', 'MW', 'bmrs_fuelinst_iris', 'Can import or export'],
        ]
        
        data.extend(fuel_terms)
        data.append(['', '', '', '', ''])
        
        # Section 4: BIGQUERY TABLE REFERENCE
        data.append([
            '🗄️ BIGQUERY TABLE REFERENCE',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append([
            'Table Name', 'Description', 'Row Count', 'Date Range', 'Key Columns'
        ])
        
        # Query table metadata
        table_info = []
        tables = [
            ('bmrs_bod', 'Bid-Offer Data - submitted price pairs', 'bmUnit, bid, offer, settlementDate, settlementPeriod'),
            ('bmrs_boalf', 'Accepted balancing actions', 'acceptanceNumber, bmUnit, levelFrom, levelTo'),
            ('bmrs_mid_iris', 'Market Index Data - system prices (real-time)', 'systemSellPrice, systemBuyPrice, settlementDate'),
            ('bmrs_fuelinst_iris', 'Fuel generation mix (real-time)', 'fuelType, generation, publishTime'),
            ('bmrs_freq', 'Grid frequency measurements', 'frequency, measurementTime'),
            ('bmrs_remit_unavailability', 'Power plant outages', 'bmUnit, unavailableCapacity, publishTime'),
            ('bmu_registration_data', 'BMU lookup - plant names and capacities', 'bmUnit, ngcBmUnit, leadPartyName, registeredCapacity'),
            ('gb_power.duos_unit_rates', 'DUoS rates by DNO and voltage', 'dno_id, voltage_level, red_rate, amber_rate, green_rate'),
        ]
        
        for table_name, description, key_cols in tables:
            try:
                # Get row count
                count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.{table_name}`"
                df = bq_client.query(count_query).to_dataframe()
                row_count = f"{int(df.iloc[0]['cnt']):,}"
            except:
                row_count = 'N/A'
            
            table_info.append([
                table_name,
                description,
                row_count,
                '2022-present' if 'iris' not in table_name else 'Last 48h',
                key_cols
            ])
        
        data.extend(table_info)
        data.append(['', '', '', '', ''])
        
        # Section 5: CALCULATION FORMULAS
        data.append([
            '🧮 KEY CALCULATIONS',
            '', '', '', '', '', '', '', '', ''
        ])
        data.append([
            'Calculation', 'Formula', 'Notes'
        ])
        
        formulas = [
            ['BM Revenue (single action)', 'acceptedVolumeMW × appliedPrice × 0.5 hours', 'appliedPrice = offerPrice if volume>0, bidPrice if volume<0'],
            ['Spread', 'offerPrice - bidPrice', 'Positive spread = cost to increase vs cost to decrease'],
            ['Volume Change', 'levelTo - levelFrom', 'Positive = increase, negative = decrease'],
            ['Total UK Capacity', '733,533 MW', 'From bmu_registration_data (sum of registeredCapacity)'],
            ['% Lost (Outages)', '(unavailableCapacity / 42,000 MW) × 100', 'Using 42 GW as reference capacity'],
            ['Settlement Period', '30 minutes', 'Each day has 48 settlement periods'],
            ['DUoS p/kWh → £/MWh', 'p/kWh × 10', 'Conversion: 1 p/kWh = £10/MWh'],
        ]
        
        data.extend(formulas)
        
        # Write to sheet
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Data Dictionary!A1',
            valueInputOption='USER_ENTERED',
            body={'values': data}
        ).execute()
        
        # Format header rows (bold)
        format_requests = [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': get_sheet_id(sheets_service, 'Data Dictionary'),
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True, 'fontSize': 14},
                            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Bold section headers
            {
                'repeatCell': {
                    'range': {
                        'sheetId': get_sheet_id(sheets_service, 'Data Dictionary'),
                        'startRowIndex': 3,
                        'endRowIndex': 4
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True, 'fontSize': 12},
                            'backgroundColor': {'red': 1.0, 'green': 0.9, 'blue': 0.6}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            }
        ]
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': format_requests}
        ).execute()
        
        print(f"   ✅ Created Data Dictionary with {len(data)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_sheet_id(sheets_service, sheet_name):
    """Get sheet ID by name"""
    spreadsheet = sheets_service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID
    ).execute()
    
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    
    return None


def main():
    print("📚 Adding Data Dictionary to Dashboard V3")
    print("="*80)
    
    sheets_service, bq_client = get_clients()
    
    success = True
    success &= add_cell_notes(sheets_service)
    success &= create_data_dictionary_sheet(sheets_service, bq_client)
    
    print("="*80)
    if success:
        print("✅ Data Dictionary complete!")
        print("\n📍 What was added:")
        print("   • Cell notes on Dashboard V3 cells E44-E48")
        print("   • New 'Data Dictionary' sheet with:")
        print("     - Balancing Mechanism terms")
        print("     - Price & revenue schemas (all £ definitions)")
        print("     - Generation & fuel mix")
        print("     - BigQuery table reference")
        print("     - Key calculation formulas")
    else:
        print("⚠️  Completed with errors")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
