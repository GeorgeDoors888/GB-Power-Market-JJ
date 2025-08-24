#!/usr/bin/env python3
"""
Google Drive Data Manager for BMRS API Data Collection
Organizes data by type and date, saves as CSV files, uploads to Google Drive
"""

import os
import csv
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
from dotenv import load_dotenv
import concurrent.futures
import threading
from pathlib import Path
import time

# Load environment variables
load_dotenv('api.env')

class BMRSDataCollector:
    def __init__(self):
        self.api_key = os.getenv('BMRS_API_KEY')
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # File structure configuration
        self.data_types = {
            'bid_offer_acceptances': {
                'endpoint': 'balancing/acceptances/all',
                'folder': 'bid_offer_acceptances',
                'description': 'Bid-Offer Acceptance Data'
            },
            'demand_outturn': {
                'endpoint': 'demand/outturn/all',
                'folder': 'demand_outturn', 
                'description': 'Demand Outturn Data'
            },
            'generation_outturn': {
                'endpoint': 'generation/outturn/all',
                'folder': 'generation_outturn',
                'description': 'Generation Outturn Data'
            },
            'system_warnings': {
                'endpoint': 'datasets/SYSWARN',
                'folder': 'system_warnings',
                'description': 'System Warnings Data'
            },
            'frequency_data': {
                'endpoint': 'balancing/physical/all',
                'folder': 'frequency_data',
                'description': 'System Frequency Data'
            },
            'pricing_data': {
                'endpoint': 'balancing/pricing/all', 
                'folder': 'pricing_data',
                'description': 'Balancing Pricing Data'
            }
        }
        
        # Google Drive setup
        self.drive_service = None
        self.setup_google_drive()
        
        # Create local directory structure
        self.setup_local_directories()
        
    def setup_local_directories(self):
        """Create local directory structure for data organization"""
        base_dir = Path("bmrs_data")
        base_dir.mkdir(exist_ok=True)
        
        for data_type, config in self.data_types.items():
            folder_path = base_dir / config['folder']
            folder_path.mkdir(exist_ok=True)
            
            # Create subdirectories by year
            for year in range(2016, 2026):
                year_path = folder_path / str(year)
                year_path.mkdir(exist_ok=True)
                
        print("✅ Local directory structure created")
        
    def setup_google_drive(self):
        """Setup Google Drive API connection"""
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = None
        
        # Check for existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # You'll need to create credentials.json from Google Cloud Console
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print("⚠️  credentials.json not found. Google Drive upload will be disabled.")
                    print("   Create credentials at: https://console.cloud.google.com/")
                    return
                    
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                
        try:
            self.drive_service = build('drive', 'v3', credentials=creds)
            print("✅ Google Drive API connected")
        except Exception as e:
            print(f"⚠️  Google Drive setup failed: {e}")
            
    def create_drive_folder_structure(self):
        """Create folder structure in Google Drive"""
        if not self.drive_service:
            return None
            
        try:
            # Create main BMRS Data folder
            main_folder = self.create_drive_folder("BMRS_Historical_Data", None)
            
            folder_ids = {}
            for data_type, config in self.data_types.items():
                # Create data type folder
                type_folder = self.create_drive_folder(config['folder'], main_folder)
                folder_ids[data_type] = type_folder
                
                # Create year subfolders
                for year in range(2016, 2026):
                    year_folder = self.create_drive_folder(str(year), type_folder)
                    
            print("✅ Google Drive folder structure created")
            return folder_ids
            
        except Exception as e:
            print(f"❌ Failed to create Drive folders: {e}")
            return None
            
    def create_drive_folder(self, name, parent_id):
        """Create a folder in Google Drive"""
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
        
    def download_data_for_date(self, data_type, date, settlement_period=None):
        """Download data for a specific date and settlement period"""
        try:
            config = self.data_types[data_type]
            endpoint = config['endpoint']
            
            params = {
                'apikey': self.api_key,
                'settlementDate': date.strftime('%Y-%m-%d')
            }
            
            if settlement_period:
                params['settlementPeriod'] = settlement_period
                
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', [])
                return records
            else:
                print(f"❌ {data_type} - {date.strftime('%Y-%m-%d')}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error downloading {data_type} for {date}: {e}")
            return []
            
    def save_to_csv(self, data_type, date, records):
        """Save records to CSV file with proper structure"""
        if not records:
            return None
            
        try:
            config = self.data_types[data_type]
            year = date.year
            
            # Create filename
            filename = f"{data_type}_{date.strftime('%Y_%m_%d')}.csv"
            filepath = Path("bmrs_data") / config['folder'] / str(year) / filename
            
            # Convert to DataFrame and save
            df = pd.DataFrame(records)
            df.to_csv(filepath, index=False)
            
            print(f"💾 Saved: {filepath} ({len(records)} records)")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving {data_type} CSV: {e}")
            return None
            
    def upload_to_drive(self, filepath, data_type, year):
        """Upload CSV file to Google Drive"""
        if not self.drive_service or not filepath:
            return
            
        try:
            # Find the appropriate folder (simplified - you'd need folder ID tracking)
            file_metadata = {
                'name': filepath.name,
                'parents': ['your_folder_id_here']  # Replace with actual folder ID
            }
            
            media = MediaFileUpload(str(filepath), mimetype='text/csv')
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"☁️  Uploaded to Drive: {filepath.name}")
            
        except Exception as e:
            print(f"❌ Drive upload failed: {e}")
            
    def collect_historical_data(self, start_date, end_date, data_types=None):
        """Collect historical data for date range"""
        if data_types is None:
            data_types = list(self.data_types.keys())
            
        print(f"🚀 Starting historical data collection")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📊 Data types: {data_types}")
        
        current_date = start_date
        total_days = (end_date - start_date).days + 1
        processed_days = 0
        
        while current_date <= end_date:
            print(f"\n📅 Processing {current_date.strftime('%Y-%m-%d')} ({processed_days+1}/{total_days})")
            
            for data_type in data_types:
                # For bid_offer_acceptances, we need all 48 settlement periods
                if data_type == 'bid_offer_acceptances':
                    all_records = []
                    for period in range(1, 49):  # 1-48 settlement periods
                        records = self.download_data_for_date(data_type, current_date, period)
                        all_records.extend(records)
                        time.sleep(0.1)  # Rate limiting
                        
                    if all_records:
                        filepath = self.save_to_csv(data_type, current_date, all_records)
                        if filepath:
                            self.upload_to_drive(filepath, data_type, current_date.year)
                else:
                    # For other data types, single request per day
                    records = self.download_data_for_date(data_type, current_date)
                    if records:
                        filepath = self.save_to_csv(data_type, current_date, records)
                        if filepath:
                            self.upload_to_drive(filepath, data_type, current_date.year)
                            
                time.sleep(0.2)  # Rate limiting between data types
                
            current_date += timedelta(days=1)
            processed_days += 1
            
        print(f"\n🎉 Historical data collection completed!")
        print(f"📊 Processed {processed_days} days")

def main():
    """Main execution function"""
    collector = BMRSDataCollector()
    
    # Set date range from 2016 to today
    start_date = datetime(2016, 1, 1)
    end_date = datetime.now() - timedelta(days=1)  # Yesterday to ensure data availability
    
    print("🌟 BMRS Historical Data Collection System")
    print("=" * 50)
    
    # Create Google Drive folder structure
    collector.create_drive_folder_structure()
    
    # Start collection
    collector.collect_historical_data(start_date, end_date)
    
if __name__ == "__main__":
    main()
