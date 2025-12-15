#!/usr/bin/env python3
import os
import shutil

# Source file on Dell
source = "/home/george/Downloads/property_directors_crm_20251211_1131.csv"

# Try to find Mac's mounted Downloads folder
mac_downloads_options = [
    "/home/shared/FullMacBackup/",
    "/Users/georgemajor/Downloads/",
    os.path.expanduser("~/Downloads/")
]

print("🔍 Looking for accessible Mac location...")

for path in mac_downloads_options:
    if os.path.exists(path) and os.path.isdir(path):
        destination = os.path.join(path, "property_directors_crm_20251211_1131.csv")
        print(f"✅ Found: {path}")
        print(f"📂 Copying to: {destination}")
        
        try:
            shutil.copy2(source, destination)
            print(f"✅ SUCCESS! File copied to: {destination}")
            print(f"📊 File size: {os.path.getsize(destination) / 1024 / 1024:.2f} MB")
            break
        except Exception as e:
            print(f"❌ Failed: {e}")
    else:
        print(f"⏭️  Not found: {path}")
else:
    print("\n❌ Could not find accessible Mac location")
    print("\n📝 File remains at: /home/george/Downloads/property_directors_crm_20251211_1131.csv")
