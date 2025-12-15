#!/bin/bash
# 3-year BM data ingestion runner
# Auto-confirms and runs in background

cd /home/george/GB-Power-Market-JJ

echo "yes" | python3 ingest_bm_3years.py --start 2022-01-01 --end 2025-12-13
