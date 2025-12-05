import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'inner-cinema-credentials.json'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc' # GB Energy Dashboard V3
SHEET_NAME = 'Dashboard V3'

def inspect_sheet():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # Get values and formatting for A1:K50 (Header area and start of tables)
    range_name = f"'{SHEET_NAME}'!A1:K50"
    
    print(f"--- Inspecting {range_name} ---")
    
    # 1. Get Values
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    rows = result.get('values', [])
    
    print("\n[VALUES]")
    for i, row in enumerate(rows):
        print(f"Row {i+1}: {row}")

    # 2. Get Formatting (Background Colors)
    # We need to use spreadsheets.get with includeGridData=True for specific range
    request = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[range_name],
        includeGridData=True
    )
    response = request.execute()
    
    print("\n[FORMATTING - Background Colors]")
    rowData = response['sheets'][0]['data'][0].get('rowData', [])
    
    for i, row in enumerate(rowData):
        cells = row.get('values', [])
        row_colors = []
        for j, cell in enumerate(cells):
            format_spec = cell.get('effectiveFormat', {})
            bg_color = format_spec.get('backgroundColor', {})
            
            # Convert to RGB tuple for easier reading
            red = bg_color.get('red', 0)
            green = bg_color.get('green', 0)
            blue = bg_color.get('blue', 0)
            
            # Simple color name approximation
            color_name = "White/None"
            if red > 0.9 and green > 0.9 and blue > 0.9: color_name = "White"
            elif red > 0.9 and green < 0.5 and blue < 0.5: color_name = "Red"
            elif red < 0.5 and green > 0.9 and blue < 0.5: color_name = "Green"
            elif red < 0.5 and green < 0.5 and blue > 0.9: color_name = "Blue"
            elif red > 0.9 and green > 0.5 and blue < 0.2: color_name = "Orange"
            elif red < 0.1 and green < 0.1 and blue < 0.1: color_name = "Black"
            elif red > 0.8 and green > 0.8 and blue > 0.8: color_name = "Grey"
            
            if color_name != "White":
                row_colors.append(f"Col {chr(65+j)}: {color_name} ({red:.1f},{green:.1f},{blue:.1f})")
        
        if row_colors:
            print(f"Row {i+1}: {', '.join(row_colors)}")

if __name__ == '__main__':
    inspect_sheet()
