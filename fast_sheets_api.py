#!/usr/bin/env python3
"""
Fast Google Sheets API - Direct v4 API (10-20x faster than gspread)
Bypasses slow worksheet loading by using batchUpdate directly
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import logging

class FastSheetsAPI:
    """Direct Google Sheets API v4 - much faster than gspread"""
    
    def __init__(self, credentials_file='inner-cinema-credentials.json'):
        """Initialize with service account credentials"""
        self.credentials_file = credentials_file
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=self.scopes)
        self.service = build('sheets', 'v4', credentials=self.creds, cache_discovery=False)
        logging.info(f"✅ FastSheetsAPI initialized with {credentials_file}")
    
    def batch_update(self, spreadsheet_id, updates):
        """
        Batch update multiple ranges at once
        
        Args:
            spreadsheet_id: The spreadsheet ID
            updates: List of dict with 'range' and 'values' keys
                    [{'range': 'Sheet1!A1:B2', 'values': [[1,2],[3,4]]}, ...]
        
        Returns:
            Response from API
        """
        try:
            body = {
                'valueInputOption': 'USER_ENTERED',  # Allows formulas
                'data': [
                    {
                        'range': update['range'],
                        'values': update['values']
                    }
                    for update in updates
                ]
            }
            
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return result
        
        except HttpError as e:
            logging.error(f"❌ Batch update failed: {e}")
            raise
    
    def update_single_range(self, spreadsheet_id, range_name, values):
        """
        Update a single range (convenience method)
        
        Args:
            spreadsheet_id: The spreadsheet ID
            range_name: A1 notation like 'Sheet1!A1:B2'
            values: 2D array of values [[row1], [row2], ...]
        """
        return self.batch_update(spreadsheet_id, [{'range': range_name, 'values': values}])
    
    def read_range(self, spreadsheet_id, range_name):
        """
        Read a range of cells
        
        Args:
            spreadsheet_id: The spreadsheet ID
            range_name: A1 notation like 'Sheet1!A1:B2'
        
        Returns:
            2D array of values
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        
        except HttpError as e:
            logging.error(f"❌ Read failed: {e}")
            return []
    
    def clear_range(self, spreadsheet_id, range_name):
        """Clear a range of cells"""
        try:
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                body={}
            ).execute()
            logging.info(f"✅ Cleared {range_name}")
        except HttpError as e:
            logging.error(f"❌ Clear failed: {e}")
    
    def get_sheet_id(self, spreadsheet_id, sheet_name):
        """Get the sheetId for a given sheet name"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            logging.error(f"❌ Sheet '{sheet_name}' not found")
            return None
        
        except HttpError as e:
            logging.error(f"❌ Failed to get sheet ID: {e}")
            return None
    
    def merge_cells(self, spreadsheet_id, sheet_name, range_notation):
        """
        Merge cells in A1 notation (e.g., 'N13:P13')
        
        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Sheet name (e.g., 'Live Dashboard v2')
            range_notation: A1 notation like 'N13:P13'
        """
        try:
            # Get sheet ID
            sheet_id = self.get_sheet_id(spreadsheet_id, sheet_name)
            if sheet_id is None:
                return False
            
            # Parse range notation (e.g., 'N13:P13')
            parts = range_notation.split(':')
            if len(parts) != 2:
                logging.error(f"❌ Invalid range notation: {range_notation}")
                return False
            
            start_cell = parts[0]
            end_cell = parts[1]
            
            # Convert A1 to row/col indices (0-based)
            def a1_to_indices(cell):
                col = 0
                row = 0
                i = 0
                while i < len(cell) and cell[i].isalpha():
                    col = col * 26 + (ord(cell[i].upper()) - ord('A') + 1)
                    i += 1
                row = int(cell[i:])
                return row - 1, col - 1  # 0-based
            
            start_row, start_col = a1_to_indices(start_cell)
            end_row, end_col = a1_to_indices(end_cell)
            
            # First unmerge in case already merged, then merge
            requests = [
                {
                    'unmergeCells': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': start_row,
                            'endRowIndex': end_row + 1,
                            'startColumnIndex': start_col,
                            'endColumnIndex': end_col + 1
                        }
                    }
                },
                {
                    'mergeCells': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': start_row,
                            'endRowIndex': end_row + 1,
                            'startColumnIndex': start_col,
                            'endColumnIndex': end_col + 1
                        },
                        'mergeType': 'MERGE_ALL'
                    }
                }
            ]
            
            # Execute
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            logging.info(f"✅ Merged {range_notation}")
            return True
        
        except HttpError as e:
            # Ignore unmerge errors (cells might not be merged), but log merge failures
            if 'unmergeCells' not in str(e):
                logging.error(f"❌ Merge failed for {range_notation}: {e}")
            return False


def test_performance():
    """Compare gspread vs direct API performance"""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
    
    print("=" * 60)
    print("PERFORMANCE TEST: gspread vs Direct API v4")
    print("=" * 60)
    
    # Test 1: gspread (SLOW)
    print("\n1️⃣  Testing gspread (old method)...")
    t0 = time.time()
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.worksheet('Live Dashboard v2')
    data = worksheet.get('A1:A2')
    t1 = time.time()
    print(f"   ⏱️  gspread time: {t1-t0:.2f}s")
    print(f"   📊 Data: {data}")
    
    # Test 2: Direct API v4 (FAST)
    print("\n2️⃣  Testing Direct API v4 (new method)...")
    t2 = time.time()
    fast_api = FastSheetsAPI()
    data2 = fast_api.read_range(SPREADSHEET_ID, 'Live Dashboard v2!A1:A2')
    t3 = time.time()
    print(f"   ⏱️  Direct API time: {t3-t2:.2f}s")
    print(f"   📊 Data: {data2}")
    
    # Results
    print("\n" + "=" * 60)
    print(f"⚡ SPEEDUP: {(t1-t0)/(t3-t2):.1f}x faster with Direct API!")
    print("=" * 60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    test_performance()
