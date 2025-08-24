"""
Collection statistics tracker for BMRS data downloads
Stores and retrieves stats in Google Cloud Storage
"""

import json
from datetime import datetime, timedelta
from google.cloud import storage
from typing import Dict, List, Optional

class CollectionStats:
    def __init__(self, bucket_name: str, stats_path: str = "stats/collection_stats.json"):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.stats_path = stats_path
        
    def load_stats(self) -> Dict:
        """Load existing stats from GCS"""
        try:
            blob = self.bucket.blob(self.stats_path)
            if blob.exists():
                return json.loads(blob.download_as_string())
        except Exception:
            pass
        return {
            "total_downloads": 0,
            "downloads_by_dataset": {},
            "hourly_rate": {},
            "last_updated": None,
            "datasets_remaining": len(DATASETS),
            "start_date": None,
            "end_date": None
        }
    
    def update_stats(self, dataset: str, num_records: int, start_date: str = None, end_date: str = None):
        """Update download statistics"""
        stats = self.load_stats()
        
        # First download? Set start date
        if not stats["start_date"]:
            stats["start_date"] = start_date
            
        stats["end_date"] = end_date
        stats["total_downloads"] += num_records
        
        # Update per-dataset stats
        if dataset not in stats["downloads_by_dataset"]:
            stats["downloads_by_dataset"][dataset] = 0
        stats["downloads_by_dataset"][dataset] += num_records
        
        # Calculate hourly rate
        now = datetime.utcnow()
        hour_key = now.strftime("%Y-%m-%d-%H")
        if hour_key not in stats["hourly_rate"]:
            stats["hourly_rate"][hour_key] = 0
        stats["hourly_rate"][hour_key] += num_records
        
        # Cleanup old hourly stats (keep last 24 hours)
        cutoff = now - timedelta(hours=24)
        stats["hourly_rate"] = {k: v for k, v in stats["hourly_rate"].items()
                               if datetime.strptime(k, "%Y-%m-%d-%H") > cutoff}
        
        stats["last_updated"] = now.isoformat()
        stats["datasets_remaining"] = len(DATASETS) - len(stats["downloads_by_dataset"])
        
        # Save updated stats
        blob = self.bucket.blob(self.stats_path)
        blob.upload_from_string(json.dumps(stats, indent=2))
        
    def get_summary(self) -> Dict:
        """Get a human-readable summary of collection progress"""
        stats = self.load_stats()
        
        if not stats["last_updated"]:
            return {"status": "No downloads recorded yet"}
            
        # Calculate average hourly rate
        hourly_rates = list(stats["hourly_rate"].values())
        avg_hourly = sum(hourly_rates) / len(hourly_rates) if hourly_rates else 0
        
        return {
            "total_records_downloaded": stats["total_downloads"],
            "datasets_completed": len(stats["downloads_by_dataset"]),
            "datasets_remaining": stats["datasets_remaining"],
            "average_records_per_hour": int(avg_hourly),
            "collection_period": {
                "start": stats["start_date"],
                "end": stats["end_date"],
                "last_update": stats["last_updated"]
            },
            "progress_by_dataset": stats["downloads_by_dataset"]
        }
