#!/usr/bin/env python3
"""
Download ALL historical FiT Levelisation Reports (2015-2025)
and extract consumer levy rates
"""

import pickle
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# OAuth credentials
if not os.path.exists('token.pickle'):
    print("❌ No OAuth token found. Run google_drive_oauth.py first.")
    exit(1)

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

service = build('drive', 'v3', credentials=creds)

# Target quarterly levelisation reports (2015-2025)
target_files = [
    # 2015
    ("Feed-in Tariff (FIT) Levelisation Report October to December 2015..xlsx", "2015-Q3"),
    
    # 2016
    ("Feed-in Tariff (FIT) Levelisation Report January to March 2016.xlsx", "2016-Q4"),
    ("Feed-in Tariff (FIT) Levelisation Report April to June 2016.xlsx", "2016-Q1"),
    ("Feed-in Tariff (FIT) Levelisation Report July to September 2016.xlsx", "2016-Q2"),
    ("Feed-in Tariff (FIT) Levelisation Report October to December 2016.xlsx", "2016-Q3"),
    
    # 2017
    ("Feed-in Tariff (FIT) Levelisation Report January to March 2017.xlsx", "2017-Q4"),
    ("Feed-in Tariff (FIT) Levelisation Report April to June 2017.xlsx", "2017-Q1"),
    ("Feed-in Tariff (FIT) Levelisation Report July to September 2017.xlsx", "2017-Q2"),
    ("Feed-in Tariff (FIT) Levelisation Report October to December 2017.xlsx", "2017-Q3"),
    
    # 2018
    ("Feed-in Tariff (FIT) levelisation report January to March 2018.xlsx", "2018-Q4"),
    ("Feed-in Tariff (FIT) levelisation report April to June 2018.xlsx", "2018-Q1"),
    ("Feed-in Tariff (FIT) Levelisation Report July to September 2018.xlsx", "2018-Q2"),
    ("Feed-in Tariff (FIT) Levelisation Report October to December 2018.xlsx", "2018-Q3"),
    
    # 2019
    ("Feed-in Tariff (FIT) Levelisation Report January to March 2019.xlsx", "2019-Q4"),
    ("Feed-in Tariff (FIT) levelisation report - April to June 2019.xlsx", "2019-Q1"),
    ("Feed-in Tariff (FIT) Levelisation Report July to September 2019.xlsx", "2019-Q2"),
    ("Feed-in Tariff (FIT) Levelisation Report October to December 2019.xlsx", "2019-Q3"),
    
    # 2020
    ("Feed-in Tariff (FIT) Levelisation Report January to March 2020.xlsx", "2020-Q4"),
    ("Feed-in Tariff (FIT) Levelisation Report April to June 2020.xlsx", "2020-Q1"),
    ("Feed-in Tariff (FIT) Levelisation Report July to September 2020.xlsx", "2020-Q2"),
    ("Feed-in Tariff (FIT) Levelisation Report October to December 2020.xlsx", "2020-Q3"),
    
    # 2021
    ("Feed-in Tariff (FIT) levelisation report - January to March 2021.xlsx", "2021-Q4"),
    ("Feed-in Tariff (FIT) levelisation report - April to June 2021.xlsx", "2021-Q1"),
    ("Feed-in Tariff (FIT) Levelisation Report July to September 2021.xlsx", "2021-Q2"),
    ("Feed-in Tariff (FIT) levelisation report - October to December 2021.xlsx", "2021-Q3"),
    
    # 2022
    ("Feed-in Tariff (FIT) levelisation report - January to March 2022.xlsx", "2022-Q4"),
    ("Feed-in Tariff (FIT) levelisation report - April to June 2022.xlsx", "2022-Q1"),
    ("Feed-in Tariff (FIT) levelisation report - July to September 2022.xlsx", "2022-Q2"),
    ("Feed-in Tariff (FIT) levelisation report - October to December 2022.xlsx", "2022-Q3"),
    
    # 2023
    ("Feed-in Tariff (FIT) levelisation report - January to March 2023.xlsx", "2023-Q4"),
    ("Feed-in Tariff (FIT) levelisation report - 1 April to 30 June 2023.xlsx", "2023-Q1"),
    ("Feed-in Tariff (FIT) levelisation report - July to September 2023.xlsx", "2023-Q2"),
    ("Feed-in Tariff (FIT) levelisation report - October to December 2023.xlsx", "2023-Q3"),
    
    # 2024
    ("Feed-in Tariff (FIT) levelisation report - 1 January to 31 March 2024.xlsx", "2024-Q4"),
    ("Feed-in Tariff (FIT) levelisation report - 1 April to 30 June 2024.xlsx", "2024-Q1"),
    ("Feed-in Tariff (FIT) levelisation report - July to September 2024.xlsx", "2024-Q2"),
    ("Feed-in tariff levelisation report October to December 2024.xlsx", "2024-Q3"),
    
    # 2025
    ("Feed-in tariff levelisation report January to March 2025.xlsx", "2025-Q4"),
]

def search_and_download(filename, period):
    """Search for file and download it"""
    try:
        query = f"name = '{filename}'"
        results = service.files().list(
            q=query,
            pageSize=1,
            fields="files(id, name)"
        ).execute()
        
        files = results.get('files', [])
        if not files:
            print(f"  ❌ Not found: {filename}")
            return None
        
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        
        file_path = f"fit_levelisation_data/{period}_{filename}"
        os.makedirs("fit_levelisation_data", exist_ok=True)
        
        with open(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        print(f"  ✅ {period}: {filename}")
        return file_path
    
    except Exception as e:
        print(f"  ❌ Error downloading {filename}: {e}")
        return None

def extract_rate(filepath, period):
    """Extract levelisation rate from Excel file"""
    try:
        # Read Levelisation Parameters sheet
        df = pd.read_excel(filepath, sheet_name='Levelisation Parameters', header=None)
        
        # Find total fund and total electricity
        total_fund = None
        total_electricity = None
        exempt_electricity = 0
        
        for idx, row in df.iterrows():
            row_str = ' '.join([str(x).lower() if pd.notna(x) else '' for x in row])
            
            if 'total levelisation fund' in row_str:
                # Next column should be the value
                for val in row:
                    if pd.notna(val) and isinstance(val, (int, float)) and val > 1000000:
                        total_fund = float(val)
                        break
            
            elif 'total electricity supplied' in row_str:
                for val in row:
                    if pd.notna(val) and isinstance(val, (int, float)) and val > 10000:
                        total_electricity = float(val)
                        break
            
            elif 'energy intensive' in row_str or 'exempt' in row_str:
                for val in row:
                    if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                        exempt_electricity = float(val)
                        break
        
        if total_fund and total_electricity:
            net_electricity = total_electricity - exempt_electricity
            rate_per_mwh = total_fund / net_electricity
            rate_per_kwh_pence = (rate_per_mwh / 1000) * 100
            
            return {
                'period': period,
                'total_fund': total_fund,
                'total_electricity': total_electricity,
                'exempt_electricity': exempt_electricity,
                'net_electricity': net_electricity,
                'rate_mwh': rate_per_mwh,
                'rate_pkwh': rate_per_kwh_pence
            }
        else:
            print(f"  ⚠️  Could not extract data from {period}")
            return None
    
    except Exception as e:
        print(f"  ❌ Error extracting from {filepath}: {e}")
        return None

def create_google_sheet(all_data):
    """Create comprehensive Google Sheet with all historical rates"""
    
    # Prepare rows
    rows = [
        ['Period', 'Year', 'Quarter', 'Months', 'FiT Fund (£)', 'Total Electricity (MWh)', 
         'Exempt EII (MWh)', 'Net Liable (MWh)', 'Rate (£/MWh)', 'Consumer Levy (p/kWh)', 
         'Annual Impact (£)'],
        ['', '', '', '', '', '', '', '', '', '', 'Based on 3,000 kWh/year typical home']
    ]
    
    # Sort by period
    sorted_data = sorted(all_data, key=lambda x: x['period'])
    
    for d in sorted_data:
        period = d['period']
        year = period.split('-')[0]
        quarter = period.split('-')[1]
        
        # Map quarter to months
        quarter_months = {
            'Q1': 'Apr-Jun',
            'Q2': 'Jul-Sep',
            'Q3': 'Oct-Dec',
            'Q4': 'Jan-Mar'
        }
        months = quarter_months.get(quarter, quarter)
        
        annual_impact = d['rate_pkwh'] / 100 * 3000  # £ for typical home
        
        rows.append([
            period,
            year,
            quarter,
            months,
            f"{d['total_fund']:,.2f}",
            f"{d['total_electricity']:,.2f}",
            f"{d['exempt_electricity']:,.2f}",
            f"{d['net_electricity']:,.2f}",
            f"{d['rate_mwh']:.2f}",
            f"{d['rate_pkwh']:.4f}",
            f"{annual_impact:.2f}"
        ])
    
    # Add summary
    rows.append(['', '', '', '', '', '', '', '', '', '', ''])
    rows.append(['SUMMARY', '', '', '', '', '', '', '', '', '', ''])
    
    all_rates = [d['rate_pkwh'] for d in sorted_data]
    rows.append(['Starting Rate', sorted_data[0]['period'], '', '', '', '', '', '', '', 
                 f"{sorted_data[0]['rate_pkwh']:.4f}", ''])
    rows.append(['Current Rate', sorted_data[-1]['period'], '', '', '', '', '', '', '', 
                 f"{sorted_data[-1]['rate_pkwh']:.4f}", ''])
    rows.append(['Average Rate', '', '', '', '', '', '', '', '', 
                 f"{sum(all_rates) / len(all_rates):.4f}", ''])
    rows.append(['Minimum Rate', '', '', '', '', '', '', '', '', 
                 f"{min(all_rates):.4f}", ''])
    rows.append(['Maximum Rate', '', '', '', '', '', '', '', '', 
                 f"{max(all_rates):.4f}", ''])
    
    # Calculate percentage change
    if len(sorted_data) > 1:
        first_rate = sorted_data[0]['rate_pkwh']
        last_rate = sorted_data[-1]['rate_pkwh']
        pct_change = ((last_rate - first_rate) / first_rate) * 100
        rows.append(['Total Change', '', '', '', '', '', '', '', '', 
                     f"{pct_change:.1f}%", ''])
    
    # Create Google Sheet
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        CREDS_FILE = 'jibber_jabber_key.json'
        creds_sheets = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds_sheets)
        
        sheet_name = f"FiT Levelisation History 2015-2025 ({datetime.now().strftime('%Y-%m-%d')})"
        sh = gc.create(sheet_name)
        
        # Share with user
        sh.share('george@upowerenergy.co.uk', perm_type='user', role='writer')
        
        ws = sh.sheet1
        ws.update('A1', rows)
        
        # Format header
        ws.format('A1:K1', {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
        
        # Auto-resize
        ws.columns_auto_resize(0, 11)
        
        print(f"\n✅ Google Sheet created successfully!")
        print(f"   Sheet name: {sheet_name}")
        print(f"   URL: {sh.url}")
        print(f"   Total periods: {len(sorted_data)}")
        
        return sh.url
    
    except Exception as e:
        print(f"❌ Error creating Google Sheet: {e}")
        
        # Save to CSV as backup
        df = pd.DataFrame(rows[2:], columns=rows[0])
        csv_path = 'fit_levelisation_history_2015_2025.csv'
        df.to_csv(csv_path, index=False)
        print(f"   Saved to CSV: {csv_path}")
        return None

if __name__ == '__main__':
    print("📊 DOWNLOADING ALL FIT LEVELISATION REPORTS (2015-2025)")
    print("="*80)
    
    all_data = []
    
    for filename, period in target_files:
        filepath = search_and_download(filename, period)
        
        if filepath:
            data = extract_rate(filepath, period)
            if data:
                all_data.append(data)
                print(f"      Rate: {data['rate_pkwh']:.4f} p/kWh")
    
    print(f"\n✅ Successfully extracted {len(all_data)} periods")
    
    if all_data:
        # Create Google Sheet
        sheet_url = create_google_sheet(all_data)
        
        print("\n" + "="*80)
        print("COMPLETE")
        print("="*80)
        
        if sheet_url:
            print(f"\n📊 View your Google Sheet: {sheet_url}")
    else:
        print("\n❌ No data extracted")
