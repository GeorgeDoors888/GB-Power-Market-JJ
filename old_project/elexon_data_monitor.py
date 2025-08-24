#!/usr/bin/env python3
"""
Elexon Data Monitor & Smart Scheduler
====================================
Monitors your cloud storage and schedules smart downloads of new data
"""

import os
import json
import time
from datetime import datetime, timedelta
from google.cloud import storage
from typing import Dict, List
# import schedule  # Optional - for automated scheduling

class ElexonDataMonitor:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket("jibber-jabber-knowledge-bmrs-data")
        
    def get_bucket_status(self) -> Dict:
        """Get current status of bucket contents"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'folders': {},
            'total_files': 0,
            'total_size_mb': 0,
            'latest_files': []
        }
        
        for blob in self.bucket.list_blobs():
            status['total_files'] += 1
            size_mb = blob.size / (1024 * 1024)
            status['total_size_mb'] += size_mb
            
            folder = blob.name.split('/')[0] if '/' in blob.name else 'root'
            if folder not in status['folders']:
                status['folders'][folder] = {'files': 0, 'size_mb': 0, 'latest': None}
            
            status['folders'][folder]['files'] += 1
            status['folders'][folder]['size_mb'] += size_mb
            
            if blob.time_created and (not status['folders'][folder]['latest'] or 
                                    blob.time_created > status['folders'][folder]['latest']):
                status['folders'][folder]['latest'] = blob.time_created
            
            # Track recent files
            if blob.time_created and blob.time_created > datetime.now().replace(tzinfo=blob.time_created.tzinfo) - timedelta(hours=1):
                status['latest_files'].append({
                    'name': blob.name,
                    'size_mb': round(size_mb, 2),
                    'created': blob.time_created.isoformat()
                })
        
        status['total_size_mb'] = round(status['total_size_mb'], 1)
        return status
    
    def save_status_report(self, status: Dict):
        """Save status report to cloud"""
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Deep convert all datetime objects
        status_serializable = json.loads(json.dumps(status, default=convert_datetime))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"monitoring/status_report_{timestamp}.json"
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(status_serializable, indent=2), content_type='application/json')
        return f"gs://jibber-jabber-knowledge-bmrs-data/{blob_name}"
    
    def check_for_new_data_sources(self) -> List[str]:
        """Check Elexon for any new data sources we haven't seen"""
        # This would connect to Elexon APIs to discover new datasets
        new_sources = []
        
        # For now, return some common datasets we might want to add
        known_datasets = {'FUELINST', 'MELNGC', 'TEMP', 'WINDFOR', 'NONBM', 'INDGEN', 'SYSWARN', 'MID', 'NETBSAD'}
        
        # Additional datasets that might become available
        potential_new = {
            'SOSO': 'System Operator-System Operator data',
            'IMBALPRICES': 'Imbalance Pricing data', 
            'DYNDEM': 'Dynamic Demand data',
            'CARBINT': 'Carbon Intensity data',
            'STORAGEDATA': 'Energy Storage data'
        }
        
        # Check if we have these yet
        existing_datasets = set()
        for blob in self.bucket.list_blobs(prefix='datasets/'):
            dataset_name = blob.name.split('/')[1] if len(blob.name.split('/')) > 1 else None
            if dataset_name:
                existing_datasets.add(dataset_name)
        
        for dataset, description in potential_new.items():
            if dataset not in existing_datasets:
                new_sources.append(f"{dataset}: {description}")
        
        return new_sources
    
    def estimate_next_download_cycle(self) -> Dict:
        """Estimate when next download cycle should run"""
        # Get latest dataset timestamps
        latest_timestamps = {}
        
        for blob in self.bucket.list_blobs(prefix='datasets/'):
            parts = blob.name.split('/')
            if len(parts) >= 2:
                dataset_name = parts[1]
                if blob.time_created:
                    if dataset_name not in latest_timestamps or blob.time_created > latest_timestamps[dataset_name]:
                        latest_timestamps[dataset_name] = blob.time_created
        
        # Calculate recommendations
        now = datetime.now().replace(tzinfo=list(latest_timestamps.values())[0].tzinfo if latest_timestamps else None)
        recommendations = {
            'next_full_sync': 'Tomorrow at 6:00 AM',
            'incremental_updates': 'Every 4 hours',
            'estimated_new_data_size': '10-50 MB per day',
            'stale_datasets': []
        }
        
        # Find datasets that haven't been updated in 24+ hours
        for dataset, last_update in latest_timestamps.items():
            hours_since_update = (now - last_update).total_seconds() / 3600
            if hours_since_update > 24:
                recommendations['stale_datasets'].append({
                    'dataset': dataset,
                    'hours_old': round(hours_since_update, 1)
                })
        
        return recommendations
    
    def generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        print("🔍 ELEXON DATA MONITORING REPORT")
        print("=" * 50)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get current status
        status = self.get_bucket_status()
        
        print("📊 CURRENT STORAGE STATUS")
        print("-" * 30)
        print(f"📁 Total folders: {len(status['folders'])}")
        print(f"📄 Total files: {status['total_files']:,}")
        print(f"💾 Total size: {status['total_size_mb']:.1f} MB")
        print()
        
        print("📂 FOLDER BREAKDOWN")
        print("-" * 30)
        for folder_name, folder_data in status['folders'].items():
            latest_str = folder_data['latest'].strftime('%Y-%m-%d %H:%M') if folder_data['latest'] else 'No files'
            print(f"   {folder_name}/: {folder_data['files']} files, {folder_data['size_mb']:.1f} MB (latest: {latest_str})")
        print()
        
        # Check for new data sources
        new_sources = self.check_for_new_data_sources()
        if new_sources:
            print("🆕 POTENTIAL NEW DATA SOURCES")
            print("-" * 30)
            for source in new_sources:
                print(f"   • {source}")
        else:
            print("✅ All known data sources are being monitored")
        print()
        
        # Download recommendations
        recommendations = self.estimate_next_download_cycle()
        print("📈 DOWNLOAD RECOMMENDATIONS")
        print("-" * 30)
        print(f"🔄 Next full sync: {recommendations['next_full_sync']}")
        print(f"⚡ Incremental updates: {recommendations['incremental_updates']}")
        print(f"📏 Expected daily growth: {recommendations['estimated_new_data_size']}")
        
        if recommendations['stale_datasets']:
            print("\n⚠️ STALE DATASETS (need updating):")
            for stale in recommendations['stale_datasets']:
                print(f"   • {stale['dataset']}: {stale['hours_old']} hours old")
        else:
            print("✅ All datasets are current")
        
        print()
        
        # Save report to cloud
        report_path = self.save_status_report(status)
        print(f"💾 Full report saved to: {report_path}")
        print()
        print("🎯 NEXT ACTIONS:")
        print("   1. Review stale datasets for immediate update")
        print("   2. Consider adding new data sources")
        print("   3. Schedule next monitoring check")

def main():
    """Main monitoring function"""
    monitor = ElexonDataMonitor()
    monitor.generate_monitoring_report()

if __name__ == "__main__":
    main()
