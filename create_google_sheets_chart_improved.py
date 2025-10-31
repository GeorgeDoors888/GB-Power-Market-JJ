#!/usr/bin/env python3
"""
Create Google Sheets Charts Programmatically
Improved version with error handling and flexibility
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
from typing import Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. Configuration ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_FILE = "service.json"

class GoogleSheetsChartCreator:
    """Helper class for creating charts in Google Sheets"""
    
    def __init__(self, service_account_file: str):
        """Initialize with service account credentials"""
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_file, 
            scopes=SCOPES
        )
        self.service = build("sheets", "v4", credentials=self.creds)
    
    def create_line_chart(
        self,
        spreadsheet_id: str,
        sheet_id: int = 0,
        title: str = "Chart",
        x_axis_title: str = "X-Axis",
        y_axis_title: str = "Y-Axis",
        date_column: str = "A",  # e.g., "A" for column A
        value_column: str = "B",  # e.g., "B" for column B
        start_row: int = 2,  # Skip header row
        end_row: int = 100,
        position: str = "new_sheet",  # "new_sheet" or "overlay"
        chart_position: Optional[Dict[str, int]] = None  # For overlay: {"row": 0, "col": 3}
    ) -> Dict[str, Any]:
        """
        Create a line chart in Google Sheets
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_id: The sheet ID (0 for first sheet)
            title: Chart title
            x_axis_title: X-axis label
            y_axis_title: Y-axis label
            date_column: Column letter for X-axis data (e.g., "A")
            value_column: Column letter for Y-axis data (e.g., "B")
            start_row: First data row (1-indexed, usually 2 to skip header)
            end_row: Last data row (1-indexed)
            position: "new_sheet" or "overlay"
            chart_position: For overlay, dict with {"row": 0, "col": 3}
        
        Returns:
            API response
        """
        
        # Convert column letters to indices (A=0, B=1, etc.)
        def col_letter_to_index(letter: str) -> int:
            return ord(letter.upper()) - ord('A')
        
        date_col_idx = col_letter_to_index(date_column)
        value_col_idx = col_letter_to_index(value_column)
        
        # Determine chart position
        if position == "new_sheet":
            chart_pos = {"newSheet": True}
        else:
            if chart_position is None:
                chart_position = {"row": 0, "col": 3}  # Default to D1
            chart_pos = {
                "overlayPosition": {
                    "anchorCell": {
                        "sheetId": sheet_id,
                        "rowIndex": chart_position["row"],
                        "columnIndex": chart_position["col"]
                    }
                }
            }
        
        # Build chart request
        chart_request = {
            "requests": [{
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": title,
                            "basicChart": {
                                "chartType": "LINE",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {
                                        "position": "BOTTOM_AXIS",
                                        "title": x_axis_title
                                    },
                                    {
                                        "position": "LEFT_AXIS",
                                        "title": y_axis_title
                                    }
                                ],
                                "domains": [{
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": start_row - 1,  # Convert to 0-indexed
                                                "endRowIndex": end_row,
                                                "startColumnIndex": date_col_idx,
                                                "endColumnIndex": date_col_idx + 1
                                            }]
                                        }
                                    }
                                }],
                                "series": [{
                                    "series": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": start_row - 1,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": value_col_idx,
                                                "endColumnIndex": value_col_idx + 1
                                            }]
                                        }
                                    },
                                    "targetAxis": "LEFT_AXIS"
                                }]
                            }
                        },
                        "position": chart_pos
                    }
                }
            }]
        }
        
        # Execute request
        try:
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=chart_request
            ).execute()
            
            logging.info(f"✅ Chart '{title}' created successfully!")
            return response
            
        except Exception as e:
            logging.error(f"❌ Failed to create chart: {e}")
            raise
    
    def create_multi_series_line_chart(
        self,
        spreadsheet_id: str,
        sheet_id: int = 0,
        title: str = "Multi-Series Chart",
        x_axis_title: str = "X-Axis",
        y_axis_title: str = "Y-Axis",
        date_column: str = "A",
        value_columns: list = ["B", "C", "D"],  # Multiple series
        series_names: Optional[list] = None,  # Names for each series
        start_row: int = 2,
        end_row: int = 100,
        position: str = "new_sheet"
    ) -> Dict[str, Any]:
        """
        Create a line chart with multiple series (e.g., SSP, SBP, SMP)
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_id: The sheet ID (0 for first sheet)
            title: Chart title
            x_axis_title: X-axis label
            y_axis_title: Y-axis label
            date_column: Column letter for X-axis data
            value_columns: List of column letters for Y-axis data (e.g., ["B", "C", "D"])
            series_names: Optional list of names for each series
            start_row: First data row (1-indexed)
            end_row: Last data row (1-indexed)
            position: "new_sheet" or "overlay"
        
        Returns:
            API response
        """
        
        def col_letter_to_index(letter: str) -> int:
            return ord(letter.upper()) - ord('A')
        
        date_col_idx = col_letter_to_index(date_column)
        
        # Build series for each value column
        series_list = []
        for i, col in enumerate(value_columns):
            col_idx = col_letter_to_index(col)
            series = {
                "series": {
                    "sourceRange": {
                        "sources": [{
                            "sheetId": sheet_id,
                            "startRowIndex": start_row - 1,
                            "endRowIndex": end_row,
                            "startColumnIndex": col_idx,
                            "endColumnIndex": col_idx + 1
                        }]
                    }
                },
                "targetAxis": "LEFT_AXIS"
            }
            
            # Add series name if provided
            if series_names and i < len(series_names):
                series["series"]["name"] = series_names[i]
            
            series_list.append(series)
        
        # Build chart request
        chart_request = {
            "requests": [{
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": title,
                            "basicChart": {
                                "chartType": "LINE",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": x_axis_title},
                                    {"position": "LEFT_AXIS", "title": y_axis_title}
                                ],
                                "domains": [{
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [{
                                                "sheetId": sheet_id,
                                                "startRowIndex": start_row - 1,
                                                "endRowIndex": end_row,
                                                "startColumnIndex": date_col_idx,
                                                "endColumnIndex": date_col_idx + 1
                                            }]
                                        }
                                    }
                                }],
                                "series": series_list
                            }
                        },
                        "position": {"newSheet": True} if position == "new_sheet" else {
                            "overlayPosition": {
                                "anchorCell": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 5}
                            }
                        }
                    }
                }
            }]
        }
        
        # Execute request
        try:
            response = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=chart_request
            ).execute()
            
            logging.info(f"✅ Multi-series chart '{title}' created successfully!")
            return response
            
        except Exception as e:
            logging.error(f"❌ Failed to create chart: {e}")
            raise


# --- Example Usage ---
if __name__ == "__main__":
    
    # Initialize chart creator
    chart_creator = GoogleSheetsChartCreator(SERVICE_FILE)
    
    # Your spreadsheet ID
    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
    
    # Example 1: Simple SSP vs Date chart
    try:
        chart_creator.create_line_chart(
            spreadsheet_id=SPREADSHEET_ID,
            sheet_id=0,
            title="System Sell Price (SSP) vs Date",
            x_axis_title="Date",
            y_axis_title="SSP (£/MWh)",
            date_column="A",  # Date in column A
            value_column="B",  # SSP in column B
            start_row=2,  # Skip header
            end_row=100,  # Adjust based on your data
            position="new_sheet"
        )
    except Exception as e:
        logging.error(f"Failed to create simple chart: {e}")
    
    # Example 2: Multi-series chart (SSP, SBP, SMP)
    try:
        chart_creator.create_multi_series_line_chart(
            spreadsheet_id=SPREADSHEET_ID,
            sheet_id=0,
            title="System Prices Comparison",
            x_axis_title="Date",
            y_axis_title="Price (£/MWh)",
            date_column="A",
            value_columns=["B", "C", "D"],  # SSP, SBP, SMP
            series_names=["SSP", "SBP", "SMP"],
            start_row=2,
            end_row=100,
            position="new_sheet"
        )
    except Exception as e:
        logging.error(f"Failed to create multi-series chart: {e}")
    
    print("\n✅ All charts created successfully!")
