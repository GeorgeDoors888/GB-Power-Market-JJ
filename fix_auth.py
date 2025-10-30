#!/usr/bin/env python3
"""Fix bulk_downloader.py to use Application Default Credentials"""

with open('bulk_downloader.py', 'r') as f:
    content = f.read()

# Replace the hardcoded service account section
old_auth = '''# Ensure GOOGLE_APPLICATION_CREDENTIALS is set to a valid path
service_account_path = "/Users/georgemajor/service-account-key.json"  # Update this path as needed
if not os.path.exists(service_account_path):
    raise FileNotFoundError(f"Service account key file not found at {service_account_path}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Initialize BigQuery client with the service account credentials
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(service_account_path)
bq = bigquery.Client(credentials=credentials)'''

new_auth = '''# Use Application Default Credentials (from gcloud auth login)
# No need for service account JSON file
print("🔐 Using Application Default Credentials...")

# Initialize BigQuery client with default credentials
bq = bigquery.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT", "jibber-jabber-knowledge"))'''

content = content.replace(old_auth, new_auth)

with open('bulk_downloader.py', 'w') as f:
    f.write(content)

print("✅ Fixed bulk_downloader.py to use Application Default Credentials")
print("   No service account JSON file needed!")
