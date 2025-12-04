#!/usr/bin/env python3
"""
Fix Dashboard V3 Sparklines - Make Larger with Titles

Improvements:
- Larger sparkline charts (span multiple columns)
- Better titles and formatting
- Complete data visualization
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
WORKSHEET_NAME = "Dashboard V3"

def get_monthly_data():
    """Fetch 12-month sparkline data"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        month_label,
        total_net_revenue_monthly,
        avg_margin,
        max_margin,
        min_margin,
        total_volume_monthly,
        active_units
    FROM `{PROJECT_ID}.{DATASET}.vlp_revenue_monthly_sparklines`
    WHERE breakdown = 'GB_total'
    ORDER BY month_label
    """
    
    df = client.query(query).to_dataframe()
    return df

def add_enhanced_sparklines():
    """Add larger, better formatted sparklines to Dashboard V3"""
    
    # Get data
    print("📊 Fetching data from BigQuery...")
    df = get_monthly_data()
    print(f"✅ Got {len(df)} months of data")
    
    # Connect to Sheets
    print("📝 Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    
    # Clear existing sparklines area (rows 14-25)
    print("🧹 Clearing existing area...")
    sheet.batch_clear(['F14:M25'])
    
    # Calculate stats
    total_revenue = df['total_net_revenue_monthly'].sum() / 1e6
    avg_margin = df['avg_margin'].mean()
    max_margin = df['max_margin'].max()
    total_volume = df['total_volume_monthly'].sum()
    avg_units = df['active_units'].mean()
    
    # Prepare sparkline data
    revenue_data = ','.join([f"{v/1e6:.1f}" for v in df['total_net_revenue_monthly'].values])
    margin_data = ','.join([f"{v:.1f}" for v in df['avg_margin'].values])
    volume_data = ','.join([f"{abs(v):.0f}" for v in df['total_volume_monthly'].values])
    units_data = ','.join([f"{int(v)}" for v in df['active_units'].values])
    
    # Build update data
    updates = []
    
    # Row 14: Section header
    updates.append({
        'range': 'F14:M14',
        'values': [['📊 VLP REVENUE - 12 MONTH TRENDS', '', '', '', '', '', '', '']]
    })
    
    # Row 15: Empty spacing
    updates.append({'range': 'F15', 'values': [['']]})
    
    # Row 16: Revenue chart - LARGER (span columns G:L)
    revenue_formula = f'=SPARKLINE({{{revenue_data}}},{{"charttype","line";"color","#34A853";"linewidth",3;"max",1600;"min",0}})'
    updates.append({
        'range': 'F16:M16',
        'values': [[
            '💰 Net Revenue (£M)',
            revenue_formula,
            '', '', '', '',
            f'Total: £{total_revenue:.0f}M',
            f'Avg: £{total_revenue/len(df):.0f}M/mo'
        ]]
    })
    
    # Row 17: Margin chart - LARGER
    margin_formula = f'=SPARKLINE({{{margin_data}}},{{"charttype","line";"color","#4285F4";"linewidth",3;"max",1400;"min",0}})'
    updates.append({
        'range': 'F17:M17',
        'values': [[
            '📊 Net Margin (£/MWh)',
            margin_formula,
            '', '', '', '',
            f'Avg: £{avg_margin:.0f}/MWh',
            f'Peak: £{max_margin:.0f}/MWh'
        ]]
    })
    
    # Row 18: Volume chart - LARGER
    volume_formula = f'=SPARKLINE({{{volume_data}}},{{"charttype","column";"color","#FBBC04";"max",5500000}})'
    updates.append({
        'range': 'F18:M18',
        'values': [[
            '⚡ Volume (MWh)',
            volume_formula,
            '', '', '', '',
            f'Total: {abs(total_volume)/1e6:.1f}M MWh',
            ''
        ]]
    })
    
    # Row 19: Units chart - LARGER
    units_formula = f'=SPARKLINE({{{units_data}}},{{"charttype","line";"color","#EA4335";"linewidth",3;"max",360;"min",300}})'
    updates.append({
        'range': 'F19:M19',
        'values': [[
            '🔋 Active BMUs',
            units_formula,
            '', '', '', '',
            f'Avg: {avg_units:.0f} units/mo',
            ''
        ]]
    })
    
    # Row 20: Empty
    updates.append({'range': 'F20', 'values': [['']]})
    
    # Row 21-22: Month labels
    months = df['month_label'].tolist()
    updates.append({
        'range': 'F21:L21',
        'values': [['Months:'] + months[:6]]
    })
    updates.append({
        'range': 'G22:L22',
        'values': [months[6:]]
    })
    
    # Batch update
    print("📝 Writing sparklines...")
    sheet.batch_update(updates)
    
    # Format the sparkline columns to be wider
    print("🎨 Formatting columns...")
    sheet.format('G16:K19', {
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE'
    })
    
    # Merge sparkline cells for larger display
    print("📏 Merging cells for larger sparklines...")
    merge_requests = [
        {'range': 'G16:K16'},  # Revenue sparkline
        {'range': 'G17:K17'},  # Margin sparkline
        {'range': 'G18:K18'},  # Volume sparkline
        {'range': 'G19:K19'},  # Units sparkline
    ]
    
    for merge in merge_requests:
        try:
            sheet.merge_cells(merge['range'])
        except:
            pass  # Already merged or error
    
    # Bold the titles
    sheet.format('F16:F19', {
        'textFormat': {'bold': True, 'fontSize': 10}
    })
    
    # Header formatting
    sheet.format('F14:M14', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86},
        'horizontalAlignment': 'CENTER'
    })
    
    print("✅ Enhanced sparklines added!")
    print(f"\n📈 Summary:")
    print(f"   • {len(df)} months of data (Dec 2024 - Oct 2025)")
    print(f"   • Total Revenue: £{total_revenue:.0f}M")
    print(f"   • Avg Margin: £{avg_margin:.0f}/MWh")
    print(f"   • Sparklines now span columns G-K (5 columns wide)")
    print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

if __name__ == '__main__':
    add_enhanced_sparklines()
