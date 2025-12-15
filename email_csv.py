#!/usr/bin/env python3
"""
Simple solution: Just tell user where file is and show them how to access it
"""

import os

file_path = "/home/george/Downloads/property_directors_crm_20251211_1131.csv"
file_size = os.path.getsize(file_path) / (1024*1024)

print("="*70)
print("CSV FILE ACCESS OPTIONS")
print("="*70)
print()
print(f"📁 File Location: {file_path}")
print(f"📊 File Size: {file_size:.2f} MB")
print(f"📈 Records: 87,987 directors")
print()
print("🔧 ACCESS OPTIONS:")
print()
print("1️⃣  EMAIL TO YOURSELF:")
print("    - Attach the file to an email")
print("    - Send to your email address")
print("    - Download from Mac")
print()
print("2️⃣  USE SFTP CLIENT (FileZilla, Cyberduck, etc):")
print("    - Server: 192.168.1.50")
print("    - User: george")
print("    - Path: /home/george/Downloads/")
print("    - File: property_directors_crm_20251211_1131.csv")
print()
print("3️⃣  COPY TO SHARED NETWORK FOLDER:")

# Try to find any mounted network shares
import subprocess
result = subprocess.run(['mount'], capture_output=True, text=True)
mounts = [line for line in result.stdout.split('\n') if 'cifs' in line or 'nfs' in line or 'smb' in line]

if mounts:
    print("    Found network mounts:")
    for mount in mounts:
        print(f"    - {mount}")
else:
    print("    No network shares found")

print()
print("4️⃣  UPLOAD TO CLOUD:")
print("    - Google Drive")
print("    - Dropbox")
print("    - OneDrive")
print()
print("="*70)
