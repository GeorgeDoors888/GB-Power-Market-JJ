import csv
from collections import defaultdict
import json

# Parse endpoints.csv to extract dataset IDs and available formats
csv_path = "old_project/endpoints.csv"
dataset_formats = defaultdict(set)

with open(csv_path, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        ds_id = row["id"].strip()
        # Only consider request fields for ServiceType (format)
        if row["direction"] == "request" and row["Field Name"] == "ServiceType":
            # Formats are comma-separated, e.g. 'csv/xml'
            for fmt in row["Sample Data"].split("/"):
                fmt = fmt.strip().lower()
                if fmt:
                    dataset_formats[ds_id].add(fmt)

with open("dataset_formats.json", "w") as f:
    json.dump({k: sorted(list(v)) for k, v in dataset_formats.items()}, f, indent=2)

print(f"Wrote dataset_formats.json with {len(dataset_formats)} dataset IDs.")
