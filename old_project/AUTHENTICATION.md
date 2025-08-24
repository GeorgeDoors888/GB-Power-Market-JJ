# BigQuery Authentication Tools

This directory contains tools for managing BigQuery authentication in the Jibber Jabber energy data analysis project.

## Available Tools

### 1. Authentication Module (`bq_auth.py`)

A standalone authentication module that provides multiple authentication methods with fallbacks:

- Service account JSON key file
- Application Default Credentials
- User account with OAuth flow
- Interactive password input

Usage:
```bash
# Test authentication
./bq_auth.py --test

# Reset authentication (force re-authentication)
./bq_auth.py --reset

# Specify service account key file
./bq_auth.py --key-file=/path/to/service-account.json
```

### 2. Reset Credentials Script (`reset_credentials.sh`)

A convenient shell script to reset authentication and prompt for new credentials:

```bash
# Run the script
./reset_credentials.sh
```

This will:
- Clear any cached credentials
- Guide you through the authentication process
- Optionally test the new credentials
- Optionally run the BOD analysis with new credentials

### 3. BOD Analysis with Authentication (`run_bod_with_auth.py`)

Run the BOD (Bid-Offer Data) analysis with proper authentication:

```bash
# Run with default settings (last 30 days)
./run_bod_with_auth.py

# Specify date range
./run_bod_with_auth.py --start-date=2025-01-01 --end-date=2025-08-23

# Force re-authentication
./run_bod_with_auth.py --reset

# Use synthetic data (no authentication needed)
./run_bod_with_auth.py --synthetic
```

## Authentication Methods

The authentication tools attempt the following methods in order:

1. **Service Account Key File**: Uses a JSON key file for a service account
2. **Application Default Credentials**: Uses credentials from `gcloud auth application-default login`
3. **OAuth Flow**: Launches browser-based authentication for user accounts
4. **Interactive Input**: Asks for manual authentication information if all else fails

## Troubleshooting

If you're having authentication issues:

1. Run `./bq_auth.py --reset --test` to reset credentials and test
2. Check if your service account key file is valid and has necessary permissions
3. Try using Application Default Credentials with: `gcloud auth application-default login`
4. Check if your project ID is correct (default: "jibber-jabber-knowledge")

For persistent issues, use the `--synthetic` flag to bypass authentication and use synthetic data for testing.
