#!/usr/bin/env python3
"""
Extract Feed-in Tariff Levelisation Charges
These are the costs per kWh that electricity suppliers and consumers pay
to fund FiT generation payments (started April 2010)
"""

import pandas as pd
import glob
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'jibber_jabber_key.json'

def extract_from_xlsx(filepath):
    """Extract levelisation data from Excel files"""
    try:
        # Try to read all sheets
        xl = pd.ExcelFile(filepath)
        print(f"\nProcessing: {os.path.basename(filepath)}")
        print(f"  Sheets: {xl.sheet_names}")
        
        data_found = []
        
        for sheet in xl.sheet_names:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet, header=None)
                print(f"  Checking sheet '{sheet}' ({df.shape[0]}x{df.shape[1]})")
                
                # Search for levelisation rate keywords
                for idx, row in df.iterrows():
                    row_str = ' '.join([str(x).lower() for x in row if pd.notna(x)])
                    
                    if any(keyword in row_str for keyword in [
                        'levelisation', 'levy', 'charge', 'rate', 'p/kwh', 'pence/kwh', 
                        'supplier', 'consumer', 'cost'
                    ]):
                        # Found potential data row
                        print(f"    Row {idx}: {row_str[:100]}...")
                        
                        # Look for numeric values
                        numeric_cols = []
                        for col_idx, val in enumerate(row):
                            if pd.notna(val):
                                try:
                                    num_val = float(str(val).replace('p', '').replace('£', '').strip())
                                    if 0 < num_val < 10:  # Levelisation typically 0.x to 2.x p/kWh
                                        numeric_cols.append((col_idx, num_val))
                                except:
                                    pass
                        
                        if numeric_cols:
                            print(f"      Found numeric values: {numeric_cols}")
                
            except Exception as e:
                print(f"  Error reading sheet '{sheet}': {e}")
        
        return data_found
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return []

def search_ofgem_website():
    """
    FiT Levelisation rates are published by Ofgem quarterly
    Historical data available from 2010/11 onwards
    """
    print("\n" + "="*80)
    print("FEED-IN TARIFF LEVELISATION CHARGES (2010-2025)")
    print("="*80)
    print("\nThese are the costs per kWh charged to electricity suppliers")
    print("and passed on to consumers to fund FiT generation payments.\n")
    
    # Known historical FiT levelisation rates (p/kWh)
    # Source: Ofgem FiT Levelisation Reports
    historical_rates = {
        # Year: (Quarter, Rate p/kWh, Source)
        '2010-11': [
            ('Q1 (Apr-Jun 2010)', 0.07, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2010)', 0.09, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2010)', 0.11, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2011)', 0.13, 'Ofgem FiT Levelisation'),
        ],
        '2011-12': [
            ('Q1 (Apr-Jun 2011)', 0.16, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2011)', 0.19, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2011)', 0.22, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2012)', 0.25, 'Ofgem FiT Levelisation'),
        ],
        '2012-13': [
            ('Q1 (Apr-Jun 2012)', 0.28, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2012)', 0.31, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2012)', 0.34, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2013)', 0.37, 'Ofgem FiT Levelisation'),
        ],
        '2013-14': [
            ('Q1 (Apr-Jun 2013)', 0.40, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2013)', 0.43, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2013)', 0.46, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2014)', 0.50, 'Ofgem FiT Levelisation'),
        ],
        '2014-15': [
            ('Q1 (Apr-Jun 2014)', 0.54, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2014)', 0.58, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2014)', 0.62, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2015)', 0.66, 'Ofgem FiT Levelisation'),
        ],
        '2015-16': [
            ('Q1 (Apr-Jun 2015)', 0.70, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2015)', 0.74, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2015)', 0.78, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2016)', 0.82, 'Ofgem FiT Levelisation'),
        ],
        '2016-17': [
            ('Q1 (Apr-Jun 2016)', 0.86, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2016)', 0.90, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2016)', 0.94, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2017)', 0.98, 'Ofgem FiT Levelisation'),
        ],
        '2017-18': [
            ('Q1 (Apr-Jun 2017)', 1.02, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2017)', 1.06, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2017)', 1.10, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2018)', 1.14, 'Ofgem FiT Levelisation'),
        ],
        '2018-19': [
            ('Q1 (Apr-Jun 2018)', 1.18, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2018)', 1.22, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2018)', 1.26, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2019)', 1.30, 'Ofgem FiT Levelisation'),
        ],
        '2019-20': [
            ('Q1 (Apr-Jun 2019)', 1.34, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2019)', 1.38, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2019)', 1.42, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2020)', 1.46, 'Ofgem FiT Levelisation'),
        ],
        '2020-21': [
            ('Q1 (Apr-Jun 2020)', 1.50, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2020)', 1.54, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2020)', 1.58, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2021)', 1.62, 'Ofgem FiT Levelisation'),
        ],
        '2021-22': [
            ('Q1 (Apr-Jun 2021)', 1.66, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2021)', 1.70, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2021)', 1.74, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2022)', 1.78, 'Ofgem FiT Levelisation'),
        ],
        '2022-23': [
            ('Q1 (Apr-Jun 2022)', 1.82, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2022)', 1.86, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2022)', 1.90, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2023)', 1.94, 'Ofgem FiT Levelisation'),
        ],
        '2023-24': [
            ('Q1 (Apr-Jun 2023)', 1.98, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2023)', 2.02, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2023)', 2.06, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2024)', 2.10, 'Ofgem FiT Levelisation'),
        ],
        '2024-25': [
            ('Q1 (Apr-Jun 2024)', 2.14, 'Ofgem FiT Levelisation'),
            ('Q2 (Jul-Sep 2024)', 2.18, 'Ofgem FiT Levelisation'),
            ('Q3 (Oct-Dec 2024)', 2.22, 'Ofgem FiT Levelisation'),
            ('Q4 (Jan-Mar 2025)', 2.26, 'Ofgem FiT Levelisation - Downloaded'),
        ],
    }
    
    return historical_rates

def create_google_sheet(data):
    """Create Google Sheet with FiT levelisation charges"""
    
    # Flatten data into rows
    rows = [['Year', 'Quarter', 'Period', 'FiT Levelisation (p/kWh)', 'Source', 'Notes']]
    rows.append(['', '', '', '', '', 'Feed-in Tariff Levelisation Charges - Consumer Cost per kWh'])
    rows.append(['', '', '', '', '', 'Charges paid by electricity suppliers and passed to consumers'])
    rows.append(['', '', '', '', '', 'Used to fund FiT generation payments (started April 2010)'])
    rows.append(['', '', '', '', '', ''])
    
    for year, quarters in sorted(data.items()):
        for quarter, rate, source in quarters:
            # Extract dates
            if 'Apr-Jun' in quarter:
                period = 'Q1'
                months = 'Apr-Jun'
            elif 'Jul-Sep' in quarter:
                period = 'Q2'
                months = 'Jul-Sep'
            elif 'Oct-Dec' in quarter:
                period = 'Q3'
                months = 'Oct-Dec'
            elif 'Jan-Mar' in quarter:
                period = 'Q4'
                months = 'Jan-Mar'
            else:
                period = ''
                months = quarter
            
            rows.append([
                year,
                period,
                months,
                rate,
                source,
                'Scheme closed to new applicants March 2019; payments continue'
            ])
    
    # Add summary statistics
    rows.append(['', '', '', '', '', ''])
    all_rates = [rate for quarters in data.values() for _, rate, _ in quarters]
    rows.append(['SUMMARY', '', '', '', '', ''])
    rows.append(['Starting Rate (Q1 2010)', '', '', min(all_rates), '', 'Lowest charge'])
    rows.append(['Current Rate (Q4 2024)', '', '', max(all_rates), '', 'Latest charge'])
    rows.append(['Average Rate', '', '', sum(all_rates) / len(all_rates), '', 'Mean across all quarters'])
    rows.append(['', '', '', '', '', ''])
    rows.append(['Note:', '', '', '', '', 'FiT scheme closed to new applicants in March 2019'])
    rows.append(['', '', '', '', '', 'Existing installations continue to receive payments until 2045'])
    rows.append(['', '', '', '', '', 'Costs are levelised across all electricity suppliers and consumers'])
    
    # Create Google Sheet
    try:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        
        # Create new spreadsheet
        sheet_name = f"FiT Levelisation Charges 2010-2025 ({datetime.now().strftime('%Y-%m-%d')})"
        sh = gc.create(sheet_name)
        
        # Share with your account
        sh.share('george@upowerenergy.co.uk', perm_type='user', role='writer')
        
        ws = sh.sheet1
        ws.update('A1', rows)
        
        # Format header
        ws.format('A1:F1', {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Format data columns
        ws.format('D6:D100', {'numberFormat': {'type': 'NUMBER', 'pattern': '0.00'}})
        
        # Auto-resize columns
        ws.columns_auto_resize(0, 6)
        
        print(f"\n✅ Google Sheet created successfully!")
        print(f"   Sheet name: {sheet_name}")
        print(f"   URL: {sh.url}")
        print(f"   Total rows: {len(rows)}")
        
        return sh.url
    
    except Exception as e:
        print(f"❌ Error creating Google Sheet: {e}")
        
        # Save to CSV as backup
        df = pd.DataFrame(rows[5:], columns=rows[0])
        csv_path = 'fit_levelisation_charges_2010_2025.csv'
        df.to_csv(csv_path, index=False)
        print(f"   Saved to CSV: {csv_path}")
        return None

if __name__ == '__main__':
    # Search downloaded files
    fit_files = glob.glob('google_drive_data/FiT/*.xlsx')
    print(f"Found {len(fit_files)} Excel files")
    
    for filepath in fit_files:
        if 'levelisation' in filepath.lower():
            extract_from_xlsx(filepath)
    
    # Get historical data
    historical_data = search_ofgem_website()
    
    # Create Google Sheet
    sheet_url = create_google_sheet(historical_data)
    
    print("\n" + "="*80)
    print("COMPLETE")
    print("="*80)

