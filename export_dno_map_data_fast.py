#!/usr/bin/env python3
"""
export_dno_map_data_fast.py

FAST version using direct BigQuery → CSV → Google Sheets
Bypasses slow to_dataframe() conversion
"""

from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import csv
import io

PROJECT_ID = "inner-cinema-476211-u9"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

bq_client = bigquery.Client(project=PROJECT_ID, location="US")

def export_dno_totals_fast():
    """Export DNO total costs - optimized"""
    print("\n🚀 FAST Export: DNO Totals\n")

    query = f"""
    SELECT
        c.dno_full_name,
        SUM(c.allocated_total_cost) as total_cost,
        SUM(c.allocated_voltage_cost) as voltage_cost,
        SUM(c.allocated_thermal_cost) as thermal_cost,
        AVG(c.area_sq_km) as area_sq_km,
        COUNT(*) as months,
        g.dno_code,
        ST_Y(ST_CENTROID(g.boundary)) as lat,
        ST_X(ST_CENTROID(g.boundary)) as lon
    FROM `{PROJECT_ID}.uk_energy_prod.constraint_costs_by_dno` c
    LEFT JOIN `{PROJECT_ID}.uk_energy_prod.neso_dno_boundaries` g
        ON c.dno_id = g.dno_id
    GROUP BY c.dno_full_name, g.dno_code, g.boundary
    ORDER BY total_cost DESC
    LIMIT 14
    """

    print("   Querying BigQuery...")
    query_job = bq_client.query(query)

    # Get results as list (faster than to_dataframe)
    rows = []
    rows.append(['DNO Name', 'Total Cost (£)', 'Voltage (£)', 'Thermal (£)',
                 'Area (km²)', 'Months', 'Code', 'Latitude', 'Longitude'])

    for row in query_job:
        rows.append([
            row.dno_full_name,
            float(row.total_cost),
            float(row.voltage_cost),
            float(row.thermal_cost),
            float(row.area_sq_km) if row.area_sq_km else 0,
            int(row.months),
            row.dno_code or '',
            float(row.lat) if row.lat else 0,
            float(row.lon) if row.lon else 0
        ])

    print(f"   ✅ Retrieved {len(rows)-1} DNOs")
    return rows

def export_to_sheets_fast(data, sheet_name, start_cell='A1'):
    """Fast export using API v4 batch update"""
    print(f"\n📤 Exporting to '{sheet_name}'...")

    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)

    # Single batch update (fast)
    body = {
        'valueInputOption': 'RAW',
        'data': [{
            'range': f"'{sheet_name}'!{start_cell}",
            'values': data
        }]
    }

    try:
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        updated = result.get('totalUpdatedCells', 0)
        print(f"   ✅ Updated {updated} cells in '{sheet_name}'")
        return True

    except Exception as e:
        if 'Unable to parse range' in str(e):
            print(f"   ⚠️ Sheet '{sheet_name}' doesn't exist. Creating...")

            # Create sheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {'rowCount': 2000, 'columnCount': 20}
                    }
                }
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': [request]}
            ).execute()

            print(f"   ✅ Created '{sheet_name}', retrying export...")
            return export_to_sheets_fast(data, sheet_name, start_cell)
        else:
            print(f"   ❌ Error: {e}")
            return False

def main():
    print("=" * 70)
    print("🗺️  FAST DNO MAP DATA EXPORT")
    print("=" * 70)

    # Export DNO totals
    dno_data = export_dno_totals_fast()
    success = export_to_sheets_fast(dno_data, 'DNO Map Data', 'A1')

    if success:
        print(f"\n" + "=" * 70)
        print("✅ EXPORT COMPLETE")
        print("=" * 70)
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"📋 Sheet: 'DNO Map Data'")
        print(f"\n📊 Data exported:")
        print(f"   • {len(dno_data)-1} DNO regions")
        print(f"   • Total costs, voltage, thermal breakdown")
        print(f"   • Latitude/Longitude for mapping")
        print(f"\n🗺️ To Create Geo Chart:")
        print(f"   1. Select columns A:B (DNO Name, Total Cost)")
        print(f"   2. Insert → Chart → Geo chart")
        print(f"   3. Customize → Region: United Kingdom")
        print(f"   4. Color by: Total Cost")

if __name__ == "__main__":
    main()
