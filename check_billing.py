import os

from google.api_core import exceptions
from google.cloud import billing_v1


def check_billing_status(project_id: str):
    """
    Checks the billing status of a Google Cloud project.

    Args:
        project_id (str): The ID of the Google Cloud project.
    """
    try:
        billing_client = billing_v1.CloudBillingClient()
        project_name = f"projects/{project_id}"

        print(f"Checking billing status for project: {project_name}")

        billing_info = billing_client.get_project_billing_info(name=project_name)

        if billing_info.billing_enabled:
            print(f"  -> Billing is ENABLED for project '{project_id}'.")
            print(
                f"  -> Associated Billing Account: {billing_info.billing_account_name}"
            )
        else:
            print(f"  -> Billing is DISABLED for project '{project_id}'.")
            print(
                "  -> To use services that require billing, please enable it in the Google Cloud Console."
            )

    except exceptions.PermissionDenied as e:
        print(
            f"Error: Permission Denied. The current user/service account does not have the required permissions."
        )
        print(
            "Please ensure you have the 'billing.projects.getBillingInfo' permission."
        )
        print(f"Details: {e}")
    except exceptions.NotFound:
        print(f"Error: Project '{project_id}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # You can set the project ID directly or via an environment variable
    gcp_project_id = os.environ.get("GCP_PROJECT") or "jibber-jabber-knowledge"
    if not gcp_project_id:
        raise ValueError(
            "Project ID not found. Please set the GCP_PROJECT environment variable."
        )
    check_billing_status(gcp_project_id)
