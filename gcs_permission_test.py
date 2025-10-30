
import os
from google.cloud import storage
from google.api_core.exceptions import Forbidden
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gcs_permission_test')

def test_gcs_permissions():
    """
    Tests GCS permissions by trying to list objects in a bucket.
    """
    key_path = "jibber_jabber_key.json"
    bucket_name = os.getenv('GCS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
    project_id = os.getenv('GCP_PROJECT', 'jibber-jabber-knowledge')

    logger.info(f"--- Starting GCS Permission Test ---")
    logger.info(f"Using Project ID: {project_id}")
    logger.info(f"Using Bucket: {bucket_name}")

    if not os.path.exists(key_path):
        logger.error(f"❌ Service account key file not found at: {key_path}")
        return

    logger.info(f"✅ Found service account key file: {key_path}")

    try:
        # Initialize client with the service account key
        storage_client = storage.Client.from_service_account_json(key_path, project=project_id)
        bucket = storage_client.bucket(bucket_name)

        logger.info("Attempting to list objects in the bucket (requires 'storage.objects.list')...")

        # The list_blobs() method requires 'storage.objects.list' permission.
        # We only need to fetch one to test the connection and permissions.
        blobs = list(bucket.list_blobs(max_results=1))

        logger.info(f"✅ Successfully listed {len(blobs)} object(s). Read permissions are working.")

        # Now, let's test write permissions by trying to upload a dummy file.
        # This requires 'storage.objects.create' permission.
        logger.info("Attempting to upload a dummy file to test write permissions (requires 'storage.objects.create')...")
        blob = bucket.blob("permission_test_dummy_file.txt")
        blob.upload_from_string("This is a test file for checking write permissions.")
        logger.info("✅ Successfully uploaded dummy file.")

        # Clean up the dummy file
        logger.info("Attempting to delete the dummy file (requires 'storage.objects.delete')...")
        blob.delete()
        logger.info("✅ Successfully deleted dummy file.")

        logger.info("--- GCS Permission Test Result ---")
        logger.info("✅ SUCCESS: All tested permissions (list, create, delete) are correctly configured for this service account key.")

    except Forbidden as e:
        logger.error("--- GCS Permission Test Result ---")
        logger.error(f"❌ FAILURE: A permission error occurred.")
        logger.error(f"Error details: {e}")
        logger.error("This confirms the service account associated with 'jibber_jabber_key.json' lacks the required IAM roles.")
        logger.error("Please grant the 'Storage Object Creator' and 'Storage Object Viewer' roles to the service account in the GCP Console.")

    except Exception as e:
        logger.error("--- GCS Permission Test Result ---")
        logger.error(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_gcs_permissions()
