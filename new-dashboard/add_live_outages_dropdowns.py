#!/usr/bin/env python3
"""
Add dropdowns and data validation to Live Outages sheet
"""

import sys
from google.oauth2 import service_account
import gspread
from google.cloud import bigquery

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def main():
    print("🔄 Adding dropdowns to Live Outages sheet...")
    
    # Connect to Google Sheets
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('Live Outages')
    
    # Connect to BigQuery
    bq_creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json'
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location='US')
    
    print("📋 Getting unique BM Units and Asset Names...")
    
    # Get unique BM Units
    query = f"""
    WITH latest_outages AS (
        SELECT 
            affectedUnit,
            ROW_NUMBER() OVER (PARTITION BY affectedUnit ORDER BY revisionNumber DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
    )
    SELECT DISTINCT affectedUnit
    FROM latest_outages
    WHERE rn = 1
    ORDER BY affectedUnit
    """
    
    bmu_df = bq_client.query(query).to_dataframe()
    bmu_list = ['All Units'] + bmu_df['affectedUnit'].tolist()
    
    print(f"✅ Found {len(bmu_list)-1} unique BM Units")
    
    # Add dropdown options to hidden columns
    # BM Units in column L (hidden)
    sheet.update('L1', [['BM_UNITS']])
    sheet.update('L2', [[bmu] for bmu in bmu_list])
    
    print("✅ Added BM Units list to column L")
    
    # Add filter input rows
    sheet.update('A7', [['All Units']])  # Default BM Unit filter
    sheet.update('C7', [['']])  # Asset name search
    sheet.update('E7', [['']])  # Start date
    sheet.update('G7', [['']])  # End date
    
    # Add data validation for BM Unit dropdown (A7)
    sheet.spreadsheet.batch_update({
        'requests': [
            {
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet.id,
                        'startRowIndex': 6,  # Row 7
                        'endRowIndex': 7,
                        'startColumnIndex': 0,  # Column A
                        'endColumnIndex': 1
                    },
                    'rule': {
                        'condition': {
                            'type': 'ONE_OF_RANGE',
                            'values': [
                                {
                                    'userEnteredValue': f'=\'Live Outages\'!L2:L{len(bmu_list)+1}'
                                }
                            ]
                        },
                        'showCustomUi': True,
                        'strict': False
                    }
                }
            }
        ]
    })
    
    print("✅ Added dropdown validation to A7 (BM Unit filter)")
    
    # Hide column L
    sheet.spreadsheet.batch_update({
        'requests': [
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet.id,
                        'dimension': 'COLUMNS',
                        'startIndex': 11,  # Column L (0-indexed)
                        'endIndex': 12
                    },
                    'properties': {
                        'hiddenByUser': True
                    },
                    'fields': 'hiddenByUser'
                }
            }
        ]
    })
    
    print("✅ Hidden column L (dropdown data)")
    
    # Add instructions
    sheet.update('A8', [['↑ Select BM Unit to filter, or type Asset/Date to search manually']])
    
    # Format instruction row
    sheet.format('A8:J8', {
        'textFormat': {
            'fontSize': 9,
            'italic': True,
            'foregroundColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}
        }
    })
    
    print("=" * 80)
    print("✅ LIVE OUTAGES DROPDOWNS ADDED SUCCESSFULLY")
    print("=" * 80)
    print("\n📝 Usage:")
    print("   1. Select A7 dropdown to filter by BM Unit")
    print("   2. Type in C7 to search by Asset Name")
    print("   3. Enter dates in E7/G7 (YYYY-MM-DD format)")
    print("   4. Use Google Sheets Filter Views (Data → Filter views) for live filtering")
    print("\n🔗 Open sheet:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={sheet.id}")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
