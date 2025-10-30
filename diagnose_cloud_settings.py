import json
import os

from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ----- Configuration -----
SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"
PROJECT_ID = "jibber-jabber-knowledge"


# ----- Cloud Settings Diagnostics -----
def diagnose_cloud_settings():
    print("=" * 80)
    print("GOOGLE CLOUD SETTINGS DIAGNOSTICS")
    print("=" * 80)

    # 1. Service Account Information
    print("\n1. SERVICE ACCOUNT INFORMATION")
    print("-" * 50)
    try:
        with open(SERVICE_ACCOUNT_FILE, "r") as f:
            service_account_info = json.load(f)

        service_account_email = service_account_info.get("client_email", "Unknown")
        service_account_project = service_account_info.get("project_id", "Unknown")

        print(f"Service Account Email: {service_account_email}")
        print(f"Service Account Project: {service_account_project}")
        print(f"Current Project ID: {PROJECT_ID}")

        if service_account_project != PROJECT_ID:
            print(
                "WARNING: Service account project ID does not match configured project ID"
            )
    except Exception as e:
        print(f"Error reading service account file: {e}")

    # 2. API Access & Scopes
    print("\n2. API ACCESS & SCOPES")
    print("-" * 50)

    apis_to_check = [
        {
            "name": "Google Sheets API",
            "api": "sheets",
            "version": "v4",
            "scopes": ["https://www.googleapis.com/auth/spreadsheets"],
        },
        {
            "name": "Google Drive API",
            "api": "drive",
            "version": "v3",
            "scopes": ["https://www.googleapis.com/auth/drive"],
        },
        {
            "name": "Google Apps Script API",
            "api": "script",
            "version": "v1",
            "scopes": ["https://www.googleapis.com/auth/script.projects"],
        },
        {
            "name": "BigQuery API",
            "api": "bigquery",
            "version": "v2",
            "scopes": ["https://www.googleapis.com/auth/bigquery"],
        },
    ]

    for api_info in apis_to_check:
        print(f"\nChecking {api_info['name']}:")
        try:
            # Create credentials with the specific scope
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=api_info["scopes"]
            )

            # Build the service to test access
            service = build(
                api_info["api"], api_info["version"], credentials=credentials
            )

            # Try a simple API call based on the service
            if api_info["api"] == "sheets":
                # Test with a dummy spreadsheet ID
                try:
                    service.spreadsheets().get(
                        spreadsheetId="12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
                    ).execute()
                    print("✅ Can access Google Sheets")
                except Exception as e:
                    print(f"❌ Cannot access Google Sheets: {str(e)}")

            elif api_info["api"] == "drive":
                try:
                    service.files().list(pageSize=1).execute()
                    print("✅ Can access Google Drive")
                except Exception as e:
                    print(f"❌ Cannot access Google Drive: {str(e)}")

            elif api_info["api"] == "script":
                try:
                    service.projects().list().execute()
                    print("✅ Can access Google Apps Script")
                except Exception as e:
                    print(f"❌ Cannot access Google Apps Script: {str(e)}")

            elif api_info["api"] == "bigquery":
                try:
                    bq_client = bigquery.Client(
                        credentials=credentials, project=PROJECT_ID
                    )
                    bq_client.list_datasets(max_results=1)
                    print("✅ Can access BigQuery")
                except Exception as e:
                    print(f"❌ Cannot access BigQuery: {str(e)}")

        except Exception as e:
            print(f"❌ Error testing {api_info['name']}: {e}")

    # 3. Specific Google Drive Storage Check
    print("\n3. GOOGLE DRIVE STORAGE CHECK")
    print("-" * 50)
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive"]
        )
        drive_service = build("drive", "v3", credentials=credentials)

        about = drive_service.about().get(fields="storageQuota,user").execute()

        print(f"User Email: {about.get('user', {}).get('emailAddress', 'Unknown')}")

        storage_quota = about.get("storageQuota", {})
        usage = int(storage_quota.get("usage", 0))
        limit = (
            int(storage_quota.get("limit", 0)) if storage_quota.get("limit") else None
        )

        # Convert to MB for readability
        usage_mb = usage / (1024 * 1024)
        limit_mb = limit / (1024 * 1024) if limit else "Unlimited"

        print(f"Storage Used: {usage_mb:.2f} MB")
        print(f"Storage Limit: {limit_mb}")

        if limit and usage > limit * 0.9:
            print("WARNING: Google Drive storage is over 90% full")
    except Exception as e:
        print(f"Error checking Drive storage: {e}")

    # 4. BigQuery Dataset & Storage Analysis
    print("\n4. BIGQUERY ANALYSIS")
    print("-" * 50)
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

        # List datasets
        datasets = list(bq_client.list_datasets())
        print(f"Number of datasets in project {PROJECT_ID}: {len(datasets)}")

        if datasets:
            dataset_id = "uk_energy_insights"  # The dataset we're interested in
            dataset_exists = any(ds.dataset_id == dataset_id for ds in datasets)

            if dataset_exists:
                print(f"✅ Dataset '{dataset_id}' exists")

                # Check for tables that might store GeoJSON
                tables = list(bq_client.list_tables(dataset_id))
                print(f"Number of tables in dataset {dataset_id}: {len(tables)}")

                geojson_tables = [
                    table.table_id
                    for table in tables
                    if "geo" in table.table_id.lower()
                ]
                if geojson_tables:
                    print(f"Potential GeoJSON tables: {', '.join(geojson_tables)}")
                else:
                    print("No tables with 'geo' in the name found")

                # Analyze BigQuery GeoJSON storage options
                print("\nAnalysis of BigQuery GeoJSON Storage Options:")
                print("- BigQuery supports GEOGRAPHY data type for geospatial data")
                print("- Can store points, lines, polygons, and multi-polygons")
                print(
                    "- Supports spatial analysis functions like ST_DISTANCE, ST_CONTAINS, etc."
                )
                print(
                    "- GeoJSON can be converted to GEOGRAPHY type using ST_GEOGFROMGEOJSON"
                )
                print("- Maximum size for a GEOGRAPHY value is 10MB")

                # Test if the GeoJSON is too large for BigQuery
                try:
                    with open("system_regulatory/gis/merged_geojson.geojson", "r") as f:
                        geojson_data = json.load(f)

                    geojson_size_mb = len(json.dumps(geojson_data)) / (1024 * 1024)
                    print(f"GeoJSON file size: {geojson_size_mb:.2f} MB")

                    if geojson_size_mb > 10:
                        print(
                            "❌ GeoJSON is larger than BigQuery's 10MB limit for GEOGRAPHY values"
                        )
                        print(
                            "   This is likely why BigQuery is not suitable for hosting this GeoJSON"
                        )
                    else:
                        print(
                            "✅ GeoJSON size is within BigQuery's GEOGRAPHY value limit"
                        )

                    num_features = len(geojson_data.get("features", []))
                    print(f"Number of features in GeoJSON: {num_features}")

                    if num_features > 100:
                        print(
                            "ℹ️ GeoJSON has many features, which may need to be split into multiple rows"
                        )
                except Exception as e:
                    print(f"Error analyzing GeoJSON file: {e}")
            else:
                print(f"❌ Dataset '{dataset_id}' does not exist")
    except Exception as e:
        print(f"Error analyzing BigQuery: {e}")

    # 5. Recommended Architecture
    print("\n5. RECOMMENDED ARCHITECTURE")
    print("-" * 50)
    print("Based on diagnostics, the following architecture is recommended:")

    print("\nOption 1: Google Drive + Apps Script")
    print("- ✅ Simple to implement")
    print("- ✅ Direct integration with Google Sheets")
    print("- ✅ No data transformation needed")
    print("- ❌ May have storage quota issues")
    print("- ❌ Slower for large GeoJSON files")

    print("\nOption 2: GitHub + Apps Script")
    print("- ✅ No storage quota issues")
    print("- ✅ Version control for GeoJSON files")
    print("- ✅ Fast CDN delivery")
    print("- ❌ Requires public repository")
    print("- ❌ Extra setup step")

    print("\nOption 3: BigQuery + Cloud Storage + Apps Script")
    print("- ✅ Powerful geospatial analysis")
    print("- ✅ Good for large datasets")
    print("- ❌ Complex setup")
    print("- ❌ Requires data transformation")
    print("- ❌ Size limitations for GEOGRAPHY values")

    print(
        "\nRECOMMENDATION: Based on the diagnostics, the most suitable approach appears to be:"
    )
    print(
        "GitHub + Apps Script (Option 2) - due to potential Drive quota issues and GeoJSON size"
    )


# Run diagnostics
if __name__ == "__main__":
    diagnose_cloud_settings()
