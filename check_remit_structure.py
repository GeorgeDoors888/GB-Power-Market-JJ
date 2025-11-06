#!/usr/bin/env python3
"""
Quick check of REMIT API response structure
"""
import requests
import json

BMRS_API = 'https://data.elexon.co.uk/bmrs/api/v1'

print("🔍 Checking REMIT API response structure...\n")

# Test assets endpoint
print("="*80)
print("REMIT ASSETS")
print("="*80)
url = f"{BMRS_API}/reference/remit/assets/all"
response = requests.get(url, timeout=60)
assets = response.json()

print(f"Response type: {type(assets)}")
print(f"Length: {len(assets) if isinstance(assets, list) else 'N/A'}")

if isinstance(assets, list) and len(assets) > 0:
    print(f"\nFirst item type: {type(assets[0])}")
    print(f"First item value: {assets[0]}")
    
    if len(assets) > 1:
        print(f"\nSecond item type: {type(assets[1])}")
        print(f"Second item value: {assets[1]}")
        
    print(f"\nSample of first 10 items:")
    for i, asset in enumerate(assets[:10]):
        print(f"  [{i}] {type(asset)}: {asset}")

# Test participants endpoint
print("\n" + "="*80)
print("REMIT PARTICIPANTS")
print("="*80)
url = f"{BMRS_API}/reference/remit/participants/all"
response = requests.get(url, timeout=60)
participants = response.json()

print(f"Response type: {type(participants)}")
print(f"Length: {len(participants) if isinstance(participants, list) else 'N/A'}")

if isinstance(participants, list) and len(participants) > 0:
    print(f"\nFirst item type: {type(participants[0])}")
    print(f"First item value: {participants[0]}")
    
    print(f"\nSample of first 5 items:")
    for i, part in enumerate(participants[:5]):
        print(f"  [{i}] {type(part)}: {part}")

# Save to files for inspection
with open('remit_assets_sample.json', 'w') as f:
    json.dump(assets[:20] if isinstance(assets, list) else assets, f, indent=2)
    print(f"\n✅ Saved sample to: remit_assets_sample.json")

with open('remit_participants_sample.json', 'w') as f:
    json.dump(participants[:20] if isinstance(participants, list) else participants, f, indent=2)
    print(f"✅ Saved sample to: remit_participants_sample.json")
