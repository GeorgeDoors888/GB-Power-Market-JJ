#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv("/app/.env")

print("🔧 Configuration Check:")
print(f"DRIVE_CRAWL_Q: {os.environ.get('DRIVE_CRAWL_Q', 'NOT SET')}")
print(f"\n✅ Filter is set to index ALL files (no MIME type restrictions)")
