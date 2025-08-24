#!/usr/bin/env python3
"""
Transfer Local Files to Google Cloud Storage
==========================================
Move existing downloaded files to GCS and clean up local storage
"""

import os
import sys
import json
from pathlib import Path
import subprocess
from datetime import datetime

def setup_google_cloud_storage():
    """Setup Google Cloud Storage bucket for BMRS data"""
    
    print("🚀 Setting up Google Cloud Storage...")
    
    project_id = "jibber-jabber-knowledge"
    bucket_name = f"{project_id}-bmrs-data"
    
    try:
        # Check if bucket exists, create if not
        result = subprocess.run([
            'gsutil', 'ls', f'gs://{bucket_name}/'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"📦 Creating bucket: {bucket_name}")
            subprocess.run([
                'gsutil', 'mb', '-p', project_id, f'gs://{bucket_name}'
            ], check=True)
        else:
            print(f"✅ Bucket exists: {bucket_name}")
        
        return bucket_name
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error setting up bucket: {e}")
        return None

def transfer_local_files_to_gcs(bucket_name):
    """Transfer all local BMRS files to Google Cloud Storage"""
    
    print(f"📤 Transferring local files to gs://{bucket_name}/...")
    
    local_data_path = Path('bmrs_data')
    
    if not local_data_path.exists():
        print("⚪ No local data to transfer")
        return True
    
    # Get file count and size before transfer
    local_files = list(local_data_path.glob('**/*.json'))
    total_files = len(local_files)
    
    print(f"📊 Files to transfer: {total_files}")
    
    if total_files == 0:
        print("⚪ No JSON files to transfer")
        return True
    
    try:
        # Use gsutil to sync the entire directory
        print("🔄 Starting transfer (this may take a few minutes)...")
        
        result = subprocess.run([
            'gsutil', '-m', 'rsync', '-r', '-d', 
            str(local_data_path), f'gs://{bucket_name}/bmrs_data'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Transfer completed successfully!")
        
        # Verify transfer
        verify_result = subprocess.run([
            'gsutil', 'du', '-s', f'gs://{bucket_name}/bmrs_data'
        ], capture_output=True, text=True)
        
        if verify_result.returncode == 0:
            cloud_size = verify_result.stdout.strip().split()[0]
            print(f"☁️  Cloud storage used: {cloud_size} bytes")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Transfer failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def cleanup_local_files():
    """Remove local files after successful transfer"""
    
    print("🧹 Cleaning up local files...")
    
    local_data_path = Path('bmrs_data')
    
    if not local_data_path.exists():
        print("⚪ No local files to clean")
        return
    
    try:
        # Remove all JSON files
        json_files = list(local_data_path.glob('**/*.json'))
        
        for file_path in json_files:
            file_path.unlink()
        
        print(f"✅ Removed {len(json_files)} local files")
        
        # Remove empty directories
        for root, dirs, files in os.walk(local_data_path, topdown=False):
            for directory in dirs:
                dir_path = Path(root) / directory
                try:
                    dir_path.rmdir()  # Only removes if empty
                except OSError:
                    pass  # Directory not empty, that's fine
        
        print("🎉 Local cleanup completed!")
        
        # Show remaining local storage
        try:
            result = subprocess.run(['du', '-sh', str(local_data_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                remaining_size = result.stdout.strip().split()[0]
                print(f"💾 Local storage now: {remaining_size}")
        except:
            pass
            
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Main transfer process"""
    
    print("☁️  GOOGLE CLOUD STORAGE TRANSFER")
    print("=" * 50)
    print("Moving local BMRS data to Google Cloud Storage")
    print("This will free up your local hard drive space")
    print("=" * 50)
    
    # Check if gsutil is available
    try:
        subprocess.run(['gsutil', 'version'], check=True, 
                      capture_output=True, text=True)
        print("✅ Google Cloud SDK available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Google Cloud SDK not found!")
        print("💡 Please install: https://cloud.google.com/sdk/docs/install")
        return False
    
    # Setup bucket
    bucket_name = setup_google_cloud_storage()
    if not bucket_name:
        return False
    
    # Check local storage before transfer
    local_path = Path('bmrs_data')
    if local_path.exists():
        try:
            result = subprocess.run(['du', '-sh', str(local_path)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                local_size = result.stdout.strip().split()[0]
                print(f"📊 Local data size: {local_size}")
        except:
            print("📊 Local data exists (size unknown)")
    
    # Transfer files
    success = transfer_local_files_to_gcs(bucket_name)
    
    if success:
        # Clean up local files
        cleanup_local_files()
        
        print("\n🎉 TRANSFER COMPLETED SUCCESSFULLY!")
        print("=" * 40)
        print(f"☁️  Your data is now in: gs://{bucket_name}/bmrs_data")
        print("💾 Local hard drive space freed up")
        print("🔄 Ready to continue downloading to cloud")
        
        # Save bucket info for future use
        config = {
            'bucket_name': bucket_name,
            'transfer_date': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        with open('cloud_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"⚙️  Cloud config saved to: cloud_config.json")
        
        return True
    
    else:
        print("\n❌ TRANSFER FAILED!")
        print("🛡️ Your local files are safe and unchanged")
        print("💡 Please check your Google Cloud setup")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
