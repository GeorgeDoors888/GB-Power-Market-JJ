import os
from google.cloud import bigquery

def get_bq_client():
    project_id = os.getenv("PROJECT_ID", "inner-cinema-476211-u9")
    return bigquery.Client(project=project_id)
