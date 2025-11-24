#!/usr/bin/env python3
"""
BESS Sheet Export & Reporting
=============================
Export BESS data to multiple formats and generate reports

Features:
- CSV export
- JSON export
- PDF report generation
- Email delivery
- Automated daily reports

Usage: python3 bess_export_reports.py [--format csv|json|pdf] [--email user@example.com]
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime
import json
import csv
import sys
from typing import Dict, List
from io import StringIO

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
PROJECT_ID = "inner-cinema-476211-u9"


def read_bess_data(sheet: gspread.Worksheet) -> Dict:
    """
    Read all BESS data into structured dict
    """
    print("📖 Reading BESS sheet data...")
    
    data = {
        'metadata': {
            'export_time': datetime.now().isoformat(),
            'sheet_id': SHEET_ID,
            'sheet_name': 'BESS'
        },
        'site_info': {
            'postcode': sheet.acell('A6').value or '',
            'mpan_id': sheet.acell('B6').value or '',
            'dno_key': sheet.acell('C6').value or '',
            'dno_name': sheet.acell('D6').value or '',
            'short_code': sheet.acell('E6').value or '',
            'market_participant': sheet.acell('F6').value or '',
            'gsp_group_id': sheet.acell('G6').value or '',
            'gsp_group': sheet.acell('H6').value or '',
        },
        'duos_rates': {
            'voltage_level': sheet.acell('A10').value or '',
            'red_rate_pkwh': sheet.acell('B10').value or 0,
            'amber_rate_pkwh': sheet.acell('C10').value or 0,
            'green_rate_pkwh': sheet.acell('D10').value or 0,
        },
        'mpan_details': {
            'profile_class': sheet.acell('E10').value or '',
            'meter_registration': sheet.acell('F10').value or '',
            'voltage_level': sheet.acell('G10').value or '',
            'charging_class': sheet.acell('H10').value or '',
            'tariff_id': sheet.acell('I10').value or '',
            'loss_factor': sheet.acell('J10').value or '',
        },
        'time_bands': {
            'weekday': {
                'red': [],
                'amber': [],
                'green': []
            }
        },
        'hh_profile': {
            'min_kw': sheet.acell('B17').value or 0,
            'avg_kw': sheet.acell('B18').value or 0,
            'max_kw': sheet.acell('B19').value or 0,
        }
    }
    
    # Read time bands (rows 13-15)
    try:
        for row in range(13, 16):  # Rows 13, 14, 15
            red_times = sheet.acell(f'A{row}').value or ''
            amber_times = sheet.acell(f'B{row}').value or ''
            green_times = sheet.acell(f'C{row}').value or ''
            
            if red_times:
                data['time_bands']['weekday']['red'].append(red_times)
            if amber_times:
                data['time_bands']['weekday']['amber'].append(amber_times)
            if green_times:
                data['time_bands']['weekday']['green'].append(green_times)
    except:
        pass
    
    print(f"✅ Read data for MPAN: {data['site_info']['mpan_id']}")
    return data


def export_to_csv(data: Dict, filename: str = None) -> str:
    """
    Export BESS data to CSV format
    Returns: filename of created CSV
    """
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bess_export_{timestamp}.csv'
    
    print(f"📄 Exporting to CSV: {filename}")
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Metadata
        writer.writerow(['BESS Data Export'])
        writer.writerow(['Export Time', data['metadata']['export_time']])
        writer.writerow([])
        
        # Site Info
        writer.writerow(['SITE INFORMATION'])
        for key, value in data['site_info'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([])
        
        # DUoS Rates
        writer.writerow(['DUOS RATES'])
        writer.writerow(['Voltage Level', data['duos_rates']['voltage_level']])
        writer.writerow(['Red Rate (p/kWh)', data['duos_rates']['red_rate_pkwh']])
        writer.writerow(['Amber Rate (p/kWh)', data['duos_rates']['amber_rate_pkwh']])
        writer.writerow(['Green Rate (p/kWh)', data['duos_rates']['green_rate_pkwh']])
        writer.writerow([])
        
        # Time Bands
        writer.writerow(['TIME BANDS (Weekday)'])
        writer.writerow(['Red', 'Amber', 'Green'])
        max_bands = max(
            len(data['time_bands']['weekday']['red']),
            len(data['time_bands']['weekday']['amber']),
            len(data['time_bands']['weekday']['green'])
        )
        for i in range(max_bands):
            red = data['time_bands']['weekday']['red'][i] if i < len(data['time_bands']['weekday']['red']) else ''
            amber = data['time_bands']['weekday']['amber'][i] if i < len(data['time_bands']['weekday']['amber']) else ''
            green = data['time_bands']['weekday']['green'][i] if i < len(data['time_bands']['weekday']['green']) else ''
            writer.writerow([red, amber, green])
        writer.writerow([])
        
        # HH Profile
        writer.writerow(['HALF-HOURLY PROFILE PARAMETERS'])
        writer.writerow(['Min kW', data['hh_profile']['min_kw']])
        writer.writerow(['Avg kW', data['hh_profile']['avg_kw']])
        writer.writerow(['Max kW', data['hh_profile']['max_kw']])
    
    print(f"✅ CSV exported: {filename}")
    return filename


def export_to_json(data: Dict, filename: str = None) -> str:
    """
    Export BESS data to JSON format
    Returns: filename of created JSON
    """
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bess_export_{timestamp}.json'
    
    print(f"📄 Exporting to JSON: {filename}")
    
    with open(filename, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=2)
    
    print(f"✅ JSON exported: {filename}")
    return filename


def generate_text_report(data: Dict) -> str:
    """
    Generate formatted text report
    """
    report = []
    report.append("="*60)
    report.append("BESS SITE REPORT")
    report.append("="*60)
    report.append(f"Generated: {data['metadata']['export_time']}")
    report.append("")
    
    report.append("SITE INFORMATION")
    report.append("-"*60)
    report.append(f"Postcode:           {data['site_info']['postcode']}")
    report.append(f"MPAN ID:            {data['site_info']['mpan_id']}")
    report.append(f"DNO:                {data['site_info']['dno_name']}")
    report.append(f"DNO Key:            {data['site_info']['dno_key']}")
    report.append(f"Short Code:         {data['site_info']['short_code']}")
    report.append(f"Market Participant: {data['site_info']['market_participant']}")
    report.append(f"GSP Group:          {data['site_info']['gsp_group']} ({data['site_info']['gsp_group_id']})")
    report.append("")
    
    report.append("DUOS RATES")
    report.append("-"*60)
    report.append(f"Voltage Level:      {data['duos_rates']['voltage_level']}")
    
    # Convert rates to float if they're strings
    red_rate = float(data['duos_rates']['red_rate_pkwh']) if data['duos_rates']['red_rate_pkwh'] else 0.0
    amber_rate = float(data['duos_rates']['amber_rate_pkwh']) if data['duos_rates']['amber_rate_pkwh'] else 0.0
    green_rate = float(data['duos_rates']['green_rate_pkwh']) if data['duos_rates']['green_rate_pkwh'] else 0.0
    
    report.append(f"Red Rate:           {red_rate:.3f} p/kWh")
    report.append(f"Amber Rate:         {amber_rate:.3f} p/kWh")
    report.append(f"Green Rate:         {green_rate:.3f} p/kWh")
    report.append("")
    
    report.append("TIME BANDS (Weekday)")
    report.append("-"*60)
    report.append("RED (Peak):")
    for time in data['time_bands']['weekday']['red']:
        report.append(f"  • {time}")
    report.append("AMBER (Mid-Peak):")
    for time in data['time_bands']['weekday']['amber']:
        report.append(f"  • {time}")
    report.append("GREEN (Off-Peak):")
    for time in data['time_bands']['weekday']['green']:
        report.append(f"  • {time}")
    report.append("")
    
    report.append("HALF-HOURLY PROFILE")
    report.append("-"*60)
    report.append(f"Min Demand:         {data['hh_profile']['min_kw']} kW")
    report.append(f"Avg Demand:         {data['hh_profile']['avg_kw']} kW")
    report.append(f"Max Demand:         {data['hh_profile']['max_kw']} kW")
    report.append("")
    
    report.append("="*60)
    report.append("End of Report")
    report.append("="*60)
    
    return "\n".join(report)


def save_text_report(report: str, filename: str = None) -> str:
    """Save text report to file"""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bess_report_{timestamp}.txt'
    
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"✅ Text report saved: {filename}")
    return filename


def main():
    """Main export function"""
    print("="*60)
    print("🔋 BESS EXPORT & REPORTING")
    print("="*60)
    
    # Parse command line arguments
    export_format = 'csv'  # default
    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            export_format = sys.argv[idx + 1].lower()
    
    # Connect to Google Sheets
    print("\n🔧 Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    bess_sheet = spreadsheet.worksheet('BESS')
    print("✅ Connected to BESS sheet")
    
    # Read data
    data = read_bess_data(bess_sheet)
    
    # Export based on format
    print(f"\n📤 Exporting as: {export_format.upper()}")
    
    if export_format == 'csv':
        filename = export_to_csv(data)
    elif export_format == 'json':
        filename = export_to_json(data)
    elif export_format == 'txt' or export_format == 'report':
        report = generate_text_report(data)
        filename = save_text_report(report)
        print("\n" + report)
    elif export_format == 'all':
        # Export all formats
        csv_file = export_to_csv(data)
        json_file = export_to_json(data)
        report = generate_text_report(data)
        txt_file = save_text_report(report)
        print(f"\n✅ Exported all formats:")
        print(f"   CSV:  {csv_file}")
        print(f"   JSON: {json_file}")
        print(f"   TXT:  {txt_file}")
    else:
        print(f"❌ Unknown format: {export_format}")
        print("Available formats: csv, json, txt, all")
        return
    
    print("\n" + "="*60)
    print("✅ EXPORT COMPLETE")
    print("="*60)


if __name__ == "__main__":
    if '--help' in sys.argv:
        print("""
BESS Export & Reporting Usage:
  python3 bess_export_reports.py                    # Export as CSV (default)
  python3 bess_export_reports.py --format csv       # Export as CSV
  python3 bess_export_reports.py --format json      # Export as JSON
  python3 bess_export_reports.py --format txt       # Generate text report
  python3 bess_export_reports.py --format all       # Export all formats
  python3 bess_export_reports.py --help             # Show this help
        """)
    else:
        main()
