#!/usr/bin/env python3
"""Dell R630 Resource Monitor - Logs to BigQuery"""
import psutil, os, pandas as pd
from datetime import datetime
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"

mem = psutil.virtual_memory()
disk = psutil.disk_usage("/home")
cpu = psutil.cpu_percent(interval=1)
python_procs = len([p for p in psutil.process_iter(["name"]) if "python" in p.info.get("name", "").lower()])

df = pd.DataFrame([{
    "timestamp": datetime.now(),
    "hostname": "dell-r630",
    "ram_used_gb": round(mem.used / 1e9, 2),
    "ram_available_gb": round(mem.available / 1e9, 2),
    "ram_percent": mem.percent,
    "cpu_percent": cpu,
    "disk_used_gb": round(disk.used / 1e9, 2),
    "disk_free_gb": round(disk.free / 1e9, 2),
    "disk_percent": disk.percent,
    "active_python_processes": python_procs,
    "load_avg_1min": os.getloadavg()[0],
    "load_avg_5min": os.getloadavg()[1],
    "load_avg_15min": os.getloadavg()[2]
}])

client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
table_id = "inner-cinema-476211-u9.uk_energy_prod.dell_resource_usage"

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()

print(f"✅ Logged: RAM {mem.percent:.1f}%, CPU {cpu:.1f}%, Disk {disk.percent:.1f}%, Py-procs: {python_procs}")
