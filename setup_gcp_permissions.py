import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# =============================
# CONFIGURATION
# =============================
PROJECT_ID = "jibber-jabber-knowledge"
# This is the service account we are trying to fix.
SERVICE_ACCOUNT_EMAIL = "jibber-jabber-knowledge@appspot.gserviceaccount.com"
KEY_FILE = "jibber_jabber_key.json"
ROLES_TO_ASSIGN = [
    "roles/storage.objectCreator",
    "roles/bigquery.dataUser",
    "roles/bigquery.jobUser"
]

# =============================
# STEP 1 — AUTHENTICATE
# =============================
def authenticate():
    """Authenticate using the service account key."""
    if not os.path.exists(KEY_FILE):
        raise FileNotFoundError(f"Service account key file not found at: {KEY_FILE}")

    creds = service_account.Credentials.from_service_account_file(
        KEY_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    print("✅ Authenticated successfully using service account key.")
    return creds

# =============================
# STEP 2 — ASSIGN IAM ROLES
# =============================
def assign_roles(crm_service, sa_email):
    """Assigns predefined roles to the service account."""
    try:
        policy = crm_service.projects().getIamPolicy(
            resource=PROJECT_ID, body={}
        ).execute()

        bindings = policy.get("bindings", [])
        member = f"serviceAccount:{sa_email}"

        for role in ROLES_TO_ASSIGN:
            binding = next((b for b in bindings if b["role"] == role), None)

            if binding:
                if member not in binding["members"]:
                    binding["members"].append(member)
                    print(f"🔑 Adding role {role} to {sa_email}")
                else:
                    print(f"ℹ️ Role {role} is already assigned to {sa_email}")
            else:
                bindings.append({"role": role, "members": [member]})
                print(f"🔑 Assigning new role {role} to {sa_email}")

        policy["bindings"] = bindings

        crm_service.projects().setIamPolicy(
            resource=PROJECT_ID,
            body={"policy": policy}
        ).execute()

        print(f"\n✅ IAM roles assigned successfully to {sa_email}")

    except Exception as e:
        print(f"❌ An error occurred while assigning roles: {e}")
        print("\nℹ️ This is likely because the service account itself does not have permission to modify IAM policies.")
        print("A user with 'Project IAM Admin' or 'Owner' role needs to perform this action in the Google Cloud Console.")
        raise

# =============================
# MAIN FUNCTION
# =============================
def main():
    creds = authenticate()

    # Build the Cloud Resource Manager API client
    crm_service = build("cloudresourcemanager", "v1", credentials=creds)

    # Assign roles to the existing service account
    assign_roles(crm_service, SERVICE_ACCOUNT_EMAIL)

    print("\n🎉 Permission check/update script complete!")

if __name__ == "__main__":
    main()

