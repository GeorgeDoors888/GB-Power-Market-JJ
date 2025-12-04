#!/usr/bin/env python3
"""
add_chart_and_map.py
--------------------
Adds the main combo chart and generator map to the V3 Dashboard.
This script uses the Google Sheets API to create and configure the chart
and places a placeholder for the map.
"""

import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'
DASHBOARD_SHEET_NAME = 'Dashboard'
CHART_DATA_SHEET_NAME = 'Chart Data'

def get_client():
    """Authorize and return gspread client."""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def add_chart_and_map(ss):
    """Adds the combo chart and map placeholder to the dashboard."""
    print(f"--- Adding Chart & Map to '{DASHBOARD_SHEET_NAME}' ---")
    
    try:
        dashboard_sheet = ss.worksheet(DASHBOARD_SHEET_NAME)
        chart_data_sheet = ss.worksheet(CHART_DATA_SHEET_NAME)
    except gspread.WorksheetNotFound as e:
        print(f"❌ Error: Worksheet not found - {e}. Please ensure 'Dashboard' and 'Chart Data' sheets exist.")
        return

    dashboard_sheet_id = dashboard_sheet.id
    chart_data_sheet_id = chart_data_sheet.id

    # --- Chart Definition (based on V3 plan) ---
    chart_spec = {
        "title": "GB Market Overview (Live)",
        "basicChart": {
            "chartType": "COMBO",
            "legendPosition": "BOTTOM_LEGEND",
            "axis": [
                {"position": "BOTTOM_AXIS", "title": "Settlement Period"},
                {"position": "LEFT_AXIS", "title": "MW"},
                {"position": "RIGHT_AXIS", "title": "Price (£/MWh)"}
            ],
            "domains": [
                {"domain": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 0, "endRowIndex": 49, "startColumnIndex": 0, "endColumnIndex": 1}]}}}
            ],
            "series": [
                # Series 1: DA Price (Line, Right Axis)
                {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 0, "endRowIndex": 49, "startColumnIndex": 1, "endColumnIndex": 2}]}}, "targetAxis": "RIGHT_AXIS", "type": "LINE"},
                # Series 2: Imbalance Price (Line, Right Axis)
                {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 0, "endRowIndex": 49, "startColumnIndex": 2, "endColumnIndex": 3}]}}, "targetAxis": "RIGHT_AXIS", "type": "LINE"},
                # Series 3: Demand (Area, Left Axis)
                {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 0, "endRowIndex": 49, "startColumnIndex": 3, "endColumnIndex": 4}]}}, "targetAxis": "LEFT_AXIS", "type": "AREA"},
                # Series 4: Generation (Area, Left Axis)
                {"series": {"sourceRange": {"sources": [{"sheetId": chart_data_sheet_id, "startRowIndex": 0, "endRowIndex": 49, "startColumnIndex": 4, "endColumnIndex": 5}]}}, "targetAxis": "LEFT_AXIS", "type": "AREA"},
            ],
            "headerCount": 1
        }
    }
    
    position_spec = {
        "overlayPosition": {
            "anchorCell": {"sheetId": dashboard_sheet_id, "rowIndex": 4, "columnIndex": 11}, # L5
            "widthPixels": 800,
            "heightPixels": 400
        }
    }


    # --- Map Placeholder ---
    # A simple text box as a placeholder for the map image/link
    dashboard_sheet.update(range_name='L26', values=[['(Placeholder for embedded Google Map of Generator Locations)']])


    print("   1. Deleting existing charts to prevent duplicates...")
    # Get all charts in the sheet and delete them
    sheet_metadata = ss.fetch_sheet_metadata()
    dashboard_sheet_properties = next((s for s in sheet_metadata['sheets'] if s['properties']['sheetId'] == dashboard_sheet_id), None)
    
    if dashboard_sheet_properties and 'charts' in dashboard_sheet_properties:
        charts = dashboard_sheet_properties['charts']
        if charts:
            requests = [{"deleteEmbeddedObject": {"objectId": chart['chartId']}} for chart in charts]
            ss.batch_update({"requests": requests})
            print(f"   ✅ Deleted {len(charts)} old chart(s).")
        else:
            print("   No existing charts found to delete.")
    else:
        print("   No existing charts found to delete.")


    print("   2. Creating and inserting the new combo chart...")
    request_body = {
        'requests': [{
            'addChart': {
                'chart': {
                    'spec': chart_spec,
                    'position': position_spec
                }
            }
        }]
    }
    ss.batch_update(request_body)
    
    print("--- ✅ Chart and Map placeholder added successfully! ---")


def main():
    try:
        client = get_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        add_chart_and_map(spreadsheet)
        sheet_id = spreadsheet.worksheet(DASHBOARD_SHEET_NAME).id
        print(f"\n🔗 View your updated dashboard: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet_id}")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
