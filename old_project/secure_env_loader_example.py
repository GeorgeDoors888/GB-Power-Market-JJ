import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access your IRIS credentials securely
IRIS_CLIENT_ID = os.getenv('IRIS_CLIENT_ID')
IRIS_CLIENT_SECRET = os.getenv('IRIS_CLIENT_SECRET')
IRIS_TENANT_ID = os.getenv('IRIS_TENANT_ID')
IRIS_QUEUE_NAME = os.getenv('IRIS_QUEUE_NAME')
IRIS_NAMESPACE = os.getenv('IRIS_NAMESPACE')
IRIS_QUEUE_URL = os.getenv('IRIS_QUEUE_URL')

# Example usage (do NOT print secrets in production)
print(f"IRIS_CLIENT_ID loaded: {bool(IRIS_CLIENT_ID)}")
print(f"IRIS_QUEUE_NAME: {IRIS_QUEUE_NAME}")
