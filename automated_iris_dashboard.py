#!/usr/bin/env python3
"""
Automated IRIS Dashboard - Charts and Data
Automatically queries BigQuery, updates Google Sheets, and creates charts
No manual intervention needed!

Usage:
    python automated_iris_dashboard.py          # Run once
    python automated_iris_dashboard.py --loop   # Run continuously (every 5 min)
"""

import os
import sys
import time
import logging
import argparse
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread

# Configuration
BQ_PROJECT = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/bigquery"
]

# Spreadsheet configuration
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"  # GB Energy Dashboard
UPDATE_INTERVAL = 300  # 5 minutes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_dashboard.log'),
        logging.StreamHandler()
    ]
)

class IRISDashboard:
    """Automated IRIS Dashboard Manager"""
    
    def __init__(self, service_account_file: str = None):
        """Initialize with Application Default Credentials for BigQuery, OAuth for Sheets"""
        # BigQuery with Application Default Credentials (auto-detects credentials)
        # This matches the pattern used by update_graph_data.py
        self.bq_client = bigquery.Client(project=BQ_PROJECT)
        
        # Google Sheets with OAuth
        oauth_creds = self._get_oauth_credentials()
        self.sheets_service = build("sheets", "v4", credentials=oauth_creds)
        self.gc = gspread.authorize(oauth_creds)
        
        self.spreadsheet = None
        self.spreadsheet_id = None
        
        logging.info("✅ Dashboard initialized (Application Default Credentials for BigQuery, OAuth for Sheets)")
    
    def _get_oauth_credentials(self):
        """Get OAuth credentials from token.pickle"""
        creds = None
        
        # Load existing token
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                logging.info("📋 Loaded OAuth token from token.pickle")
                
                # Check if BigQuery scope is present
                if creds and hasattr(creds, 'scopes'):
                    if 'https://www.googleapis.com/auth/bigquery' not in (creds.scopes or []):
                        logging.warning("⚠️ Token missing BigQuery scope - will request new token")
                        creds = None  # Force new authorization
        
        # Refresh if expired or missing scopes
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logging.info("🔄 Refreshed OAuth token")
                except Exception as e:
                    logging.warning(f"⚠️ Token refresh failed: {e} - requesting new token")
                    creds = None
            
            if not creds and os.path.exists('credentials.json'):
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                logging.info("✅ Got new OAuth token via browser (with BigQuery scope)")
            elif not creds:
                raise FileNotFoundError(
                    "❌ Neither token.pickle nor credentials.json found. "
                    "Please run authorize_google_docs.py first."
                )
            
            # Save token for next time
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def get_or_create_spreadsheet(self) -> str:
        """Get existing GB Energy Dashboard spreadsheet"""
        try:
            # Open existing GB Energy Dashboard
            self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
            self.spreadsheet_id = SPREADSHEET_ID
            logging.info(f"📊 Connected to GB Energy Dashboard")
            logging.info(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        except Exception as e:
            logging.error(f"❌ Could not open GB Energy Dashboard: {e}")
            logging.error(f"   Make sure the service account has access to the spreadsheet")
            logging.error(f"   Service account: jibber-jabber-knowledge@appspot.gserviceaccount.com")
            raise
        
        return self.spreadsheet_id
    
    def query_bigquery(self, query: str) -> List[Dict[str, Any]]:
        """Execute BigQuery query and return results as list of dicts"""
        try:
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            # Convert to list of dicts
            data = []
            for row in results:
                data.append(dict(row))
            
            logging.info(f"✅ Query returned {len(data)} rows")
            return data
            
        except Exception as e:
            logging.error(f"❌ BigQuery query failed: {e}")
            return []
    
    def update_sheet(self, sheet_name: str, data: List[Dict[str, Any]], 
                     headers: Optional[List[str]] = None) -> bool:
        """Update or create sheet with data"""
        try:
            # Get or create worksheet
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=len(data) + 1,
                    cols=len(data[0]) if data else 10
                )
            
            if not data:
                logging.warning(f"⚠️ No data for sheet: {sheet_name}")
                return False
            
            # Prepare data for writing
            if headers is None:
                headers = list(data[0].keys())
            
            # Convert data to rows
            rows = [headers]
            for row_dict in data:
                row = [row_dict.get(h, '') for h in headers]
                rows.append(row)
            
            # Write to sheet
            worksheet.update('A1', rows, value_input_option='USER_ENTERED')
            
            logging.info(f"✅ Updated sheet '{sheet_name}' with {len(data)} rows")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to update sheet '{sheet_name}': {e}")
            return False
    
    def create_chart(self, sheet_name: str, chart_config: Dict[str, Any]) -> bool:
        """Create or update chart on a sheet"""
        try:
            # Get sheet ID
            worksheet = self.spreadsheet.worksheet(sheet_name)
            sheet_id = worksheet.id
            
            # Delete existing charts on this sheet (optional)
            # This ensures we don't create duplicates
            charts = worksheet.get_all_charts()
            if charts:
                delete_requests = [{"deleteEmbeddedObject": {"objectId": chart.id}} for chart in charts]
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": delete_requests}
                ).execute()
            
            # Create new chart
            chart_request = {
                "requests": [{
                    "addChart": {
                        "chart": {
                            "spec": chart_config["spec"],
                            "position": chart_config.get("position", {
                                "overlayPosition": {
                                    "anchorCell": {
                                        "sheetId": sheet_id,
                                        "rowIndex": 0,
                                        "columnIndex": chart_config.get("start_col", 5)
                                    }
                                }
                            })
                        }
                    }
                }]
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=chart_request
            ).execute()
            
            logging.info(f"✅ Created chart on '{sheet_name}'")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to create chart on '{sheet_name}': {e}")
            return False
    
    def update_system_prices(self):
        """Update System Prices (MID Market Price) with chart"""
        logging.info("📊 Updating System Prices...")
        
        # Query last 100 settlement periods
        query = f"""
        SELECT 
            FORMAT_DATETIME('%Y-%m-%d %H:%M', settlementDate) as datetime,
            settlementPeriod as period,
            ROUND(price, 2) as price,
            ROUND(volume, 2) as volume
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 2 DAY)
        ORDER BY settlementDate DESC, settlementPeriod DESC
        LIMIT 100
        """
        
        data = self.query_bigquery(query)
        
        if not data:
            logging.warning("⚠️ No system prices data")
            return
        
        # Reverse so oldest first (for chart)
        data = list(reversed(data))
        
        # Update sheet
        self.update_sheet(
            "System Prices",
            data,
            headers=["datetime", "period", "price", "volume"]
        )
        
        # Get sheet ID
        worksheet = self.spreadsheet.worksheet("System Prices")
        sheet_id = worksheet.id
        
        # Create multi-line chart
        chart_config = {
            "spec": {
                "title": "System Prices - Last 48 Hours",
                "basicChart": {
                    "chartType": "LINE",
                    "legendPosition": "BOTTOM_LEGEND",
                    "axis": [
                        {"position": "BOTTOM_AXIS", "title": "Time"},
                        {"position": "LEFT_AXIS", "title": "Price (£/MWh)"}
                    ],
                    "domains": [{
                        "domain": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(data) + 1,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 1
                                }]
                            }
                        }
                    }],
                    "series": [
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 1,
                                        "endRowIndex": len(data) + 1,
                                        "startColumnIndex": 2,
                                        "endColumnIndex": 3
                                    }]
                                }
                            },
                            "targetAxis": "LEFT_AXIS"
                        },
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 1,
                                        "endRowIndex": len(data) + 1,
                                        "startColumnIndex": 3,
                                        "endColumnIndex": 4
                                    }]
                                }
                            },
                            "targetAxis": "LEFT_AXIS"
                        },
                        {
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": sheet_id,
                                        "startRowIndex": 1,
                                        "endRowIndex": len(data) + 1,
                                        "startColumnIndex": 4,
                                        "endColumnIndex": 5
                                    }]
                                }
                            },
                            "targetAxis": "LEFT_AXIS"
                        }
                    ]
                }
            },
            "start_col": 6
        }
        
        self.create_chart("System Prices", chart_config)
    
    def update_grid_frequency(self):
        """Update Grid Frequency with chart"""
        logging.info("⚡ Updating Grid Frequency...")
        
        query = f"""
        SELECT 
            FORMAT_DATETIME('%Y-%m-%d %H:%M:%S', measurementTime) as time,
            ROUND(frequency, 3) as frequency
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_freq_iris`
        WHERE measurementTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
        ORDER BY measurementTime DESC
        LIMIT 200
        """
        
        data = self.query_bigquery(query)
        
        if not data:
            logging.warning("⚠️ No frequency data")
            return
        
        data = list(reversed(data))
        
        self.update_sheet("Grid Frequency", data, headers=["time", "frequency"])
        
        # Create chart
        worksheet = self.spreadsheet.worksheet("Grid Frequency")
        sheet_id = worksheet.id
        
        chart_config = {
            "spec": {
                "title": "Grid Frequency - Last Hour",
                "basicChart": {
                    "chartType": "LINE",
                    "legendPosition": "BOTTOM_LEGEND",
                    "axis": [
                        {"position": "BOTTOM_AXIS", "title": "Time"},
                        {"position": "LEFT_AXIS", "title": "Frequency (Hz)"}
                    ],
                    "domains": [{
                        "domain": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(data) + 1,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 1
                                }]
                            }
                        }
                    }],
                    "series": [{
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(data) + 1,
                                    "startColumnIndex": 1,
                                    "endColumnIndex": 2
                                }]
                            }
                        },
                        "targetAxis": "LEFT_AXIS"
                    }]
                }
            },
            "start_col": 4
        }
        
        self.create_chart("Grid Frequency", chart_config)
    
    def update_fuel_generation(self):
        """Update Fuel Generation Mix"""
        logging.info("🔥 Updating Fuel Generation...")
        
        query = f"""
        SELECT 
            fuelType as fuel,
            ROUND(AVG(generation), 0) as avg_mw,
            ROUND(MAX(generation), 0) as max_mw,
            ROUND(MIN(generation), 0) as min_mw
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_fuelinst_iris`
        WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 1 HOUR)
        GROUP BY fuelType
        ORDER BY avg_mw DESC
        """
        
        data = self.query_bigquery(query)
        
        if not data:
            logging.warning("⚠️ No fuel generation data")
            return
        
        self.update_sheet("Fuel Generation", data, headers=["fuel", "avg_mw", "max_mw", "min_mw"])
        
        # Create bar chart
        worksheet = self.spreadsheet.worksheet("Fuel Generation")
        sheet_id = worksheet.id
        
        chart_config = {
            "spec": {
                "title": "Generation by Fuel Type (Last Hour Average)",
                "basicChart": {
                    "chartType": "BAR",
                    "legendPosition": "BOTTOM_LEGEND",
                    "axis": [
                        {"position": "BOTTOM_AXIS", "title": "Generation (MW)"},
                        {"position": "LEFT_AXIS", "title": "Fuel Type"}
                    ],
                    "domains": [{
                        "domain": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(data) + 1,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 1
                                }]
                            }
                        }
                    }],
                    "series": [{
                        "series": {
                            "sourceRange": {
                                "sources": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(data) + 1,
                                    "startColumnIndex": 1,
                                    "endColumnIndex": 2
                                }]
                            }
                        },
                        "targetAxis": "BOTTOM_AXIS"
                    }]
                }
            },
            "start_col": 6
        }
        
        self.create_chart("Fuel Generation", chart_config)
    
    def update_recent_activity(self):
        """Update Recent Activity summary"""
        logging.info("📋 Updating Recent Activity...")
        
        query = f"""
        SELECT 
            'BOD' as dataset,
            COUNT(*) as records,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', MAX(ingested_utc)) as last_update
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_bod_iris`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        
        UNION ALL
        
        SELECT 
            'BOALF',
            COUNT(*),
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', MAX(ingested_utc))
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_boalf_iris`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        
        UNION ALL
        
        SELECT 
            'MELS',
            COUNT(*),
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', MAX(ingested_utc))
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_mels_iris`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        
        UNION ALL
        
        SELECT 
            'FREQ',
            COUNT(*),
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', MAX(ingested_utc))
        FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_freq_iris`
        WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        
        ORDER BY records DESC
        """
        
        data = self.query_bigquery(query)
        
        if data:
            self.update_sheet("Recent Activity", data, headers=["dataset", "records", "last_update"])
    
    def run_full_update(self):
        """Run full dashboard update"""
        logging.info("=" * 60)
        logging.info("🚀 Starting Dashboard Update")
        logging.info("=" * 60)
        
        start_time = time.time()
        
        # Get or create spreadsheet
        self.get_or_create_spreadsheet()
        
        # Update all sections
        self.update_system_prices()
        self.update_grid_frequency()
        self.update_fuel_generation()
        self.update_recent_activity()
        
        elapsed = time.time() - start_time
        
        logging.info("=" * 60)
        logging.info(f"✅ Dashboard updated in {elapsed:.1f}s")
        logging.info(f"📊 View at: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        logging.info("=" * 60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Automated IRIS Dashboard')
    parser.add_argument('--loop', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=300, help='Update interval in seconds (default: 300)')
    args = parser.parse_args()
    
    # Check service account file exists
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logging.error(f"❌ Service account file not found: {SERVICE_ACCOUNT_FILE}")
        sys.exit(1)
    
    # Create dashboard
    dashboard = IRISDashboard(SERVICE_ACCOUNT_FILE)
    
    if args.loop:
        logging.info(f"🔄 Running in loop mode (every {args.interval}s)")
        logging.info("Press Ctrl+C to stop")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                logging.info(f"\n📊 Update Cycle #{cycle}")
                dashboard.run_full_update()
                
                logging.info(f"⏳ Sleeping for {args.interval}s...")
                time.sleep(args.interval)
                
            except KeyboardInterrupt:
                logging.info("\n👋 Shutting down gracefully...")
                break
            except Exception as e:
                logging.error(f"❌ Error in update cycle: {e}", exc_info=True)
                logging.info(f"⏳ Waiting {args.interval}s before retry...")
                time.sleep(args.interval)
    else:
        # Run once
        dashboard.run_full_update()


if __name__ == "__main__":
    main()
