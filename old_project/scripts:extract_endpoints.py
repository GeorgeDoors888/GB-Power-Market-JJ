import json
import csv
from pathlib import Path

input_file = Path("elexon_api2.json")
csv_out = Path("endpoints_list.csv")
txt_out = Path("endpoints_list.txt")

with open(input_file) as f:
    data = json.load(f)

endpoints = []

def extract(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "url" and isinstance(v, str):
                endpoints.append(v)
            else:
                extract(v)
    elif isinstance(obj, list):
        for item in obj:
            extract(item)

extract(data)

with open(csv_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["endpoint"])
    for ep in sorted(set(endpoints)):
        writer.writerow([ep])

with open(txt_out, "w") as f:
    for ep in sorted(set(endpoints)):
        f.write(ep + "\n")

print(f"Extracted {len(set(endpoints))} endpoints.")
print(f"- CSV: {csv_out}")
print(f"- TXT: {txt_out}")