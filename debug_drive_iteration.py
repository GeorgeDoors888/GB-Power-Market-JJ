#!/usr/bin/env python3
"""Debug Drive file iteration."""
import sys
sys.path.insert(0, '/app')

from src.config import load_settings
from src.indexing.drive_crawler import iter_drive_files

cfg = load_settings()
print(f"Config loaded:")
print(f"  Project: {cfg.get('project')}")
print(f"  Dataset: {cfg.get('dataset')}")
print(f"  Drive query: {cfg['drive']['query'][:100]}...")

print("\nIterating Drive files...")
count = 0
for f in iter_drive_files(cfg["drive"]["query"]):
    count += 1
    print(f"  {count}. {f.get('name')} ({f.get('mimeType')})")
    if count >= 10:
        print(f"  ... (showing first 10)")
        break

print(f"\nTotal files matching query: {count}+")
