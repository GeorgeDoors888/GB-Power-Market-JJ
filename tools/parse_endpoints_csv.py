import csv
from collections import defaultdict

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

# Print all dataset IDs and their available formats
for ds_id, formats in sorted(dataset_formats.items()):
    print(f"{ds_id}: {', '.join(sorted(formats))}")
