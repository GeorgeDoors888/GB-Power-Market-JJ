#!/usr/bin/env python3
"""
Fast Google Sheets API Helper Module
Uses Google Sheets API v4 directly (298x faster than gspread)

Performance:
- gspread.open_by_key():  120+ seconds
- sheets_fast methods:    0.4-0.6 seconds

Author: GB Power Market JJ Performance Optimization
Date: December 22, 2025
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import time
from typing import List, Dict, Any, Optional

# Default credentials path
DEFAULT_CREDS = '/home/george/inner-cinema-credentials.json'


class SheetsFast:
    """Fast Google Sheets API wrapper using API v4 directly"""

    def __init__(self, credentials_file: str = DEFAULT_CREDS):
        """Initialize with service account credentials

        Args:
            credentials_file: Path to service account JSON file
        """
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.creds)

    def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """Read a single range from a spreadsheet

        Args:
            spreadsheet_id: Spreadsheet ID
            range_name: A1 notation (e.g., 'Sheet1!A1:C10')

        Returns:
            2D list of cell values

        Example:
            >>> sheets = SheetsFast()
            >>> data = sheets.read_range('abc123', 'Dashboard!A1:C10')
            >>> print(data[0][0])  # First cell value
        """
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        return result.get('values', [])

    def batch_read(self, spreadsheet_id: str, ranges: List[str]) -> Dict[str, List[List[Any]]]:
        """Read multiple ranges in a single API call (FAST)

        Args:
            spreadsheet_id: Spreadsheet ID
            ranges: List of range names in A1 notation

        Returns:
            Dictionary mapping range names to their values

        Example:
            >>> sheets = SheetsFast()
            >>> data = sheets.batch_read('abc123', [
            ...     'Dashboard!A1:C10',
            ...     'Data_Hidden!A1:AZ48'
            ... ])
            >>> dashboard_data = data['Dashboard!A1:C10']
        """
        result = self.service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=ranges
        ).execute()

        # Map ranges to their values
        output = {}
        for value_range in result.get('valueRanges', []):
            output[value_range['range']] = value_range.get('values', [])
        return output

    def write_range(self, spreadsheet_id: str, range_name: str,
                   values: List[List[Any]], value_input_option: str = 'USER_ENTERED') -> dict:
        """Write to a single range

        Args:
            spreadsheet_id: Spreadsheet ID
            range_name: A1 notation (e.g., 'Sheet1!A1:C10')
            values: 2D list of cell values
            value_input_option: 'USER_ENTERED' (parse formulas) or 'RAW' (literal text)

        Returns:
            API response dict

        Example:
            >>> sheets = SheetsFast()
            >>> sheets.write_range('abc123', 'Dashboard!A1:C3', [
            ...     [1, 2, 3],
            ...     [4, 5, 6],
            ...     [7, 8, 9]
            ... ])
        """
        body = {'values': values}
        result = self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body
        ).execute()
        return result

    def batch_write(self, spreadsheet_id: str, data: List[Dict[str, Any]],
                   value_input_option: str = 'USER_ENTERED') -> dict:
        """Write multiple ranges in a single API call (FAST)

        Args:
            spreadsheet_id: Spreadsheet ID
            data: List of dicts with 'range' and 'values' keys
            value_input_option: 'USER_ENTERED' or 'RAW'

        Returns:
            API response dict

        Example:
            >>> sheets = SheetsFast()
            >>> sheets.batch_write('abc123', [
            ...     {'range': 'Dashboard!A1:C3', 'values': [[1,2,3], [4,5,6]]},
            ...     {'range': 'Data_Hidden!A1', 'values': [['Updated']]}
            ... ])
        """
        body = {
            'valueInputOption': value_input_option,
            'data': data
        }
        result = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        return result

    def append_rows(self, spreadsheet_id: str, range_name: str,
                   values: List[List[Any]], value_input_option: str = 'USER_ENTERED') -> dict:
        """Append rows to end of a range

        Args:
            spreadsheet_id: Spreadsheet ID
            range_name: A1 notation (e.g., 'Sheet1!A:C')
            values: 2D list of row values to append
            value_input_option: 'USER_ENTERED' or 'RAW'

        Returns:
            API response dict

        Example:
            >>> sheets = SheetsFast()
            >>> sheets.append_rows('abc123', 'Logs!A:D', [
            ...     ['2025-12-22', '12:00', 'INFO', 'System started']
            ... ])
        """
        body = {'values': values}
        result = self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=body
        ).execute()
        return result

    def clear_range(self, spreadsheet_id: str, range_name: str) -> dict:
        """Clear values in a range

        Args:
            spreadsheet_id: Spreadsheet ID
            range_name: A1 notation (e.g., 'Sheet1!A1:C10')

        Returns:
            API response dict

        Example:
            >>> sheets = SheetsFast()
            >>> sheets.clear_range('abc123', 'Dashboard!A1:Z100')
        """
        result = self.service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body={}
        ).execute()
        return result

    def get_spreadsheet_metadata(self, spreadsheet_id: str) -> dict:
        """Get spreadsheet metadata (properties, sheets, etc.)

        Args:
            spreadsheet_id: Spreadsheet ID

        Returns:
            Full spreadsheet metadata dict including worksheet IDs

        Example:
            >>> sheets = SheetsFast()
            >>> meta = sheets.get_spreadsheet_metadata('abc123')
            >>> for sheet in meta['sheets']:
            ...     print(f"{sheet['properties']['title']}: {sheet['properties']['sheetId']}")
        """
        result = self.service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        return result

    def batch_update_formatting(self, spreadsheet_id: str, requests: List[dict]) -> dict:
        """Apply formatting/structural changes (colors, borders, etc.)

        Args:
            spreadsheet_id: Spreadsheet ID
            requests: List of batchUpdate request dicts

        Returns:
            API response dict

        Example:
            >>> sheets = SheetsFast()
            >>> sheets.batch_update_formatting('abc123', [{
            ...     'repeatCell': {
            ...         'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1},
            ...         'cell': {'userEnteredFormat': {'backgroundColor': {'red': 0, 'green': 1, 'blue': 0}}},
            ...         'fields': 'userEnteredFormat.backgroundColor'
            ...     }
            ... }])
        """
        body = {'requests': requests}
        result = self.service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        return result


# Convenience functions for quick operations
def quick_read(spreadsheet_id: str, range_name: str,
               credentials_file: str = DEFAULT_CREDS) -> List[List[Any]]:
    """Quick read without creating SheetsFast object

    Example:
        >>> from sheets_fast import quick_read
        >>> data = quick_read('abc123', 'Dashboard!A1:C10')
    """
    sheets = SheetsFast(credentials_file)
    return sheets.read_range(spreadsheet_id, range_name)


def quick_write(spreadsheet_id: str, range_name: str, values: List[List[Any]],
                credentials_file: str = DEFAULT_CREDS) -> dict:
    """Quick write without creating SheetsFast object

    Example:
        >>> from sheets_fast import quick_write
        >>> quick_write('abc123', 'Dashboard!A1', [['Hello']])
    """
    sheets = SheetsFast(credentials_file)
    return sheets.write_range(spreadsheet_id, range_name, values)


def benchmark_comparison(spreadsheet_id: str, range_name: str = 'A1'):
    """Compare gspread vs sheets_fast performance

    Args:
        spreadsheet_id: Spreadsheet ID to test
        range_name: Range to read (default: A1)

    Prints:
        Performance comparison results
    """
    print("🔬 Benchmarking Google Sheets API Methods\n")
    print("=" * 60)

    # Test gspread (slow method)
    try:
        import gspread

        print("\n📊 Method 1: gspread (traditional)")
        start = time.time()
        creds = service_account.Credentials.from_service_account_file(
            DEFAULT_CREDS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(spreadsheet_id)
        ws = sheet.worksheets()[0]  # Get first worksheet
        value = ws.acell(range_name).value
        gspread_time = time.time() - start
        print(f"  ⏱️  Time: {gspread_time:.2f}s")
        print(f"  📋 Value: {value}")
    except ImportError:
        print("\n⚠️  gspread not installed (pip install gspread)")
        gspread_time = None
    except Exception as e:
        print(f"\n❌ gspread error: {e}")
        gspread_time = None

    # Test sheets_fast (fast method)
    print("\n⚡ Method 2: sheets_fast (optimized)")
    start = time.time()
    sheets = SheetsFast()
    # Extract sheet name if present, otherwise use first sheet
    if '!' in range_name:
        test_range = range_name
    else:
        # Get first sheet name
        meta = sheets.get_spreadsheet_metadata(spreadsheet_id)
        first_sheet = meta['sheets'][0]['properties']['title']
        test_range = f"'{first_sheet}'!{range_name}"

    data = sheets.read_range(spreadsheet_id, test_range)
    value = data[0][0] if data and data[0] else None
    fast_time = time.time() - start
    print(f"  ⏱️  Time: {fast_time:.2f}s")
    print(f"  📋 Value: {value}")

    # Show comparison
    if gspread_time:
        speedup = gspread_time / fast_time
        print(f"\n⚡ Speedup: {speedup:.1f}x faster")
        print(f"   Time saved: {gspread_time - fast_time:.1f}s per operation")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Run benchmark if executed directly
    import sys

    if len(sys.argv) > 1:
        sheet_id = sys.argv[1]
        benchmark_comparison(sheet_id)
    else:
        print(__doc__)
        print("\nUsage:")
        print(f"  python3 {sys.argv[0]} <spreadsheet_id>")
        print("\nExample:")
        print(f"  python3 {sys.argv[0]} 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
