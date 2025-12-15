#!/usr/bin/env python3
import os
import shutil

source = "/home/george/Downloads/property_directors_crm_20251211_1131.csv"

# The ACTUAL Mac path (not the backup)
mac_path = "/Users/georgemajor/Downloads/property_directors_crm_20251211_1131.csv"

print(f"📂 Source: {source}")
print(f"🎯 Target: {mac_path}")
print()

if os.path.exists("/Users/georgemajor/Downloads/"):
    try:
        shutil.copy2(source, mac_path)
        print(f"✅ SUCCESS! File copied to your Mac Downloads folder")
        print(f"📊 Size: {os.path.getsize(mac_path) / 1024 / 1024:.2f} MB")
        print()
        print(f"📁 Open Finder → Downloads → property_directors_crm_20251211_1131.csv")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Mac Downloads folder not accessible from Dell")
    print()
    print("💡 Alternative: Use VS Code to download:")
    print("   1. In VS Code Explorer, navigate to /home/george/Downloads/")
    print("   2. Find: property_directors_crm_20251211_1131.csv")
    print("   3. Right-click → 'Save As...' → Save to Mac Downloads")
