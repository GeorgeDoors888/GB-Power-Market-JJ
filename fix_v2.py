import re

with open("parallel_bm_kpi_pipeline_v2.py", "r") as f:
    content = f.read()

# Fix nested quotes in f-strings
content = content.replace(
    'print(f"�� BACKFILL MODE: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}")',
    'start_str = start_date.strftime("%Y-%m-%d")\n        end_str = end_date.strftime("%Y-%m-%d")\n        print(f"🔵 BACKFILL MODE: {start_str} to {end_str}")'
)

with open("parallel_bm_kpi_pipeline_v2.py", "w") as f:
    f.write(content)

print("Fixed")
