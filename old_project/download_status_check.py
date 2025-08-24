#!/usr/bin/env python3
"""
Quick Status Check for Sunday Data Download
=========================================
Check progress of the comprehensive data download
"""

import os
import json
from datetime import datetime
from pathlib import Path

def check_download_status():
    """Check the current status of data download"""
    
    print("📊 SUNDAY DATA DOWNLOAD STATUS")
    print("=" * 40)
    print(f"🕐 Check time: {datetime.now().strftime('%H:%M:%S')}")
    
    base_path = Path('bmrs_data')
    
    if not base_path.exists():
        print("❌ No data directory found")
        print("💡 Download may not have started yet")
        return
    
    data_types = ['bid_offer_acceptances', 'generation_outturn', 'demand_outturn', 'system_warnings']
    
    total_files = 0
    total_records = 0
    
    for data_type in data_types:
        type_path = base_path / data_type
        
        if type_path.exists():
            files = list(type_path.glob('**/*.json'))
            
            records_count = 0
            recent_files = 0
            
            # Count recent files (last hour)
            one_hour_ago = datetime.now().timestamp() - 3600
            
            for file_path in files:
                try:
                    # Check if file is recent
                    if file_path.stat().st_mtime > one_hour_ago:
                        recent_files += 1
                    
                    # Count records in file
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        records_count += data.get('record_count', 0)
                except:
                    pass
            
            total_files += len(files)
            total_records += records_count
            
            print(f"📁 {data_type}:")
            print(f"   Files: {len(files)} (Recent: {recent_files})")
            print(f"   Records: {records_count:,}")
        else:
            print(f"📁 {data_type}: Not started")
    
    print(f"\n📊 TOTALS:")
    print(f"   Files: {total_files}")
    print(f"   Records: {total_records:,}")
    
    # Check if processing summary exists
    summary_file = base_path / 'processing_ready_summary.json'
    if summary_file.exists():
        print(f"\n✅ DOWNLOAD COMPLETE!")
        print(f"📋 Processing summary available")
        
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            print(f"🎯 Ready for Sunday processing:")
            for data_type, info in summary.get('data_types', {}).items():
                print(f"   {data_type}: {info['files']} files, {info['records']:,} records")
                
        except Exception as e:
            print(f"⚠️ Could not read summary: {e}")
    
    else:
        print(f"\n🔄 DOWNLOAD IN PROGRESS...")
        print(f"💡 Run this script again to check updated status")
    
    # Estimate completion if download is active
    if total_files > 0:
        # Rough estimate based on typical download patterns
        estimated_total = 180 * 4  # 180 days × 4 data types
        if total_files < estimated_total:
            progress = total_files / estimated_total
            print(f"📈 Estimated progress: {progress:.1%}")
        else:
            print(f"🎉 Download appears complete!")

if __name__ == "__main__":
    check_download_status()
