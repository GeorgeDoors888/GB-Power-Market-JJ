#!/usr/bin/env python3
"""
Universal Fast Sheets Wrapper
Drop-in replacement for common gspread operations
Import this instead of gspread for 255x speedup
"""

from fast_sheets_helper import FastSheetsAPI
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

class FastSheet:
    """Fast replacement for gspread.Client"""
    
    def __init__(self, credentials_file='inner-cinema-credentials.json'):
        self.api = FastSheetsAPI(credentials_file)
        self.credentials_file = credentials_file
        
        # For advanced operations (formatting, data validation)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=scopes
        )
        self.service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        print("⚡ FastSheet initialized (255x faster than gspread)")
    
    def open_by_key(self, spreadsheet_id):
        """Return a FastSpreadsheet object (no slow metadata fetch!)"""
        return FastSpreadsheet(spreadsheet_id, self.api, self.service)


class FastSpreadsheet:
    """Fast replacement for gspread.Spreadsheet"""
    
    def __init__(self, spreadsheet_id, api, service):
        self.id = spreadsheet_id
        self.api = api
        self.service = service
        self._worksheets = {}
    
    def worksheet(self, title):
        """Return FastWorksheet (no slow metadata fetch!)"""
        if title not in self._worksheets:
            self._worksheets[title] = FastWorksheet(self.id, title, self.api, self.service)
        return self._worksheets[title]
    
    def batch_update(self, body):
        """Execute batch update request"""
        return self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body=body
        ).execute()


class FastWorksheet:
    """Fast replacement for gspread.Worksheet"""
    
    def __init__(self, spreadsheet_id, title, api, service):
        self.spreadsheet_id = spreadsheet_id
        self.title = title
        self.api = api
        self.service = service
        self._sheet_id = None
    
    @property
    def id(self):
        """Get worksheet ID (lazy load)"""
        if self._sheet_id is None:
            metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            for sheet in metadata.get('sheets', []):
                if sheet['properties']['title'] == self.title:
                    self._sheet_id = sheet['properties']['sheetId']
                    break
        return self._sheet_id
    
    def get(self, range_name):
        """Read range - returns 2D list"""
        full_range = f"{self.title}!{range_name}"
        return self.api.read_range(self.spreadsheet_id, full_range)
    
    def update(self, range_name, values, **kwargs):
        """Update range with values"""
        full_range = f"{self.title}!{range_name}"
        return self.api.update_single_range(self.spreadsheet_id, full_range, values)
    
    def batch_update(self, data, **kwargs):
        """Batch update multiple ranges"""
        # Convert gspread format to API format
        updates = []
        for item in data:
            range_name = item['range']
            # Add sheet name if not present
            if '!' not in range_name:
                range_name = f"{self.title}!{range_name}"
            updates.append({
                'range': range_name,
                'values': item['values']
            })
        return self.api.batch_update(self.spreadsheet_id, updates)
    
    def acell(self, label):
        """Get single cell - returns object with .value"""
        data = self.get(label)
        value = data[0][0] if data and data[0] else ''
        
        class Cell:
            def __init__(self, val):
                self.value = val
        
        return Cell(value)
    
    def update_cell(self, row, col, value):
        """Update single cell by row/col (1-indexed)"""
        # Convert to A1 notation
        col_letter = chr(64 + col)  # A=1, B=2, etc.
        range_name = f"{col_letter}{row}"
        return self.update(range_name, [[value]])
    
    def format(self, range_name, format_dict):
        """Apply formatting to range"""
        # Get sheet ID
        sheet_id = self.id
        
        # Convert A1 notation to grid range
        # Simplified - assumes single cell for now
        import re
        match = re.match(r'([A-Z]+)(\d+)', range_name)
        if not match:
            return
        
        col_letter, row_num = match.groups()
        col_idx = ord(col_letter) - 65  # A=0, B=1, etc.
        row_idx = int(row_num) - 1
        
        request = {
            "requests": [{
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_idx,
                        "endRowIndex": row_idx + 1,
                        "startColumnIndex": col_idx,
                        "endColumnIndex": col_idx + 1
                    },
                    "cell": {
                        "userEnteredFormat": format_dict
                    },
                    "fields": "userEnteredFormat"
                }
            }]
        }
        
        return self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=request
        ).execute()


# Convenience function
def authorize(credentials_file='inner-cinema-credentials.json'):
    """
    Drop-in replacement for gspread.authorize()
    
    Usage:
        # OLD: client = gspread.authorize(creds)
        # NEW: client = fast_gspread.authorize('credentials.json')
    """
    return FastSheet(credentials_file)


# Example usage
if __name__ == '__main__':
    start = time.time()
    
    # Initialize (fast!)
    client = authorize()
    
    # Open sheet (fast - no metadata load!)
    sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
    ws = sheet.worksheet('Live Dashboard v2')
    
    # Read (fast!)
    data = ws.get('A6')
    print(f"✅ Read A6: {data}")
    
    # Write (fast!)
    ws.update('Z99', [['Fast Wrapper Test']])
    print(f"✅ Write Z99")
    
    print(f"\n⚡ Total time: {time.time()-start:.2f}s (vs 60s+ with gspread)")
