#!/usr/bin/env python3
"""Wrapper to run continuous_extract with 6 workers"""
from importlib.machinery import SourceFileLoader
import os

# Load the module
mod = SourceFileLoader('ce', '/tmp/continuous_extract.py').load_module()

# Override MAX_WORKERS to 6 (optimal for 4 cores with I/O wait)
mod.MAX_WORKERS = 6

# Create PID file for monitoring
with open('/tmp/continuous_extract.pid', 'w') as f:
    f.write(str(os.getpid()))

print(f"⚡ Starting continuous extraction with {mod.MAX_WORKERS} workers")
print(f"📝 PID: {os.getpid()}")

# Run main extraction
mod.main()
