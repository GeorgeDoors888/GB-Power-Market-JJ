import os

from google.cloud import billing_v1

project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")


def is_billing_enabled(project_id):
    client = billing_v1.CloudBillingClient()
    project_name = f"projects/{project_id}"
    billing_info = client.get_project_billing_info(name=project_name)
    return billing_info.billing_enabled


if __name__ == "__main__":
    if not project_id:
        print("GOOGLE_CLOUD_PROJECT environment variable not set.")
    else:
        enabled = is_billing_enabled(project_id)
        if enabled:
            print(
                f"Billing is enabled for project {project_id}. Sandbox mode is NOT active."
            )
        else:
            print(
                f"Billing is NOT enabled for project {project_id}. Sandbox mode IS active."
            )
