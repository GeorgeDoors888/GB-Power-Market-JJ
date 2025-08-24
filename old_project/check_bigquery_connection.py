# check_bigquery_connection.py
from google.cloud import bigquery
import os

def check_connection():
    """
    Checks the connection to Google BigQuery and runs a minimal query.
    """
    project_id = "jibber-jabber-knowledge"
    print(f"Attempting to connect to BigQuery project: {project_id}...")

    try:
        # The client will automatically use the credentials from the environment
        # (e.g., from 'gcloud auth application-default login')
        client = bigquery.Client(project=project_id)
        print("✅ BigQuery client created successfully.")
        
        # Run a minimal query to confirm the connection and permissions
        print("Running a minimal test query...")
        query = "SELECT 1"
        query_job = client.query(query)
        
        # Wait for the job to complete
        results = query_job.result()
        print("✅ Test query executed successfully.")
        
        for row in results:
            print(f"Query result: {row[0]}")

        print("\nConclusion: BigQuery connection is working correctly.")

    except Exception as e:
        print("\n❌ FAILED to connect to BigQuery or execute query.")
        print("Error details:")
        print(e)
        print("\nPlease ensure you are authenticated. Run the following command in your terminal:")
        print("gcloud auth application-default login")

if __name__ == "__main__":
    check_connection()
