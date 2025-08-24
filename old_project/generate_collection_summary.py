#!/usr/bin/env python3
"""Generate collection summary for BMRS data in GCS (client library, no gsutil).

Counts daily bid_offer_acceptances JSON files as the proxy for day completeness and
aggregates yearly progress + storage sizing.

Auth: export GOOGLE_APPLICATION_CREDENTIALS=sa-key.json (service account with storage.objectViewer)
"""
import json
import datetime
import re
import os
from google.cloud import storage
import google.auth.exceptions
from datetime import datetime as _dt

BUCKET = os.getenv('BMRS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
PREFIX = 'bmrs_data'
OUTPUT = 'collection_summary.json'

# Target days per year (leap years accounted; 2025 partial YTD target adjustable)
YEAR_TARGETS = {
    2016: 366,
    2017: 365,
    2018: 365,
    2019: 365,
    2020: 366,
    2021: 365,
    2022: 365,
    2023: 365,
    2024: 366,
    2025: 220
}

def collect_metadata():
    try:
        client = storage.Client()
    except Exception as e:
        raise RuntimeError(f"Storage client init failed: {e}. Ensure GOOGLE_APPLICATION_CREDENTIALS points to valid service account JSON.")
    # Only list under acceptances path for counting days
    accept_prefix = f'{PREFIX}/bid_offer_acceptances/'
    blobs = client.list_blobs(BUCKET, prefix=accept_prefix)

    file_re = re.compile(r'bmrs_data/bid_offer_acceptances/(\d{4})/(\d{2})/bid_offer_acceptances_(\d{4}-\d{2}-\d{2})\.json$')
    day_counts = {}
    total_size = 0
    for b in blobs:
        total_size += b.size if b.size else 0
        m = file_re.match(b.name)
        if m:
            year = int(m.group(1))
            day = m.group(3)
            day_counts.setdefault(year, set()).add(day)
    return day_counts, total_size

def build_summary(day_counts, total_size):
    summary_years = []
    total_collected = 0
    total_target = 0
    for year, target in YEAR_TARGETS.items():
        collected = len(day_counts.get(year, []))
        total_collected += collected
        total_target += target
        summary_years.append({
            'year': year,
            'collected_files': collected,
            'target_files': target,
            'completion_pct': round((collected / target) * 100, 1) if target else 0
        })

    return {
        'bucket': BUCKET,
        'prefix': PREFIX,
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'years': summary_years,
        'totals': {
            'collected': total_collected,
            'target': total_target,
            'overall_completion_pct': round((total_collected / total_target) * 100, 1) if total_target else 0
        },
        'storage_bytes': total_size,
        'storage_gb': round(total_size / (1024**3), 3) if total_size else None
    }

def upload_summary(client: storage.Client, summary: dict):
    bucket = client.bucket(BUCKET)
    # Current summary
    blob = bucket.blob(f'{PREFIX}/{OUTPUT}')
    blob.cache_control = 'no-cache'
    blob.upload_from_string(json.dumps(summary, indent=2), content_type='application/json')
    # Historical timestamped summary
    ts = _dt.utcnow().strftime('%Y%m%d_%H%M%S')
    hist_blob = bucket.blob(f'{PREFIX}/summaries/collection_summary_{ts}.json')
    hist_blob.cache_control = 'public, max-age=60'
    hist_blob.upload_from_string(json.dumps(summary, indent=2), content_type='application/json')
    return f'gs://{BUCKET}/{PREFIX}/{OUTPUT}'

def main():
    day_counts, total_size = collect_metadata()
    summary = build_summary(day_counts, total_size)

    with open(OUTPUT, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'✅ Wrote {OUTPUT}')

    try:
        client = storage.Client()
    except Exception as e:
        print(f"❌ Skipping upload; credentials error: {e}")
        return
    uri = upload_summary(client, summary)
    print(f'☁️  Uploaded to {uri}')
    print('If not already public, make bucket objects readable (one-time):')
    print(f'  gsutil iam ch allUsers:objectViewer gs://{BUCKET}')

if __name__ == '__main__':
    main()
